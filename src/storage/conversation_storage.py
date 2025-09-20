# src/storage/conversation_storage.py
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..utils.logging import logger

class ConversationStorage:
    """Manages JSON-based conversation persistence with atomic writes and error recovery."""

    def __init__(self, storage_dir: str = "data/conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.active_dir = self.storage_dir / "active"
        self.active_dir.mkdir(exist_ok=True)
        self.archived_dir = self.storage_dir / "archived"
        self.archived_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._conversations: Dict[str, Dict[str, Any]] = {}
        self._load_conversations()

    def _load_conversations(self) -> None:
        """Load all conversations from storage."""
        try:
            self._conversations = {}
            for file_path in self.active_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    conversation_id = data.get('id')
                    if conversation_id:
                        self._conversations[conversation_id] = data
                except Exception as e:
                    logger.error(f"Failed to load conversation from {file_path}: {e}")
            logger.info(f"Loaded {len(self._conversations)} conversations")
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")
            self._conversations = {}

    def _atomic_write(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write data to file atomically to prevent corruption."""
        try:
            # Create temporary file in same directory
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f"{file_path.stem}_",
                suffix=".tmp"
            )

            with os.fdopen(temp_fd, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic move
            temp_file = Path(temp_path)
            temp_file.replace(file_path)

            logger.debug(f"Atomically wrote data to {file_path}")
        except Exception as e:
            logger.error(f"Failed to write data atomically to {file_path}: {e}")
            # Clean up temp file if it exists
            temp_file = Path(temp_path)
            if temp_file.exists():
                temp_file.unlink()
            raise

    def create_conversation(self, conversation_id: str, title: str = "New Conversation") -> bool:
        """Create a new conversation."""
        with self._lock:
            try:
                if conversation_id in self._conversations:
                    logger.warning(f"Conversation {conversation_id} already exists")
                    return False

                conversation = {
                    'id': conversation_id,
                    'title': title,
                    'messages': [],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'metadata': {}
                }

                self._conversations[conversation_id] = conversation
                file_path = self.active_dir / f"{conversation_id}.json"
                self._atomic_write(file_path, conversation)

                logger.info(f"Created conversation {conversation_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to create conversation {conversation_id}: {e}")
                return False

    def save_message(self, conversation_id: str, message: Dict[str, Any]) -> bool:
        """Save a message to a conversation."""
        with self._lock:
            try:
                if conversation_id not in self._conversations:
                    logger.error(f"Conversation {conversation_id} not found")
                    return False

                conversation = self._conversations[conversation_id]
                message_with_timestamp = {
                    **message,
                    'timestamp': datetime.now().isoformat()
                }
                conversation['messages'].append(message_with_timestamp)
                conversation['updated_at'] = datetime.now().isoformat()

                file_path = self.active_dir / f"{conversation_id}.json"
                self._atomic_write(file_path, conversation)

                logger.debug(f"Saved message to conversation {conversation_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to save message to conversation {conversation_id}: {e}")
                return False

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID."""
        with self._lock:
            return self._conversations.get(conversation_id)

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all active conversations."""
        with self._lock:
            return list(self._conversations.values())

    def update_conversation_metadata(self, conversation_id: str, metadata: Dict[str, Any]) -> bool:
        """Update conversation metadata."""
        with self._lock:
            try:
                if conversation_id not in self._conversations:
                    logger.error(f"Conversation {conversation_id} not found")
                    return False

                conversation = self._conversations[conversation_id]
                conversation['metadata'].update(metadata)
                conversation['updated_at'] = datetime.now().isoformat()

                file_path = self.active_dir / f"{conversation_id}.json"
                self._atomic_write(file_path, conversation)

                logger.debug(f"Updated metadata for conversation {conversation_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to update metadata for conversation {conversation_id}: {e}")
                return False

    def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation."""
        with self._lock:
            try:
                if conversation_id not in self._conversations:
                    logger.error(f"Conversation {conversation_id} not found")
                    return False

                conversation = self._conversations[conversation_id]
                conversation['archived_at'] = datetime.now().isoformat()

                # Move file to archived directory
                source_path = self.active_dir / f"{conversation_id}.json"
                dest_path = self.archived_dir / f"{conversation_id}.json"

                if source_path.exists():
                    source_path.rename(dest_path)

                del self._conversations[conversation_id]

                logger.info(f"Archived conversation {conversation_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to archive conversation {conversation_id}: {e}")
                return False

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation permanently."""
        with self._lock:
            try:
                # Check both active and archived
                active_path = self.active_dir / f"{conversation_id}.json"
                archived_path = self.archived_dir / f"{conversation_id}.json"

                deleted = False
                if active_path.exists():
                    active_path.unlink()
                    deleted = True
                if archived_path.exists():
                    archived_path.unlink()
                    deleted = True

                if conversation_id in self._conversations:
                    del self._conversations[conversation_id]

                if deleted:
                    logger.info(f"Deleted conversation {conversation_id}")
                return deleted
            except Exception as e:
                logger.error(f"Failed to delete conversation {conversation_id}: {e}")
                return False

    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Search conversations by title or message content."""
        with self._lock:
            results = []
            query_lower = query.lower()

            for conversation in self._conversations.values():
                # Search in title
                if query_lower in conversation.get('title', '').lower():
                    results.append(conversation)
                    continue

                # Search in messages
                for message in conversation.get('messages', []):
                    if query_lower in message.get('content', '').lower():
                        results.append(conversation)
                        break

            return results

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about conversations."""
        with self._lock:
            total_conversations = len(self._conversations)
            total_messages = sum(
                len(conv.get('messages', []))
                for conv in self._conversations.values()
            )

            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'active_conversations': len(list(self.active_dir.glob("*.json"))),
                'archived_conversations': len(list(self.archived_dir.glob("*.json")))
            }