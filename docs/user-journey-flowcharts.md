# User Journey Flowcharts - Personal AI Chatbot

## Overview

This document contains detailed flowcharts for the primary user journeys in the Personal AI Chatbot application. Flowcharts are presented in ASCII art format with decision points, success/failure paths, and interaction details.

## Primary Chat Flow

```
┌─────────────────┐
│   App Launch    │
│   (Desktop)     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│  Load Gradio    │────▶│   Welcome Screen │
│   Interface     │     │   (First Time)  │
│   (< 3 sec)     │     └─────────┬───────┘
└─────────────────┘               │
          │                       ▼
          │             ┌─────────────────┐
          │             │  API Key Setup  │
          │             │   (Required)    │
          │             └─────────┬───────┘
          │                       │
          │                       ▼
          │             ┌─────────────────┐     ┌─────────────────┐
          │             │  Key Validation │────▶│   Error: Invalid│
          │             │   (Format/API)  │     │     API Key     │
          │             └─────────┬───────┘     └─────────┬───────┘
          │                       │                       │
          │                       ▼                       ▼
          │             ┌─────────────────┐     ┌─────────────────┐
          │             │   Key Stored    │     │   Retry Input   │
          │             │   Securely      │     │   (Clear Error) │
          │             └─────────────────┘     └─────────────────┘
          │                       │                       │
          │                       └───────────────────────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│  Chat Interface │────▶│   Input Field   │
│    Loads        │     │   Focused       │
│   (< 2 sec)     │     └─────────┬───────┘
└─────────────────┘               │
                                  ▼
                        ┌─────────────────┐
                        │   User Types    │
                        │   Message       │
                        │   (Real-time    │
                        │    counter)     │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Send Button   │────▶│   Button State  │
                        │   Enabled       │     │   Changes       │
                        └─────────┬───────┘     └─────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   User Clicks   │
                        │   Send or       │
                        │   Presses Enter │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐     ┌─────────────────┐
│  Message Sent   │────▶│   UI Updates    │
│   to Chat Area  │     │   Immediately   │
└─────────┬───────┘     └─────────────────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│  Loading State  │────▶│   "AI is        │
│   Appears       │     │   thinking..."  │
└─────────┬───────┘     └─────────────────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│  API Request    │────▶│   ChatController│
│   Initiated     │     │   .send_message()│
│   (OpenRouter)  │     └─────────┬───────┘
└─────────────────┘               │
                                  ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Success Path  │────▶│   Response      │
                        │   (< 10 sec)    │     │   Received      │
                        └─────────┬───────┘     └─────────┬───────┘
                                  │                       │
                                  ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Error Path    │────▶│   API Error     │
                        │   (Timeout/Rate │     │   Handling      │
                        │    Limit/Auth)  │     └─────────┬───────┘
                        └─────────────────┘               │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Error Message │
                                                │   Displayed     │
                                                │   (Clear,       │
                                                │    Actionable)  │
                                                └─────────┬───────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   User Options  │
                                                │   - Retry       │
                                                │   - Change Model│
                                                │   - Check API   │
                                                └─────────────────┘
```

## Model Selection and Switching Flow

```
┌─────────────────┐
│  Current Model  │
│   Displayed     │
│   (Header/Sidebar│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│  User Clicks    │────▶│   Model Button  │
│   Model Button  │     │   (Dropdown)    │
└─────────┬───────┘     └─────────────────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│  Model List     │────▶│   Available     │
│   Loads         │     │   Models        │
│   (< 1 sec)     │     └─────────┬───────┘
└─────────────────┘               │
                                  ▼
                        ┌─────────────────┐
                        │   Model Info    │
                        │   Displayed     │
                        │   - Name        │
                        │   - Description │
                        │   - Cost/Token  │
                        │   - Capabilities│
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   User Selects  │────▶│   New Model     │
                        │   Different     │     │   Selected      │
                        │   Model         │     └─────────┬───────┘
                        └─────────────────┘               │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Loading State │
                                                │   "Switching    │
                                                │    model..."    │
                                                └─────────┬───────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Validation    │
                                                │   Check         │
                                                │   (API Test)    │
                                                └─────────┬───────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Success       │────▶│   Model Updated │────▶│   UI Updates    │
│   (< 2 sec)     │     │   in Controller │     │   - Header      │
│                 │     └─────────────────┘     │   - Sidebar     │
│                 │                             │   - Status      │
└─────────────────┘                             └─────────────────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Error         │────▶│   Validation    │
│   Path          │     │   Failed        │
└─────────────────┘     └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Error Message │
                        │   - Model       │
                        │     unavailable │
                        │   - API error   │
                        │   - Rate limit  │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   User Options  │
                        │   - Try again   │
                        │   - Select      │
                        │     different   │
                        │     model       │
                        │   - Keep        │
                        │     current     │
                        └─────────────────┘
```

