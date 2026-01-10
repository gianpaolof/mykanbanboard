# AI Components

This directory contains AI-powered components for Kanban AI.

## Components

### AgentChat

**Production-ready AI chat component** with slide-in panel, glassmorphism design, and full integration with the Tauri backend agent API.

**Quick Start:**

```typescript
import { AgentChat } from '@/components/ai';

<AgentChat
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  context={{ ticketId: 'ticket-123', ticketTitle: 'Fix bug' }}
/>
```

**Features:**
- Slide-in panel animation from right
- Auto-resize textarea (up to 200px)
- Typing indicator with animated dots
- Action display for agent operations
- Context-aware (ticket info)
- Relative timestamps
- Error handling with banner
- Keyboard shortcuts (Enter/Shift+Enter)

**Documentation:**
- `AgentChat.tsx` - Main component (496 lines)
- `AgentChat.md` - Full documentation
- `AgentChat.example.tsx` - Usage examples
- `INTEGRATION.md` - Integration guide
- `COMPONENT_TREE.md` - Visual component hierarchy
- `SUMMARY.md` - Quick overview

### AIPanel

Legacy demo component. Use `AgentChat` for new implementations.

## Files

```
ai/
├── AgentChat.tsx           16KB  Main chat component
├── AgentChat.md           6.2KB  Full documentation
├── AgentChat.example.tsx  2.6KB  Usage examples
├── INTEGRATION.md         9.4KB  Integration guide
├── COMPONENT_TREE.md      8.0KB  Component hierarchy
├── SUMMARY.md             6.0KB  Quick overview
├── README.md              (this) Directory overview
├── AIPanel.tsx            10KB   Legacy component
└── index.ts               246B   Exports
```

## Quick Reference

### Import

```typescript
import { AgentChat, AgentChatMessage, AgentChatProps } from '@/components/ai';
```

### Props

```typescript
interface AgentChatProps {
  isOpen: boolean;         // Panel visibility
  onClose: () => void;     // Close handler
  context?: {              // Optional ticket context
    ticketId?: string;
    ticketTitle?: string;
  };
}
```

### API Integration

```typescript
import { api } from '@/lib/tauri';

const result = await api.agent.chat(message, context);
// Returns: { response: string, actions?: Array<{type, data}> }
```

### State Management (Zustand)

```typescript
// stores/uiStore.ts
interface UIStore {
  agentChatOpen: boolean;
  agentChatContext?: { ticketId?: string; ticketTitle?: string };
  openAgentChat: (context?) => void;
  closeAgentChat: () => void;
}
```

## Design System

- **Width:** 480px
- **Background:** bg-bg-secondary/95 + backdrop-blur-xl
- **User bubble:** bg-indigo-600/80
- **Assistant bubble:** bg-glass-bg + border-glass-border
- **Accent:** Indigo-600
- **Font:** Inter (14px messages, 10px timestamps)

## Keyboard Shortcuts

- **Enter** - Send message
- **Shift+Enter** - New line
- **Cmd+Shift+A** - Open chat (when implemented globally)

## Integration Steps

1. Import component: `import { AgentChat } from '@/components/ai'`
2. Add state: `const [open, setOpen] = useState(false)` or use Zustand
3. Add to JSX: `<AgentChat isOpen={open} onClose={() => setOpen(false)} />`
4. Add trigger button: `<button onClick={() => setOpen(true)}>Ask AI</button>`
5. (Optional) Add keyboard shortcut
6. (Optional) Add to command palette

See `INTEGRATION.md` for detailed guide.

## Examples

**Basic Usage:**

```typescript
function App() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button onClick={() => setOpen(true)}>Ask AI</button>
      <AgentChat isOpen={open} onClose={() => setOpen(false)} />
    </>
  );
}
```

**With Ticket Context:**

```typescript
<AgentChat
  isOpen={open}
  onClose={() => setOpen(false)}
  context={{
    ticketId: ticket.id,
    ticketTitle: ticket.title,
  }}
/>
```

**With Zustand Store:**

```typescript
const { agentChatOpen, closeAgentChat, openAgentChat } = useUIStore();

<button onClick={() => openAgentChat({ ticketId: '123', ticketTitle: 'Bug' })}>
  Ask AI
</button>

<AgentChat
  isOpen={agentChatOpen}
  onClose={closeAgentChat}
  context={agentChatContext}
/>
```

## Architecture

```
User Input
    ↓
handleSendMessage()
    ↓
Add user message to state
    ↓
api.agent.chat(message, context)
    ↓
Add assistant response to state
    ↓
Display with actions (if any)
```

## Testing

```typescript
import { render, screen } from '@testing-library/react';
import { AgentChat } from '@/components/ai';

test('renders when open', () => {
  render(<AgentChat isOpen={true} onClose={() => {}} />);
  expect(screen.getByText('AI Agent Chat')).toBeInTheDocument();
});
```

## Browser Support

- Modern browsers with:
  - CSS backdrop-filter
  - Framer Motion support
  - ES2020+ JavaScript

## TypeScript

Fully typed with strict mode. All exports have proper TypeScript definitions.

## Status

- AgentChat: ✅ Production ready
- AIPanel: ⚠️  Legacy (use AgentChat instead)

## Performance

- Auto-scroll: `scrollIntoView({ behavior: 'smooth' })`
- Textarea resize: Capped at 200px max height
- Messages: Unique IDs for React key optimization
- Animations: GPU-accelerated with Framer Motion

## Accessibility

- Semantic HTML
- Keyboard navigation (Enter, Shift+Enter, Escape)
- Auto-focus management
- ARIA labels on buttons
- High contrast (WCAG AA)

## Future Enhancements

- [ ] Message persistence (localStorage)
- [ ] Export chat history
- [ ] Markdown rendering
- [ ] Code syntax highlighting
- [ ] Voice input
- [ ] Message reactions
- [ ] Thread branching

## Contributing

When modifying components:

1. Update TypeScript types
2. Update documentation
3. Update examples
4. Run `npm run type-check`
5. Test manually in the app

## Support

For questions or issues:

1. Check `AgentChat.md` for full docs
2. Review `INTEGRATION.md` for setup
3. See `AgentChat.example.tsx` for patterns
4. Check `COMPONENT_TREE.md` for architecture

## Credits

Built with:
- React 18
- TypeScript
- Framer Motion
- Tailwind CSS
- Lucide Icons
- Tauri IPC

Design inspired by:
- Linear (slide-in panels)
- Notion (chat interface)
- Arc Browser (glassmorphism)

## License

Part of Kanban AI project.
