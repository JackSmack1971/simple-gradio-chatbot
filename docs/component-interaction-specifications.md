# Component Interaction Specifications - Personal AI Chatbot

## Overview

This document specifies the detailed interactions between UI components and backend systems in the Personal AI Chatbot. Each component's interface, data flow, event handling, and error management is documented with code examples and integration patterns.

## Core Architecture

### Component Hierarchy

```
GradioInterface (Main Container)
├── HeaderBar
│   ├── Logo/Title
│   ├── CurrentModelDisplay
│   └── StatusIndicator
├── SidebarPanel
│   ├── NavigationMenu
│   ├── CurrentModelSelector
│   └── ConversationList
├── ChatPanel
│   ├── MessageHistory
│   ├── StreamingIndicator
│   └── MessageActions
├── InputPanel
│   ├── MessageInput
│   ├── SendButton
│   └── CharacterCounter
└── SettingsPanel (Modal)
    ├── APISettings
    ├── UISettings
    └── ModelSettings
```

### Data Flow Patterns

```
UI Component → Event Handler → ChatController → Backend Service → Response → UI Update
     │               │               │               │               │           │
     ▼               ▼               ▼               ▼               ▼           ▼
  User Action    Event Processing  Business Logic   API Call      Data Transform  Visual Feedback
```

## HeaderBar Component

### Purpose
Display application branding, current model, and connection status

### Properties
```typescript
interface HeaderBarProps {
  appTitle: string;
  currentModel: ModelInfo;
  connectionStatus: ConnectionStatus;
  lastActivity: Date;
}
```

### Interactions

**Model Display Update**
```javascript
// When model changes via ChatController.update_model()
headerBar.updateModel = (modelId) => {
  const model = this.getModelInfo(modelId);
  this.currentModelDisplay.text = model.name;
  this.currentModelDisplay.icon = model.icon;
};

// Integration with ChatController
chatController.on('modelChanged', (newModel) => {
  headerBar.updateModel(newModel.id);
});
```

**Status Indicator Updates**
```javascript
// Real-time status updates
statusIndicator.updateStatus = (status) => {
  this.element.className = `status-${status}`;
  this.element.textContent = status.charAt(0).toUpperCase() + status.slice(1);
};

// Connection monitoring
connectionMonitor.onStatusChange = (status) => {
  statusIndicator.updateStatus(status);
  if (status === 'error') {
    statusIndicator.showTooltip('Connection lost. Retrying...');
  }
};
```

## SidebarPanel Component

### Purpose
Navigation, model selection, and conversation management

### Properties
```typescript
interface SidebarPanelProps {
  conversations: ConversationMetadata[];
  availableModels: ModelInfo[];
  currentModel: string;
  isCollapsed: boolean;
}
```

### Model Selector Interactions

**Model Selection Flow**
```javascript
// Model dropdown interaction
modelSelector.onModelSelect = async (modelId) => {
  try {
    // Show loading state
    modelSelector.setLoading(true);

    // Call ChatController
    const success = await chatController.updateModel(modelId);

    if (success) {
      // Update UI
      modelSelector.updateSelectedModel(modelId);
      headerBar.updateModel(modelId);

      // Show success feedback
      this.showNotification('Model switched successfully', 'success');
    } else {
      throw new Error('Model switch failed');
    }
  } catch (error) {
    // Show error and revert
    this.showNotification(error.message, 'error');
    modelSelector.revertSelection();
  } finally {
    modelSelector.setLoading(false);
  }
};
```

**Model Information Display**
```javascript
// Model capabilities display
modelSelector.displayModelInfo = (model) => {
  return `
    <div class="model-info">
      <div class="model-name">${model.name}</div>
      <div class="model-description">${model.description}</div>
      <div class="model-capabilities">
        ${model.capabilities.map(cap => `<span class="capability">${cap}</span>`).join('')}
      </div>
      <div class="model-cost">$${model.pricing.perToken}/1K tokens</div>
    </div>
  `;
};
```

### Conversation Management Interactions

