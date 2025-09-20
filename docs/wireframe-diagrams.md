# Wireframe Diagrams - Personal AI Chatbot

## Overview

This document contains detailed wireframe diagrams for all interface components of the Personal AI Chatbot. Wireframes are presented in ASCII art format with detailed annotations and specifications for implementation.

## Main Interface Layout

### Desktop Layout (1024px+)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Personal AI Chatbot                                            🤖 GPT-4 ⚡ Online │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐ │
│ │ NAVIGATION                          │ │ CHAT AREA                           │ │
│ │ ├─────────────────────────────────┤ │ │ 💬 Project Ideas - GPT-4             │ │
│ │ │ 💬 Conversations               │ │ │ ├───────────────────────────────────┤ │ │
│ │ │ ⚙️  Settings                   │ │ │ │                                     │ │
│ │ │ 🤖 Models                      │ │ │ │ [User] How can I improve my        │ │
│ │ └─────────────────────────────────┘ │ │ │         coding skills?             │ │
│ │                                     │ │ │ │ [12:30 PM]                       │ │
│ │ CURRENT MODEL                       │ │ │ │                                     │ │
│ │ ┌─────────────────────────────────┐ │ │ │ │ [AI] Here are several effective  │ │
│ │ │ [Model Selector ▼]             │ │ │ │ │      strategies for improving     │ │
│ │ │ ├─────────────────────────────┤ │ │ │ │ │      your coding skills:         │ │
│ │ │ │ GPT-4                       │ │ │ │ │ │                                   │ │
│ │ │ │ Claude-3                    │ │ │ │ │ │ 1. Practice regularly...         │ │
│ │ │ │ Gemini Pro                  │ │ │ │ │ │                                   │ │
│ │ │ └─────────────────────────────┘ │ │ │ │ [12:30 PM] ┌─────┐ ┌────┐ ┌─────┐ │ │
│ │ │                                 │ │ │ │             │Copy │ │Edit│ │Regen│ │ │
│ │ │ 💡 Fast responses              │ │ │ │             └─────┘ └────┘ └─────┘ │ │
│ │ │ 💰 $0.002/1K tokens            │ │ │ │                                     │ │
│ │ │ 🎯 Code generation             │ │ │ │ [User] What about pair programming?│ │
│ │ └─────────────────────────────────┘ │ │ │ [12:31 PM]                       │ │
│ │                                     │ │ │                                     │ │
│ │ CONVERSATIONS                       │ │ │ [AI] [Generating response...]     │ │
│ │ ┌─────────────────────────────────┐ │ │ │                                     │ │
│ │ │ ➕ New Conversation             │ │ │ └───────────────────────────────────┘ │ │
│ │ │ ├─────────────────────────────┤ │ │ ├─────────────────────────────────────┤ │
│ │ │ │ 💬 Project Ideas             │ │ │ │ Type your message...                │ │
│ │ │ │ 💬 Code Review               │ │ │ │                                     │ │
│ │ │ │ 💬 Research Notes            │ │ │ │ [Character counter: 0/2000]         │ │
│ │ │ └─────────────────────────────┘ │ │ └─────────────────────────────────────┘ │ │
│ └─────────────────────────────────────┘ └─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [🎤 Voice] [📎 Attach] [⚙️ Options] [📤 Send]                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Tablet Layout (768px-1023px)

