# tests/unit/test_api_client_manager.py
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from src.core.managers.api_client_manager import (
    APIClientManager,
    RequestState,
    REQUEST_ID_PREFIX,
    REQUEST_ID_SUFFIX_HEX_LENGTH,
    REQUEST_ID_TOTAL_LENGTH,
)
from src.external.openrouter.client import OpenRouterClient
from src.external.openrouter.rate_limiter import RateLimiter
from src.external.openrouter.error_handler import ErrorHandler
from src.core.managers.conversation_manager import ConversationManager


class TestAPIClientManager:
    @pytest.fixture
    def mock_openrouter_client(self):
        """Mock OpenRouterClient for testing."""
        return Mock(spec=OpenRouterClient)

    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock RateLimiter for testing."""
        return Mock(spec=RateLimiter)

    @pytest.fixture
    def mock_error_handler(self):
        """Mock ErrorHandler for testing."""
        mock_handler = Mock(spec=ErrorHandler)

        def passthrough(func, *args, **kwargs):
            """Simulate retry wrapper by directly invoking the provided callable."""
            return func(*args, **kwargs)

        mock_handler.execute_with_retry.side_effect = passthrough
        return mock_handler

    @pytest.fixture
    def mock_conversation_manager(self):
        """Mock ConversationManager for testing."""
        return Mock(spec=ConversationManager)

    @pytest.fixture
    def manager(self, mock_openrouter_client, mock_rate_limiter, mock_error_handler, mock_conversation_manager):
        """Create APIClientManager with mocked dependencies."""
        return APIClientManager(
            mock_openrouter_client,
            mock_rate_limiter,
            mock_error_handler,
            mock_conversation_manager
        )

    def test_initialization(self, mock_openrouter_client, mock_rate_limiter, mock_error_handler, mock_conversation_manager):
        """Test manager initialization."""
        manager = APIClientManager(
            mock_openrouter_client,
            mock_rate_limiter,
            mock_error_handler,
            mock_conversation_manager
        )

        assert manager.openrouter_client == mock_openrouter_client
        assert manager.rate_limiter == mock_rate_limiter
        assert manager.error_handler == mock_error_handler
        assert manager.conversation_manager == mock_conversation_manager
        assert isinstance(manager.active_requests, dict)
        assert isinstance(manager.request_history, list)

    def test_initialization_default_dependencies(self):
        """Test manager initialization with default dependencies."""
        with patch('src.core.managers.api_client_manager.OpenRouterClient') as mock_client_class, \
             patch('src.core.managers.api_client_manager.RateLimiter') as mock_limiter_class, \
             patch('src.core.managers.api_client_manager.ErrorHandler') as mock_handler_class, \
             patch('src.core.managers.api_client_manager.ConversationManager') as mock_manager_class:

            mock_client = Mock()
            mock_limiter = Mock()
            mock_handler = Mock()
            mock_conv_manager = Mock()

            mock_client_class.return_value = mock_client
            mock_limiter_class.return_value = mock_limiter
            mock_handler_class.return_value = mock_handler
            mock_manager_class.return_value = mock_conv_manager

            manager = APIClientManager()

            assert manager.openrouter_client == mock_client
            assert manager.rate_limiter == mock_limiter
            assert manager.error_handler == mock_handler
            assert manager.conversation_manager == mock_conv_manager

    def test_chat_completion_success(self, manager, mock_openrouter_client, mock_conversation_manager):
        """Test successful chat completion."""
        conversation_id = "test-conv-123"
        message = "Hello world!"
        model = "anthropic/claude-3-haiku"

        # Mock conversation exists
        mock_conversation_manager.get_conversation.return_value = {"id": conversation_id}
        mock_conversation_manager.add_message.return_value = True
        mock_conversation_manager.get_conversation_messages.return_value = [
            {"role": "user", "content": message}
        ]

        # Mock API response
        mock_response = {
            "choices": [{"message": {"content": "Hello! How can I help you?"}}]
        }
        mock_openrouter_client.chat_completion.return_value = (True, mock_response)

        success, response = manager.chat_completion(conversation_id, message, model)

        assert success is True
        assert response == mock_response
        mock_conversation_manager.add_message.assert_any_call(conversation_id, message, "user")
        mock_conversation_manager.add_message.assert_any_call(
            conversation_id, "Hello! How can I help you?", "assistant"
        )

    def test_chat_completion_conversation_not_found(self, manager, mock_conversation_manager):
        """Test chat completion with non-existent conversation."""
        mock_conversation_manager.get_conversation.return_value = None

        success, response = manager.chat_completion("non-existent", "Hello")

        assert success is False
        assert "not found" in response["error"]

    def test_chat_completion_add_user_message_failure(self, manager, mock_conversation_manager):
        """Test chat completion when adding user message fails."""
        conversation_id = "test-conv-123"
        mock_conversation_manager.get_conversation.return_value = {"id": conversation_id}
        mock_conversation_manager.add_message.return_value = False

        success, response = manager.chat_completion(conversation_id, "Hello")

        assert success is False
        assert "Failed to add user message" in response["error"]

    def test_chat_completion_api_failure(self, manager, mock_openrouter_client, mock_conversation_manager):
        """Test chat completion with API failure."""
        conversation_id = "test-conv-123"
        mock_conversation_manager.get_conversation.return_value = {"id": conversation_id}
        mock_conversation_manager.add_message.return_value = True
        mock_conversation_manager.get_conversation_messages.return_value = []

        mock_openrouter_client.chat_completion.return_value = (False, {"error": "API Error"})

        success, response = manager.chat_completion(conversation_id, "Hello")

        assert success is False
        assert response["error"] == "API Error"

    def test_stream_chat_completion_success(self, manager, mock_openrouter_client, mock_conversation_manager):
        """Test successful streaming chat completion."""
        conversation_id = "test-conv-123"
        message = "Hello world!"

        mock_conversation_manager.get_conversation.return_value = {"id": conversation_id}
        mock_conversation_manager.add_message.return_value = True
        mock_conversation_manager.get_conversation_messages.return_value = []

        mock_response = {
            "choices": [{"message": {"content": "Hello! How can I help?"}}]
        }
        mock_openrouter_client.chat_completion.return_value = (True, mock_response)

        success, response = manager.stream_chat_completion(conversation_id, message)

        assert success is True
        assert response == "Hello! How can I help?"

    def test_get_request_status(self, manager):
        """Test getting request status."""
        request_id = "req_test_123"
        request_data = {
            "id": request_id,
            "state": "completed",
            "created_at": datetime.now().isoformat()
        }

        manager.active_requests[request_id] = request_data

        status = manager.get_request_status(request_id)

        assert status == request_data

    def test_get_request_status_not_found(self, manager):
        """Test getting status for non-existent request."""
        status = manager.get_request_status("non-existent")

        assert status is None

    def test_list_active_requests(self, manager):
        """Test listing active requests."""
        manager.active_requests = {
            "req1": {"id": "req1", "state": "processing", "metadata": {}},
            "req2": {"id": "req2", "state": "completed", "metadata": {}}
        }

        active = manager.list_active_requests()

        assert len(active) == 2
        assert active[0]["id"] == "req1"
        assert active[1]["id"] == "req2"

    def test_generate_request_id_length_and_format(self, manager):
        """Ensure generated request IDs follow the centralized format."""
        request_id = manager._generate_request_id()

        assert request_id.startswith(REQUEST_ID_PREFIX)
        assert len(request_id) == REQUEST_ID_TOTAL_LENGTH

        # Validate hexadecimal suffix for robustness against format regressions
        suffix = request_id[len(REQUEST_ID_PREFIX):]
        assert len(suffix) == REQUEST_ID_SUFFIX_HEX_LENGTH
        int(suffix, 16)  # Will raise ValueError if suffix is not valid hex

    def test_cancel_request(self, manager):
        """Test cancelling an active request."""
        request_id = "req_test_123"
        manager._init_request_state(request_id, {"reason": "unit-test"})

        success = manager.cancel_request(request_id)

        assert success is True
        assert request_id not in manager.active_requests

    def test_cancel_request_not_found(self, manager):
        """Test cancelling non-existent request."""
        success = manager.cancel_request("non-existent")

        assert success is False

    def test_get_usage_stats(self, manager):
        """Test getting usage statistics."""
        manager.request_history = [
            {"state": "completed", "metadata": {"tokens": 100, "cost": 0.01}},
            {"state": "completed", "metadata": {"tokens": 200, "cost": 0.02}},
            {"state": "failed", "metadata": {"tokens": 50, "cost": 0.005}}
        ]

        stats = manager.get_usage_stats()

        assert stats["total_requests"] == 3
        assert stats["completed_requests"] == 2
        assert stats["failed_requests"] == 1
        assert stats["success_rate"] == 2/3
        assert stats["total_tokens"] == 350
        assert stats["total_cost"] == 0.035
        assert stats["active_requests"] == 0

    def test_validate_api_connection(self, manager, mock_openrouter_client):
        """Test API connection validation."""
        mock_openrouter_client.validate_connection.return_value = True

        result = manager.validate_api_connection()

        assert result is True
        mock_openrouter_client.validate_connection.assert_called_once()

    def test_get_available_models_success(self, manager, mock_openrouter_client):
        """Test getting available models successfully."""
        mock_models = [
            {"id": "model1", "name": "Model 1"},
            {"id": "model2", "name": "Model 2"}
        ]
        mock_openrouter_client.list_models.return_value = (True, {"data": mock_models})

        success, models = manager.get_available_models()

        assert success is True
        assert models == mock_models

    def test_get_available_models_failure(self, manager, mock_openrouter_client):
        """Test getting available models failure."""
        mock_openrouter_client.list_models.return_value = (False, {"error": "API Error"})

        success, models = manager.get_available_models()

        assert success is False
        assert models == []

    def test_cleanup(self, manager, mock_rate_limiter, mock_openrouter_client):
        """Test cleanup method."""
        manager.cleanup()

        mock_rate_limiter.shutdown.assert_called_once()
        mock_openrouter_client.close.assert_called_once()

    def test_generate_request_id(self, manager):
        """Test request ID generation."""
        request_id = manager._generate_request_id()

        assert request_id.startswith("req_")
        assert len(request_id) == 16  # "req_" + 8 hex chars

    def test_init_request_state(self, manager):
        """Test request state initialization."""
        request_id = "req_test_123"
        metadata = {"type": "chat_completion", "model": "test-model"}

        manager._init_request_state(request_id, metadata)

        assert request_id in manager.active_requests
        request_data = manager.active_requests[request_id]
        assert request_data["id"] == request_id
        assert request_data["state"] == RequestState.PENDING.value
        assert "created_at" in request_data
        assert request_data["metadata"] == metadata

    def test_update_request_state_completed(self, manager):
        """Test updating request state to completed."""
        request_id = "req_test_123"
        manager.active_requests[request_id] = {
            "id": request_id,
            "state": "processing",
            "created_at": datetime.now().isoformat(),
            "metadata": {}
        }

        manager._update_request_state(request_id, RequestState.COMPLETED, {"result": "success"})

        assert request_id not in manager.active_requests
        assert len(manager.request_history) == 1
        assert manager.request_history[0]["state"] == RequestState.COMPLETED.value
        assert manager.request_history[0]["metadata"]["result"] == "success"

    def test_update_request_state_failed(self, manager):
        """Test updating request state to failed."""
        request_id = "req_test_123"
        manager.active_requests[request_id] = {
            "id": request_id,
            "state": "processing",
            "metadata": {}
        }

        manager._update_request_state(request_id, RequestState.FAILED, {"error": "test error"})

        assert request_id not in manager.active_requests
        assert len(manager.request_history) == 1
        assert manager.request_history[0]["state"] == RequestState.FAILED.value

    def test_prepare_messages(self, manager, mock_conversation_manager):
        """Test message preparation for API."""
        conversation_id = "test-conv-123"
        messages = [
            {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi!", "timestamp": "2023-01-01T00:00:01"}
        ]

        mock_conversation_manager.get_conversation_messages.return_value = messages

        prepared = manager._prepare_messages(conversation_id)

        assert len(prepared) == 2
        assert prepared[0]["role"] == "user"
        assert prepared[0]["content"] == "Hello"
        assert prepared[1]["role"] == "assistant"
        assert prepared[1]["content"] == "Hi!"

    def test_execute_with_protection_success(self, manager, mock_error_handler):
        """Test protected execution success."""
        def test_func():
            return (True, "success")

        mock_error_handler.execute_with_retry.return_value = (True, "success")

        success, result = manager._execute_with_protection(test_func)

        assert success is True
        assert result == "success"
        mock_error_handler.execute_with_retry.assert_called_once()

    def test_simulate_streaming_response(self, manager, mock_openrouter_client):
        """Test streaming response simulation."""
        messages = [{"role": "user", "content": "Hello"}]
        model = "test-model"
        callback_count = 0

        def test_callback(chunk):
            nonlocal callback_count
            callback_count += 1

        mock_response = {
            "choices": [{"message": {"content": "Hello! How are you?"}}]
        }
        mock_openrouter_client.chat_completion.return_value = (True, mock_response)

        response = manager._simulate_streaming_response(messages, model, test_callback)

        assert response == "Hello! How are you?"
        assert callback_count > 0  # Callback should have been called
        mock_openrouter_client.chat_completion.assert_called_once_with(model, messages)