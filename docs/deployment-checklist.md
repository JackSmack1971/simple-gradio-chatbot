# Deployment Checklist - Personal AI Chatbot

## Overview

This deployment checklist ensures systematic verification of all deployment aspects, from environment preparation through post-deployment monitoring. Each checklist item includes specific validation steps and success criteria.

## 1. Pre-Deployment Preparation

### 1.1 Environment Prerequisites

**System Requirements Verification**:
- [ ] **Python Version Check**:
  ```bash
  python --version  # Must be 3.9 or higher
  python -c "import sys; print(f'Python {sys.version}'); assert sys.version_info >= (3, 9)"
  ```
  *Expected: Python 3.9.x or higher reported*

- [ ] **Operating System Compatibility**:
  ```bash
  # Windows
  systeminfo | findstr /B /C:"OS Name" /C:"OS Version"

  # macOS
  sw_vers

  # Linux
  lsb_release -a
  ```
  *Expected: Supported OS version (Windows 10+, macOS 11+, Ubuntu 20.04+)*

- [ ] **System Resources Available**:
  ```bash
  # Check available RAM
  systeminfo | find "Total Physical Memory"  # Windows
  vm_stat | grep "Pages free"                # macOS
  free -h                                    # Linux

  # Check available disk space
  dir C:\ | find "bytes free"                # Windows
  df -h /                                    # macOS/Linux
  ```
  *Expected: Minimum 4GB RAM, 1GB free disk space*

### 1.2 Development Environment Setup

**Virtual Environment Creation**:
- [ ] **Virtual Environment Created**:
  ```bash
  python -m venv venv
  # Windows: python -m venv venv
  # macOS/Linux: python3 -m venv venv
  ```
  *Expected: venv directory created without errors*

- [ ] **Virtual Environment Activated**:
  ```bash
  # Windows
  venv\Scripts\activate

  # macOS/Linux
  source venv/bin/activate
  ```
  *Expected: Command prompt shows (venv) prefix*

- [ ] **Dependencies Installed**:
  ```bash
  pip install -r requirements.txt
  pip list | grep -E "(gradio|cryptography|requests|openai)"
  ```
  *Expected: All packages installed, versions match requirements.txt*

**Project Structure Verification**:
- [ ] **Directory Structure Complete**:
  ```bash
  ls -la  # Should show src/, data/, docs/, tests/, etc.
  find . -name "*.py" | head -10  # Should find Python files
  ```
  *Expected: All directories from architecture present*

- [ ] **Data Directories Created**:
  ```bash
  mkdir -p data/{config,conversations/active,conversations/archived,backups,logs}
  ls -la data/
  ```
  *Expected: All subdirectories created with correct permissions*

### 1.3 Configuration Setup

**Environment Configuration**:
- [ ] **Environment File Created**:
  ```bash
  cp .env.example .env
  ls -la .env
  ```
  *Expected: .env file exists and is readable*

- [ ] **API Key Configured**:
  ```bash
  # Edit .env file to add OpenRouter API key
  nano .env  # or notepad .env on Windows
  ```
  *Expected: OPENROUTER_API_KEY set with valid key*

- [ ] **Configuration Validation**:
  ```bash
  python -c "
  import os
  from dotenv import load_dotenv
  load_dotenv()
  key = os.getenv('OPENROUTER_API_KEY')
  print(f'API Key configured: {bool(key and key.startswith(\"sk-or-v1-\"))}')
  "
  ```
  *Expected: API Key configured: True*

## 2. Component Implementation Verification

### 2.1 Core Component Imports

**Foundation Components**:
- [ ] **Logger Import Test**:
  ```bash
  python -c "from src.utils.logger import logger; logger.info('Logger test'); print('Logger OK')"
  ```
  *Expected: Logger OK message, no import errors*

- [ ] **Validators Import Test**:
  ```bash
  python -c "from src.utils.validators import validate_api_key; print('Validators OK')"
  ```
  *Expected: Validators OK message*

