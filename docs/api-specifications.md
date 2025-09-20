# API Specifications - Personal AI Chatbot

## Overview

This document provides complete technical specifications for all API integrations in the Personal AI Chatbot system. The primary focus is the OpenRouter API integration, which serves as the core AI model access layer.

## 1. OpenRouter API Integration Contract

### 1.1 Authentication Specification

**Authentication Method**: Bearer Token Authentication
**Header**: `Authorization: Bearer {api_key}`
**API Key Source**: User-provided OpenRouter API key
**Validation Requirements**:
- Key format validation (starts with 'sk-or-v1-')
- Functional validation via API test call
- Secure storage with AES-256 encryption
- Automatic rotation support

**Authentication Flow**:
```python
# Authentication header construction
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://personal-chatbot.local",
    "X-Title": "Personal AI Chatbot"
}
```

### 1.2 Chat Completions Endpoint

**Endpoint**: `POST https://openrouter.ai/api/v1/chat/completions`
**Purpose**: Generate AI responses using specified models

#### Request Specification

**Method**: POST
**Content-Type**: application/json
**Timeout**: 60 seconds

**Request Schema**:
```json
{
  "type": "object",
  "required": ["model", "messages"],
  "properties": {
    "model": {
      "type": "string",
      "description": "AI model identifier from OpenRouter catalog",
      "examples": ["anthropic/claude-3-haiku", "openai/gpt-4", "meta-llama/llama-2-70b-chat"]
    },
    "messages": {
      "type": "array",
      "description": "Conversation history as message objects",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["role", "content"],
        "properties": {
          "role": {
            "type": "string",
            "enum": ["system", "user", "assistant"],
            "description": "Role of the message sender"
          },
          "content": {
            "type": "string",
            "description": "Message content",
            "maxLength": 2000
          }
        }
      }
    },
    "stream": {
      "type": "boolean",
      "description": "Enable streaming response",
      "default": false
    },
    "temperature": {
      "type": "number",
      "description": "Response randomness (0.0-2.0)",
      "minimum": 0.0,
      "maximum": 2.0,
      "default": 0.7
    },
    "max_tokens": {
      "type": "integer",
      "description": "Maximum response length",
      "minimum": 1,
      "maximum": 4096,
      "default": 1000
    },
    "top_p": {
      "type": "number",
      "description": "Nucleus sampling parameter",
      "minimum": 0.0,
      "maximum": 1.0
    },
    "frequency_penalty": {
      "type": "number",
      "description": "Repetition penalty",
      "minimum": -2.0,
      "maximum": 2.0,
      "default": 0.0
    },
    "presence_penalty": {
      "type": "number",
      "description": "Topic diversity penalty",
      "minimum": -2.0,
      "maximum": 2.0,
      "default": 0.0
    }
  }
}
```

#### Response Specification

**Success Response (200)**:
```json
{
  "type": "object",
  "required": ["id", "choices", "usage"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique request identifier"
    },
    "object": {
      "type": "string",
      "enum": ["chat.completion"],
      "description": "Response object type"
    },
    "created": {
      "type": "integer",
      "description": "Unix timestamp of response creation"
    },
    "model": {
      "type": "string",
      "description": "Model used for generation"
    },
    "choices": {
      "type": "array",
      "description": "Array of completion choices",
      "items": {
        "type": "object",
        "required": ["index", "message", "finish_reason"],
        "properties": {
          "index": {
            "type": "integer",
            "description": "Choice index"
          },
          "message": {
            "type": "object",
            "required": ["role", "content"],
            "properties": {
              "role": {
                "type": "string",
                "enum": ["assistant"],
                "description": "Assistant role"
              },
              "content": {
                "type": "string",
                "description": "Generated response content"
              }
            }
          },
          "finish_reason": {
            "type": "string",
            "enum": ["stop", "length", "content_filter"],
            "description": "Reason for completion termination"
          }
        }
      }
    },
    "usage": {
      "type": "object",
      "required": ["prompt_tokens", "completion_tokens", "total_tokens"],
      "properties": {
        "prompt_tokens": {
          "type": "integer",
          "description": "Tokens in the prompt"
        },
        "completion_tokens": {
          "type": "integer",
          "description": "Tokens in the completion"
        },
        "total_tokens": {
          "type": "integer",
          "description": "Total tokens used"
        }
      }
    }
  }
}
```

### 1.3 Streaming Response Specification

