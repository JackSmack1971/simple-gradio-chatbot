# src/ui/components/sidebar_panel.py
"""
Sidebar panel component for navigation and controls.

Provides navigation menu, model selector, and conversation management.
"""

import gradio as gr
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime


class SidebarPanel:
    """
    Sidebar panel with navigation, model selection, and conversations.
    """

    def __init__(self):
        """Initialize the sidebar panel."""
        self.current_model = "anthropic/claude-3-haiku"
        self.conversations = []
        self.available_models = [
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            "google/gemini-pro",
            "meta/llama-2-70b-chat"
        ]

        # Event handlers
        self.on_model_select: Optional[Callable] = None
        self.on_conversation_select: Optional[Callable] = None
        self.on_new_conversation: Optional[Callable] = None

    def create_sidebar(self):
        """
        Create the sidebar panel UI components.

        Returns:
            Tuple of (model_dropdown, model_info, new_conversation_btn, conversations_container)
        """
        # Navigation menu
        with gr.Accordion("Navigation", open=True):
            with gr.Column():
                self._create_navigation_menu()

        # Current model selector
        with gr.Accordion("Current Model", open=True):
            with gr.Column():
                model_dropdown, model_info = self._create_model_selector()

        # Conversations list
        with gr.Accordion("Conversations", open=True):
            with gr.Column():
                new_conversation_btn, conversations_container = self._create_conversations_list()

        return model_dropdown, model_info, new_conversation_btn, conversations_container

    def _create_navigation_menu(self) -> None:
        """Create the navigation menu."""
        navigation_items = [
            ("💬", "Conversations", "conversations"),
            ("⚙️", "Settings", "settings"),
            ("🤖", "Models", "models")
        ]

        for icon, label, action in navigation_items:
            gr.Button(
                f"{icon} {label}",
                variant="secondary",
                size="sm",
                elem_id=f"nav-{action}"
            )

    def _create_model_selector(self):
        """Create the model selector."""
        # Model dropdown
        model_dropdown = gr.Dropdown(
            choices=self.available_models,
            value=self.current_model,
            label="Select Model",
            interactive=True,
            elem_id="model-selector"
        )

        # Model info display
        model_info = gr.HTML(
            self._get_model_info_html(self.current_model),
            elem_id="model-info"
        )

        # Set up event handler for model selection
        model_dropdown.change(
            fn=self._handle_model_change,
            inputs=[model_dropdown],
            outputs=[model_info]
        )

        return model_dropdown, model_info

    def _create_conversations_list(self):
        """Create the conversations list."""
        # New conversation button
        new_conversation_btn = gr.Button(
            "➕ New Conversation",
            variant="primary",
            size="sm",
            elem_id="new-conversation"
        )

        # Conversations container
        conversations_container = gr.HTML(
            self._get_conversations_html(),
            elem_id="conversations-list"
        )

        # Set up event handlers
        new_conversation_btn.click(
            fn=self._handle_new_conversation,
            outputs=[]
        )

        return new_conversation_btn, conversations_container

    def _get_model_info_html(self, model_id: str) -> str:
        """Get HTML for model information display."""
        model_info = self._get_model_details(model_id)

        return f"""
            <div style="padding: 0.5rem; background: var(--background-fill-secondary); border-radius: 0.375rem; margin-top: 0.5rem;">
                <div style="font-weight: 500; margin-bottom: 0.25rem;">{model_info['name']}</div>
                <div style="font-size: 0.875rem; color: var(--text-color-secondary); margin-bottom: 0.5rem;">
                    {model_info['description']}
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
                    {' '.join(f'<span style="background: var(--color-accent-soft); color: var(--color-accent); padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.75rem;">{cap}</span>' for cap in model_info['capabilities'])}
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-color-secondary);">
                    💰 ${model_info['cost']}/1K tokens
                </div>
            </div>
        """

    def _get_model_details(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information for a model."""
        model_details = {
            "anthropic/claude-3-haiku": {
                "name": "Claude 3 Haiku",
                "description": "Fast and efficient model for most tasks",
                "capabilities": ["💡 Fast", "💰 Low Cost", "🎯 General"],
                "cost": "0.001"
            },
            "anthropic/claude-3-sonnet": {
                "name": "Claude 3 Sonnet",
                "description": "Balanced performance and intelligence",
                "capabilities": ["💡 Smart", "⚖️ Balanced", "🎯 General"],
                "cost": "0.002"
            },
            "openai/gpt-4": {
                "name": "GPT-4",
                "description": "OpenAI's most advanced model",
                "capabilities": ["🧠 Advanced", "💰 Higher Cost", "🎯 Complex"],
                "cost": "0.002"
            },
            "openai/gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "description": "Fast and cost-effective",
                "capabilities": ["💡 Fast", "💰 Low Cost", "🎯 General"],
                "cost": "0.001"
            },
            "google/gemini-pro": {
                "name": "Gemini Pro",
                "description": "Google's multimodal model",
                "capabilities": ["🌟 Creative", "💰 Low Cost", "🎯 General"],
                "cost": "0.001"
            },
            "meta/llama-2-70b-chat": {
                "name": "Llama 2 70B",
                "description": "Meta's open-source model",
                "capabilities": ["🔓 Open Source", "💰 Low Cost", "🎯 General"],
                "cost": "0.001"
            }
        }

        return model_details.get(model_id, {
            "name": model_id.split("/")[-1].title(),
            "description": "AI model",
            "capabilities": ["🤖 AI"],
            "cost": "0.001"
        })

    def _get_conversations_html(self) -> str:
        """Get HTML for conversations list."""
        if not self.conversations:
            return """
                <div style="text-align: center; padding: 1rem; color: var(--text-color-secondary);">
                    No conversations yet
                </div>
            """

        conversation_items = []
        for conv in self.conversations[-5:]:  # Show last 5 conversations
            conversation_items.append(f"""
                <div style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 0.375rem; margin-bottom: 0.5rem; cursor: pointer;" onclick="selectConversation('{conv['id']}')">
                    <div style="font-weight: 500; margin-bottom: 0.25rem;">{conv['title']}</div>
                    <div style="font-size: 0.875rem; color: var(--text-color-secondary);">
                        {conv['message_count']} messages • {self._format_time_ago(conv['last_activity'])}
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-color-secondary); margin-top: 0.25rem;">
                        {conv.get('preview', '')[:50]}...
                    </div>
                </div>
            """)

        return "\n".join(conversation_items)

    def _format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as time ago."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            diff = now - dt

            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        except:
            return "Unknown"

    def _handle_model_change(self, model_id: str) -> str:
        """Handle model selection change."""
        self.current_model = model_id
        if self.on_model_select:
            # This would be handled asynchronously in the main interface
            pass
        return self._get_model_info_html(model_id)

    def _handle_new_conversation(self) -> None:
        """Handle new conversation creation."""
        if self.on_new_conversation:
            # This would trigger the event handler
            pass

    def update_current_model(self, model_id: str) -> None:
        """Update the current model display."""
        self.current_model = model_id
        # Update the dropdown value and info display

    def add_conversation(self, conversation_id: str, title: str = "New Conversation") -> None:
        """Add a new conversation to the list."""
        conversation = {
            "id": conversation_id,
            "title": title,
            "message_count": 0,
            "last_activity": datetime.now().isoformat(),
            "preview": ""
        }
        self.conversations.append(conversation)

    def update_conversation_metadata(self, conversation_id: str, metadata: Dict[str, Any]) -> None:
        """Update conversation metadata."""
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                conv.update(metadata)
                break

    def get_current_model(self) -> str:
        """Get the currently selected model."""
        return self.current_model

    def get_conversations(self) -> List[Dict[str, Any]]:
        """Get the list of conversations."""
        return self.conversations.copy()