# src/ui/components/chat_panel.py
"""
Chat panel component for displaying conversation messages.

Handles message display, streaming responses, and message interactions.
"""

import gradio as gr
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid


class Message:
    """Represents a chat message."""

    def __init__(self, id: str, role: str, content: str, timestamp: Optional[str] = None):
        self.id = id
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


class ChatPanel:
    """
    Chat panel for displaying conversation messages and handling interactions.
    """

    def __init__(self):
        """Initialize the chat panel."""
        self.messages: List[Message] = []
        self.conversation_id: Optional[str] = None
        self.is_streaming = False
        self.streaming_message_id: Optional[str] = None

        # Event handlers
        self.on_message_action: Optional[Callable] = None

    def create_chat_panel(self):
        """
        Create the chat panel UI components.

        Returns:
            Tuple of (conversation_header, messages_container, streaming_indicator)
        """
        # Conversation header
        conversation_header = gr.HTML(
            self._get_conversation_header_html(),
            elem_id="conversation-header"
        )

        # Messages container
        messages_container = gr.HTML(
            self._get_messages_html(),
            elem_id="messages-container"
        )

        # Streaming indicator (hidden by default)
        streaming_indicator = gr.HTML(
            "",
            visible=False,
            elem_id="streaming-indicator"
        )

        return conversation_header, messages_container, streaming_indicator

    def _get_conversation_header_html(self) -> str:
        """Get HTML for conversation header."""
        title = "New Conversation"
        model = "Claude 3 Haiku"

        return f"""
            <div style="padding: 1rem; border-bottom: 1px solid var(--border-color); background: var(--background-fill-primary);">
                <h2 style="margin: 0; font-size: 1.125rem; font-weight: 600;">
                    💬 {title}
                </h2>
                <div style="font-size: 0.875rem; color: var(--text-color-secondary); margin-top: 0.25rem;">
                    Model: {model}
                </div>
            </div>
        """

    def _get_messages_html(self) -> str:
        """Get HTML for messages display."""
        if not self.messages:
            return self._get_empty_state_html()

        message_htmls = []
        for message in self.messages:
            message_htmls.append(self._render_message(message))

        return "\n".join(message_htmls)

    def _get_empty_state_html(self) -> str:
        """Get HTML for empty conversation state."""
        return """
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; text-align: center; color: var(--text-color-secondary);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
                <h3 style="margin: 0 0 0.5rem 0; color: var(--text-color);">Start a conversation</h3>
                <p style="margin: 0; font-size: 0.875rem;">Type a message below to begin chatting with the AI assistant.</p>
            </div>
        """

    def _render_message(self, message: Message) -> str:
        """Render a single message."""
        is_user = message.role == "user"
        alignment = "flex-end" if is_user else "flex-start"
        background = "var(--color-accent)" if is_user else "var(--background-fill-secondary)"
        text_color = "white" if is_user else "var(--text-color)"
        border_radius = "1rem 1rem 0.25rem 1rem" if is_user else "1rem 1rem 1rem 0.25rem"

        # Format timestamp
        timestamp = self._format_timestamp(message.timestamp)

        # Action buttons for assistant messages
        actions_html = ""
        if not is_user:
            actions_html = f"""
                <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem; justify-content: {alignment};">
                    <button onclick="handleMessageAction('copy', '{message.id}')" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; border: 1px solid var(--border-color); border-radius: 0.25rem; background: var(--background-fill-primary); cursor: pointer;">📋 Copy</button>
                    <button onclick="handleMessageAction('edit', '{message.id}')" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; border: 1px solid var(--border-color); border-radius: 0.25rem; background: var(--background-fill-primary); cursor: pointer;">✏️ Edit</button>
                    <button onclick="handleMessageAction('regenerate', '{message.id}')" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; border: 1px solid var(--border-color); border-radius: 0.25rem; background: var(--background-fill-primary); cursor: pointer;">🔄 Regenerate</button>
                </div>
            """

        return f"""
            <div style="display: flex; flex-direction: column; align-items: {alignment}; margin: 1rem 0;">
                <div style="max-width: 80%; background: {background}; color: {text_color}; padding: 1rem; border-radius: {border_radius};">
                    <div style="font-size: 0.875rem; margin-bottom: 0.5rem; opacity: 0.8;">
                        {'You' if is_user else 'Assistant'} • {timestamp}
                    </div>
                    <div style="line-height: 1.5;">
                        {self._format_message_content(message.content)}
                    </div>
                </div>
                {actions_html}
            </div>
        """

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(dt.tzinfo)
            diff = now - dt

            if diff.days > 0:
                return dt.strftime("%b %d, %Y")
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600}h ago"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60}m ago"
            else:
                return "Just now"
        except:
            return "Unknown time"

    def _format_message_content(self, content: str) -> str:
        """Format message content with markdown-like features."""
        # Basic formatting - in a real implementation, use a proper markdown parser
        formatted = content.replace('\n', '<br>')

        # Code blocks (basic)
        import re
        formatted = re.sub(r'`([^`]+)`', r'<code style="background: rgba(0,0,0,0.1); padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-family: monospace;">\1</code>', formatted)

        # Bold
        formatted = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', formatted)

        # Italic
        formatted = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', formatted)

        return formatted

    def add_user_message(self, content: str) -> str:
        """Add a user message to the chat."""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        message = Message(message_id, "user", content)
        self.messages.append(message)
        return message_id

    def add_assistant_message(self, content: str) -> str:
        """Add an assistant message to the chat."""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        message = Message(message_id, "assistant", content)
        self.messages.append(message)
        return message_id

    def start_streaming(self, message_id: str) -> str:
        """Start streaming for a message. Returns the streaming indicator HTML."""
        self.is_streaming = True
        self.streaming_message_id = message_id

        # Return streaming indicator HTML
        return """
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: var(--background-fill-secondary); border-radius: 0.375rem; margin: 0.5rem 0;">
                <div style="display: flex; gap: 0.25rem;">
                    <div class="dot" style="width: 6px; height: 6px; border-radius: 50%; background: var(--color-accent); animation: pulse 1.5s infinite;"></div>
                    <div class="dot" style="width: 6px; height: 6px; border-radius: 50%; background: var(--color-accent); animation: pulse 1.5s infinite 0.5s;"></div>
                    <div class="dot" style="width: 6px; height: 6px; border-radius: 50%; background: var(--color-accent); animation: pulse 1.5s infinite 1s;"></div>
                </div>
                <span style="font-size: 0.875rem;">AI is generating response...</span>
            </div>
            <style>
                @keyframes pulse {
                    0%, 80%, 100% { opacity: 0.3; }
                    40% { opacity: 1; }
                }
            </style>
        """

    def append_to_streaming_message(self, chunk: str) -> None:
        """Append content to the currently streaming message."""
        if self.is_streaming and self.streaming_message_id:
            for message in self.messages:
                if message.id == self.streaming_message_id:
                    message.content += chunk
                    break

    def complete_streaming(self) -> None:
        """Complete the streaming process."""
        self.is_streaming = False
        self.streaming_message_id = None

    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages = []
        self.is_streaming = False
        self.streaming_message_id = None

    def load_conversation(self, conversation_id: str) -> None:
        """Load messages for a conversation."""
        self.conversation_id = conversation_id
        # In a real implementation, this would load messages from storage
        # For now, we'll keep existing messages or clear them
        self.clear_messages()

    def get_message_content(self, message_id: str) -> str:
        """Get content of a specific message."""
        for message in self.messages:
            if message.id == message_id:
                return message.content
        return ""

    def get_user_message_for_response(self, response_message_id: str) -> Optional[str]:
        """Get the user message that prompted a specific assistant response."""
        # Find the assistant message
        assistant_index = None
        for i, message in enumerate(self.messages):
            if message.id == response_message_id and message.role == "assistant":
                assistant_index = i
                break

        if assistant_index is not None and assistant_index > 0:
            # Get the previous user message
            for i in range(assistant_index - 1, -1, -1):
                if self.messages[i].role == "user":
                    return self.messages[i].content

        return None

    def enable_message_editing(self, message_id: str) -> None:
        """Enable editing for a message."""
        # In a real implementation, this would make the message editable
        # For now, just log the action
        print(f"Editing enabled for message {message_id}")

    def mark_message_failed(self, message_id: str) -> None:
        """Mark a message as failed."""
        for message in self.messages:
            if message.id == message_id:
                message.content += " (Failed to send)"
                break

    def update_conversation_title(self, title: str) -> None:
        """Update the conversation title in the header."""
        # Update the header HTML
        pass

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages as dictionaries."""
        return [msg.to_dict() for msg in self.messages]

    def get_streaming_status(self) -> Dict[str, Any]:
        """Get streaming status information."""
        return {
            "is_streaming": self.is_streaming,
            "streaming_message_id": self.streaming_message_id
        }