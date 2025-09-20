# src/core/managers/conversation_manager.py
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from ...utils.logging import logger
from ...storage.conversation_storage import ConversationStorage
from ..processors.message_processor import MessageProcessor


class ConversationManager:
    """Manages conversation lifecycle and persistence."""

    def __init__(self, storage: Optional[ConversationStorage] = None,
                 message_processor: Optional[MessageProcessor] = None):
        """
        Initialize the ConversationManager.

        Args:
            storage: Conversation storage instance. If None, creates a new one.
            message_processor: Message processor instance. If None, creates a new one.
        """
        self.storage = storage or ConversationStorage()
        self.message_processor = message_processor or MessageProcessor()
        logger.info("ConversationManager initialized")

    def create_conversation(self, title: str = "New Conversation",
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new conversation.

        Args:
            title: Conversation title
            metadata: Additional metadata

        Returns:
            Conversation ID
        """
        try:
            conversation_id = str(uuid.uuid4())

            # Initialize metadata
            if metadata is None:
                metadata = {}

            metadata.update({
                'created_by': 'system',
                'version': '1.0',
                'tags': []
            })

            success = self.storage.create_conversation(conversation_id, title)
            if not success:
                raise Exception("Failed to create conversation in storage")

            # Update metadata
            self.storage.update_conversation_metadata(conversation_id, metadata)

            logger.info(f"Created conversation {conversation_id}: {title}")
            return conversation_id

        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            raise

    def add_message(self, conversation_id: str, content: str, role: str = "user",
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user, assistant, system)
            metadata: Additional message metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate conversation exists
            conversation = self.storage.get_conversation(conversation_id)
            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return False

            # Validate and process message
            is_valid, error, msg_metadata = self.message_processor.validate_message(content)
            if not is_valid:
                logger.error(f"Invalid message for conversation {conversation_id}: {error}")
                return False

            # Prepare message data
            message_data = {
                'role': role,
                'content': content,
                'metadata': msg_metadata
            }

            if metadata:
                message_data['metadata'].update(metadata)

            # Save message
            success = self.storage.save_message(conversation_id, message_data)
            if success:
                logger.debug(f"Added message to conversation {conversation_id}")
                # Update conversation metadata with stats
                self._update_conversation_stats(conversation_id)
            else:
                logger.error(f"Failed to save message to conversation {conversation_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {str(e)}")
            return False

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation data or None if not found
        """
        try:
            conversation = self.storage.get_conversation(conversation_id)
            if conversation:
                # Add computed metadata
                conversation['computed_metadata'] = self._compute_conversation_metadata(conversation)
            return conversation
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
            return None

    def list_conversations(self, limit: int = 50, offset: int = 0,
                          sort_by: str = "updated_at", sort_order: str = "desc") -> List[Dict[str, Any]]:
        """
        List conversations with pagination and sorting.

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            List of conversations
        """
        try:
            conversations = self.storage.list_conversations()

            # Sort conversations
            reverse = sort_order.lower() == "desc"
            conversations.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)

            # Apply pagination
            start = offset
            end = offset + limit
            paginated = conversations[start:end]

            # Add computed metadata
            for conv in paginated:
                conv['computed_metadata'] = self._compute_conversation_metadata(conv)

            logger.debug(f"Listed {len(paginated)} conversations (offset: {offset}, limit: {limit})")
            return paginated

        except Exception as e:
            logger.error(f"Failed to list conversations: {str(e)}")
            return []

    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search conversations by title or content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching conversations
        """
        try:
            results = self.storage.search_conversations(query)

            # Limit results
            limited_results = results[:limit]

            # Add computed metadata
            for conv in limited_results:
                conv['computed_metadata'] = self._compute_conversation_metadata(conv)

            logger.info(f"Found {len(limited_results)} conversations matching '{query}'")
            return limited_results

        except Exception as e:
            logger.error(f"Failed to search conversations: {str(e)}")
            return []

    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """
        Update conversation title.

        Args:
            conversation_id: Conversation ID
            title: New title

        Returns:
            True if successful, False otherwise
        """
        try:
            metadata = {'title': title}
            success = self.storage.update_conversation_metadata(conversation_id, metadata)

            if success:
                logger.info(f"Updated title for conversation {conversation_id}: {title}")
            else:
                logger.error(f"Failed to update title for conversation {conversation_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to update conversation title: {str(e)}")
            return False

    def add_conversation_tag(self, conversation_id: str, tag: str) -> bool:
        """
        Add a tag to a conversation.

        Args:
            conversation_id: Conversation ID
            tag: Tag to add

        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = self.storage.get_conversation(conversation_id)
            if not conversation:
                return False

            current_tags = conversation.get('metadata', {}).get('tags', [])
            if tag not in current_tags:
                current_tags.append(tag)
                metadata = {'tags': current_tags}
                success = self.storage.update_conversation_metadata(conversation_id, metadata)

                if success:
                    logger.debug(f"Added tag '{tag}' to conversation {conversation_id}")
                return success

            return True  # Tag already exists

        except Exception as e:
            logger.error(f"Failed to add tag to conversation {conversation_id}: {str(e)}")
            return False

    def archive_conversation(self, conversation_id: str) -> bool:
        """
        Archive a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.storage.archive_conversation(conversation_id)

            if success:
                logger.info(f"Archived conversation {conversation_id}")
            else:
                logger.error(f"Failed to archive conversation {conversation_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to archive conversation: {str(e)}")
            return False

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation permanently.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.storage.delete_conversation(conversation_id)

            if success:
                logger.info(f"Deleted conversation {conversation_id}")
            else:
                logger.error(f"Failed to delete conversation {conversation_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete conversation: {str(e)}")
            return False

    def get_conversation_messages(self, conversation_id: str, limit: int = 100,
                                offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation with pagination.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of messages
        """
        try:
            conversation = self.storage.get_conversation(conversation_id)
            if not conversation:
                return []

            messages = conversation.get('messages', [])

            # Apply pagination
            start = offset
            end = offset + limit
            paginated_messages = messages[start:end]

            logger.debug(f"Retrieved {len(paginated_messages)} messages from conversation {conversation_id}")
            return paginated_messages

        except Exception as e:
            logger.error(f"Failed to get messages from conversation {conversation_id}: {str(e)}")
            return []

    def _update_conversation_stats(self, conversation_id: str) -> None:
        """Update conversation statistics in metadata."""
        try:
            conversation = self.storage.get_conversation(conversation_id)
            if not conversation:
                return

            messages = conversation.get('messages', [])
            stats = {
                'message_count': len(messages),
                'last_message_at': datetime.now().isoformat(),
                'total_tokens': sum(msg.get('metadata', {}).get('tokens', 0) for msg in messages)
            }

            self.storage.update_conversation_metadata(conversation_id, {'stats': stats})

        except Exception as e:
            logger.error(f"Failed to update conversation stats: {str(e)}")

    def _compute_conversation_metadata(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Compute additional metadata for a conversation."""
        try:
            messages = conversation.get('messages', [])
            created_at = conversation.get('created_at')
            updated_at = conversation.get('updated_at')

            computed: Dict[str, Any] = {
                'age_days': 0,
                'messages_per_day': 0.0,
                'total_tokens': 0,
                'avg_message_length': 0.0
            }

            if created_at:
                created_dt = datetime.fromisoformat(created_at)
                age = datetime.now() - created_dt
                computed['age_days'] = age.days

                if age.days > 0 and messages:
                    computed['messages_per_day'] = len(messages) / age.days

            if messages:
                total_length = sum(len(msg.get('content', '')) for msg in messages)
                computed['avg_message_length'] = total_length / len(messages)
                computed['total_tokens'] = sum(msg.get('metadata', {}).get('tokens', 0) for msg in messages)

            return computed

        except Exception as e:
            logger.error(f"Failed to compute conversation metadata: {str(e)}")
            return {}

    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Get overall conversation statistics.

        Returns:
            Dictionary with conversation statistics
        """
        try:
            storage_stats = self.storage.get_conversation_stats()

            # Add additional computed stats
            conversations = self.storage.list_conversations()
            total_messages = sum(len(conv.get('messages', [])) for conv in conversations)

            stats = {
                **storage_stats,
                'total_messages': total_messages,
                'avg_messages_per_conversation': total_messages / max(1, len(conversations)),
                'active_conversations_7d': self._count_recent_conversations(7),
                'active_conversations_30d': self._count_recent_conversations(30)
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get conversation stats: {str(e)}")
            return {}

    def _count_recent_conversations(self, days: int) -> int:
        """Count conversations active within the last N days."""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            conversations = self.storage.list_conversations()

            count = 0
            for conv in conversations:
                updated_at = conv.get('updated_at')
                if updated_at:
                    updated_dt = datetime.fromisoformat(updated_at)
                    if updated_dt > cutoff:
                        count += 1

            return count

        except Exception as e:
            logger.error(f"Failed to count recent conversations: {str(e)}")
            return 0