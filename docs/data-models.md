# Data Models and Schemas - Personal AI Chatbot

## Overview

This document specifies all data models, schemas, and persistence structures for the Personal AI Chatbot system. All data models include validation rules, migration strategies, and integrity guarantees.

## 1. Core Data Models

### 1.1 Message Model

**Purpose**: Represents individual chat messages in conversations

**Schema Definition**:
```python
@dataclass
class Message:
    """Individual chat message with metadata"""
    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    model: Optional[str] = None
    tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validation after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate message data integrity"""
        if not self.id:
            raise ValueError("Message ID is required")
        if self.role not in ['user', 'assistant', 'system']:
            raise ValueError(f"Invalid role: {self.role}")
        if not self.content:
            raise ValueError("Message content cannot be empty")
        if len(self.content) > 2000:
            raise ValueError("Message content exceeds maximum length")
        if self.tokens is not None and self.tokens < 0:
            raise ValueError("Token count cannot be negative")
```

**JSON Schema**:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["id", "role", "content", "timestamp"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^msg_[a-f0-9]{8}$",
      "description": "Unique message identifier"
    },
    "role": {
      "type": "string",
      "enum": ["user", "assistant", "system"],
      "description": "Message sender role"
    },
    "content": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000,
      "description": "Message text content"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Message creation timestamp"
    },
    "model": {
      "type": ["string", "null"],
      "description": "AI model used for generation"
    },
    "tokens": {
      "type": ["integer", "null"],
      "minimum": 0,
      "description": "Token count for the message"
    },
    "metadata": {
      "type": "object",
      "description": "Additional message metadata",
      "properties": {
        "finish_reason": {
          "type": ["string", "null"],
          "enum": ["stop", "length", "content_filter", null]
        },
        "usage": {
          "type": "object",
          "properties": {
            "prompt_tokens": {"type": "integer", "minimum": 0},
            "completion_tokens": {"type": "integer", "minimum": 0}
          }
        }
      }
    }
  }
}
```

### 1.2 Conversation Model

**Purpose**: Represents complete chat conversations with metadata

**Schema Definition**:
```python
@dataclass
class Conversation:
    """Complete conversation with messages and metadata"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message]
    model_used: str
    total_tokens: int
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validation after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate conversation data integrity"""
        if not self.id:
            raise ValueError("Conversation ID is required")
        if not self.title:
            raise ValueError("Conversation title is required")
        if self.created_at > self.updated_at:
            raise ValueError("Created timestamp cannot be after updated timestamp")
        if self.total_tokens < 0:
            raise ValueError("Total tokens cannot be negative")
        if len(self.messages) == 0:
            raise ValueError("Conversation must contain at least one message")

        # Validate all messages
        for message in self.messages:
            message.validate()

    def add_message(self, message: Message) -> None:
        """Add message and update metadata"""
        self.messages.append(message)
        self.updated_at = datetime.now()
        self.total_tokens += message.tokens or 0

    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary for listing"""
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages),
            'model_used': self.model_used,
            'total_tokens': self.total_tokens,
            'tags': self.tags
        }
```

**JSON Schema**:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["id", "title", "created_at", "updated_at", "messages", "model_used", "total_tokens"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^conv_[a-f0-9]{8}$",
      "description": "Unique conversation identifier"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Human-readable conversation title"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Conversation creation timestamp"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Last modification timestamp"
    },
    "messages": {
      "type": "array",
      "description": "Array of conversation messages",
      "items": {"$ref": "#/definitions/Message"},
      "minItems": 1
    },
    "model_used": {
      "type": "string",
      "description": "Primary AI model used in conversation"
    },
    "total_tokens": {
      "type": "integer",
      "minimum": 0,
      "description": "Total token count across all messages"
    },
    "tags": {
      "type": "array",
      "description": "User-defined conversation tags",
      "items": {"type": "string", "maxLength": 50}
    },
    "metadata": {
      "type": "object",
      "description": "Additional conversation metadata"
    }
  },
  "definitions": {
    "Message": {
      "type": "object",
      "required": ["id", "role", "content", "timestamp"],
      "properties": {
        "id": {"type": "string"},
        "role": {"type": "string", "enum": ["user", "assistant", "system"]},
        "content": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "model": {"type": ["string", "null"]},
        "tokens": {"type": ["integer", "null"]},
        "metadata": {"type": "object"}
      }
    }
  }
}
```

### 1.3 Configuration Model

**Purpose**: Application configuration and user preferences

**Schema Definition**:
```python
@dataclass
class ApplicationConfig:
    """Application configuration with validation"""
    api_key_encrypted: str
    active_model: str
    ui_theme: str
    max_tokens: int
    temperature: float
    conversation_retention_days: int
    auto_save_interval: int
    rate_limit_requests_per_minute: int
    enable_streaming: bool
    enable_error_logging: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        """Validation after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate configuration values"""
        if not self.api_key_encrypted:
            raise ValueError("API key is required")
        if self.max_tokens < 1 or self.max_tokens > 4096:
            raise ValueError("max_tokens must be between 1 and 4096")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        if self.conversation_retention_days < 1:
            raise ValueError("conversation_retention_days must be positive")
        if self.rate_limit_requests_per_minute < 1:
            raise ValueError("rate_limit_requests_per_minute must be positive")
```

**JSON Schema**:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["api_key_encrypted", "active_model", "ui_theme", "max_tokens", "temperature", "conversation_retention_days", "auto_save_interval", "rate_limit_requests_per_minute", "enable_streaming", "enable_error_logging", "created_at", "updated_at"],
  "properties": {
    "api_key_encrypted": {
      "type": "string",
      "description": "AES-256 encrypted OpenRouter API key"
    },
    "active_model": {
      "type": "string",
      "description": "Currently selected AI model"
    },
    "ui_theme": {
      "type": "string",
      "enum": ["light", "dark", "auto"],
      "default": "auto",
      "description": "UI theme preference"
    },
    "max_tokens": {
      "type": "integer",
      "minimum": 1,
      "maximum": 4096,
      "default": 1000,
      "description": "Maximum tokens per response"
    },
    "temperature": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 2.0,
      "default": 0.7,
      "description": "Response randomness"
    },
    "conversation_retention_days": {
      "type": "integer",
      "minimum": 1,
      "default": 365,
      "description": "Days to retain conversations"
    },
    "auto_save_interval": {
      "type": "integer",
      "minimum": 30,
      "default": 300,
      "description": "Auto-save interval in seconds"
    },
    "rate_limit_requests_per_minute": {
      "type": "integer",
      "minimum": 1,
      "default": 20,
      "description": "Rate limit for API requests"
    },
    "enable_streaming": {
      "type": "boolean",
      "default": true,
      "description": "Enable streaming responses"
    },
    "enable_error_logging": {
      "type": "boolean",
      "default": true,
      "description": "Enable detailed error logging"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Configuration creation timestamp"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Configuration last update timestamp"
    }
  }
}
```

## 2. File Format Specifications

### 2.1 Conversation File Format

**File Extension**: `.json`
**Location**: `conversations/{conversation_id}.json`
**Encoding**: UTF-8
**Structure**:

```json
{
  "version": "1.0",
  "conversation": {
    "id": "conv_a1b2c3d4",
    "title": "AI Assistant Discussion",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:45:00Z",
    "model_used": "anthropic/claude-3-haiku",
    "total_tokens": 2450,
    "tags": ["productivity", "coding"],
    "metadata": {
      "source": "web_interface",
      "user_agent": "PersonalAIChatbot/1.0"
    }
  },
  "messages": [
    {
      "id": "msg_00112233",
      "role": "user",
      "content": "How can I improve my Python code?",
      "timestamp": "2024-01-15T10:30:00Z",
      "tokens": 8,
      "metadata": {}
    },
    {
      "id": "msg_44556677",
      "role": "assistant",
      "content": "Here are several ways to improve your Python code...",
      "timestamp": "2024-01-15T10:30:05Z",
      "model": "anthropic/claude-3-haiku",
      "tokens": 342,
      "metadata": {
        "finish_reason": "stop",
        "usage": {
          "prompt_tokens": 8,
          "completion_tokens": 342
        }
      }
    }
  ]
}
```

### 2.2 Configuration File Format

**File Extension**: `.json`
**Location**: `config/app_config.json`
**Encoding**: UTF-8
**Encryption**: AES-256 for sensitive fields

**Structure**:
```json
{
  "version": "1.0",
  "config": {
    "api_key_encrypted": "U2FsdGVkX1+encrypted_data_here==",
    "active_model": "anthropic/claude-3-haiku",
    "ui_theme": "auto",
    "max_tokens": 1000,
    "temperature": 0.7,
    "conversation_retention_days": 365,
    "auto_save_interval": 300,
    "rate_limit_requests_per_minute": 20,
    "enable_streaming": true,
    "enable_error_logging": true,
    "created_at": "2024-01-15T09:00:00Z",
    "updated_at": "2024-01-15T11:30:00Z"
  },
  "checksum": "sha256_hash_of_config_data"
}
```

### 2.3 Backup File Format

**File Extension**: `.backup`
**Location**: `backups/{timestamp}_{conversation_id}.backup`
**Compression**: gzip
**Structure**: Identical to conversation file format

## 3. Database Schema (Alternative SQLite Implementation)

### 3.1 Tables Schema

**conversations table**:
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    model_used TEXT NOT NULL,
    total_tokens INTEGER DEFAULT 0,
    tags TEXT, -- JSON array
    metadata TEXT, -- JSON object
    version TEXT DEFAULT '1.0'
);

CREATE INDEX idx_conversations_updated_at ON conversations(updated_at);
CREATE INDEX idx_conversations_model ON conversations(model_used);
```

**messages table**:
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    model TEXT,
    tokens INTEGER,
    metadata TEXT, -- JSON object
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
```

**config table**:
```sql
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT FALSE,
    updated_at TEXT NOT NULL
);
```

### 3.2 Migration Strategy

**Version 1.0 Initial Schema**:
```python
def migrate_to_v1_0(connection):
    """Initial database schema migration"""
    with connection:
        connection.execute('''
            CREATE TABLE schema_version (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        ''')

        # Create tables as defined above
        # ... table creation statements ...

        connection.execute('''
            INSERT INTO schema_version (version, applied_at)
            VALUES ('1.0', datetime('now'))
        ''')
```

## 4. Data Validation Rules

### 4.1 Message Validation

```python
class MessageValidator:
    """Comprehensive message validation"""

    @staticmethod
    def validate_content(content: str) -> List[str]:
        """Validate message content, return list of errors"""
        errors = []

        if not content or not content.strip():
            errors.append("Message content cannot be empty")

        if len(content) > 2000:
            errors.append("Message content exceeds 2000 character limit")

        # Check for potentially harmful content
        if MessageValidator._contains_suspicious_patterns(content):
            errors.append("Message contains potentially harmful content")

        return errors

    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> List[str]:
        """Validate message metadata"""
        errors = []

        if 'usage' in metadata:
            usage = metadata['usage']
            if not isinstance(usage.get('prompt_tokens'), int):
                errors.append("prompt_tokens must be integer")
            if not isinstance(usage.get('completion_tokens'), int):
                errors.append("completion_tokens must be integer")

        return errors

    @staticmethod
    def _contains_suspicious_patterns(content: str) -> bool:
        """Check for potentially harmful patterns"""
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<\w+[^>]*>.*?</\w+>'
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
```

### 4.2 Conversation Validation

```python
class ConversationValidator:
    """Conversation-level validation"""

    @staticmethod
    def validate_structure(conversation: Dict[str, Any]) -> List[str]:
        """Validate conversation structure"""
        errors = []

        required_fields = ['id', 'title', 'created_at', 'updated_at', 'messages']
        for field in required_fields:
            if field not in conversation:
                errors.append(f"Missing required field: {field}")

        if 'messages' in conversation:
            if not isinstance(conversation['messages'], list):
                errors.append("messages must be an array")
            elif len(conversation['messages']) == 0:
                errors.append("conversation must contain at least one message")

        return errors

    @staticmethod
    def validate_integrity(conversation: Dict[str, Any]) -> List[str]:
        """Validate conversation data integrity"""
        errors = []

        # Check timestamp consistency
        created_at = conversation.get('created_at')
        updated_at = conversation.get('updated_at')

        if created_at and updated_at:
            try:
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                if created > updated:
                    errors.append("created_at cannot be after updated_at")
            except ValueError as e:
                errors.append(f"Invalid timestamp format: {e}")

        return errors
```

## 5. Data Migration Strategies

### 5.1 File-based Migration

```python
class DataMigrator:
    """Handle data format migrations"""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.backup_dir = storage_dir / 'backups'

    def migrate_conversation_file(self, file_path: Path) -> bool:
        """Migrate single conversation file"""
        try:
            # Read current format
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Determine current version
            version = data.get('version', '0.9')

            # Apply migrations sequentially
            if version == '0.9':
                data = self._migrate_0_9_to_1_0(data)
                data['version'] = '1.0'

            # Backup original
            backup_path = self._create_backup(file_path)

            # Write migrated data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            return True

        except Exception as e:
            logger.error(f"Migration failed for {file_path}: {e}")
            self._restore_backup(file_path, backup_path)
            return False

    def _migrate_0_9_to_1_0(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 0.9 to 1.0"""
        # Add missing fields with defaults
        if 'version' not in data:
            data['version'] = '1.0'

        if 'conversation' not in data:
            data['conversation'] = {
                'id': data.get('id', str(uuid.uuid4())),
                'title': data.get('title', 'Untitled Conversation'),
                'created_at': data.get('created_at', datetime.now().isoformat()),
                'updated_at': data.get('updated_at', datetime.now().isoformat()),
                'model_used': data.get('model_used', 'unknown'),
                'total_tokens': data.get('total_tokens', 0),
                'tags': data.get('tags', []),
                'metadata': data.get('metadata', {})
            }

        return data