```
┌─────────────────────────────────────────────────────────────────┐
│ Personal AI Chatbot                            🤖 GPT-4 ⚡ Online │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 💬 Project Ideas - GPT-4                                   │ │
│ │ ├─────────────────────────────────────────────────────────┤ │
│ │ │                                                         │ │
│ │ │ [User] How can I improve my coding skills?              │ │
│ │ │ [12:30 PM]                                              │ │
│ │ │                                                         │ │
│ │ │ [AI] Here are several effective strategies...           │ │
│ │ │ [12:30 PM] ┌─────┐ ┌────┐ ┌─────┐                       │ │
│ │ │             │Copy │ │Edit│ │Regen│                       │ │
│ │ │             └─────┘ └────┘ └─────┘                       │ │
│ │ │                                                         │ │
│ │ │ [User] What about pair programming?                     │ │
│ │ │ [12:31 PM]                                              │ │
│ │ │                                                         │ │
│ │ │ [AI] [Generating response...]                           │ │
│ │ └─────────────────────────────────────────────────────────┘ │
│ │ ├─────────────────────────────────────────────────────────┤ │
│ │ │ Type your message...                                    │ │
│ │ │                                                         │ │
│ │ │ [Character counter: 0/2000]                             │ │
│ │ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ [🎤 Voice] [📎 Attach] [⚙️ Options] [📤 Send]                 │
├─────────────────────────────────────────────────────────────────┤
│ [☰ Menu]                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (320px-767px)

```
┌─────────────────────────────────┐
│ 🤖 GPT-4 ⚡ Online               │
├─────────────────────────────────┤
│                                 │
│ [User] How can I improve my     │
│         coding skills?          │
│ [12:30 PM]                      │
│                                 │
│ [AI] Here are several effective │
│      strategies for improving   │
│      your coding skills:        │
│                                 │
│ 1. Practice regularly...        │
│                                 │
│ [12:30 PM] ┌─────┐ ┌────┐ ┌─────┐
│             │Copy │ │Edit│ │Regen│
│             └─────┘ └────┘ └─────┘
│                                 │
│ [User] What about pair          │
│         programming?            │
│ [12:31 PM]                      │
│                                 │
│ [AI] [Generating response...]   │
│                                 │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ Type your message...            │
│                                 │
│ [0/2000]                        │
├─────────────────────────────────┤
│ [🎤] [📎] [⚙️] [📤 Send]        │
├─────────────────────────────────┤
│ [☰ Menu]                        │
└─────────────────────────────────┘
```

## Component Wireframes

### 1. Header Bar Component

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────┐ ┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐ │
│ │  Logo   │ │ Personal AI Chatbot │ │ 🤖 GPT-4        │ │ ⚡ Online           │ │
│ │  [Icon] │ │                     │ │ [Model Dropdown]│ │ [Status Indicator] │ │
│ └─────────┘ └─────────────────────┴───────────────────┴───────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Specifications**:
- Height: 60px
- Logo: 40px x 40px, clickable
- Title: 24px font, left-aligned
- Model: 16px font, clickable dropdown
- Status: 14px font, color-coded (green=online, yellow=connecting, red=offline)
- Background: Primary brand color with subtle gradient

### 2. Sidebar Panel Component

```
┌─────────────────────────────────────┐
│ NAVIGATION                          │
│ ├─────────────────────────────────┤ │
│ │ ┌───┐ 💬 Conversations          │ │
│ │ └───┘                           │ │
│ │ ┌───┐ ⚙️  Settings              │ │
│ │ └───┘                           │ │
│ │ ┌───┐ 🤖 Models                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ CURRENT MODEL                       │
│ ┌─────────────────────────────────┐ │
│ │ [Model Selector ▼]             │ │
│ │ ├─────────────────────────────┤ │ │
│ │ │ 🤖 GPT-4                    │ │ │
│ │ │ 🤖 Claude-3                 │ │ │
│ │ │ 🤖 Gemini Pro               │ │ │
│ │ │ 🤖 Llama 2                  │ │ │
│ │ └─────────────────────────────┘ │ │
│ │                                 │ │
│ │ 💡 Fast responses              │ │
│ │ 💰 $0.002/1K tokens            │ │
│ │ 🎯 Code generation             │ │
│ │ 🌟 Best for chat               │ │
│ └─────────────────────────────────┘ │
│                                     │
│ CONVERSATIONS                       │
│ ┌─────────────────────────────────┐ │
│ │ ┌───┐ ➕ New Conversation       │ │
│ │ └───┘                           │ │
│ │ ├─────────────────────────────┤ │ │
│ │ │ 💬 Project Ideas             │ │
│ │ │     2 hours ago              │ │
│ │ │ ├─────────────────────────┤ │ │
│ │ │ 💬 Code Review               │ │
│ │ │     Yesterday                │ │
│ │ │ ├─────────────────────────┤ │ │
│ │ │ 💬 Research Notes            │ │
│ │ │     3 days ago               │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Specifications**:
- Width: 280px (desktop), full width (mobile overlay)
- Navigation: Icon + text, 44px height each
- Model selector: Dropdown with 200px width
- Model info: 4-5 capability indicators
- Conversation list: Title + timestamp, 60px height each
- Scrollable when content exceeds viewport

