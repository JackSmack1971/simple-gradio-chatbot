# src/external/openrouter/client.py
import json
import time
from typing import Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...utils.logging import logger
from ...utils.validators import validate_api_key, validate_model_id
from ...storage.config_manager import ConfigManager


class OpenRouterClient:
    """HTTP client for OpenRouter API with authentication and request handling."""

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the OpenRouter client.

        Args:
            config_manager: Configuration manager instance. If None, creates a new one.
        """
        self.config_manager = config_manager or ConfigManager()
        self._session: requests.Session = requests.Session()
        self._setup_session()

    def _setup_session(self) -> None:
        """Set up HTTP session with connection pooling and retry strategy."""
        self._session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        # Set default headers
        self._session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PersonalAI-Chatbot/1.0'
        })

    def _get_api_key(self) -> Optional[str]:
        """Get API key from configuration."""
        return self.config_manager.get_api_key()

    def _validate_api_key(self) -> bool:
        """Validate that API key is configured and valid."""
        api_key = self._get_api_key()
        if not api_key:
            logger.error("OpenRouter API key not configured")
            return False

        is_valid, error = validate_api_key(api_key)
        if not is_valid:
            logger.error(f"Invalid API key: {error}")
            return False

        return True

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None,
                     timeout: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Make HTTP request to OpenRouter API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request payload for POST requests
            timeout: Request timeout in seconds

        Returns:
            Tuple of (success, response_data)
        """
        if not self._validate_api_key():
            return False, {"error": "API key not configured or invalid"}

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {'Authorization': f'Bearer {self._get_api_key()}'}

        request_timeout = timeout or self.DEFAULT_TIMEOUT

        try:
            logger.debug(f"Making {method} request to {url}")

            if method.upper() == 'POST' and data:
                response = self._session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=request_timeout
                )
            elif method.upper() == 'GET':
                response = self._session.get(
                    url,
                    headers=headers,
                    timeout=request_timeout
                )
            else:
                return False, {"error": f"Unsupported HTTP method: {method}"}

            response.raise_for_status()

            # Parse JSON response
            try:
                response_data = response.json()
                logger.debug(f"Request successful: {response.status_code}")
                return True, response_data
            except json.JSONDecodeError:
                return False, {"error": "Invalid JSON response from API"}

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {request_timeout} seconds")
            return False, {"error": f"Request timeout after {request_timeout} seconds"}
        except requests.exceptions.ConnectionError:
            logger.error("Connection error - check network connectivity")
            return False, {"error": "Connection error - check network connectivity"}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            try:
                error_data = e.response.json()
                return False, error_data
            except:
                return False, {"error": f"HTTP {e.response.status_code}: {e.response.reason}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, {"error": f"Unexpected error: {str(e)}"}

    def chat_completion(self, model: str, messages: list, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Make a chat completion request.

        Args:
            model: Model identifier (e.g., 'anthropic/claude-3-haiku')
            messages: List of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Tuple of (success, response_data)
        """
        # Validate model ID
        is_valid, error = validate_model_id(model)
        if not is_valid:
            logger.error(f"Invalid model ID: {error}")
            return False, {"error": error}

        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }

        logger.info(f"Making chat completion request with model: {model}")
        return self._make_request('POST', 'chat/completions', payload)

    def list_models(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Get list of available models.

        Returns:
            Tuple of (success, response_data)
        """
        logger.info("Fetching available models")
        return self._make_request('GET', 'models')

    def validate_connection(self) -> bool:
        """
        Validate API connection and authentication.

        Returns:
            True if connection is valid, False otherwise
        """
        success, response = self.list_models()
        if success:
            logger.info("OpenRouter API connection validated successfully")
            return True
        else:
            logger.error(f"OpenRouter API connection validation failed: {response.get('error', 'Unknown error')}")
            return False

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            logger.debug("HTTP session closed")