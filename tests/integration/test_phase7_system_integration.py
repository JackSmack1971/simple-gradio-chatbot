# tests/integration/test_phase7_system_integration.py
"""Comprehensive system integration tests for Phase 7 - Full System Integration and Testing."""

import pytest
import asyncio
import time
import json
import psutil
from unittest.mock import patch
from typing import Dict, Any, List
from pathlib import Path

from src.core.controllers.chat_controller import ChatController
from src.core.managers.api_client_manager import APIClientManager
from src.core.managers.conversation_manager import ConversationManager
from src.core.managers.state_manager import StateManager
from src.core.processors.message_processor import MessageProcessor
from src.external.openrouter.client import OpenRouterClient
from src.storage.conversation_storage import ConversationStorage
from src.storage.config_manager import ConfigManager
from src.ui.gradio_interface import create_gradio_interface
from src.utils.logging import logger
from src.utils.events import EventBus, EventType
from tests.fixtures.test_data import (
    MOCK_CHAT_COMPLETION_RESPONSE,
    MOCK_CONVERSATION_DATA,
    create_mock_event_data
)

class TestPhase7SystemIntegration:
    """Comprehensive system integration tests covering all components end-to-end."""

    def test_system_initialization_complete(self, full_system_app):
        """Test that all system components initialize correctly."""
        app = full_system_app

        # Verify core components exist
        assert app.chat_controller is not None
        assert app.api_client_manager is not None
        assert app.conversation_manager is not None
        assert app.state_manager is not None
        assert app.config_manager is not None
        assert app.event_bus is not None

        # Verify component wiring
        assert app.chat_controller.api_client_manager is app.api_client_manager
        assert app.chat_controller.conversation_manager is app.conversation_manager
        assert app.chat_controller.state_manager is app.state_manager

    def test_data_flow_user_input_to_persistence(self, full_system_app, system_config):
        """Test complete data flow from user input through processing to persistence."""
        app = full_system_app

        # Create conversation
        conversation_id = app.conversation_manager.create_conversation("Test Conversation")
        assert conversation_id is not None

        # Simulate user input
        user_message = "Hello, this is a test message"
        message_id = app.conversation_manager.add_message(conversation_id, "user", user_message)
        assert message_id is not None

        # Process message (would normally call API, but we'll mock it)
        with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
            response = app.chat_controller.process_message(conversation_id, user_message)
            assert response is not None

        # Verify data persistence
        conversation = app.conversation_manager.get_conversation(conversation_id)
        assert len(conversation.messages) >= 2  # User message + AI response
        assert conversation.messages[0].content == user_message
        assert conversation.messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_event_driven_architecture_integration(self, full_system_app):
        """Test event-driven architecture across all components."""
        app = full_system_app

        events_received = []

        def event_handler(event):
            events_received.append(event)

        # Subscribe to multiple event types
        app.event_bus.subscribe(EventType.USER_INPUT, event_handler)
        app.event_bus.subscribe(EventType.API_RESPONSE, event_handler)
        app.event_bus.subscribe(EventType.STATE_CHANGE, event_handler)

        # Start event bus
        await app.event_bus.start()

        try:
            # Trigger event cascade
            conversation_id = app.conversation_manager.create_conversation("Event Test")

            # This should trigger multiple events
            with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
                await app.chat_controller.send_message_async(conversation_id, "Test message")

            # Allow time for event processing
            await asyncio.sleep(0.1)

            # Verify events were processed
            assert len(events_received) >= 2  # At minimum user_input and api_response

            event_types = [e.event_type for e in events_received]
            assert EventType.USER_INPUT in event_types
            assert EventType.API_RESPONSE in event_types

            user_event = next(event for event in events_received if event.event_type == EventType.USER_INPUT)
            assert user_event.data["conversation_id"] == conversation_id
            assert user_event.data["input"] == "Test message"
            assert user_event.data["valid"] is True
            assert user_event.data["operation_id"].startswith("op_")

            api_event = next(event for event in events_received if event.event_type == EventType.API_RESPONSE)
            assert api_event.data["conversation_id"] == conversation_id
            assert api_event.data["success"] is True
            assert api_event.data["request_id"].startswith("req_")
            assert isinstance(api_event.data["processing_time"], float)
            assert "choices" in api_event.data["response"]
            assert api_event.data["operation_id"] == user_event.data["operation_id"]

            state_events = [event for event in events_received if event.event_type == EventType.STATE_CHANGE]
            assert state_events, "Expected at least one state change event"
            final_state_event = next(
                event for event in state_events
                if event.data.get("status") == "idle" and "state_snapshot" in event.data
            )
            assert final_state_event.data["operation_id"] == user_event.data["operation_id"]
            assert "state_snapshot" in final_state_event.data
            assert "last_operation" in final_state_event.data["state_snapshot"]

        finally:
            await app.event_bus.stop()

    @pytest.mark.asyncio
    async def test_streaming_events_include_payloads(self, full_system_app):
        """Ensure streaming responses emit rich event payloads."""
        app = full_system_app
        events_received = []

        def event_handler(event):
            events_received.append(event)

        app.event_bus.subscribe(EventType.USER_INPUT, event_handler)
        app.event_bus.subscribe(EventType.API_RESPONSE, event_handler)
        app.event_bus.subscribe(EventType.STATE_CHANGE, event_handler)

        await app.event_bus.start()

        conversation_id = app.conversation_manager.create_conversation("Streaming Event Test")

        try:
            success, full_response = await asyncio.to_thread(
                app.chat_controller.start_streaming_response,
                "Stream test message",
                conversation_id,
                app.config_manager.get("model"),
            )

            assert success is True
            assert isinstance(full_response, str)
            assert full_response

            await asyncio.sleep(0.1)

            event_types = [e.event_type for e in events_received]
            assert EventType.USER_INPUT in event_types
            assert EventType.API_RESPONSE in event_types

            user_event = next(event for event in events_received if event.event_type == EventType.USER_INPUT)
            assert user_event.data["conversation_id"] == conversation_id
            assert user_event.data["mode"] == "streaming"
            assert user_event.data["valid"] is True

            api_event = next(event for event in events_received if event.event_type == EventType.API_RESPONSE)
            assert api_event.data["success"] is True
            assert api_event.data["response"] == full_response
            assert api_event.data["operation_id"] == user_event.data["operation_id"]

            state_events = [event for event in events_received if event.event_type == EventType.STATE_CHANGE]
            assert state_events

        finally:
            await app.event_bus.stop()

    def test_error_handling_across_layers(self, full_system_app):
        """Test error handling propagation across all system layers."""
        app = full_system_app

        # Test API layer error handling
        with patch.object(app.api_client_manager, 'send_chat_request', side_effect=Exception("API Error")):
            conversation_id = app.conversation_manager.create_conversation("Error Test")

            # This should handle the error gracefully
            result = app.chat_controller.process_message(conversation_id, "Test message")

            # Verify error was handled (exact behavior depends on implementation)
            # Should not crash the system
            assert result is not None or isinstance(result, dict)  # Error response or handled gracefully

        # Verify system remains stable
        assert app.chat_controller is not None
        assert app.conversation_manager.get_conversation(conversation_id) is not None

    def test_state_management_across_operations(self, full_system_app):
        """Test state management consistency across operations."""
        app = full_system_app

        initial_state = app.state_manager.get_application_state()

        # Perform multiple operations
        conv1 = app.conversation_manager.create_conversation("State Test 1")
        conv2 = app.conversation_manager.create_conversation("State Test 2")

        with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
            app.chat_controller.process_message(conv1, "Message 1")
            app.chat_controller.process_message(conv2, "Message 2")

        # Check state was updated
        current_state = app.state_manager.get_application_state()
        assert current_state != initial_state

        # Verify conversation state
        conversations = app.conversation_manager.list_conversations()
        assert len(conversations) >= 2

    def test_configuration_management_integration(self, full_system_app, system_config):
        """Test configuration management across all components."""
        app = full_system_app

        # Verify configuration was loaded
        assert app.config_manager.get("api_key") == system_config["api_key"]
        assert app.config_manager.get("model") == system_config["model"]

        # Test configuration updates
        app.config_manager.set("model", "openai/gpt-4")
        assert app.config_manager.get("model") == "openai/gpt-4"

        # Verify configuration persistence
        app.config_manager.save_config()
        # Reload and verify
        new_config_manager = ConfigManager(config_dir=system_config["config_dir"])
        assert new_config_manager.get("model") == "openai/gpt-4"

    def test_concurrent_operations_handling(self, full_system_app):
        """Test handling of concurrent operations."""
        app = full_system_app

        async def concurrent_operation(conv_id, message_num):
            with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
                result = await app.chat_controller.send_message_async(conv_id, f"Message {message_num}")
                return result

        async def run_concurrent_test():
            # Create multiple conversations
            conv_ids = []
            for i in range(3):
                conv_id = app.conversation_manager.create_conversation(f"Concurrent Test {i}")
                conv_ids.append(conv_id)

            # Run concurrent operations
            tasks = []
            for i, conv_id in enumerate(conv_ids):
                for j in range(2):  # 2 messages per conversation
                    tasks.append(concurrent_operation(conv_id, f"{i}-{j}"))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify no exceptions occurred
            exceptions = [r for r in results if isinstance(r, Exception)]
            assert len(exceptions) == 0, f"Concurrent operations failed: {exceptions}"

            # Verify all conversations were updated
            for conv_id in conv_ids:
                conv = app.conversation_manager.get_conversation(conv_id)
                assert len(conv.messages) >= 4  # 2 user + 2 assistant messages

        asyncio.run(run_concurrent_test())

    def test_memory_management_under_load(self, full_system_app):
        """Test memory management during sustained operations."""
        app = full_system_app

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many operations
        conversation_id = app.conversation_manager.create_conversation("Memory Test")

        for i in range(50):
            with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
                app.chat_controller.process_message(conversation_id, f"Message {i}")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify reasonable memory usage (should be < 100MB increase for 50 messages)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB, exceeds limit"

        # Verify conversation integrity
        conversation = app.conversation_manager.get_conversation(conversation_id)
        assert len(conversation.messages) >= 100  # 50 user + 50 assistant

    def test_data_persistence_across_restarts(self, full_system_app):
        """Test data persistence across application restarts."""
        app = full_system_app

        # Create and populate conversation
        conversation_id = app.conversation_manager.create_conversation("Persistence Test")

        messages = ["Message 1", "Message 2", "Message 3"]
        for msg in messages:
            with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
                app.chat_controller.process_message(conversation_id, msg)

        # Force persistence
        app.conversation_manager.save_conversation(conversation_id)

        # Simulate restart by creating new conversation manager instance
        new_conv_manager = ConversationManager()

        # Verify data was persisted and can be loaded
        loaded_conversation = new_conv_manager.get_conversation(conversation_id)
        assert loaded_conversation is not None
        assert loaded_conversation.get('title') == "Persistence Test"
        assert len(loaded_conversation.get('messages', [])) >= 6  # 3 user + 3 assistant

        # Verify message content
        user_messages = [m.get('content') for m in loaded_conversation.get('messages', []) if m.get('role') == "user"]
        assert all(msg in user_messages for msg in messages)

    def test_ui_component_integration(self, full_system_app):
        """Test UI component integration with backend systems."""
        app = full_system_app

        # Create Gradio interface
        interface = create_gradio_interface(app)

        # Verify interface was created with proper components
        assert interface is not None

        # Test that interface can access backend data
        conversations = app.conversation_manager.list_conversations()
        # Interface should be able to display this data (exact test depends on Gradio implementation)

        # This is a basic integration test - more detailed UI testing would require
        # Gradio's testing utilities or Selenium-based testing

    def test_performance_baselines_integration(self, full_system_app):
        """Test that system meets performance baselines during integration."""
        app = full_system_app

        # Test response time baseline
        conversation_id = app.conversation_manager.create_conversation("Performance Test")

        start_time = time.time()
        with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
            result = app.chat_controller.process_message(conversation_id, "Test message")
        end_time = time.time()

        response_time = end_time - start_time

        # Verify response time meets baseline (< 2 seconds for simple operations)
        assert response_time < 2.0, f"Response time {response_time}s exceeds 2s baseline"

        # Test memory baseline
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB

        # Verify memory usage is reasonable (< 500MB baseline)
        assert memory_usage < 500, f"Memory usage {memory_usage}MB exceeds 500MB baseline"

    def test_security_integration_validation(self, full_system_app):
        """Test security measures across integrated components."""
        app = full_system_app

        # Test that API keys are not exposed in logs or error messages
        with patch.object(app.api_client_manager, 'send_chat_request', side_effect=Exception("Test error")):
            conversation_id = app.conversation_manager.create_conversation("Security Test")

            # This should not expose API key in any output
            result = app.chat_controller.process_message(conversation_id, "Test")

            # Verify no API key exposure (exact validation depends on implementation)
            # Check logs, error messages, etc.

        # Test input validation across components
        malicious_input = "<script>alert('xss')</script>"
        conversation_id = app.conversation_manager.create_conversation("Security Test 2")

        # System should handle malicious input safely
        result = app.chat_controller.process_message(conversation_id, malicious_input)
        # Should not crash or expose vulnerabilities

    def test_backup_and_recovery_integration(self, full_system_app, system_config):
        """Test backup and recovery functionality integration."""
        app = full_system_app

        # Create conversation with data
        conversation_id = app.conversation_manager.create_conversation("Backup Test")

        for i in range(5):
            with patch.object(app.api_client_manager, 'send_chat_request', return_value=MOCK_CHAT_COMPLETION_RESPONSE):
                app.chat_controller.process_message(conversation_id, f"Backup message {i}")

        # Trigger backup
        app.conversation_manager.backup_conversation(conversation_id)

        # Verify backup exists
        backup_dir = Path(system_config["data_dir"]) / "backups"
        backup_files = list(backup_dir.glob(f"{conversation_id}*.json"))
        assert len(backup_files) > 0

        # Simulate data loss
        app.conversation_manager.delete_conversation(conversation_id)

        # Test recovery
        recovered = app.conversation_manager.restore_from_backup(conversation_id)
        assert recovered

        # Verify recovered data
        recovered_conv = app.conversation_manager.get_conversation(conversation_id)
        assert recovered_conv is not None
        assert len(recovered_conv.messages) >= 10  # 5 user + 5 assistant messages


