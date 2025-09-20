# Security Considerations

## Overview

This document outlines security practices for the Personal AI Chatbot, focusing on API key management, data protection, and secure coding practices for local deployment.

## API Key Security

### Environment Variable Management

**Never commit API keys to version control**:

```python
# ❌ BAD: Hardcoded API key
OPENROUTER_API_KEY = "sk-or-v1-1234567890abcdef"

# ✅ GOOD: Environment variable
import os
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
```

**Use .env files with proper exclusion**:

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=anthropic/claude-3-haiku

# .gitignore
.env
.env.local
.env.*.local
```

**Validate API key presence**:

```python
class Config:
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

    @classmethod
    def validate(cls):
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        if not cls.OPENROUTER_API_KEY.startswith('sk-or-v1-'):
            raise ValueError("Invalid OpenRouter API key format")

# Call at startup
Config.validate()
```

### Secure Key Storage Options

**Option 1: Encrypted .env files**:

```python
from cryptography.fernet import Fernet
import base64
import os

class SecureEnv:
    def __init__(self, key_file='.env.key', env_file='.env.encrypted'):
        self.key_file = key_file
        self.env_file = env_file
        self._cipher = None

    def _get_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        return key

    def encrypt_env(self, env_content: str):
        """Encrypt .env content"""
        key = self._get_or_create_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(env_content.encode())
        with open(self.env_file, 'wb') as f:
            f.write(encrypted)

    def decrypt_env(self):
        """Decrypt .env content"""
        if not os.path.exists(self.env_file):
            return ""

        key = self._get_or_create_key()
        cipher = Fernet(key)

        with open(self.env_file, 'rb') as f:
            encrypted = f.read()

        try:
            return cipher.decrypt(encrypted).decode()
        except Exception:
            return ""

# Usage
secure_env = SecureEnv()
# First time: encrypt your .env
# with open('.env', 'r') as f:
#     secure_env.encrypt_env(f.read())

# Load configuration
env_content = secure_env.decrypt_env()
# Parse env_content into environment variables
```

**Option 2: System keyring integration**:

```python
import keyring
import getpass

class KeyringManager:
    SERVICE_NAME = "personal-ai-chatbot"

    @staticmethod
    def set_api_key():
        """Securely store API key"""
        api_key = getpass.getpass("Enter your OpenRouter API key: ")
        keyring.set_password(KeyringManager.SERVICE_NAME, "openrouter_api_key", api_key)
        print("API key stored securely")

    @staticmethod
    def get_api_key():
        """Retrieve API key"""
        return keyring.get_password(KeyringManager.SERVICE_NAME, "openrouter_api_key")

    @staticmethod
    def delete_api_key():
        """Remove stored API key"""
        keyring.delete_password(KeyringManager.SERVICE_NAME, "openrouter_api_key")
        print("API key removed")

# Usage
# KeyringManager.set_api_key()  # Run once to store
# api_key = KeyringManager.get_api_key()  # Use in application
```

## Data Protection

### Conversation Data Security

**File permissions**:

```python
import os
import stat

def secure_file_permissions(file_path: str):
    """Set secure file permissions (owner read/write only)"""
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)

# Apply to conversation files
conversation_dir = Path("conversations")
conversation_dir.mkdir(exist_ok=True)
os.chmod(conversation_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

# When saving conversations
save_conversation_history(history)
secure_file_permissions("conversations.json")
```

**Data sanitization**:

```python
import re

def sanitize_conversation_data(messages: list) -> list:
    """Remove potentially sensitive data from conversation history"""
    sanitized = []

    for msg in messages:
        # Remove API keys from content
        content = msg.get('content', '')
        content = re.sub(r'sk-or-v1-[a-zA-Z0-9]{64}', '[API_KEY_REDACTED]', content)
        content = re.sub(r'sk-[a-zA-Z0-9]{48}', '[API_KEY_REDACTED]', content)

        # Remove email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', content)

        # Remove phone numbers (basic pattern)
        content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', content)

        sanitized.append({
            'role': msg.get('role'),
            'content': content,
            'timestamp': msg.get('timestamp')
        })

    return sanitized
```

### Backup Security

**Encrypted backups**:

```python
from cryptography.fernet import Fernet
import json
from pathlib import Path

class SecureBackup:
    def __init__(self, key: bytes = None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)

    def create_backup(self, conversation_id: str, messages: list, backup_dir: str = "backups"):
        """Create encrypted backup of conversation"""
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)

        data = {
            'conversation_id': conversation_id,
            'messages': messages,
            'backup_date': str(datetime.now()),
            'version': '1.0'
        }

        # Serialize and encrypt
        json_data = json.dumps(data, indent=2, default=str)
        encrypted_data = self.cipher.encrypt(json_data.encode())

        # Save encrypted backup
        backup_file = backup_dir / f"{conversation_id}_{int(time.time())}.backup"
        with open(backup_file, 'wb') as f:
            f.write(encrypted_data)

        # Secure permissions
        os.chmod(backup_file, stat.S_IRUSR | stat.S_IWUSR)

        return backup_file

    def restore_backup(self, backup_file: str) -> dict:
        """Restore conversation from encrypted backup"""
        with open(backup_file, 'rb') as f:
            encrypted_data = f.read()

        decrypted_data = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
