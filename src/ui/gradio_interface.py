# src/ui/gradio_interface.py
"""
Main Gradio interface for the Personal AI Chatbot.

This module provides the complete web interface using Gradio, integrating
all UI components with the ChatController and EventBus for real-time updates.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import json
from typing import Dict, Any, Optional, Callable

import gradio as gr

from ..core.controllers.chat_controller import ChatController
from ..utils.events import EventBus, EventType, EventPriority, publish_event_sync
from ..utils.logging import logger
from .components.header_bar import HeaderBar
from .components.sidebar_panel import SidebarPanel
from .components.chat_panel import ChatPanel
from .components.input_panel import InputPanel
from .components.settings_panel import SettingsPanel


@dataclass
class MessageInputAdapter:
    """Adapter exposing message input component accessibility metadata."""

    component: gr.Textbox
    label_text: str
    aria_label: Optional[str]
    describedby_id: Optional[str]
    help_text: Optional[str]
    show_label: bool
    container: bool

    def to_metadata(self) -> Dict[str, Any]:
        """Return metadata dictionary for testing and inspection."""
        return {
            "label_text": self.label_text,
            "aria_label": self.aria_label,
            "describedby_id": self.describedby_id,
            "help_text": self.help_text,
            "show_label": self.show_label,
            "container": self.container,
        }


class GradioInterface:
    """
    Main Gradio interface application.

    Orchestrates all UI components and manages state synchronization
    between the frontend and backend systems.
    """

    def __init__(self, chat_controller: Optional[ChatController] = None,
                 event_bus: Optional[EventBus] = None):
        """
        Initialize the Gradio interface.

        Args:
            chat_controller: Chat controller instance
            event_bus: Event bus instance
        """
        self.chat_controller = chat_controller or ChatController()
        self.event_bus = event_bus or EventBus()

        # Initialize components
        self.header_bar = HeaderBar()
        self.sidebar_panel = SidebarPanel()
        self.chat_panel = ChatPanel()
        self.input_panel = InputPanel()
        self.settings_panel = SettingsPanel()

        # Application state
        self.current_conversation_id = None
        self.current_model = "anthropic/claude-3-haiku"
        self.is_streaming = False

        # Performance tracking
        self.load_start_time = None

        # Track interface/state lifecycle
        self.interface: Optional[gr.Blocks] = None
        self._state_initialized = False

        # Adapter handles
        self.message_input_adapter: Optional[MessageInputAdapter] = None

        # Instantiate interface immediately so component handles exist post-init
        self.interface = self.create_interface(run_state_setup=False)

        logger.info("GradioInterface initialized")

    def create_interface(self, run_state_setup: bool = True) -> gr.Blocks:
        """
        Create the main Gradio interface.

        Args:
            run_state_setup: Whether to initialize conversation state immediately.

        Returns:
            Gradio Blocks interface
        """
        if self.interface is not None:
            if run_state_setup and not self._state_initialized:
                self._setup_state_management()
                self._state_initialized = True
            return self.interface

        self.load_start_time = datetime.now()

        # Create main interface with custom theme
        interface = gr.Blocks(
            title="Personal AI Chatbot",
            theme=self._create_theme(),
            css=self._get_custom_css()
        )

        with interface:
            # Header
            with gr.Row(elem_id="header"):
                self.model_display, self.status_display = self.header_bar.create_header()

            # Main content area
            with gr.Row(elem_id="main-content"):
                # Sidebar
                with gr.Column(scale=1, elem_id="sidebar"):
                    self.model_dropdown, self.model_info, self.new_conversation_btn, self.conversations_container = self.sidebar_panel.create_sidebar()

                # Main chat area
                with gr.Column(scale=3, elem_id="chat-area"):
                    # Chat panel
                    self.conversation_header, self.messages_container, self.streaming_indicator = self.chat_panel.create_chat_panel()

                    # Input panel
                    self.message_input, self.character_counter, self.send_button = self.input_panel.create_input_panel()

            # Settings panel (modal) - TODO: Implement modal system
            # self.settings_panel.create_settings_panel()

        # Set up event handlers and state management
        self._setup_event_handlers(interface)

        # Update adapters for accessibility metadata
        if self.message_input is not None:
            metadata = self.input_panel.get_message_input_accessibility_metadata()
            self.message_input_adapter = MessageInputAdapter(
                component=self.message_input,
                label_text=metadata.get("label_text"),
                aria_label=metadata.get("aria_label"),
                describedby_id=metadata.get("describedby_id"),
                help_text=metadata.get("help_text"),
                show_label=bool(metadata.get("show_label")),
                container=bool(metadata.get("container")),
            )

        if run_state_setup:
            self._setup_state_management()
            self._state_initialized = True
        else:
            self._state_initialized = False

        # Subscribe to events
        self._setup_event_subscriptions()

        self.interface = interface

        logger.info("Gradio interface created")
        return interface

    def get_message_input_metadata(self) -> Dict[str, Any]:
        """Expose message input accessibility metadata for tests."""
        if self.message_input_adapter:
            return self.message_input_adapter.to_metadata()
        return {}

    def _create_theme(self):
        """Create custom Gradio theme."""
        # Using default theme for now - Gradio themes API may vary
        return None

    def _get_custom_css(self) -> str:
        """Get custom CSS for the interface."""
        return """
        /* Custom styles for accessibility and design */
        .gradio-container {
            max-width: 1400px !important;
            margin: 0 auto;
        }

        #header {
            border-bottom: 1px solid var(--border-color);
            padding: 1rem;
            background: var(--background-fill-primary);
        }

        #sidebar {
            border-right: 1px solid var(--border-color);
            padding: 1rem;
            background: var(--background-fill-secondary);
            min-height: 600px;
        }

        #chat-area {
            padding: 1rem;
            display: flex;
            flex-direction: column;
            min-height: 600px;
        }

        /* Message bubbles */
        .message-user {
            background: var(--color-accent);
            color: white;
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 1rem 1rem 0.25rem 1rem;
            max-width: 80%;
            align-self: flex-end;
        }

        .message-assistant {
            background: var(--background-fill-secondary);
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 1rem 1rem 1rem 0.25rem;
            max-width: 80%;
            align-self: flex-start;
        }

        /* Focus indicators for accessibility */
        button:focus, input:focus, select:focus, textarea:focus {
            outline: 2px solid var(--color-accent);
            outline-offset: 2px;
        }

        /* Loading states */
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }

        /* Responsive design */
        @media (max-width: 1023px) {
            #sidebar {
                display: none;
            }
            #chat-area {
                width: 100%;
            }
        }

        @media (max-width: 767px) {
            .gradio-container {
                padding: 0.5rem;
            }
            #header, #chat-area {
                padding: 0.5rem;
            }
        }
        """

    def _setup_event_handlers(self, interface: gr.Blocks) -> None:
        """Set up event handlers for UI interactions."""
        # Input panel events
        self.input_panel.on_send_message = self._handle_send_message
        self.input_panel.on_input_change = self._handle_input_change

        # Sidebar events
        self.sidebar_panel.on_model_select = self._handle_model_select
        self.sidebar_panel.on_conversation_select = self._handle_conversation_select
        self.sidebar_panel.on_new_conversation = self._handle_new_conversation

        # Settings events
        self.settings_panel.on_settings_save = self._handle_settings_save
        self.settings_panel.on_api_key_update = self._handle_api_key_update

        # Chat panel events
        self.chat_panel.on_message_action = self._handle_message_action

    def _setup_state_management(self) -> None:
        """Set up state management for the interface."""
        # Initialize with default conversation
        if not self.current_conversation_id:
            self._create_new_conversation()

    def _setup_event_subscriptions(self) -> None:
        """Set up event bus subscriptions."""
        # Subscribe to chat controller events
        self.event_bus.subscribe(EventType.STATE_CHANGE, self._handle_state_change)
        self.event_bus.subscribe(EventType.ERROR, self._handle_error_event)
        self.event_bus.subscribe(EventType.API_RESPONSE, self._handle_api_response)

    async def _handle_send_message(self, message: str) -> Dict[str, Any]:
        """Handle sending a message."""
        if not message.strip():
            return {"error": "Message cannot be empty"}

        # Ensure we have a conversation
        if not self.current_conversation_id:
            self._create_new_conversation()

        try:
            # Disable input during processing
            self.input_panel.set_disabled(True)

            # Add user message to chat
            user_message_id = self.chat_panel.add_user_message(message)

            # Clear input
            self.input_panel.clear_input()

            # Start streaming response
            self.is_streaming = True
            success, response = self.chat_controller.start_streaming_response(
                message,
                str(self.current_conversation_id),
                self.current_model,
                self._handle_streaming_chunk
            )

            if success:
                # Add assistant message
                assistant_message_id = self.chat_panel.add_assistant_message("")
                self.chat_panel.start_streaming(assistant_message_id)

                # Process streaming chunks
                full_response = ""
                for chunk in self._parse_streaming_response(response):
                    full_response += chunk
                    self.chat_panel.append_to_streaming_message(chunk)

                # Complete streaming
                self.chat_panel.complete_streaming()
                self.is_streaming = False

                # Update conversation
                self._update_conversation_metadata()

                return {"success": True, "message_id": assistant_message_id}
            else:
                # Handle error
                self.chat_panel.mark_message_failed(user_message_id)
                return {"error": response}

        except Exception as e:
            logger.error(f"Send message failed: {str(e)}")
            return {"error": f"Failed to send message: {str(e)}"}
        finally:
            self.input_panel.set_disabled(False)
            self.input_panel.focus_input()

    def _handle_streaming_chunk(self, chunk: str) -> None:
        """Handle streaming response chunks."""
        if self.is_streaming:
            self.chat_panel.append_to_streaming_message(chunk)

    def _parse_streaming_response(self, response: str):
        """Parse streaming response into chunks."""
        # Simple implementation - split by words for demo
        words = response.split()
        for word in words:
            yield word + " "
            # Small delay for streaming effect
            import time
            time.sleep(0.05)

    def _handle_input_change(self, value: str) -> None:
        """Handle input field changes."""
        length = len(value)
        self.input_panel.update_character_count(length)

        # Enable/disable send button
        max_length = 2000  # From specs
        self.input_panel.set_send_enabled(length > 0 and length <= max_length)

    async def _handle_model_select(self, model_id: str) -> Dict[str, Any]:
        """Handle model selection."""
        try:
            # Update model in controller
            success = await asyncio.get_event_loop().run_in_executor(
                None, self.chat_controller.update_model, model_id
            )

            if success:
                self.current_model = model_id
                self.header_bar.update_model_display(model_id)
                self.sidebar_panel.update_current_model(model_id)

                # Publish event
                publish_event_sync(
                    EventType.STATE_CHANGE,
                    {"type": "model_changed", "model": model_id},
                    source="gradio_interface"
                )

                return {"success": True, "model": model_id}
            else:
                return {"error": "Failed to update model"}

        except Exception as e:
            logger.error(f"Model selection failed: {str(e)}")
            return {"error": str(e)}

    async def _handle_conversation_select(self, conversation_id: str) -> Dict[str, Any]:
        """Handle conversation selection."""
        try:
            # Load conversation
            success = await asyncio.get_event_loop().run_in_executor(
                None, self.chat_controller.load_conversation, conversation_id
            )

            if success:
                self.current_conversation_id = conversation_id
                self.chat_panel.load_conversation(conversation_id)

                return {"success": True, "conversation_id": conversation_id}
            else:
                return {"error": "Failed to load conversation"}

        except Exception as e:
            logger.error(f"Conversation selection failed: {str(e)}")
            return {"error": str(e)}

    async def _handle_new_conversation(self) -> Dict[str, Any]:
        """Handle new conversation creation."""
        try:
            self._create_new_conversation()
            self.chat_panel.clear_messages()
            if self.current_conversation_id:
                self.sidebar_panel.add_conversation(str(self.current_conversation_id))

            return {"success": True, "conversation_id": self.current_conversation_id}
        except Exception as e:
            logger.error(f"New conversation failed: {str(e)}")
            return {"error": str(e)}

    def _create_new_conversation(self) -> None:
        """Create a new conversation."""
        # Generate conversation ID
        import uuid
        self.current_conversation_id = f"conv_{uuid.uuid4().hex[:8]}"

        # Initialize conversation in controller
        # Note: This would typically call chat_controller.create_new_conversation()

    def _handle_settings_save(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Handle settings save."""
        try:
            # Save settings via config manager
            # This would integrate with the config management system
            logger.info(f"Settings saved: {settings}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Settings save failed: {str(e)}")
            return {"error": str(e)}

    def _handle_api_key_update(self, api_key: str) -> Dict[str, Any]:
        """Handle API key update."""
        try:
            # Validate and update API key
            # This would integrate with the API client manager
            logger.info("API key updated")
            return {"success": True}
        except Exception as e:
            logger.error(f"API key update failed: {str(e)}")
            return {"error": str(e)}

    def _handle_message_action(self, action: str, message_id: str) -> Dict[str, Any]:
        """Handle message actions (copy, edit, regenerate)."""
        try:
            if action == "copy":
                # Copy message to clipboard
                message_content = self.chat_panel.get_message_content(message_id)
                # This would use navigator.clipboard in frontend
                return {"success": True, "action": "copy"}
            elif action == "edit":
                # Enable editing mode
                self.chat_panel.enable_message_editing(message_id)
                return {"success": True, "action": "edit"}
            elif action == "regenerate":
                # Regenerate response
                self._handle_regenerate_message(message_id)
                return {"success": True, "action": "regenerate"}
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Message action failed: {str(e)}")
            return {"error": str(e)}

    def _handle_regenerate_message(self, message_id: str) -> None:
        """Handle message regeneration."""
        # Find the user message that prompted this response
        user_message = self.chat_panel.get_user_message_for_response(message_id)
        if user_message:
            # Trigger send with the same message
            asyncio.create_task(self._handle_send_message(user_message))

    def _handle_state_change(self, event) -> None:
        """Handle state change events."""
        event_data = event.data
        if event_data.get("type") == "model_changed":
            self.current_model = event_data["model"]
            self.header_bar.update_model_display(self.current_model)
        elif event_data.get("type") == "conversation_loaded":
            self.current_conversation_id = event_data["conversation_id"]
            self.chat_panel.load_conversation(self.current_conversation_id)

    def _handle_error_event(self, event) -> None:
        """Handle error events."""
        error_data = event.data
        self._show_error_notification(error_data.get("message", "An error occurred"))

    def _handle_api_response(self, event) -> None:
        """Handle API response events."""
        response_data = event.data
        # Update UI based on API response
        if response_data.get("type") == "chat_completion":
            # Handle completion response
            pass

    def _show_error_notification(self, message: str) -> None:
        """Show error notification to user."""
        # This would integrate with Gradio's notification system
        logger.error(f"UI Error: {message}")

    def _update_conversation_metadata(self) -> None:
        """Update conversation metadata after changes."""
        # Update last activity time, message count, etc.
        if self.current_conversation_id:
            self.sidebar_panel.update_conversation_metadata(
                str(self.current_conversation_id),
                {"last_activity": datetime.now().isoformat()}
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get interface performance metrics."""
        load_time = None
        if self.load_start_time:
            load_time = (datetime.now() - self.load_start_time).total_seconds()

        return {
            "interface_load_time": load_time,
            "current_conversation": self.current_conversation_id,
            "current_model": self.current_model,
            "is_streaming": self.is_streaming
        }


def create_gradio_interface(chat_controller: Optional[ChatController] = None,
                           event_bus: Optional[EventBus] = None) -> gr.Blocks:
    """
    Create and return the main Gradio interface.

    Args:
        chat_controller: Chat controller instance
        event_bus: Event bus instance

    Returns:
        Gradio Blocks interface
    """
    interface = GradioInterface(chat_controller, event_bus)
    return interface.create_interface()