**Content-Type**: text/plain
**Transfer-Encoding**: chunked

**Stream Chunk Format**:
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"anthropic/claude-3-haiku","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652289,"model":"anthropic/claude-3-haiku","choices":[{"index":0,"delta":{"content":" there"},"finish_reason":null}]}

data: [DONE]
```

**Stream Chunk Schema**:
```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Request identifier"
    },
    "object": {
      "type": "string",
      "enum": ["chat.completion.chunk"],
      "description": "Chunk object type"
    },
    "created": {
      "type": "integer",
      "description": "Chunk creation timestamp"
    },
    "model": {
      "type": "string",
      "description": "Model identifier"
    },
    "choices": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "index": {
            "type": "integer",
            "description": "Choice index"
          },
          "delta": {
            "type": "object",
            "properties": {
              "content": {
                "type": "string",
                "description": "Incremental content"
              }
            }
          },
          "finish_reason": {
            "type": ["string", "null"],
            "enum": ["stop", "length", "content_filter", null],
            "description": "Completion finish reason"
          }
        }
      }
    }
  }
}
```

### 1.4 Models Endpoint

**Endpoint**: `GET https://openrouter.ai/api/v1/models`
**Purpose**: Retrieve available models catalog

#### Request Specification

**Method**: GET
**Headers**: Standard authentication headers

#### Response Specification

**Success Response (200)**:
```json
{
  "type": "object",
  "required": ["data"],
  "properties": {
    "data": {
      "type": "array",
      "description": "Array of available models",
      "items": {
        "type": "object",
        "required": ["id", "name", "pricing"],
        "properties": {
          "id": {
            "type": "string",
            "description": "Model identifier"
          },
          "name": {
            "type": "string",
            "description": "Human-readable model name"
          },
          "description": {
            "type": "string",
            "description": "Model description"
          },
          "pricing": {
            "type": "object",
            "properties": {
              "prompt": {
                "type": "string",
                "description": "Cost per prompt token"
              },
              "completion": {
                "type": "string",
                "description": "Cost per completion token"
              }
            }
          },
          "context_length": {
            "type": "integer",
            "description": "Maximum context length"
          },
          "architecture": {
            "type": "object",
            "properties": {
              "modality": {
                "type": "string",
                "description": "Input/output modalities"
              },
              "tokenizer": {
                "type": "string",
                "description": "Tokenizer type"
              }
            }
          }
        }
      }
    }
  }
}
```

### 1.5 Key Information Endpoint

**Endpoint**: `GET https://openrouter.ai/api/v1/key`
**Purpose**: Retrieve API key usage and limits

#### Response Specification

```json
{
  "type": "object",
  "required": ["data"],
  "properties": {
    "data": {
      "type": "object",
      "properties": {
        "label": {
          "type": "string",
          "description": "API key label"
        },
        "usage": {
          "type": "number",
          "description": "Current usage in credits"
        },
        "limit": {
          "type": "number",
          "description": "Usage limit in credits"
        },
        "is_free_tier": {
          "type": "boolean",
          "description": "Whether key is on free tier"
        },
        "rate_limit": {
          "type": "object",
          "properties": {
            "requests": {
              "type": "integer",
              "description": "Requests per time window"
            },
            "interval": {
              "type": "string",
              "description": "Time window (e.g., '1m', '1h')"
            }
          }
        }
      }
    }
  }
}
```

## 2. Error Handling Specifications

### 2.1 HTTP Error Codes

| Status Code | Error Type | Description | Recovery Action |
|-------------|------------|-------------|----------------|
| 400 | Bad Request | Invalid request parameters | Validate input, retry with correction |
| 401 | Unauthorized | Invalid API key | Prompt user for new key |
| 402 | Payment Required | Insufficient credits | Prompt user to add credits |
| 403 | Forbidden | Content policy violation | Notify user, suggest rephrasing |
| 408 | Request Timeout | Request took too long | Retry with backoff |
| 429 | Too Many Requests | Rate limit exceeded | Wait and retry |
| 500 | Internal Server Error | OpenRouter server error | Retry with exponential backoff |
| 502 | Bad Gateway | Model provider unavailable | Retry or suggest alternative model |
| 503 | Service Unavailable | No providers available | Retry or show offline mode |

### 2.2 Error Response Schema

