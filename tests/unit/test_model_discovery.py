# tests/unit/test_model_discovery.py
import pytest
from unittest.mock import Mock, patch

from src.external.openrouter.model_discovery import ModelDiscovery, ModelInfo
from src.external.openrouter.client import OpenRouterClient


class TestModelInfo:
    """Test the ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test ModelInfo object creation."""
        model = ModelInfo(
            id="anthropic/claude-3-haiku",
            name="Claude 3 Haiku",
            provider="anthropic",
            context_length=200000,
            pricing={"prompt": 0.25, "completion": 1.25},
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=False
        )

        assert model.id == "anthropic/claude-3-haiku"
        assert model.name == "Claude 3 Haiku"
        assert model.provider == "anthropic"
        assert model.context_length == 200000
        assert model.cost_per_token_input == 0.25
        assert model.cost_per_token_output == 1.25
        assert model.supports_streaming is True
        assert model.supports_function_calling is True
        assert model.supports_vision is False

    def test_model_info_defaults(self):
        """Test ModelInfo with default values."""
        model = ModelInfo(
            id="test/model",
            name="Test Model",
            provider="test",
            context_length=1000,
            pricing={}
        )

        assert model.cost_per_token_input == 0.0
        assert model.cost_per_token_output == 0.0
        assert model.supports_streaming is False
        assert model.supports_function_calling is False
        assert model.supports_vision is False
        assert model.max_tokens is None
        assert model.description is None