**Data Layer Components**:
- [ ] **ConfigManager Import Test**:
  ```bash
  python -c "
  from src.storage.config_manager import ConfigManager
  cm = ConfigManager()
  print('ConfigManager OK')
  "
  ```
  *Expected: ConfigManager OK message*

- [ ] **ConversationStorage Import Test**:
  ```bash
  python -c "
  from src.storage.conversation_storage import ConversationStorage
  cs = ConversationStorage()
  print('ConversationStorage OK')
  "
  ```
  *Expected: ConversationStorage OK message*

**Core Logic Components**:
- [ ] **MessageProcessor Import Test**:
  ```bash
  python -c "
  from src.core.message_processor import MessageProcessor
  mp = MessageProcessor()
  print('MessageProcessor OK')
  "
  ```
  *Expected: MessageProcessor OK message*

- [ ] **APIClient Import Test**:
  ```bash
  python -c "
  from src.core.api_client import APIClient
  from src.storage.config_manager import ConfigManager
  cm = ConfigManager()
  ac = APIClient(cm)
  print('APIClient OK')
  "
  ```
  *Expected: APIClient OK message*

- [ ] **ConversationManager Import Test**:
  ```bash
  python -c "
  from src.core.conversation_manager import ConversationManager
  from src.storage.conversation_storage import ConversationStorage
  cs = ConversationStorage()
  cm = ConversationManager(cs)
  print('ConversationManager OK')
  "
  ```
  *Expected: ConversationManager OK message*

### 2.2 Component Integration Tests

**Basic Component Wiring**:
- [ ] **Configuration Integration**:
  ```bash
  python -c "
  from src.storage.config_manager import ConfigManager
  cm = ConfigManager()
  cm.set_setting('test.deployment', 'success')
  value = cm.get_setting('test.deployment')
  print(f'Config integration: {value == \"success\"}')
  "
  ```
  *Expected: Config integration: True*

- [ ] **Storage Integration**:
  ```bash
  python -c "
  from src.storage.conversation_storage import ConversationStorage
  from src.core.conversation_manager import ConversationManager
  cs = ConversationStorage()
  cm = ConversationManager(cs)
  conv_id = cm.create_conversation('Deployment Test')
  print(f'Storage integration: {bool(conv_id)}')
  "
  ```
  *Expected: Storage integration: True*

**API Integration Test**:
- [ ] **API Connectivity Test**:
  ```bash
  python -c "
  import asyncio
  from src.core.api_client import APIClient
  from src.storage.config_manager import ConfigManager

  async def test_api():
      cm = ConfigManager()
      ac = APIClient(cm)
      try:
          models = ac.get_available_models()
          print(f'API connectivity: {len(models) > 0}')
      except Exception as e:
          print(f'API connectivity: False (expected if no key)')
      finally:
          await ac.close()

  asyncio.run(test_api())
  "
  ```
  *Expected: API connectivity: True (or False if no valid API key)*

## 3. Application Startup Verification

### 3.1 Basic Application Launch

**Application Entry Point**:
- [ ] **Main Application Import**:
  ```bash
  python -c "from src.app import main; print('Main app import OK')"
  ```
  *Expected: Main app import OK*

- [ ] **Application Startup Test**:
  ```bash
  timeout 10 python src/app.py &
  sleep 3
  jobs  # Check if process is running
  curl -s http://localhost:7860 > /dev/null && echo "App responding" || echo "App not responding"
  pkill -f "python src/app.py"
  ```
  *Expected: App responding (within 10 seconds)*

**Startup Validation**:
- [ ] **Startup Time Measurement**:
  ```bash
  time python -c "
  import time
  start = time.time()
  from src.app import main
  end = time.time()
  print(f'Startup time: {end - start:.2f} seconds')
  "
  ```
  *Expected: Startup time < 3 seconds*