## Conversation Management Flow

```
┌─────────────────┐
│   Current       │
│   Conversation  │
│   Active        │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   User Wants to │────▶│   Access        │
│   Manage        │     │   Conversations │
│   Conversations │     └─────────┬───────┘
└─────────────────┘               │
                                  ▼
                        ┌─────────────────┐
                        │   Click         │
                        │   Conversations │
                        │   (Sidebar)     │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐     ┌─────────────────┐
│   Conversation   │────▶│   List Loads    │
│   Panel Opens   │     │   (< 2 sec)     │
│   (Modal/Slide) │     └─────────┬───────┘
└─────────────────┘               │
                                  ▼
                        ┌─────────────────┐
                        │   Conversations │
                        │   Displayed     │
                        │   - Title       │
                        │   - Last        │
                        │     modified   │
                        │   - Message     │
                        │     count      │
                        │   - Preview     │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Action   │────▶│   Load Existing │────▶│   Select        │
│   Decision      │     │   Conversation  │     │   Conversation  │
└─────────────────┘     └─────────┬───────┘     └─────────┬───────┘
                                  │                       │
                                  ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Loading State │     │   Preview       │
                        │   "Loading..."  │     │   Displayed     │
                        └─────────┬───────┘     └─────────┬───────┘
                                  │                       │
                                  ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Load Request  │     │   User Confirms │
                        │   to Controller │     │   Load          │
                        └─────────┬───────┘     └─────────┬───────┘
                                  │                       │
                                  ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Success       │────▶│   Current       │────▶│   Conversation  │
│   (< 5 sec)     │     │   Conversation  │     │   Replaced      │
│                 │     │   Backed Up     │     │   in UI         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Error         │────▶│   Load Failed   │
│   Path          │     │   - File not    │
│                 │     │     found       │
│                 │     │   - Corrupted   │
│                 │     │   - Permission  │
└─────────────────┘     └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Error Message │
                        │   with Options  │
                        │   - Try again   │
                        │   - Select      │
                        │     different  │
                        │   - Create new  │
                        └─────────────────┘
```

## Settings Configuration Flow

```
┌─────────────────┐
│   User Needs to │
│   Configure     │
│   Settings      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Access        │────▶│   Settings      │
│   Settings      │     │   Panel         │
│   (Sidebar)     │     └─────────┬───────┘
└─────────────────┘               │
                                  ▼
                        ┌─────────────────┐
                        │   Settings      │
                        │   Panel Loads   │
                        │   (< 1 sec)     │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Settings      │
                        │   Categories    │
                        │   - API         │
                        │   - UI          │
                        │   - Model       │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Selects  │────▶│   API Settings  │────▶│   API Key       │
│   Category      │     │   Section       │     │   Management    │
└─────────────────┘     └─────────┬───────┘     └─────────┬───────┘
                                  │                       │
                                  ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Current Key   │     │   Update Key    │
                        │   Displayed     │     │   Process       │
                        │   (Masked)      │     └─────────┬───────┘
                        └─────────────────┘               │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Key Input     │
                                                │   Field         │
                                                └─────────┬───────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   User Enters   │
                                                │   New Key       │
                                                └─────────┬───────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐     ┌─────────────────┐
                                                │   Validation    │────▶│   Valid Key     │
                                                │   Check         │     │   Format        │
                                                └─────────┬───────┘     └─────────┬───────┘
                                                          │                       │
                                                          ▼                       ▼
                                                ┌─────────────────┐     ┌─────────────────┐
                                                │   Invalid Key   │     │   API Test      │
                                                │   - Format       │     │   Connection   │
                                                │   - Required     │     └─────────┬───────┘
                                                └─────────┬───────┘               │
                                                          │                       ▼
                                                          ▼             ┌─────────────────┐
                                                ┌─────────────────┐     │   Success       │
                                                │   Error Message │     │   - Key stored  │
                                                │   Displayed     │     │   - Encrypted   │
                                                │   - Clear        │     │   - UI updated  │
                                                │   - Actionable   │     └─────────────────┘
                                                └─────────────────┘
```

## Error Recovery Flow

