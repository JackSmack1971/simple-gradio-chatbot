"""Wrapper validators for external integrations.

This module provides a class-based interface that delegates to the shared
validator functions defined under :mod:`src.utils.validators`. Keeping a class
interface maintains backwards compatibility for components that expect a
``Validators`` object while reusing the centralised validation logic.
"""

from typing import Tuple

from ...utils import validators as shared_validators


class Validators:
    """Static helpers that proxy to shared validator functions."""

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """Validate an API key using the shared validation routine."""

        return shared_validators.validate_api_key(api_key)

    @staticmethod
    def validate_message_content(content: str) -> Tuple[bool, str]:
        """Validate chat message content for safety and length."""

        return shared_validators.validate_message_content(content)

    @staticmethod
    def validate_model_id(model_id: str) -> Tuple[bool, str]:
        """Validate an AI model identifier."""

        return shared_validators.validate_model_id(model_id)

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """Validate a URL for format and allowed protocol."""

        return shared_validators.validate_url(url)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitise a filename to remove unsafe characters."""

        return shared_validators.sanitize_filename(filename)

