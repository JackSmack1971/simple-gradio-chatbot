# tests/unit/test_openrouter_client.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from src.external.openrouter.client import OpenRouterClient
from src.storage.config_manager import ConfigManager


class TestOpenRouterClient:
    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager for testing."""
        config = Mock(spec=ConfigManager)
        config.get_api_key.return_value = "sk-or-v1-test-key"
        return config

    @pytest.fixture
    def client(self, mock_config_manager):
        """Create client with mocked config manager."""
        return OpenRouterClient(mock_config_manager)

    def test_initialization(self, mock_config_manager):
        """Test client initialization."""
        client = OpenRouterClient(mock_config_manager)
        assert client.config_manager == mock_config_manager
        assert client._session is not None
        assert client.BASE_URL == "https://openrouter.ai/api/v1"

    def test_get_api_key(self, client, mock_config_manager):
        """Test API key retrieval."""
        key = client._get_api_key()
        assert key == "sk-or-v1-test-key"
        mock_config_manager.get_api_key.assert_called_once()

    def test_validate_api_key_success(self, client, mock_config_manager):
        """Test API key validation success."""
        mock_config_manager.get_api_key.return_value = "sk-or-v1-valid-key"
        assert client._validate_api_key() is True

    def test_validate_api_key_missing(self, client, mock_config_manager):
        """Test API key validation with missing key."""
        mock_config_manager.get_api_key.return_value = None
        assert client._validate_api_key() is False

    def test_validate_api_key_invalid(self, client, mock_config_manager):
        """Test API key validation with invalid key."""
        mock_config_manager.get_api_key.return_value = "invalid-key"
        assert client._validate_api_key() is False

    @patch('src.external.openrouter.client.requests.Session')
    def test_setup_session(self, mock_session_class, mock_config_manager):
        """Test session setup with retry strategy."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        client = OpenRouterClient(mock_config_manager)

        # Verify session was created
        mock_session_class.assert_called_once()

        # Verify headers were set
        mock_session.headers.update.assert_called_with({
            'Content-Type': 'application/json',
            'User-Agent': 'PersonalAI-Chatbot/1.0'
        })

        # Verify adapter was mounted
        mock_session.mount.assert_called()

    @patch.object(OpenRouterClient, '_make_request')
    def test_chat_completion_success(self, mock_make_request, client):
        """Test successful chat completion."""
        mock_response = {"choices": [{"message": {"content": "Hello!"}}]}
        mock_make_request.return_value = (True, mock_response)

        messages = [{"role": "user", "content": "Hello"}]
        success, response = client.chat_completion("test-model", messages)

        assert success is True
        assert response == mock_response
        mock_make_request.assert_called_once_with(
            'POST', 'chat/completions',
            {"model": "test-model", "messages": messages}
        )

    def test_chat_completion_invalid_model(self, client):
        """Test chat completion with invalid model ID."""
        from src.utils.validators import validate_model_id

        with patch('src.external.openrouter.client.validate_model_id') as mock_validate:
            mock_validate.return_value = (False, "Invalid model")

            messages = [{"role": "user", "content": "Hello"}]
            success, response = client.chat_completion("invalid/model", messages)

            assert success is False
            assert response == {"error": "Invalid model"}

    @patch.object(OpenRouterClient, '_make_request')
    def test_list_models_success(self, mock_make_request, client):
        """Test successful model listing."""
        mock_response = {"data": [{"id": "model1"}, {"id": "model2"}]}
        mock_make_request.return_value = (True, mock_response)

        success, response = client.list_models()

        assert success is True
        assert response == mock_response
        mock_make_request.assert_called_once_with('GET', 'models')

    @patch.object(OpenRouterClient, '_make_request')
    def test_validate_connection_success(self, mock_make_request, client):
        """Test successful connection validation."""
        mock_make_request.return_value = (True, {"data": []})

        result = client.validate_connection()

        assert result is True
        mock_make_request.assert_called_once_with('GET', 'models')

    @patch.object(OpenRouterClient, '_make_request')
    def test_validate_connection_failure(self, mock_make_request, client):
        """Test connection validation failure."""
        mock_make_request.return_value = (False, {"error": "Connection failed"})

        result = client.validate_connection()

        assert result is False

    def test_close(self, client):
        """Test session closing."""
        client.close()
        client._session.close.assert_called_once()

    @patch.object(OpenRouterClient, '_validate_api_key')
    @patch('src.external.openrouter.client.requests.Session')
    def test_make_request_success(self, mock_session_class, mock_validate_api_key, mock_config_manager):
        """Test successful request making."""
        mock_validate_api_key.return_value = True

        # Mock session and response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = OpenRouterClient(mock_config_manager)

        success, data = client._make_request('POST', 'test/endpoint', {"test": "data"})

        assert success is True
        assert data == {"success": True}

        # Verify request was made correctly
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://openrouter.ai/api/v1/test/endpoint"
        assert call_args[1]["json"] == {"test": "data"}
        assert "Authorization" in call_args[1]["headers"]

    @patch.object(OpenRouterClient, '_validate_api_key')
    def test_make_request_invalid_api_key(self, mock_validate_api_key, client):
        """Test request making with invalid API key."""
        mock_validate_api_key.return_value = False

        success, data = client._make_request('GET', 'test')

        assert success is False
        assert data == {"error": "API key not configured or invalid"}

    @patch.object(OpenRouterClient, '_validate_api_key')
    @patch('src.external.openrouter.client.requests.Session')
    def test_make_request_timeout(self, mock_session_class, mock_validate_api_key, mock_config_manager):
        """Test request timeout handling."""
        mock_validate_api_key.return_value = True

        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.Timeout()
        mock_session_class.return_value = mock_session

        client = OpenRouterClient(mock_config_manager)

        success, data = client._make_request('GET', 'test')

        assert success is False
        assert "timeout" in data["error"].lower()

    @patch.object(OpenRouterClient, '_validate_api_key')
    @patch('src.external.openrouter.client.requests.Session')
    def test_make_request_http_error(self, mock_session_class, mock_validate_api_key, mock_config_manager):
        """Test HTTP error handling."""
        mock_validate_api_key.return_value = True

        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.reason = "Too Many Requests"
        mock_response.json.return_value = {"error": "Rate limited"}

        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_session.get.side_effect = http_error
        mock_session_class.return_value = mock_session

        client = OpenRouterClient(mock_config_manager)

        success, data = client._make_request('GET', 'test')

        assert success is False
        assert data == {"error": "Rate limited"}