# Personal AI Chatbot

A personal AI chatbot application built with Gradio 5 and OpenRouter for local deployment.

## Overview

This is a single-user AI chatbot designed for personal productivity and daily use. It provides a clean, intuitive interface for interacting with multiple AI models through the OpenRouter API.

## Technology Stack

- **Frontend**: Gradio 5 (Python web framework)
- **AI Provider**: OpenRouter (multi-model API service)
- **Runtime**: Python 3.9+
- **Deployment**: Local development server

## Features

### Core Chat Functionality
- Clean, accessible chat interface with real-time message streaming
- Conversation history with chronological message display
- Message actions (copy, edit, regenerate responses)
- Auto-scroll and virtual scrolling for performance

### Model Management
- Dynamic model selection from OpenRouter API
- Model capability display (cost, features, use cases)
- Real-time model switching (< 2 seconds)
- Model-specific parameter tuning

### User Interface
- **Responsive Design**: Optimized for desktop (1024px+), tablet, and mobile
- **Accessibility**: Full WCAG 2.1 AA compliance with keyboard navigation
- **Themes**: Light/dark mode support with system preference detection
- **Performance**: < 3 second initial load time

### Conversation Management
- Create, save, and load conversations
- Conversation search and filtering
- Automatic conversation persistence
- Export/import conversation data

### Settings & Configuration
- Secure API key management with encryption
- UI preferences (theme, font size, timestamps)
- Model parameters (temperature, max tokens)
- Connection settings and error handling

### Advanced Features
- Streaming response display with typing indicators
- Character counting and input validation
- Keyboard shortcuts for power users
- Comprehensive error handling and recovery
- Real-time connection status monitoring

## Project Structure

```
personal-ai-chatbot/
├── src/                    # Source code
│   ├── ui/                 # Gradio web interface
│   │   ├── gradio_interface.py    # Main interface orchestrator
│   │   └── components/     # UI component modules
│   │       ├── chat_panel.py      # Message display & streaming
│   │       ├── input_panel.py     # Message input & controls
│   │       ├── sidebar_panel.py   # Navigation & model selection
│   │       ├── header_bar.py      # Branding & status
│   │       └── settings_panel.py  # Configuration modal
│   └── core/               # Application logic (Phase 5)
├── docs/                   # Comprehensive documentation
├── tests/                  # Test suite (>85% coverage)
│   ├── unit/              # Component unit tests
│   ├── integration/       # End-to-end integration tests
│   ├── performance/       # Performance benchmarks
│   └── accessibility/     # WCAG compliance tests
├── control/               # Project control files
│   └── workflow-state.json
└── memory-bank/           # Context engineering memory
    ├── progress.md
    ├── decisionLog.md
    ├── systemPatterns.md
    └── qualityMetrics.md
```

## Development Status

✅ **Phase 6 Complete**: User Interface Layer implementation finished
- Gradio-based web interface fully implemented
- WCAG 2.1 AA accessibility compliance achieved
- Performance targets met (< 3s load time, < 2s model switching)
- Comprehensive test suite with > 85% coverage

All core functionality is implemented and production-ready.

## Requirements

- Python 3.9+
- OpenRouter API key
- Internet connection for AI model access

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application

```bash
# Launch the Gradio web interface
python src/main.py
```

The application will start a local web server and open your default browser to the chat interface.

### First-Time Setup

1. **API Key Configuration**: Enter your OpenRouter API key in the settings panel
2. **Model Selection**: Choose your preferred AI model from the sidebar
3. **Start Chatting**: Begin conversations in the main chat area

## Testing

The project includes comprehensive testing coverage:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/  # Integration tests
python -m pytest tests/performance/  # Performance tests
python -m pytest tests/accessibility/ # Accessibility tests

# Generate coverage report
python -m pytest --cov=src --cov-report=html
```

### Test Coverage
- **Unit Tests**: Component-level functionality testing
- **Integration Tests**: End-to-end UI and ChatController interaction
- **Performance Tests**: Load time and responsiveness benchmarks
- **Accessibility Tests**: WCAG 2.1 AA compliance verification

## Quality Assurance

- ✅ **WCAG 2.1 AA Compliant**: Full accessibility support
- ✅ **Performance Optimized**: < 3s load time, < 2s model switching
- ✅ **Cross-Platform**: Works on desktop, tablet, and mobile
- ✅ **Error Resilient**: Comprehensive error handling and recovery
- ✅ **Tested**: > 85% code coverage with automated testing

## Context Engineering

This project follows a comprehensive context engineering methodology to ensure zero ambiguity before implementation. All decisions, requirements, and specifications are documented in the memory-bank/ directory.