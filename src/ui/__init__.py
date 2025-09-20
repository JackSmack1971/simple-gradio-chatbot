"""User Interface layer for Personal AI Chatbot."""

from .gradio_interface import GradioInterface
from .components import ChatPanel, SettingsPanel

__version__ = "1.0.0"
__all__ = ["GradioInterface", "ChatPanel", "SettingsPanel"]