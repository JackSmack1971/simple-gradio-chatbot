# tests/unit/test_chat_panel.py
"""
Unit tests for ChatPanel component.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.ui.components.chat_panel import ChatPanel, Message


class TestChatPanel:
    """Test cases for ChatPanel component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chat_panel = ChatPanel()

    def test_initialization(self):
        """Test ChatPanel initialization."""
        assert self.chat_panel.messages == []
        assert self.chat_panel.conversation_id is None
        assert not self.chat_panel.is_streaming
        assert self.chat_panel.streaming_message_id is None
        assert self.chat_panel.on_message_action is None

    def test_add_user_message(self):
        """Test adding a user message."""
        message_id = self.chat_panel.add_user_message("Hello, AI!")

        assert len(self.chat_panel.messages) == 1
        assert self.chat_panel.messages[0].id == message_id
        assert self.chat_panel.messages[0].role == "user"
        assert self.chat_panel.messages[0].content == "Hello, AI!"
        assert isinstance(self.chat_panel.messages[0].timestamp, str)

    def test_add_assistant_message(self):
        """Test adding an assistant message."""
        message_id = self.chat_panel.add_assistant_message("Hello, human!")

        assert len(self.chat_panel.messages) == 1
        assert self.chat_panel.messages[0].id == message_id
        assert self.chat_panel.messages[0].role == "assistant"
        assert self.chat_panel.messages[0].content == "Hello, human!"

    def test_start_streaming(self):
        """Test starting streaming for a message."""
        # Add a message first
        message_id = self.chat_panel.add_assistant_message("")

        # Start streaming
        html = self.chat_panel.start_streaming(message_id)

        assert self.chat_panel.is_streaming
        assert self.chat_panel.streaming_message_id == message_id
        assert "AI is generating response" in html
        assert "pulse" in html  # Animation class

    def test_append_to_streaming_message(self):
        """Test appending content to streaming message."""
        # Start streaming
        message_id = self.chat_panel.add_assistant_message("")
        self.chat_panel.start_streaming(message_id)

        # Append content
        self.chat_panel.append_to_streaming_message("Hello")
        self.chat_panel.append_to_streaming_message(" world!")

        assert self.chat_panel.messages[0].content == "Hello world!"

    def test_complete_streaming(self):
        """Test completing streaming."""
        # Start streaming
        message_id = self.chat_panel.add_assistant_message("")
        self.chat_panel.start_streaming(message_id)

        # Complete streaming
        self.chat_panel.complete_streaming()

        assert not self.chat_panel.is_streaming
        assert self.chat_panel.streaming_message_id is None

    def test_clear_messages(self):
        """Test clearing all messages."""
        self.chat_panel.add_user_message("Test message")
        self.chat_panel.add_assistant_message("Response")

        assert len(self.chat_panel.messages) == 2

        self.chat_panel.clear_messages()

        assert len(self.chat_panel.messages) == 0
        assert not self.chat_panel.is_streaming

    def test_load_conversation(self):
        """Test loading a conversation."""
        conversation_id = "conv_123"

        self.chat_panel.load_conversation(conversation_id)

        assert self.chat_panel.conversation_id == conversation_id
        # Messages should be cleared when loading new conversation
        assert len(self.chat_panel.messages) == 0

    def test_get_message_content(self):
        """Test getting message content by ID."""
        message_id = self.chat_panel.add_user_message("Test content")

        content = self.chat_panel.get_message_content(message_id)
        assert content == "Test content"

        # Test non-existent message
        content = self.chat_panel.get_message_content("nonexistent")
        assert content == ""

    def test_get_user_message_for_response(self):
        """Test getting user message that prompted a response."""
        # Add user message
        user_message_id = self.chat_panel.add_user_message("User question")

        # Add assistant response
        response_id = self.chat_panel.add_assistant_message("AI response")

        # Get user message for response
        user_content = self.chat_panel.get_user_message_for_response(response_id)

        assert user_content == "User question"

    def test_get_messages(self):
        """Test getting all messages as dictionaries."""
        self.chat_panel.add_user_message("User message")
        self.chat_panel.add_assistant_message("AI response")

        messages = self.chat_panel.get_messages()

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "User message"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "AI response"

    def test_get_streaming_status(self):
        """Test getting streaming status."""
        # Initially not streaming
        status = self.chat_panel.get_streaming_status()
        assert not status["is_streaming"]
        assert status["streaming_message_id"] is None

        # Start streaming
        message_id = self.chat_panel.add_assistant_message("")
        self.chat_panel.start_streaming(message_id)

        status = self.chat_panel.get_streaming_status()
        assert status["is_streaming"]
        assert status["streaming_message_id"] == message_id

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # Test with recent timestamp
        recent_time = datetime.now().isoformat()
        formatted = self.chat_panel._format_timestamp(recent_time)
        assert formatted == "Just now"

        # Test with invalid timestamp
        formatted = self.chat_panel._format_timestamp("invalid")
        assert formatted == "Unknown time"

    def test_format_message_content(self):
        """Test message content formatting."""
        # Test basic formatting
        content = "Hello\nWorld"
        formatted = self.chat_panel._format_message_content(content)
        assert "<br>" in formatted

        # Test code formatting
        content = "`code`"
        formatted = self.chat_panel._format_message_content(content)
        assert "<code" in formatted

        # Test bold formatting
        content = "**bold**"
        formatted = self.chat_panel._format_message_content(content)
        assert "<strong>bold</strong>" in formatted

        # Test italic formatting
        content = "*italic*"
        formatted = self.chat_panel._format_message_content(content)
        assert "<em>italic</em>" in formatted


class TestMessage:
    """Test cases for Message class."""

    def test_message_creation(self):
        """Test Message object creation."""
        message = Message("msg_123", "user", "Hello world")

        assert message.id == "msg_123"
        assert message.role == "user"
        assert message.content == "Hello world"
        assert isinstance(message.timestamp, str)

    def test_message_to_dict(self):
        """Test converting Message to dictionary."""
        message = Message("msg_123", "user", "Hello world", "2024-01-01T12:00:00")

        data = message.to_dict()

        assert data["id"] == "msg_123"
        assert data["role"] == "user"
        assert data["content"] == "Hello world"
        assert data["timestamp"] == "2024-01-01T12:00:00"