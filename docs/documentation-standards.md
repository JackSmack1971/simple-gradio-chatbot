# Documentation Standards - Personal AI Chatbot

## Overview

This document establishes documentation standards and requirements for the Personal AI Chatbot project. As a personal productivity tool that may attract future contributors, documentation balances clarity with practicality.

## Documentation Hierarchy

```
Project Documentation
├── README.md (Project overview, setup, usage)
├── docs/
│   ├── architecture.md (System design)
│   ├── components.md (Component specifications)
│   ├── coding-standards.md (Development standards)
│   ├── testing-standards.md (Testing guidelines)
│   ├── documentation-standards.md (This file)
│   ├── user-journeys.md (User experience flows)
│   ├── acceptance-criteria.md (Requirements validation)
│   ├── deployment.md (Installation and deployment)
│   └── api-reference.md (Generated API docs)
├── Code Documentation
│   ├── Docstrings (All public functions/classes)
│   ├── Inline comments (Complex logic)
│   └── Type hints (All function parameters/returns)
└── Inline Documentation
    ├── TODO/FIXME comments
    ├── Bug references
    └── Implementation notes
```

## README.md Standards

### Required Sections

Every README.md must include:

```markdown
# Project Name

Brief description of what the project does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Quick Start

### Prerequisites
- Python 3.9+
- Required dependencies

### Installation
```bash
pip install -r requirements.txt
```

### Usage
```bash
python src/main.py
```

## Configuration

Environment variables and configuration options.

## Development

How to set up development environment.

## Testing

How to run tests.

## Contributing

Guidelines for contributors.

## License

Project license information.
```

### README Maintenance

- Keep installation instructions current
- Update feature list as functionality evolves
- Include troubleshooting section for common issues
- Add badges for build status, coverage, version

## Code Documentation Standards

### Docstring Format

Use Google-style docstrings for all public functions, classes, and modules:

```python
def send_message(user_input: str, model: str) -> Message:
    """Send a user message to the AI model and return the response.

    Processes the user input through message validation, API communication,
    and response formatting. Handles errors gracefully with user feedback.

    Args:
        user_input: The user's message content (max 4000 characters)
        model: The AI model identifier (e.g., 'anthropic/claude-3-haiku')

    Returns:
        Message object containing the AI response

    Raises:
        APIError: If the API request fails after retries
        ValidationError: If the input message is invalid

    Example:
        >>> response = send_message("Hello world", "claude-3-haiku")
        >>> print(response.content)
        "Hello! How can I help you today?"
    """
    pass
```

### Class Documentation

```python
class ChatController:
    """Manages chat interactions and coordinates between UI and backend.

    The ChatController orchestrates the complete message flow from user input
    through AI processing to response display. It maintains conversation state
    and handles error scenarios.

    Attributes:
        message_processor: Handles message validation and formatting
        conversation_manager: Manages conversation persistence
        api_client: Handles external API communications

    Example:
        controller = ChatController(
            message_processor=MessageProcessor(),
            conversation_manager=ConversationManager(),
            api_client=APIClient()
        )
    """
```

### Module Documentation

Each module must start with a module docstring:

```python
"""Chat controller for managing user interactions.

This module provides the ChatController class which orchestrates
chat conversations between users and AI models. It handles message
processing, state management, and error handling.
"""
```

## Inline Comments Standards

### When to Comment

- Complex business logic that isn't self-explanatory
- Non-obvious algorithmic decisions
- Integration points with external systems
- Workarounds for known issues
- TODO items and future improvements

```python
def calculate_token_estimate(content: str) -> int:
    """Estimate token count for message content."""
    # Use character-based estimation as fallback
    # TODO: Replace with proper tokenizer when available
    char_count = len(content)

    # Rough estimation: 1 token ≈ 4 characters for English text
    # This is approximate and may vary by model
    estimated_tokens = char_count // 4

    return max(estimated_tokens, 1)  # Minimum 1 token
```

### Comment Style

```python
# Good: descriptive comments that explain why, not what
total_tokens = sum(msg.tokens for msg in messages if msg.tokens)
# Handle messages without token counts (legacy data)
total_tokens += len([msg for msg in messages if not msg.tokens])

# Avoid: redundant comments
total_tokens = 0  # Initialize total tokens variable
for msg in messages:  # Loop through messages
    total_tokens += msg.tokens  # Add message tokens
```

## Type Hints Standards

### Function Signatures

All functions must include type hints:

```python
from typing import List, Optional, Dict, Any, Tuple

def process_conversation(
    conversation_id: str,
    messages: List[Message],
    model: str,
    options: Optional[Dict[str, Any]] = None
) -> Tuple[Conversation, List[Message]]:
    pass
```

### Generic Types

Use appropriate generic types:

```python
from typing import Union, Literal, Callable

def validate_input(value: Union[str, int], validator: Callable[[Any], bool]) -> bool:
    pass

def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None:
    pass
```

### Custom Types

Define custom types for complex structures:

```python
from typing import TypedDict

class APIResponse(TypedDict):
    content: str
    tokens: int
    model: str
    finish_reason: str

class ModelConfig(TypedDict, total=False):
    temperature: float
    max_tokens: int
    top_p: float
```

## API Documentation

### REST API Documentation

For any REST endpoints, use OpenAPI/Swagger format:

```yaml
openapi: 3.0.0
info:
  title: Personal AI Chatbot API
  version: 1.0.0

paths:
  /api/chat:
    post:
      summary: Send a chat message
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                model:
                  type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  response:
                    type: string
                  tokens:
                    type: integer
```

