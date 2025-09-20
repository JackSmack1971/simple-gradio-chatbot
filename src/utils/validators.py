# src/utils/validators.py
import re
from typing import Tuple, Optional
from urllib.parse import urlparse

from .logging import logger

def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate OpenRouter API key format.

    Args:
        api_key: The API key to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"

    if not api_key.strip():
        return False, "API key cannot be only whitespace"

    # OpenRouter keys start with 'sk-or-v1-'
    if not api_key.startswith('sk-or-v1-'):
        return False, "API key must start with 'sk-or-v1-'"

    if len(api_key) < 50:  # Minimum reasonable length
        return False, "API key appears too short"

    if len(api_key) > 200:  # Maximum reasonable length
        return False, "API key appears too long"

    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
        return False, "API key contains invalid characters"

    return True, ""

def validate_message_content(content: str) -> Tuple[bool, str]:
    """
    Validate message content for chat.

    Args:
        content: The message content to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not isinstance(content, str):
        return False, "Message content must be a non-empty string"

    content = content.strip()
    if not content:
        return False, "Message content cannot be only whitespace"

    # Check length limits
    MAX_LENGTH = 4000  # OpenRouter limit
    if len(content) > MAX_LENGTH:
        return False, f"Message content exceeds maximum length of {MAX_LENGTH} characters"

    # Check for potentially harmful content (basic check)
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'data:',                      # Data URLs that might be malicious
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            logger.warning(f"Potentially dangerous content detected in message: {pattern}")
            return False, "Message contains potentially harmful content"

    return True, ""

def validate_model_id(model_id: str) -> Tuple[bool, str]:
    """
    Validate AI model identifier.

    Args:
        model_id: The model identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not model_id or not isinstance(model_id, str):
        return False, "Model ID must be a non-empty string"

    model_id = model_id.strip()
    if not model_id:
        return False, "Model ID cannot be only whitespace"

    # Basic format validation (provider/model-name)
    if '/' not in model_id:
        return False, "Model ID must be in format 'provider/model-name'"

    provider, model_name = model_id.split('/', 1)

    if not provider or not model_name:
        return False, "Both provider and model name must be non-empty"

    # Check for valid characters
    if not re.match(r'^[a-zA-Z0-9\-_\.]+$', provider):
        return False, "Provider name contains invalid characters"

    if not re.match(r'^[a-zA-Z0-9\-_\.]+$', model_name):
        return False, "Model name contains invalid characters"

    return True, ""

def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format and security.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    try:
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            return False, "URL must have valid scheme and network location"

        # Only allow http and https
        if parsed.scheme not in ['http', 'https']:
            return False, "URL must use HTTP or HTTPS protocol"

        # Basic domain validation
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', parsed.netloc.replace('.', '')):
            return False, "Domain contains invalid characters"

        return True, ""

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and invalid characters.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed_file"

    # Remove directory separators
    filename = re.sub(r'[\/\\]', '_', filename)

    # Remove other dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    # Ensure not empty after sanitization
    if not filename.strip():
        filename = "unnamed_file"

    return filename