```

### 5.2 Integrity Verification

```python
class DataIntegrityChecker:
    """Verify data integrity after migrations"""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir

    def verify_all_conversations(self) -> Dict[str, Any]:
        """Verify integrity of all conversation files"""
        results = {
            'total_files': 0,
            'valid_files': 0,
            'corrupted_files': [],
            'missing_files': []
        }

        for file_path in self.storage_dir.glob("*.json"):
            results['total_files'] += 1

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Validate structure
                errors = ConversationValidator.validate_structure(data)
                if errors:
                    results['corrupted_files'].append({
                        'file': str(file_path),
                        'errors': errors
                    })
                else:
                    results['valid_files'] += 1

            except json.JSONDecodeError:
                results['corrupted_files'].append({
                    'file': str(file_path),
                    'errors': ['Invalid JSON format']
                })
            except Exception as e:
                results['corrupted_files'].append({
                    'file': str(file_path),
                    'errors': [str(e)]
                })

        return results
```

## 6. Backup and Recovery Specifications

### 6.1 Backup Strategy

**Backup Types**:
- **Full Backup**: Complete conversation and configuration data
- **Incremental Backup**: Only changed conversations since last backup
- **Configuration Backup**: Settings and API key data only

**Backup Schedule**:
- Full backup: Daily at 02:00
- Configuration backup: On every configuration change
- Incremental backup: Every 6 hours

**Retention Policy**:
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

### 6.2 Recovery Procedures

```python
class BackupRecovery:
    """Handle backup and recovery operations"""

    def create_backup(self, backup_type: str = 'full') -> str:
        """Create backup of specified type"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{backup_type}_{timestamp}"

        if backup_type == 'full':
            return self._create_full_backup(backup_name)
        elif backup_type == 'incremental':
            return self._create_incremental_backup(backup_name)
        elif backup_type == 'config':
            return self._create_config_backup(backup_name)

    def restore_backup(self, backup_name: str) -> bool:
        """Restore from specified backup"""
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")

        try:
            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(self.storage_dir)

            # Verify integrity
            integrity_results = DataIntegrityChecker(self.storage_dir).verify_all_conversations()

            if integrity_results['corrupted_files']:
                logger.warning(f"Backup restoration completed with {len(integrity_results['corrupted_files'])} corrupted files")
                return False

            return True

        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False
```

This data model specification provides the complete foundation for data persistence, validation, and integrity in the Personal AI Chatbot system.