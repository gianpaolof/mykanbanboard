# Kanban AI - UI Design Guidelines

## Design Philosophy

### Core Principles

1. **Clarity First**
   - Every pixel serves a purpose
   - No decorative elements without function
   - Information hierarchy is immediately clear

2. **Speed & Responsiveness**
   - Interactions feel instant
   - Animations enhance, never delay
   - Progressive loading for heavy content

3. **Keyboard-Native**
   - Power users never touch the mouse
   - Every action has a shortcut
   - Focus states are always visible

4. **Calm Technology**
   - Dark mode reduces eye strain
   - Subtle animations, not flashy
   - Notifications are meaningful

---

## Visual Style

### Hybrid Linear + Glassmorphism

Combiniamo:
- **Linear's foundation:** Dark mode, high contrast, clean typography
- **Glassmorphism accents:** Frosted glass effects su cards e modali
- **Bold status colors:** Priority e labels con colori vivaci

### Color Palette

```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0a0b;
  --bg-secondary: #141415;
  --bg-tertiary: #1c1c1e;
  --bg-elevated: rgba(255, 255, 255, 0.03);
  --bg-hover: rgba(255, 255, 255, 0.05);
  --bg-active: rgba(255, 255, 255, 0.08);
  
  /* Glass effect */
  --glass-bg: rgba(255, 255, 255, 0.03);
  --glass-border: rgba(255, 255, 255, 0.06);
  --glass-blur: 12px;
  
  /* Text */
  --text-primary: #fafafa;
  --text-secondary: #a1a1aa;
  --text-tertiary: #71717a;
  --text-muted: #52525b;
  
  /* Accent */
  --accent-primary: #6366f1;
  --accent-hover: #818cf8;
  --accent-muted: rgba(99, 102, 241, 0.15);
  
  /* Status */
  --status-success: #22c55e;
  --status-warning: #eab308;
  --status-error: #ef4444;
  --status-info: #3b82f6;
  
  /* Priority */
  --priority-critical: #ef4444;
  --priority-high: #f97316;
  --priority-medium: #eab308;
  --priority-low: #22c55e;
  
  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --border-strong: rgba(255, 255, 255, 0.15);
}
```

### Typography

```css
:root {
  /* Font Families */
  --font-display: 'Plus Jakarta Sans', -apple-system, sans-serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* Font Sizes */
  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.875rem;    /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.25rem;     /* 20px */
  --text-2xl: 1.5rem;     /* 24px */
  --text-3xl: 1.875rem;   /* 30px */
  
  /* Font Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
}
```

### Spacing

```css
:root {
  /* Base unit: 4px */
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
}
```

### Border Radius

```css
:root {
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-full: 9999px;
}
```

### Shadows

```css
:root {
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.3);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.4);
  
  /* Glow effects for accents */
  --glow-accent: 0 0 20px rgba(99, 102, 241, 0.3);
  --glow-success: 0 0 20px rgba(34, 197, 94, 0.3);
  --glow-error: 0 0 20px rgba(239, 68, 68, 0.3);
}
```

---

## Components

### Glass Card

```css
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
}

.glass-card:hover {
  background: var(--bg-hover);
  border-color: var(--border-default);
}
```

### Button Variants

```css
/* Primary */
.btn-primary {
  background: var(--accent-primary);
  color: white;
}
.btn-primary:hover {
  background: var(--accent-hover);
}

/* Secondary */
.btn-secondary {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
}
.btn-secondary:hover {
  background: var(--bg-hover);
}

/* Ghost */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}
.btn-ghost:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* Danger */
.btn-danger {
  background: var(--status-error);
  color: white;
}
```

### Input Fields

```css
.input {
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: var(--space-2) var(--space-3);
}

.input:focus {
  border-color: var(--accent-primary);
  outline: none;
  box-shadow: 0 0 0 2px var(--accent-muted);
}

.input::placeholder {
  color: var(--text-muted);
}
```

### Ticket Card

