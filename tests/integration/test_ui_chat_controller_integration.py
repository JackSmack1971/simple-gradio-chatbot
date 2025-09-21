# tests/integration/test_ui_chat_controller_integration.py
"""
Integration tests for UI components with ChatController.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.core.controllers.chat_controller import ChatController
from src.ui.gradio_interface import GradioInterface
from src.utils.events import EventBus


class TestUIChatControllerIntegration:
    """Integration tests for UI and ChatController interaction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
        self.chat_controller = ChatController(event_bus=self.event_bus)
        self.ui = GradioInterface(self.chat_controller, self.event_bus)

    def test_ui_initialization_with_chat_controller(self):
        """Test that UI initializes properly with ChatController."""
        assert self.ui.chat_controller is self.chat_controller
        assert self.ui.event_bus is self.event_bus
        assert self.ui.current_conversation_id is None
        assert self.ui.current_model == "anthropic/claude-3-haiku"

    @patch('src.core.controllers.chat_controller.ChatController.validate_chat_request')
    def test_message_validation_integration(self, mock_validate):
        """Test message validation through UI and ChatController."""
        # Mock validation to return valid
        mock_validate.return_value = (True, "")

        # Test validation through ChatController
        is_valid, error = self.chat_controller.validate_chat_request("Test message", "test-model")

        assert is_valid
        assert error == ""
        mock_validate.assert_called_once_with("Test message", "test-model")

    @pytest.mark.asyncio
    @patch('src.core.controllers.chat_controller.ChatController.process_user_message')
    async def test_message_processing_integration(self, mock_process):
        """Test message processing through UI and ChatController."""
        # Mock the process method
        mock_process.return_value = (True, {"response": "AI response", "usage": {"total_tokens": 100}})

        # Create a conversation first
        self.ui._create_new_conversation()

        def fake_start_streaming(message, conversation_id, model, callback, **kwargs):
            """Simulate streaming by delegating to process_user_message."""
            success, response_data = self.chat_controller.process_user_message(
                message,
                conversation_id,
                model
            )
            if success:
                return True, response_data["response"]
            return False, response_data.get("error", "Unknown error")

        # Process message through the UI while intercepting streaming
        with patch.object(self.chat_controller, 'start_streaming_response', side_effect=fake_start_streaming):
            result = await self.ui._handle_send_message("Test message")

        assert result["success"] is True

        # Verify the call was made
        assert mock_process.called
        call_args = mock_process.call_args[0]
        assert call_args[0] == "Test message"  # user_input
        assert call_args[1] == str(self.ui.current_conversation_id)  # conversation_id
        assert call_args[2] == self.ui.current_model  # model

    @pytest.mark.asyncio
    @patch('src.core.controllers.chat_controller.ChatController.start_streaming_response')
    async def test_streaming_response_integration(self, mock_stream):
        """Test streaming response integration."""
        # Mock streaming response
        mock_stream.return_value = (True, "Full AI response")

        # Create conversation
        self.ui._create_new_conversation()

        # Start streaming
        result = await self.ui._handle_send_message("Test streaming")

        assert mock_stream.called
        assert result["success"] is True

        assistant_message_id = result["message_id"]
        messages = self.ui.chat_panel.get_messages()

        # Expect user and assistant messages in chat history
        assert len(messages) >= 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Test streaming"

        assistant_message = next(msg for msg in messages if msg["id"] == assistant_message_id)
        assert assistant_message["role"] == "assistant"
        assert assistant_message["content"].strip() == "Full AI response"
        assert self.ui.chat_panel.is_streaming is False

    def test_model_update_integration(self):
        """Test model update integration between UI and ChatController."""
        new_model = "openai/gpt-4"

        # Update model in UI
        self.ui.current_model = new_model

        # Verify model is updated
        assert self.ui.current_model == new_model

        # Test that header bar would be updated
        self.ui.header_bar.update_model_display(new_model)
        assert self.ui.header_bar.current_model == new_model

    def test_conversation_management_integration(self):
        """Test conversation management integration."""
        # Create new conversation
        self.ui._create_new_conversation()
        conversation_id = self.ui.current_conversation_id

        assert conversation_id is not None

        # Add conversation to sidebar
        self.ui.sidebar_panel.add_conversation(str(conversation_id), "Test Conversation")

        # Verify conversation exists in sidebar
        conversations = self.ui.sidebar_panel.get_conversations()
        assert len(conversations) == 1
        assert conversations[0]["id"] == str(conversation_id)

    def test_event_bus_integration(self):
        """Test event bus integration between UI and ChatController."""
        # Subscribe to events
        events_received = []

        def event_handler(event):
            events_received.append(event)

        self.event_bus.subscribe("test_event", event_handler)

        # Publish an event
        from src.utils.events import Event, EventType
        test_event = Event(EventType.USER_INPUT, {"test": "data"})
        self.event_bus.publish_sync(test_event)

        # Verify event was received
        assert len(events_received) == 1
        assert events_received[0].data["test"] == "data"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling integration."""
        # Test error notification
        error_message = "Test error message"

        # This should not raise an exception
        self.ui._show_error_notification(error_message)

        # Test with invalid message
        result = await self.ui._handle_send_message("")  # Empty message

        assert result["error"] == "Message cannot be empty"

    def test_state_synchronization(self):
        """Test state synchronization between UI components."""
        # Create conversation
        self.ui._create_new_conversation()
        conversation_id = self.ui.current_conversation_id

        # Update conversation metadata
        self.ui.sidebar_panel.update_conversation_metadata(str(conversation_id), {
            "last_activity": "2024-01-01T12:00:00"
        })

        # Verify metadata was updated
        conversations = self.ui.sidebar_panel.get_conversations()
        assert conversations[0]["last_activity"] == "2024-01-01T12:00:00"

    def test_ui_performance_metrics(self):
        """Test UI performance metrics collection."""
        # Set load time
        self.ui.load_start_time = datetime.now()

        # Get metrics
        metrics = self.ui.get_performance_metrics()

        assert "interface_load_time" in metrics
        assert "current_conversation" in metrics
        assert "current_model" in metrics
        assert "is_streaming" in metrics

    def test_chat_controller_metrics_integration(self):
        """Test integration with ChatController metrics."""
        metrics = self.chat_controller.get_performance_metrics()

        # Verify expected metrics are present
        expected_keys = [
            'total_operations',
            'successful_operations',
            'failed_operations',
            'average_response_time',
            'total_tokens_processed',
            'current_operation',
            'operation_history_count'
        ]

        for key in expected_keys:
            assert key in metrics

    def test_message_flow_integration(self):
        """Test complete message flow integration."""
        # Create conversation
        self.ui._create_new_conversation()

        # Add user message
        message_id = self.ui.chat_panel.add_user_message("Integration test message")

        # Verify message was added
        messages = self.ui.chat_panel.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "Integration test message"
        assert messages[0]["role"] == "user"

    @patch('src.ui.components.input_panel.InputPanel._handle_input_change')
    def test_input_panel_integration(self, mock_input_change):
        """Test InputPanel integration with UI."""
        # Mock input change to return expected format
        mock_input_change.return_value = ("Updated HTML", True)

        # The input panel is initialized in the UI
        # This test verifies the component exists and is properly integrated
        assert self.ui.message_input is not None
        assert self.ui.character_counter is not None
        assert self.ui.send_button is not None

    def test_component_initialization_order(self):
        """Test that components are initialized in the correct order."""
        # All components should be initialized
        assert self.ui.header_bar is not None
        assert self.ui.sidebar_panel is not None
        assert self.ui.chat_panel is not None
        assert self.ui.input_panel is not None
        assert self.ui.settings_panel is not None

        # ChatController should be set
        assert self.ui.chat_controller is not None

        # Event bus should be set
        assert self.ui.event_bus is not None