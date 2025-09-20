# src/ui/components/input_panel.py
"""
Input panel component for message composition and sending.

Handles text input, character counting, and send functionality.
"""

import gradio as gr
from typing import Dict, Any, Optional, Callable


class InputPanel:
    """
    Input panel for composing and sending messages.
    """

    def __init__(self, max_length: int = 2000):
        """Initialize the input panel."""
        self.max_length = max_length
        self.current_length = 0
        self.disabled = False

        # Event handlers
        self.on_send_message: Optional[Callable] = None
        self.on_input_change: Optional[Callable] = None

    def create_input_panel(self):
        """
        Create the input panel UI components.

        Returns:
            Tuple of (message_input, character_counter, send_button)
        """
        # Input area
        with gr.Row(elem_id="input-area"):
            with gr.Column(scale=1):
                # Text input
                message_input = gr.Textbox(
                    label="",
                    placeholder="Type your message...",
                    lines=3,
                    max_lines=6,
                    show_label=False,
                    container=False,
                    elem_id="message-input",
                    interactive=not self.disabled
                )

                # Character counter and controls
                with gr.Row(elem_id="input-controls"):
                    character_counter = gr.HTML(
                        self._get_character_count_html(),
                        elem_id="character-counter"
                    )

                    # Action buttons
                    with gr.Row():
                        voice_button = gr.Button(
                            "🎤",
                            variant="secondary",
                            size="sm",
                            elem_id="voice-btn",
                            interactive=False  # Disabled for now
                        )

                        attach_button = gr.Button(
                            "📎",
                            variant="secondary",
                            size="sm",
                            elem_id="attach-btn",
                            interactive=False  # Disabled for now
                        )

                        options_button = gr.Button(
                            "⚙️",
                            variant="secondary",
                            size="sm",
                            elem_id="options-btn",
                            interactive=False  # Disabled for now
                        )

                        send_button = gr.Button(
                            "📤 Send",
                            variant="primary",
                            size="sm",
                            elem_id="send-btn",
                            interactive=self._can_send()
                        )

        # Set up event handlers
        self._setup_event_handlers_with_components(message_input, character_counter, send_button)

        return message_input, character_counter, send_button

    def _setup_event_handlers_with_components(self, message_input, character_counter, send_button) -> None:
        """Set up event handlers for input interactions."""
        # Store component references
        self.message_input = message_input
        self.character_counter = character_counter
        self.send_button = send_button

        # Input change handler
        message_input.change(
            fn=self._handle_input_change,
            inputs=[message_input],
            outputs=[character_counter, send_button]
        )

        # Send button handler
        send_button.click(
            fn=self._handle_send_click,
            inputs=[message_input],
            outputs=[message_input, character_counter, send_button]
        )

        # Enter key handler (would need custom JavaScript in real implementation)
        # For now, we'll rely on the send button

    def _handle_input_change(self, value: str) -> tuple:
        """Handle input field changes."""
        self.current_length = len(value) if value else 0

        # Call external handler if set
        if self.on_input_change:
            self.on_input_change(value)

        # Return updated UI elements
        return (
            self._get_character_count_html(),
            gr.update(interactive=self._can_send())
        )

    def _handle_send_click(self, message: str) -> tuple:
        """Handle send button click."""
        if not message.strip():
            return message, self._get_character_count_html(), gr.update(interactive=False)

        # Call external handler
        if self.on_send_message:
            result = self.on_send_message(message)
            # In a real implementation, handle the async result

        # Clear input and reset state
        return "", self._get_character_count_html(), gr.update(interactive=False)

    def _get_character_count_html(self) -> str:
        """Get HTML for character counter display."""
        percentage = (self.current_length / self.max_length) * 100
        is_warning = percentage > 90
        is_error = self.current_length > self.max_length

        color = "var(--text-color-secondary)"
        if is_error:
            color = "var(--color-red)"
        elif is_warning:
            color = "var(--color-orange)"

        return f"""
            <div style="font-size: 0.75rem; color: {color}; text-align: right;">
                {self.current_length}/{self.max_length}
            </div>
        """

    def _can_send(self) -> bool:
        """Check if message can be sent."""
        return (
            not self.disabled and
            self.current_length > 0 and
            self.current_length <= self.max_length
        )

    def set_disabled(self, disabled: bool) -> None:
        """Set the disabled state of the input."""
        self.disabled = disabled
        # Update UI components

    def clear_input(self) -> None:
        """Clear the input field."""
        self.current_length = 0

    def focus_input(self) -> None:
        """Focus the input field."""
        # In Gradio, this would require JavaScript
        pass

    def update_character_count(self, length: int) -> None:
        """Update the character count display."""
        self.current_length = length

    def set_send_enabled(self, enabled: bool) -> None:
        """Enable or disable the send button."""
        # Update send button state
        pass

    def set_placeholder(self, placeholder: str) -> None:
        """Set the input placeholder text."""
        # Update placeholder text
        pass

    def get_input_value(self) -> str:
        """Get the current input value."""
        return ""

    def set_input_value(self, value: str) -> None:
        """Set the input value."""
        self.current_length = len(value)

    def show_validation_error(self, message: str) -> None:
        """Show validation error message."""
        # Security: raise explicit assertion to prevent silent validation issues
        raise AssertionError(f"Validation error: {message}")

    def get_max_length(self) -> int:
        """Get the maximum message length."""
        return self.max_length

    def set_max_length(self, length: int) -> None:
        """Set the maximum message length."""
        self.max_length = length

    def get_current_length(self) -> int:
        """Get the current input length."""
        return self.current_length

    def is_disabled(self) -> bool:
        """Check if input is disabled."""
        return self.disabled