```css
.ticket-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  cursor: grab;
  transition: all 0.15s ease;
}

.ticket-card:hover {
  background: var(--bg-hover);
  border-color: var(--border-default);
  transform: translateY(-1px);
}

.ticket-card:active,
.ticket-card.dragging {
  cursor: grabbing;
  box-shadow: var(--shadow-lg);
  transform: scale(1.02);
}

.ticket-card .priority-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
}

.ticket-card .priority-dot.critical { background: var(--priority-critical); }
.ticket-card .priority-dot.high { background: var(--priority-high); }
.ticket-card .priority-dot.medium { background: var(--priority-medium); }
.ticket-card .priority-dot.low { background: var(--priority-low); }
```

### Labels/Tags

```css
.label {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

/* Label with background color */
.label[data-color="red"] {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.label[data-color="blue"] {
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
}

.label[data-color="green"] {
  background: rgba(34, 197, 94, 0.15);
  color: #86efac;
}

.label[data-color="yellow"] {
  background: rgba(234, 179, 8, 0.15);
  color: #fde047;
}

.label[data-color="purple"] {
  background: rgba(168, 85, 247, 0.15);
  color: #d8b4fe;
}
```

---

## Animation Guidelines

### Timing

```css
:root {
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --duration-slower: 500ms;
  
  /* Easings */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### Common Animations

```css
/* Fade in up (for cards, modals) */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Scale in (for tooltips, dropdowns) */
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Slide in from right (for sidebars) */
@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}
```

### Framer Motion Variants

```tsx
// Stagger children
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.2,
      ease: [0.16, 1, 0.3, 1],
    },
  },
};

// Card hover
const cardVariants = {
  rest: { scale: 1, y: 0 },
  hover: { 
    scale: 1.01, 
    y: -2,
    transition: { duration: 0.2 }
  },
  tap: { scale: 0.98 },
};
```

---

## Layout Patterns

### App Shell

```
┌─────────────────────────────────────────────────────────────┐
│                        Header (48px)                        │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ Sidebar  │                    Main Content                  │
│ (240px)  │                                                  │
│          │                                                  │
│ - Fixed  │                    - Scrollable                  │
│          │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

### Responsive Breakpoints

```css
/* Mobile first */
--breakpoint-sm: 640px;   /* Large phones */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Laptops */
--breakpoint-xl: 1280px;  /* Desktops */
--breakpoint-2xl: 1536px; /* Large screens */
```

---

## Accessibility

### Focus States

```css
/* All interactive elements must have visible focus */
:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

/* Remove default focus ring, use custom */
:focus:not(:focus-visible) {
  outline: none;
}
```

### Color Contrast

- Text on background: minimum 4.5:1
- Large text: minimum 3:1
- Interactive elements: minimum 3:1

### Keyboard Navigation

- Tab order follows visual order
- Focus trap in modals
- Escape closes modals/dropdowns
- Arrow keys for list navigation

### Screen Readers

- All images have alt text
- Icons have aria-labels
- Live regions for dynamic content
- Semantic HTML structure

---

## Icon Usage

### Icon Library: Lucide

```tsx
import { 
  Plus,
  Search,
  Settings,
  ChevronDown,
  MoreHorizontal,
  Calendar,
  Clock,
  MessageSquare,
  Tag,
  Sparkles, // AI features
  Bot,      // Agent
} from 'lucide-react';
```

### Icon Sizes

- Small (in text): 14px
- Default: 16px
- Medium: 20px
- Large: 24px

### Icon Colors

- Default: `var(--text-secondary)`
- Hover: `var(--text-primary)`
- Active: `var(--accent-primary)`
- Disabled: `var(--text-muted)`

---

## Dark Mode / Light Mode

### Theme Toggle

```css
/* Light mode overrides */
[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f4f4f5;
  --bg-tertiary: #e4e4e7;
  --bg-elevated: rgba(0, 0, 0, 0.02);
  
  --text-primary: #09090b;
  --text-secondary: #52525b;
  --text-tertiary: #a1a1aa;
  
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(0, 0, 0, 0.06);
  
  --border-subtle: rgba(0, 0, 0, 0.06);
  --border-default: rgba(0, 0, 0, 0.1);
}
```

### System Preference Detection

```tsx
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
```

---

## Asset Guidelines

### Logo

- Minimum size: 24px
- Clear space: 8px around
- Variants: full color, monochrome, icon only

### Illustrations

- Style: Geometric, minimal
- Colors: Use accent palette
- Usage: Empty states, onboarding

### Screenshots

- Resolution: 2x for retina
- Format: WebP with PNG fallback
- Annotations: Use accent color
