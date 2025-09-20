# Integration Pattern Recommendations

## Overview

This document provides concrete implementation patterns for integrating Gradio 5, OpenRouter API, and file-based storage in the Personal AI Chatbot. All patterns include error handling and best practices.

## Gradio Chat Interface Patterns

### Basic Chat Interface with State Persistence

```python
import gradio as gr
import json
from pathlib import Path

def load_conversation_history():
    """Load conversation history from JSON file"""
    history_file = Path("conversations.json")
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_conversation_history(history):
    """Save conversation history to JSON file"""
    history_file = Path("conversations.json")
    try:
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving history: {e}")

def chat_response(message, history):
    """Handle chat message and update history"""
    if not history:
        history = []

    # Add user message
    history.append({"role": "user", "content": message, "timestamp": str(datetime.now())})

    try:
        # Call OpenRouter API (see pattern below)
        bot_response = call_openrouter_api(message, history)

        # Add bot response
        history.append({"role": "assistant", "content": bot_response, "timestamp": str(datetime.now())})

        # Save to file
        save_conversation_history(history)

        return "", history
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        history.append({"role": "assistant", "content": error_msg, "timestamp": str(datetime.now())})
        return "", history

# Create interface
with gr.Blocks() as demo:
    gr.Markdown("# Personal AI Chatbot")

    chatbot = gr.Chatbot(
        type="messages",
        height=500,
        show_copy_button=True
    )

    msg = gr.Textbox(
        placeholder="Type your message...",
        show_label=False
    )

    # Load initial history
    initial_history = load_conversation_history()

    msg.submit(
        chat_response,
        [msg, chatbot],
        [msg, chatbot]
    )

if __name__ == "__main__":
    demo.launch()
```

### Streaming Response Pattern

```python
import gradio as gr
import requests
import json

def stream_openrouter_response(message, history):
    """Stream response from OpenRouter API"""
    history = history or []

    # Add user message
    history.append({"role": "user", "content": message})

    # Prepare API request
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "anthropic/claude-3-haiku",
        "messages": history,
        "stream": True
    }

    response_text = ""
    history.append({"role": "assistant", "content": ""})

    try:
        with requests.post(url, headers=headers, json=payload, stream=True) as r:
            r.raise_for_status()

            for line in r.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break

                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and chunk['choices']:
                                content = chunk['choices'][0]['delta'].get('content', '')
                                if content:
                                    response_text += content
                                    history[-1]['content'] = response_text
                                    yield "", history
                        except json.JSONDecodeError:
                            continue

    except requests.exceptions.RequestException as e:
        history[-1]['content'] = f"API Error: {str(e)}"
        yield "", history

# Use with ChatInterface for streaming
gr.ChatInterface(stream_openrouter_response, type="messages")
```

## OpenRouter API Integration Patterns

### Authentication and Request Pattern

```python
import os
import requests
from typing import List, Dict, Any

class OpenRouterClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key required")

        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",  # Optional
            "X-Title": "Personal AI Chatbot"  # Optional
        }

    def check_rate_limits(self) -> Dict[str, Any]:
        """Check current usage and limits"""
        try:
            response = requests.get(f"{self.base_url}/key", headers={
                "Authorization": f"Bearer {self.api_key}"
            })
            response.raise_for_status()
            return response.json()['data']
        except requests.exceptions.RequestException as e:
            print(f"Rate limit check failed: {e}")
            return {}

    def chat_completion(self, messages: List[Dict], model: str = "anthropic/claude-3-haiku",
                       stream: bool = False, **kwargs) -> Dict[str, Any]:
        """Make chat completion request"""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 402:
                raise Exception("Insufficient credits. Please add more credits to your OpenRouter account.")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded. Please wait before making more requests.")
            elif response.status_code == 401:
                raise Exception("Invalid API key. Please check your OpenRouter API key.")
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
```

### Error Handling Pattern

