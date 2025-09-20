# tests/unit/test_message_processor.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.processors.message_processor import MessageProcessor
from src.external.openrouter.client import OpenRouterClient


class TestMessageProcessor:
    @pytest.fixture
    def mock_openrouter_client(self):
        """Mock OpenRouterClient for testing."""
        return Mock(spec=OpenRouterClient)

    @pytest.fixture
    def processor(self, mock_openrouter_client):
        """Create MessageProcessor with mocked client."""
        return MessageProcessor(mock_openrouter_client)

    def test_initialization(self, mock_openrouter_client):
        """Test processor initialization."""
        processor = MessageProcessor(mock_openrouter_client)
        assert processor.openrouter_client == mock_openrouter_client

    def test_initialization_default_client(self):
        """Test processor initialization with default client."""
        with patch('src.core.processors.message_processor.OpenRouterClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            processor = MessageProcessor()
            assert processor.openrouter_client == mock_client
            mock_client_class.assert_called_once()

    def test_validate_message_success(self, processor):
        """Test successful message validation."""
        content = "Hello, this is a valid message."

        with patch('src.core.processors.message_processor.validate_message_content') as mock_validate:
            mock_validate.return_value = (True, "")

            is_valid, error, metadata = processor.validate_message(content)

            assert is_valid is True
            assert error == ""
            assert 'length' in metadata
            assert 'word_count' in metadata
            assert metadata['length'] == len(content)

    def test_validate_message_failure(self, processor):
        """Test message validation failure."""
        content = ""

        with patch('src.core.processors.message_processor.validate_message_content') as mock_validate:
            mock_validate.return_value = (False, "Message is empty")

            is_valid, error, metadata = processor.validate_message(content)

            assert is_valid is False
            assert error == "Message is empty"
            assert metadata == {}

    def test_extract_metadata(self, processor):
        """Test metadata extraction."""
        content = "Hello world! This is a test message with https://example.com URL."

        metadata = processor._extract_metadata(content)

        assert metadata['length'] == len(content)
        assert metadata['word_count'] == 9  # Approximate count
        assert 'urls' in metadata
        assert metadata['urls'] == 1
        assert 'code_blocks' in metadata
        assert 'timestamp' in metadata

    def test_extract_metadata_with_code(self, processor):
        """Test metadata extraction with code blocks."""
        content = "Here's some code:\n```python\nprint('hello')\n```"

        metadata = processor._extract_metadata(content)

        assert metadata['code_blocks'] == 1
        assert metadata['length'] == len(content)

    def test_estimate_tokens(self, processor):
        """Test token estimation."""
        content = "Hello world! This is a test message."

        token_count = processor.estimate_tokens(content)

        assert isinstance(token_count, int)
        assert token_count > 0
        # Basic check that it's reasonable
        assert token_count >= len(content) / 10  # Rough approximation

    def test_estimate_tokens_with_code(self, processor):
        """Test token estimation with code blocks."""
        content = "```python\ndef hello():\n    print('world')\n```"

        token_count = processor.estimate_tokens(content)

        assert isinstance(token_count, int)
        assert token_count > 0

    def test_estimate_cost(self, processor):
        """Test cost estimation."""
        token_count = 1000

        cost = processor.estimate_cost(token_count)

        assert isinstance(cost, float)
        assert cost > 0
        assert cost == token_count * 0.0001  # Default rate

    def test_estimate_cost_claude_model(self, processor):
        """Test cost estimation for Claude model."""
        token_count = 1000
        model = "anthropic/claude-3-haiku"

        cost = processor.estimate_cost(token_count, model)

        assert cost == token_count * 0.00015  # Claude rate

    def test_estimate_cost_gpt4_model(self, processor):
        """Test cost estimation for GPT-4 model."""
        token_count = 1000
        model = "openai/gpt-4"

        cost = processor.estimate_cost(token_count, model)

        assert cost == token_count * 0.0002  # GPT-4 rate

    def test_format_for_api(self, processor):
        """Test message formatting for API."""
        content = "Hello world!"
        role = "user"

        formatted = processor.format_for_api(content, role)

        assert formatted['role'] == role
        assert formatted['content'] == content
        assert 'metadata' in formatted
        assert 'original_length' in formatted['metadata']
        assert formatted['metadata']['original_length'] == len(content)

    def test_format_for_api_with_sanitization(self, processor):
        """Test message formatting with content sanitization."""
        content = "Hello <script>alert('xss')</script> world!"
        role = "user"

        formatted = processor.format_for_api(content, role)

        assert '<script>' not in formatted['content']
        assert 'alert' not in formatted['content']
        assert '<script>' in formatted['content']  # Should be HTML encoded

    def test_sanitize_content(self, processor):
        """Test content sanitization."""
        dangerous_content = "<script>alert('xss')</script>Hello\n\n\nworld!"

        sanitized = processor._sanitize_content(dangerous_content)

        assert '<script>' not in sanitized
        assert 'alert' not in sanitized
        assert '<script>' in sanitized
        assert '\n\n\n' not in sanitized  # Whitespace normalized
        assert 'Hello world!' in sanitized

    def test_process_conversation_messages(self, processor):
        """Test conversation message processing."""
        messages = [
            {"content": "Hello!", "role": "user"},
            {"content": "Hi there!", "role": "assistant"},
            {"content": "How are you?", "role": "user"}
        ]

        with patch.object(processor, 'validate_message') as mock_validate:
            mock_validate.return_value = (True, "", {"tokens": 10, "length": 5})

            processed, summary = processor.process_conversation_messages(messages)

            assert len(processed) == 3
            assert summary['total_messages'] == 3
            assert 'total_tokens' in summary
            assert 'processed_at' in summary

            # Check that each message has been processed
            for msg in processed:
                assert 'metadata' in msg
                assert 'tokens' in msg['metadata']

    def test_process_conversation_messages_with_invalid(self, processor):
        """Test conversation processing with invalid messages."""
        messages = [
            {"content": "Valid message", "role": "user"},
            {"content": "", "role": "user"},  # Invalid
            {"content": "Another valid", "role": "assistant"}
        ]

        with patch.object(processor, 'validate_message') as mock_validate:
            def validate_side_effect(content):
                if content == "":
                    return False, "Empty message", {}
                return True, "", {"tokens": 10, "length": len(content)}

            mock_validate.side_effect = validate_side_effect

            processed, summary = processor.process_conversation_messages(messages)

            assert len(processed) == 2  # Invalid message should be skipped
            assert summary['total_messages'] == 2

    def test_process_conversation_messages_empty(self, processor):
        """Test processing empty message list."""
        processed, summary = processor.process_conversation_messages([])

        assert processed == []
        assert summary['total_messages'] == 0
        assert summary['total_tokens'] == 0

    def test_get_processing_stats(self, processor):
        """Test getting processing statistics."""
        stats = processor.get_processing_stats()

        assert isinstance(stats, dict)
        assert 'messages_processed' in stats
        assert 'total_tokens_processed' in stats
        assert 'average_processing_time' in stats
        assert 'error_count' in stats

    def test_estimate_tokens_empty_content(self, processor):
        """Test token estimation with empty content."""
        token_count = processor.estimate_tokens("")

        assert token_count == 0

    def test_estimate_cost_zero_tokens(self, processor):
        """Test cost estimation with zero tokens."""
        cost = processor.estimate_cost(0)

        assert cost == 0.0

    def test_extract_metadata_empty_content(self, processor):
        """Test metadata extraction with empty content."""
        metadata = processor._extract_metadata("")

        assert metadata['length'] == 0
        assert metadata['word_count'] == 0
        assert metadata['code_blocks'] == 0
        assert metadata['urls'] == 0
        assert metadata['mentions'] == 0