- [ ] **No Startup Errors**:
  ```bash
  python src/app.py > startup.log 2>&1 &
  sleep 5
  grep -i error startup.log || echo "No errors found"
  pkill -f "python src/app.py"
  ```
  *Expected: No errors found in logs*

### 3.2 Web Interface Verification

**Gradio Interface Loading**:
- [ ] **Interface Accessibility**:
  ```bash
  python src/app.py &
  sleep 5
  curl -s -o /dev/null -w "%{http_code}" http://localhost:7860
  pkill -f "python src/app.py"
  ```
  *Expected: HTTP 200 response*

- [ ] **Interface Content Check**:
  ```bash
  python src/app.py &
  sleep 5
  curl -s http://localhost:7860 | grep -i gradio && echo "Gradio interface loaded" || echo "Gradio interface not found"
  pkill -f "python src/app.py"
  ```
  *Expected: Gradio interface loaded*

## 4. Functional Testing

### 4.1 Basic Chat Functionality

**Message Processing Test**:
- [ ] **Message Validation**:
  ```bash
  python -c "
  from src.core.message_processor import MessageProcessor
  mp = MessageProcessor()
  valid, error = mp.validate_message('Hello world')
  print(f'Message validation: {valid and not error}')
  "
  ```
  *Expected: Message validation: True*

- [ ] **API Message Formatting**:
  ```bash
  python -c "
  from src.core.message_processor import MessageProcessor
  mp = MessageProcessor()
  formatted = mp.format_for_api({'role': 'user', 'content': 'Test'}, 'gpt-3.5-turbo')
  print(f'API formatting: {formatted[\"role\"] == \"user\" and \"content\" in formatted}')
  "
  ```
  *Expected: API formatting: True*

**Conversation Management**:
- [ ] **Conversation Creation**:
  ```bash
  python -c "
  from src.core.conversation_manager import ConversationManager
  from src.storage.conversation_storage import ConversationStorage
  cs = ConversationStorage()
  cm = ConversationManager(cs)
  conv_id = cm.create_conversation('Functional Test')
  print(f'Conversation creation: {bool(conv_id)}')
  "
  ```
  *Expected: Conversation creation: True*

- [ ] **Message Saving and Loading**:
  ```python
  # In a Python script
  from src.core.conversation_manager import ConversationManager
  from src.storage.conversation_storage import ConversationStorage

  cs = ConversationStorage()
  cm = ConversationManager(cs)

  # Create and save
  conv_id = cm.create_conversation('Persistence Test')
  messages = [
      {'role': 'user', 'content': 'Test message', 'timestamp': '2024-01-01T10:00:00'}
  ]
  cm.save_conversation(conv_id, messages)

  # Load and verify
  loaded = cm.load_conversation(conv_id)
  success = len(loaded) == 1 and loaded[0]['content'] == 'Test message'
  print(f'Message persistence: {success}')
  ```
  *Expected: Message persistence: True*

### 4.2 API Integration Testing

**Mock API Test**:
- [ ] **API Response Processing**:
  ```python
  # Test with mock response
  from src.core.message_processor import MessageProcessor

  mp = MessageProcessor()
  mock_response = {
      'choices': [{
          'message': {'content': 'Mock response'},
          'finish_reason': 'stop'
      }]
  }

  processed = mp.process_response(mock_response, 'test-model')
  success = (processed['role'] == 'assistant' and
            processed['content'] == 'Mock response' and
            'tokens' in processed)
  print(f'API response processing: {success}')
  ```
  *Expected: API response processing: True*