### 3. Chat Panel Component

```
┌─────────────────────────────────────┐
│ 💬 Project Ideas - GPT-4             │
│ ├───────────────────────────────────┤ │
│ │                                   │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ [Avatar] User                   │ │ │
│ │ │                                 │ │ │
│ │ │ How can I improve my coding     │ │ │
│ │ │ skills?                         │ │ │
│ │ │                                 │ │ │
│ │ │ [12:30 PM]                      │ │ │
│ │ └─────────────────────────────────┘ │ │
│ │                                   │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ 🤖 Assistant                    │ │ │
│ │ │                                 │ │ │
│ │ │ Here are several effective      │ │ │
│ │ │ strategies for improving your   │ │ │
│ │ │ coding skills:                  │ │ │
│ │ │                                 │ │ │
│ │ │ 1. Practice regularly with      │ │ │
│ │ │    small projects               │ │ │
│ │ │                                 │ │ │
│ │ │ 2. Learn from others through    │ │ │
│ │ │    code reviews                 │ │ │
│ │ │                                 │ │ │
│ │ │ [12:30 PM] ┌─────┐ ┌────┐ ┌─────┐ │ │
│ │             │Copy │ │Edit│ │Regen│ │ │
│ │             └─────┘ └────┘ └─────┘ │ │
│ │                                   │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ [Avatar] User                   │ │ │
│ │ │                                 │ │ │
│ │ │ What about pair programming?    │ │ │
│ │ │                                 │ │ │
│ │ │ [12:31 PM]                      │ │ │
│ │ └─────────────────────────────────┘ │ │
│ │                                   │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ 🤖 Assistant                    │ │ │
│ │ │                                 │ │ │
│ │ │ [Generating response...]        │ │ │
│ │ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ │ │
│ │ └─────────────────────────────────┘ │ │
│ │                                   │ │
│ └───────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Specifications**:
- Conversation header: Title + model, 50px height
- Message bubbles: Rounded corners, max 80% width
- User messages: Right-aligned, light blue background
- AI messages: Left-aligned, light gray background
- Timestamps: 12px font, subtle color
- Action buttons: 32px height, appear on hover/focus
- Streaming indicator: Animated dots or progress bar
- Auto-scroll: To bottom on new messages

### 4. Input Panel Component

```
┌─────────────────────────────────────┐
│ ┌─────────────────────────────────┐ │
│ │ Type your message...            │ │
│ │                                 │ │
│ │                                 │ │
│ │                                 │ │
│ │                                 │ │
│ │ [Character counter: 0/2000]     │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────────┐ │
│ │🎤   │ │📎   │ │⚙️   │ │ 📤 Send  │ │
│ │Voice│ │Attach│ │Options│ │         │ │
│ └─────┘ └─────┘ └─────┘ └─────────┘ │
└─────────────────────────────────────┘
```

**Specifications**:
- Input area: Multi-line textarea, auto-resize
- Minimum height: 80px, maximum: 200px
- Character counter: Right-aligned, red when near limit
- Toolbar buttons: 44px x 44px, disabled when not available
- Send button: Primary color, disabled when input empty
- Placeholder text: "Type your message..." (changes based on context)

### 5. Settings Panel Component

```
┌─────────────────────────────────────┐
│ ⚙️ Settings                          │
│ ├───────────────────────────────────┤ │
│ │ API CONFIGURATION                 │ │
│ │ ├────────────────────────────────┤ │ │
│ │ │ API Key: ************abcd      │ │ │
│ │ │ ├────────────────────────────┤ │ │ │
│ │ │ │ [Update API Key]            │ │ │
│ │ │ └────────────────────────────┤ │ │ │
│ │ │                                │ │ │
│ │ │ Timeout: [ 30 ] seconds        │ │ │
│ │ │ Retry: [ 3 ] times             │ │ │
│ │ └────────────────────────────────┤ │ │
│ │                                  │ │ │
│ │ UI PREFERENCES                   │ │ │
│ │ ├────────────────────────────────┤ │ │ │
│ │ │ Theme: [Dark ▼]                │ │ │
│ │ │ ├────────────────────────────┤ │ │ │
│ │ │ │ Light                       │ │ │
│ │ │ │ Dark                        │ │ │
│ │ │ │ Auto                        │ │ │
│ │ │ └────────────────────────────┤ │ │ │
│ │ │                                │ │ │
│ │ │ Font Size: [Medium ▼]          │ │ │
│ │ │ ├────────────────────────────┤ │ │ │
│ │ │ │ Small                       │ │ │
│ │ │ │ Medium                      │ │ │
│ │ │ │ Large                       │ │ │
│ │ │ └────────────────────────────┤ │ │ │
│ │ │                                │ │ │
│ │ │ [ ] Enable notifications       │ │ │
│ │ │ [ ] Auto-save conversations    │ │ │
│ │ │ [x] Show timestamps            │ │ │
│ │ └────────────────────────────────┤ │ │
│ │                                  │ │ │
│ │ MODEL PREFERENCES                │ │ │
│ │ ├────────────────────────────────┤ │ │ │
│ │ │ Default Model: [GPT-4 ▼]       │ │ │
│ │ │ ├────────────────────────────┤ │ │ │
│ │ │ │ GPT-4                       │ │ │
│ │ │ │ Claude-3                    │ │ │
│ │ │ │ Gemini Pro                  │ │ │
│ │ │ └────────────────────────────┤ │ │ │
│ │ │                                │ │ │
│ │ │ Temperature: [0.7]             │ │ │
│ │ │ Max Tokens: [4096]             │ │ │
│ │ └────────────────────────────────┤ │ │
│ ├───────────────────────────────────┤ │
│ │ [Save Settings] [Reset to Default] │ │
│ └───────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Specifications**:
- Modal overlay or slide-out panel
- Section headers: 16px font, bold
- Form controls: Consistent spacing and alignment
- Dropdowns: 200px width, 32px height
- Checkboxes: 20px x 20px with labels
- Action buttons: Primary/secondary styling
- Validation feedback: Inline error messages