### Auto-generated API Docs

Use tools to generate API documentation:

```python
# docs/generate_api_docs.py
"""Generate API documentation from code."""

import inspect
from pathlib import Path
from typing import get_type_hints

def generate_api_docs():
    """Generate Markdown API documentation."""
    # Implementation to scan modules and generate docs
    pass
```

## Error Documentation

### Error Messages

Error messages should be:
- User-friendly and actionable
- Consistent in format and tone
- Include context when helpful

```python
# Good error messages
class APIError(Exception):
    """Base API error with user-friendly messaging."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.formatted_message)

    @property
    def formatted_message(self) -> str:
        """Format error message for user display."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message

# Usage
raise APIError(
    "Failed to connect to AI service",
    "Check your internet connection and API key"
)
```

### Exception Hierarchy

Define clear exception hierarchy:

```python
class ChatbotError(Exception):
    """Base exception for all chatbot errors."""
    pass

class ValidationError(ChatbotError):
    """Input validation errors."""
    pass

class APIError(ChatbotError):
    """External API communication errors."""
    pass

class StorageError(ChatbotError):
    """Data persistence errors."""
    pass
```

## Configuration Documentation

### Environment Variables

Document all environment variables:

```python
# config.py
"""
Environment Variables:

PERSONAL_CHATBOT_API_KEY: OpenRouter API key (required)
    Get from: https://openrouter.ai/keys

PERSONAL_CHATBOT_DEFAULT_MODEL: Default AI model to use
    Default: anthropic/claude-3-haiku
    Options: See OpenRouter model list

PERSONAL_CHATBOT_MAX_TOKENS: Maximum tokens per response
    Default: 4000
    Range: 100-8000

PERSONAL_CHATBOT_DEBUG: Enable debug logging
    Default: false
    Values: true, false
"""

import os

API_KEY = os.getenv("PERSONAL_CHATBOT_API_KEY")
DEFAULT_MODEL = os.getenv("PERSONAL_CHATBOT_DEFAULT_MODEL", "anthropic/claude-3-haiku")
MAX_TOKENS = int(os.getenv("PERSONAL_CHATBOT_MAX_TOKENS", "4000"))
DEBUG = os.getenv("PERSONAL_CHATBOT_DEBUG", "false").lower() == "true"
```

### Configuration Files

Document configuration file formats:

```json
// config/default.json
{
  "api": {
    "timeout": 30,
    "max_retries": 3,
    "rate_limit_buffer": 0.1
  },
  "ui": {
    "theme": "default",
    "max_conversation_history": 100,
    "auto_save_interval": 30
  },
  "storage": {
    "backup_enabled": true,
    "max_backup_age_days": 30,
    "compression_level": 6
  }
}
```

## Development Documentation

### Development Setup

Document development environment setup:

```bash
# Clone repository
git clone https://github.com/username/personal-ai-chatbot.git
cd personal-ai-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run initial tests
pytest
```

### Contributing Guidelines

```markdown
# Contributing to Personal AI Chatbot

## Code Style
- Follow PEP 8 with Black formatting
- Use type hints for all function signatures
- Write comprehensive docstrings

## Testing
- Write tests for new features
- Maintain >80% test coverage
- Run tests before committing

## Documentation
- Update README for new features
- Document API changes
- Keep docstrings current

## Commit Messages
```
feat: add conversation export functionality
fix: handle API timeout errors gracefully
docs: update installation instructions
refactor: simplify message validation logic
```
```

## User Documentation

### User Guides

Create user-focused documentation:

```markdown
# User Guide - Personal AI Chatbot

## Getting Started

1. Install the application
2. Set up your API key
3. Start chatting with AI models

## Features

### Chat Interface
- Type messages in the input box
- Select different AI models
- View conversation history

### Settings
- Configure API key
- Choose default model
- Adjust response parameters

## Troubleshooting

### Common Issues

**"API key not configured"**
- Go to Settings panel
- Enter your OpenRouter API key
- Save settings

**"Connection timeout"**
- Check internet connection
- Try a different model
- Wait a few minutes and retry
```

## Documentation Maintenance

### Documentation Reviews

- Review documentation during code reviews
- Update docs when APIs change
- Validate examples in documentation

### Automated Checks

Use automated tools for documentation quality:

```yaml
# .github/workflows/docs.yml
name: Documentation
on: [push, pull_request]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check docstrings
        run: |
          python -m pydocstyle src/
      - name: Build docs
        run: |
          # Generate API docs if using Sphinx
          make docs
```

### Documentation Tools

Recommended tools:

```txt
# requirements-docs.txt
sphinx>=5.0.0          # Documentation generator
sphinx-rtd-theme>=1.2.0  # Read the Docs theme
myst-parser>=0.18.0    # Markdown support for Sphinx
pydocstyle>=6.3.0      # Docstring style checker
```

## Documentation Standards Checklist

### Code Documentation
- [ ] All public functions have docstrings
- [ ] All classes have docstrings
- [ ] Complex logic has explanatory comments
- [ ] Type hints on all function signatures
- [ ] Custom exceptions documented

### Project Documentation
- [ ] README.md is current and complete
- [ ] Installation instructions work
- [ ] Configuration options documented
- [ ] API endpoints documented (if any)
- [ ] Troubleshooting guide exists

### User Documentation
- [ ] User guide covers main features
- [ ] Setup instructions are clear
- [ ] Common issues documented
- [ ] Screenshots included where helpful

These standards ensure the codebase remains maintainable and accessible to future contributors while keeping documentation overhead appropriate for a personal project.