```python
def handle_openrouter_error(response: requests.Response) -> str:
    """Handle OpenRouter API errors gracefully"""
    try:
        error_data = response.json()
        error = error_data.get('error', {})

        error_code = error.get('code', response.status_code)
        error_message = error.get('message', 'Unknown error')

        if error_code == 402:
            return "Your OpenRouter account has insufficient credits. Please add more credits."
        elif error_code == 403:
            metadata = error.get('metadata', {})
            if 'flagged_input' in metadata:
                return "Your message was flagged by content moderation. Please rephrase and try again."
            return "Access denied. Please check your account permissions."
        elif error_code == 429:
            return "Rate limit exceeded. Please wait a moment before sending another message."
        elif error_code == 408:
            return "Request timed out. Please try again."
        elif error_code == 502:
            return "The AI model is currently unavailable. Please try again later."
        elif error_code == 503:
            return "No available AI model provider. Please try again later."
        else:
            return f"An error occurred: {error_message}"

    except json.JSONDecodeError:
        return f"Server error ({response.status_code}). Please try again."
```

## File-based Storage Patterns

### JSON Conversation Storage

```python
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class ConversationStore:
    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_conversation(self, conversation_id: str, messages: List[Dict[str, Any]]):
        """Save conversation with atomic write"""
        file_path = self.storage_dir / f"{conversation_id}.json"

        # Create backup if file exists
        if file_path.exists():
            backup_path = file_path.with_suffix('.bak')
            file_path.replace(backup_path)

        try:
            # Atomic write using temporary file
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump({
                    'id': conversation_id,
                    'messages': messages,
                    'updated_at': datetime.now().isoformat(),
                    'version': '1.0'
                }, f, indent=2, default=str)

            # Atomic move
            temp_path.replace(file_path)

            # Remove backup on success
            if backup_path.exists():
                backup_path.unlink()

        except Exception as e:
            # Restore backup on failure
            if backup_path.exists():
                backup_path.replace(file_path)
            raise e

    def load_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Load conversation from file"""
        file_path = self.storage_dir / f"{conversation_id}.json"

        if not file_path.exists():
            return {'id': conversation_id, 'messages': [], 'version': '1.0'}

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Validate structure
            if not isinstance(data.get('messages', []), list):
                data['messages'] = []

            return data

        except json.JSONDecodeError:
            # Try backup file
            backup_path = file_path.with_suffix('.bak')
            if backup_path.exists():
                try:
                    with open(backup_path, 'r') as f:
                        return json.load(f)
                except:
                    pass

            # Return empty conversation on failure
            return {'id': conversation_id, 'messages': [], 'version': '1.0'}

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations with metadata"""
        conversations = []

        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                conversations.append({
                    'id': data.get('id', file_path.stem),
                    'message_count': len(data.get('messages', [])),
                    'updated_at': data.get('updated_at'),
                    'size_bytes': file_path.stat().st_size
                })

            except Exception:
                # Skip corrupted files
                continue

        return sorted(conversations, key=lambda x: x.get('updated_at', ''), reverse=True)
```

### SQLite Storage Alternative (for Scale)

```python
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any

class SQLiteConversationStore:
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            ''')
            conn.commit()

    def save_conversation(self, conversation_id: str, messages: List[Dict[str, Any]], title: str = None):
        with self.get_connection() as conn:
            # Insert/update conversation
            conn.execute('''
                INSERT OR REPLACE INTO conversations (id, title, updated_at)
                VALUES (?, ?, datetime('now'))
            ''', (conversation_id, title or f"Conversation {conversation_id[:8]}"))

            # Clear existing messages
            conn.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))

            # Insert messages
            for msg in messages:
                conn.execute('''
                    INSERT INTO messages (conversation_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    conversation_id,
                    msg.get('role'),
                    msg.get('content'),
                    msg.get('timestamp', datetime.now().isoformat())
                ))

            conn.commit()
```

## Configuration Management Patterns

### Environment Variable Configuration

```python
# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # OpenRouter settings
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-haiku')

    # Application settings
    APP_TITLE = os.getenv('APP_TITLE', 'Personal AI Chatbot')
    MAX_CONVERSATION_LENGTH = int(os.getenv('MAX_CONVERSATION_LENGTH', '100'))

    # Storage settings
    STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'json')  # 'json' or 'sqlite'
    STORAGE_DIR = os.getenv('STORAGE_DIR', 'conversations')

    # UI settings
    THEME = os.getenv('THEME', 'default')
    CHAT_HEIGHT = int(os.getenv('CHAT_HEIGHT', '500'))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        if cls.STORAGE_TYPE not in ['json', 'sqlite']:
            raise ValueError("STORAGE_TYPE must be 'json' or 'sqlite'")

# .env.example
# OPENROUTER_API_KEY=your_api_key_here
# OPENROUTER_MODEL=anthropic/claude-3-haiku
# APP_TITLE=Personal AI Chatbot
# MAX_CONVERSATION_LENGTH=100
# STORAGE_TYPE=json
# STORAGE_DIR=conversations
# THEME=default
# CHAT_HEIGHT=500
```