**Load Conversation**
```javascript
// Conversation selection
conversationList.onConversationSelect = async (conversationId) => {
  try {
    // Show loading
    conversationList.setLoading(conversationId, true);

    // Call ChatController
    const success = await chatController.loadConversation(conversationId);

    if (success) {
      // Update chat panel
      chatPanel.loadConversation(conversationId);

      // Update UI state
      this.updateActiveConversation(conversationId);
      this.showNotification('Conversation loaded', 'success');
    }
  } catch (error) {
    this.showNotification(`Failed to load conversation: ${error.message}`, 'error');
  } finally {
    conversationList.setLoading(conversationId, false);
  }
};
```

**Create New Conversation**
```javascript
// New conversation creation
conversationList.onNewConversation = async (title = null) => {
  try {
    // Call ChatController
    const conversationId = await chatController.createNewConversation(title);

    // Update UI
    chatPanel.clearMessages();
    this.addConversationToList({
      id: conversationId,
      title: title || 'New Conversation',
      createdAt: new Date(),
      messageCount: 0
    });

    // Switch to new conversation
    this.updateActiveConversation(conversationId);
  } catch (error) {
    this.showNotification(`Failed to create conversation: ${error.message}`, 'error');
  }
};
```

## ChatPanel Component

### Purpose
Display conversation messages and handle message interactions

### Properties
```typescript
interface ChatPanelProps {
  messages: Message[];
  conversationId: string;
  isStreaming: boolean;
  streamingMessageId: string | null;
}
```

### Message Display Interactions

**Message Rendering**
```javascript
// Message display logic
chatPanel.renderMessage = (message) => {
  const messageElement = document.createElement('div');
  messageElement.className = `message ${message.role}`;
  messageElement.setAttribute('data-message-id', message.id);

  messageElement.innerHTML = `
    <div class="message-header">
      <span class="message-role">${message.role === 'user' ? 'You' : 'Assistant'}</span>
      <time class="message-time" datetime="${message.timestamp}">
        ${this.formatTime(message.timestamp)}
      </time>
    </div>
    <div class="message-content">
      ${this.formatContent(message.content)}
    </div>
    ${message.role === 'assistant' ? this.renderMessageActions(message.id) : ''}
  `;

  return messageElement;
};
```

**Streaming Response Handling**
```javascript
// Streaming response updates
chatPanel.handleStreamingChunk = (chunk, messageId) => {
  const messageElement = this.getMessageElement(messageId);
  const contentElement = messageElement.querySelector('.message-content');

  // Append chunk to existing content
  contentElement.innerHTML += this.formatContent(chunk);

  // Auto-scroll to bottom
  this.scrollToBottom();

  // Update character count if needed
  this.updateStreamingIndicators();
};
```

**Message Actions**
```javascript
// Message action handlers
chatPanel.onMessageAction = (action, messageId) => {
  switch (action) {
    case 'copy':
      this.copyMessageToClipboard(messageId);
      break;
    case 'edit':
      this.enableMessageEditing(messageId);
      break;
    case 'regenerate':
      this.regenerateResponse(messageId);
      break;
    case 'delete':
      this.deleteMessage(messageId);
      break;
  }
};

// Copy message implementation
chatPanel.copyMessageToClipboard = async (messageId) => {
  const message = this.getMessage(messageId);
  try {
    await navigator.clipboard.writeText(message.content);
    this.showNotification('Message copied to clipboard', 'success');
  } catch (error) {
    this.showNotification('Failed to copy message', 'error');
  }
};
```

## InputPanel Component

### Purpose
Handle message composition and sending

### Properties
```typescript
interface InputPanelProps {
  maxLength: number;
  placeholder: string;
  disabled: boolean;
  currentLength: number;
}
```

### Message Sending Interactions

