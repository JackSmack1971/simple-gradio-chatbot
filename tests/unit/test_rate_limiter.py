# tests/unit/test_rate_limiter.py
import time
import pytest
from unittest.mock import Mock, patch

from src.external.openrouter.rate_limiter import RateLimiter, Request


class TestRequest:
    """Test the Request class."""

    def test_request_creation(self):
        """Test Request object creation."""
        def test_func():
            return "test"

        req = Request(test_func, (1, 2), {"key": "value"}, priority=5)

        assert req.func == test_func
        assert req.args == (1, 2)
        assert req.kwargs == {"key": "value"}
        assert req.priority == 5
        assert isinstance(req.timestamp, float)
        assert isinstance(req.id, int)

    def test_request_lt_same_priority(self):
        """Test Request comparison with same priority (earlier timestamp first)."""
        req1 = Request(lambda: None, (), {}, priority=1)
        time.sleep(0.001)  # Ensure different timestamps
        req2 = Request(lambda: None, (), {}, priority=1)

        assert req1 < req2

    def test_request_lt_different_priority(self):
        """Test Request comparison with different priorities (lower number first)."""
        req1 = Request(lambda: None, (), {}, priority=1)
        req2 = Request(lambda: None, (), {}, priority=2)

        assert req1 < req2
        assert not (req2 < req1)


class TestRateLimiter:
    """Test the RateLimiter class."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
        yield limiter
        limiter.shutdown()  # Clean up

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=30, burst_limit=5)

        assert limiter.requests_per_minute == 30
        assert limiter.burst_limit == 5
        assert limiter.tokens == 5  # Starts with burst limit
        assert limiter.queue == []
        assert limiter.worker_thread is not None  # Worker should be started

    def test_token_refill(self, rate_limiter):
        """Test token refilling over time."""
        # Use some tokens
        rate_limiter.tokens = 1
        initial_time = rate_limiter.last_refill

        # Simulate time passing (1 second)
        with patch('time.time', return_value=initial_time + 1):
            rate_limiter._refill_tokens()

        # Should have refilled tokens (60 tokens/minute = 1 token/second)
        expected_tokens = 1 + 1.0  # 1 remaining + 1 refilled
        assert rate_limiter.tokens == min(expected_tokens, rate_limiter.burst_limit)

    def test_can_make_request_with_tokens(self, rate_limiter):
        """Test can_make_request when tokens are available."""
        rate_limiter.tokens = 5
        assert rate_limiter._can_make_request() is True
        assert rate_limiter.tokens == 4  # Token consumed

    def test_can_make_request_no_tokens(self, rate_limiter):
        """Test can_make_request when no tokens available."""
        rate_limiter.tokens = 0
        assert rate_limiter._can_make_request() is False

    def test_consume_token(self, rate_limiter):
        """Test token consumption."""
        rate_limiter.tokens = 5
        rate_limiter._consume_token()
        assert rate_limiter.tokens == 4

    def test_set_model_limit(self, rate_limiter):
        """Test setting model-specific rate limits."""
        rate_limiter.set_model_limit("test-model", 30, 5)

        limits = rate_limiter.get_model_limit("test-model")
        assert limits["requests_per_minute"] == 30
        assert limits["burst_limit"] == 5

    def test_get_model_limit_default(self, rate_limiter):
        """Test getting default limits for unknown model."""
        limits = rate_limiter.get_model_limit("unknown-model")
        assert limits["requests_per_minute"] == rate_limiter.requests_per_minute
        assert limits["burst_limit"] == rate_limiter.burst_limit

    @patch('threading.Thread')
    def test_make_request_immediate(self, mock_thread, rate_limiter):
        """Test immediate request execution."""
        mock_func = Mock()
        rate_limiter.tokens = 5  # Ensure tokens available

        result = rate_limiter.make_request(mock_func, 1, 2, key="value")

        assert result is True  # Should execute immediately
        mock_thread.assert_called()  # Should start thread

    @patch('threading.Thread')
    def test_make_request_queued(self, mock_thread, rate_limiter):
        """Test request queuing when rate limited."""
        mock_func = Mock()
        rate_limiter.tokens = 0  # No tokens available

        result = rate_limiter.make_request(mock_func, priority=1)

        assert result is False  # Should be queued
        assert len(rate_limiter.queue) == 1
        mock_thread.assert_not_called()  # Should not start thread immediately

    def test_get_queue_status(self, rate_limiter):
        """Test queue status retrieval."""
        # Add some requests to queue
        rate_limiter.make_request(lambda: None, priority=1)
        rate_limiter.make_request(lambda: None, priority=2)

        status = rate_limiter.get_queue_status()

        assert status["queue_size"] == 2
        assert "tokens_available" in status
        assert "burst_limit" in status
        assert "requests_per_minute" in status

    def test_wait_for_slot_success(self, rate_limiter):
        """Test waiting for slot when tokens become available."""
        rate_limiter.tokens = 0

        # Simulate tokens becoming available after delay
        def mock_can_make_request():
            if time.time() > rate_limiter.last_refill + 0.1:
                rate_limiter.tokens = 1
                return True
            return False

        rate_limiter._can_make_request = mock_can_make_request

        result = rate_limiter.wait_for_slot(timeout=1.0)
        assert result is True

    def test_wait_for_slot_timeout(self, rate_limiter):
        """Test waiting for slot timeout."""
        rate_limiter.tokens = 0
        rate_limiter._can_make_request = lambda: False  # Never available

        result = rate_limiter.wait_for_slot(timeout=0.1)
        assert result is False

    def test_clear_queue(self, rate_limiter):
        """Test queue clearing."""
        # Add requests to queue
        rate_limiter.make_request(lambda: None)
        rate_limiter.make_request(lambda: None)
        rate_limiter.make_request(lambda: None)

        assert len(rate_limiter.queue) == 3

        cleared = rate_limiter.clear_queue()
        assert cleared == 3
        assert len(rate_limiter.queue) == 0

    @patch('threading.Thread')
    def test_shutdown(self, mock_thread_class, rate_limiter):
        """Test rate limiter shutdown."""
        mock_worker = Mock()
        mock_worker.is_alive.return_value = True
        rate_limiter.worker_thread = mock_worker

        rate_limiter.shutdown()

        assert rate_limiter.stop_event.is_set()
        mock_worker.join.assert_called_with(timeout=5.0)

    @patch('src.external.openrouter.rate_limiter.time.sleep')
    def test_process_queue_with_requests(self, mock_sleep, rate_limiter):
        """Test queue processing with available requests."""
        # Stop the actual worker
        rate_limiter.stop_event.set()

        # Add a request
        executed = []
        def test_func():
            executed.append(True)

        rate_limiter.make_request(test_func)
        rate_limiter.tokens = 1  # Make token available

        # Process queue manually
        rate_limiter._process_queue()

        # Should have executed the request
        assert len(executed) == 1

    def test_execute_request(self, rate_limiter):
        """Test request execution."""
        executed = []
        exception_caught = []

        def success_func():
            executed.append("success")

        def failing_func():
            raise ValueError("Test error")

        # Test successful execution
        request = Request(success_func, (), {})
        rate_limiter._execute_request(request)
        assert executed == ["success"]

        # Test exception handling
        request = Request(failing_func, (), {})
        # Should not raise exception
        rate_limiter._execute_request(request)