**Live API Test (if API key available)**:
- [ ] **Real API Connectivity**:
  ```bash
  python -c "
  import asyncio
  from src.core.api_client import APIClient
  from src.storage.config_manager import ConfigManager

  async def test_live_api():
      try:
          cm = ConfigManager()
          ac = APIClient(cm)
          models = ac.get_available_models()
          if models:
              print(f'Live API test: {len(models)} models available')
          else:
              print('Live API test: No models (check API key)')
          await ac.close()
      except Exception as e:
          print(f'Live API test: Failed ({e})')

  asyncio.run(test_live_api())
  "
  ```
  *Expected: Live API test: X models available (or appropriate error message)*

## 5. Performance Validation

### 5.1 Startup Performance

**Cold Start Time**:
- [ ] **Application Startup Time**:
  ```bash
  time (
    python src/app.py &
    sleep 2
    curl -s http://localhost:7860 > /dev/null
    pkill -f "python src/app.py"
  ) 2>&1 | grep real | awk '{print "Startup time:", $2}'
  ```
  *Expected: Startup time < 10 seconds total*

### 5.2 Runtime Performance

**Memory Usage Check**:
- [ ] **Memory Consumption**:
  ```bash
  python src/app.py &
  sleep 5

  # Check memory usage
  # Windows: tasklist /FI "IMAGENAME eq python.exe" /FO LIST
  # macOS/Linux: ps aux | grep "python src/app.py" | grep -v grep

  # Get memory in MB
  mem_usage=$(ps aux | grep "python src/app.py" | grep -v grep | awk '{print $6/1024}')
  echo "Memory usage: ${mem_usage} MB"

  pkill -f "python src/app.py"
  ```
  *Expected: Memory usage < 500 MB*

**Response Time Test**:
- [ ] **UI Responsiveness**:
  ```bash
  python src/app.py &
  sleep 5

  # Test interface response time
  time curl -s http://localhost:7860 > /dev/null

  pkill -f "python src/app.py"
  ```
  *Expected: Interface response < 1 second*

## 6. Security Verification

### 6.1 Data Protection

**API Key Security**:
- [ ] **API Key Not in Plaintext Logs**:
  ```bash
  # Check that API key doesn't appear in logs
  grep -r "sk-or-v1" data/logs/ || echo "API key not found in logs"
  ```
  *Expected: API key not found in logs*

- [ ] **Configuration File Permissions**:
  ```bash
  # Check encryption key file permissions
  ls -la data/config/encryption.key
  ```
  *Expected: Permissions restrict access (600 or similar)*

**Data Encryption**:
- [ ] **Conversation Data Protection**:
  ```bash
  # Check that conversation files aren't plaintext sensitive data
  find data/conversations/ -name "*.json" -exec head -5 {} \; | head -10
  ```
  *Expected: No plaintext API keys or sensitive data visible*

### 6.2 Input Validation

**Security Input Tests**:
- [ ] **XSS Prevention**:
  ```python
  from src.core.message_processor import MessageProcessor

  mp = MessageProcessor()
  malicious_input = '<script>alert("xss")</script>Hello'
  valid, error = mp.validate_message(malicious_input)

  # Should either reject or sanitize
  print(f'XSS handling: {not valid or "<script>" not in malicious_input}')
  ```
  *Expected: XSS handling: True*

## 7. Cross-Platform Compatibility

### 7.1 File System Operations

**Path Handling**:
- [ ] **Cross-Platform Paths**:
  ```python
  from src.storage.conversation_storage import ConversationStorage
  import os

  cs = ConversationStorage()
  test_id = "test/path\\with:chars"
  result = cs.save_conversation(test_id, {
      "id": test_id,
      "title": "Path Test",
      "created_at": "2024-01-01T00:00:00",
      "messages": [],
      "metadata": {"message_count": 0, "total_tokens": 0}
  })

  print(f'Cross-platform paths: {result}')
  ```
  *Expected: Cross-platform paths: True*

### 7.2 Browser Compatibility

**Web Interface Access**:
- [ ] **Multiple Browser Access**:
  ```bash
  python src/app.py &
  sleep 5

  # Test with curl (simulates browser request)
  response=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:7860)
  echo "Browser compatibility: HTTP ${response}"

  pkill -f "python src/app.py"
  ```
  *Expected: Browser compatibility: HTTP 200*

