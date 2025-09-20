# src/ui/components/header_bar.py
"""
Header bar component for the Gradio interface.

Displays application branding, current model, and status indicators.
"""

import gradio as gr
from typing import Dict, Any, Optional
from datetime import datetime


class HeaderBar:
    """
    Header bar component with branding, model display, and status.
    """

    def __init__(self):
        """Initialize the header bar."""
        self.app_title = "Personal AI Chatbot"
        self.current_model = "anthropic/claude-3-haiku"
        self.connection_status = "online"

    def create_header(self):
        """
        Create the header bar UI components.

        Returns:
            Tuple of (model_display, status_display) Gradio components
        """
        with gr.Row(elem_id="header-row"):
            # Logo and title
            with gr.Column(scale=1):
                gr.HTML(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <div style="font-size: 1.5rem;">🤖</div>
                        <h1 style="margin: 0; font-size: 1.25rem; font-weight: 600;">
                            {self.app_title}
                        </h1>
                    </div>
                """)

            # Current model and status
            with gr.Column(scale=1):
                with gr.Row():
                    # Model display
                    model_display = gr.HTML(
                        self._get_model_display_html(),
                        elem_id="current-model"
                    )

                    # Status indicator
                    status_display = gr.HTML(
                        self._get_status_display_html(),
                        elem_id="connection-status"
                    )

        return model_display, status_display

    def _get_model_display_html(self) -> str:
        """Get HTML for model display."""
        return f"""
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 0.875rem; color: var(--text-color-secondary);">Model:</span>
                <span style="font-weight: 500;">{self._format_model_name(self.current_model)}</span>
            </div>
        """

    def _get_status_display_html(self) -> str:
        """Get HTML for status display."""
        status_color = {
            "online": "#10b981",    # green
            "connecting": "#f59e0b", # yellow
            "offline": "#ef4444"     # red
        }.get(self.connection_status, "#6b7280")

        return f"""
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background-color: {status_color};
                "></div>
                <span style="font-size: 0.875rem; text-transform: capitalize;">
                    {self.connection_status}
                </span>
            </div>
        """

    def _format_model_name(self, model_id: str) -> str:
        """Format model ID for display."""
        # Extract provider and model name
        if "/" in model_id:
            provider, model = model_id.split("/", 1)
            # Format provider name
            provider_names = {
                "anthropic": "Claude",
                "openai": "GPT",
                "google": "Gemini",
                "meta": "Llama"
            }
            provider_display = provider_names.get(provider, provider.title())

            # Format model name
            if "claude" in model.lower():
                return f"{provider_display} {model.split('-')[-1].title()}"
            elif "gpt" in model.lower():
                return f"{provider_display} {model.split('-')[-1].upper()}"
            else:
                return f"{provider_display} {model.title()}"
        else:
            return model_id.title()

    def update_model_display(self, model_id: str) -> None:
        """Update the model display."""
        self.current_model = model_id
        # In Gradio, this would update the component state
        # The actual update would happen through Gradio's state management

    def update_status_display(self, status: str) -> None:
        """Update the connection status display."""
        self.connection_status = status
        # Update the status indicator

    def get_current_model(self) -> str:
        """Get the currently displayed model."""
        return self.current_model

    def get_connection_status(self) -> str:
        """Get the current connection status."""
        return self.connection_status