```
┌─────────────────┐
│   Error Occurs  │
│   During Use    │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Error Type    │────▶│   API Error     │
│   Detection     │     │   - Timeout     │
│                 │     │   - Rate limit  │
│                 │     │   - Auth failed │
└─────────────────┘     └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Error State   │
                        │   UI Updates    │
                        │   - Loading     │
                        │     stops       │
                        │   - Error       │
                        │     message     │
                        │   - Action      │
                        │     buttons     │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Error Message │
                        │   Displayed     │
                        │   - Clear       │
                        │   - Specific    │
                        │   - Actionable  │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Response │────▶│   Automatic     │────▶│   Retry Logic   │
│   Options       │     │   Retry         │     │   (3 attempts)  │
└─────────────────┘     └─────────┬───────┘     └─────────┬───────┘
                                  │                       │
                                  ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Manual Retry  │     │   Success       │
                        │   Button        │     └─────────┬───────┘
                        └─────────┬───────┘               │
                                  │                       ▼
                                  ▼             ┌─────────────────┐
                        ┌─────────────────┐     │   Normal        │
                        │   User Clicks   │     │   Operation     │
                        │   Retry         │     │   Resumes       │
                        └─────────┬───────┘     └─────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Alternative   │
                        │   Actions       │
                        │   - Change      │
                        │     model       │
                        │   - Check       │
                        │     settings    │
                        │   - Contact     │
                        │     support     │
                        └─────────────────┘
```

## Onboarding Flow for New Users

```
┌─────────────────┐
│   First Launch  │
│   Detected      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Welcome       │────▶│   Onboarding    │
│   Screen        │     │   Modal         │
│   Appears       │     └─────────┬───────┘
└─────────────────┘               │
                                  ▼
                        ┌─────────────────┐
                        │   Step 1:       │
                        │   Introduction  │
                        │   - App purpose │
                        │   - Key features│
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Step 2:       │
                        │   API Setup     │
                        │   - Instructions│
                        │   - Key input   │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Key Validation│────▶│   Valid Key     │
                        │   Process       │     │   Accepted      │
                        └─────────┬───────┘     └─────────┬───────┘
                                  │                       │
                                  ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Invalid Key   │     │   Step 3:       │
                        │   - Error       │     │   Model Setup   │
                        │     message     │     │   - Default     │
                        │   - Retry       │     │     selection   │
                        └─────────────────┘     └─────────┬───────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Step 4:       │
                                                │   First Chat    │
                                                │   - Input       │
                                                │     focused     │
                                                │   - Placeholder  │
                                                │     text        │
                                                └─────────┬───────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Onboarding    │
                                                │   Complete      │
                                                │   - Modal closes │
                                                │   - Normal UI    │
                                                └─────────────────┘
```

## Advanced Features Flow

```
┌─────────────────┐
│   User Wants    │
│   Advanced      │
│   Features      │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Feature       │────▶│   Model         │
│   Selection     │     │   Comparison    │
└─────────────────┘     └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Enable        │
                        │   Comparison    │
                        │   Mode          │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   UI Adapts     │
                        │   - Split view  │
                        │   - Multiple    │
                        │     panels      │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   User Selects  │
                        │   Models        │
                        │   (2-4 models)  │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   User Enters   │
                        │   Prompt        │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Parallel      │
                        │   API Calls     │
                        │   Initiated     │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Responses     │────▶│   Displayed     │────▶│   Side-by-side  │
│   Received      │     │   Progressively │     │   Comparison    │
│   (Variable     │     │   (Streaming)   │     └─────────┬───────┘
│    timing)      │     └─────────────────┘               │
└─────────────────┘                                        ▼
                                                 ┌─────────────────┐
                                                 │   Analysis       │
                                                 │   Options        │
                                                 │   - Timing       │
                                                 │   - Cost         │
                                                 │   - Quality      │
                                                 │   - Export       │
                                                 └─────────────────┘
```

## Performance Monitoring Flow

```
┌─────────────────┐
│   System       │
│   Performance  │
│   Monitoring   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Response      │────▶│   Time Tracking │
│   Time Goals    │     │   - Cold start  │
│                 │     │     < 3 sec    │
│                 │     │   - Warm resp   │
│                 │     │     < 10 sec   │
└─────────────────┘     └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Threshold     │
                        │   Monitoring    │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Within        │────▶│   Performance   │────▶│   Normal        │
│   Limits        │     │   Acceptable    │     │   Operation     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Exceeds       │────▶│   Performance   │
│   Threshold     │     │   Warning       │
└─────────────────┘     └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   UI Feedback   │
                        │   - Loading     │
                        │     indicator   │
                        │   - Progress    │
                        │     bar         │
                        │   - Time        │
                        │     estimate    │
                        └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   User Options  │
                        │   - Continue    │
                        │     waiting     │
                        │   - Cancel      │
                        │     request     │
                        │   - Switch      │
                        │     model       │
                        └─────────────────┘
```

---

*These flowcharts provide detailed navigation paths for all primary user interactions. Each decision point includes success and failure scenarios with appropriate user feedback and recovery options.*