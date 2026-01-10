# CommandPalette Component Structure

## Visual Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│                     BACKDROP OVERLAY                       │
│                  (blur, black/60 opacity)                  │
│                                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │              COMMAND PALETTE MODAL               │     │
│  │              (560px width, centered)             │     │
│  ├──────────────────────────────────────────────────┤     │
│  │  🔍  Type a command or search...                 │     │
│  ├──────────────────────────────────────────────────┤     │
│  │                                                  │     │
│  │  ACTIONS                                         │     │
│  │  ├─ ➕ Create new ticket             ⌘ N       │     │
│  │  ├─ ✨ Ask AI assistant              ⌘ ⇧ A      │     │
│  │  └─ 📄 Get daily summary             ⌘ ⇧ S      │     │
│  │                                                  │     │
│  │  NAVIGATION                                      │     │
│  │  ├─ ▦  Switch to Board view          ⌘ 1       │     │
│  │  ├─ ☰  Switch to List view           ⌘ 2       │     │
│  │  ├─ 📅 Switch to Timeline view       ⌘ 3       │     │
│  │  └─ ⚙  Open settings                 ⌘ ,       │     │
│  │                                                  │     │
│  │  RECENT TICKETS                                  │     │
│  │  ├─ 🕐 Implement authentication flow   [HIGH]   │     │
│  │  ├─ 🕐 Design dashboard wireframes   [MEDIUM]   │     │
│  │  ├─ 🕐 Fix navigation bug           [CRITICAL]  │     │
│  │  └─ 🕐 Update documentation             [LOW]   │     │
│  │                                                  │     │
│  └──────────────────────────────────────────────────┘     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Component Tree

```
CommandPalette
├── AnimatePresence (Framer Motion)
│   ├── Backdrop (motion.div)
│   │   └── onClick: close palette
│   │
│   └── Dialog Container (motion.div)
│       └── Command (from cmdk)
│           ├── Search Header
│           │   ├── Search Icon
│           │   └── Command.Input
│           │
│           └── Command.List
│               ├── Command.Empty (no results state)
│               │
│               ├── Command.Group: "Actions"
│               │   ├── CommandItem: Create ticket
│               │   ├── CommandItem: Ask AI
│               │   └── CommandItem: Daily summary
│               │
│               ├── Command.Group: "Navigation"
│               │   ├── CommandItem: Board view
│               │   ├── CommandItem: List view
│               │   ├── CommandItem: Timeline view
│               │   └── CommandItem: Settings
│               │
│               └── Command.Group: "Recent Tickets"
│                   └── CommandItem[] (mapped from RECENT_TICKETS)
```

## CommandItem Anatomy

```
┌─────────────────────────────────────────────────────┐
│  [ICON]  Label text                [BADGE]  [KBD]  │
│   16px   flex-1                    optional kbd     │
└─────────────────────────────────────────────────────┘

Example:
┌─────────────────────────────────────────────────────┐
│  ✨  Ask AI assistant                    ⌘  ⇧  A   │
└─────────────────────────────────────────────────────┘

States:
- Default: text-zinc-300, bg-transparent
- Hover/Selected: text-zinc-100, bg-bg-hover
- Disabled: opacity-50, pointer-events-none
```

## Styling Classes

### Modal Container
```css
max-w-[560px]           /* Width constraint */
rounded-xl              /* 12px border radius */
border border-border    /* 1px border */
bg-bg-secondary         /* Dark background */
shadow-xl               /* Large shadow */
backdrop-blur-xl        /* Strong blur */
```

### Search Input
```css
h-12                    /* 48px height */
px-4                    /* 16px horizontal padding */
border-b border-border  /* Bottom border separator */
```

### Command Item
```css
px-3 py-2.5                           /* Padding */
rounded-lg                            /* 8px radius */
aria-selected:bg-bg-hover             /* Selected state */
aria-selected:text-zinc-100           /* Selected text */
```

### Keyboard Shortcut (kbd)
```css
h-5                     /* 20px height */
px-1.5                  /* 6px horizontal padding */
rounded                 /* 4px radius */
border border-zinc-700  /* Dark border */
bg-bg-tertiary          /* Tertiary background */
font-mono text-[10px]   /* Monospace, 10px */
text-zinc-400           /* Gray text */
```

## Animation Details

### Entry Animation
```typescript
initial: {
  opacity: 0,    // Fully transparent
  scale: 0.96,   // Slightly scaled down
  y: -20         // 20px above final position
}

animate: {
  opacity: 1,    // Fully visible
  scale: 1,      // Normal scale
  y: 0           // Final position
}

duration: 150ms
easing: easeOut
```

### Exit Animation
```typescript
exit: {
  opacity: 0,    // Fade out
  scale: 0.96,   // Scale down slightly
  y: -20         // Move up
}

duration: 150ms
```

### Backdrop Animation
```typescript
initial: { opacity: 0 }
animate: { opacity: 1 }
exit: { opacity: 0 }
duration: 150ms
```

## Color Reference

```css
/* Backgrounds */
bg-black/60           /* Backdrop: #000000 @ 60% */
bg-bg-secondary       /* Modal: #141415 */
bg-bg-tertiary        /* Kbd: #1c1c1e */
bg-bg-hover           /* Selected: rgba(255,255,255,0.05) */

/* Text */
text-zinc-100         /* Primary: #fafafa */
text-zinc-300         /* Secondary: #d4d4d8 */
text-zinc-400         /* Tertiary: #a1a1aa */
text-zinc-500         /* Muted: #71717a */

/* Borders */
border-border         /* Default: rgba(255,255,255,0.1) */
border-zinc-700       /* Kbd: #3f3f46 */

/* Accents */
text-indigo-400       /* AI icon: #818cf8 */
text-red-400          /* Critical: #f87171 */
text-orange-400       /* High: #fb923c */
text-yellow-400       /* Medium: #facc15 */
text-blue-400         /* Low: #60a5fa */
```

## Accessibility Features

- **Keyboard Navigation**: Full arrow key support via cmdk
- **Focus Management**: Automatic focus trap when open
- **ARIA Attributes**: Command items use aria-selected
- **Screen Reader**: Descriptive labels and shortcuts
- **Escape Key**: Close on Escape press
- **Click Outside**: Close when clicking backdrop

## Performance Notes

- **AnimatePresence**: Only renders when open
- **Command.List**: Virtualized scrolling for large lists
- **Search**: Debounced filtering via cmdk
- **Event Listeners**: Properly cleaned up on unmount
