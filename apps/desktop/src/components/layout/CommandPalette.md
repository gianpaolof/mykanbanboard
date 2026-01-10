# CommandPalette Component

A beautiful, fully-featured command palette component built with `cmdk`, matching the Kanban AI design system with glassmorphism effects and smooth animations.

## Features

- **Full keyboard navigation** - Arrow keys, Enter, Escape
- **Smooth animations** - Framer Motion scale and fade transitions
- **Glassmorphism design** - Backdrop blur and transparent overlays
- **Grouped commands** - Actions, Navigation, Recent Tickets
- **Keyboard shortcuts display** - Visual kbd elements showing shortcuts
- **Search functionality** - Built-in filtering via cmdk
- **Priority badges** - Color-coded ticket priorities
- **Accessible** - ARIA compliant, keyboard friendly

## Installation

The component uses these dependencies (already installed):

```json
{
  "cmdk": "^1.0.0",
  "framer-motion": "^11.11.0",
  "lucide-react": "^0.447.0"
}
```

## Usage

```tsx
import { useState, useEffect } from 'react';
import { CommandPalette } from './components/layout';

function App() {
  const [open, setOpen] = useState(false);

  // Open with Cmd+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return (
    <>
      <div>Your app content...</div>

      <CommandPalette
        open={open}
        onOpenChange={setOpen}
        onCreateTicket={() => console.log('Create ticket')}
        onOpenAI={() => console.log('Open AI')}
        onSwitchView={(view) => console.log('Switch to', view)}
      />
    </>
  );
}
```

## Props

```typescript
interface CommandPaletteProps {
  // Controls visibility
  open: boolean;

  // Callback when open state changes
  onOpenChange: (open: boolean) => void;

  // Called when "Create new ticket" is selected
  onCreateTicket: () => void;

  // Called when "Ask AI assistant" is selected
  onOpenAI: () => void;

  // Called when switching views (Board/List/Timeline)
  onSwitchView: (view: 'board' | 'list' | 'timeline') => void;
}
```

## Command Groups

### Actions
- **Create new ticket** (⌘N) - Opens ticket creation dialog
- **Ask AI assistant** (⌘⇧A) - Opens AI chat interface
- **Get daily summary** (⌘⇧S) - Generates standup summary

### Navigation
- **Switch to Board view** (⌘1) - Kanban board layout
- **Switch to List view** (⌘2) - List/table layout
- **Switch to Timeline view** (⌘3) - Timeline/calendar view
- **Open settings** (⌘,) - Application settings

### Recent Tickets
Displays the last 4 accessed tickets with:
- Ticket title
- Priority badge (color-coded)
- Quick access to open ticket

## Customization

### Recent Tickets Data

Currently using mock data. Replace with your store/API:

```tsx
// In CommandPalette.tsx
const RECENT_TICKETS = useTicketStore((state) => state.recentTickets);
```

### Adding New Commands

Add to the appropriate `Command.Group`:

```tsx
<Command.Group heading="Your Group">
  <CommandItem
    onSelect={() => handleAction(() => yourFunction())}
    icon={<YourIcon className="h-4 w-4" />}
    label="Your command"
    shortcut={['⌘', 'X']}
  />
</Command.Group>
```

### Styling

Uses Tailwind classes from the design system:

```tsx
// Colors
bg-bg-secondary      // Modal background
bg-bg-tertiary       // Kbd background
bg-bg-hover          // Selected item
border-border        // Border color

// Glass effect
backdrop-blur-xl     // Blur backdrop
bg-black/60          // Overlay transparency
```

## Keyboard Shortcuts

Global shortcuts (implement in your app):

- `⌘K` - Toggle command palette
- `⌘N` - Create new ticket (also works in palette)
- `⌘⇧A` - Ask AI assistant
- `⌘⇧S` - Get daily summary
- `⌘1/2/3` - Switch views
- `⌘,` - Open settings

Palette navigation:

- `↑/↓` - Navigate commands
- `Enter` - Select command
- `Escape` - Close palette
- Type to filter commands

## Animation

Entry/exit animations via Framer Motion:

```tsx
initial={{ opacity: 0, scale: 0.96, y: -20 }}
animate={{ opacity: 1, scale: 1, y: 0 }}
exit={{ opacity: 0, scale: 0.96, y: -20 }}
transition={{ duration: 0.15, ease: 'easeOut' }}
```

## Design Specs

- **Width**: 560px max-width
- **Position**: Centered, 15vh from top
- **Border**: 1px, default border color
- **Border radius**: xl (12px)
- **Shadow**: xl shadow
- **Input height**: 48px
- **List max height**: 400px
- **Item padding**: 10px vertical, 12px horizontal
- **Icon size**: 16px (h-4 w-4)
- **Shortcut text**: 10px mono font

## Accessibility

- Full ARIA support via cmdk
- Keyboard navigation
- Screen reader friendly
- Focus management
- Semantic HTML

## Examples

See `CommandPalette.example.tsx` for complete integration example.

## Future Enhancements

- [ ] Recent tickets from actual store
- [ ] Command history
- [ ] Fuzzy search scoring
- [ ] Custom command registration
- [ ] Nested commands/submenus
- [ ] Command execution history
- [ ] Analytics tracking
