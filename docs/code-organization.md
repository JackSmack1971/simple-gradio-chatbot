# Code Organization Standards - Personal AI Chatbot

## Overview

This document defines the file structure, module organization, and package layout standards for the Personal AI Chatbot project. The organization follows a layered architecture with clear separation of concerns.

## Project Structure

```
personal-ai-chatbot/
├── src/                          # Main source code
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Application entry point
│   ├── ui/                      # User Interface Layer
│   │   ├── __init__.py
│   │   ├── gradio_interface.py  # Main Gradio application
│   │   ├── components/          # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── chat_panel.py
│   │   │   ├── settings_panel.py
│   │   │   └── model_selector.py
│   │   └── themes/              # UI themes and styles
│   │       └── __init__.py
│   ├── core/                    # Application Logic Layer
│   │   ├── __init__.py
│   │   ├── controllers/         # Business logic controllers
│   │   │   ├── __init__.py
│   │   │   ├── chat_controller.py
│   │   │   └── state_manager.py
│   │   ├── processors/          # Data processors
│   │   │   ├── __init__.py
│   │   │   └── message_processor.py
│   │   └── managers/            # Resource managers
│   │       ├── __init__.py
│   │       ├── conversation_manager.py
│   │       └── api_client.py
│   ├── data/                    # Data Persistence Layer
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   ├── storage/             # Storage implementations
│   │   │   ├── __init__.py
│   │   │   ├── conversation_storage.py
│   │   │   └── backup_manager.py
│   │   └── models/              # Data models
│   │       ├── __init__.py
│   │       ├── message.py
│   │       ├── conversation.py
│   │       └── types.py
│   ├── external/                # External Integration Layer
│   │   ├── __init__.py
│   │   ├── openrouter/          # OpenRouter API client
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   └── rate_limiter.py
│   │   └── utils/               # External utilities
│   │       ├── __init__.py
│   │       └── validators.py
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       ├── logging.py
│       ├── exceptions.py
│       └── helpers.py
├── tests/                       # Test files
│   ├── __init__.py
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data and fixtures
├── docs/                        # Documentation
├── scripts/                     # Utility scripts
│   ├── setup.py
│   └── dev_tools.py
├── config/                      # Configuration files
│   ├── default.json
│   └── development.json
└── data/                        # Application data directory
    ├── conversations/
    ├── backups/
    └── cache/
```

## Module Organization Principles

### 1. Layer Separation

- **UI Layer** (`src/ui/`): Handles all user interface concerns
- **Core Layer** (`src/core/`): Contains business logic and application flow
- **Data Layer** (`src/data/`): Manages data persistence and models
- **External Layer** (`src/external/`): Handles external API integrations
- **Utils** (`src/utils/`): Shared utilities and helpers

### 2. Import Hierarchy

Imports should follow this hierarchy:
1. Standard library
2. Third-party packages
3. Local modules (same layer)
4. Parent layer modules
5. Sibling layer modules

```python
# src/core/controllers/chat_controller.py
import asyncio
from typing import List, Optional

import gradio as gr

from ...data.models import Message, Conversation
from ...data.config import ConfigManager
from ..processors import MessageProcessor
from .state_manager import StateManager
```

### 3. Circular Import Prevention

- Use dependency injection to break circular dependencies
- Import modules at function level when necessary
- Use protocols/interfaces for loose coupling

```python
# Good: dependency injection
class ChatController:
    def __init__(self,
                 message_processor: MessageProcessor,
                 conversation_manager: ConversationManager):
        self.message_processor = message_processor
        self.conversation_manager = conversation_manager

# Avoid: direct instantiation that creates circular imports
class ChatController:
    def __init__(self):
        self.message_processor = MessageProcessor()  # ❌ Creates tight coupling
```

## File Naming Conventions

### Python Files
- Use `snake_case` for all Python files
- Module files: `module_name.py`
- Package files: `__init__.py`
- Test files: `test_module_name.py`

### Directory Names
- Use `snake_case` for directories
- Group related functionality: `controllers/`, `processors/`, `managers/`
- Use plural for collections: `conversations/`, `backups/`

### Configuration Files
- JSON: `filename.json`
- YAML: `filename.yaml`
- Environment: `.env`
- Python config: `config.py`

## Package Initialization

### `__init__.py` Files

Each package should have an `__init__.py` that:
- Defines the public API of the package
- Imports commonly used classes/functions
- Provides version information
- Includes package-level documentation

```python
# src/ui/__init__.py
"""User Interface layer for Personal AI Chatbot."""

from .gradio_interface import GradioInterface
from .components import ChatPanel, SettingsPanel

__version__ = "1.0.0"
__all__ = ["GradioInterface", "ChatPanel", "SettingsPanel"]
```

### Main Package