class TestModelDiscovery:
    """Test the ModelDiscovery class."""

    @pytest.fixture
    def mock_client(self):
        """Mock OpenRouterClient."""
        return Mock(spec=OpenRouterClient)

    @pytest.fixture
    def model_discovery(self, mock_client):
        """Create ModelDiscovery instance."""
        return ModelDiscovery(mock_client, cache_ttl=60)

    def test_initialization(self, mock_client):
        """Test ModelDiscovery initialization."""
        discovery = ModelDiscovery(mock_client, cache_ttl=300)

        assert discovery.client == mock_client
        assert discovery.cache_ttl == 300
        assert discovery._cache is None
        assert discovery._cache_timestamp is None
        assert discovery._models == {}

    def test_is_cache_valid_no_cache(self, model_discovery):
        """Test cache validity when no cache exists."""
        assert model_discovery._is_cache_valid() is False

    def test_is_cache_valid_expired(self, model_discovery):
        """Test cache validity when cache is expired."""
        import time
        model_discovery._cache_timestamp = time.time() - 120  # 2 minutes ago
        model_discovery._cache = {"data": []}

        assert model_discovery._is_cache_valid() is False

    @patch('time.time')
    def test_is_cache_valid_fresh(self, mock_time, model_discovery):
        """Test cache validity when cache is fresh."""
        mock_time.return_value = 1000
        model_discovery._cache_timestamp = 950  # 50 seconds ago
        model_discovery._cache = {"data": []}

        assert model_discovery._is_cache_valid() is True

    def test_parse_single_model(self, model_discovery):
        """Test parsing a single model from API data."""
        model_data = {
            "id": "anthropic/claude-3-haiku",
            "name": "Claude 3 Haiku",
            "context_length": 200000,
            "pricing": {"prompt": "0.25", "completion": "1.25"},
            "supported_parameters": ["streaming", "tools"],
            "architecture": {"modality": "text"},
            "description": "A helpful AI model"
        }

        model = model_discovery._parse_single_model(model_data)

        assert model.id == "anthropic/claude-3-haiku"
        assert model.name == "Claude 3 Haiku"
        assert model.provider == "anthropic"
        assert model.context_length == 200000
        assert model.cost_per_token_input == 0.25
        assert model.cost_per_token_output == 1.25
        assert model.supports_streaming is True
        assert model.supports_function_calling is True
        assert model.supports_vision is False
        assert model.description == "A helpful AI model"

    def test_parse_single_model_missing_id(self, model_discovery):
        """Test parsing model with missing ID."""
        model_data = {"name": "Test Model"}
        model = model_discovery._parse_single_model(model_data)
        assert model is None

    def test_parse_models(self, model_discovery):
        """Test parsing multiple models from API response."""
        api_data = {
            "data": [
                {"id": "model1", "name": "Model 1"},
                {"id": "model2", "name": "Model 2"},
                {"name": "Invalid Model"}  # Missing ID
            ]
        }

        model_discovery._parse_models(api_data)

        assert len(model_discovery._models) == 2
        assert "model1" in model_discovery._models
        assert "model2" in model_discovery._models
        assert "Invalid Model" not in [m.name for m in model_discovery._models.values()]

    def test_fetch_models_success(self, model_discovery, mock_client):
        """Test successful model fetching."""
        mock_response = {
            "data": [
                {"id": "test/model1", "name": "Test Model 1"},
                {"id": "test/model2", "name": "Test Model 2"}
            ]
        }
        mock_client.list_models.return_value = (True, mock_response)

        success = model_discovery._fetch_models()

        assert success is True
        assert len(model_discovery._models) == 2
        assert model_discovery._cache == mock_response
        assert model_discovery._cache_timestamp is not None

    def test_fetch_models_failure(self, model_discovery, mock_client):
        """Test failed model fetching."""
        mock_client.list_models.return_value = (False, {"error": "API error"})

        success = model_discovery._fetch_models()

        assert success is False
        assert len(model_discovery._models) == 0

    def test_get_all_models_cached(self, model_discovery):
        """Test getting all models from cache."""
        # Set up cache
        model_discovery._models = {"model1": Mock(id="model1")}
        model_discovery._cache_timestamp = 1000

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            models = model_discovery.get_all_models()

        assert len(models) == 1
        assert "model1" in models

    def test_get_all_models_refresh(self, model_discovery):
        """Test getting all models with refresh."""
        with patch.object(model_discovery, '_fetch_models', return_value=True) as mock_fetch:
            model_discovery.get_all_models(refresh=True)

        mock_fetch.assert_called_once()

    def test_get_model_found(self, model_discovery):
        """Test getting a specific model that exists."""
        mock_model = Mock()
        model_discovery._models = {"test/model": mock_model}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            result = model_discovery.get_model("test/model")

        assert result == mock_model

    def test_get_model_not_found(self, model_discovery):
        """Test getting a specific model that doesn't exist."""
        model_discovery._models = {}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            result = model_discovery.get_model("nonexistent/model")

        assert result is None

    def test_find_models_by_provider(self, model_discovery):
        """Test finding models by provider."""
        model1 = Mock(provider="anthropic")
        model2 = Mock(provider="openai")
        model3 = Mock(provider="anthropic")

        model_discovery._models = {
            "model1": model1,
            "model2": model2,
            "model3": model3
        }

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            anthropic_models = model_discovery.find_models_by_provider("anthropic")

        assert len(anthropic_models) == 2
        assert model1 in anthropic_models
        assert model3 in anthropic_models

    def test_find_models_by_capability_streaming(self, model_discovery):
        """Test finding models by streaming capability."""
        model1 = Mock(supports_streaming=True)
        model2 = Mock(supports_streaming=False)

        model_discovery._models = {"model1": model1, "model2": model2}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            streaming_models = model_discovery.find_models_by_capability("streaming")

        assert len(streaming_models) == 1
        assert model1 in streaming_models

    def test_find_models_by_capability_unknown(self, model_discovery):
        """Test finding models by unknown capability."""
        model_discovery._models = {"model1": Mock()}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            models = model_discovery.find_models_by_capability("unknown")

        assert len(models) == 0

    def test_get_cheapest_model(self, model_discovery):
        """Test finding the cheapest model."""
        model1 = Mock()
        model1.cost_per_token_input = 0.5
        model1.cost_per_token_output = 1.0

        model2 = Mock()
        model2.cost_per_token_input = 0.3
        model2.cost_per_token_output = 0.8

        model_discovery._models = {"model1": model1, "model2": model2}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            cheapest = model_discovery.get_cheapest_model()

        assert cheapest == model2  # Lower total cost

    def test_get_cheapest_model_with_constraints(self, model_discovery):
        """Test finding cheapest model with capability constraints."""
        model1 = Mock()
        model1.cost_per_token_input = 0.3
        model1.cost_per_token_output = 0.8
        model1.supports_streaming = False

        model2 = Mock()
        model2.cost_per_token_input = 0.5
        model2.cost_per_token_output = 1.0
        model2.supports_streaming = True

        model_discovery._models = {"model1": model1, "model2": model2}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            cheapest = model_discovery.get_cheapest_model(required_capabilities=["streaming"])

        assert cheapest == model2  # Only model with streaming

    def test_get_fallback_model_preferred_available(self, model_discovery):
        """Test fallback when preferred model is available."""
        model_discovery._models = {"preferred/model": Mock()}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            result = model_discovery.get_fallback_model("preferred/model")

        assert result == "preferred/model"

    def test_get_fallback_model_from_defaults(self, model_discovery):
        """Test fallback to default models."""
        model_discovery._models = {"anthropic/claude-3-haiku": Mock()}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            result = model_discovery.get_fallback_model("unavailable/model")

        assert result == "anthropic/claude-3-haiku"

    def test_get_fallback_model_none_available(self, model_discovery):
        """Test fallback when no models are available."""
        model_discovery._models = {}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            result = model_discovery.get_fallback_model()

        assert result is None

    def test_validate_model_valid(self, model_discovery):
        """Test model validation for existing model."""
        model_discovery._models = {"valid/model": Mock()}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            result = model_discovery.validate_model("valid/model")

        assert result is True

    def test_validate_model_invalid(self, model_discovery):
        """Test model validation for non-existing model."""
        model_discovery._models = {}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            result = model_discovery.validate_model("invalid/model")

        assert result is False

    def test_get_model_capabilities(self, model_discovery):
        """Test getting model capabilities."""
        mock_model = Mock()
        mock_model.supports_streaming = True
        mock_model.supports_function_calling = False
        mock_model.supports_vision = True

        model_discovery._models = {"test/model": mock_model}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            capabilities = model_discovery.get_model_capabilities("test/model")

        assert capabilities == {
            "streaming": True,
            "function_calling": False,
            "vision": True
        }

    def test_get_model_capabilities_not_found(self, model_discovery):
        """Test getting capabilities for non-existing model."""
        model_discovery._models = {}

        with patch.object(model_discovery, '_is_cache_valid', return_value=True):
            capabilities = model_discovery.get_model_capabilities("nonexistent/model")

        assert capabilities is None

    def test_clear_cache(self, model_discovery):
        """Test cache clearing."""
        model_discovery._cache = {"data": []}
        model_discovery._cache_timestamp = 1000
        model_discovery._models = {"model1": Mock()}

        model_discovery.clear_cache()

        assert model_discovery._cache is None
        assert model_discovery._cache_timestamp is None
        assert model_discovery._models == {}