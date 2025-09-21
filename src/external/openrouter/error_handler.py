# src/external/openrouter/error_handler.py
import time
import random
from typing import Dict, Any, Optional, Tuple, Callable
from enum import Enum

from ...utils.logging import logger


class ErrorType(Enum):
    """Types of errors that can occur."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class ErrorHandler:
    """Comprehensive error handler for OpenRouter API interactions."""

    # HTTP status code mappings
    HTTP_ERROR_MESSAGES = {
        400: "Bad request - please check your input parameters",
        401: "Authentication failed - please check your API key",
        403: "Access forbidden - you may not have permission for this operation",
        404: "Resource not found - the requested endpoint or model may not exist",
        429: "Rate limit exceeded - please wait before making more requests",
        500: "Internal server error - OpenRouter is experiencing issues",
        502: "Bad gateway - there may be a network issue",
        503: "Service unavailable - OpenRouter may be temporarily down",
        504: "Gateway timeout - the request took too long to process"
    }

    # OpenRouter-specific error codes
    OPENROUTER_ERROR_CODES = {
        "authentication_required": "API key is required for this request",
        "authentication_invalid": "The provided API key is invalid",
        "insufficient_balance": "Your account balance is insufficient for this request",
        "model_not_found": "The requested model is not available",
        "model_not_supported": "This model is not supported for the requested operation",
        "context_length_exceeded": "The input exceeds the model's context length limit",
        "rate_limit_exceeded": "You have exceeded the rate limit for this model",
        "billing_required": "Billing information is required for this request",
        "invalid_request": "The request format is invalid",
        "server_error": "An internal error occurred on the server"
    }

    def __init__(self, max_retries: int = 3, base_backoff: float = 1.0, max_backoff: float = 60.0):
        """
        Initialize the error handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_backoff: Base backoff time in seconds
            max_backoff: Maximum backoff time in seconds
        """
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff

    def classify_error(self, error_data: Dict[str, Any], status_code: Optional[int] = None) -> ErrorType:
        """
        Classify the type of error from API response.

        Args:
            error_data: Error response data
            status_code: HTTP status code

        Returns:
            ErrorType enum value
        """
        # Check HTTP status codes first
        if status_code:
            if status_code == 401:
                return ErrorType.AUTHENTICATION
            elif status_code == 429:
                return ErrorType.RATE_LIMIT
            elif status_code >= 500:
                return ErrorType.API_ERROR

        # Check OpenRouter error codes
        if isinstance(error_data, dict):
            error_code = error_data.get('code') or error_data.get('error', {}).get('code')
            if error_code in ['authentication_required', 'authentication_invalid']:
                return ErrorType.AUTHENTICATION
            elif error_code in ['rate_limit_exceeded']:
                return ErrorType.RATE_LIMIT
            elif error_code in ['model_not_found', 'model_not_supported', 'invalid_request']:
                return ErrorType.VALIDATION

        # Check for network-related errors
        error_message = str(error_data).lower()
        if any(keyword in error_message for keyword in ['timeout', 'connection', 'network', 'dns']):
            return ErrorType.NETWORK

        return ErrorType.UNKNOWN

    def get_user_friendly_message(self, error_data: Dict[str, Any], status_code: Optional[int] = None) -> str:
        """
        Convert technical error data into user-friendly messages.

        Args:
            error_data: Error response data
            status_code: HTTP status code

        Returns:
            User-friendly error message
        """
        # Handle HTTP status codes
        if status_code and status_code in self.HTTP_ERROR_MESSAGES:
            return self.HTTP_ERROR_MESSAGES[status_code]

        # Handle OpenRouter error codes
        if isinstance(error_data, dict):
            error_code = error_data.get('code') or error_data.get('error', {}).get('code')
            if error_code and error_code in self.OPENROUTER_ERROR_CODES:
                return self.OPENROUTER_ERROR_CODES[error_code]

            # Check nested error structure
            nested_error = error_data.get('error', {})
            if isinstance(nested_error, dict):
                message = nested_error.get('message')
                if message:
                    return self._sanitize_error_message(message)

        # Handle string error messages
        if isinstance(error_data, str):
            return self._sanitize_error_message(error_data)

        # Handle generic error dict
        if isinstance(error_data, dict):
            message = error_data.get('message') or error_data.get('error')
            if message:
                return self._sanitize_error_message(str(message))

        # Fallback message
        return "An unexpected error occurred. Please try again later."

    def _sanitize_error_message(self, message: str) -> str:
        """
        Sanitize error messages to remove sensitive information.

        Args:
            message: Raw error message

        Returns:
            Sanitized error message
        """
        # Remove potential sensitive information
        sensitive_patterns = [
            r'api[_-]?key[^\s]*',  # API keys
            r'token[^\s]*',        # Tokens
            r'password[^\s]*',     # Passwords
            r'secret[^\s]*',       # Secrets
        ]

        sanitized = message
        for pattern in sensitive_patterns:
            import re
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)

        return sanitized

    def should_retry(self, error_type: ErrorType, attempt_count: int) -> bool:
        """
        Determine if an error should be retried.

        Args:
            error_type: Type of error that occurred
            attempt_count: Number of attempts made so far

        Returns:
            True if should retry, False otherwise
        """
        if attempt_count >= self.max_retries:
            return False

        # Retry these error types
        retryable_errors = [
            ErrorType.NETWORK,
            ErrorType.RATE_LIMIT,
            ErrorType.API_ERROR  # Sometimes server errors are transient
        ]

        return error_type in retryable_errors

    def calculate_backoff(self, attempt_count: int, error_type: ErrorType) -> float:
        """
        Calculate backoff time for retry attempts.

        Args:
            attempt_count: Current attempt count (0-based)
            error_type: Type of error

        Returns:
            Backoff time in seconds
        """
        # Exponential backoff with jitter
        base_delay = self.base_backoff * (2 ** attempt_count)

        # Longer backoff for rate limits
        if error_type == ErrorType.RATE_LIMIT:
            base_delay *= 2

        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.1, 1.0) * base_delay * 0.1
        delay = base_delay + jitter

        return min(delay, self.max_backoff)

    def handle_error(self, error_data: Dict[str, Any], status_code: Optional[int] = None,
                    attempt_count: int = 0) -> Dict[str, Any]:
        """
        Handle an error comprehensively.

        Args:
            error_data: Error response data
            status_code: HTTP status code
            attempt_count: Number of attempts made so far

        Returns:
            Dict with error handling information
        """
        error_type = self.classify_error(error_data, status_code)
        user_message = self.get_user_friendly_message(error_data, status_code)
        should_retry_attempt = self.should_retry(error_type, attempt_count)

        # Log the error with appropriate level
        log_data = {
            'error_type': error_type.value,
            'status_code': status_code,
            'attempt_count': attempt_count,
            'should_retry': should_retry_attempt,
            'user_message': user_message
        }

        if error_type in [ErrorType.AUTHENTICATION, ErrorType.VALIDATION]:
            logger.warning(f"Non-retryable error: {log_data}")
        elif error_type == ErrorType.UNKNOWN:
            logger.error(f"Unknown error type: {log_data}")
        else:
            logger.info(f"Handled error: {log_data}")

        result = {
            'error_type': error_type.value,
            'user_message': user_message,
            'should_retry': should_retry_attempt,
            'attempt_count': attempt_count
        }

        if should_retry_attempt:
            backoff_time = self.calculate_backoff(attempt_count, error_type)
            result['backoff_time'] = backoff_time
            logger.debug(f"Calculated backoff time: {backoff_time}s")

        return result

    def execute_with_retry(self, func: Callable, *args, max_attempts: Optional[int] = None, **kwargs) -> Tuple[bool, Any]:
        """
        Execute a function with automatic retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            max_attempts: Maximum number of attempts (overrides instance setting)
            **kwargs: Keyword arguments for the function

        Returns:
            Tuple of (success, result_or_error_data)
        """
        max_attempts = max_attempts or (self.max_retries + 1)
        attempt_count = 0
        last_error_info: Optional[Dict[str, Any]] = None
        last_raw_error: Any = None

        def _format_failure_payload(error_info: Dict[str, Any], raw_error: Any,
                                     attempt_index: int, override_retry: Optional[bool] = None) -> Dict[str, Any]:
            """Create a consistent failure payload with sanitized content."""
            sanitized_message = error_info.get('user_message') or self.get_user_friendly_message(raw_error)
            payload: Dict[str, Any] = {'error': sanitized_message}

            error_type = error_info.get('error_type')
            if error_type:
                payload['details'] = {'type': error_type}

            retry_metadata = {
                'attempt': attempt_index + 1,
                'max_attempts': max_attempts
            }

            if override_retry is None:
                retry_metadata['will_retry'] = error_info.get('should_retry', False)
            else:
                retry_metadata['will_retry'] = override_retry

            backoff_time = error_info.get('backoff_time')
            if backoff_time is not None:
                retry_metadata['backoff_seconds'] = backoff_time

            payload['retry'] = retry_metadata

            return payload

        while attempt_count < max_attempts:
            try:
                result = func(*args, **kwargs)

                # Assume success if no exception and result is not an error dict
                if isinstance(result, tuple) and len(result) == 2:
                    success, data = result
                    if success:
                        return True, data
                    else:
                        # Handle API error response
                        error_info = self.handle_error(data, attempt_count=attempt_count)
                        if error_info.get('should_retry'):
                            error_type_value = error_info.get('error_type', ErrorType.UNKNOWN.value)
                            error_enum = ErrorType(error_type_value) if error_type_value in ErrorType._value2member_map_ else ErrorType.UNKNOWN
                            error_info['backoff_time'] = self.calculate_backoff(attempt_count, error_enum)

                        failure_payload = _format_failure_payload(error_info, data, attempt_count)
                        last_error_info = error_info
                        last_raw_error = data

                        if not error_info['should_retry']:
                            return False, failure_payload
                        else:
                            backoff_time = error_info.get('backoff_time', self.base_backoff)
                            logger.info(f"Retrying after {backoff_time}s (attempt {attempt_count + 1}/{max_attempts})")
                            time.sleep(backoff_time)
                            attempt_count += 1
                else:
                    # Function returned successfully
                    return True, result

            except Exception as e:
                # Handle unexpected exceptions
                error_data = {'error': str(e)}
                error_info = self.handle_error(error_data, attempt_count=attempt_count)
                if error_info.get('should_retry'):
                    error_type_value = error_info.get('error_type', ErrorType.UNKNOWN.value)
                    error_enum = ErrorType(error_type_value) if error_type_value in ErrorType._value2member_map_ else ErrorType.UNKNOWN
                    error_info['backoff_time'] = self.calculate_backoff(attempt_count, error_enum)

                failure_payload = _format_failure_payload(error_info, error_data, attempt_count)
                last_error_info = error_info
                last_raw_error = error_data

                if not error_info['should_retry']:
                    return False, failure_payload
                else:
                    backoff_time = error_info.get('backoff_time', self.base_backoff)
                    logger.info(f"Retrying after exception: {backoff_time}s (attempt {attempt_count + 1}/{max_attempts})")
                    time.sleep(backoff_time)
                    attempt_count += 1

        # All attempts exhausted
        if last_error_info is not None:
            exhausted_payload = _format_failure_payload(
                last_error_info,
                last_raw_error,
                max(attempt_count - 1, 0),
                override_retry=False
            )
            exhausted_payload['retry']['will_retry'] = False
            exhausted_payload['retry']['attempt'] = max_attempts
            return False, exhausted_payload

        fallback_message = self._sanitize_error_message(
            f"Operation failed after {max_attempts} attempts"
        )
        return False, {
            'error': fallback_message,
            'retry': {
                'attempt': max_attempts,
                'max_attempts': max_attempts,
                'will_retry': False
            }
        }