### 6. Model Selector Component

```
┌─────────────────────────────────────┐
│ 🤖 Select AI Model                   │
│ ├───────────────────────────────────┤ │
│ │ ┌────────────────────────────────┐ │ │
│ │ │ [Search models...]             │ │ │
│ │ └────────────────────────────────┘ │ │
│ │                                    │ │
│ │ ┌────────────────────────────────┐ │ │
│ │ │ 🤖 GPT-4                       │ │ │
│ │ │    OpenAI's flagship model     │ │ │
│ │ │    💡 Smart 💰 $0.002/1K 🎯 Chat│ │ │
│ │ │ ├────────────────────────────┤ │ │ │
│ │ │ │ Select                      │ │ │
│ │ │ └────────────────────────────┤ │ │ │
│ │ └────────────────────────────────┘ │ │
│ │                                    │ │
│ │ ┌────────────────────────────────┐ │ │
│ │ │ 🤖 Claude-3                    │ │ │
│ │ │    Anthropic's helpful model   │ │ │
│ │ │    💡 Fast 💰 $0.001/1K 🎯 Code │ │ │
│ │ │ ├────────────────────────────┤ │ │ │
│ │ │ │ Select                      │ │ │
│ │ │ └────────────────────────────┤ │ │ │
│ │ └────────────────────────────────┘ │ │
│ │                                    │ │
│ │ ┌────────────────────────────────┐ │ │
│ │ │ 🤖 Gemini Pro                  │ │ │
│ │ │    Google's multimodal model   │ │ │
│ │ │    💡 Creative 💰 $0.001/1K 🌟 Art│ │ │
│ │ │ ├────────────────────────────┤ │ │ │
│ │ │ │ Select                      │ │ │
│ │ │ └────────────────────────────┤ │ │ │
│ │ └────────────────────────────────┘ │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Specifications**:
- Modal dialog: 500px width, 600px height
- Search field: Full width, real-time filtering
- Model cards: 100% width, 120px height each
- Model info: Name, description, capability icons
- Pricing: Per 1K tokens, color-coded
- Select button: Primary styling, loading state

### 7. Conversation Manager Component

```
┌─────────────────────────────────────┐
│ 💬 Conversations                     │
│ ├───────────────────────────────────┤ │
│ │ ┌────────────────────────────────┐ │ │
│ │ │ [Search conversations...]      │ │ │
│ │ └────────────────────────────────┘ │ │
│ │                                    │ │
│ │ ┌───┐ ➕ New Conversation          │ │
│ │ └───┘                              │ │
│ │ ├────────────────────────────────┤ │ │
│ │ │ ┌────────────────────────────┐ │ │ │
│ │ │ │ 💬 Project Ideas           │ │ │ │
│ │ │ │ 2 hours ago • 15 messages  │ │ │ │
│ │ │ │ ├────────────────────────┤ │ │ │ │
│ │ │ │ │ How can I improve my... │ │ │ │ │
│ │ │ │ └────────────────────────┤ │ │ │ │
│ │ │ │ ├────────────────────────┤ │ │ │ │
│ │ │ │ │ [Load] [Delete]         │ │ │ │ │
│ │ │ │ └────────────────────────┤ │ │ │ │
│ │ │ └────────────────────────────┘ │ │ │
│ │ │                                  │ │ │
│ │ │ ┌────────────────────────────┐ │ │ │ │
│ │ │ │ 💬 Code Review             │ │ │ │ │
│ │ │ │ Yesterday • 8 messages     │ │ │ │ │
│ │ │ │ ├────────────────────────┤ │ │ │ │ │
│ │ │ │ │ Please review this...   │ │ │ │ │
│ │ │ │ └────────────────────────┤ │ │ │ │ │
│ │ │ │ ├────────────────────────┤ │ │ │ │ │
│ │ │ │ │ [Load] [Delete]         │ │ │ │ │ │
│ │ │ │ └────────────────────────┤ │ │ │ │ │
│ │ │ └────────────────────────────┘ │ │ │ │
│ │ └────────────────────────────────┤ │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Specifications**:
- List view: Scrollable, 400px height
- Search: Real-time filtering by title/content
- Conversation cards: 100% width, 100px height each
- Metadata: Timestamp, message count
- Preview: First message snippet (100 chars)
- Actions: Load (primary), Delete (destructive)
- Empty state: Illustration + "No conversations yet"

