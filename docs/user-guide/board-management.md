# Board Management

Learn how to create, organize, and manage your Kanban boards effectively.

## Overview

Kanban AI uses a board-based system to organize your work. Each board contains columns that represent workflow stages, and tickets that represent individual tasks.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Board                              │
├───────────────┬───────────────┬───────────────┬────────────────┤
│   Backlog     │  In Progress  │    Review     │     Done       │
├───────────────┼───────────────┼───────────────┼────────────────┤
│ [Ticket 1]    │ [Ticket 3]    │ [Ticket 5]    │ [Ticket 7]     │
│ [Ticket 2]    │ [Ticket 4]    │               │ [Ticket 8]     │
│               │               │               │                │
└───────────────┴───────────────┴───────────────┴────────────────┘
```

---

## Creating a Board

### Quick Create

1. Press `Cmd+N` (Mac) or `Ctrl+N` (Windows/Linux)
2. Enter a board name
3. Press Enter

The board will be created with default columns: **Backlog**, **In Progress**, **Review**, **Done**.

### Custom Board

1. Click **New Board** in the sidebar
2. Fill in the board details:
   - **Name**: Board name (required)
   - **Description**: Optional description
   - **Columns**: Add custom columns
3. Click **Create**

---

## Managing Columns

### Adding Columns

1. Click the **+** button at the end of the column row
2. Enter column name
3. Optionally set:
   - **Color**: Visual identifier
   - **WIP Limit**: Maximum tickets allowed

### Editing Columns

1. Click the column header menu (three dots)
2. Select **Edit Column**
3. Modify settings:
   - Rename the column
   - Change color
   - Set WIP limit

### Reordering Columns

Drag and drop columns by their header to reorder them.

### Deleting Columns

1. Click the column header menu
2. Select **Delete Column**
3. Choose where to move existing tickets
4. Confirm deletion

!!! warning "Column Deletion"
    When deleting a column with tickets, you must specify a destination column. Tickets are never deleted automatically.

---

## Working with Tickets

### Creating Tickets

**Quick Create:**
1. Press `N` or click **+ New Ticket**
2. Enter ticket title
3. Press Enter

**Detailed Create:**
1. Press `Cmd+Shift+N` or click **New Ticket** with details
2. Fill in:
   - **Title** (required)
   - **Description** (Markdown supported)
   - **Priority**: Low, Medium, High, Critical
   - **Effort**: XS, S, M, L, XL
   - **Labels**: Add categorization tags
   - **Due Date**: Set deadline
3. Click **Create** or press `Cmd+Enter`

### Editing Tickets

1. Click a ticket to open the detail panel
2. Edit any field directly
3. Changes save automatically

Or use keyboard shortcut:
- Select ticket with arrow keys
- Press `E` to edit
- Press `Escape` to close

### Moving Tickets

**Drag and Drop:**
Simply drag a ticket to a new column or position.

**Keyboard:**
1. Select ticket with arrow keys
2. Press `M` to move
3. Use arrow keys to select destination
4. Press Enter to confirm

**Quick Move:**
Use the command palette (`Cmd+K`) and type:
- `move to [column name]`
- `move [ticket title] to [column]`

### Deleting Tickets

1. Select the ticket
2. Press `Delete` or `Backspace`
3. Confirm deletion

Or right-click the ticket and select **Delete**.

---

## Organizing Your Board

### Using Labels

Labels help categorize tickets across columns.

**Creating Labels:**
1. Click a ticket
2. In the labels field, type a new label name
3. Press Enter to create and apply

**Filtering by Labels:**
1. Click the filter icon in the toolbar
2. Select one or more labels
3. Board shows only matching tickets

**Suggested Labels:**
When AI Triage is enabled, the system suggests relevant labels:
- `bug` - Issues and defects
- `feature` - New functionality
- `refactor` - Code improvements
- `docs` - Documentation tasks
- `urgent` - Time-sensitive items

### Setting Priorities

| Priority | Color | Use Case |
|----------|-------|----------|
| Low | Gray | Nice-to-have, can wait |
| Medium | Blue | Standard work items |
| High | Orange | Important, needs attention |
| Critical | Red | Urgent, blocks other work |

**Quick Priority Change:**
- Select ticket
- Press `1-4` to set priority (1=Low, 4=Critical)

### Effort Estimation

| Size | Icon | Typical Duration |
|------|------|------------------|
| XS | | Less than 1 hour |
| S | | 1-4 hours |
| M | | 1-2 days |
| L | | 3-5 days |
| XL | | More than a week |

---

## WIP Limits

Work-in-Progress limits help prevent overcommitment.

### Setting WIP Limits

1. Click column header menu
2. Select **Set WIP Limit**
3. Enter maximum number of tickets
4. Click **Save**

### WIP Limit Behavior

- **Under limit**: Normal appearance
- **At limit**: Column header shows warning color
- **Over limit**: Column highlighted, prevents new tickets

!!! tip "Recommended WIP Limits"
    - **In Progress**: 3-5 per person
    - **Review**: 2-3 items
    - **Keep Done unlimited** for completed work

---

## Views

Switch between different board visualizations.

### Board View (Default)
- Classic Kanban columns
- Drag and drop support
- Best for daily work

**Shortcut:** `Cmd+1`

### List View
- All tickets in a sortable table
- Good for bulk operations
- Easy filtering and search

**Shortcut:** `Cmd+2`

### Timeline View
- Gantt-style visualization
- Based on due dates
- Good for planning

**Shortcut:** `Cmd+3`

### Calendar View
- Month/week calendar
- Tickets shown by due date
- Drag to reschedule

**Shortcut:** `Cmd+4`

---

## Filtering and Search

### Quick Search

Press `Cmd+F` or `/` to open search:
- Type to filter visible tickets
- Results highlight in real-time
- Press `Escape` to clear

### Advanced Filters

Click the filter icon or press `F` to open filter panel:

| Filter | Example |
|--------|---------|
| Priority | `priority:high` |
| Label | `label:bug` |
| Due Date | `due:today`, `due:this-week` |
| Column | `column:in-progress` |
| Effort | `effort:m` |

**Combining Filters:**
```
priority:high label:bug due:this-week
```

### Saved Filters

1. Set up your filters
2. Click **Save Filter**
3. Name your filter
4. Access from filter dropdown

---

## Bulk Operations

### Select Multiple Tickets

- **Cmd+Click**: Add/remove from selection
- **Shift+Click**: Select range
- **Cmd+A**: Select all visible

### Bulk Actions

With multiple tickets selected:
- **M**: Move all to column
- **L**: Add label to all
- **P**: Set priority for all
- **Delete**: Delete all selected

---

## Archiving

### Archive Completed Work

1. Select tickets to archive
2. Click **Archive** or press `A`
3. Tickets move to archive

Or set up auto-archive:
1. Open board settings
2. Enable **Auto-archive completed**
3. Set delay (e.g., 7 days in Done)

### Viewing Archives

1. Click **View Archive** in sidebar
2. Browse archived tickets
3. Restore or permanently delete

---

## Board Settings

Access via gear icon or `Cmd+,`:

### General
- Board name and description
- Default column for new tickets
- Archive settings

### Columns
- Manage all columns
- Set default WIP limits
- Configure auto-archive

### Labels
- Manage label library
- Set default colors
- Delete unused labels

### AI Settings
- Enable/disable AI triage
- Configure auto-decompose
- Set suggestion frequency

---

## Tips for Effective Board Management

1. **Keep columns minimal** - 4-6 columns is optimal
2. **Use WIP limits** - Prevents overload
3. **Regular grooming** - Review backlog weekly
4. **Archive done items** - Keep board focused
5. **Consistent labels** - Use a defined set
6. **Enable AI triage** - Automate categorization

---

## Related Documentation

- [AI Features](ai-features.md) - Automate ticket management
- [Keyboard Shortcuts](keyboard-shortcuts.md) - Speed up your workflow
- [Tips & Tricks](tips-tricks.md) - Pro tips for power users