```

## Input Validation and Sanitization

### Message Input Validation

```python
import re

class InputValidator:
    MAX_MESSAGE_LENGTH = 4000
    MAX_MESSAGES_PER_HOUR = 100

    @staticmethod
    def validate_message(message: str) -> tuple[bool, str]:
        """Validate user message input"""
        if not message or not message.strip():
            return False, "Message cannot be empty"

        if len(message) > InputValidator.MAX_MESSAGE_LENGTH:
            return False, f"Message too long (max {InputValidator.MAX_MESSAGE_LENGTH} characters)"

        # Check for potentially harmful patterns
        if InputValidator._contains_suspicious_patterns(message):
            return False, "Message contains potentially harmful content"

        return True, ""

    @staticmethod
    def _contains_suspicious_patterns(message: str) -> bool:
        """Check for suspicious patterns that might indicate attacks"""
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:',  # Data URLs
            r'\b(eval|exec|system)\b',  # Dangerous function calls
            r'\b(rm|del|format|shutdown)\b',  # System commands
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def validate_conversation_length(history: list) -> tuple[bool, str]:
        """Validate conversation length"""
        if len(history) > 1000:
            return False, "Conversation too long. Please start a new conversation."

        return True, ""

# Usage in chat handler
def chat_response(message, history):
    # Validate input
    is_valid, error_msg = InputValidator.validate_message(message)
    if not is_valid:
        return "", history + [{"role": "assistant", "content": f"Error: {error_msg}"}]

    # Validate conversation length
    is_valid, error_msg = InputValidator.validate_conversation_length(history)
    if not is_valid:
        return "", history + [{"role": "assistant", "content": f"Error: {error_msg}"}]

    # Proceed with normal processing...
```

## Network Security

### HTTPS and Certificate Validation

```python
import requests
import urllib3

# Ensure SSL verification is enabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SecureHTTPClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

        # Configure session for security
        self.session.verify = True  # Always verify SSL certificates
        self.session.timeout = timeout

    def post(self, url: str, **kwargs) -> requests.Response:
        """Secure POST request"""
        try:
            response = self.session.post(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError as e:
            raise Exception(f"SSL certificate verification failed: {e}")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Network connection failed: {e}")

# Use secure client for OpenRouter API
secure_client = SecureHTTPClient()

def call_openrouter_secure(message: str, history: list) -> str:
    payload = {
        "model": "anthropic/claude-3-haiku",
        "messages": history + [{"role": "user", "content": message}],
        "max_tokens": 1000
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    response = secure_client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        json=payload,
        headers=headers
    )

    return response.json()["choices"][0]["message"]["content"]
```

### Rate Limiting Protection

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_id: str = "default") -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        client_requests = self.requests[client_id]

        # Remove old requests outside the window
        client_requests[:] = [req_time for req_time in client_requests
                            if now - req_time < self.window_seconds]

        if len(client_requests) >= self.max_requests:
            return False

        client_requests.append(now)
        return True

    def get_remaining_requests(self, client_id: str = "default") -> int:
        """Get remaining requests in current window"""
        now = time.time()
        client_requests = self.requests[client_id]
        client_requests[:] = [req_time for req_time in client_requests
                            if now - req_time < self.window_seconds]
        return max(0, self.max_requests - len(client_requests))

# Global rate limiter
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)

def chat_with_rate_limit(message, history):
    if not rate_limiter.is_allowed():
        remaining_time = 60  # Could calculate exact remaining time
        return "", history + [{
            "role": "assistant",
            "content": f"Rate limit exceeded. Please wait {remaining_time} seconds before sending another message."
        }]

    # Proceed with normal processing...
```

## Local Security Practices

### Application Hardening

**Disable debug mode in production**:

```python
import os

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Only enable debug in development
if DEBUG:
    print("WARNING: Debug mode is enabled. Disable for production use.")
```

**Secure logging**:

```python
import logging
import os

# Don't log sensitive information
class SafeFormatter(logging.Formatter):
    def format(self, record):
        # Remove sensitive fields from log records
        if hasattr(record, 'api_key'):
            record.api_key = '[REDACTED]'
        return super().format(record)

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Safe logging example
def log_api_call(endpoint: str, api_key: str):
    logger.info(f"API call to {endpoint}", extra={'api_key': api_key})
```

### Dependency Security

**Requirements with pinned versions**:

```txt
# requirements.txt - Pin versions for security
gradio==5.44.1
requests==2.31.0
python-dotenv==1.0.0
cryptography==41.0.7
keyring==24.3.0
psutil==5.9.6
```

**Vulnerability scanning**:

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Update dependencies securely
pip install pip-tools
pip-compile --upgrade  # Updates requirements.txt with latest compatible versions
```

## Compliance Considerations

### Data Privacy

**Data minimization**:

```python
class PrivacyManager:
    @staticmethod
    def should_retain_message(message: str) -> bool:
        """Determine if message should be retained based on privacy rules"""
        # Don't store messages with PII
        pii_patterns = [
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # SSN
            r'\b\d{9}\b',  # SSN without separators
        ]

        for pattern in pii_patterns:
            if re.search(pattern, message):
                return False

        return True

    @staticmethod
    def anonymize_message(message: str) -> str:
        """Anonymize sensitive data in message"""
        # Replace PII with placeholders
        message = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CREDIT_CARD]', message)
        message = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[SSN]', message)
        return message