### 8. Error States and Loading Components

#### Loading Spinner
```
┌─────────────────────────────────────┐
│                                     │
│           ⭕⭕⭕⭕⭕                │
│         ⭕        ⭕              │
│       ⭕   LOADING   ⭕            │
│         ⭕        ⭕              │
│           ⭕⭕⭕⭕⭕                │
│                                     │
│    Generating response...           │
│                                     │
└─────────────────────────────────────┘
```

#### Error Message
```
┌─────────────────────────────────────┐
│ ⚠️  Error                            │
│ ├───────────────────────────────────┤ │
│ │ Failed to send message            │ │
│ │                                   │ │
│ │ The API request timed out.        │ │
│ │ Please try again.                 │ │
│ │                                   │ │
│ │ ┌─────────┐ ┌─────────┐           │ │
│ │ │  Retry  │ │ Settings │           │ │
│ │ └─────────┘ └─────────┘           │ │
│ └───────────────────────────────────┘ │
└─────────────────────────────────────┘
```

#### Success Confirmation
```
┌─────────────────────────────────────┐
│ ✅ Success                           │
│ ├───────────────────────────────────┤ │
│ │ Conversation saved successfully   │ │
│ │                                   │ │
│ │ Your conversation has been saved  │ │
│ │ and can be accessed later.        │ │
│ │                                   │ │
│ │ ┌─────────┐                       │ │
│ │ │   OK    │                       │ │
│ │ └─────────┘                       │ │
└─────────────────────────────────────┘
```