## 8. Post-Deployment Monitoring

### 8.1 Operational Checks

**Application Stability**:
- [ ] **Extended Runtime Test**:
  ```bash
  python src/app.py &
  sleep 30  # Run for 30 seconds

  # Check still responding
  curl -s http://localhost:7860 > /dev/null && echo "App stable" || echo "App unstable"

  pkill -f "python src/app.py"
  ```
  *Expected: App stable*

**Log File Generation**:
- [ ] **Logging Functionality**:
  ```bash
  ls -la data/logs/app.log
  tail -5 data/logs/app.log
  ```
  *Expected: Log file exists with recent entries*

### 8.2 Data Persistence Verification

**Conversation Persistence**:
- [ ] **Data Survival Across Restarts**:
  ```python
  # Create test conversation
  from src.core.conversation_manager import ConversationManager
  from src.storage.conversation_storage import ConversationStorage

  cs = ConversationStorage()
  cm = ConversationManager(cs)

  conv_id = cm.create_conversation('Restart Test')
  cm.save_conversation(conv_id, [
      {'role': 'user', 'content': 'Restart persistence test', 'timestamp': '2024-01-01T10:00:00'}
  ])

  # Simulate restart by creating new instances
  cs2 = ConversationStorage()
  cm2 = ConversationManager(cs2)
  loaded = cm2.load_conversation(conv_id)

  success = len(loaded) == 1 and 'Restart persistence test' in loaded[0]['content']
  print(f'Data persistence: {success}')
  ```
  *Expected: Data persistence: True*

## 9. Rollback Procedures

### 9.1 Emergency Shutdown

**Graceful Shutdown**:
- [ ] **Clean Application Stop**:
  ```bash
  # Send shutdown signal
  curl -X POST http://localhost:7860/shutdown 2>/dev/null || echo "Shutdown endpoint not available"

  # Force stop if needed
  pkill -f "python src/app.py"

  # Verify stopped
  ps aux | grep "python src/app.py" | grep -v grep || echo "Application stopped"
  ```
  *Expected: Application stopped cleanly*

### 9.2 Configuration Rollback

**Settings Recovery**:
- [ ] **Configuration Backup Restore**:
  ```bash
  # If backup exists, restore configuration
  if [ -f data/config/app_config.json.backup ]; then
    cp data/config/app_config.json.backup data/config/app_config.json
    echo "Configuration restored from backup"
  else
    echo "No configuration backup found"
  fi
  ```
  *Expected: Configuration restored or appropriate message*

## Deployment Success Criteria

**All following must be true for successful deployment**:

### Functional Completeness
- [ ] All components import without errors
- [ ] Application starts within 3 seconds
- [ ] Web interface loads and responds
- [ ] Basic chat functionality works
- [ ] Conversations can be created and saved
- [ ] API integration functions (with valid key)

### Performance Requirements
- [ ] Memory usage < 500MB under normal operation
- [ ] Startup time < 3 seconds
- [ ] UI responsiveness < 100ms for local operations
- [ ] No performance degradation over time

### Reliability Standards
- [ ] Application runs stably for extended periods
- [ ] Error handling prevents crashes
- [ ] Data persistence works across restarts
- [ ] Logs are generated and useful

### Security Compliance
- [ ] API keys are encrypted and secure
- [ ] No sensitive data in logs
- [ ] Input validation prevents common attacks
- [ ] File permissions are appropriate

### User Experience
- [ ] Interface works in target browsers
- [ ] Cross-platform compatibility verified
- [ ] Error messages are user-friendly
- [ ] Basic workflows complete successfully

**Final Deployment Status**: ☐ PASS ☐ FAIL

**Deployment Date**: ________________

**Deployed By**: ________________

**Notes/Issues**: ________________