**Send Message Flow**
```javascript
// Send message handler
inputPanel.onSendMessage = async () => {
  const content = this.inputElement.value.trim();

  if (!content) {
    this.showValidationError('Message cannot be empty');
    return;
  }

  if (content.length > this.maxLength) {
    this.showValidationError(`Message too long (max ${this.maxLength} characters)`);
    return;
  }

  try {
    // Disable input during sending
    this.setDisabled(true);

    // Add message to chat immediately
    const tempMessageId = chatPanel.addUserMessage(content);

    // Clear input
    this.clearInput();

    // Send to ChatController
    const success = await chatController.processUserMessage(
      content,
      this.conversationId,
      this.currentModel
    );

    if (success) {
      // Message sent successfully - temp message will be replaced
      this.showNotification('Message sent', 'success');
    } else {
      // Handle failure
      chatPanel.markMessageFailed(tempMessageId);
      this.showValidationError('Failed to send message');
    }
  } catch (error) {
    this.showValidationError(error.message);
  } finally {
    this.setDisabled(false);
    this.focusInput();
  }
};
```

**Input Validation**
```javascript
// Real-time input validation
inputPanel.onInputChange = (value) => {
  // Update character counter
  this.updateCharacterCount(value.length);

  // Visual feedback for limits
  if (value.length > this.maxLength * 0.9) {
    this.setCharacterCountWarning(true);
  } else {
    this.setCharacterCountWarning(false);
  }

  // Enable/disable send button
  this.updateSendButtonState(value.length > 0 && value.length <= this.maxLength);
};
```

**Keyboard Shortcuts**
```javascript
// Keyboard event handling
inputPanel.onKeydown = (event) => {
  if (event.key === 'Enter') {
    if (event.ctrlKey || event.metaKey) {
      // Ctrl+Enter to send
      event.preventDefault();
      this.onSendMessage();
    } else if (!event.shiftKey) {
      // Enter sends message (if not shift+enter for new line)
      event.preventDefault();
      this.onSendMessage();
    }
  } else if (event.key === 'Escape') {
    // Escape to cancel editing or close suggestions
    this.cancelCurrentAction();
  }
};
```

## SettingsPanel Component

### Purpose
Manage application settings and preferences

### Properties
```typescript
interface SettingsPanelProps {
  apiKey: string;
  theme: string;
  fontSize: string;
  defaultModel: string;
  notifications: boolean;
}
```

### Settings Management Interactions

**API Key Management**
```javascript
// API key update
settingsPanel.onApiKeyUpdate = async (newApiKey) => {
  try {
    // Validate format
    if (!this.validateApiKey(newApiKey)) {
      throw new Error('Invalid API key format');
    }

    // Show loading
    this.setApiKeyLoading(true);

    // Update via ConfigManager
    const success = await configManager.setApiKey(newApiKey);

    if (success) {
      // Test connection
      const testSuccess = await this.testApiConnection(newApiKey);

      if (testSuccess) {
        this.showNotification('API key updated successfully', 'success');
        this.closePanel();
      } else {
        throw new Error('API key validation failed');
      }
    } else {
      throw new Error('Failed to save API key');
    }
  } catch (error) {
    this.showValidationError(error.message);
  } finally {
    this.setApiKeyLoading(false);
  }
};
```

**Theme Switching**
```javascript
// Theme change handler
settingsPanel.onThemeChange = (newTheme) => {
  // Apply theme immediately
  document.documentElement.setAttribute('data-theme', newTheme);

  // Save preference
  configManager.setSetting('theme', newTheme);

  // Update UI elements
  this.updateThemePreview(newTheme);

  // Show confirmation
  this.showNotification(`Theme changed to ${newTheme}`, 'success');
};
```

## Error Handling and Recovery

### Global Error Handler

```javascript
// Global error handling
class ErrorHandler {
  static handleApiError(error, context) {
    switch (error.type) {
      case 'RATE_LIMIT':
        return {
          message: 'Rate limit exceeded. Please wait before trying again.',
          actions: ['retry', 'upgrade'],
          retryDelay: error.retryAfter
        };

      case 'AUTHENTICATION':
        return {
          message: 'API key is invalid or expired.',
          actions: ['settings', 'help'],
          severity: 'high'
        };

      case 'NETWORK':
        return {
          message: 'Network connection lost.',
          actions: ['retry', 'offline'],
          autoRetry: true
        };

      default:
        return {
          message: 'An unexpected error occurred.',
          actions: ['retry', 'report'],
          severity: 'medium'
        };
    }
  }
}
```