## Interaction States

### Button States
```
Normal:     ┌─────────┐    Hover:      ┌─────────┐    Pressed:    ┌─────────┐
            │  Send   │               │  Send   │               │  Send   │
            └─────────┘               └─────────┘               └─────────┘

Disabled:   ┌─────────┐    Loading:    ┌─────────┐
            │  Send   │               │ ⭕ Send  │
            └─────────┘               └─────────┘
```

### Form States
```
Normal:     ┌─────────────────────────────┐
            │ Type your message...        │
            └─────────────────────────────┘

Focused:    ┌─────────────────────────────┐
            │ Type your message...        │
            └─────────────────────────────┘
                   [blue border]

Error:      ┌─────────────────────────────┐
            │ Type your message...        │
            └─────────────────────────────┘
                   [red border]
            Message cannot be empty

Success:    ┌─────────────────────────────┐
            │ Type your message...        │
            └─────────────────────────────┘
                   [green border]
```

### Message States
```
Normal:     ┌─────────────────────────────────┐
            │ [AI] This is a response...     │
            └─────────────────────────────────┘

Streaming:  ┌─────────────────────────────────┐
            │ [AI] This is a response... ░░░  │
            └─────────────────────────────────┘

Error:      ┌─────────────────────────────────┐
            │ [AI] Failed to generate...      │
            │ ┌─────┐                         │
            │ │Retry│                         │
            │ └─────┘                         │
            └─────────────────────────────────┘
```

## Responsive Breakpoints

### Desktop (1024px+)
- Full three-column layout
- Sidebar: 280px fixed width
- Chat area: Flexible width
- Input: Full width with toolbar

### Tablet (768px-1023px)
- Two-column layout (hamburger menu hides sidebar)
- Sidebar: Overlay mode, 320px width
- Chat area: 100% width when sidebar hidden
- Input: Condensed toolbar

### Mobile (320px-767px)
- Single column layout
- Sidebar: Full screen overlay
- Chat area: 100% width, message bubbles stack
- Input: Bottom-fixed with simplified toolbar

## Color Scheme and Typography

### Color Palette
```
Primary:     #2563eb (Blue)
Secondary:   #64748b (Gray)
Success:     #10b981 (Green)
Error:       #ef4444 (Red)
Warning:     #f59e0b (Yellow)
Background:  #ffffff (White)
Text:        #1f2937 (Dark Gray)
Border:      #e5e7eb (Light Gray)
```

### Typography Scale
```
H1: 32px / 40px (Bold)
H2: 24px / 32px (Bold)
H3: 20px / 28px (Bold)
Body: 16px / 24px (Regular)
Small: 14px / 20px (Regular)
Caption: 12px / 16px (Regular)
```

### Component Spacing
```
Component margin: 16px
Element spacing: 8px
Content padding: 16px
Border radius: 8px
Border width: 1px
```

---

*These wireframes provide the visual blueprint for implementing the Gradio interface. All measurements are in pixels and should be adapted for different screen densities.*