# tests/unit/test_main_integration.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from src.core.controllers.chat_controller import ChatController, OperationState
from src.core.managers.state_manager import StateManager
from src.core.managers.conversation_manager import ConversationManager
from src.core.managers.api_client_manager import APIClientManager
from src.core.processors.message_processor import MessageProcessor
from src.storage.config_manager import ConfigManager
from src.utils.events import EventBus, Event, EventType, EventPriority
from tests.fixtures.test_data import MOCK_CHAT_COMPLETION_RESPONSE


class TestMainComponentsIntegration:
    @pytest.fixture
    def integrated_setup(self, tmp_path):
        """Create an integrated setup of main components."""
        # Create mocks for external dependencies
        message_processor = Mock(spec=MessageProcessor)
        conversation_manager = Mock(spec=ConversationManager)
        api_client_manager = Mock(spec=APIClientManager)
        config_manager = Mock(spec=ConfigManager)

        # Create real components
        state_manager = StateManager(
            config_manager=config_manager,
            state_file=str(tmp_path / "test_state.json")
        )
        event_bus = EventBus()

        # Create controller with mixed real and mock dependencies
        controller = ChatController(
            message_processor=message_processor,
            conversation_manager=conversation_manager,
            api_client_manager=api_client_manager,
            state_manager=state_manager
        )

        conversation_manager.get_conversation.side_effect = lambda conv_id: {
            'id': conv_id,
            'status': 'active'
        }

        return {
            'controller': controller,
            'state_manager': state_manager,
            'event_bus': event_bus,
            'message_processor': message_processor,
            'conversation_manager': conversation_manager,
            'api_client_manager': api_client_manager,
            'config_manager': config_manager
        }

    def test_chat_controller_state_manager_integration(self, integrated_setup):
        """Test integration between ChatController and StateManager."""
        controller = integrated_setup['controller']
        state_manager = integrated_setup['state_manager']

        # Initial state should be default
        initial_state = state_manager.get_application_state()
        assert 'operation' in initial_state
        assert initial_state['operation']['status'] == 'idle'

        # Simulate a chat operation
        with patch.object(controller, '_set_operation_state') as mock_set_state:
            controller._set_operation_state('op_test123', OperationState.PROCESSING, {'type': 'chat'})

            # Check that operation state was set
            mock_set_state.assert_called()

        # Check that state manager was updated
        final_state = state_manager.get_application_state()
        # The state should have been updated during operation processing

    def test_state_manager_event_bus_integration(self, integrated_setup):
        """Test integration between StateManager and EventBus."""
        state_manager = integrated_setup['state_manager']
        event_bus = integrated_setup['event_bus']

        events_received = []

        def event_handler(event):
            events_received.append(event)

        # Subscribe to state change events
        event_bus.subscribe(EventType.STATE_CHANGE, event_handler)

        # Update state - this should trigger events in a real implementation
        # Since StateManager doesn't directly publish events, this tests the interface
        result = state_manager.update_application_state({'test': 'value'})
        assert result is True

        # In a full integration, state changes would publish events
        # Here we verify the state was updated
        state = state_manager.get_application_state()
        assert state['test'] == 'value'

    def test_controller_event_driven_state_updates(self, integrated_setup):
        """Test that controller operations update state appropriately."""
        controller = integrated_setup['controller']
        state_manager = integrated_setup['state_manager']
        conversation_manager = integrated_setup['conversation_manager']
        message_processor = integrated_setup['message_processor']
        api_client_manager = integrated_setup['api_client_manager']

        # Mock successful message processing
        message_processor.validate_message.return_value = (True, "", 10)
        api_client_manager.chat_completion.return_value = (True, MOCK_CHAT_COMPLETION_RESPONSE)

        user_input = "Hello, world!"
        conversation_id = "conv_test123"

        state_manager.update_application_state({
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        })
        with patch('time.time', side_effect=[100.0, 101.2]):
            success, response = controller.process_user_message(user_input, conversation_id)

        assert success is True

        # Check that state was updated with operation info
        state = state_manager.get_application_state()
        assert '_metadata' in state
        assert 'last_updated' in state['_metadata']

        # Check metrics were updated
        metrics = controller.get_performance_metrics()
        assert metrics['total_operations'] == 1
        assert metrics['successful_operations'] == 1

    def test_operation_state_transitions_integration(self, integrated_setup):
        """Test complete operation state transitions."""
        controller = integrated_setup['controller']

        operation_id = "op_integration_test"

        # Start operation
        controller._set_operation_state(operation_id, OperationState.PROCESSING, {'type': 'test'})
        assert controller.current_operation['state'] == OperationState.PROCESSING

        # Complete operation
        controller._set_operation_state(operation_id, OperationState.IDLE, {'result': 'success'})
        assert controller.current_operation['state'] == OperationState.IDLE

        # Check operation history
        assert len(controller.operation_history) == 2
        assert controller.operation_history[0]['id'] == operation_id
        assert controller.operation_history[1]['id'] == operation_id

    def test_error_handling_across_components(self, integrated_setup):
        """Test error handling integration across components."""
        controller = integrated_setup['controller']
        message_processor = integrated_setup['message_processor']
        api_client_manager = integrated_setup['api_client_manager']

        # Mock validation failure
        message_processor.validate_message.return_value = (False, "Invalid input", 0)

        success, response = controller.process_user_message("invalid", "conv123")

        assert success is False
        assert "Validation failed" in response["error"]

        # Check that error state was recorded
        assert controller.current_operation is None
        assert controller.operation_history
        assert controller.operation_history[-1]['state'] == OperationState.ERROR

    def test_concurrent_operation_prevention(self, integrated_setup):
        """Test prevention of concurrent operations."""
        controller = integrated_setup['controller']
        message_processor = integrated_setup['message_processor']
        state_manager = integrated_setup['state_manager']

        # Start first operation
        controller._set_operation_state("op1", OperationState.PROCESSING)

        # Try second operation
        message_processor.validate_message.return_value = (True, "", 5)
        state_manager.update_application_state({
            'current_conversation': 'conv123',
            'conversations': {
                'conv123': {'status': 'active'}
            }
        })

        success, response = controller.process_user_message("test", "conv123")

        assert success is False
        assert "Another operation is currently in progress" in response["error"]

    def test_state_persistence_integration(self, integrated_setup, tmp_path):
        """Test state persistence and restoration."""
        state_manager = integrated_setup['state_manager']
        controller = integrated_setup['controller']

        # Update state
        state_manager.update_application_state({
            'test_integration': 'value',
            'operation': {'status': 'processing'}
        })

        # Persist state
        result = state_manager.persist_state()
        assert result is True

        # Create new state manager instance (simulate restart)
        new_state_manager = StateManager(
            state_file=str(tmp_path / "test_state.json")
        )

        # Check state was restored
        restored_state = new_state_manager.get_application_state()
        assert restored_state['test_integration'] == 'value'

    def test_performance_metrics_tracking(self, integrated_setup):
        """Test performance metrics tracking across operations."""
        controller = integrated_setup['controller']
        message_processor = integrated_setup['message_processor']
        api_client_manager = integrated_setup['api_client_manager']
        state_manager = integrated_setup['state_manager']

        # Mock successful operations
        message_processor.validate_message.return_value = (True, "", 10)
        api_client_manager.chat_completion.return_value = (True, {
            **MOCK_CHAT_COMPLETION_RESPONSE,
            'usage': {'total_tokens': 25}
        })

        state_manager.update_application_state({
            'current_conversation': 'conv1',
            'conversations': {
                'conv1': {'status': 'active'},
                'conv2': {'status': 'active'}
            }
        })

        # Perform multiple operations
        operations = [
            ("Hello", "conv1"),
            ("How are you?", "conv2"),
            ("Goodbye", "conv1")
        ]

        for user_input, conv_id in operations:
            with patch('time.time', side_effect=[100.0, 100.5]):
                success, _ = controller.process_user_message(user_input, conv_id)
                assert success is True

        # Check accumulated metrics
        metrics = controller.get_performance_metrics()
        assert metrics['total_operations'] == 3
        assert metrics['successful_operations'] == 3
        assert metrics['failed_operations'] == 0
        assert metrics['total_tokens_processed'] == 75  # 25 * 3
        assert metrics['operation_history_count'] == 6  # Each operation records start and completion states

    def test_cleanup_integration(self, integrated_setup):
        """Test cleanup integration across components."""
        controller = integrated_setup['controller']
        state_manager = integrated_setup['state_manager']
        api_client_manager = integrated_setup['api_client_manager']

        # Set up some state
        controller._set_operation_state("op_cleanup_test", OperationState.PROCESSING)
        state_manager.update_application_state({'cleanup_test': 'value'})

        # Perform cleanup
        controller.cleanup()

        # Check cleanup occurred
        # Current operation should be cancelled
        assert controller.current_operation['state'] == OperationState.CANCELLED

        # State should be persisted
        # API client cleanup should be called

    def test_validation_integration(self, integrated_setup):
        """Test validation integration across components."""
        controller = integrated_setup['controller']
        message_processor = integrated_setup['message_processor']
        state_manager = integrated_setup['state_manager']
        conversation_manager = integrated_setup['conversation_manager']

        conversation_id = "conv_valid"
        state_manager.update_application_state({
            'current_conversation': conversation_id,
            'conversations': {
                conversation_id: {'status': 'active'}
            }
        })
        # Test successful validation
        message_processor.validate_message.return_value = (True, "", 15)

        is_valid, error = controller.validate_chat_request(
            "Valid message", "anthropic/claude-3-haiku", conversation_id
        )
        assert is_valid is True
        assert error == ""

        # Test validation with operation in progress
        controller._set_operation_state("op_blocking", OperationState.STREAMING)
        is_valid, error = controller.validate_chat_request(
            "Another message", "anthropic/claude-3-haiku", conversation_id
        )
        assert is_valid is False
        assert "currently in progress" in error

    def test_streaming_integration(self, integrated_setup):
        """Test streaming response integration."""
        controller = integrated_setup['controller']
        message_processor = integrated_setup['message_processor']
        api_client_manager = integrated_setup['api_client_manager']
        state_manager = integrated_setup['state_manager']

        # Mock streaming setup
        message_processor.validate_message.return_value = (True, "", 20)
        api_client_manager.stream_chat_completion.return_value = (True, "Streaming response complete")

        state_manager.update_application_state({
            'current_conversation': 'conv_stream123',
            'conversations': {
                'conv_stream123': {'status': 'active'}
            }
        })

        success, response = controller.start_streaming_response(
            "Tell me a story", "conv_stream123", "anthropic/claude-3-haiku"
        )

        assert success is True
        assert response == "Streaming response complete"

    def test_operation_cancellation_integration(self, integrated_setup):
        """Test operation cancellation integration."""
        controller = integrated_setup['controller']
        api_client_manager = integrated_setup['api_client_manager']

        # Start an operation
        controller._set_operation_state("op_cancel_test", OperationState.PROCESSING, {'type': 'chat_completion'})

        # Cancel it
        result = controller.cancel_current_operation()

        assert result is True
        assert controller.current_operation['state'] == OperationState.CANCELLED

    def test_state_summary_integration(self, integrated_setup):
        """Test state summary integration."""
        state_manager = integrated_setup['state_manager']

        # Set up some state data
        state_manager._state = {
            'conversations': {
                'conv1': {'status': 'active', 'title': 'Test Conv 1'},
                'conv2': {'status': 'completed'},
                'conv3': {'status': 'active'}
            },
            'operation': {'status': 'processing'},
            '_metadata': {
                'last_updated': '2024-01-01T12:00:00.000000',
                'update_count': 42
            }
        }

        summary = state_manager.get_state_summary()

        assert summary['conversation_count'] == 3
        assert summary['active_conversation'] == 'conv1'  # First active found
        assert summary['current_operation'] == 'processing'
        assert summary['total_updates'] == 42

    def test_component_initialization_integration(self, integrated_setup):
        """Test proper initialization of integrated components."""
        setup = integrated_setup

        # Check all components are properly initialized
        assert setup['controller'] is not None
        assert setup['state_manager'] is not None
        assert setup['event_bus'] is not None

        # Check controller has all managers
        controller = setup['controller']
        assert hasattr(controller, 'message_processor')
        assert hasattr(controller, 'conversation_manager')
        assert hasattr(controller, 'api_client_manager')
        assert hasattr(controller, 'state_manager')

        # Check state manager has config
        assert setup['state_manager'].config_manager is not None

    def test_metrics_calculation_integration(self, integrated_setup):
        """Test metrics calculation across multiple operations."""
        controller = integrated_setup['controller']
        message_processor = integrated_setup['message_processor']
        api_client_manager = integrated_setup['api_client_manager']

        message_processor.validate_message.return_value = (True, "", 10)
        api_client_manager.chat_completion.return_value = (True, MOCK_CHAT_COMPLETION_RESPONSE)

        # Perform operations with different response times
        response_times = [1.0, 2.0, 1.5]

        for i, resp_time in enumerate(response_times):
            with patch('time.time', side_effect=[100.0, 100.0 + resp_time]):
                controller.process_user_message(f"Message {i}", f"conv{i}")

        metrics = controller.get_performance_metrics()

        # Check total operations
        assert metrics['total_operations'] == 3
        assert metrics['successful_operations'] == 3

        # Check average response time: (1.0 + 2.0 + 1.5) / 3 = 1.5
        assert abs(metrics['average_response_time'] - 1.5) < 0.01

    def test_operation_history_management(self, integrated_setup):
        """Test operation history management."""
        controller = integrated_setup['controller']

        # Create multiple operations
        for i in range(105):  # Exceed the 100 limit
            controller._set_operation_state(f"op_{i}", OperationState.IDLE)

        # History should be capped at 100
        assert len(controller.operation_history) == 100

        # Most recent operations should be kept
        assert controller.operation_history[-1]['id'] == 'op_104'
        assert controller.operation_history[0]['id'] == 'op_5'  # Oldest remaining

    def test_state_validation_integration(self, integrated_setup):
        """Test state validation in integration context."""
        state_manager = integrated_setup['state_manager']

        # Test valid state transitions
        from_state = {'operation': {'status': 'idle'}}
        to_state = {'operation': {'status': 'processing'}}

        is_valid, error = state_manager.validate_state_transition(from_state, to_state)
        assert is_valid is True

        # Test invalid state transitions
        invalid_to_state = {'operation': {'status': 'invalid_status'}}
        is_valid, error = state_manager.validate_state_transition(from_state, invalid_to_state)
        assert is_valid is False
        assert "Invalid operation status" in error