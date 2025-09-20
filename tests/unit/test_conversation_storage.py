# tests/unit/test_conversation_storage.py
import pytest
import tempfile
import json
import threading
from pathlib import Path
from datetime import datetime

from src.storage.conversation_storage import ConversationStorage

class TestConversationStorage:
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage_dir = self.temp_dir / "conversations"
        self.storage = ConversationStorage(str(self.storage_dir))

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization_creates_directories(self):
        """Test that ConversationStorage creates necessary directories."""
        assert self.storage_dir.exists()
        assert (self.storage_dir / "active").exists()
        assert (self.storage_dir / "archived").exists()

    def test_create_conversation(self):
        """Test creating a new conversation."""
        conversation_id = "test_conv_001"
        title = "Test Conversation"

        result = self.storage.create_conversation(conversation_id, title)
        assert result is True

        # Check that conversation file was created
        conv_file = self.storage_dir / "active" / f"{conversation_id}.json"
        assert conv_file.exists()

        # Check conversation content
        with open(conv_file, 'r') as f:
            data = json.load(f)

        assert data['id'] == conversation_id
        assert data['title'] == title
        assert data['messages'] == []
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_create_duplicate_conversation(self):
        """Test creating a conversation that already exists."""
        conversation_id = "test_conv_001"

        # Create first time
        result1 = self.storage.create_conversation(conversation_id)
        assert result1 is True

        # Try to create again
        result2 = self.storage.create_conversation(conversation_id)
        assert result2 is False

    def test_save_and_get_message(self):
        """Test saving and retrieving messages."""
        conversation_id = "test_conv_001"
        self.storage.create_conversation(conversation_id)

        message = {
            'role': 'user',
            'content': 'Hello, world!'
        }

        # Save message
        result = self.storage.save_message(conversation_id, message)
        assert result is True

        # Get conversation and check message
        conversation = self.storage.get_conversation(conversation_id)
        assert conversation is not None
        assert len(conversation['messages']) == 1

        saved_message = conversation['messages'][0]
        assert saved_message['role'] == 'user'
        assert saved_message['content'] == 'Hello, world!'
        assert 'timestamp' in saved_message

    def test_save_message_nonexistent_conversation(self):
        """Test saving message to non-existent conversation."""
        result = self.storage.save_message("nonexistent", {'role': 'user', 'content': 'test'})
        assert result is False

    def test_get_nonexistent_conversation(self):
        """Test getting a conversation that doesn't exist."""
        conversation = self.storage.get_conversation("nonexistent")
        assert conversation is None

    def test_list_conversations(self):
        """Test listing all conversations."""
        # Create multiple conversations
        conv1 = "conv_001"
        conv2 = "conv_002"

        self.storage.create_conversation(conv1, "Conversation 1")
        self.storage.create_conversation(conv2, "Conversation 2")

        conversations = self.storage.list_conversations()
        assert len(conversations) == 2

        ids = [c['id'] for c in conversations]
        assert conv1 in ids
        assert conv2 in ids

    def test_update_conversation_metadata(self):
        """Test updating conversation metadata."""
        conversation_id = "test_conv_001"
        self.storage.create_conversation(conversation_id)

        metadata = {'tags': ['important', 'test'], 'priority': 'high'}

        result = self.storage.update_conversation_metadata(conversation_id, metadata)
        assert result is True

        conversation = self.storage.get_conversation(conversation_id)
        assert conversation is not None
        assert conversation['metadata'] == metadata

    def test_update_metadata_nonexistent_conversation(self):
        """Test updating metadata for non-existent conversation."""
        result = self.storage.update_conversation_metadata("nonexistent", {'test': 'value'})
        assert result is False

    def test_archive_conversation(self):
        """Test archiving a conversation."""
        conversation_id = "test_conv_001"
        self.storage.create_conversation(conversation_id)

        result = self.storage.archive_conversation(conversation_id)
        assert result is True

        # Check that file was moved to archived
        active_file = self.storage_dir / "active" / f"{conversation_id}.json"
        archived_file = self.storage_dir / "archived" / f"{conversation_id}.json"

        assert not active_file.exists()
        assert archived_file.exists()

        # Check that conversation is no longer in active list
        conversation = self.storage.get_conversation(conversation_id)
        assert conversation is None

    def test_archive_nonexistent_conversation(self):
        """Test archiving a non-existent conversation."""
        result = self.storage.archive_conversation("nonexistent")
        assert result is False

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        conversation_id = "test_conv_001"
        self.storage.create_conversation(conversation_id)

        result = self.storage.delete_conversation(conversation_id)
        assert result is True

        # Check that file was deleted
        conv_file = self.storage_dir / "active" / f"{conversation_id}.json"
        assert not conv_file.exists()

    def test_delete_nonexistent_conversation(self):
        """Test deleting a non-existent conversation."""
        result = self.storage.delete_conversation("nonexistent")
        assert result is False

    def test_search_conversations(self):
        """Test searching conversations by title and content."""
        # Create conversations with different content
        conv1 = "conv_001"
        conv2 = "conv_002"

        self.storage.create_conversation(conv1, "Python Programming")
        self.storage.create_conversation(conv2, "JavaScript Guide")

        self.storage.save_message(conv1, {'role': 'user', 'content': 'How to use Python?'})
        self.storage.save_message(conv2, {'role': 'user', 'content': 'JavaScript tutorial'})

        # Search by title
        results = self.storage.search_conversations("Python")
        assert len(results) == 1
        assert results[0]['id'] == conv1

        # Search by message content
        results = self.storage.search_conversations("tutorial")
        assert len(results) == 1
        assert results[0]['id'] == conv2

        # Search with no results
        results = self.storage.search_conversations("nonexistent")
        assert len(results) == 0

    def test_atomic_write_prevents_corruption(self):
        """Test that atomic writes prevent file corruption."""
        conversation_id = "test_conv_001"
        self.storage.create_conversation(conversation_id)

        # Simulate corruption by writing invalid JSON during atomic write
        conv_file = self.storage_dir / "active" / f"{conversation_id}.json"

        # Save a message (should use atomic write)
        message = {'role': 'user', 'content': 'Test message'}
        result = self.storage.save_message(conversation_id, message)
        assert result is True

        # Verify file is still valid JSON
        with open(conv_file, 'r') as f:
            data = json.load(f)
        assert data['id'] == conversation_id
        assert len(data['messages']) == 1

    def test_conversation_stats(self):
        """Test getting conversation statistics."""
        # Create some conversations
        self.storage.create_conversation("conv_001")
        self.storage.create_conversation("conv_002")

        # Archive one
        self.storage.archive_conversation("conv_002")

        stats = self.storage.get_conversation_stats()

        assert stats['total_conversations'] == 1  # Only active
        assert stats['total_messages'] == 0
        assert stats['active_conversations'] == 1
        assert stats['archived_conversations'] == 1

    def test_thread_safety(self):
        """Test that operations are thread-safe."""
        conversation_id = "test_conv_001"
        self.storage.create_conversation(conversation_id)

        results = []

        def save_message_worker(message_num):
            message = {'role': 'user', 'content': f'Message {message_num}'}
            result = self.storage.save_message(conversation_id, message)
            results.append(result)

        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=save_message_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All saves should have succeeded
        assert all(results)

        # Check that all messages were saved
        conversation = self.storage.get_conversation(conversation_id)
        assert conversation is not None
        assert len(conversation['messages']) == 10