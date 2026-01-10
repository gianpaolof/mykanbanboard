# AgentChat Component

A slide-in chat panel for interacting with the AI agent in Kanban AI. Features glassmorphism design, auto-resize textarea, typing indicators, and action displays.

## Features

- **Slide-in animation** from the right side (Linear/Notion style)
- **Glassmorphism design** with backdrop blur and transparency
- **Auto-resize textarea** that grows up to 200px
- **Typing indicator** with animated dots when agent is thinking
- **Action display** shows what actions the agent performed
- **Context awareness** can receive ticket context
- **Relative timestamps** (e.g., "2m ago", "just now")
- **Error handling** with error banner
- **Keyboard shortcuts** Enter to send, Shift+Enter for newline
- **Auto-scroll** to latest message
- **Clear chat** button to reset conversation

## Usage

### Basic Usage

```tsx
import { AgentChat } from '@/components/ai';

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Open AI Chat
      </button>

      <AgentChat
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  );
}
```

### With Ticket Context

```tsx
<AgentChat
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  context={{
    ticketId: 'ticket-123',
    ticketTitle: 'Implement authentication flow',
  }}
/>
```

## Props

```typescript
interface AgentChatProps {
  isOpen: boolean;         // Controls panel visibility
  onClose: () => void;     // Called when user closes panel
  context?: {              // Optional ticket context
    ticketId?: string;
    ticketTitle?: string;
  };
}
```

## API Integration

The component integrates with the Tauri backend via:

```typescript
import { api } from '@/lib/tauri';

const result = await api.agent.chat(message, context);
// result.response: string - The agent's text response
// result.actions: Array<{type: string, data: Record<string, unknown>}> - Actions performed
```

## Component Architecture

```
AgentChat
├── Header
│   ├── Title + Context display
│   ├── Clear button (if messages exist)
│   └── Close button
├── Error Banner (conditional)
├── Messages Area
│   ├── Empty state (if no messages)
│   ├── MessageBubble[] (user + assistant)
│   ├── ActionDisplay (for agent actions)
│   └── TypingIndicator (when loading)
└── Input Area
    ├── Auto-resize textarea
    ├── Send button
    └── Keyboard hint
```

## Design System

### Colors

- **Background**: `bg-bg-secondary/95` with `backdrop-blur-xl`
- **Border**: `border-border-subtle`
- **User message**: `bg-indigo-600/80` with backdrop blur
- **Assistant message**: `bg-glass-bg` with `border-glass-border`
- **Avatar gradient**: `from-indigo-500 to-purple-500`
- **Accent**: `bg-accent` (indigo)

### Animations

- **Panel slide-in**: Spring animation (damping: 30, stiffness: 300)
- **Backdrop fade**: 0.2s fade in/out
- **Messages**: Fade-in + slide-up (0.2s)
- **Typing indicator**: Bounce animation with staggered delays

### Typography

- **Title**: `text-base font-semibold`
- **Message**: `text-sm leading-relaxed`
- **Timestamp**: `text-2xs text-gray-500`
- **Action**: `text-xs`

## Message Format

```typescript
interface AgentChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string; // ISO 8601
  actions?: Array<{
    type: string;
    data: Record<string, unknown>;
  }>;
}
```

## Keyboard Shortcuts

- **Enter**: Send message
- **Shift + Enter**: New line in textarea
- **Escape**: Close panel (via backdrop click)

## Accessibility

- Auto-focus on textarea when panel opens
- Keyboard navigation support
- ARIA labels on buttons
- Proper contrast ratios
- Semantic HTML structure

## State Management

The component manages its own state:

- `messages`: Array of chat messages
- `inputValue`: Current textarea content
- `isLoading`: Whether agent is responding
- `error`: Error message (if any)

## Error Handling

Errors are displayed in a banner at the top of the panel:

```tsx
{error && (
  <div className="error-banner">
    <AlertCircle />
    <p>{error}</p>
    <button onClick={() => setError(null)}>×</button>
  </div>
)}
```

## Performance Considerations

- Auto-scroll uses `scrollIntoView({ behavior: 'smooth' })`
- Textarea auto-resize capped at 200px max height
- Messages use unique IDs for React key optimization
- AnimatePresence for smooth mount/unmount

## Examples

See `AgentChat.example.tsx` for more usage examples:

1. Basic usage
2. With ticket context
3. With keyboard shortcuts
4. Multiple instances

## Customization

### Custom Context

You can extend the context object:

```typescript
context={{
  ticketId: ticket.id,
  ticketTitle: ticket.title,
  // Add more custom fields
  projectId: project.id,
  tags: ticket.tags,
}}
```

### Custom Actions Display

The `ActionDisplay` component can be customized to handle different action types:

```typescript
// In ActionDisplay component
switch (action.type) {
  case 'create_ticket':
    return <CreateTicketAction data={action.data} />;
  case 'update_ticket':
    return <UpdateTicketAction data={action.data} />;
  default:
    return <GenericAction action={action} />;
}
```

## Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentChat } from './AgentChat';

test('renders when open', () => {
  render(<AgentChat isOpen={true} onClose={() => {}} />);
  expect(screen.getByText('AI Agent Chat')).toBeInTheDocument();
});

test('sends message on Enter key', async () => {
  render(<AgentChat isOpen={true} onClose={() => {}} />);
  const textarea = screen.getByPlaceholderText(/Ask AI anything/);

  fireEvent.change(textarea, { target: { value: 'Hello' } });
  fireEvent.keyDown(textarea, { key: 'Enter' });

  expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

## Browser Compatibility

- Modern browsers with support for:
  - CSS backdrop-filter
  - Framer Motion
  - ES2020+ JavaScript

## Future Enhancements

- [ ] Message persistence (save to local storage)
- [ ] Export chat history
- [ ] Voice input
- [ ] Markdown rendering in messages
- [ ] Code syntax highlighting
- [ ] Message reactions
- [ ] Thread branching
- [ ] Agent memory (conversation history in context)
