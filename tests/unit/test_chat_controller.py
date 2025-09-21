# tests/unit/test_chat_controller.py
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import time
import uuid
import threading
import types

from src.core.controllers.chat_controller import ChatController, OperationState
from src.core.processors.message_processor import MessageProcessor
from src.core.managers.conversation_manager import ConversationManager
from src.core.managers.api_client_manager import APIClientManager, APIRequestResult
from src.core.managers.state_manager import StateManager
from tests.fixtures.test_data import MOCK_CHAT_COMPLETION_RESPONSE


class TestChatController:
    @pytest.fixture
    def mock_message_processor(self):
        """Mock MessageProcessor for testing."""
        return Mock(spec=MessageProcessor)

    @pytest.fixture
    def mock_conversation_manager(self):
        """Mock ConversationManager for testing."""
        return Mock(spec=ConversationManager)

    @pytest.fixture
    def mock_api_client_manager(self):
        """Mock APIClientManager for testing."""
        return Mock(spec=APIClientManager)

    @pytest.fixture
    def mock_state_manager(self):
        """Mock StateManager for testing."""
        return Mock(spec=StateManager)

    @pytest.fixture
    def controller(self, mock_message_processor, mock_conversation_manager,
                  mock_api_client_manager, mock_state_manager):
        """Create ChatController with mocked dependencies."""
        mock_state_manager.get_application_state.return_value = {
            'current_conversation': 'conv_default',
            'conversations': {
                'conv_default': {'status': 'active'}
            }
        }
        mock_conversation_manager.get_conversation.return_value = {
            'id': 'conv_default'
        }
        return ChatController(
            message_processor=mock_message_processor,
            conversation_manager=mock_conversation_manager,
            api_client_manager=mock_api_client_manager,
            state_manager=mock_state_manager
        )

    def test_initialization_with_dependencies(self, mock_message_processor, mock_conversation_manager,
                                           mock_api_client_manager, mock_state_manager):
        """Test controller initialization with provided dependencies."""
        controller = ChatController(
            message_processor=mock_message_processor,
            conversation_manager=mock_conversation_manager,
            api_client_manager=mock_api_client_manager,
            state_manager=mock_state_manager
        )

        assert controller.message_processor == mock_message_processor
        assert controller.conversation_manager == mock_conversation_manager
        assert controller.api_client_manager == mock_api_client_manager
        assert controller.state_manager == mock_state_manager
        assert controller.current_operation is None
        assert controller.active_operations == {}
        assert isinstance(controller.operation_history, list)
        assert isinstance(controller.metrics, dict)

    def test_initialization_default_dependencies(self):
        """Test controller initialization with default dependencies."""
        with patch('src.core.controllers.chat_controller.MessageProcessor') as mock_mp_class, \
             patch('src.core.controllers.chat_controller.ConversationManager') as mock_cm_class, \
             patch('src.core.controllers.chat_controller.APIClientManager') as mock_acm_class, \
             patch('src.core.controllers.chat_controller.StateManager') as mock_sm_class:

            mock_mp = Mock()
            mock_cm = Mock()
            mock_acm = Mock()
            mock_sm = Mock()

            mock_mp_class.return_value = mock_mp
            mock_cm_class.return_value = mock_cm
            mock_acm_class.return_value = mock_acm
            mock_sm_class.return_value = mock_sm

            controller = ChatController()

            assert controller.message_processor == mock_mp
            assert controller.conversation_manager == mock_cm
            assert controller.api_client_manager == mock_acm
            assert controller.state_manager == mock_sm

    def test_process_user_message_success(self, controller, mock_message_processor,
                                        mock_conversation_manager, mock_api_client_manager,
                                        mock_state_manager):
        """Test successful user message processing."""
        user_input = "Hello, world!"
        conversation_id = "conv_test123"
        model = "anthropic/claude-3-haiku"

        # Mock validation
        mock_message_processor.validate_message.return_value = (True, "", 10)
        mock_state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        mock_conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }

        # Mock API response
        mock_api_client_manager.chat_completion.return_value = APIRequestResult(
            True,
            "req_success_123",
            MOCK_CHAT_COMPLETION_RESPONSE,
        )

        with patch('time.time', side_effect=[100.0, 101.2]), \
             patch('uuid.uuid4', return_value=MagicMock(hex='abcd1234')):

            success, response = controller.process_user_message(user_input, conversation_id, model)

        assert success is True
        assert response == MOCK_CHAT_COMPLETION_RESPONSE
        assert controller.metrics['total_operations'] == 1
        assert controller.metrics['successful_operations'] == 1
        assert controller.metrics['average_response_time'] == 1.2
        assert controller.current_operation is None  # Should be cleared after completion
        assert any(
            entry.get('metadata', {}).get('request_id') == 'req_success_123'
            for entry in controller.operation_history
        )

    def test_process_user_message_validation_failure(self, controller, mock_message_processor):
        """Test message processing with validation failure."""
        user_input = ""
        conversation_id = "conv_test123"

        mock_message_processor.validate_message.return_value = (False, "Empty message", 0)

        with patch('time.time', side_effect=[100.0, 100.5]):
            success, response = controller.process_user_message(user_input, conversation_id)

        assert success is False
        assert "Validation failed: Empty message" in response["error"]
        assert controller.metrics['total_operations'] == 1
        assert controller.metrics['failed_operations'] == 1

    def test_process_user_message_operation_in_progress(self, controller, mock_message_processor):
        """Test message processing when another operation is in progress."""
        user_input = "Hello"
        conversation_id = "conv_test123"

        # Set current operation to processing
        controller._set_operation_state(
            'op_test123',
            OperationState.PROCESSING,
            {'conversation_id': conversation_id}
        )

        mock_message_processor.validate_message.return_value = (True, "", 5)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }

        success, response = controller.process_user_message(user_input, conversation_id)

        assert success is False
        assert "Another operation is currently in progress" in response["error"]

    def test_process_user_message_api_failure(self, controller, mock_message_processor,
                                            mock_api_client_manager):
        """Test message processing with API failure."""
        user_input = "Hello"
        conversation_id = "conv_test123"

        mock_message_processor.validate_message.return_value = (True, "", 5)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }
        mock_api_client_manager.chat_completion.return_value = APIRequestResult(
            False,
            "req_failure_123",
            {"error": "API Error"},
        )

        with patch('time.time', side_effect=[100.0, 101.0]):
            success, response = controller.process_user_message(user_input, conversation_id)

        assert success is False
        assert response["error"] == "API Error"
        assert controller.metrics['failed_operations'] == 1

    def test_process_user_message_exception_handling(self, controller, mock_message_processor):
        """Test message processing with unexpected exception."""
        user_input = "Hello"
        conversation_id = "conv_test123"

        mock_message_processor.validate_message.side_effect = Exception("Unexpected error")

        with patch('time.time', side_effect=[100.0, 100.8]):
            success, response = controller.process_user_message(user_input, conversation_id)

        assert success is False
        assert "Chat processing failed: Unexpected error" in response["error"]
        assert controller.metrics['failed_operations'] == 1

    def test_start_streaming_response_success(self, controller, mock_message_processor,
                                            mock_api_client_manager):
        """Test successful streaming response."""
        user_input = "Tell me a story"
        conversation_id = "conv_test123"
        model = "anthropic/claude-3-haiku"
        full_response = "Once upon a time..."

        mock_message_processor.validate_message.return_value = (True, "", 15)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }
        mock_api_client_manager.stream_chat_completion.return_value = APIRequestResult(
            True,
            "req_stream_success",
            full_response,
        )

        success, response = controller.start_streaming_response(user_input, conversation_id, model)

        assert success is True
        assert response == full_response
        assert any(
            entry.get('metadata', {}).get('request_id') == 'req_stream_success'
            for entry in controller.operation_history
        )

    def test_start_streaming_response_validation_failure(self, controller, mock_message_processor):
        """Test streaming response with validation failure."""
        user_input = ""
        conversation_id = "conv_test123"

        mock_message_processor.validate_message.return_value = (False, "Empty input", 0)

        success, response = controller.start_streaming_response(user_input, conversation_id)

        assert success is False
        assert "Validation failed: Empty input" in response

    def test_start_streaming_response_api_failure(self, controller, mock_message_processor,
                                                mock_api_client_manager):
        """Test streaming response with API failure."""
        user_input = "Hello"
        conversation_id = "conv_test123"

        mock_message_processor.validate_message.return_value = (True, "", 5)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }
        mock_api_client_manager.stream_chat_completion.return_value = APIRequestResult(
            False,
            "req_stream_failure",
            "API Error",
        )

        success, response = controller.start_streaming_response(user_input, conversation_id)

        assert success is False
        assert response == "API Error"

    def test_cancel_current_operation_with_active_operation(self, controller, mock_api_client_manager):
        """Test cancelling an active operation."""
        controller._set_operation_state(
            'op_test123',
            OperationState.PROCESSING,
            {
                'type': 'chat_completion',
                'request_id': 'req_current_123',
                'conversation_id': 'conv_cancel_primary'
            }
        )

        result = controller.cancel_current_operation()

        assert result is True
        assert controller.current_operation['state'] == OperationState.CANCELLED
        mock_api_client_manager.cancel_request.assert_called_once_with('req_current_123')

    def test_cancel_current_operation_removes_api_manager_entry(self):
        """Simulate a live request cancellation and ensure API state is cleaned up."""
        conversation_id = "conv_cancel"
        request_registered = threading.Event()
        release_request = threading.Event()

        class BlockingOpenRouterClient:
            def chat_completion(self, model, messages, **kwargs):
                request_registered.wait()
                release_request.wait()
                return True, {
                    "choices": [{"message": {"content": "ack"}}],
                    "usage": {"total_tokens": 1},
                }

        class SimpleErrorHandler:
            def execute_with_retry(self, func, *args, **kwargs):
                return func(*args, **kwargs)

        class SimpleMessageProcessor:
            def validate_message(self, message):
                return True, "", {}

        class SimpleConversationManager:
            def __init__(self, conv_id: str):
                self.conv_id = conv_id
                self.messages = []

            def get_conversation(self, conv_id: str):
                if conv_id == self.conv_id:
                    return {'id': conv_id}
                return None

            def add_message(self, conv_id: str, content: str, role: str = "user"):
                if conv_id != self.conv_id:
                    return False
                self.messages.append({'conversation_id': conv_id, 'role': role, 'content': content})
                return True

            def get_conversation_messages(self, conv_id: str, limit: int = 50):
                return [
                    {'role': entry['role'], 'content': entry['content']}
                    for entry in self.messages
                    if entry['conversation_id'] == conv_id
                ][:limit]

        class SimpleStateManager:
            def __init__(self, conv_id: str):
                self.state = {
                    'current_conversation': conv_id,
                    'conversations': {conv_id: {'status': 'active'}},
                }

            def get_application_state(self):
                return self.state

            def update_application_state(self, updates):
                self.state.update(updates)

            def persist_state(self):
                return True

        conversation_manager = SimpleConversationManager(conversation_id)
        state_manager = SimpleStateManager(conversation_id)
        api_manager = APIClientManager(
            openrouter_client=BlockingOpenRouterClient(),
            rate_limiter=Mock(),
            error_handler=SimpleErrorHandler(),
            conversation_manager=conversation_manager,
        )

        controller = ChatController(
            message_processor=SimpleMessageProcessor(),
            conversation_manager=conversation_manager,
            api_client_manager=api_manager,
            state_manager=state_manager,
        )

        original_record = controller._record_request_id

        def record_and_signal(self, operation_id: str, request_id: str):
            original_record(operation_id, request_id)
            if request_id:
                request_registered.set()

        controller._record_request_id = types.MethodType(record_and_signal, controller)

        def run_process():
            controller.process_user_message("hello", conversation_id)

        worker = threading.Thread(target=run_process)
        worker.start()

        try:
            assert request_registered.wait(timeout=2), "Request ID was not registered in time"

            current_request_id = controller.current_operation.get('request_id')
            assert current_request_id
            assert current_request_id in api_manager.active_requests

            cancelled = controller.cancel_current_operation()

            assert cancelled is True
            assert current_request_id not in api_manager.active_requests
            assert controller.current_operation['state'] == OperationState.CANCELLED
        finally:
            release_request.set()
            worker.join(timeout=2)

    def test_cancel_current_operation_no_active_operation(self, controller):
        """Test cancelling when no operation is active."""
        controller.current_operation = None

        result = controller.cancel_current_operation()

        assert result is False

    def test_get_operation_status_with_active_operation(self, controller):
        """Test getting status of active operation."""
        controller.current_operation = {
            'id': 'op_test123',
            'state': OperationState.PROCESSING,
            'started_at': '2024-01-01T12:00:00.000000',
            'metadata': {'type': 'chat_completion'}
        }

        status = controller.get_operation_status()

        assert status is not None
        assert status['id'] == 'op_test123'
        assert status['state'] == 'processing'
        assert status['metadata'] == {'type': 'chat_completion'}

    def test_get_operation_status_no_active_operation(self, controller):
        """Test getting status when no operation is active."""
        controller.current_operation = None

        status = controller.get_operation_status()

        assert status is None

    def test_validate_chat_request_success(self, controller, mock_message_processor):
        """Test successful chat request validation."""
        user_input = "Hello, how are you?"
        model = "anthropic/claude-3-haiku"
        conversation_id = "conv_test123"

        mock_message_processor.validate_message.return_value = (True, "", 20)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }

        is_valid, error = controller.validate_chat_request(user_input, model, conversation_id)

        assert is_valid is True
        assert error == ""

    def test_validate_chat_request_invalid_message(self, controller, mock_message_processor):
        """Test validation with invalid message."""
        user_input = ""
        model = "anthropic/claude-3-haiku"

        mock_message_processor.validate_message.return_value = (False, "Message too short", 0)

        is_valid, error = controller.validate_chat_request(user_input, model)

        assert is_valid is False
        assert error == "Message too short"

    def test_validate_chat_request_invalid_model(self, controller, mock_message_processor):
        """Test validation with invalid model format."""
        user_input = "Hello"
        model = "invalid-model"

        mock_message_processor.validate_message.return_value = (True, "", 5)

        is_valid, error = controller.validate_chat_request(user_input, model)

        assert is_valid is False
        assert error == "Invalid model format"

    def test_validate_chat_request_operation_in_progress(self, controller, mock_message_processor):
        """Test validation when operation is in progress."""
        user_input = "Hello"
        model = "anthropic/claude-3-haiku"

        controller._set_operation_state(
            'op_streaming',
            OperationState.STREAMING,
            {'conversation_id': 'conv_test123'}
        )

        mock_message_processor.validate_message.return_value = (True, "", 5)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': 'conv_test123',
            'conversations': {
                'conv_test123': {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': 'conv_test123'
        }

        is_valid, error = controller.validate_chat_request(user_input, model, 'conv_test123')

        assert is_valid is False
        assert "Another operation is currently in progress" in error

    def test_validate_chat_request_no_active_conversation(self, controller, mock_message_processor):
        """Ensure validation fails when no active conversation is registered."""
        user_input = "Hello"
        model = "anthropic/claude-3-haiku"

        mock_message_processor.validate_message.return_value = (True, "", 5)
        controller.state_manager.get_application_state.return_value = {}
        controller.conversation_manager.get_conversation.return_value = None

        is_valid, error = controller.validate_chat_request(user_input, model)

        assert is_valid is False
        assert error == "No active conversation is available"

    def test_validate_chat_request_exception(self, controller, mock_message_processor):
        """Test validation with exception."""
        user_input = "Hello"
        model = "anthropic/claude-3-haiku"

        mock_message_processor.validate_message.side_effect = Exception("Validation error")

        is_valid, error = controller.validate_chat_request(user_input, model)

        assert is_valid is False
        assert "Validation error: Validation error" in error

    def test_get_performance_metrics(self, controller):
        """Test getting performance metrics."""
        controller.metrics = {
            'total_operations': 10,
            'successful_operations': 8,
            'failed_operations': 2,
            'average_response_time': 1.5,
            'total_tokens_processed': 500
        }
        controller.operation_history = [{'id': 'op1'}, {'id': 'op2'}]

        metrics = controller.get_performance_metrics()

        assert metrics['total_operations'] == 10
        assert metrics['successful_operations'] == 8
        assert metrics['average_response_time'] == 1.5
        assert metrics['current_operation'] is None  # No active operation
        assert metrics['operation_history_count'] == 2

    def test_generate_operation_id(self, controller):
        """Test operation ID generation."""
        with patch('uuid.uuid4', return_value=MagicMock(hex='abcd1234')):
            operation_id = controller._generate_operation_id()

        assert operation_id == "op_abcd1234"

    def test_set_operation_state(self, controller):
        """Test setting operation state."""
        operation_id = "op_test123"
        state = OperationState.PROCESSING
        metadata = {'type': 'chat_completion'}

        controller._set_operation_state(operation_id, state, metadata)

        assert controller.current_operation['id'] == operation_id
        assert controller.current_operation['state'] == state
        assert controller.current_operation['metadata'] == metadata
        assert operation_id in controller.current_operation['started_at']
        assert len(controller.operation_history) == 1

    def test_set_operation_state_no_metadata(self, controller):
        """Test setting operation state without metadata."""
        operation_id = "op_test123"
        state = OperationState.IDLE

        controller._set_operation_state(operation_id, state)

        assert controller.current_operation['metadata'] == {}

    def test_set_operation_state_history_limit(self, controller):
        """Test operation history size limit."""
        # Add 101 operations to exceed limit
        for i in range(101):
            controller._set_operation_state(f"op_{i}", OperationState.IDLE)

        assert len(controller.operation_history) == 100  # Should be capped at 100

    def test_update_metrics_success(self, controller):
        """Test updating metrics for successful operation."""
        controller.metrics = {
            'total_operations': 5,
            'successful_operations': 4,
            'failed_operations': 1,
            'average_response_time': 1.0,
            'total_tokens_processed': 100
        }

        response_data = {
            'usage': {'total_tokens': 25}
        }

        controller._update_metrics(True, 1.5, response_data)

        assert controller.metrics['total_operations'] == 6
        assert controller.metrics['successful_operations'] == 5
        assert controller.metrics['failed_operations'] == 1
        assert controller.metrics['average_response_time'] == pytest.approx(1.083, rel=1e-2)
        assert controller.metrics['total_tokens_processed'] == 125

    def test_update_metrics_failure(self, controller):
        """Test updating metrics for failed operation."""
        initial_metrics = controller.metrics.copy()

        controller._update_metrics(False, 2.0, None)

        assert controller.metrics['total_operations'] == initial_metrics['total_operations'] + 1
        assert controller.metrics['failed_operations'] == initial_metrics['failed_operations'] + 1
        assert controller.metrics['successful_operations'] == initial_metrics['successful_operations']

    def test_update_metrics_no_usage_data(self, controller):
        """Test updating metrics without usage data."""
        initial_tokens = controller.metrics['total_tokens_processed']

        controller._update_metrics(True, 1.0, {})

        assert controller.metrics['total_tokens_processed'] == initial_tokens

    def test_cleanup(self, controller, mock_api_client_manager, mock_state_manager):
        """Test cleanup method."""
        controller._set_operation_state(
            'op_test123',
            OperationState.PROCESSING,
            {
                'type': 'chat_completion',
                'request_id': 'req_cleanup_123',
                'conversation_id': 'conv_cleanup'
            }
        )

        controller.cleanup()

        mock_api_client_manager.cancel_request.assert_called_once_with('req_cleanup_123')
        mock_state_manager.persist_state.assert_called_once()
        assert controller.current_operation['state'] == OperationState.CANCELLED

    def test_cleanup_no_active_operation(self, controller, mock_state_manager):
        """Test cleanup with no active operation."""
        controller.current_operation = None

        controller.cleanup()

        mock_state_manager.persist_state.assert_called_once()

    def test_cleanup_exception_handling(self, controller, mock_state_manager):
        """Test cleanup with exception."""
        mock_state_manager.persist_state.side_effect = Exception("Persist error")

        # Should not raise exception
        controller.cleanup()

    def test_performance_benchmark_response_time(self, controller, mock_message_processor,
                                               mock_api_client_manager):
        """Test that response time stays under 2 seconds for performance requirement."""
        user_input = "Quick test"
        conversation_id = "conv_perf123"

        mock_message_processor.validate_message.return_value = (True, "", 10)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }
        mock_api_client_manager.chat_completion.return_value = APIRequestResult(
            True,
            "req_perf_123",
            MOCK_CHAT_COMPLETION_RESPONSE,
        )

        start_time = time.time()
        success, response = controller.process_user_message(user_input, conversation_id)
        end_time = time.time()

        processing_time = end_time - start_time

        assert success is True
        assert processing_time < 2.0  # Performance requirement: <2s response time

    def test_concurrent_operation_handling(self, controller, mock_message_processor):
        """Test handling of concurrent operations."""
        # Start first operation
        conversation_id = "conv_123"
        controller._set_operation_state(
            'op_1',
            OperationState.PROCESSING,
            {'conversation_id': conversation_id}
        )

        # Try to start second operation
        user_input = "Second message"

        mock_message_processor.validate_message.return_value = (True, "", 15)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': conversation_id
        }

        success, response = controller.process_user_message(user_input, conversation_id)

        assert success is False
        assert "Another operation is currently in progress" in response["error"]

    def test_validate_allows_parallel_conversations(self, controller, mock_message_processor):
        """Validation should permit concurrent operations for different conversations."""
        controller._set_operation_state(
            'op_conv_a',
            OperationState.PROCESSING,
            {'conversation_id': 'conv_a'}
        )

        mock_message_processor.validate_message.return_value = (True, "", 8)
        controller.state_manager.get_application_state.return_value = {
            'current_conversation': 'conv_b',
            'conversations': {
                'conv_a': {'status': 'active'},
                'conv_b': {'status': 'active'}
            }
        }
        controller.conversation_manager.get_conversation.return_value = {
            'id': 'conv_b'
        }

        is_valid, error = controller.validate_chat_request("Hi", "anthropic/claude-3-haiku", 'conv_b')

        assert is_valid is True
        assert error == ""
        assert 'conv_a' in controller.active_operations
        assert 'conv_b' not in controller.active_operations

    def test_clear_current_operation_updates_active_map(self, controller):
        """Clearing an operation should remove it from active bookkeeping."""
        controller._set_operation_state(
            'op_a',
            OperationState.PROCESSING,
            {'conversation_id': 'conv_a'}
        )
        controller._set_operation_state(
            'op_b',
            OperationState.PROCESSING,
            {'conversation_id': 'conv_b'}
        )

        # Mark conversation A as finished while conversation B stays active.
        controller._set_operation_state(
            'op_a',
            OperationState.IDLE,
            {'conversation_id': 'conv_a'}
        )
        controller._set_operation_state(
            'op_b',
            OperationState.PROCESSING,
            {'conversation_id': 'conv_b'}
        )

        controller._clear_current_operation('op_a')

        assert 'conv_a' not in controller.active_operations
        assert 'conv_b' in controller.active_operations
        assert controller.active_operations['conv_b']['id'] == 'op_b'
        assert controller.current_operation['id'] == 'op_b'

    def test_operation_state_transitions(self, controller):
        """Test proper operation state transitions."""
        operation_id = "op_test123"

        # Start processing
        controller._set_operation_state(operation_id, OperationState.PROCESSING)
        assert controller.current_operation['state'] == OperationState.PROCESSING

        # Transition to completed
        controller._set_operation_state(operation_id, OperationState.IDLE)
        assert controller.current_operation['state'] == OperationState.IDLE

    def test_metrics_calculation_edge_cases(self, controller):
        """Test metrics calculation with edge cases."""
        # Test with zero operations
        assert controller.metrics['average_response_time'] == 0.0

        # Test with first operation
        controller._update_metrics(True, 1.5, None)
        assert controller.metrics['average_response_time'] == 1.5

        # Test with second operation
        controller._update_metrics(True, 2.5, None)
        expected_avg = (1.5 + 2.5) / 2
        assert controller.metrics['average_response_time'] == expected_avg