```json
{
  "type": "object",
  "properties": {
    "error": {
      "type": "object",
      "required": ["message"],
      "properties": {
        "message": {
          "type": "string",
          "description": "Human-readable error message"
        },
        "code": {
          "type": "integer",
          "description": "Error code"
        },
        "metadata": {
          "type": "object",
          "description": "Additional error context",
          "properties": {
            "flagged_input": {
              "type": "string",
              "description": "Flagged content identifier"
            },
            "retry_after": {
              "type": "integer",
              "description": "Seconds to wait before retry"
            }
          }
        }
      }
    }
  }
}
```

## 3. Rate Limiting and Retry Logic

### 3.1 Rate Limiting Specification

**Free Tier Limits**:
- 20 requests per minute
- 1000 requests per day
- Automatic upgrade prompts when approaching limits

**Rate Limit Headers**:
```
X-RateLimit-Limit-Requests: 20
X-RateLimit-Remaining-Requests: 19
X-RateLimit-Reset-Requests: 1677652340
```

### 3.2 Retry Strategy

**Retry Conditions**:
- HTTP 408 (Timeout)
- HTTP 429 (Rate Limited)
- HTTP 500-503 (Server Errors)
- Network connection errors

**Retry Configuration**:
```python
retry_config = {
    "max_attempts": 3,
    "backoff_factor": 2.0,
    "initial_delay": 1.0,
    "max_delay": 60.0,
    "jitter": True
}
```

**Exponential Backoff Algorithm**:
```
delay = min(initial_delay * (backoff_factor ^ attempt), max_delay)
delay = delay * (0.5 + random(0, 1))  # Add jitter
```

## 4. API Client Implementation Contract

### 4.1 Interface Definition

```python
class OpenRouterAPIClient:
    """OpenRouter API client with comprehensive error handling"""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1")

    async def chat_completion(self,
                            messages: List[Dict[str, Any]],
                            model: str,
                            **kwargs) -> Dict[str, Any]:
        """Execute chat completion with full error handling"""

    async def stream_completion(self,
                               messages: List[Dict[str, Any]],
                               model: str,
                               **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion with real-time error handling"""

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Retrieve and cache available models"""

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Check current rate limiting status"""

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and functionality"""
```

### 4.2 Error Handling Contract

```python
class APIError(Exception):
    """Base API error"""
    pass

class AuthenticationError(APIError):
    """API key authentication failure"""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after

class ModelError(APIError):
    """Model not available or invalid"""
    pass

class ServerError(APIError):
    """OpenRouter server error"""
    pass
```

## 5. Performance Specifications

### 5.1 Response Time Targets

- **Cold Start**: < 3 seconds to first API call
- **Warm Response**: < 10 seconds for typical queries (100-500 tokens)
- **Streaming Latency**: < 500ms per chunk
- **Model Switch**: < 2 seconds validation and switch

### 5.2 Resource Limits

- **Concurrent Requests**: Maximum 5 simultaneous API calls
- **Request Timeout**: 60 seconds maximum
- **Connection Pool**: 10 connections maximum
- **Retry Budget**: 3 attempts per request

### 5.3 Monitoring Requirements

**Metrics to Track**:
- Response time percentiles (p50, p95, p99)
- Error rate by error type
- Rate limit usage percentage
- Model availability status
- Token usage per request

**Health Checks**:
- API connectivity test
- Model availability verification
- Rate limit status monitoring
- Response time degradation alerts

## 6. Security Specifications

### 6.1 Data Protection

- **API Key Storage**: AES-256 encryption with PBKDF2 key derivation
- **Network Security**: HTTPS-only with certificate validation
- **Input Validation**: Multi-layer sanitization and validation
- **Output Encoding**: XSS prevention in all responses

### 6.2 Authentication Security

- **Key Validation**: Format and functional verification
- **Secure Headers**: Proper security headers in all requests
- **Key Rotation**: Support for seamless API key updates
- **Access Logging**: Audit trail of all API interactions

### 6.3 Content Security

- **Input Sanitization**: Remove potentially harmful content
- **Output Filtering**: Prevent XSS and injection attacks
- **Content Moderation**: Handle OpenRouter content policy responses
- **Data Leakage Prevention**: No sensitive data in logs or responses

This API specification provides the complete contract for OpenRouter integration, ensuring reliable, secure, and performant AI model access for the Personal AI Chatbot.
    async def list_models(self) -> List[Dict[str, Any]]:
        """Retrieve available models catalog"""

    async def validate_key(self) -> Dict[str, Any]:
        """Validate API key and retrieve usage information"""

