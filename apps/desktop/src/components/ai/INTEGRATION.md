# AgentChat Integration Guide

Quick guide to integrate the AgentChat component into Kanban AI.

## 1. Import the Component

```typescript
import { AgentChat } from '@/components/ai';
```

## 2. Add State Management

### Option A: Local State (Simple)

```typescript
import { useState } from 'react';

function MyComponent() {
  const [agentChatOpen, setAgentChatOpen] = useState(false);

  return (
    <>
      <button onClick={() => setAgentChatOpen(true)}>
        Ask AI
      </button>

      <AgentChat
        isOpen={agentChatOpen}
        onClose={() => setAgentChatOpen(false)}
      />
    </>
  );
}
```

### Option B: Zustand Store (Recommended)

Create a store in `src/stores/uiStore.ts`:

```typescript
import { create } from 'zustand';

interface UIStore {
  agentChatOpen: boolean;
  agentChatContext?: {
    ticketId?: string;
    ticketTitle?: string;
  };
  openAgentChat: (context?: UIStore['agentChatContext']) => void;
  closeAgentChat: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  agentChatOpen: false,
  agentChatContext: undefined,
  openAgentChat: (context) => set({ agentChatOpen: true, agentChatContext: context }),
  closeAgentChat: () => set({ agentChatOpen: false, agentChatContext: undefined }),
}));
```

Then in your app:

```typescript
import { useUIStore } from '@/stores/uiStore';
import { AgentChat } from '@/components/ai';

function App() {
  const { agentChatOpen, agentChatContext, closeAgentChat } = useUIStore();

  return (
    <>
      {/* Your app content */}

      <AgentChat
        isOpen={agentChatOpen}
        onClose={closeAgentChat}
        context={agentChatContext}
      />
    </>
  );
}
```

## 3. Add to Command Palette

Update `src/components/layout/CommandPalette.tsx`:

```typescript
import { useUIStore } from '@/stores/uiStore';

export function CommandPalette({ ... }) {
  const { openAgentChat } = useUIStore();

  return (
    <Command.Item
      value="ai-chat"
      onSelect={() => {
        openAgentChat();
        onOpenChange(false);
      }}
    >
      <Sparkles className="mr-3 h-4 w-4 text-indigo-400" />
      <span className="flex-1">Open AI Chat</span>
      <Shortcut keys={['⌘', '⇧', 'A']} />
    </Command.Item>
  );
}
```

## 4. Add Global Keyboard Shortcut

In your main `App.tsx` or layout component:

```typescript
import { useEffect } from 'react';
import { useUIStore } from '@/stores/uiStore';

function App() {
  const { openAgentChat } = useUIStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + Shift + A
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'a') {
        e.preventDefault();
        openAgentChat();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openAgentChat]);

  return (
    // ... your app
  );
}
```

## 5. Add Context from Ticket View

In a ticket detail component:

```typescript
import { useUIStore } from '@/stores/uiStore';

function TicketDetail({ ticket }: { ticket: Ticket }) {
  const { openAgentChat } = useUIStore();

  const handleAskAI = () => {
    openAgentChat({
      ticketId: ticket.id,
      ticketTitle: ticket.title,
    });
  };

  return (
    <div>
      <h1>{ticket.title}</h1>

      <button onClick={handleAskAI}>
        <Sparkles className="w-4 h-4" />
        Ask AI about this ticket
      </button>

      {/* Rest of ticket detail */}
    </div>
  );
}
```

## 6. Add to Header/Toolbar

In `src/components/layout/Header.tsx`:

```typescript
import { Sparkles } from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';

export function Header() {
  const { openAgentChat } = useUIStore();

  return (
    <header className="flex items-center justify-between px-6 py-4">
      {/* ... other header content */}

      <button
        onClick={() => openAgentChat()}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 hover:from-indigo-500/30 hover:to-purple-500/30 transition-all"
      >
        <Sparkles className="w-4 h-4 text-indigo-400" />
        <span className="text-sm font-medium text-white">Ask AI</span>
      </button>
    </header>
  );
}
```

## 7. Add Floating Action Button (FAB)

For a persistent AI button:

