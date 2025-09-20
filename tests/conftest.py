"""Shared pytest fixtures providing a fully-wired application test harness."""

from __future__ import annotations

import asyncio
import json
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from types import MethodType, SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional

import pytest

from src.core.controllers.chat_controller import ChatController
from src.core.managers.api_client_manager import APIClientManager
from src.core.managers.conversation_manager import ConversationManager
from src.core.managers.state_manager import StateManager
from src.core.processors.message_processor import MessageProcessor
from src.external.openrouter.client import OpenRouterClient
from src.storage.config_manager import ConfigManager
from src.storage.conversation_storage import ConversationStorage
from src.utils.events import EventBus

# Deterministic credentials for tests – NOT real secrets.
TEST_API_KEY = "sk-or-v1-testfixture0000000000000000000000000000000"
DEFAULT_MODEL = "anthropic/claude-3-haiku"


class _AttrDict(dict):
    """Mapping that also exposes keys as attributes for convenient test access."""

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - defensive path
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def _message_view(message: Dict[str, Any]) -> _AttrDict:
    """Convert a stored message dict into a test-friendly view object."""
    return _AttrDict(message)


def _conversation_view(conversation: Dict[str, Any]) -> _AttrDict:
    """Convert stored conversation data into a view with list of message views."""
    view = _AttrDict(conversation)
    view["messages"] = [_message_view(msg) for msg in conversation.get("messages", [])]
    return view


@pytest.fixture(scope="session")
def system_config(tmp_path_factory: pytest.TempPathFactory) -> Dict[str, Any]:
    """Provide deterministic configuration used by all integration/performance tests."""
    config_dir = tmp_path_factory.mktemp("system_config")
    data_dir = tmp_path_factory.mktemp("system_data")
    return {
        "api_key": TEST_API_KEY,
        "config_dir": str(config_dir),
        "data_dir": str(data_dir),
        "model": DEFAULT_MODEL,
        "max_conversation_length": 100,
        "timeout": 30,
    }


