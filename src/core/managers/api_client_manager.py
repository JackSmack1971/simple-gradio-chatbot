# src/core/managers/api_client_manager.py
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
from enum import Enum

from ...utils.logging import logger
from ...external.openrouter.client import OpenRouterClient
from ...external.openrouter.rate_limiter import RateLimiter
from ...external.openrouter.error_handler import ErrorHandler
from .conversation_manager import ConversationManager


# Centralized request ID format controls to keep consistency across generators
REQUEST_ID_PREFIX = "req_"
REQUEST_ID_SUFFIX_HEX_LENGTH = 12
REQUEST_ID_TOTAL_LENGTH = len(REQUEST_ID_PREFIX) + REQUEST_ID_SUFFIX_HEX_LENGTH


class RequestState(Enum):
    """States for API request processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class APIRequestResult:
    """Structured response for API requests exposing the tracking identifier."""

    success: bool
    request_id: str
    data: Any


class APIClientManager:
    """High-level orchestration of API operations with state management and error handling."""

    def __init__(self, openrouter_client: Optional[OpenRouterClient] = None,
                 rate_limiter: Optional[RateLimiter] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 conversation_manager: Optional[ConversationManager] = None):
        """
        Initialize the APIClientManager.

        Args:
            openrouter_client: OpenRouter client instance. If None, creates a new one.
            rate_limiter: Rate limiter instance. If None, creates a new one.
            error_handler: Error handler instance. If None, creates a new one.
            conversation_manager: Conversation manager instance. If None, creates a new one.
        """
        self.openrouter_client = openrouter_client or OpenRouterClient()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.error_handler = error_handler or ErrorHandler()
        self.conversation_manager = conversation_manager or ConversationManager()

        # Request tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.request_history: List[Dict[str, Any]] = []

        logger.info("APIClientManager initialized")

    def chat_completion(self, conversation_id: str, message: str, model: str = "anthropic/claude-3-haiku",
                       request_id_consumer: Optional[Callable[[str], None]] = None,
                       **kwargs) -> APIRequestResult:
        """
        Perform a chat completion with full orchestration.

        Args:
            conversation_id: Conversation ID
            message: User message
            model: Model identifier
            request_id_consumer: Optional callback invoked with generated request ID
            **kwargs: Additional parameters

        Returns:
            APIRequestResult exposing the request ID and response payload
        """
        request_id = self._generate_request_id()
        if request_id_consumer:
            try:
                request_id_consumer(request_id)
            except Exception as callback_error:
                logger.error(f"request_id_consumer failed: {callback_error}")
        start_time = time.time()

        try:
            # Initialize request state
            self._init_request_state(request_id, {
                'type': 'chat_completion',
                'conversation_id': conversation_id,
                'model': model,
                'message_length': len(message)
            })

            # Validate conversation
            conversation = self.conversation_manager.get_conversation(conversation_id)
            if not conversation:
                return APIRequestResult(False, request_id, {"error": f"Conversation {conversation_id} not found"})

            # Add user message to conversation
            success = self.conversation_manager.add_message(conversation_id, message, "user")
            if not success:
                return APIRequestResult(False, request_id, {"error": "Failed to add user message to conversation"})

            # Get conversation history
            messages = self._prepare_messages(conversation_id)

            # Execute with rate limiting and error handling
            result = self._execute_with_protection(
                self._chat_completion_request,
                request_id,
                messages,
                model,
                **kwargs
            )

            success, response_data = result

            if not success:
                response_data = self._normalize_failure_payload(response_data)

            if success:
                # Add assistant response to conversation
                assistant_message = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                if assistant_message:
                    self.conversation_manager.add_message(conversation_id, assistant_message, "assistant")

                # Update request state
                self._update_request_state(request_id, RequestState.COMPLETED, {
                    'response_length': len(assistant_message),
                    'processing_time': time.time() - start_time
                })

            else:
                # Update request state on failure
                failure_state = {
                    'error': response_data.get('error'),
                    'processing_time': time.time() - start_time
                }
                if 'details' in response_data:
                    failure_state['details'] = response_data['details']
                if 'retry' in response_data:
                    failure_state['retry'] = response_data['retry']
                self._update_request_state(request_id, RequestState.FAILED, {
                    **failure_state
                })

            return APIRequestResult(success, request_id, response_data)

        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            sanitized_error = self.error_handler.get_user_friendly_message(str(e))
            self._update_request_state(request_id, RequestState.FAILED, {
                'error': sanitized_error,
                'processing_time': time.time() - start_time
            })
            return APIRequestResult(False, request_id, {"error": f"Chat completion failed: {sanitized_error}"})

    def _chat_completion_request(self, request_id: str, messages: List[Dict[str, Any]],
                                model: str, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """Execute the actual chat completion request."""
        self._update_request_state(request_id, RequestState.PROCESSING)

        # Make the API call
        success, response = self.openrouter_client.chat_completion(model, messages, **kwargs)

        return success, response

    def _execute_with_protection(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Execute a function with rate limiting and error handling protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tuple of (success, result)
        """
        def rate_limited_func(*args, **kwargs):
            """Wrapper function for rate limiting."""
            return func(*args, **kwargs)

        # Execute with retry logic
        success, result = self.error_handler.execute_with_retry(
            self._rate_limited_execution,
            rate_limited_func,
            *args,
            **kwargs
        )

        return success, result

    def _normalize_failure_payload(self, payload: Any) -> Dict[str, Any]:
        """Ensure failure payloads follow the structured error contract."""
        if isinstance(payload, dict):
            normalized = dict(payload)
            error_value = normalized.get('error')

            if error_value:
                normalized['error'] = self.error_handler.get_user_friendly_message(error_value)
            else:
                normalized['error'] = self.error_handler.get_user_friendly_message(normalized)

            return normalized

        sanitized_message = self.error_handler.get_user_friendly_message(payload)
        return {'error': sanitized_message}

    def _rate_limited_execution(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """Execute function with rate limiting."""
        # For now, execute directly (rate limiting would be integrated here)
        # In a full implementation, this would use the rate limiter
        return func(*args, **kwargs)

    def _prepare_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Prepare message history for API request."""
        messages = self.conversation_manager.get_conversation_messages(conversation_id, limit=limit)

        # Convert to API format
        api_messages = []
        for msg in messages:
            api_messages.append({
                'role': msg.get('role', 'user'),
                'content': msg.get('content', '')
            })

        return api_messages

    def stream_chat_completion(self, conversation_id: str, message: str, model: str = "anthropic/claude-3-haiku",
                             callback: Optional[Callable[[str], None]] = None,
                             request_id_consumer: Optional[Callable[[str], None]] = None,
                             **kwargs) -> APIRequestResult:
        """
        Perform a streaming chat completion.

        Args:
            conversation_id: Conversation ID
            message: User message
            model: Model identifier
            callback: Callback function for streaming chunks
            request_id_consumer: Optional callback invoked with generated request ID
            **kwargs: Additional parameters

        Returns:
            APIRequestResult exposing the request ID and streaming payload
        """
        request_id = self._generate_request_id()
        if request_id_consumer:
            try:
                request_id_consumer(request_id)
            except Exception as callback_error:
                logger.error(f"request_id_consumer failed: {callback_error}")
        start_time = time.time()

        try:
            # Initialize request state
            self._init_request_state(request_id, {
                'type': 'streaming_chat_completion',
                'conversation_id': conversation_id,
                'model': model,
                'streaming': True
            })

            # Add user message
            success = self.conversation_manager.add_message(conversation_id, message, "user")
            if not success:
                return APIRequestResult(False, request_id, "Failed to add user message")

            # Get conversation history
            messages = self._prepare_messages(conversation_id)

            # For now, simulate streaming (in a real implementation, this would use the actual streaming API)
            streaming_success, payload = self._simulate_streaming_response(messages, model, callback)

            if not streaming_success:
                error_message = payload or "Streaming request failed"
                self._update_request_state(request_id, RequestState.FAILED, {
                    'error': error_message,
                    'processing_time': time.time() - start_time
                })
                return APIRequestResult(False, request_id, error_message)

            full_response = payload

            # Add assistant response
            if full_response:
                self.conversation_manager.add_message(conversation_id, full_response, "assistant")

            self._update_request_state(request_id, RequestState.COMPLETED, {
                'response_length': len(full_response),
                'processing_time': time.time() - start_time
            })

            return APIRequestResult(True, request_id, full_response)

        except Exception as e:
            logger.error(f"Streaming chat completion failed: {str(e)}")
            self._update_request_state(request_id, RequestState.FAILED, {
                'error': str(e),
                'processing_time': time.time() - start_time
            })
            return APIRequestResult(False, request_id, f"Streaming failed: {str(e)}")

    def _simulate_streaming_response(self, messages: List[Dict[str, Any]], model: str,
                                   callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Simulate a streaming response for demonstration."""
        # In a real implementation, this would use the actual streaming API
        # For now, make a regular request and simulate streaming

        success, response = self.openrouter_client.chat_completion(model, messages)

        if not success:
            # Security: do not leak raw structures; normalize into safe message
            if isinstance(response, dict):
                error_message = response.get('error') or response.get('message') or str(response)
            else:
                error_message = str(response)
            return False, error_message or "Streaming request failed"

        full_content = response.get('choices', [{}])[0].get('message', {}).get('content', '')

        # Simulate streaming by calling callback with chunks
        if callback:
            words = full_content.split()
            for i, word in enumerate(words):
                chunk = word + " "
                callback(chunk)
                time.sleep(0.05)  # Simulate delay

        return True, full_content

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a request.

        Args:
            request_id: Request ID

        Returns:
            Request status data or None if not found
        """
        return self.active_requests.get(request_id)

    def list_active_requests(self) -> List[Dict[str, Any]]:
        """
        List all active requests.

        Returns:
            List of active request data
        """
        return list(self.active_requests.values())

    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel an active request.

        Args:
            request_id: Request ID

        Returns:
            True if cancelled, False otherwise
        """
        if request_id in self.active_requests:
            self._update_request_state(request_id, RequestState.FAILED, {'cancelled': True})
            # Use pop to avoid race conditions where the update handler already removed the entry
            self.active_requests.pop(request_id, None)
            logger.info(f"Cancelled request {request_id}")
            return True

        return False

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.

        Returns:
            Dictionary with usage statistics
        """
        total_requests = len(self.request_history)
        completed_requests = len([r for r in self.request_history if r.get('state') == RequestState.COMPLETED.value])
        failed_requests = len([r for r in self.request_history if r.get('state') == RequestState.FAILED.value])

        total_tokens = sum(r.get('metadata', {}).get('tokens', 0) for r in self.request_history)
        total_cost = sum(r.get('metadata', {}).get('cost', 0.0) for r in self.request_history)

        return {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'failed_requests': failed_requests,
            'success_rate': completed_requests / max(1, total_requests),
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'active_requests': len(self.active_requests)
        }

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        import uuid
        # Security: deterministic prefix ensures IDs can be filtered while suffix stays random
        return f"{REQUEST_ID_PREFIX}{uuid.uuid4().hex[:REQUEST_ID_SUFFIX_HEX_LENGTH]}"

    def _init_request_state(self, request_id: str, metadata: Dict[str, Any]) -> None:
        """Initialize request state tracking."""
        self.active_requests[request_id] = {
            'id': request_id,
            'state': RequestState.PENDING.value,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata
        }

    def _update_request_state(self, request_id: str, state: RequestState,
                            additional_data: Optional[Dict[str, Any]] = None) -> None:
        """Update request state."""
        if request_id in self.active_requests:
            request_data = self.active_requests[request_id]
            request_data['state'] = state.value
            request_data['updated_at'] = datetime.now().isoformat()

            if additional_data:
                request_data['metadata'].update(additional_data)

            # Move to history if completed or failed
            if state in [RequestState.COMPLETED, RequestState.FAILED]:
                self.request_history.append(request_data)
                # Keep only recent history
                if len(self.request_history) > 1000:
                    self.request_history = self.request_history[-1000:]
                del self.active_requests[request_id]

    def validate_api_connection(self) -> bool:
        """
        Validate API connection and authentication.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            return self.openrouter_client.validate_connection()
        except Exception as e:
            logger.error(f"API connection validation failed: {str(e)}")
            return False

    def get_available_models(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Get list of available models.

        Returns:
            Tuple of (success, models_list)
        """
        try:
            success, response = self.openrouter_client.list_models()
            if success:
                models = response.get('data', [])
                return True, models
            else:
                logger.error(f"Failed to get models: {response}")
                return False, []
        except Exception as e:
            logger.error(f"Get models failed: {str(e)}")
            return False, []

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.rate_limiter.shutdown()
            self.openrouter_client.close()
            logger.info("APIClientManager cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")