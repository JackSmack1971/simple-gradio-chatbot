# tests/unit/test_events.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import uuid
import time
from datetime import datetime

from src.utils.events import (
    Event, EventBus, EventType, EventPriority,
    publish_event, publish_event_sync, event_bus
)


class TestEvent:
    def test_event_initialization(self):
        """Test Event initialization."""
        event_type = EventType.USER_INPUT
        data = {"input": "hello"}
        priority = EventPriority.HIGH
        source = "test_source"
        correlation_id = "test_corr_123"

        with patch('src.utils.events.uuid') as mock_uuid, \
             patch('src.utils.events.datetime') as mock_datetime:

            mock_uuid.uuid4.return_value.hex = "abcd1234"
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00.000000"

            event = Event(event_type, data, priority, source, correlation_id)

        assert event.event_type == event_type
        assert event.data == data
        assert event.priority == priority
        assert event.source == source
        assert event.correlation_id == correlation_id
        assert event.timestamp == "2024-01-01T12:00:00.000000"
        assert event.id == "evt_abcd1234"

    def test_event_initialization_default_values(self):
        """Test Event initialization with default values."""
        event_type = EventType.API_RESPONSE
        data = {"response": "ok"}

        with patch('src.utils.events.uuid') as mock_uuid, \
             patch('src.utils.events.datetime') as mock_datetime:

            mock_uuid.uuid4.return_value.hex = "efgh5678"
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00.000000"

            event = Event(event_type, data)

        assert event.priority == EventPriority.NORMAL
        assert event.source == "unknown"
        assert event.correlation_id == "corr_efgh5678"  # Generated correlation ID

    def test_generate_event_id(self):
        """Test event ID generation."""
        event = Event(EventType.USER_INPUT, {})

        with patch('src.utils.events.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value.hex = "testid123"

            event_id = event._generate_event_id()

        assert event_id == "evt_testid123"

    def test_generate_correlation_id(self):
        """Test correlation ID generation."""
        event = Event(EventType.USER_INPUT, {})

        with patch('src.utils.events.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value.hex = "corrid456"

            corr_id = event._generate_correlation_id()

        assert corr_id == "corr_corrid456"

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event_type = EventType.STATE_CHANGE
        data = {"old_state": {}, "new_state": {"status": "active"}}
        priority = EventPriority.CRITICAL
        source = "state_manager"
        correlation_id = "corr_test123"

        with patch('src.utils.events.uuid') as mock_uuid, \
             patch('src.utils.events.datetime') as mock_datetime:

            mock_uuid.uuid4.return_value.hex = "eventid789"
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00.000000"

            event = Event(event_type, data, priority, source, correlation_id)

        event_dict = event.to_dict()

        expected = {
            'id': 'evt_eventid789',
            'type': 'state_change',
            'data': data,
            'priority': 4,  # CRITICAL value
            'source': source,
            'correlation_id': correlation_id,
            'timestamp': '2024-01-01T12:00:00.000000'
        }
        assert event_dict == expected


class TestEventBus:
    @pytest.fixture
    def event_bus_instance(self):
        """Create a fresh EventBus instance for testing."""
        return EventBus(drain_timeout=0.05)

    def test_initialization(self, event_bus_instance):
        """Test EventBus initialization."""
        assert isinstance(event_bus_instance._subscribers, dict)
        assert isinstance(event_bus_instance._async_subscribers, dict)
        assert isinstance(event_bus_instance._event_queue, asyncio.Queue)
        assert event_bus_instance._processing_task is None
        assert event_bus_instance._is_running is False
        assert isinstance(event_bus_instance._stats, dict)

    @pytest.mark.asyncio
    async def test_start_stop(self, event_bus_instance):
        """Test starting and stopping the event bus."""
        await event_bus_instance.start()
        assert event_bus_instance._is_running is True
        assert event_bus_instance._processing_task is not None

        await event_bus_instance.stop()
        assert event_bus_instance._is_running is False
        assert event_bus_instance._processing_task is None

    @pytest.mark.asyncio
    async def test_start_when_already_running(self, event_bus_instance):
        """Test starting an already running event bus."""
        await event_bus_instance.start()
        assert event_bus_instance._is_running is True

        # Should not raise exception
        await event_bus_instance.start()
        assert event_bus_instance._is_running is True

        await event_bus_instance.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, event_bus_instance):
        """Test stopping a non-running event bus."""
        assert event_bus_instance._is_running is False

        # Should not raise exception
        await event_bus_instance.stop()

    def test_subscribe(self, event_bus_instance):
        """Test subscribing to events."""
        callback = Mock()
        event_type = EventType.USER_INPUT

        event_bus_instance.subscribe(event_type, callback)

        assert event_type in event_bus_instance._subscribers
        assert callback in event_bus_instance._subscribers[event_type]

    def test_subscribe_async(self, event_bus_instance):
        """Test subscribing to events asynchronously."""
        callback = AsyncMock()
        event_type = EventType.API_RESPONSE

        event_bus_instance.subscribe_async(event_type, callback)

        assert event_type in event_bus_instance._async_subscribers
        assert callback in event_bus_instance._async_subscribers[event_type]

    def test_unsubscribe(self, event_bus_instance):
        """Test unsubscribing from events."""
        callback = Mock()
        event_type = EventType.USER_INPUT

        event_bus_instance.subscribe(event_type, callback)
        assert callback in event_bus_instance._subscribers[event_type]

        event_bus_instance.unsubscribe(event_type, callback)
        assert callback not in event_bus_instance._subscribers[event_type]

    def test_unsubscribe_nonexistent(self, event_bus_instance):
        """Test unsubscribing non-existent callback."""
        callback = Mock()
        event_type = EventType.USER_INPUT

        # Should not raise exception
        event_bus_instance.unsubscribe(event_type, callback)

    def test_unsubscribe_async(self, event_bus_instance):
        """Test unsubscribing from async events."""
        callback = AsyncMock()
        event_type = EventType.API_RESPONSE

        event_bus_instance.subscribe_async(event_type, callback)
        assert callback in event_bus_instance._async_subscribers[event_type]

        event_bus_instance.unsubscribe(event_type, callback)
        assert callback not in event_bus_instance._async_subscribers[event_type]

    @pytest.mark.asyncio
    async def test_publish(self, event_bus_instance):
        """Test publishing an event."""
        event = Event(EventType.USER_INPUT, {"input": "test"})

        await event_bus_instance.publish(event)

        assert event_bus_instance._stats['events_published'] == 1
        assert event_bus_instance._event_queue.qsize() == 1

    def test_publish_sync_with_running_loop(self, event_bus_instance):
        """Test synchronous publishing with running event loop."""
        event = Event(EventType.USER_INPUT, {"input": "test"})

        with patch('asyncio.get_event_loop') as mock_loop, \
             patch('asyncio.create_task') as mock_create_task:

            mock_loop.return_value.is_running.return_value = True

            event_bus_instance.publish_sync(event)

            mock_create_task.assert_called_once()

    def test_publish_sync_without_running_loop(self, event_bus_instance):
        """Test synchronous publishing without running event loop."""
        event = Event(EventType.USER_INPUT, {"input": "test"})

        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No loop")), \
             patch('asyncio.run') as mock_run:

            event_bus_instance.publish_sync(event)

            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_processing(self, event_bus_instance):
        """Test event processing loop."""
        processed_event = asyncio.Event()
        callback = Mock()

        def on_event(event_arg):
            processed_event.set()

        callback.side_effect = on_event
        event_type = EventType.USER_INPUT
        event = Event(event_type, {"input": "test"})

        event_bus_instance.subscribe(event_type, callback)

        # Start processing
        await event_bus_instance.start()

        # Publish event
        await event_bus_instance.publish(event)

        # Wait for the callback to be invoked
        await asyncio.wait_for(processed_event.wait(), timeout=0.5)

        # Stop processing
        await event_bus_instance.stop()

        # Callback should have been called
        callback.assert_called_once_with(event)
        assert event_bus_instance._stats['events_processed'] == 1

    @pytest.mark.asyncio
    async def test_event_processing_with_async_subscriber(self, event_bus_instance):
        """Test event processing with async subscriber."""
        processed_event = asyncio.Event()

        async def handler(event_arg):
            processed_event.set()

        callback = AsyncMock(side_effect=handler)
        event_type = EventType.API_RESPONSE
        event = Event(event_type, {"response": "ok"})

        event_bus_instance.subscribe_async(event_type, callback)

        await event_bus_instance.start()
        await event_bus_instance.publish(event)
        await asyncio.wait_for(processed_event.wait(), timeout=0.5)
        await event_bus_instance.stop()

        callback.assert_awaited_once_with(event)
        assert event_bus_instance._stats['events_processed'] == 1

    @pytest.mark.asyncio
    async def test_event_processing_callback_exception(self, event_bus_instance):
        """Test event processing when callback raises exception."""
        processed_event = asyncio.Event()

        def failing_callback(event_arg):
            processed_event.set()
            raise Exception("Callback error")

        callback = Mock(side_effect=failing_callback)
        event_type = EventType.ERROR
        event = Event(event_type, {"error": "test"})

        event_bus_instance.subscribe(event_type, callback)

        await event_bus_instance.start()
        await event_bus_instance.publish(event)
        await asyncio.wait_for(processed_event.wait(), timeout=0.5)
        await event_bus_instance.stop()

        callback.assert_called_once_with(event)
        assert event_bus_instance._stats['events_failed'] == 1

    @pytest.mark.asyncio
    async def test_event_processing_timeout(self, event_bus_instance):
        """Test event processing timeout handling."""
        processed_event = asyncio.Event()

        async def timeout_get(*args, **kwargs):
            processed_event.set()
            raise asyncio.TimeoutError

        # Mock queue.get to timeout and ensure the processing loop continues
        with patch.object(
            event_bus_instance._event_queue,
            'get',
            AsyncMock(side_effect=timeout_get)
        ):
            await event_bus_instance.start()
            await asyncio.wait_for(processed_event.wait(), timeout=0.5)
            await event_bus_instance.stop()

    @pytest.mark.asyncio
    async def test_stop_returns_quickly_when_queue_get_timeouts(self, event_bus_instance):
        """Ensure stop completes promptly when queue.get repeatedly times out."""
        processed_event = asyncio.Event()

        async def timeout_get(*args, **kwargs):
            processed_event.set()
            raise asyncio.TimeoutError

        with patch.object(
            event_bus_instance._event_queue,
            'get',
            AsyncMock(side_effect=timeout_get)
        ):
            await event_bus_instance.start()
            await asyncio.wait_for(processed_event.wait(), timeout=0.5)
            stop_task = asyncio.create_task(event_bus_instance.stop())
            await asyncio.wait_for(stop_task, timeout=0.2)

    @pytest.mark.asyncio
    async def test_stop_handles_queue_join_timeout(self, event_bus_instance):
        """Ensure stop handles queue.join raising TimeoutError without delay."""
        processed_event = asyncio.Event()

        async def timeout_get(*args, **kwargs):
            processed_event.set()
            raise asyncio.TimeoutError

        async def join_timeout():
            raise asyncio.TimeoutError

        with patch.object(
            event_bus_instance._event_queue,
            'get',
            AsyncMock(side_effect=timeout_get)
        ), patch.object(
            event_bus_instance._event_queue,
            'join',
            AsyncMock(side_effect=join_timeout)
        ):
            await event_bus_instance.start()
            await asyncio.wait_for(processed_event.wait(), timeout=0.5)
            stop_task = asyncio.create_task(event_bus_instance.stop())
            await asyncio.wait_for(stop_task, timeout=0.2)

    @pytest.mark.asyncio
    async def test_safe_call_async_success(self, event_bus_instance):
        """Test safe async callback calling."""
        callback = AsyncMock()
        event = Event(EventType.USER_INPUT, {"input": "test"})

        await event_bus_instance._safe_call_async(callback, event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_safe_call_async_exception(self, event_bus_instance):
        """Test safe async callback calling with exception."""
        callback = AsyncMock(side_effect=Exception("Async error"))
        event = Event(EventType.USER_INPUT, {"input": "test"})

        with pytest.raises(Exception, match="Async error"):
            await event_bus_instance._safe_call_async(callback, event)

        callback.assert_called_once_with(event)
        assert event_bus_instance._stats['events_failed'] == 1

    def test_get_stats(self, event_bus_instance):
        """Test getting event processing statistics."""
        event_bus_instance._stats = {
            'events_published': 10,
            'events_processed': 8,
            'events_failed': 2,
            'processing_time_avg': 1.5
        }

        # Mock queue size
        with patch.object(event_bus_instance._event_queue, 'qsize', return_value=3):
            stats = event_bus_instance.get_stats()

        expected = {
            'events_published': 10,
            'events_processed': 8,
            'events_failed': 2,
            'processing_time_avg': 1.5,
            'queue_size': 3,
            'subscriber_count': 0,
            'async_subscriber_count': 0
        }
        assert stats == expected

    @pytest.mark.asyncio
    async def test_wait_for_empty_queue_success(self, event_bus_instance):
        """Test waiting for empty queue successfully."""
        result = await event_bus_instance.wait_for_empty_queue(timeout=0.1)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_empty_queue_timeout(self, event_bus_instance):
        """Test waiting for empty queue with timeout."""
        # Add an event to the queue
        event = Event(EventType.USER_INPUT, {"input": "test"})
        await event_bus_instance._event_queue.put(event)

        # Wait should timeout since event won't be processed
        result = await event_bus_instance.wait_for_empty_queue(timeout=0.1)

        assert result is False

    @pytest.mark.asyncio
    async def test_processing_time_calculation(self, event_bus_instance):
        """Test processing time average calculation."""
        callback = Mock()
        event_type = EventType.USER_INPUT

        event_bus_instance.subscribe(event_type, callback)

        # Mock time to control processing time
        real_time = time.time
        base_time = real_time()
        schedule = {
            0: base_time,
            1: base_time + 0.5,
            2: base_time + 2.0,
            3: base_time + 2.2,
        }
        call_count = {
            'count': 0
        }

        def time_side_effect():
            index = call_count['count']
            call_count['count'] += 1
            return schedule.get(index, real_time())

        event1 = Event(event_type, {"input": "test1"})
        event2 = Event(event_type, {"input": "test2"})

        with patch('time.time', side_effect=time_side_effect):
            await event_bus_instance._handle_event(event1)
            await event_bus_instance._handle_event(event2)

        # Check processing times: 0.5s first, 0.2s second, average = (0.5 + 0.2) / 2 = 0.35
        assert event_bus_instance._stats['events_processed'] == 2
        assert abs(event_bus_instance._stats['processing_time_avg'] - 0.35) < 0.01

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(self, event_bus_instance):
        """Test multiple subscribers for the same event type."""
        callback1 = Mock()
        callback2 = Mock()
        event_type = EventType.STATE_CHANGE

        event_bus_instance.subscribe(event_type, callback1)
        event_bus_instance.subscribe(event_type, callback2)

        event = Event(event_type, {"state": "changed"})

        # Simulate handling (normally done in _handle_event)
        await event_bus_instance._handle_event(event)

        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_handle_event_sync_failure_increments_stats(self, event_bus_instance):
        """Ensure sync handler failures increment stats and propagate."""
        callback = Mock(side_effect=Exception("Callback boom"))
        event_type = EventType.ERROR
        event = Event(event_type, {"error": "boom"})

        event_bus_instance.subscribe(event_type, callback)

        with pytest.raises(Exception, match="Callback boom"):
            await event_bus_instance._handle_event(event)

        assert event_bus_instance._stats['events_failed'] == 1
        assert event_bus_instance._stats['events_processed'] == 0

    @pytest.mark.asyncio
    async def test_handle_event_async_failure_increments_stats(self, event_bus_instance):
        """Ensure async handler failures increment stats and propagate."""
        callback = AsyncMock(side_effect=Exception("Async boom"))
        event_type = EventType.API_RESPONSE
        event = Event(event_type, {"response": "boom"})

        event_bus_instance.subscribe_async(event_type, callback)

        with pytest.raises(Exception, match="Async boom"):
            await event_bus_instance._handle_event(event)

        assert event_bus_instance._stats['events_failed'] == 1
        assert event_bus_instance._stats['events_processed'] == 0

    @pytest.mark.asyncio
    async def test_async_subscriber_exception_handling(self, event_bus_instance):
        """Test that async subscriber exceptions are recorded."""
        first_callback_triggered = asyncio.Event()
        second_callback_triggered = asyncio.Event()

        async def failing_callback(event_arg):
            first_callback_triggered.set()
            raise Exception("Async error")

        async def successful_callback(event_arg):
            second_callback_triggered.set()

        callback1 = AsyncMock(side_effect=failing_callback)
        callback2 = AsyncMock(side_effect=successful_callback)
        event_type = EventType.API_RESPONSE

        event_bus_instance.subscribe_async(event_type, callback1)
        event_bus_instance.subscribe_async(event_type, callback2)

        await event_bus_instance.start()
        await event_bus_instance.publish(Event(event_type, {"response": "test"}))
        await asyncio.wait_for(
            asyncio.gather(
                first_callback_triggered.wait(),
                second_callback_triggered.wait()
            ),
            timeout=0.5
        )
        await event_bus_instance.stop()

        callback1.assert_awaited_once()
        callback2.assert_awaited_once()
        assert event_bus_instance._stats['events_failed'] == 1
        assert event_bus_instance._stats['events_processed'] == 0


class TestGlobalFunctions:
    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test global publish_event function."""
        event_type = EventType.USER_INPUT
        data = {"input": "hello"}
        priority = EventPriority.HIGH
        source = "test"

        with patch('src.utils.events.event_bus') as mock_bus, \
             patch('src.utils.events.Event') as mock_event_class:

            mock_event = Mock()
            mock_event_class.return_value = mock_event

            mock_bus.publish = AsyncMock()

            await publish_event(event_type, data, priority, source)

            mock_event_class.assert_called_once_with(event_type, data, priority, source)
            mock_bus.publish.assert_awaited_once_with(mock_event)

    def test_publish_event_sync(self):
        """Test global publish_event_sync function."""
        event_type = EventType.API_RESPONSE
        data = {"response": "ok"}
        priority = EventPriority.NORMAL
        source = "api"

        with patch('src.utils.events.event_bus') as mock_bus, \
             patch('src.utils.events.Event') as mock_event_class:

            mock_event = Mock()
            mock_event_class.return_value = mock_event

            publish_event_sync(event_type, data, priority, source)

            mock_event_class.assert_called_once_with(event_type, data, priority, source)
            mock_bus.publish_sync.assert_called_once_with(mock_event)


class TestEventSystemIntegration:
    @pytest.mark.asyncio
    async def test_full_event_lifecycle(self):
        """Test complete event publishing and handling lifecycle."""
        bus = EventBus(drain_timeout=0.05)
        received_events = []
        processed_event = asyncio.Event()

        def event_handler(event):
            received_events.append(event)
            if len(received_events) == 2:
                processed_event.set()

        # Subscribe to events
        bus.subscribe(EventType.USER_INPUT, event_handler)
        bus.subscribe(EventType.API_RESPONSE, event_handler)

        # Start processing
        await bus.start()

        # Publish events
        event1 = Event(EventType.USER_INPUT, {"input": "hello"})
        event2 = Event(EventType.API_RESPONSE, {"response": "world"})

        await bus.publish(event1)
        await bus.publish(event2)

        # Wait for processing
        await asyncio.wait_for(processed_event.wait(), timeout=0.5)

        # Stop processing
        await bus.stop()

        # Verify events were received
        assert len(received_events) == 2
        assert received_events[0].event_type == EventType.USER_INPUT
        assert received_events[1].event_type == EventType.API_RESPONSE

        # Check stats
        stats = bus.get_stats()
        assert stats['events_published'] == 2
        assert stats['events_processed'] == 2
        assert stats['subscriber_count'] == 2

    def test_event_priority_enum_values(self):
        """Test EventPriority enum values."""
        assert EventPriority.LOW.value == 1
        assert EventPriority.NORMAL.value == 2
        assert EventPriority.HIGH.value == 3
        assert EventPriority.CRITICAL.value == 4

    def test_event_type_enum_values(self):
        """Test EventType enum values."""
        assert EventType.USER_INPUT.value == "user_input"
        assert EventType.API_RESPONSE.value == "api_response"
        assert EventType.STATE_CHANGE.value == "state_change"
        assert EventType.ERROR.value == "error"
        assert EventType.SYSTEM_EVENT.value == "system_event"
        assert EventType.LIFECYCLE_EVENT.value == "lifecycle_event"

    def test_event_bus_global_instance(self):
        """Test that global event_bus is an EventBus instance."""
        from src.utils.events import event_bus
        assert isinstance(event_bus, EventBus)