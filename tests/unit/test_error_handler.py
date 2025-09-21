# tests/unit/test_error_handler.py
import pytest
import time
from unittest.mock import Mock, patch

from src.external.openrouter.error_handler import ErrorHandler, ErrorType


class TestErrorHandler:
    """Test the ErrorHandler class."""

    @pytest.fixture
    def error_handler(self):
        """Create an error handler for testing."""
        return ErrorHandler(max_retries=3, base_backoff=1.0, max_backoff=10.0)

    def test_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler(max_retries=5, base_backoff=2.0, max_backoff=20.0)

        assert handler.max_retries == 5
        assert handler.base_backoff == 2.0
        assert handler.max_backoff == 20.0

    def test_classify_error_network(self, error_handler):
        """Test network error classification."""
        error_data = {"error": "Connection timeout"}
        error_type = error_handler.classify_error(error_data)
        assert error_type == ErrorType.NETWORK

    def test_classify_error_authentication(self, error_handler):
        """Test authentication error classification."""
        # Test by status code
        error_type = error_handler.classify_error({}, status_code=401)
        assert error_type == ErrorType.AUTHENTICATION

        # Test by error code
        error_data = {"code": "authentication_required"}
        error_type = error_handler.classify_error(error_data)
        assert error_type == ErrorType.AUTHENTICATION

    def test_classify_error_rate_limit(self, error_handler):
        """Test rate limit error classification."""
        # Test by status code
        error_type = error_handler.classify_error({}, status_code=429)
        assert error_type == ErrorType.RATE_LIMIT

        # Test by error code
        error_data = {"code": "rate_limit_exceeded"}
        error_type = error_handler.classify_error(error_data)
        assert error_type == ErrorType.RATE_LIMIT

    def test_classify_error_api_error(self, error_handler):
        """Test API error classification."""
        error_type = error_handler.classify_error({}, status_code=500)
        assert error_type == ErrorType.API_ERROR

    def test_classify_error_validation(self, error_handler):
        """Test validation error classification."""
        error_data = {"code": "model_not_found"}
        error_type = error_handler.classify_error(error_data)
        assert error_type == ErrorType.VALIDATION

    def test_classify_error_unknown(self, error_handler):
        """Test unknown error classification."""
        error_data = {"unknown": "error"}
        error_type = error_handler.classify_error(error_data)
        assert error_type == ErrorType.UNKNOWN

    def test_get_user_friendly_message_http_status(self, error_handler):
        """Test user-friendly message from HTTP status."""
        message = error_handler.get_user_friendly_message({}, status_code=429)
        assert "Rate limit exceeded" in message

    def test_get_user_friendly_message_openrouter_code(self, error_handler):
        """Test user-friendly message from OpenRouter error code."""
        error_data = {"code": "authentication_invalid"}
        message = error_handler.get_user_friendly_message(error_data)
        assert "invalid" in message.lower()

    def test_get_user_friendly_message_nested_error(self, error_handler):
        """Test user-friendly message from nested error structure."""
        error_data = {"error": {"message": "Custom error message"}}
        message = error_handler.get_user_friendly_message(error_data)
        assert message == "Custom error message"

    def test_get_user_friendly_message_string_error(self, error_handler):
        """Test user-friendly message from string error."""
        error_data = "Simple error message"
        message = error_handler.get_user_friendly_message(error_data)
        assert message == "Simple error message"

    def test_get_user_friendly_message_fallback(self, error_handler):
        """Test fallback user-friendly message."""
        error_data = {"unknown_field": "unknown_value"}
        message = error_handler.get_user_friendly_message(error_data)
        assert "unexpected error" in message.lower()

    def test_sanitize_error_message(self, error_handler):
        """Test error message sanitization."""
        message = "Error with api_key=sk-123 and token=abc"
        sanitized = error_handler._sanitize_error_message(message)
        assert "[REDACTED]" in sanitized
        assert "sk-123" not in sanitized
        assert "abc" not in sanitized

    def test_should_retry_network_error(self, error_handler):
        """Test retry decision for network errors."""
        assert error_handler.should_retry(ErrorType.NETWORK, 0) is True
        assert error_handler.should_retry(ErrorType.NETWORK, 2) is True
        assert error_handler.should_retry(ErrorType.NETWORK, 3) is False  # Max retries reached

    def test_should_retry_rate_limit_error(self, error_handler):
        """Test retry decision for rate limit errors."""
        assert error_handler.should_retry(ErrorType.RATE_LIMIT, 0) is True
        assert error_handler.should_retry(ErrorType.RATE_LIMIT, 3) is False

    def test_should_retry_authentication_error(self, error_handler):
        """Test retry decision for authentication errors."""
        assert error_handler.should_retry(ErrorType.AUTHENTICATION, 0) is False

    def test_should_retry_validation_error(self, error_handler):
        """Test retry decision for validation errors."""
        assert error_handler.should_retry(ErrorType.VALIDATION, 0) is False

    def test_calculate_backoff_normal(self, error_handler):
        """Test backoff calculation for normal errors."""
        backoff = error_handler.calculate_backoff(0, ErrorType.NETWORK)
        assert 1.0 <= backoff <= 2.0  # Base delay with jitter

    def test_calculate_backoff_rate_limit(self, error_handler):
        """Test backoff calculation for rate limit errors."""
        backoff = error_handler.calculate_backoff(0, ErrorType.RATE_LIMIT)
        assert 2.0 <= backoff <= 4.0  # Double base delay with jitter

    def test_calculate_backoff_max_limit(self, error_handler):
        """Test backoff calculation respects max limit."""
        # High attempt count should give high backoff, but capped at max_backoff
        backoff = error_handler.calculate_backoff(10, ErrorType.NETWORK)
        assert backoff <= error_handler.max_backoff

    def test_handle_error_with_retry(self, error_handler):
        """Test error handling that should be retried."""
        error_data = {"code": "rate_limit_exceeded"}
        result = error_handler.handle_error(error_data, status_code=429, attempt_count=0)

        assert result["error_type"] == ErrorType.RATE_LIMIT.value
        assert result["should_retry"] is True
        assert "backoff_time" in result
        assert "Rate limit exceeded" in result["user_message"]

    def test_handle_error_no_retry(self, error_handler):
        """Test error handling that should not be retried."""
        error_data = {"code": "authentication_invalid"}
        result = error_handler.handle_error(error_data, status_code=401, attempt_count=0)

        assert result["error_type"] == ErrorType.AUTHENTICATION.value
        assert result["should_retry"] is False
        assert "backoff_time" not in result

    @patch('time.sleep')
    def test_execute_with_retry_success(self, mock_sleep, error_handler):
        """Test successful function execution with retry."""
        def successful_func():
            return True, {"result": "success"}

        success, result = error_handler.execute_with_retry(successful_func)

        assert success is True
        assert result == {"result": "success"}
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    def test_execute_with_retry_with_retries(self, mock_sleep, error_handler):
        """Test function execution that requires retries."""
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return False, {"error": "Temporary failure"}
            return True, {"result": "success"}

        success, result = error_handler.execute_with_retry(failing_func)

        assert success is True
        assert result == {"result": "success"}
        assert call_count == 3
        assert mock_sleep.call_count == 2  # Two retries

    @patch('time.sleep')
    def test_execute_with_retry_exhaustion(self, mock_sleep, error_handler):
        """Test function execution that exhausts all retries."""
        def always_failing_func():
            return False, {"error": "Persistent failure"}

        success, result = error_handler.execute_with_retry(always_failing_func)

        assert success is False
        assert "failed after" in result["error"].lower()
        assert result["retry"]["will_retry"] is False
        assert mock_sleep.call_count == 3  # Max retries

    @patch('time.sleep')
    def test_execute_with_retry_exception(self, mock_sleep, error_handler):
        """Test function execution that raises exceptions."""
        call_count = 0

        def exception_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return True, {"result": "success"}

        success, result = error_handler.execute_with_retry(exception_func)

        assert success is True
        assert result == {"result": "success"}
        assert call_count == 2
        assert mock_sleep.call_count == 1

    def test_execute_with_retry_max_attempts_override(self, error_handler):
        """Test custom max attempts override."""
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            return False, {"error": "Failure"}

        success, result = error_handler.execute_with_retry(failing_func, max_attempts=2)

        assert success is False
        assert "failure" in result["error"].lower()
        assert result["retry"]["max_attempts"] == 2
        assert call_count == 2  # Only 2 attempts instead of default 4