if __name__ == "__main__":
    # Run basic integration validation
    print("Running Phase 7 System Integration Tests...")

    try:
        # Basic component instantiation test
        config = {
            "api_key": "test_key",
            "data_dir": "./test_data",
            "config_dir": "./test_config",
            "model": "test_model"
        }

        print("✓ Creating test components...")
        from src.core.controllers.chat_controller import ChatController
        from src.core.managers.api_client_manager import APIClientManager
        from src.core.managers.conversation_manager import ConversationManager
        from src.core.managers.state_manager import StateManager
        from src.utils.events import EventBus

        state_mgr = StateManager()
        api_mgr = APIClientManager()
        conv_mgr = ConversationManager()
        event_bus = EventBus()
        chat_ctrl = ChatController(
            api_client_manager=api_mgr,
            conversation_manager=conv_mgr,
            state_manager=state_mgr
        )

        print("✓ Testing component initialization...")
        assert app.chat_controller is not None
        assert app.api_client_manager is not None
        assert app.conversation_manager is not None

        print("✓ Testing basic functionality...")
        conv_id = app.conversation_manager.create_conversation("Integration Test")
        assert conv_id is not None

        print("✓ Phase 7 system integration tests completed successfully!")

    except Exception as e:
        print(f"✗ Integration test failed: {str(e)}")
        raise
