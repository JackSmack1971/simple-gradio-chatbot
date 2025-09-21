"""Security regression tests for GradioInterface logging."""

import logging

import pytest

from src.ui.gradio_interface import GradioInterface


@pytest.fixture()
def gradio_interface() -> GradioInterface:
    """Provide a GradioInterface instance for logging tests."""
    return GradioInterface()


def test_settings_save_masks_sensitive_values(gradio_interface: GradioInterface, caplog: pytest.LogCaptureFixture) -> None:
    """Ensure API keys or other secrets are never written to logs in plaintext."""
    settings_payload = {
        "api_key": "sk-test-redact-me",
        "theme": "dark",
        "model": "anthropic/claude-3-haiku",
    }

    caplog.clear()
    with caplog.at_level(logging.INFO, logger="personal_ai_chatbot"):
        result = gradio_interface._handle_settings_save(settings_payload)

    assert result["success"] is True
    assert settings_payload["api_key"] == "sk-test-redact-me"

    settings_logs = [
        record for record in caplog.records if "Settings saved" in record.getMessage()
    ]
    assert settings_logs, "Expected a settings saved log entry"

    for record in settings_logs:
        message = record.getMessage()
        assert "sk-test-redact-me" not in message
        assert "theme" in message

        if hasattr(record, "settings"):
            assert record.settings["api_key"] == "[REDACTED]"
            assert record.settings["theme"] == "dark"
            assert record.settings["model"] == "anthropic/claude-3-haiku"