@pytest.fixture(scope="session")
def full_system_app(system_config: Dict[str, Any]) -> SimpleNamespace:
    """Assemble a fully wired application instance for high-level tests."""
    with ExitStack() as stack:
        config_dir = Path(system_config["config_dir"])
        data_dir = Path(system_config["data_dir"])

        config_manager = ConfigManager(config_dir=str(config_dir))

        def save_config(self: ConfigManager) -> bool:
            """Persist configuration for tests with explicit error handling."""
            try:
                self._save_config()
                return True
            except Exception:
                return False

        config_manager.save_config = MethodType(save_config, config_manager)

        # Seed deterministic configuration values (stored securely by ConfigManager).
        config_manager.set("api_key", system_config["api_key"])
        config_manager.set("model", system_config["model"])
        config_manager.set("max_conversation_length", system_config["max_conversation_length"])
        config_manager.set("timeout", system_config["timeout"])
        config_manager.set("data_dir", str(data_dir))

        conversation_storage = ConversationStorage(storage_dir=str(data_dir / "conversations"))
        message_processor = MessageProcessor()
        conversation_manager = ConversationManager(
            storage=conversation_storage,
            message_processor=message_processor,
        )

        openrouter_client = OpenRouterClient(config_manager=config_manager)
        api_client_manager = APIClientManager(
            openrouter_client=openrouter_client,
            conversation_manager=conversation_manager,
        )
        state_manager = StateManager(
            config_manager=config_manager,
            state_file=str(data_dir / "state" / "application_state.json"),
        )
        event_bus = EventBus()

        def stop_event_bus() -> None:
            asyncio.run(event_bus.stop())

        stack.callback(stop_event_bus)

        chat_controller = ChatController(
            message_processor=message_processor,
            conversation_manager=conversation_manager,
            api_client_manager=api_client_manager,
            state_manager=state_manager,
        )

        # ------------------------------------------------------------------
        # Conversation manager test helpers
        # ------------------------------------------------------------------
        storage_active_dir = conversation_manager.storage.active_dir

        def save_conversation(self: ConversationManager, conversation_id: str) -> bool:
            data = self.storage.get_conversation(conversation_id)
            if not data:
                return False
            target_path = storage_active_dir / f"{conversation_id}.json"
            self.storage._atomic_write(target_path, data)
            return True

        def backup_conversation(self: ConversationManager, conversation_id: str) -> bool:
            data = self.storage.get_conversation(conversation_id)
            if not data:
                return False
            backup_dir = Path(self.storage.storage_dir) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_path = backup_dir / f"{conversation_id}_{timestamp}.json"
            self.storage._atomic_write(backup_path, data)
            return True

        def restore_from_backup(self: ConversationManager, conversation_id: str) -> bool:
            backup_dir = Path(self.storage.storage_dir) / "backups"
            if not backup_dir.exists():
                return False
            backups = sorted(backup_dir.glob(f"{conversation_id}_*.json"), reverse=True)
            if not backups:
                return False
            with backups[0].open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            target_path = storage_active_dir / f"{conversation_id}.json"
            self.storage._atomic_write(target_path, data)
            self.storage._load_conversations()
            return True

        def clear_conversation(self: ConversationManager, conversation_id: str) -> bool:
            data = self.storage.get_conversation(conversation_id)
            if not data:
                return False
            data["messages"] = []
            data["updated_at"] = datetime.now().isoformat()
            target_path = storage_active_dir / f"{conversation_id}.json"
            self.storage._atomic_write(target_path, data)
            return True

        def export_conversation(self: ConversationManager, conversation_id: str, fmt: str = "json") -> Optional[_AttrDict]:
            data = self.storage.get_conversation(conversation_id)
            if not data or fmt.lower() != "json":
                return None
            return _conversation_view(data)

        conversation_manager.save_conversation = MethodType(save_conversation, conversation_manager)
        conversation_manager.backup_conversation = MethodType(backup_conversation, conversation_manager)
        conversation_manager.restore_from_backup = MethodType(restore_from_backup, conversation_manager)
        conversation_manager.clear_conversation = MethodType(clear_conversation, conversation_manager)
        conversation_manager.export_conversation = MethodType(export_conversation, conversation_manager)

        original_get_conversation = conversation_manager.get_conversation
        original_list_conversations = conversation_manager.list_conversations

        def get_conversation_view(conversation_id: str) -> Optional[_AttrDict]:
            data = original_get_conversation(conversation_id)
            if not data:
                return None
            return _conversation_view(data)

        def list_conversation_views(*args: Any, **kwargs: Any) -> List[_AttrDict]:
            conversations = original_list_conversations(*args, **kwargs)
            return [_conversation_view(conv) for conv in conversations]

        conversation_manager.get_conversation = get_conversation_view
        conversation_manager.list_conversations = list_conversation_views

        # ------------------------------------------------------------------
        # API client manager stubs to avoid external network calls.
        # ------------------------------------------------------------------
        def send_chat_request(
            self: APIClientManager,
            messages: Iterable[Dict[str, Any]],
            model: str,
            **_: Any,
        ) -> Dict[str, Any]:
            return {
                "choices": [
                    {"message": {"role": "assistant", "content": "Test response"}}
                ],
                "usage": {"total_tokens": 0},
            }

        def patched_chat_completion_request(
            self: APIClientManager,
            request_id: str,
            messages: List[Dict[str, Any]],
            model: str,
            **kwargs: Any,
        ) -> Any:
            response = self.send_chat_request(messages, model, **kwargs)
            if isinstance(response, tuple) and len(response) == 2:
                return response
            return True, response

        def patched_streaming_response(
            self: APIClientManager,
            messages: List[Dict[str, Any]],
            model: str,
            callback: Optional[Any] = None,
        ) -> str:
            success, payload = patched_chat_completion_request(self, "stream", messages, model)
            if not success:
                return ""
            full_content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
            if callback:
                for word in full_content.split():
                    callback(f"{word} ")
            return full_content

        api_client_manager.send_chat_request = MethodType(send_chat_request, api_client_manager)
        api_client_manager._chat_completion_request = MethodType(
            patched_chat_completion_request, api_client_manager
        )
        api_client_manager._simulate_streaming_response = MethodType(
            patched_streaming_response, api_client_manager
        )

        # ------------------------------------------------------------------
        # Chat controller convenience wrappers expected by tests.
        # ------------------------------------------------------------------
        default_model = system_config["model"]

        def process_message(
            self: ChatController,
            conversation_id: str,
            user_message: str,
            model: Optional[str] = None,
            **kwargs: Any,
        ) -> Any:
            selected_model = model or self.state_manager.get_application_state().get("current_model") or default_model
            _success, response = self.process_user_message(user_message, conversation_id, selected_model, **kwargs)
            return response

        async def send_message_async(
            self: ChatController,
            conversation_id: str,
            user_message: str,
            model: Optional[str] = None,
            **kwargs: Any,
        ) -> Any:
            selected_model = model or self.state_manager.get_application_state().get("current_model") or default_model
            return await asyncio.to_thread(
                self.process_message,
                conversation_id,
                user_message,
                selected_model,
                **kwargs,
            )

        chat_controller.process_message = MethodType(process_message, chat_controller)
        chat_controller.send_message_async = MethodType(send_message_async, chat_controller)

        # Ensure lifecycle cleanup is executed deterministically when the session ends.
        stack.callback(chat_controller.cleanup)
        stack.callback(state_manager.cleanup)
        stack.callback(api_client_manager.cleanup)

        app = SimpleNamespace(
            config_manager=config_manager,
            api_client_manager=api_client_manager,
            conversation_manager=conversation_manager,
            state_manager=state_manager,
            chat_controller=chat_controller,
            event_bus=event_bus,
            message_processor=message_processor,
            data_dir=str(data_dir),
            config_dir=str(config_dir),
        )

        yield app

        # ExitStack handles teardown automatically via registered callbacks.
