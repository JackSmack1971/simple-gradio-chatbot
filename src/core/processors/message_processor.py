# src/core/processors/message_processor.py
import re
import time
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime

from ...utils.logging import logger
from ...utils.validators import validate_message_content
from ...external.openrouter.client import OpenRouterClient


class MessageProcessor:
    """Handles message validation, formatting, and processing for AI interactions."""

    # Token estimation constants (rough approximation)
    CHARS_PER_TOKEN = 4.0  # Average characters per token
    BASE_OVERHEAD = 10     # Base tokens for system overhead

    def __init__(self, openrouter_client: Optional[OpenRouterClient] = None):
        """
        Initialize the MessageProcessor.

        Args:
            openrouter_client: OpenRouter client instance. If None, creates a new one.
        """
        self.openrouter_client = openrouter_client or OpenRouterClient()
        logger.info("MessageProcessor initialized")

    def validate_message(self, content: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate message content and extract metadata.

        Args:
            content: The message content to validate

        Returns:
            Tuple of (is_valid, error_message, metadata)
        """
        try:
            # Basic validation using existing validator
            is_valid, error = validate_message_content(content)
            if not is_valid:
                logger.warning(f"Message validation failed: {error}")
                return False, error, {}

            # Extract metadata
            metadata = self._extract_metadata(content)

            logger.debug("Message validation successful")
            return True, "", metadata

        except Exception as e:
            error_msg = f"Message validation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from message content.

        Args:
            content: Message content

        Returns:
            Dictionary containing metadata
        """
        metadata = {
            'length': len(content),
            'word_count': len(content.split()),
            'timestamp': datetime.now().isoformat(),
            'processed_at': time.time()
        }

        # Check for code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        metadata['code_blocks'] = len(code_blocks)

        # Check for URLs
        urls = re.findall(r'https?://[^\s]+', content)
        metadata['urls'] = len(urls)

        # Check for mentions (@username)
        mentions = re.findall(r'@\w+', content)
        metadata['mentions'] = len(mentions)

        return metadata

    def estimate_tokens(self, content: str, model: str = "default") -> int:
        """
        Estimate token count for message content.

        Args:
            content: Message content
            model: Model identifier for model-specific estimation

        Returns:
            Estimated token count
        """
        try:
            # Basic estimation based on character count
            base_tokens = len(content) / self.CHARS_PER_TOKEN

            # Add overhead for different message types
            overhead = self.BASE_OVERHEAD

            # Add tokens for code blocks (they use more tokens)
            code_blocks = re.findall(r'```[\s\S]*?```', content)
            for block in code_blocks:
                # Code blocks typically use more tokens
                overhead += len(block) / 2.0

            # Add tokens for URLs (they're treated specially)
            urls = re.findall(r'https?://[^\s]+', content)
            overhead += len(urls) * 2

            total_tokens = int(base_tokens + overhead)

            logger.debug(f"Estimated {total_tokens} tokens for content (length: {len(content)})")
            return total_tokens

        except Exception as e:
            logger.error(f"Token estimation error: {str(e)}")
            return 0

    def estimate_cost(self, token_count: int, model: str = "default") -> float:
        """
        Estimate cost for token usage.

        Args:
            token_count: Number of tokens
            model: Model identifier

        Returns:
            Estimated cost in USD
        """
        try:
            # Basic cost estimation (these are example rates)
            # In a real implementation, you'd get actual rates from the API
            cost_per_token = 0.0001  # Example rate

            # Model-specific adjustments
            if "claude" in model.lower():
                cost_per_token = 0.00015
            elif "gpt-4" in model.lower():
                cost_per_token = 0.0002
            elif "gpt-3.5" in model.lower():
                cost_per_token = 0.00005

            cost = token_count * cost_per_token

            logger.debug(".6f")
            return cost

        except Exception as e:
            logger.error(f"Cost estimation error: {str(e)}")
            return 0.0

    def format_for_api(self, content: str, role: str = "user") -> Dict[str, Any]:
        """
        Format message content for API request.

        Args:
            content: Message content
            role: Message role (user, assistant, system)

        Returns:
            Formatted message dictionary
        """
        try:
            # Sanitize content
            sanitized_content = self._sanitize_content(content)

            message = {
                "role": role,
                "content": sanitized_content,
                "metadata": {
                    "original_length": len(content),
                    "sanitized_length": len(sanitized_content),
                    "formatted_at": datetime.now().isoformat()
                }
            }

            logger.debug(f"Formatted message for API: role={role}, length={len(sanitized_content)}")
            return message

        except Exception as e:
            logger.error(f"Message formatting error: {str(e)}")
            return {
                "role": role,
                "content": content,  # Return original if sanitization fails
                "metadata": {"error": str(e)}
            }

    def _sanitize_content(self, content: str) -> str:
        """
        Sanitize message content for security.

        Args:
            content: Raw content

        Returns:
            Sanitized content
        """
        # Remove or escape potentially dangerous patterns
        sanitized = content

        # Remove script tags (already checked in validation, but extra safety)
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '[SCRIPT REMOVED]', sanitized, flags=re.IGNORECASE)

        # Escape HTML entities that might be problematic
        sanitized = sanitized.replace('<', '<').replace('>', '>')

        # Trim excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        return sanitized

    def process_conversation_messages(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process a list of conversation messages.

        Args:
            messages: List of message dictionaries

        Returns:
            Tuple of (processed_messages, summary_stats)
        """
        try:
            processed_messages = []
            total_tokens = 0
            total_cost = 0.0

            for msg in messages:
                content = msg.get('content', '')
                role = msg.get('role', 'user')

                # Validate individual message
                is_valid, error, metadata = self.validate_message(content)
                if not is_valid:
                    logger.warning(f"Skipping invalid message: {error}")
                    continue

                # Format for API
                formatted_msg = self.format_for_api(content, role)

                # Estimate tokens and cost
                token_count = self.estimate_tokens(content)
                cost = self.estimate_cost(token_count)

                # Add processing metadata
                formatted_msg['metadata'].update({
                    'tokens': token_count,
                    'estimated_cost': cost,
                    'validation_metadata': metadata
                })

                processed_messages.append(formatted_msg)
                total_tokens += token_count
                total_cost += cost

            summary = {
                'total_messages': len(processed_messages),
                'total_tokens': total_tokens,
                'estimated_total_cost': total_cost,
                'processed_at': datetime.now().isoformat()
            }

            logger.info(f"Processed {len(processed_messages)} messages, {total_tokens} tokens total")
            return processed_messages, summary

        except Exception as e:
            logger.error(f"Conversation processing error: {str(e)}")
            return [], {'error': str(e)}

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        # In a real implementation, you'd track actual processing metrics
        return {
            'messages_processed': 0,  # Would be incremented in actual usage
            'total_tokens_processed': 0,
            'average_processing_time': 0.0,
            'error_count': 0
        }