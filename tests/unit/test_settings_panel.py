# tests/unit/test_settings_panel.py
"""
Unit tests for SettingsPanel component.
"""

import pytest

from src.ui.components.settings_panel import SettingsPanel


class TestSettingsPanel:
    """Test cases for SettingsPanel component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings_panel = SettingsPanel()

    def test_initialization(self):
        """Test SettingsPanel initialization."""
        expected_settings = {
            "api_key": "",
            "theme": "light",
            "font_size": "medium",
            "default_model": "anthropic/claude-3-haiku",
            "notifications": True,
            "auto_save": True,
            "show_timestamps": True,
            "temperature": 0.7,
            "max_tokens": 4096
        }

        assert self.settings_panel.settings == expected_settings
        assert self.settings_panel.on_settings_save is None
        assert self.settings_panel.on_api_key_update is None

    def test_get_settings(self):
        """Test getting current settings."""
        settings = self.settings_panel.get_settings()
        assert isinstance(settings, dict)
        assert "api_key" in settings
        assert "theme" in settings
        assert settings["theme"] == "light"

    def test_update_settings(self):
        """Test updating settings."""
        new_settings = {
            "theme": "dark",
            "font_size": "large",
            "notifications": False
        }

        self.settings_panel.update_settings(new_settings)

        assert self.settings_panel.settings["theme"] == "dark"
        assert self.settings_panel.settings["font_size"] == "large"
        assert self.settings_panel.settings["notifications"] is False

        # Other settings should remain unchanged
        assert self.settings_panel.settings["api_key"] == ""

    def test_handle_settings_save(self):
        """Test handling settings save."""
        # Mock callback
        save_called = False
        saved_data = None

        def mock_save(settings):
            nonlocal save_called, saved_data
            save_called = True
            saved_data = settings
            return {"success": True}

        self.settings_panel.on_settings_save = mock_save

        # Simulate save with test data
        test_args = ["sk-test", 30, 3, "Dark", "Large", False, True, True, "gpt-4", 0.8, 2048]
        result = self.settings_panel._handle_save_settings(*test_args)

        assert save_called
        assert saved_data["api_key"] == "sk-test"
        assert saved_data["theme"] == "dark"
        assert saved_data["font_size"] == "large"
        assert saved_data["temperature"] == 0.8
        assert saved_data["max_tokens"] == 2048

        # Check that local settings were updated
        assert self.settings_panel.settings["theme"] == "dark"

    def test_handle_reset_settings(self):
        """Test handling settings reset."""
        # Modify current settings
        self.settings_panel.update_settings({
            "theme": "dark",
            "font_size": "large",
            "api_key": "modified_key"
        })

        # Reset settings
        result = self.settings_panel._handle_reset_settings()

        # Should return default values
        assert len(result) == 11  # All setting inputs
        assert result[0] == ""  # API key (masked)
        assert result[3] == "Light"  # Theme
        assert result[4] == "Medium"  # Font size

        # Local settings should be reset
        assert self.settings_panel.settings["theme"] == "light"
        assert self.settings_panel.settings["font_size"] == "medium"
        assert self.settings_panel.settings["api_key"] == ""

    def test_handle_api_key_update(self):
        """Test handling API key update."""
        # Mock callback
        update_called = False
        updated_key = None

        def mock_update(key):
            nonlocal update_called, updated_key
            update_called = True
            updated_key = key
            return {"success": True}

        self.settings_panel.on_api_key_update = mock_update

        # Test update
        result = self.settings_panel._handle_api_key_update("sk-or-v1-newkey")

        assert update_called
        assert updated_key == "sk-or-v1-newkey"

    def test_handle_test_connection(self):
        """Test handling connection test."""
        # This method currently just prints, so we test it doesn't crash
        self.settings_panel._handle_test_connection()
        # If we get here without exception, test passes

    def test_validate_api_key(self):
        """Test API key validation."""
        # Valid keys
        assert self.settings_panel.validate_api_key("sk-or-v1-1234567890abcdef")
        assert self.settings_panel.validate_api_key("sk-or-v1-abcdefghijklmnopqrstuvwx")

        # Invalid keys
        assert not self.settings_panel.validate_api_key("")
        assert not self.settings_panel.validate_api_key("invalid-key")
        assert not self.settings_panel.validate_api_key("sk-or-v1-short")

    def test_mask_api_key(self):
        """Test API key masking."""
        # Long key
        masked = self.settings_panel._mask_api_key("sk-or-v1-abcdefghijklmnopqrstuvwx")
        assert masked == "sk-or-v1-abcde*************************vwx"

        # Short key
        masked = self.settings_panel._mask_api_key("short")
        assert masked == "short"

        # Empty key
        masked = self.settings_panel._mask_api_key("")
        assert masked == ""

    def test_capitalize_first(self):
        """Test first letter capitalization."""
        assert self.settings_panel._capitalize_first("light") == "Light"
        assert self.settings_panel._capitalize_first("DARK") == "Dark"
        assert self.settings_panel._capitalize_first("") == ""
        assert self.settings_panel._capitalize_first("a") == "A"

    def test_get_all_setting_inputs(self):
        """Test getting all setting input components."""
        inputs = self.settings_panel._get_all_setting_inputs()

        # Should return list of 11 inputs
        assert len(inputs) == 11
        # All should be None since no Gradio components are created
        assert all(inp is None for inp in inputs)

    def test_show_panel_and_hide_panel(self):
        """Test showing and hiding settings panel."""
        # These methods currently do nothing, so we test they don't crash
        self.settings_panel.show_panel()
        self.settings_panel.hide_panel()
        # If we get here without exception, test passes

    def test_settings_persistence(self):
        """Test that settings changes persist."""
        original_theme = self.settings_panel.settings["theme"]

        # Change setting
        self.settings_panel.update_settings({"theme": "dark"})
        assert self.settings_panel.settings["theme"] == "dark"

        # Change again
        self.settings_panel.update_settings({"theme": "light"})
        assert self.settings_panel.settings["theme"] == "light"

        # Reset
        self.settings_panel._handle_reset_settings()
        assert self.settings_panel.settings["theme"] == original_theme