# tests/unit/test_conversation_manager.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

from src.core.managers.conversation_manager import ConversationManager
from src.storage.conversation_storage import ConversationStorage
from src.core.processors.message_processor import MessageProcessor


class TestConversationManager:
    @pytest.fixture
    def mock_storage(self):
        """Mock ConversationStorage for testing."""
        return Mock(spec=ConversationStorage)

    @pytest.fixture
    def mock_message_processor(self):
        """Mock MessageProcessor for testing."""
        return Mock(spec=MessageProcessor)

    @pytest.fixture
    def manager(self, mock_storage, mock_message_processor):
        """Create ConversationManager with mocked dependencies."""
        return ConversationManager(mock_storage, mock_message_processor)

    def test_initialization(self, mock_storage, mock_message_processor):
        """Test manager initialization."""
        manager = ConversationManager(mock_storage, mock_message_processor)
        assert manager.storage == mock_storage
        assert manager.message_processor == mock_message_processor

    def test_initialization_default_dependencies(self):
        """Test manager initialization with default dependencies."""
        with patch('src.core.managers.conversation_manager.ConversationStorage') as mock_storage_class, \
             patch('src.core.managers.conversation_manager.MessageProcessor') as mock_processor_class:

            mock_storage = Mock()
            mock_processor = Mock()
            mock_storage_class.return_value = mock_storage
            mock_processor_class.return_value = mock_processor

            manager = ConversationManager()

            assert manager.storage == mock_storage
            assert manager.message_processor == mock_processor
            mock_storage_class.assert_called_once()
            mock_processor_class.assert_called_once()

    def test_create_conversation_success(self, manager, mock_storage):
        """Test successful conversation creation."""
        mock_storage.create_conversation.return_value = True
        mock_storage.update_conversation_metadata.return_value = True

        conversation_id = manager.create_conversation("Test Conversation")

        assert isinstance(conversation_id, str)
        mock_storage.create_conversation.assert_called_once()
        mock_storage.update_conversation_metadata.assert_called_once()

    def test_create_conversation_failure(self, manager, mock_storage):
        """Test conversation creation failure."""
        mock_storage.create_conversation.return_value = False

        with pytest.raises(Exception):
            manager.create_conversation("Test Conversation")

    def test_add_message_success(self, manager, mock_storage, mock_message_processor):
        """Test successful message addition."""
        conversation_id = "test-conv-123"
        message = "Hello world!"
        role = "user"

        # Mock conversation exists
        mock_storage.get_conversation.return_value = {"id": conversation_id, "messages": []}
        mock_storage.save_message.return_value = True

        # Mock message validation
        mock_message_processor.validate_message.return_value = (True, "", {"tokens": 10})

        success = manager.add_message(conversation_id, message, role)

        assert success is True
        mock_storage.save_message.assert_called_once()
        mock_message_processor.validate_message.assert_called_once_with(message)

    def test_add_message_with_swapped_arguments(self, manager, mock_storage, mock_message_processor):
        """Test message addition when content/role arguments are swapped."""
        conversation_id = "test-conv-123"
        swapped_content = "user"
        swapped_role = "Hello from the user"
        extra_metadata = {"source": "cli"}

        mock_storage.get_conversation.return_value = {"id": conversation_id, "messages": []}
        mock_storage.save_message.return_value = True
        mock_message_processor.validate_message.return_value = (True, "", {"tokens": 5})

        success = manager.add_message(
            conversation_id,
            swapped_content,
            swapped_role,
            metadata=extra_metadata
        )

        assert success is True
        mock_message_processor.validate_message.assert_called_once_with(swapped_role)
        mock_storage.save_message.assert_called_once()

        saved_message = mock_storage.save_message.call_args[0][1]
        assert saved_message["role"] == "user"
        assert saved_message["content"] == swapped_role
        # Ensure metadata from validation and caller metadata are preserved after swap
        assert saved_message["metadata"]["tokens"] == 5
        assert saved_message["metadata"]["source"] == "cli"

    def test_add_message_conversation_not_found(self, manager, mock_storage):
        """Test message addition with non-existent conversation."""
        mock_storage.get_conversation.return_value = None

        success = manager.add_message("non-existent", "Hello")

        assert success is False
        mock_storage.save_message.assert_not_called()

    def test_add_message_validation_failure(self, manager, mock_storage, mock_message_processor):
        """Test message addition with validation failure."""
        conversation_id = "test-conv-123"
        invalid_message = ""

        mock_storage.get_conversation.return_value = {"id": conversation_id}
        mock_message_processor.validate_message.return_value = (False, "Empty message", {})

        success = manager.add_message(conversation_id, invalid_message)

        assert success is False
        mock_storage.save_message.assert_not_called()

    def test_get_conversation(self, manager, mock_storage):
        """Test conversation retrieval."""
        conversation_id = "test-conv-123"
        conversation_data = {
            "id": conversation_id,
            "title": "Test",
            "messages": [],
            "created_at": datetime.now().isoformat()
        }

        mock_storage.get_conversation.return_value = conversation_data

        result = manager.get_conversation(conversation_id)

        assert result == conversation_data
        assert 'computed_metadata' in result
        mock_storage.get_conversation.assert_called_once_with(conversation_id)

    def test_get_conversation_not_found(self, manager, mock_storage):
        """Test conversation retrieval for non-existent conversation."""
        mock_storage.get_conversation.return_value = None

        result = manager.get_conversation("non-existent")

        assert result is None

    def test_list_conversations(self, manager, mock_storage):
        """Test conversation listing."""
        conversations = [
            {"id": "conv1", "title": "Test 1", "messages": []},
            {"id": "conv2", "title": "Test 2", "messages": []}
        ]

        mock_storage.list_conversations.return_value = conversations

        result = manager.list_conversations(limit=10, offset=0)

        assert len(result) == 2
        for conv in result:
            assert 'computed_metadata' in conv
        mock_storage.list_conversations.assert_called_once()

    def test_list_conversations_with_sorting(self, manager, mock_storage):
        """Test conversation listing with sorting."""
        conversations = [
            {"id": "conv1", "title": "B Test", "updated_at": "2023-01-02T00:00:00"},
            {"id": "conv2", "title": "A Test", "updated_at": "2023-01-01T00:00:00"}
        ]

        mock_storage.list_conversations.return_value = conversations

        result = manager.list_conversations(sort_by="title", sort_order="asc")

        assert result[0]["title"] == "A Test"
        assert result[1]["title"] == "B Test"

    def test_search_conversations(self, manager, mock_storage):
        """Test conversation search."""
        conversations = [
            {"id": "conv1", "title": "Hello World", "messages": []},
            {"id": "conv2", "title": "Test Chat", "messages": []}
        ]

        mock_storage.search_conversations.return_value = conversations

        result = manager.search_conversations("Hello")

        assert len(result) == 2
        for conv in result:
            assert 'computed_metadata' in conv
        mock_storage.search_conversations.assert_called_once_with("Hello")

    def test_update_conversation_title(self, manager, mock_storage):
        """Test conversation title update."""
        conversation_id = "test-conv-123"

        mock_storage.update_conversation_metadata.return_value = True

        success = manager.update_conversation_title(conversation_id, "New Title")

        assert success is True
        mock_storage.update_conversation_metadata.assert_called_once_with(
            conversation_id, {"title": "New Title"}
        )

    def test_add_conversation_tag(self, manager, mock_storage):
        """Test adding conversation tag."""
        conversation_id = "test-conv-123"
        conversation_data = {
            "id": conversation_id,
            "metadata": {"tags": ["existing"]}
        }

        mock_storage.get_conversation.return_value = conversation_data
        mock_storage.update_conversation_metadata.return_value = True

        success = manager.add_conversation_tag(conversation_id, "new-tag")

        assert success is True
        mock_storage.update_conversation_metadata.assert_called_once_with(
            conversation_id, {"tags": ["existing", "new-tag"]}
        )

    def test_add_conversation_tag_duplicate(self, manager, mock_storage):
        """Test adding duplicate conversation tag."""
        conversation_id = "test-conv-123"
        conversation_data = {
            "id": conversation_id,
            "metadata": {"tags": ["existing"]}
        }

        mock_storage.get_conversation.return_value = conversation_data

        success = manager.add_conversation_tag(conversation_id, "existing")

        assert success is True
        mock_storage.update_conversation_metadata.assert_not_called()

    def test_archive_conversation(self, manager, mock_storage):
        """Test conversation archiving."""
        conversation_id = "test-conv-123"

        mock_storage.archive_conversation.return_value = True

        success = manager.archive_conversation(conversation_id)

        assert success is True
        mock_storage.archive_conversation.assert_called_once_with(conversation_id)

    def test_delete_conversation(self, manager, mock_storage):
        """Test conversation deletion."""
        conversation_id = "test-conv-123"

        mock_storage.delete_conversation.return_value = True

        success = manager.delete_conversation(conversation_id)

        assert success is True
        mock_storage.delete_conversation.assert_called_once_with(conversation_id)

    def test_get_conversation_messages(self, manager, mock_storage):
        """Test getting conversation messages."""
        conversation_id = "test-conv-123"
        messages = [
            {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi!", "timestamp": "2023-01-01T00:00:01"}
        ]

        mock_storage.get_conversation.return_value = {"messages": messages}

        result = manager.get_conversation_messages(conversation_id, limit=10, offset=0)

        assert result == messages
        mock_storage.get_conversation.assert_called_once_with(conversation_id)

    def test_get_conversation_messages_pagination(self, manager, mock_storage):
        """Test conversation messages pagination."""
        conversation_id = "test-conv-123"
        messages = [{"content": f"Message {i}"} for i in range(10)]

        mock_storage.get_conversation.return_value = {"messages": messages}

        result = manager.get_conversation_messages(conversation_id, limit=5, offset=2)

        assert len(result) == 5
        assert result[0]["content"] == "Message 2"
        assert result[4]["content"] == "Message 6"

    def test_get_conversation_stats(self, manager, mock_storage):
        """Test getting conversation statistics."""
        conversations = [
            {"messages": [{"content": "msg1"}, {"content": "msg2"}]},
            {"messages": [{"content": "msg3"}]}
        ]

        mock_storage.list_conversations.return_value = conversations
        mock_storage.get_conversation_stats.return_value = {
            "total_conversations": 2,
            "active_conversations": 2,
            "archived_conversations": 0
        }

        stats = manager.get_conversation_stats()

        assert stats["total_messages"] == 3
        assert stats["avg_messages_per_conversation"] == 1.5
        assert "active_conversations_7d" in stats
        assert "active_conversations_30d" in stats

    def test_compute_conversation_metadata(self, manager):
        """Test conversation metadata computation."""
        created_at = (datetime.now() - timedelta(days=5)).isoformat()
        conversation = {
            "messages": [{"content": "Hello"}, {"content": "World"}],
            "created_at": created_at,
            "updated_at": datetime.now().isoformat()
        }

        metadata = manager._compute_conversation_metadata(conversation)

        assert metadata["age_days"] == 5
        assert metadata["messages_per_day"] == 0.4  # 2 messages / 5 days
        assert metadata["total_tokens"] == 0  # No tokens in test messages
        assert metadata["avg_message_length"] == 5.0  # (5 + 5) / 2 = 5

    def test_compute_conversation_metadata_no_messages(self, manager):
        """Test metadata computation with no messages."""
        conversation = {"messages": []}

        metadata = manager._compute_conversation_metadata(conversation)

        assert metadata["age_days"] == 0
        assert metadata["messages_per_day"] == 0.0
        assert metadata["total_tokens"] == 0
        assert metadata["avg_message_length"] == 0.0

    def test_count_recent_conversations(self, manager, mock_storage):
        """Test counting recent conversations."""
        recent_date = datetime.now().isoformat()
        old_date = (datetime.now() - timedelta(days=10)).isoformat()

        conversations = [
            {"updated_at": recent_date},
            {"updated_at": old_date},
            {"updated_at": recent_date}
        ]

        mock_storage.list_conversations.return_value = conversations

        count = manager._count_recent_conversations(7)

        assert count == 2  # Two conversations updated recently