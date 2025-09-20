"""Resource managers for Personal AI Chatbot."""

from .conversation_manager import ConversationManager
from .api_client_manager import APIClientManager

# Provide both naming conventions for compatibility
ApiClientManager = APIClientManager

__all__ = ["ConversationManager", "APIClientManager", "ApiClientManager"]