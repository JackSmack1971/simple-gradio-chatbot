# tests/integration/test_phase5_integration.py
"""Integration tests for Phase 5 Application Logic Layer components."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.core.controllers.chat_controller import ChatController, OperationState
from src.core.managers.state_manager import StateManager
from src.utils.events import EventBus, Event, EventType, EventPriority
from tests.fixtures.test_data import (
    MOCK_APPLICATION_STATE,
    MOCK_CONVERSATION_DATA,
    MOCK_CHAT_COMPLETION_RESPONSE,
    create_mock_event_data
)


class TestPhase5Integration:
    """Integration tests for Phase 5 components."""

    @pytest.fixture
    def event_bus(self):
        """Create event bus for testing."""
        bus = EventBus()
        yield bus
        # Cleanup will be handled by garbage collection

    @pytest.fixture
    def state_manager(self):
        """Create state manager for testing."""
        manager = StateManager()
        yield manager
        manager.cleanup()

    @pytest.fixture
    def chat_controller(self, state_manager):
        """Create chat controller for testing."""
        controller = ChatController(state_manager=state_manager)
        yield controller
        controller.cleanup()

    def test_chat_controller_initialization(self, chat_controller):
        """Test ChatController initializes correctly."""
        assert chat_controller.message_processor is not None
        assert chat_controller.conversation_manager is not None
        assert chat_controller.api_client_manager is not None
        assert chat_controller.state_manager is not None
        assert chat_controller.current_operation is None

    def test_state_manager_initialization(self, state_manager):
        """Test StateManager initializes correctly."""
        state = state_manager.get_application_state()
        assert isinstance(state, dict)
        assert '_metadata' in state
        assert state['_metadata']['version'] == '1.0'

    def test_event_bus_initialization(self, event_bus):
        """Test EventBus initializes correctly."""
        stats = event_bus.get_stats()
        assert isinstance(stats, dict)
        assert 'events_published' in stats
        assert stats['events_published'] == 0

    @pytest.mark.asyncio
    async def test_event_publishing_and_subscribing(self, event_bus):
        """Test event publishing and subscribing."""
        received_events = []

        def event_handler(event: Event):
            received_events.append(event)

        # Subscribe to events
        event_bus.subscribe(EventType.USER_INPUT, event_handler)

        # Start event bus
        await event_bus.start()

        try:
            # Publish event
            test_data = create_mock_event_data("user_input", input="Test message")
            event = Event(EventType.USER_INPUT, test_data)
            await event_bus.publish(event)

            # Wait for processing
            await asyncio.sleep(0.1)

            # Check event was received
            assert len(received_events) == 1
            assert received_events[0].event_type == EventType.USER_INPUT
            assert received_events[0].data["input"] == "Test message"

        finally:
            await event_bus.stop()

    def test_state_manager_persistence(self, state_manager, tmp_path):
        """Test StateManager persistence functionality."""
        # Update state
        updates = {"test_key": "test_value", "nested": {"data": 123}}
        success = state_manager.update_application_state(updates)
        assert success

        # Persist state
        persist_success = state_manager.persist_state()
        assert persist_success

        # Verify state was updated
        current_state = state_manager.get_application_state()
        assert current_state["test_key"] == "test_value"
        assert current_state["nested"]["data"] == 123

    def test_chat_controller_validation(self, chat_controller):
        """Test ChatController validation methods."""
        # Test invalid request (no active conversation)
        is_valid, error = chat_controller.validate_chat_request("test", "model")
        assert not is_valid  # Should fail due to no active conversation
        assert "conversation" in error.lower()

    def test_state_manager_state_transitions(self, state_manager):
        """Test StateManager state transition validation."""
        old_state = {"status": "idle"}
        new_state = {"status": "processing"}

        is_valid, error = state_manager.validate_state_transition(old_state, new_state)
        assert is_valid
        assert error == ""

    def test_chat_controller_operation_states(self, chat_controller):
        """Test ChatController operation state management."""
        # Initial state should be idle
        status = chat_controller.get_operation_status()
        assert status is None or status.get('state') == 'idle'

        # Test operation state setting (internal method)
        chat_controller._set_operation_state("test_op", OperationState.PROCESSING, {"test": True})
        status = chat_controller.get_operation_status()
        assert status is not None
        assert status['state'] == 'processing'
        assert status['metadata']['test'] is True

    @pytest.mark.asyncio
    async def test_event_bus_performance(self, event_bus):
        """Test EventBus performance with multiple events."""
        event_count = 0

        def count_handler(event: Event):
            nonlocal event_count
            event_count += 1

        # Subscribe to events
        event_bus.subscribe(EventType.USER_INPUT, count_handler)

        # Start event bus
        await event_bus.start()

        try:
            # Publish multiple events
            for i in range(10):
                test_data = create_mock_event_data("user_input", input=f"Message {i}")
                event = Event(EventType.USER_INPUT, test_data)
                await event_bus.publish(event)

            # Wait for processing
            await asyncio.sleep(0.2)

            # Check all events were processed
            assert event_count == 10

            # Check stats
            stats = event_bus.get_stats()
            assert stats['events_published'] >= 10
            assert stats['events_processed'] >= 10

        finally:
            await event_bus.stop()

    def test_state_manager_subscriptions(self, state_manager):
        """Test StateManager subscription functionality."""
        callback_calls = []

        def state_callback(old_state, new_state):
            callback_calls.append((old_state, new_state))

        # Subscribe to state changes
        state_manager.subscribe_to_state_changes(state_callback)

        # Update state
        state_manager.update_application_state({"test": "value"})

        # Check callback was called
        assert len(callback_calls) == 1
        old_state, new_state = callback_calls[0]
        assert isinstance(old_state, dict)
        assert isinstance(new_state, dict)
        assert new_state["test"] == "value"

    def test_chat_controller_metrics(self, chat_controller):
        """Test ChatController metrics collection."""
        # Initially should have zero metrics
        metrics = chat_controller.get_performance_metrics()
        assert isinstance(metrics, dict)
        assert 'total_operations' in metrics
        assert 'successful_operations' in metrics
        assert 'average_response_time' in metrics

        # Simulate some operations (using internal methods for testing)
        chat_controller._update_metrics(True, 1.5, {"usage": {"total_tokens": 25}})
        chat_controller._update_metrics(False, 2.0, None)
        chat_controller._update_metrics(True, 1.0, {"usage": {"total_tokens": 15}})

        # Check metrics were updated
        updated_metrics = chat_controller.get_performance_metrics()
        assert updated_metrics['total_operations'] == 3
        assert updated_metrics['successful_operations'] == 2
        assert updated_metrics['failed_operations'] == 1
        assert abs(updated_metrics['average_response_time'] - 1.5) < 0.1  # Approximate

    def test_integration_chat_workflow(self, chat_controller, state_manager):
        """Test integrated chat workflow."""
        # This is a high-level integration test that would require mocking
        # the external dependencies. For now, we test the validation and setup.

        # Test that controller has access to state manager
        assert chat_controller.state_manager is state_manager

        # Test that state manager can be updated
        success = state_manager.update_application_state({
            "integration_test": True,
            "timestamp": "2024-01-01T12:00:00.000Z"
        })
        assert success

        # Verify state was updated
        current_state = state_manager.get_application_state()
        assert current_state["integration_test"] is True

    @pytest.mark.asyncio
    async def test_full_event_system_integration(self, event_bus):
        """Test full event system integration."""
        # Test event creation, publishing, and processing
        events_received = []

        async def async_handler(event: Event):
            events_received.append(event)

        def sync_handler(event: Event):
            events_received.append(event)

        # Subscribe both sync and async handlers
        event_bus.subscribe(EventType.USER_INPUT, sync_handler)
        event_bus.subscribe_async(EventType.API_RESPONSE, async_handler)

        # Start event bus
        await event_bus.start()

        try:
            # Publish different types of events
            user_event = Event(
                EventType.USER_INPUT,
                {"input": "Hello", "conversation_id": "test123"},
                EventPriority.NORMAL,
                "test_source"
            )

            api_event = Event(
                EventType.API_RESPONSE,
                {"response": MOCK_CHAT_COMPLETION_RESPONSE},
                EventPriority.HIGH,
                "api_client"
            )

            await event_bus.publish(user_event)
            await event_bus.publish(api_event)

            # Wait for processing
            await asyncio.sleep(0.2)

            # Check events were processed
            assert len(events_received) >= 2

            # Check stats
            stats = event_bus.get_stats()
            assert stats['events_published'] >= 2
            assert stats['events_processed'] >= 2

        finally:
            await event_bus.stop()


if __name__ == "__main__":
    # Run basic integration test
    print("Running Phase 5 integration tests...")

    # Simple test without pytest
    try:
        from src.core.controllers.chat_controller import ChatController
        from src.core.managers.state_manager import StateManager
        from src.utils.events import EventBus

        print("✓ Imports successful")

        # Test basic instantiation
        state_mgr = StateManager()
        chat_ctrl = ChatController(state_manager=state_mgr)
        event_bus = EventBus()

        print("✓ Component instantiation successful")

        # Test basic functionality
        state = state_mgr.get_application_state()
        assert isinstance(state, dict)
        print("✓ StateManager basic functionality works")

        metrics = chat_ctrl.get_performance_metrics()
        assert isinstance(metrics, dict)
        print("✓ ChatController basic functionality works")

        stats = event_bus.get_stats()
        assert isinstance(stats, dict)
        print("✓ EventBus basic functionality works")

        # Cleanup
        state_mgr.cleanup()
        chat_ctrl.cleanup()

        print("✓ All Phase 5 integration tests passed!")

    except Exception as e:
        print(f"✗ Integration test failed: {str(e)}")
        raise