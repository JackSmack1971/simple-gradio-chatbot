# tests/fixtures/test_data.py
"""Test fixtures and mock data for integration tests."""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


# Mock API responses
MOCK_CHAT_COMPLETION_RESPONSE = {
    "id": "chatcmpl-mock123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "anthropic/claude-3-haiku",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "Hello! This is a mock response from the AI assistant."
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 15,
        "total_tokens": 25
    }
}

MOCK_STREAMING_RESPONSE_CHUNKS = [
    {"choices": [{"delta": {"content": "Hello"}}]},
    {"choices": [{"delta": {"content": "! "}}]},
    {"choices": [{"delta": {"content": "This"}}]},
    {"choices": [{"delta": {"content": " is"}}]},
    {"choices": [{"delta": {"content": " a"}}]},
    {"choices": [{"delta": {"content": " mock"}}]},
    {"choices": [{"delta": {"content": " response"}}]},
    {"choices": [{"delta": {"content": "."}}]},
]

MOCK_CONVERSATION_DATA = {
    "id": "conv_mock123",
    "title": "Test Conversation",
    "created_at": "2024-01-01T12:00:00.000Z",
    "updated_at": "2024-01-01T12:05:00.000Z",
    "messages": [
        {
            "role": "user",
            "content": "Hello, how are you?",
            "timestamp": "2024-01-01T12:00:00.000Z",
            "metadata": {
                "tokens": 5,
                "length": 19
            }
        },
        {
            "role": "assistant",
            "content": "I'm doing well, thank you for asking!",
            "timestamp": "2024-01-01T12:01:00.000Z",
            "metadata": {
                "tokens": 8,
                "length": 35
            }
        }
    ],
    "metadata": {
        "model": "anthropic/claude-3-haiku",
        "total_tokens": 13,
        "message_count": 2
    }
}

