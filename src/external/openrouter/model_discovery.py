# src/external/openrouter/model_discovery.py
import time
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass

from ...utils.logging import logger
from .client import OpenRouterClient


@dataclass
class ModelInfo:
    """Information about an AI model."""
    id: str
    name: str
    provider: str
    context_length: int
    pricing: Dict[str, float]
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool
    max_tokens: Optional[int] = None
    description: Optional[str] = None

    @property
    def cost_per_token_input(self) -> float:
        """Cost per input token in USD."""
        return self.pricing.get('prompt', 0.0)

    @property
    def cost_per_token_output(self) -> float:
        """Cost per output token in USD."""
        return self.pricing.get('completion', 0.0)


class ModelDiscovery:
    """Dynamic model list retrieval and capability detection."""

    # Default fallback models in order of preference
    FALLBACK_MODELS = [
        'anthropic/claude-3-haiku',
        'openai/gpt-3.5-turbo',
        'meta-llama/llama-2-70b-chat',
        'anthropic/claude-2'
    ]

    def __init__(self, client: OpenRouterClient, cache_ttl: int = 3600):
        """
        Initialize model discovery.

        Args:
            client: OpenRouterClient instance
            cache_ttl: Cache time-to-live in seconds (default 1 hour)
        """
        self.client = client
        self.cache_ttl = cache_ttl
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
        self._models: Dict[str, ModelInfo] = {}

    def _is_cache_valid(self) -> bool:
        """Check if the cached data is still valid."""
        if self._cache is None or self._cache_timestamp is None:
            return False
        return time.time() - self._cache_timestamp < self.cache_ttl

    def _fetch_models(self) -> bool:
        """
        Fetch models from the API.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Fetching models from OpenRouter API")
        success, data = self.client.list_models()

        if not success:
            logger.error(f"Failed to fetch models: {data}")
            return False

        self._cache = data
        self._cache_timestamp = time.time()
        self._parse_models(data)
        logger.info(f"Successfully fetched and parsed {len(self._models)} models")
        return True

    def _parse_models(self, data: Dict[str, Any]) -> None:
        """Parse model data from API response."""
        self._models.clear()

        models_data = data.get('data', [])
        if not isinstance(models_data, list):
            logger.warning("Models data is not a list")
            return

        for model_data in models_data:
            try:
                model_info = self._parse_single_model(model_data)
                if model_info:
                    self._models[model_info.id] = model_info
            except Exception as e:
                logger.warning(f"Failed to parse model data: {e}, data: {model_data}")

    def _parse_single_model(self, model_data: Dict[str, Any]) -> Optional[ModelInfo]:
        """Parse a single model's data."""
        model_id = model_data.get('id')
        if not model_id:
            return None

        # Extract provider from model ID
        provider = model_id.split('/')[0] if '/' in model_id else 'unknown'

        # Extract pricing information
        pricing = model_data.get('pricing', {})
        if isinstance(pricing, dict):
            # Convert string values to float
            pricing = {k: float(v) if isinstance(v, (str, int)) else v for k, v in pricing.items()}
        else:
            pricing = {}

        # Extract capabilities
        architecture = model_data.get('architecture', {})
        modality = model_data.get('architecture', {}).get('modality', '')

        supports_streaming = 'streaming' in model_data.get('supported_parameters', [])
        supports_function_calling = 'tools' in model_data.get('supported_parameters', [])
        supports_vision = 'image' in modality.lower() or 'vision' in modality.lower()

        model_info = ModelInfo(
            id=model_id,
            name=model_data.get('name', model_id),
            provider=provider,
            context_length=model_data.get('context_length', 0),
            pricing=pricing,
            supports_streaming=supports_streaming,
            supports_function_calling=supports_function_calling,
            supports_vision=supports_vision,
            max_tokens=model_data.get('top_provider', {}).get('max_completion_tokens'),
            description=model_data.get('description')
        )

        return model_info

    def get_all_models(self, refresh: bool = False) -> Dict[str, ModelInfo]:
        """
        Get all available models.

        Args:
            refresh: Force refresh from API

        Returns:
            Dict of model_id -> ModelInfo
        """
        if refresh or not self._is_cache_valid():
            if not self._fetch_models():
                logger.warning("Failed to fetch models, returning cached data if available")
                if self._models:
                    return self._models.copy()
                return {}

        return self._models.copy()

    def get_model(self, model_id: str, refresh: bool = False) -> Optional[ModelInfo]:
        """
        Get information about a specific model.

        Args:
            model_id: Model identifier
            refresh: Force refresh from API

        Returns:
            ModelInfo object or None if not found
        """
        models = self.get_all_models(refresh=refresh)
        return models.get(model_id)

    def find_models_by_provider(self, provider: str, refresh: bool = False) -> List[ModelInfo]:
        """
        Find all models from a specific provider.

        Args:
            provider: Provider name (e.g., 'anthropic', 'openai')
            refresh: Force refresh from API

        Returns:
            List of ModelInfo objects
        """
        models = self.get_all_models(refresh=refresh)
        return [model for model in models.values() if model.provider.lower() == provider.lower()]

    def find_models_by_capability(self, capability: str, refresh: bool = False) -> List[ModelInfo]:
        """
        Find models that support a specific capability.

        Args:
            capability: Capability to filter by ('streaming', 'function_calling', 'vision')
            refresh: Force refresh from API

        Returns:
            List of ModelInfo objects
        """
        models = self.get_all_models(refresh=refresh)

        if capability == 'streaming':
            return [model for model in models.values() if model.supports_streaming]
        elif capability == 'function_calling':
            return [model for model in models.values() if model.supports_function_calling]
        elif capability == 'vision':
            return [model for model in models.values() if model.supports_vision]
        else:
            logger.warning(f"Unknown capability: {capability}")
            return []

    def get_cheapest_model(self, max_cost_per_token: Optional[float] = None,
                          required_capabilities: Optional[List[str]] = None,
                          refresh: bool = False) -> Optional[ModelInfo]:
        """
        Find the cheapest model that meets requirements.

        Args:
            max_cost_per_token: Maximum cost per token (combined input+output)
            required_capabilities: List of required capabilities
            refresh: Force refresh from API

        Returns:
            ModelInfo object or None if no suitable model found
        """
        models = self.get_all_models(refresh=refresh)

        # Filter by capabilities
        if required_capabilities:
            filtered_models = []
            for model in models.values():
                has_all_capabilities = True
                for cap in required_capabilities:
                    if cap == 'streaming' and not model.supports_streaming:
                        has_all_capabilities = False
                        break
                    elif cap == 'function_calling' and not model.supports_function_calling:
                        has_all_capabilities = False
                        break
                    elif cap == 'vision' and not model.supports_vision:
                        has_all_capabilities = False
                        break
                if has_all_capabilities:
                    filtered_models.append(model)
        else:
            filtered_models = list(models.values())

        # Filter by cost
        if max_cost_per_token is not None:
            filtered_models = [
                model for model in filtered_models
                if (model.cost_per_token_input + model.cost_per_token_output) <= max_cost_per_token
            ]

        # Find cheapest
        if not filtered_models:
            return None

        return min(filtered_models, key=lambda m: m.cost_per_token_input + m.cost_per_token_output)

    def get_fallback_model(self, preferred_model: Optional[str] = None,
                          required_capabilities: Optional[List[str]] = None,
                          refresh: bool = False) -> Optional[str]:
        """
        Get a fallback model ID if the preferred model is not available.

        Args:
            preferred_model: Preferred model ID
            required_capabilities: Required capabilities for fallback
            refresh: Force refresh from API

        Returns:
            Model ID or None if no suitable fallback found
        """
        models = self.get_all_models(refresh=refresh)
        available_model_ids = set(models.keys())

        # Check if preferred model is available and meets requirements
        if preferred_model and preferred_model in available_model_ids:
            model_info = models[preferred_model]
            if self._model_meets_requirements(model_info, required_capabilities):
                return preferred_model

        # Try fallback models in order
        for fallback_id in self.FALLBACK_MODELS:
            if fallback_id in available_model_ids:
                model_info = models[fallback_id]
                if self._model_meets_requirements(model_info, required_capabilities):
                    logger.info(f"Using fallback model: {fallback_id}")
                    return fallback_id

        # If no specific fallback works, return any available model
        if models:
            first_model = next(iter(models.values()))
            logger.warning(f"No suitable fallback model found, using: {first_model.id}")
            return first_model.id

        logger.error("No models available")
        return None

    def _model_meets_requirements(self, model: ModelInfo, requirements: Optional[List[str]]) -> bool:
        """Check if a model meets the required capabilities."""
        if not requirements:
            return True

        for req in requirements:
            if req == 'streaming' and not model.supports_streaming:
                return False
            elif req == 'function_calling' and not model.supports_function_calling:
                return False
            elif req == 'vision' and not model.supports_vision:
                return False

        return True

    def validate_model(self, model_id: str, refresh: bool = False) -> bool:
        """
        Validate that a model exists and is available.

        Args:
            model_id: Model identifier to validate
            refresh: Force refresh from API

        Returns:
            True if model is valid and available
        """
        model = self.get_model(model_id, refresh=refresh)
        return model is not None

    def get_model_capabilities(self, model_id: str, refresh: bool = False) -> Optional[Dict[str, bool]]:
        """
        Get capabilities of a specific model.

        Args:
            model_id: Model identifier
            refresh: Force refresh from API

        Returns:
            Dict of capability -> bool, or None if model not found
        """
        model = self.get_model(model_id, refresh=refresh)
        if not model:
            return None

        return {
            'streaming': model.supports_streaming,
            'function_calling': model.supports_function_calling,
            'vision': model.supports_vision
        }

    def clear_cache(self) -> None:
        """Clear the cached model data."""
        self._cache = None
        self._cache_timestamp = None
        self._models.clear()
        logger.info("Model discovery cache cleared")