### Secure API Key Management

```python
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureConfig:
    def __init__(self, key_file: str = ".key", env_file: str = ".env.encrypted"):
        self.key_file = Path(key_file)
        self.env_file = Path(env_file)
        self._cipher = None

    def _get_cipher(self):
        if self._cipher is None:
            if not self.key_file.exists():
                # Generate new key
                from cryptography.hazmat.primitives.asymmetric import rsa
                from cryptography.hazmat.primitives import serialization

                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                )

                with open(self.key_file, 'wb') as f:
                    f.write(private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))

            # Load key and create cipher
            with open(self.key_file, 'rb') as f:
                key_data = f.read()

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'constant_salt',  # In production, use a proper salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_data))
            self._cipher = Fernet(key)

        return self._cipher

    def encrypt_env_file(self, plaintext_env: str):
        """Encrypt .env content"""
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(plaintext_env.encode())
        with open(self.env_file, 'wb') as f:
            f.write(encrypted)

    def decrypt_env_file(self):
        """Decrypt .env content"""
        if not self.env_file.exists():
            return ""

        cipher = self._get_cipher()
        with open(self.env_file, 'rb') as f:
            encrypted = f.read()

        try:
            return cipher.decrypt(encrypted).decode()
        except Exception:
            return ""

# Usage
secure_config = SecureConfig()
# First time: encrypt your .env
# secure_config.encrypt_env_file("OPENROUTER_API_KEY=your_key_here")

# Load configuration
env_content = secure_config.decrypt_env_file()
# Parse and load into environment
```

## Error Handling Patterns

### Comprehensive Error Boundary

```python
import logging
import traceback
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def error_boundary(func):
    """Decorator for comprehensive error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())

            # Return user-friendly error
            return f"An error occurred: {str(e)}"
    return wrapper

@error_boundary
def process_chat_message(message: str, history: List[Dict]) -> str:
    """Process chat message with full error handling"""
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")

    if len(history) > 1000:  # Prevent memory issues
        raise ValueError("Conversation too long. Please start a new conversation.")

    # Validate API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("API key not configured")

    # Make API call with timeout and retries
    client = OpenRouterClient(api_key)

    try:
        response = client.chat_completion(
            messages=history + [{"role": "user", "content": message}],
            model="anthropic/claude-3-haiku",
            max_tokens=1000,
            temperature=0.7
        )

        return response['choices'][0]['message']['content']

    except Exception as e:
        # Log detailed error for debugging
        logger.error(f"OpenRouter API error: {str(e)}")

        # Return user-friendly message
        if "insufficient credits" in str(e).lower():
            return "I'm sorry, but your OpenRouter account has insufficient credits. Please add more credits to continue."
        elif "rate limit" in str(e).lower():
            return "I'm receiving too many requests right now. Please wait a moment and try again."
        else:
            return "I apologize, but I'm having trouble connecting to the AI service right now. Please try again in a few moments."
```

### Graceful Degradation Pattern

```python
def get_ai_response_with_fallback(message: str, history: List[Dict]) -> str:
    """Get AI response with fallback options"""
    responses = []

    # Try primary model
    try:
        return call_openrouter_api(message, history, model="anthropic/claude-3-haiku")
    except Exception as e:
        responses.append(f"Primary model failed: {str(e)}")

    # Try fallback model
    try:
        return call_openrouter_api(message, history, model="openai/gpt-3.5-turbo")
    except Exception as e:
        responses.append(f"Fallback model failed: {str(e)}")

    # Return cached response or generic message
    if history:
        last_bot_message = next((msg['content'] for msg in reversed(history)
                               if msg.get('role') == 'assistant'), None)
        if last_bot_message:
            return f"Using previous response: {last_bot_message[:200]}..."

    # Final fallback
    return "I'm sorry, but I'm unable to generate a response right now. Please check your internet connection and API configuration."
```

These patterns provide a solid foundation for building a reliable, maintainable Personal AI Chatbot with proper error handling, security, and performance considerations.