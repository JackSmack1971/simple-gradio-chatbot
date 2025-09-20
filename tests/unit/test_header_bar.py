# tests/unit/test_header_bar.py
"""
Unit tests for HeaderBar component.
"""

import pytest

from src.ui.components.header_bar import HeaderBar


class TestHeaderBar:
    """Test cases for HeaderBar component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.header_bar = HeaderBar()

    def test_initialization(self):
        """Test HeaderBar initialization."""
        assert self.header_bar.app_title == "Personal AI Chatbot"
        assert self.header_bar.current_model == "anthropic/claude-3-haiku"
        assert not self.header_bar.connection_status
        assert self.header_bar.last_activity is None

    def test_update_model_display(self):
        """Test updating model display."""
        # Test with GPT-4
        self.header_bar.update_model_display("openai/gpt-4")
        assert self.header_bar.current_model == "openai/gpt-4"

        # Test with Claude
        self.header_bar.update_model_display("anthropic/claude-3-sonnet")
        assert self.header_bar.current_model == "anthropic/claude-3-sonnet"

    def test_update_connection_status(self):
        """Test updating connection status."""
        # Test online status
        self.header_bar.update_connection_status(True)
        assert self.header_bar.connection_status is True

        # Test offline status
        self.header_bar.update_connection_status(False)
        assert self.header_bar.connection_status is False

    def test_update_last_activity(self):
        """Test updating last activity timestamp."""
        from datetime import datetime
        test_time = datetime.now()

        self.header_bar.update_last_activity(test_time)
        assert self.header_bar.last_activity == test_time

    def test_get_model_display_html(self):
        """Test model display HTML generation."""
        # Test with GPT-4
        self.header_bar.current_model = "openai/gpt-4"
        html = self.header_bar._get_model_display_html()
        assert "🤖 GPT-4" in html
        assert "model-display" in html

        # Test with Claude
        self.header_bar.current_model = "anthropic/claude-3-haiku"
        html = self.header_bar._get_model_display_html()
        assert "🤖 Claude-3-haiku" in html

        # Test with unknown model
        self.header_bar.current_model = "unknown/model"
        html = self.header_bar._get_model_display_html()
        assert "🤖 Model" in html

    def test_get_status_display_html(self):
        """Test status display HTML generation."""
        # Test online status
        self.header_bar.connection_status = True
        html = self.header_bar._get_status_display_html()
        assert "⚡ Online" in html
        assert "status-online" in html

        # Test offline status
        self.header_bar.connection_status = False
        html = self.header_bar._get_status_display_html()
        assert "🔴 Offline" in html
        assert "status-offline" in html

        # Test connecting status (None)
        self.header_bar.connection_status = None
        html = self.header_bar._get_status_display_html()
        assert "🟡 Connecting" in html
        assert "status-connecting" in html

    def test_get_activity_display_html(self):
        """Test activity display HTML generation."""
        from datetime import datetime, timedelta

        # Test with recent activity
        recent_time = datetime.now() - timedelta(minutes=5)
        self.header_bar.last_activity = recent_time
        html = self.header_bar._get_activity_display_html()
        assert "5 minutes ago" in html

        # Test with no activity
        self.header_bar.last_activity = None
        html = self.header_bar._get_activity_display_html()
        assert "Never" in html

    def test_format_model_name(self):
        """Test model name formatting."""
        # Test OpenAI models
        assert self.header_bar._format_model_name("openai/gpt-4") == "GPT-4"
        assert self.header_bar._format_model_name("openai/gpt-3.5-turbo") == "GPT-3.5-turbo"

        # Test Anthropic models
        assert self.header_bar._format_model_name("anthropic/claude-3-haiku") == "Claude-3-haiku"
        assert self.header_bar._format_model_name("anthropic/claude-3-sonnet") == "Claude-3-sonnet"

        # Test Google models
        assert self.header_bar._format_model_name("google/gemini-pro") == "Gemini-pro"

        # Test unknown format
        assert self.header_bar._format_model_name("unknown-model") == "Model"

    def test_format_time_ago(self):
        """Test time ago formatting."""
        from datetime import datetime, timedelta

        now = datetime.now()

        # Test seconds
        past_time = now - timedelta(seconds=30)
        assert self.header_bar._format_time_ago(past_time) == "30 seconds ago"

        # Test minutes
        past_time = now - timedelta(minutes=5)
        assert self.header_bar._format_time_ago(past_time) == "5 minutes ago"

        # Test hours
        past_time = now - timedelta(hours=2)
        assert self.header_bar._format_time_ago(past_time) == "2 hours ago"

        # Test days
        past_time = now - timedelta(days=1)
        assert self.header_bar._format_time_ago(past_time) == "1 day ago"

        # Test future time (should not happen in practice)
        future_time = now + timedelta(hours=1)
        result = self.header_bar._format_time_ago(future_time)
        assert "ago" in result

    def test_get_status_icon(self):
        """Test status icon selection."""
        assert self.header_bar._get_status_icon(True) == "⚡"
        assert self.header_bar._get_status_icon(False) == "🔴"
        assert self.header_bar._get_status_icon(None) == "🟡"

    def test_get_status_text(self):
        """Test status text selection."""
        assert self.header_bar._get_status_text(True) == "Online"
        assert self.header_bar._get_status_text(False) == "Offline"
        assert self.header_bar._get_status_text(None) == "Connecting"

    def test_get_status_class(self):
        """Test status CSS class selection."""
        assert self.header_bar._get_status_class(True) == "status-online"
        assert self.header_bar._get_status_class(False) == "status-offline"
        assert self.header_bar._get_status_class(None) == "status-connecting"

    def test_integration_with_updates(self):
        """Test integration of multiple updates."""
        from datetime import datetime

        # Update multiple properties
        self.header_bar.update_model_display("openai/gpt-4")
        self.header_bar.update_connection_status(True)
        self.header_bar.update_last_activity(datetime.now())

        # Verify all properties are set correctly
        assert self.header_bar.current_model == "openai/gpt-4"
        assert self.header_bar.connection_status is True
        assert self.header_bar.last_activity is not None

        # Verify HTML generation includes all updates
        model_html = self.header_bar._get_model_display_html()
        status_html = self.header_bar._get_status_display_html()

        assert "GPT-4" in model_html
        assert "Online" in status_html