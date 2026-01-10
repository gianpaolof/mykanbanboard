# AgentChat Component Tree

Visual breakdown of the component hierarchy and data flow.

## Component Hierarchy

```
<AgentChat>
│
├─ <AnimatePresence>
│  │
│  ├─ <motion.div> [Backdrop]
│  │  └─ onClick={onClose}
│  │
│  └─ <motion.div> [Panel Container]
│     │
│     ├─ [Header Section]
│     │  ├─ <div> Title + Context
│     │  │  ├─ <Sparkles /> icon
│     │  │  ├─ <h2> "AI Agent Chat"
│     │  │  └─ <p> context?.ticketTitle (optional)
│     │  │
│     │  └─ <div> Actions
│     │     ├─ <button> Clear (if messages.length > 0)
│     │     └─ <button> Close
│     │
│     ├─ [Error Banner] (conditional: if error)
│     │  ├─ <AlertCircle /> icon
│     │  ├─ <p> error message
│     │  └─ <button> Dismiss
│     │
│     ├─ [Messages Area]
│     │  ├─ (Empty State) if messages.length === 0
│     │  │  ├─ <Sparkles /> large icon
│     │  │  ├─ <h3> "Start a conversation"
│     │  │  ├─ <p> helpful suggestions
│     │  │  └─ <div> context display (if context)
│     │  │
│     │  └─ (Message List) if messages.length > 0
│     │     ├─ <MessageBubble /> for each message
│     │     │  ├─ <motion.div> container
│     │     │  ├─ <div> avatar (Bot or User)
│     │     │  ├─ <div> content bubble
│     │     │  │  ├─ <p> message.content
│     │     │  │  └─ <ActionDisplay /> (if actions)
│     │     │  └─ <div> timestamp
│     │     │
│     │     ├─ <TypingIndicator /> (if isLoading)
│     │     │  ├─ <Bot /> avatar
│     │     │  └─ <div> animated dots + "Thinking..."
│     │     │
│     │     └─ <div ref={messagesEndRef} /> (scroll anchor)
│     │
│     └─ [Input Area]
│        ├─ <textarea> auto-resize
│        ├─ <button> Send
│        │  └─ <Send /> or <Loader2 /> icon
│        └─ <p> keyboard hint text
```

## Sub-Components

### MessageBubble

```
<MessageBubble message={message}>
│
├─ <motion.div> animated container
│
├─ <div> avatar circle
│  └─ <Bot /> or <User /> icon
│
├─ <div> message content
│  ├─ <div> bubble
│  │  ├─ <p> message text
│  │  └─ <ActionDisplay /> (optional)
│  │
│  └─ <div> timestamp
```

### ActionDisplay

```
<ActionDisplay actions={actions}>
│
└─ for each action in actions:
   ├─ <div> action item
   │  ├─ <CheckCircle2 /> icon
   │  └─ <div> action details
   │     ├─ <p> action.type
   │     └─ <p> formatted action.data
```

### TypingIndicator

```
<TypingIndicator>
│
├─ <motion.div> animated container
│
├─ <div> bot avatar
│  └─ <Bot /> icon
│
└─ <div> indicator bubble
   ├─ <div> 3 animated dots
   │  ├─ dot 1 (delay: 0ms)
   │  ├─ dot 2 (delay: 150ms)
   │  └─ dot 3 (delay: 300ms)
   │
   └─ <span> "Thinking..."
```

## Data Flow

```
User Input → handleSendMessage()
                    ↓
            Create user message
                    ↓
            Add to messages state
                    ↓
            Set isLoading = true
                    ↓
            Call api.agent.chat()
                    ↓
        ┌───────────┴───────────┐
        │                       │
     Success                 Error
        │                       │
        ↓                       ↓
Create assistant msg    Create error msg
        │                       │
        ↓                       ↓
  Add to messages       Add to messages
        │                       │
        └───────────┬───────────┘
                    ↓
            Set isLoading = false
                    ↓
            Auto-scroll to bottom
```

## State Flow