### Component-Specific Error Handling

**ChatPanel Error States**
```javascript
// Message failure handling
chatPanel.handleMessageFailure = (messageId, error) => {
  const messageElement = this.getMessageElement(messageId);

  // Add error styling
  messageElement.classList.add('message-error');

  // Show error message
  const errorElement = document.createElement('div');
  errorElement.className = 'message-error-text';
  errorElement.textContent = error.message;
  messageElement.appendChild(errorElement);

  // Add retry button
  const retryButton = document.createElement('button');
  retryButton.textContent = 'Retry';
  retryButton.onclick = () => this.retryMessage(messageId);
  messageElement.appendChild(retryButton);
};
```

## State Management Integration

### Application State Updates

```javascript
// State management integration
class StateManager {
  // Update application state
  updateState(updates) {
    // Merge updates
    this.state = { ...this.state, ...updates };

    // Notify components
    this.notifyComponents(updates);

    // Persist to storage
    this.persistState();
  }

  // Component notification
  notifyComponents(updates) {
    if (updates.currentModel) {
      headerBar.updateModel(updates.currentModel);
      sidebarPanel.updateCurrentModel(updates.currentModel);
    }

    if (updates.conversationId) {
      chatPanel.loadConversation(updates.conversationId);
      sidebarPanel.updateActiveConversation(updates.conversationId);
    }

    if (updates.connectionStatus) {
      headerBar.updateConnectionStatus(updates.connectionStatus);
    }
  }
}
```

### Event Bus Implementation

```javascript
// Event-driven architecture
class EventBus {
  constructor() {
    this.listeners = {};
  }

  // Subscribe to events
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  // Emit events
  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  // Remove listeners
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(
        listener => listener !== callback
      );
    }
  }
}

// Usage
const eventBus = new EventBus();

// Component subscriptions
eventBus.on('messageSent', (data) => chatPanel.addMessage(data));
eventBus.on('modelChanged', (data) => headerBar.updateModel(data.modelId));
eventBus.on('error', (data) => errorHandler.showError(data));
```

## Performance Optimization

### Lazy Loading

```javascript
// Lazy load components
class LazyLoader {
  static async loadComponent(componentName) {
    try {
      const module = await import(`./components/${componentName}.js`);
      return module.default;
    } catch (error) {
      console.error(`Failed to load component ${componentName}:`, error);
      return null;
    }
  }
}

// Usage
const SettingsPanel = await LazyLoader.loadComponent('SettingsPanel');
```

### Virtual Scrolling for Messages

```javascript
// Virtual scrolling implementation
class VirtualScroller {
  constructor(container, itemHeight, totalItems) {
    this.container = container;
    this.itemHeight = itemHeight;
    this.totalItems = totalItems;
    this.visibleItems = Math.ceil(container.clientHeight / itemHeight);
    this.scrollTop = 0;
  }

  // Update visible items on scroll
  onScroll() {
    const startIndex = Math.floor(this.scrollTop / this.itemHeight);
    const endIndex = Math.min(startIndex + this.visibleItems, this.totalItems);

    // Render only visible items
    this.renderItems(startIndex, endIndex);
  }
}
```

### Memory Management

```javascript
// Component cleanup
class ComponentManager {
  static cleanup(component) {
    // Remove event listeners
    if (component.eventListeners) {
      component.eventListeners.forEach(({ element, event, handler }) => {
        element.removeEventListener(event, handler);
      });
    }

    // Clear timers
    if (component.timers) {
      component.timers.forEach(clearTimeout);
    }

    // Clear references
    component.element = null;
    component.props = null;
  }
}
```

---

*These specifications provide the detailed interaction patterns for all UI components, ensuring proper integration with the ChatController and backend systems while maintaining optimal performance and user experience.*