MOCK_APPLICATION_STATE = {
    "_metadata": {
        "created_at": "2024-01-01T12:00:00.000Z",
        "version": "1.0",
        "update_count": 5,
        "last_updated": "2024-01-01T12:05:00.000Z"
    },
    "conversations": {
        "conv_mock123": MOCK_CONVERSATION_DATA
    },
    "ui": {
        "current_view": "chat",
        "settings": {
            "theme": "light",
            "font_size": "medium"
        },
        "preferences": {
            "auto_save": True,
            "notifications": True
        }
    },
    "operation": {
        "status": "idle",
        "current_operation": None,
        "last_operation": {
            "id": "op_mock123",
            "type": "chat_completion",
            "success": True,
            "timestamp": "2024-01-01T12:05:00.000Z"
        }
    },
    "configuration": {
        "api_key_configured": True,
        "default_model": "anthropic/claude-3-haiku",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "performance": {
        "total_operations": 10,
        "successful_operations": 9,
        "failed_operations": 1,
        "average_response_time": 1.2,
        "total_tokens_processed": 250
    }
}

MOCK_ERROR_RESPONSES = {
    "rate_limit": {
        "error": {
            "type": "rate_limit_exceeded",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": 60
        }
    },
    "invalid_api_key": {
        "error": {
            "type": "authentication_error",
            "message": "Invalid API key provided."
        }
    },
    "server_error": {
        "error": {
            "type": "server_error",
            "message": "Internal server error. Please try again."
        }
    },
    "network_error": {
        "error": "Connection failed: Network is unreachable"
    }
}

MOCK_USER_INPUTS = [
    "Hello, how are you today?",
    "Can you help me with Python programming?",
    "What is the weather like?",
    "Tell me a joke",
    "Explain quantum computing in simple terms",
    "Write a function to calculate fibonacci numbers",
    "What are the benefits of exercise?",
    "How do I cook pasta?",
    "What's the meaning of life?",
    "Help me debug this code: def hello(): print('hello')"
]

MOCK_MODEL_CONFIGURATIONS = [
    {
        "id": "anthropic/claude-3-haiku",
        "name": "Claude 3 Haiku",
        "provider": "anthropic",
        "context_window": 200000,
        "max_tokens": 4096,
        "pricing": {
            "input": 0.00025,
            "output": 0.00125
        }
    },
    {
        "id": "openai/gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "provider": "openai",
        "context_window": 16385,
        "max_tokens": 4096,
        "pricing": {
            "input": 0.0015,
            "output": 0.002
        }
    },
    {
        "id": "meta-llama/llama-2-70b-chat",
        "name": "Llama 2 70B Chat",
        "provider": "meta",
        "context_window": 4096,
        "max_tokens": 4096,
        "pricing": {
            "input": 0.0007,
            "output": 0.0009
        }
    }
]

MOCK_PERFORMANCE_METRICS = {
    "response_times": [0.8, 1.2, 1.5, 0.9, 2.1, 1.3, 0.7, 1.8, 1.1, 1.4],
    "token_counts": [25, 45, 67, 23, 89, 34, 56, 78, 45, 67],
    "success_rates": [1, 1, 0, 1, 1, 1, 1, 0, 1, 1],  # 1 = success, 0 = failure
    "memory_usage": [150, 160, 155, 170, 165, 158, 162, 175, 168, 172],  # MB
    "cpu_usage": [15, 18, 22, 16, 25, 19, 17, 28, 21, 23]  # %
}


def create_mock_conversation(conversation_id: Optional[str] = None,
                           message_count: int = 3) -> Dict[str, Any]:
    """Create a mock conversation with specified parameters."""
    if conversation_id is None:
        conversation_id = f"conv_mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    messages = []
    for i in range(message_count):
        role = "user" if i % 2 == 0 else "assistant"
        content = MOCK_USER_INPUTS[i % len(MOCK_USER_INPUTS)] if role == "user" else f"Response to: {MOCK_USER_INPUTS[(i-1) % len(MOCK_USER_INPUTS)]}"

        messages.append({
            "role": role,
            "content": content,
            "timestamp": f"2024-01-01T12:{i:02d}:00.000Z",
            "metadata": {
                "tokens": len(content.split()),
                "length": len(content)
            }
        })

    return {
        "id": conversation_id,
        "title": f"Mock Conversation {conversation_id}",
        "created_at": "2024-01-01T12:00:00.000Z",
        "updated_at": f"2024-01-01T12:{message_count-1:02d}:00.000Z",
        "messages": messages,
        "metadata": {
            "model": "anthropic/claude-3-haiku",
            "total_tokens": sum(msg["metadata"]["tokens"] for msg in messages),
            "message_count": len(messages)
        }
    }


def create_mock_event_data(event_type: str, **kwargs) -> Dict[str, Any]:
    """Create mock event data for testing."""
    base_data = {
        "timestamp": datetime.now().isoformat(),
        "correlation_id": f"corr_mock_{datetime.now().strftime('%H%M%S')}"
    }

    if event_type == "user_input":
        base_data.update({
            "input": kwargs.get("input", "Hello, world!"),
            "conversation_id": kwargs.get("conversation_id", "conv_mock123")
        })
    elif event_type == "api_response":
        base_data.update({
            "response": kwargs.get("response", MOCK_CHAT_COMPLETION_RESPONSE),
            "request_id": kwargs.get("request_id", "req_mock123"),
            "processing_time": kwargs.get("processing_time", 1.2)
        })
    elif event_type == "state_change":
        base_data.update({
            "old_state": kwargs.get("old_state", {}),
            "new_state": kwargs.get("new_state", MOCK_APPLICATION_STATE),
            "changes": kwargs.get("changes", ["operation.status"])
        })
    elif event_type == "error":
        base_data.update({
            "error_type": kwargs.get("error_type", "api_error"),
            "error_message": kwargs.get("error_message", "Mock error occurred"),
            "context": kwargs.get("context", {})
        })

    return base_data


def load_test_scenario(scenario_name: str) -> Dict[str, Any]:
    """Load a predefined test scenario."""
    scenarios = {
        "successful_chat": {
            "user_input": "Hello, how are you?",
            "expected_response": "I'm doing well, thank you for asking!",
            "model": "anthropic/claude-3-haiku",
            "conversation_id": "conv_test123"
        },
        "error_handling": {
            "user_input": "Test error scenario",
            "expected_error": "rate_limit_exceeded",
            "model": "anthropic/claude-3-haiku",
            "conversation_id": "conv_error123"
        },
        "streaming_response": {
            "user_input": "Tell me a story",
            "expected_chunks": MOCK_STREAMING_RESPONSE_CHUNKS,
            "model": "anthropic/claude-3-haiku",
            "conversation_id": "conv_stream123"
        },
        "state_management": {
            "initial_state": MOCK_APPLICATION_STATE,
            "operations": ["update_ui_settings", "add_conversation", "update_performance"],
            "expected_final_state": MOCK_APPLICATION_STATE.copy()
        }
    }

    return scenarios.get(scenario_name, {})


# Phase 5 Component Fixtures

# Chat Controller operation states
MOCK_OPERATION_DATA = {
    "id": "op_phase5_mock123",
    "state": "processing",
    "started_at": "2024-01-01T12:00:00.000000",
    "metadata": {
        "type": "chat_completion",
        "conversation_id": "conv_mock123",
        "model": "anthropic/claude-3-haiku",
        "input_length": 25
    }
}

MOCK_CONTROLLER_METRICS = {
    "total_operations": 15,
    "successful_operations": 14,
    "failed_operations": 1,
    "average_response_time": 1.2,
    "total_tokens_processed": 450,
    "current_operation": None,
    "operation_history_count": 15
}

# State Manager Phase 5 state
MOCK_PHASE5_APPLICATION_STATE = {
    "_metadata": {
        "created_at": "2024-01-01T12:00:00.000Z",
        "version": "1.0",
        "update_count": 8,
        "last_updated": "2024-01-01T12:10:00.000Z"
    },
    "conversations": {
        "conv_phase5_001": {
            "id": "conv_phase5_001",
            "title": "Phase 5 Integration Test",
            "created_at": "2024-01-01T12:00:00.000Z",
            "updated_at": "2024-01-01T12:05:00.000Z",
            "messages": [
                {
                    "role": "user",
                    "content": "Test Phase 5 chat functionality",
                    "timestamp": "2024-01-01T12:00:00.000Z",
                    "metadata": {"tokens": 6, "length": 32}
                },
                {
                    "role": "assistant",
                    "content": "Phase 5 integration test response",
                    "timestamp": "2024-01-01T12:01:00.000Z",
                    "metadata": {"tokens": 5, "length": 33}
                }
            ],
            "metadata": {
                "model": "anthropic/claude-3-haiku",
                "total_tokens": 11,
                "message_count": 2
            }
        }
    },
    "ui": {
        "current_view": "chat",
        "settings": {
            "theme": "dark",
            "font_size": "large"
        },
        "preferences": {
            "auto_save": True,
            "notifications": True,
            "streaming_enabled": True
        }
    },
    "operation": {
        "status": "idle",
        "current_operation": None,
        "last_operation": {
            "id": "op_phase5_complete",
            "type": "chat_completion",
            "success": True,
            "timestamp": "2024-01-01T12:10:00.000Z"
        }
    },
    "configuration": {
        "api_key_configured": True,
        "default_model": "anthropic/claude-3-haiku",
        "max_tokens": 4000,
        "temperature": 0.7,
        "streaming_supported": True
    },
    "performance": {
        "total_operations": 25,
        "successful_operations": 24,
        "failed_operations": 1,
        "average_response_time": 1.1,
        "total_tokens_processed": 750,
        "error_count": 1
    }
}

# Event system fixtures for Phase 5
MOCK_PHASE5_EVENTS = [
    {
        "id": "evt_phase5_user_input",
        "type": "user_input",
        "data": {
            "input": "Test Phase 5 user input",
            "conversation_id": "conv_phase5_001",
            "timestamp": "2024-01-01T12:00:00.000Z"
        },
        "priority": 2,
        "source": "chat_controller",
        "correlation_id": "corr_phase5_001",
        "timestamp": "2024-01-01T12:00:00.000000"
    },
    {
        "id": "evt_phase5_api_response",
        "type": "api_response",
        "data": {
            "response": MOCK_CHAT_COMPLETION_RESPONSE,
            "request_id": "req_phase5_001",
            "processing_time": 1.2,
            "tokens_used": 25
        },
        "priority": 2,
        "source": "api_client_manager",
        "correlation_id": "corr_phase5_001",
        "timestamp": "2024-01-01T12:01:00.000000"
    },
    {
        "id": "evt_phase5_state_change",
        "type": "state_change",
        "data": {
            "old_state": {"operation": {"status": "idle"}},
            "new_state": {"operation": {"status": "processing"}},
            "changes": ["operation.status"]
        },
        "priority": 3,
        "source": "state_manager",
        "correlation_id": "corr_phase5_002",
        "timestamp": "2024-01-01T12:02:00.000000"
    },
    {
        "id": "evt_phase5_error",
        "type": "error",
        "data": {
            "error_type": "api_error",
            "error_message": "Phase 5 test error",
            "context": {"operation_id": "op_phase5_error"},
            "retry_count": 2
        },
        "priority": 4,
        "source": "error_handler",
        "correlation_id": "corr_phase5_error",
        "timestamp": "2024-01-01T12:03:00.000000"
    }
]

# Event bus statistics for Phase 5
MOCK_EVENT_BUS_STATS = {
    "events_published": 25,
    "events_processed": 24,
    "events_failed": 1,
    "processing_time_avg": 0.05,
    "queue_size": 0,
    "subscriber_count": 3,
    "async_subscriber_count": 2
}

# Phase 5 integration test scenarios
PHASE5_TEST_SCENARIOS = {
    "successful_chat_flow": {
        "description": "Complete successful chat interaction",
        "user_input": "Hello, test Phase 5 functionality",
        "expected_response": "Phase 5 test response",
        "model": "anthropic/claude-3-haiku",
        "conversation_id": "conv_phase5_flow",
        "expected_events": ["user_input", "api_response", "state_change"],
        "expected_final_state": "idle"
    },
    "streaming_response_flow": {
        "description": "Streaming response handling",
        "user_input": "Tell me a streaming story",
        "expected_chunks": MOCK_STREAMING_RESPONSE_CHUNKS,
        "model": "anthropic/claude-3-haiku",
        "conversation_id": "conv_phase5_stream",
        "expected_events": ["user_input", "api_response"],
        "streaming_enabled": True
    },
    "error_recovery_flow": {
        "description": "Error handling and recovery",
        "user_input": "Trigger error scenario",
        "expected_error": "api_connection_failed",
        "model": "anthropic/claude-3-haiku",
        "conversation_id": "conv_phase5_error",
        "expected_events": ["user_input", "error", "state_change"],
        "expected_final_state": "error"
    },
    "concurrent_operation_prevention": {
        "description": "Prevent concurrent operations",
        "user_input": "Concurrent test",
        "model": "anthropic/claude-3-haiku",
        "conversation_id": "conv_phase5_concurrent",
        "expected_error": "operation_in_progress",
        "setup_operation": "processing"
    },
    "state_persistence_flow": {
        "description": "State persistence and restoration",
        "operations": ["update_state", "persist", "restore"],
        "expected_state_changes": 3,
        "conversation_id": "conv_phase5_persist"
    }
}


def create_mock_phase5_operation(operation_type: str = "chat_completion",
                                state: str = "processing") -> Dict[str, Any]:
    """Create a mock Phase 5 operation data."""
    return {
        "id": f"op_phase5_{operation_type}_{datetime.now().strftime('%H%M%S')}",
        "state": state,
        "started_at": datetime.now().isoformat(),
        "metadata": {
            "type": operation_type,
            "conversation_id": "conv_phase5_mock",
            "model": "anthropic/claude-3-haiku",
            "input_length": 20
        }
    }


def create_mock_phase5_event(event_type: str, **kwargs) -> Dict[str, Any]:
    """Create a mock Phase 5 event."""
    base_event = {
        "id": f"evt_phase5_{event_type}_{datetime.now().strftime('%H%M%S')}",
        "type": event_type,
        "priority": 2,
        "source": kwargs.get("source", "phase5_component"),
        "correlation_id": f"corr_phase5_{datetime.now().strftime('%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }

    if event_type == "user_input":
        base_event["data"] = {
            "input": kwargs.get("input", "Phase 5 test input"),
            "conversation_id": kwargs.get("conversation_id", "conv_phase5_test")
        }
    elif event_type == "api_response":
        base_event["data"] = {
            "response": kwargs.get("response", MOCK_CHAT_COMPLETION_RESPONSE),
            "request_id": kwargs.get("request_id", "req_phase5_test"),
            "processing_time": kwargs.get("processing_time", 1.0)
        }
    elif event_type == "state_change":
        base_event["data"] = {
            "old_state": kwargs.get("old_state", {}),
            "new_state": kwargs.get("new_state", MOCK_PHASE5_APPLICATION_STATE),
            "changes": kwargs.get("changes", ["test.change"])
        }
    elif event_type == "error":
        base_event["data"] = {
            "error_type": kwargs.get("error_type", "phase5_error"),
            "error_message": kwargs.get("error_message", "Phase 5 test error"),
            "context": kwargs.get("context", {})
        }

    return base_event


def generate_bulk_test_data(count: int = 10) -> List[Dict[str, Any]]:
    """Generate bulk test data for performance testing."""
    test_data = []

    for i in range(count):
        conversation = create_mock_conversation(f"conv_bulk_{i:03d}", message_count=5)
        test_data.append({
            "conversation": conversation,
            "performance_metrics": {
                "response_time": MOCK_PERFORMANCE_METRICS["response_times"][i % len(MOCK_PERFORMANCE_METRICS["response_times"])],
                "tokens_used": MOCK_PERFORMANCE_METRICS["token_counts"][i % len(MOCK_PERFORMANCE_METRICS["token_counts"])],
                "success": bool(MOCK_PERFORMANCE_METRICS["success_rates"][i % len(MOCK_PERFORMANCE_METRICS["success_rates"])])
            },
            "metadata": {
                "test_run": i,
                "timestamp": datetime.now().isoformat()
            }
        })

    return test_data