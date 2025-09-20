# src/external/openrouter/rate_limiter.py
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from collections import deque
import heapq

from ...utils.logging import logger


class Request:
    """Represents a queued request with priority and metadata."""

    def __init__(self, func: Callable, args: tuple, kwargs: dict, priority: int = 0):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.priority = priority
        self.timestamp = time.time()
        self.id = id(self)  # Unique identifier

    def __lt__(self, other):
        # Higher priority (lower number) comes first
        # If same priority, earlier timestamp comes first
        if self.priority == other.priority:
            return self.timestamp < other.timestamp
        return self.priority < other.priority


class RateLimiter:
    """Client-side rate limiter using token bucket algorithm with request queuing."""

    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            burst_limit: Maximum burst capacity
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit

        # Token bucket state
        self.tokens = burst_limit
        self.last_refill = time.time()
        self.refill_rate = requests_per_minute / 60.0  # tokens per second

        # Request queue (priority queue)
        self.queue: List[Request] = []
        self.queue_lock = threading.Lock()

        # Model-specific rate limits
        self.model_limits: Dict[str, Dict[str, int]] = {}

        # Worker thread
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self._start_worker()

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.debug("Rate limiter worker thread started")

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.burst_limit, self.tokens + tokens_to_add)
        self.last_refill = now

    def _can_make_request(self) -> bool:
        """Check if a request can be made immediately."""
        self._refill_tokens()
        return self.tokens >= 1

    def _consume_token(self) -> None:
        """Consume one token."""
        self.tokens -= 1

    def _process_queue(self) -> None:
        """Background worker to process queued requests."""
        while not self.stop_event.is_set():
            try:
                with self.queue_lock:
                    if self.queue and self._can_make_request():
                        # Get highest priority request
                        request = heapq.heappop(self.queue)
                        self._consume_token()

                        # Execute request in a separate thread to avoid blocking
                        threading.Thread(
                            target=self._execute_request,
                            args=(request,),
                            daemon=True
                        ).start()
                    else:
                        # No requests to process or rate limited
                        pass

                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in rate limiter worker: {e}")
                time.sleep(1)  # Back off on errors

    def _execute_request(self, request: Request) -> None:
        """Execute a queued request."""
        try:
            logger.debug(f"Executing queued request {request.id}")
            request.func(*request.args, **request.kwargs)
        except Exception as e:
            logger.error(f"Error executing queued request {request.id}: {e}")

    def set_model_limit(self, model: str, requests_per_minute: int, burst_limit: Optional[int] = None) -> None:
        """
        Set rate limits for a specific model.

        Args:
            model: Model identifier
            requests_per_minute: Requests per minute for this model
            burst_limit: Burst limit for this model (defaults to requests_per_minute // 6)
        """
        if burst_limit is None:
            burst_limit = max(1, requests_per_minute // 6)

        self.model_limits[model] = {
            'requests_per_minute': requests_per_minute,
            'burst_limit': burst_limit
        }
        logger.info(f"Set rate limit for model {model}: {requests_per_minute} req/min, burst {burst_limit}")

    def get_model_limit(self, model: str) -> Dict[str, int]:
        """
        Get rate limits for a specific model.

        Args:
            model: Model identifier

        Returns:
            Dict with 'requests_per_minute' and 'burst_limit'
        """
        return self.model_limits.get(model, {
            'requests_per_minute': self.requests_per_minute,
            'burst_limit': self.burst_limit
        })

    def make_request(self, func: Callable, *args, priority: int = 0, model: Optional[str] = None, **kwargs) -> bool:
        """
        Make a rate-limited request.

        Args:
            func: Function to call
            *args: Positional arguments for the function
            priority: Request priority (lower number = higher priority)
            model: Model identifier for model-specific limits
            **kwargs: Keyword arguments for the function

        Returns:
            True if request was made immediately, False if queued
        """
        # Check if we can make the request immediately
        if self._can_make_request():
            self._consume_token()
            try:
                # Execute immediately
                threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()
                logger.debug("Request executed immediately")
                return True
            except Exception as e:
                logger.error(f"Error executing immediate request: {e}")
                return False
        else:
            # Queue the request
            request = Request(func, args, kwargs, priority)
            with self.queue_lock:
                heapq.heappush(self.queue, request)

            queue_size = len(self.queue)
            logger.debug(f"Request queued (priority {priority}), queue size: {queue_size}")

            # Log warning if queue is getting large
            if queue_size > 10:
                logger.warning(f"Request queue size is {queue_size}, consider increasing rate limits")

            return False

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.

        Returns:
            Dict with queue statistics
        """
        with self.queue_lock:
            return {
                'queue_size': len(self.queue),
                'tokens_available': self.tokens,
                'burst_limit': self.burst_limit,
                'requests_per_minute': self.requests_per_minute
            }

    def wait_for_slot(self, timeout: float = 60.0) -> bool:
        """
        Wait for a request slot to become available.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if slot became available, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._can_make_request():
                return True
            time.sleep(0.1)
        return False

    def clear_queue(self) -> int:
        """
        Clear all queued requests.

        Returns:
            Number of requests cleared
        """
        with self.queue_lock:
            cleared = len(self.queue)
            self.queue.clear()
            logger.info(f"Cleared {cleared} queued requests")
            return cleared

    def shutdown(self) -> None:
        """Shutdown the rate limiter and worker thread."""
        logger.info("Shutting down rate limiter")
        self.stop_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        logger.debug("Rate limiter shutdown complete")