## 5. Implementation Details

### 5.1 Component Architecture

The OpenRouter API integration is implemented through four main components:

#### 5.1.1 OpenRouterClient (`src/external/openrouter/client.py`)
**Purpose**: HTTP client for OpenRouter API with authentication and request handling

**Key Features**:
- Secure API key authentication via ConfigManager
- HTTP request/response handling with proper headers
- Request timeout management (30 seconds default)
- Response parsing and validation
- Connection pooling with retry strategy (3 retries, exponential backoff)
- Session management for connection reuse

**Methods**:
- `chat_completion(model, messages, **kwargs)` - Execute chat completion requests
- `list_models()` - Retrieve available models catalog
- `validate_connection()` - Test API connectivity and authentication
- `close()` - Clean up HTTP session

#### 5.1.2 RateLimiter (`src/external/openrouter/rate_limiter.py`)
**Purpose**: Client-side rate limiting using token bucket algorithm

**Key Features**:
- Token bucket algorithm with configurable rates (default: 60 req/min, 10 burst)
- Request queuing with priority support (lower number = higher priority)
- Model-specific rate limits
- Background worker thread for processing queued requests
- Automatic token refill based on elapsed time

**Methods**:
- `make_request(func, *args, priority=0, model=None, **kwargs)` - Queue or execute request
- `set_model_limit(model, requests_per_minute, burst_limit)` - Configure model-specific limits
- `get_queue_status()` - Monitor queue statistics
- `wait_for_slot(timeout)` - Wait for rate limit slot availability
- `clear_queue()` - Clear pending requests
- `shutdown()` - Graceful shutdown of worker thread

#### 5.1.3 ErrorHandler (`src/external/openrouter/error_handler.py`)
**Purpose**: Comprehensive error processing and user-friendly messaging

**Key Features**:
- HTTP status code mapping to user-friendly messages
- OpenRouter-specific error code handling
- Automatic retry logic with exponential backoff and jitter
- Error classification (Network, Authentication, Rate Limit, API Error, Validation)
- Sensitive information sanitization in error messages
- Configurable retry parameters (max 3 attempts, 1-60s backoff range)

**Error Classifications**:
- `NETWORK`: Connection timeouts, DNS failures, network errors
- `AUTHENTICATION`: Invalid API keys, unauthorized access
- `RATE_LIMIT`: Request rate exceeded
- `API_ERROR`: Server errors (5xx status codes)
- `VALIDATION`: Invalid requests, model not found, etc.

**Methods**:
- `handle_error(error_data, status_code, attempt_count)` - Process error comprehensively
- `should_retry(error_type, attempt_count)` - Determine retry eligibility
- `calculate_backoff(attempt_count, error_type)` - Calculate retry delay
- `execute_with_retry(func, *args, **kwargs)` - Execute with automatic retries

#### 5.1.4 ModelDiscovery (`src/external/openrouter/model_discovery.py`)
**Purpose**: Dynamic model list retrieval and capability detection

**Key Features**:
- Cached model catalog with TTL (default 1 hour)
- Model capability detection (streaming, function calling, vision)
- Cost analysis and cheapest model selection
- Provider-based filtering
- Fallback model selection with capability requirements
- Model validation and metadata parsing

**Model Information Structure**:
```python
@dataclass
class ModelInfo:
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
```

**Methods**:
- `get_all_models(refresh=False)` - Retrieve all available models
- `get_model(model_id, refresh=False)` - Get specific model information
- `find_models_by_provider(provider, refresh=False)` - Filter by provider
- `find_models_by_capability(capability, refresh=False)` - Filter by capability
- `get_cheapest_model(max_cost=None, required_capabilities=None)` - Find cheapest suitable model
- `get_fallback_model(preferred_model, required_capabilities)` - Get fallback model
- `validate_model(model_id)` - Check model availability
- `clear_cache()` - Clear cached model data

### 5.2 Integration Patterns