```
Initial State:
├─ messages: []
├─ inputValue: ""
├─ isLoading: false
└─ error: null

User types "Hello" → inputValue: "Hello"
                           ↓
User presses Enter → handleSendMessage()
                           ↓
                     messages: [
                       {role: 'user', content: 'Hello', ...}
                     ]
                     inputValue: ""
                     isLoading: true
                           ↓
Agent responds → messages: [
                   {role: 'user', content: 'Hello', ...},
                   {role: 'assistant', content: 'Hi!', actions: [...]}
                 ]
                 isLoading: false

User clicks Clear → messages: []
                    error: null
```

## Effect Flow

```
isOpen changes to true
    ↓
useEffect[isOpen] fires
    ↓
setTimeout 100ms
    ↓
textareaRef.current?.focus()
    ↓
User can start typing immediately

---

messages or isLoading changes
    ↓
useEffect[messages, isLoading] fires
    ↓
messagesEndRef.current?.scrollIntoView()
    ↓
Messages area scrolls to bottom smoothly

---

inputValue changes
    ↓
useEffect[inputValue] fires
    ↓
Calculate textarea.scrollHeight
    ↓
Set height to min(scrollHeight, 200px)
    ↓
Textarea grows/shrinks smoothly
```

## Animation Flow

```
isOpen: false → true
    ↓
AnimatePresence detects new child
    ↓
Backdrop: opacity 0 → 1 (0.2s)
Panel: translateX(100%) → 0 (spring)
    ↓
Panel slides in from right

---

New message added
    ↓
MessageBubble mounts
    ↓
initial: {opacity: 0, y: 10}
animate: {opacity: 1, y: 0}
    ↓
Message fades in + slides up (0.2s)

---

isOpen: true → false
    ↓
AnimatePresence detects child removal
    ↓
Backdrop: opacity 1 → 0 (0.2s)
Panel: translateX(0) → 100% (spring)
    ↓
Panel slides out to right
    ↓
Component unmounts
```

## Event Flow

```
User Interaction Events:

1. Click backdrop
   ↓
   onClick={onClose}
   ↓
   Parent sets isOpen = false
   ↓
   Panel animates out

2. Type in textarea
   ↓
   onChange={(e) => setInputValue(e.target.value)}
   ↓
   inputValue updates
   ↓
   useEffect resizes textarea

3. Press Enter
   ↓
   onKeyDown → check if Enter && !shiftKey
   ↓
   e.preventDefault()
   ↓
   handleSendMessage()

4. Press Shift+Enter
   ↓
   onKeyDown → Enter && shiftKey
   ↓
   Default behavior (newline)

5. Click Send button
   ↓
   onClick={handleSendMessage}
   ↓
   Send message

6. Click Clear button
   ↓
   onClick={handleClearChat}
   ↓
   setMessages([])
   setError(null)
```

## Props → DOM Flow

```
Props:
├─ isOpen: boolean
│  └─ Controls AnimatePresence → mounts/unmounts entire panel
│
├─ onClose: () => void
│  ├─ Passed to backdrop onClick
│  └─ Passed to close button onClick
│
└─ context?: {ticketId, ticketTitle}
   ├─ Displayed in header: "Context: {ticketTitle}"
   ├─ Passed to API: api.agent.chat(message, {ticket_id, ticket_title})
   └─ Shown in empty state if present
```

## Class Name Flow

```
Panel Container:
├─ fixed right-0 top-0 bottom-0
├─ w-[480px]
├─ bg-bg-secondary/95
├─ border-l border-border-subtle
├─ backdrop-blur-xl
└─ z-50

User Message Bubble:
├─ bg-indigo-600/80
├─ backdrop-blur-sm
├─ max-w-[85%]
├─ rounded-2xl
├─ px-4 py-2.5
└─ text-white

Assistant Message Bubble:
├─ bg-glass-bg
├─ border border-glass-border
├─ backdrop-blur-xl
├─ max-w-[85%]
├─ rounded-2xl
├─ px-4 py-2.5
└─ text-gray-100
```

## Ref Flow

```
messagesEndRef
    ↓
Attached to empty <div> at end of messages
    ↓
Used in useEffect to scroll to bottom
    ↓
messagesEndRef.current?.scrollIntoView()

textareaRef
    ↓
Attached to <textarea> element
    ↓
Used for:
├─ Auto-focus when panel opens
├─ Reading scrollHeight for auto-resize
└─ Setting height style dynamically
```

This component tree visualization helps understand the complete structure, data flow, and interactions within the AgentChat component.
