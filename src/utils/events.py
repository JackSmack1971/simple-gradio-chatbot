# src/utils/events.py
import asyncio
import time
from typing import Dict, Any, Optional, Callable, List, Awaitable
from enum import Enum
from datetime import datetime

from .logging import logger


class EventType(Enum):
    """Types of events in the system."""
    USER_INPUT = "user_input"
    API_RESPONSE = "api_response"
    STATE_CHANGE = "state_change"
    ERROR = "error"
    SYSTEM_EVENT = "system_event"
    LIFECYCLE_EVENT = "lifecycle_event"


class EventPriority(Enum):
    """Priority levels for events."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class Event:
    """
    Represents an event in the system.

    Events are used to communicate between components and trigger state transitions,
    UI updates, and other system behaviors.
    """

    def __init__(self, event_type: EventType, data: Dict[str, Any],
                 priority: EventPriority = EventPriority.NORMAL,
                 source: str = "unknown", correlation_id: Optional[str] = None):
        """
        Initialize an event.

        Args:
            event_type: Type of the event
            data: Event data payload
            priority: Priority level of the event
            source: Source component that generated the event
            correlation_id: ID to correlate related events
        """
        self.event_type = event_type
        self.data = data
        self.priority = priority
        self.source = source
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.timestamp = datetime.now().isoformat()
        self.id = self._generate_event_id()

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import uuid
        return f"evt_{uuid.uuid4().hex[:8]}"

    def _generate_correlation_id(self) -> str:
        """Generate a correlation ID for related events."""
        import uuid
        return f"corr_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary representation.

        Returns:
            Dictionary representation of the event
        """
        return {
            'id': self.id,
            'type': self.event_type.value,
            'data': self.data,
            'priority': self.priority.value,
            'source': self.source,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp
        }


class EventBus:
    """
    Central event bus for publishing and subscribing to events.

    The EventBus manages event distribution, queuing, and processing across
    the application, supporting both synchronous and asynchronous event handling.
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._async_subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Event processing statistics
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'processing_time_avg': 0.0
        }

        logger.info("EventBus initialized")

    async def start(self) -> None:
        """Start the event processing loop."""
        if self._is_running:
            return

        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")

    async def stop(self) -> None:
        """Stop the event processing loop."""
        if not self._is_running:
            return

        self._is_running = False
        if self._processing_task:
            processing_task = self._processing_task
            processing_task.cancel()

            drain_timeout = 2.0
            waiters = []

            if not processing_task.done():
                waiters.append(processing_task)

            waiters.append(asyncio.create_task(self.wait_for_empty_queue(timeout=drain_timeout)))

            done, pending = await asyncio.wait(waiters, timeout=drain_timeout, return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

            for task in done | pending:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as exc:
                    logger.warning(f"EventBus stop wait task raised: {exc}")

            try:
                await processing_task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.warning(f"EventBus processing task raised during shutdown: {exc}")

            # Drain any leftover events to avoid dangling tasks
            drained = 0
            while True:
                try:
                    self._event_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                else:
                    drained += 1
                    self._event_queue.task_done()

            if drained:
                logger.debug(f"Drained {drained} pending events during shutdown")

        # Reset lifecycle state to allow clean restart
        self._processing_task = None
        self._event_queue = asyncio.Queue()

        logger.info("EventBus stopped")

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of events to subscribe to
            callback: Function to call when event is received
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value} events")

    def subscribe_async(self, event_type: EventType,
                       callback: Callable[[Event], Awaitable[None]]) -> None:
        """
        Subscribe to events asynchronously.

        Args:
            event_type: Type of events to subscribe to
            callback: Async function to call when event is received
        """
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []

        self._async_subscribers[event_type].append(callback)
        logger.debug(f"Subscribed asynchronously to {event_type.value} events")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Unsubscribe from events.

        Args:
            event_type: Type of events to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type.value} events")
            except ValueError:
                pass

        if event_type in self._async_subscribers:
            try:
                self._async_subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed async from {event_type.value} events")
            except ValueError:
                pass

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        self._stats['events_published'] += 1

        # Add to processing queue
        await self._event_queue.put(event)

        logger.debug(f"Published event {event.id} of type {event.event_type.value}")

    def publish_sync(self, event: Event) -> None:
        """
        Publish an event synchronously (for non-async contexts).

        Args:
            event: Event to publish
        """
        # Create a new event loop if needed
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the coroutine
                asyncio.create_task(self.publish(event))
            else:
                loop.run_until_complete(self.publish(event))
        except RuntimeError:
            # No event loop, create one
            asyncio.run(self.publish(event))

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._is_running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
                self._event_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {str(e)}")
                self._stats['events_failed'] += 1

    async def _handle_event(self, event: Event) -> None:
        """Handle a single event."""
        start_time = time.time()

        try:
            # Handle synchronous subscribers
            if event.event_type in self._subscribers:
                for callback in self._subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"Sync event handler failed: {str(e)}")

            # Handle asynchronous subscribers
            if event.event_type in self._async_subscribers:
                tasks = []
                for callback in self._async_subscribers[event.event_type]:
                    task = asyncio.create_task(self._safe_call_async(callback, event))
                    tasks.append(task)

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

            processing_time = time.time() - start_time
            self._stats['events_processed'] += 1

            # Update average processing time
            total_processed = self._stats['events_processed']
            current_avg = self._stats['processing_time_avg']
            self._stats['processing_time_avg'] = (
                (current_avg * (total_processed - 1)) + processing_time
            ) / total_processed

            logger.debug(f"Processed event {event.id} in {processing_time:.3f}s")

        except Exception as e:
            logger.error(f"Event handling failed: {str(e)}")
            self._stats['events_failed'] += 1

    async def _safe_call_async(self, callback: Callable[[Event], Awaitable[None]],
                              event: Event) -> None:
        """Safely call an async callback."""
        try:
            await callback(event)
        except Exception as e:
            logger.error(f"Async event handler failed: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event processing statistics.

        Returns:
            Dictionary with event processing statistics
        """
        return {
            **self._stats,
            'queue_size': self._event_queue.qsize(),
            'subscriber_count': sum(len(subs) for subs in self._subscribers.values()),
            'async_subscriber_count': sum(len(subs) for subs in self._async_subscribers.values())
        }

    async def wait_for_empty_queue(self, timeout: float = 5.0) -> bool:
        """
        Wait for the event queue to be empty.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if queue became empty, False if timeout occurred
        """
        try:
            await asyncio.wait_for(self._event_queue.join(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False


# Global event bus instance
event_bus = EventBus()


async def publish_event(event_type: EventType, data: Dict[str, Any],
                       priority: EventPriority = EventPriority.NORMAL,
                       source: str = "unknown") -> None:
    """
    Convenience function to publish an event.

    Args:
        event_type: Type of event to publish
        data: Event data
        priority: Event priority
        source: Event source
    """
    event = Event(event_type, data, priority, source)
    await event_bus.publish(event)


def publish_event_sync(event_type: EventType, data: Dict[str, Any],
                      priority: EventPriority = EventPriority.NORMAL,
                      source: str = "unknown") -> None:
    """
    Convenience function to publish an event synchronously.

    Args:
        event_type: Type of event to publish
        data: Event data
        priority: Event priority
        source: Event source
    """
    event = Event(event_type, data, priority, source)
    event_bus.publish_sync(event)