```python
# src/__init__.py
"""Personal AI Chatbot - A personal AI assistant with web interface."""

from .main import main
from .ui.gradio_interface import GradioInterface
from .core.controllers.chat_controller import ChatController

__version__ = "1.0.0"
__all__ = ["main", "GradioInterface", "ChatController"]
```

## Component Organization

### Controllers
Located in `src/core/controllers/`:
- Handle business logic and orchestrate operations
- Coordinate between different layers
- Manage application state

### Processors
Located in `src/core/processors/`:
- Handle data transformation and validation
- Process inputs and outputs
- Implement business rules

### Managers
Located in `src/core/managers/`:
- Manage resources and external services
- Handle lifecycle of complex objects
- Coordinate related operations

### Storage
Located in `src/data/storage/`:
- Implement data persistence interfaces
- Handle file I/O operations
- Provide data integrity guarantees

## Data Organization

### Models
Located in `src/data/models/`:
- Define data structures using dataclasses
- Include type hints and validation
- Keep business logic minimal

```python
# src/data/models/message.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Message:
    id: str
    role: str
    content: str
    timestamp: datetime
    model: Optional[str] = None
    tokens: Optional[int] = None
```

### Configuration
Located in `src/data/config.py`:
- Central configuration management
- Environment variable handling
- Configuration validation

## External Integrations

### API Clients
Located in `src/external/`:
- One subdirectory per external service
- Separate client and utility modules
- Include rate limiting and error handling

```python
# src/external/openrouter/client.py
class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = requests.Session()
```

## Testing Organization

### Test Structure
```
tests/
├── unit/                    # Unit tests (one file per module)
│   ├── test_chat_controller.py
│   ├── test_message_processor.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_full_chat_flow.py
│   └── test_api_integration.py
├── fixtures/                # Test data and mocks
│   ├── sample_messages.json
│   └── mock_responses.py
└── conftest.py             # Pytest configuration
```

### Test Naming
- Unit tests: `test_function_name.py` or `test_class_name.py`
- Integration tests: `test_feature_integration.py`
- Fixtures: `fixture_name.py`

## Utility Scripts

### Development Tools
Located in `scripts/`:
- Setup and installation scripts
- Development utilities
- Deployment helpers

```python
# scripts/dev_tools.py
#!/usr/bin/env python3
"""Development utilities for Personal AI Chatbot."""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run the test suite."""
    return subprocess.run([sys.executable, "-m", "pytest"], cwd=Path(__file__).parent.parent)

def format_code():
    """Format code with Black."""
    return subprocess.run([sys.executable, "-m", "black", "src/"], cwd=Path(__file__).parent.parent)
```

## Configuration Files

### Application Config
Located in `config/`:
- Environment-specific settings
- Default configurations
- Feature flags

```json
// config/default.json
{
  "api": {
    "timeout": 30,
    "max_retries": 3
  },
  "ui": {
    "theme": "default",
    "max_messages": 100
  },
  "storage": {
    "backup_enabled": true,
    "max_conversation_age_days": 365
  }
}
```

### Environment Variables
- Use `.env` files for local development
- Prefix with project name to avoid conflicts
- Document required variables

```bash
# .env
PERSONAL_CHATBOT_API_KEY=sk-...
PERSONAL_CHATBOT_DEBUG=true
PERSONAL_CHATBOT_LOG_LEVEL=INFO
```

## Data Directories

### Application Data
Located in `data/` (created at runtime):
- User conversations
- Configuration files
- Cache and temporary files
- Backup archives

Structure created by application:
```
data/
├── conversations/           # JSON conversation files
│   ├── conv_001.json
│   └── conv_002.json
├── config/                  # User configuration
│   └── user_settings.json
├── backups/                 # Backup archives
│   ├── backup_20241201.zip
│   └── backup_20241202.zip
└── cache/                   # Temporary cache files
    └── model_cache.json
```

## Import Best Practices

### Absolute Imports
Prefer absolute imports for clarity:

```python
# Good
from src.core.controllers.chat_controller import ChatController
from src.data.models.message import Message

# Avoid relative imports for complex hierarchies
from ...core.controllers.chat_controller import ChatController  # ❌
```

### Import Aliases
Use aliases for long module names:

```python
# Good
import src.external.openrouter.client as openrouter_client

# Avoid
import src.external.openrouter.client  # ❌ Too long
```

### Lazy Imports
Use lazy imports for optional dependencies:

```python
# Good
def get_optional_module():
    try:
        import optional_module
        return optional_module
    except ImportError:
        return None
```

## File Size Guidelines

- Python modules: < 500 lines
- Test files: < 300 lines
- Configuration files: < 100 lines
- Documentation files: < 1000 lines

Large files should be split into logical modules with clear responsibilities.

## Directory Depth Limits

- Maximum directory depth: 4 levels
- Keep related files within 2-3 levels of the package root
- Use `__init__.py` files to create clean import paths

This organization provides a scalable structure that supports the layered architecture while maintaining clarity and ease of navigation for a single developer.