```

### Audit Logging

**Security event logging**:

```python
import json
import hashlib

class SecurityAuditor:
    def __init__(self, log_file: str = "security.log"):
        self.log_file = log_file

    def log_security_event(self, event_type: str, details: dict, severity: str = "INFO"):
        """Log security-related events"""
        event = {
            'timestamp': str(datetime.now()),
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'session_hash': self._get_session_hash()
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def _get_session_hash(self) -> str:
        """Get anonymous session identifier"""
        # Create hash of session data without exposing sensitive info
        session_data = str(datetime.now().date())  # Daily hash
        return hashlib.sha256(session_data.encode()).hexdigest()[:16]

# Usage
auditor = SecurityAuditor()

def log_failed_auth(attempt_details: dict):
    auditor.log_security_event(
        'AUTHENTICATION_FAILED',
        attempt_details,
        severity='WARNING'
    )

def log_api_key_access():
    auditor.log_security_event(
        'API_KEY_ACCESSED',
        {'action': 'read'},
        severity='INFO'
    )
```

## Incident Response

### Security Incident Handling

```python
class IncidentResponse:
    @staticmethod
    def handle_suspicious_activity(activity: str, details: dict):
        """Handle detected suspicious activity"""
        print(f"SECURITY ALERT: {activity}")

        # Log incident
        auditor.log_security_event(
            'SUSPICIOUS_ACTIVITY',
            {'activity': activity, 'details': details},
            severity='CRITICAL'
        )

        # Implement response actions
        IncidentResponse._isolate_threat()
        IncidentResponse._notify_admin()

    @staticmethod
    def _isolate_threat():
        """Isolate potential threat"""
        # In a real application, this might:
        # - Revoke API keys
        # - Block IP addresses
        # - Disable user sessions
        # - Encrypt sensitive data
        print("Threat isolation measures activated")

    @staticmethod
    def _notify_admin():
        """Notify system administrator"""
        # In a real application, this might:
        # - Send email alerts
        # - Create incident tickets
        # - Trigger monitoring alerts
        print("Administrator notification sent")

    @staticmethod
    def emergency_shutdown(reason: str):
        """Emergency shutdown procedure"""
        print(f"EMERGENCY SHUTDOWN: {reason}")

        # Save critical data
        # Close connections
        # Log incident
        # Exit gracefully
        os._exit(1)
```

### Recovery Procedures

**Data breach response**:

```python
def handle_data_breach():
    """Procedure for handling suspected data breach"""
    # 1. Isolate affected systems
    print("Isolating affected systems...")

    # 2. Preserve evidence
    backup_incident_data()

    # 3. Assess damage
    assess_breach_impact()

    # 4. Notify affected parties
    notify_affected_users()

    # 5. Recover systems
    recover_from_backup()

def backup_incident_data():
    """Create forensic backup of incident data"""
    timestamp = int(time.time())
    backup_file = f"incident_backup_{timestamp}.tar.gz"

    # Create encrypted backup of logs and current state
    # This is critical for post-incident analysis

def assess_breach_impact():
    """Assess the scope and impact of the breach"""
    # Check what data was exposed
    # Determine affected users
    # Evaluate business impact

def notify_affected_users():
    """Notify users of potential data exposure"""
    # Send clear communication about the incident
    # Provide guidance on protective measures
    # Offer support resources

def recover_from_backup():
    """Restore systems from clean backups"""
    # Verify backup integrity
    # Restore from known-good state
    # Validate system security
    # Monitor for additional threats
```

## Security Checklist

### Pre-Deployment Checklist

- [ ] API keys stored in environment variables only
- [ ] .env files excluded from version control
- [ ] File permissions set to owner-only access
- [ ] SSL certificate validation enabled
- [ ] Input validation implemented
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Dependencies pinned to secure versions
- [ ] Debug mode disabled

### Ongoing Security Monitoring

- [ ] Regular dependency vulnerability scans
- [ ] API key rotation schedule
- [ ] Log file monitoring for suspicious activity
- [ ] Backup integrity verification
- [ ] Performance monitoring for anomalies
- [ ] User activity pattern analysis

### Emergency Contacts

- **Security Incidents**: Document response procedures and contact information
- **Data Breaches**: Legal notification requirements and procedures
- **API Key Compromise**: Immediate key rotation procedures

Following these security practices will help protect user data, prevent unauthorized access, and ensure compliance with privacy regulations.