```typescript
import { Sparkles } from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';

export function AIFloatingButton() {
  const { openAgentChat } = useUIStore();

  return (
    <button
      onClick={() => openAgentChat()}
      className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all z-40 flex items-center justify-center"
      title="Ask AI (Cmd+Shift+A)"
    >
      <Sparkles className="w-6 h-6 text-white" />
    </button>
  );
}

// In App.tsx
function App() {
  return (
    <>
      {/* Your app content */}
      <AIFloatingButton />
      <AgentChat {...} />
    </>
  );
}
```

## 8. Multiple Entry Points Example

Complete integration with multiple ways to open the chat:

```typescript
// App.tsx
import { useState, useEffect } from 'react';
import { AgentChat } from '@/components/ai';
import { Header } from '@/components/layout/Header';
import { CommandPalette } from '@/components/layout/CommandPalette';
import { useUIStore } from '@/stores/uiStore';

function App() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const { agentChatOpen, agentChatContext, closeAgentChat, openAgentChat } = useUIStore();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K for command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }

      // Cmd+Shift+A for AI chat
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'a') {
        e.preventDefault();
        openAgentChat();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openAgentChat]);

  return (
    <div className="h-screen bg-bg-primary text-white">
      <Header onOpenAI={() => openAgentChat()} />

      <main className="h-[calc(100vh-64px)]">
        {/* Your content */}
      </main>

      <CommandPalette
        open={commandPaletteOpen}
        onOpenChange={setCommandPaletteOpen}
        onOpenAI={() => openAgentChat()}
      />

      <AgentChat
        isOpen={agentChatOpen}
        onClose={closeAgentChat}
        context={agentChatContext}
      />
    </div>
  );
}
```

## 9. TypeScript Types

All types are exported from the component:

```typescript
import type { AgentChatProps, AgentChatMessage } from '@/components/ai';

// AgentChatProps
interface AgentChatProps {
  isOpen: boolean;
  onClose: () => void;
  context?: {
    ticketId?: string;
    ticketTitle?: string;
  };
}

// AgentChatMessage
interface AgentChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  actions?: Array<{
    type: string;
    data: Record<string, unknown>;
  }>;
}
```

## 10. Customization

### Custom Context

```typescript
openAgentChat({
  ticketId: ticket.id,
  ticketTitle: ticket.title,
  // Add any custom fields - they'll be passed to the agent API
  projectId: project.id,
  tags: ticket.tags,
});
```

### Custom Styling

The component uses Tailwind classes, so you can customize via:

1. **Global CSS variables** (in `tailwind.config.js`)
2. **Component props** (future enhancement)
3. **Fork the component** (if you need heavy customization)

## 11. Backend Requirements

Ensure your Tauri backend has the `agent_chat` command:

```rust
// src-tauri/src/main.rs
#[tauri::command]
async fn agent_chat(
  message: String,
  context: Option<serde_json::Value>
) -> Result<AgentChatResult, String> {
  // Your implementation
}
```

## 12. Testing

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentChat } from '@/components/ai';

test('opens and sends message', async () => {
  const user = userEvent.setup();
  const handleClose = jest.fn();

  render(<AgentChat isOpen={true} onClose={handleClose} />);

  const textarea = screen.getByPlaceholderText(/Ask AI anything/);
  await user.type(textarea, 'Hello AI');
  await user.keyboard('{Enter}');

  expect(screen.getByText('Hello AI')).toBeInTheDocument();
});
```

## Quick Start Checklist

- [ ] Import AgentChat component
- [ ] Add state management (Zustand store recommended)
- [ ] Add to command palette
- [ ] Add keyboard shortcut (Cmd+Shift+A)
- [ ] Add button in header/toolbar
- [ ] Test basic open/close
- [ ] Test sending messages
- [ ] Test with ticket context
- [ ] Verify Tauri backend integration
- [ ] Add to documentation

## Common Issues

**Issue**: Chat doesn't open
- Check `isOpen` prop is true
- Check z-index conflicts (component uses z-40/z-50)

**Issue**: Messages not sending
- Verify Tauri backend is running
- Check `agent_chat` command is registered
- Check browser console for errors

**Issue**: Styling looks wrong
- Ensure Tailwind CSS is configured
- Check `tailwind.config.js` has custom colors
- Verify Framer Motion is installed

**Issue**: Context not passed
- Ensure context object has correct structure
- Check Tauri command receives context parameter

## Support

See full documentation in `AgentChat.md` or examples in `AgentChat.example.tsx`.
