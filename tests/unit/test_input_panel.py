# tests/unit/test_input_panel.py
"""
Unit tests for InputPanel component.
"""

import pytest

from src.ui.components.input_panel import InputPanel


class TestInputPanel:
    """Test cases for InputPanel component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.input_panel = InputPanel(max_length=2000)

    def test_initialization(self):
        """Test InputPanel initialization."""
        assert self.input_panel.max_length == 2000
        assert self.input_panel.current_length == 0
        assert not self.input_panel.disabled
        assert self.input_panel.on_send_message is None
        assert self.input_panel.on_input_change is None

    def test_character_count_update(self):
        """Test updating character count."""
        self.input_panel.update_character_count(150)
        assert self.input_panel.current_length == 150

        self.input_panel.update_character_count(2500)  # Over limit
        assert self.input_panel.current_length == 2500

    def test_can_send_logic(self):
        """Test the logic for determining if message can be sent."""
        # Empty message
        assert not self.input_panel._can_send()

        # Add some content
        self.input_panel.current_length = 10
        assert self.input_panel._can_send()

        # At limit
        self.input_panel.current_length = 2000
        assert self.input_panel._can_send()

        # Over limit
        self.input_panel.current_length = 2001
        assert not self.input_panel._can_send()

        # Disabled
        self.input_panel.disabled = True
        self.input_panel.current_length = 10
        assert not self.input_panel._can_send()

    def test_set_disabled(self):
        """Test setting disabled state."""
        self.input_panel.set_disabled(True)
        assert self.input_panel.disabled

        self.input_panel.set_disabled(False)
        assert not self.input_panel.disabled

    def test_clear_input(self):
        """Test clearing input."""
        self.input_panel.current_length = 100
        self.input_panel.clear_input()
        assert self.input_panel.current_length == 0

    def test_set_max_length(self):
        """Test setting maximum length."""
        self.input_panel.set_max_length(1000)
        assert self.input_panel.max_length == 1000

        # Test with current length over new limit
        self.input_panel.current_length = 1500
        self.input_panel.set_max_length(1000)
        assert self.input_panel.max_length == 1000
        # Current length should remain unchanged
        assert self.input_panel.current_length == 1500

    def test_get_character_count_html(self):
        """Test character count HTML generation."""
        # Normal state
        self.input_panel.current_length = 100
        html = self.input_panel._get_character_count_html()
        assert "100/2000" in html
        assert "var(--text-color-secondary)" in html

        # Warning state (90% of limit)
        self.input_panel.current_length = 1800
        html = self.input_panel._get_character_count_html()
        assert "1800/2000" in html
        assert "var(--color-orange)" in html

        # Error state (over limit)
        self.input_panel.current_length = 2100
        html = self.input_panel._get_character_count_html()
        assert "2100/2000" in html
        assert "var(--color-red)" in html

    def test_get_max_length(self):
        """Test getting maximum length."""
        assert self.input_panel.get_max_length() == 2000

    def test_get_current_length(self):
        """Test getting current length."""
        self.input_panel.current_length = 500
        assert self.input_panel.get_current_length() == 500

    def test_is_disabled(self):
        """Test checking disabled state."""
        assert not self.input_panel.is_disabled()

        self.input_panel.disabled = True
        assert self.input_panel.is_disabled()

    def test_set_placeholder(self):
        """Test setting placeholder (placeholder implementation)."""
        # This is a placeholder test since the actual implementation
        # would require Gradio component interaction
        self.input_panel.set_placeholder("New placeholder")
        # In real implementation, this would update the Gradio component

    def test_set_input_value(self):
        """Test setting input value."""
        self.input_panel.set_input_value("Test message")
        assert self.input_panel.current_length == 12

    def test_set_send_enabled(self):
        """Test setting send button enabled state."""
        # This is a placeholder test since the actual implementation
        # would require Gradio component interaction
        self.input_panel.set_send_enabled(True)
        self.input_panel.set_send_enabled(False)
        # In real implementation, this would update the Gradio component

    def test_show_validation_error(self):
        """Test showing validation error."""
        with pytest.raises(AssertionError):
            # This should work but currently just prints
            self.input_panel.show_validation_error("Test error")
            # In real implementation, this would show error in UI

    def test_focus_input(self):
        """Test focusing input field."""
        # This is a placeholder test since the actual implementation
        # would require JavaScript interaction
        self.input_panel.focus_input()
        # In real implementation, this would focus the input field

    def test_get_input_value(self):
        """Test getting input value."""
        # This is a placeholder test since the actual implementation
        # returns empty string when no Gradio component is attached
        value = self.input_panel.get_input_value()
        assert value == ""

    def test_handle_input_change(self):
        """Test handling input change."""
        # Test with normal input
        result = self.input_panel._handle_input_change("Hello world")
        assert self.input_panel.current_length == 11
        assert len(result) == 2  # Should return tuple of (html, button_state)

        # Test with empty input
        result = self.input_panel._handle_input_change("")
        assert self.input_panel.current_length == 0
        assert len(result) == 2

        # Test with long input
        long_text = "x" * 2500
        result = self.input_panel._handle_input_change(long_text)
        assert self.input_panel.current_length == 2500
        assert len(result) == 2

    def test_handle_send_click(self):
        """Test handling send button click."""
        # Test with valid message
        result = self.input_panel._handle_send_click("Test message")
        assert len(result) == 3  # Should return tuple of (input_value, html, button_state)
        assert result[0] == ""  # Input should be cleared

        # Test with empty message
        result = self.input_panel._handle_send_click("")
        assert len(result) == 3
        assert result[0] == ""  # Input should remain empty

        # Test with whitespace only
        result = self.input_panel._handle_send_click("   ")
        assert len(result) == 3
        assert result[0] == ""  # Input should be cleared