#### 5.2.1 Basic Usage Pattern
```python
from src.external.openrouter.client import OpenRouterClient
from src.external.openrouter.rate_limiter import RateLimiter
from src.external.openrouter.error_handler import ErrorHandler
from src.external.openrouter.model_discovery import ModelDiscovery
from src.storage.config_manager import ConfigManager

# Initialize components
config = ConfigManager()
client = OpenRouterClient(config)
rate_limiter = RateLimiter()
error_handler = ErrorHandler()
model_discovery = ModelDiscovery(client)

# Make a request with full error handling and rate limiting
def make_chat_request():
    return client.chat_completion(
        model="anthropic/claude-3-haiku",
        messages=[{"role": "user", "content": "Hello!"}]
    )

# Execute with rate limiting and retries
success, result = error_handler.execute_with_retry(
    lambda: rate_limiter.make_request(make_chat_request)
)
```

#### 5.2.2 Model Selection Pattern
```python
# Find best available model for the task
model = model_discovery.get_cheapest_model(
    max_cost_per_token=0.01,
    required_capabilities=["streaming"]
)

if model:
    print(f"Selected model: {model.id} (${model.cost_per_token_input:.4f}/input token)")
else:
    # Use fallback
    fallback_id = model_discovery.get_fallback_model(
        preferred_model="anthropic/claude-3-haiku",
        required_capabilities=["streaming"]
    )
```

### 5.3 Configuration

#### 5.3.1 Environment Variables
- `OPENROUTER_API_KEY`: OpenRouter API key (stored securely via ConfigManager)

#### 5.3.2 Default Settings
- **Rate Limiting**: 60 requests/minute, 10 burst capacity
- **Timeouts**: 30 seconds per request
- **Retries**: 3 attempts maximum, exponential backoff (1-60s range)
- **Cache TTL**: 3600 seconds (1 hour) for model discovery
- **Retryable Errors**: Network, Rate Limit, API Error (5xx)

### 5.4 Error Recovery Strategies

#### 5.4.1 Network Errors
- Automatic retry with exponential backoff
- Connection pooling for efficiency
- DNS and SSL error handling

#### 5.4.2 Rate Limiting
- Client-side token bucket algorithm
- Request queuing during rate limit periods
- Model-specific rate limit configuration

#### 5.4.3 API Errors
- Retry transient server errors (5xx)
- User-friendly error messages
- Fallback model selection for unavailable models

#### 5.4.4 Authentication Errors
- API key validation on startup
- Clear error messages for key issues
- No automatic retry for auth failures

### 5.5 Testing and Validation

#### 5.5.1 Unit Test Coverage
- **OpenRouterClient**: HTTP request/response handling, authentication, error conditions
- **RateLimiter**: Token bucket algorithm, queuing, priority handling, threading
- **ErrorHandler**: Error classification, retry logic, backoff calculation, sanitization
- **ModelDiscovery**: Model parsing, caching, filtering, cost analysis

#### 5.5.2 Integration Testing
- End-to-end API communication
- Rate limiting under load
- Error recovery scenarios
- Model discovery and selection

#### 5.5.3 Validation Criteria
- [ ] API key authentication works
- [ ] Basic chat completion requests succeed
- [ ] Rate limiting prevents quota violations
- [ ] Network errors handled gracefully
- [ ] Model list retrieval functions
- [ ] Error messages are user-friendly
- [ ] All unit tests pass with 100% coverage

### 5.6 Performance Characteristics

#### 5.6.1 Throughput
- Rate limited to configured limits (default 60 req/min)
- Concurrent request handling via threading
- Connection pooling for HTTP efficiency

#### 5.6.2 Latency
- Network round-trip time + API processing
- Additional latency for retries and backoff
- Caching reduces model discovery latency

#### 5.6.3 Resource Usage
- Minimal memory footprint for rate limiting state
- HTTP connection pooling reduces overhead
- Background thread for queue processing

### 5.7 Security Considerations

#### 5.7.1 API Key Protection
- Encrypted storage via ConfigManager (AES-256)
- Never logged or exposed in error messages
- Secure key validation and rotation

#### 5.7.2 Input Validation
- Message content length limits (4000 chars)
- Harmful content pattern detection
- Model ID format validation

#### 5.7.3 Error Information
- Sensitive data sanitization in logs
- User-friendly error messages without exposure
- Debug information separated from user output

### 5.8 Monitoring and Observability

#### 5.8.1 Logging
- Structured logging with appropriate levels
- Request/response metrics
- Error classification and frequency
- Rate limiting status and queue depth

#### 5.8.2 Metrics
- Request success/failure rates
- Response times and throughput
- Queue depth and processing delays
- Token usage and rate limit status

#### 5.8.3 Health Checks
- API connectivity validation
- Model availability verification
- Rate limiter status monitoring
- Cache freshness monitoring