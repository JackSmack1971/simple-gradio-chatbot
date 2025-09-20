# src/ui/components/settings_panel.py
"""
Settings panel component for application configuration.

Provides modal interface for API settings, UI preferences, and model settings.
"""

import gradio as gr
from typing import Dict, Any, Optional, Callable


class SettingsPanel:
    """
    Settings panel for application configuration.
    """

    def __init__(self):
        """Initialize the settings panel."""
        # Default settings
        self.settings = {
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

        # Event handlers
        self.on_settings_save: Optional[Callable] = None
        self.on_api_key_update: Optional[Callable] = None

    def create_settings_panel(self) -> None:
        """
        Create the settings panel UI components.

        This method should be called within a Gradio Blocks context.
        """
        with gr.Blocks() as self.settings_modal:
            with gr.Column(elem_id="settings-modal"):
                # Header
                gr.HTML("""
                    <div style="display: flex; align-items: space-between; padding: 1rem; border-bottom: 1px solid var(--border-color);">
                        <h2 style="margin: 0; font-size: 1.25rem; font-weight: 600;">⚙️ Settings</h2>
                        <button onclick="closeSettings()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
                    </div>
                """)

                # Settings content
                with gr.Tabs():
                    with gr.TabItem("API Configuration"):
                        self._create_api_settings()

                    with gr.TabItem("UI Preferences"):
                        self._create_ui_settings()

                    with gr.TabItem("Model Settings"):
                        self._create_model_settings()

                # Action buttons
                with gr.Row(elem_id="settings-actions"):
                    self.save_button = gr.Button(
                        "Save Settings",
                        variant="primary",
                        elem_id="save-settings"
                    )

                    self.reset_button = gr.Button(
                        "Reset to Default",
                        variant="secondary",
                        elem_id="reset-settings"
                    )

        # Set up event handlers
        self._setup_event_handlers()

    def _create_api_settings(self) -> None:
        """Create API configuration settings."""
        with gr.Column():
            gr.HTML("<h3 style='margin-top: 0;'>API Configuration</h3>")

            # API Key
            self.api_key_input = gr.Textbox(
                label="OpenRouter API Key",
                placeholder="sk-or-v1-...",
                type="password",
                value=self._mask_api_key(self.settings["api_key"]),
                elem_id="api-key-input"
            )

            # API Key actions
            with gr.Row():
                self.update_api_key_button = gr.Button(
                    "Update API Key",
                    variant="secondary",
                    size="sm",
                    elem_id="update-api-key"
                )

                self.test_connection_button = gr.Button(
                    "Test Connection",
                    variant="secondary",
                    size="sm",
                    elem_id="test-connection"
                )

            # Connection settings
            self.timeout_input = gr.Number(
                label="Request Timeout (seconds)",
                value=30,
                minimum=5,
                maximum=120,
                elem_id="timeout-input"
            )

            self.retry_input = gr.Number(
                label="Max Retries",
                value=3,
                minimum=0,
                maximum=10,
                elem_id="retry-input"
            )

    def _create_ui_settings(self) -> None:
        """Create UI preferences settings."""
        with gr.Column():
            gr.HTML("<h3 style='margin-top: 0;'>UI Preferences</h3>")

            # Theme
            self.theme_dropdown = gr.Dropdown(
                label="Theme",
                choices=["Light", "Dark", "Auto"],
                value=self._capitalize_first(self.settings["theme"]),
                elem_id="theme-dropdown"
            )

            # Font size
            self.font_size_dropdown = gr.Dropdown(
                label="Font Size",
                choices=["Small", "Medium", "Large"],
                value=self._capitalize_first(self.settings["font_size"]),
                elem_id="font-size-dropdown"
            )

            # Toggles
            self.notifications_checkbox = gr.Checkbox(
                label="Enable notifications",
                value=self.settings["notifications"],
                elem_id="notifications-checkbox"
            )

            self.auto_save_checkbox = gr.Checkbox(
                label="Auto-save conversations",
                value=self.settings["auto_save"],
                elem_id="auto-save-checkbox"
            )

            self.timestamps_checkbox = gr.Checkbox(
                label="Show message timestamps",
                value=self.settings["show_timestamps"],
                elem_id="timestamps-checkbox"
            )

    def _create_model_settings(self) -> None:
        """Create model-specific settings."""
        with gr.Column():
            gr.HTML("<h3 style='margin-top: 0;'>Model Settings</h3>")

            # Default model
            self.default_model_dropdown = gr.Dropdown(
                label="Default Model",
                choices=[
                    "anthropic/claude-3-haiku",
                    "anthropic/claude-3-sonnet",
                    "openai/gpt-4",
                    "openai/gpt-3.5-turbo",
                    "google/gemini-pro",
                    "meta/llama-2-70b-chat"
                ],
                value=self.settings["default_model"],
                elem_id="default-model-dropdown"
            )

            # Generation parameters
            self.temperature_slider = gr.Slider(
                label="Temperature",
                minimum=0.0,
                maximum=2.0,
                value=self.settings["temperature"],
                step=0.1,
                elem_id="temperature-slider"
            )

            self.max_tokens_input = gr.Number(
                label="Max Tokens",
                value=self.settings["max_tokens"],
                minimum=1,
                maximum=32768,
                elem_id="max-tokens-input"
            )

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for settings interactions."""
        # Save settings
        self.save_button.click(
            fn=self._handle_save_settings,
            inputs=self._get_all_setting_inputs(),
            outputs=[]
        )

        # Reset settings
        self.reset_button.click(
            fn=self._handle_reset_settings,
            outputs=self._get_all_setting_inputs()
        )

        # API key update
        self.update_api_key_button.click(
            fn=self._handle_api_key_update,
            inputs=[self.api_key_input],
            outputs=[]
        )

        # Test connection
        self.test_connection_button.click(
            fn=self._handle_test_connection,
            outputs=[]
        )

    def _get_all_setting_inputs(self) -> list:
        """Get all setting input components."""
        return [
            self.api_key_input,
            self.timeout_input,
            self.retry_input,
            self.theme_dropdown,
            self.font_size_dropdown,
            self.notifications_checkbox,
            self.auto_save_checkbox,
            self.timestamps_checkbox,
            self.default_model_dropdown,
            self.temperature_slider,
            self.max_tokens_input
        ]

    def _handle_save_settings(self, *args) -> None:
        """Handle saving settings."""
        # Map arguments to settings
        settings_data = {
            "api_key": args[0],
            "timeout": args[1],
            "retry_count": args[2],
            "theme": args[3].lower(),
            "font_size": args[4].lower(),
            "notifications": args[5],
            "auto_save": args[6],
            "show_timestamps": args[7],
            "default_model": args[8],
            "temperature": args[9],
            "max_tokens": args[10]
        }

        # Update local settings
        self.settings.update(settings_data)

        # Call external handler
        if self.on_settings_save:
            self.on_settings_save(settings_data)

    def _handle_reset_settings(self) -> list:
        """Handle resetting settings to defaults."""
        default_settings = {
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

        self.settings.update(default_settings)

        # Return values for UI update
        return [
            self._mask_api_key(default_settings["api_key"]),
            30,  # timeout
            3,   # retry
            "Light",  # theme
            "Medium",  # font_size
            True,  # notifications
            True,  # auto_save
            True,  # timestamps
            default_settings["default_model"],
            default_settings["temperature"],
            default_settings["max_tokens"]
        ]

    def _handle_api_key_update(self, api_key: str) -> None:
        """Handle API key update."""
        # Call external handler
        if self.on_api_key_update:
            result = self.on_api_key_update(api_key)
            if result and result.get("success"):
                # Update masked display
                self.api_key_input.value = self._mask_api_key(api_key)

    def _handle_test_connection(self) -> None:
        """Handle connection testing."""
        # This would test the API connection
        print("Testing API connection...")

    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for display."""
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return api_key
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

    def _capitalize_first(self, text: str) -> str:
        """Capitalize first letter."""
        return text.capitalize() if text else ""

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        return self.settings.copy()

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Update settings."""
        self.settings.update(new_settings)

    def show_panel(self) -> None:
        """Show the settings panel."""
        # In Gradio, this would make the modal visible
        pass

    def hide_panel(self) -> None:
        """Hide the settings panel."""
        # In Gradio, this would hide the modal
        pass

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format."""
        # Basic validation - should start with sk-or-v1-
        return api_key.startswith("sk-or-v1-") and len(api_key) > 20