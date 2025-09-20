# tests/unit/test_sidebar_panel.py
"""
Unit tests for SidebarPanel component.
"""

import pytest

from src.ui.components.sidebar_panel import SidebarPanel


class TestSidebarPanel:
    """Test cases for SidebarPanel component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sidebar_panel = SidebarPanel()

    def test_initialization(self):
        """Test SidebarPanel initialization."""
        expected_models = [
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            "google/gemini-pro",
            "meta/llama-2-70b-chat"
        ]

        assert self.sidebar_panel.available_models == expected_models
        assert self.sidebar_panel.current_model == "anthropic/claude-3-haiku"
        # Note: is_collapsed attribute doesn't exist in current implementation
        assert self.sidebar_panel.conversations == []
        assert self.sidebar_panel.on_model_select is None
        assert self.sidebar_panel.on_conversation_select is None
        assert self.sidebar_panel.on_new_conversation is None

    def test_update_current_model(self):
        """Test updating current model."""
        self.sidebar_panel.update_current_model("openai/gpt-4")
        assert self.sidebar_panel.current_model == "openai/gpt-4"

    def test_add_conversation(self):
        """Test adding a conversation."""
        conversation_id = "conv_123"
        title = "Test Conversation"

        self.sidebar_panel.add_conversation(conversation_id, title)

        assert len(self.sidebar_panel.conversations) == 1
        assert self.sidebar_panel.conversations[0]["id"] == conversation_id
        assert self.sidebar_panel.conversations[0]["title"] == title
        assert self.sidebar_panel.conversations[0]["message_count"] == 0

    def test_update_conversation_metadata(self):
        """Test updating conversation metadata."""
        conversation_id = "conv_123"
        self.sidebar_panel.add_conversation(conversation_id, "Test")

        # Update metadata
        new_metadata = {"last_activity": "2024-01-01T12:00:00"}
        self.sidebar_panel.update_conversation_metadata(conversation_id, new_metadata)

        conversation = self.sidebar_panel.conversations[0]
        assert conversation["last_activity"] == "2024-01-01T12:00:00"

    def test_get_conversations(self):
        """Test getting conversations list."""
        # Add conversations
        self.sidebar_panel.add_conversation("conv_1", "First")
        self.sidebar_panel.add_conversation("conv_2", "Second")

        conversations = self.sidebar_panel.get_conversations()

        assert len(conversations) == 2
        assert conversations[0]["title"] == "First"
        assert conversations[1]["title"] == "Second"

    def test_get_conversations_html_empty(self):
        """Test conversations HTML generation when empty."""
        html = self.sidebar_panel._get_conversations_html()

        assert "No conversations yet" in html

    def test_get_conversations_html_with_conversations(self):
        """Test conversations HTML generation with conversations."""
        # Add some conversations
        self.sidebar_panel.add_conversation("conv_1", "First Conversation")
        self.sidebar_panel.add_conversation("conv_2", "Second Conversation")

        html = self.sidebar_panel._get_conversations_html()

        assert "First Conversation" in html
        assert "Second Conversation" in html

    def test_get_model_info_html(self):
        """Test model info HTML generation."""
        html = self.sidebar_panel._get_model_info_html("anthropic/claude-3-haiku")

        assert "Claude 3 Haiku" in html
        assert "Fast and efficient" in html
        assert "$0.001" in html

    def test_get_model_details_known_model(self):
        """Test getting details for known model."""
        details = self.sidebar_panel._get_model_details("anthropic/claude-3-haiku")

        assert details["name"] == "Claude 3 Haiku"
        assert "Fast and efficient" in details["description"]
        assert "💡 Fast" in details["capabilities"]

    def test_get_model_details_unknown_model(self):
        """Test getting details for unknown model."""
        details = self.sidebar_panel._get_model_details("unknown/model")

        assert details["name"] == "Model"
        assert details["description"] == "AI model"
        assert details["cost"] == "0.001"

    def test_format_time_ago_recent(self):
        """Test time ago formatting for recent time."""
        from datetime import datetime, timedelta

        recent_time = (datetime.now() - timedelta(minutes=5)).isoformat()
        result = self.sidebar_panel._format_time_ago(recent_time)

        assert "5 minutes ago" in result

    def test_format_time_ago_old(self):
        """Test time ago formatting for old time."""
        old_time = "2020-01-01T00:00:00"
        result = self.sidebar_panel._format_time_ago(old_time)

        assert "days ago" in result

    def test_handle_model_change(self):
        """Test model change handling."""
        # Change model
        html = self.sidebar_panel._handle_model_change("openai/gpt-4")

        assert self.sidebar_panel.current_model == "openai/gpt-4"
        assert "GPT-4" in html

    def test_event_handlers(self):
        """Test event handler setup."""
        # Test that event handlers can be set
        def mock_handler():
            pass

        self.sidebar_panel.on_model_select = mock_handler
        self.sidebar_panel.on_conversation_select = mock_handler
        self.sidebar_panel.on_new_conversation = mock_handler

        assert self.sidebar_panel.on_model_select is not None
        assert self.sidebar_panel.on_conversation_select is not None
        assert self.sidebar_panel.on_new_conversation is not None

    def test_integration_with_state_changes(self):
        """Test integration with state changes."""
        # Add conversations
        self.sidebar_panel.add_conversation("conv_1", "Conversation 1")
        self.sidebar_panel.add_conversation("conv_2", "Conversation 2")

        # Update model
        self.sidebar_panel.update_current_model("openai/gpt-4")

        # Update conversation metadata
        self.sidebar_panel.update_conversation_metadata("conv_1", {"last_activity": "now"})

        # Verify state
        assert self.sidebar_panel.current_model == "openai/gpt-4"
        assert len(self.sidebar_panel.conversations) == 2
        assert self.sidebar_panel.conversations[0]["last_activity"] == "now"