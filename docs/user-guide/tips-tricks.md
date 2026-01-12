# Tips & Tricks

Power user tips to get the most out of Kanban AI.

## Workflow Optimization

### Morning Routine

Start your day efficiently:

1. **Check Daily Summary** (`Cmd+Shift+S`)
   - Review your top 3 priorities
   - Note any blockers
   - Identify quick wins

2. **Process Backlog** (5 min)
   - Quick triage any new tickets
   - Move stale items to "Icebox" or delete
   - Check WIP limits

3. **Set Focus**
   - Pick your top task for the morning
   - Move it to "In Progress"
   - Close distractions

### End of Day

Before closing:

1. **Update ticket status**
   - Move completed items to Done
   - Add notes on incomplete work
   - Set reminders for tomorrow

2. **Review tomorrow**
   - Check upcoming due dates
   - Identify priorities
   - Note any blockers

---

## Ticket Writing Best Practices

### Title Guidelines

**Good Titles:**
```
Fix: Login button unresponsive on Safari iOS
Add: Dark mode toggle to settings page
Refactor: Extract authentication logic to service
```

**Avoid:**
```
Bug fix
New feature
Changes
```

### Description Template

Use this structure for clear tickets:

```markdown
## Problem
What is the issue or need?

## Expected Behavior
What should happen?

## Current Behavior
What happens now? (for bugs)

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes
Any implementation hints or constraints
```

### Using AI Effectively

For better AI suggestions:

1. **Be specific** - "Login fails" vs "Login button doesn't work on Safari iOS 17"
2. **Include context** - "Part of Q1 security initiative"
3. **Mention constraints** - "Must maintain backwards compatibility"

---

## Search Mastery

### Quick Search Patterns

| Pattern | Finds |
|---------|-------|
| `@me` | Tickets assigned to you |
| `#urgent` | Tickets with urgent label |
| `due:today` | Due today |
| `due:overdue` | Past due date |
| `priority:high` | High priority |
| `updated:today` | Modified today |

### Combining Searches

```
#bug priority:high due:this-week
```

### Semantic Search Tips

Instead of keywords, describe what you're looking for:
- "problems with user authentication"
- "slow loading issues"
- "styling inconsistencies"

---

## Command Palette Power

### Quick Actions

Type in command palette (`Cmd+K`):

| Command | Action |
|---------|--------|
| `>new Fix login bug` | Creates ticket with title |
| `>move #123 to Done` | Moves ticket |
| `>priority high` | Sets priority on selected |
| `>label #123 urgent` | Adds label |
| `>archive done` | Archives all done tickets |

### Navigation

| Command | Action |
|---------|--------|
| `@ticket-title` | Jump to ticket |
| `#label-name` | Filter by label |
| `/column-name` | Jump to column |
| `settings:ai` | Open AI settings |

---

## AI Chat Tricks

### Natural Language Commands

The AI understands context. Try:

```
"Create three tickets for the login refactor: one for backend, one for frontend, one for tests"

"What's the status of authentication-related tickets?"

"Move all critical bugs to the top of In Progress"

"Summarize what I accomplished this week"
```

### Building Context

The AI knows about your board. Ask:

- "What should I work on next?"
- "Are there any duplicate tickets?"
- "Which tickets are blocking others?"
- "What's the oldest item in backlog?"

### Getting Better Results

1. **Be specific** - "Create a ticket" vs "Create a high-priority bug ticket for the login issue we discussed"
2. **Provide context** - "Given that we're launching next week..."
3. **Iterate** - "Make that description more detailed"

---

## Board Organization

### Column Strategies

**Simple Flow:**
```
Backlog -> In Progress -> Done
```

**With Review:**
```
Backlog -> In Progress -> Review -> Done
```

**Full Process:**
```
Ideas -> Backlog -> Ready -> In Progress -> Review -> QA -> Done
```

### WIP Limit Guidelines

| Team Size | In Progress | Review |
|-----------|-------------|--------|
| 1 | 2-3 | 1-2 |
| 2-3 | 4-6 | 2-3 |
| 4-5 | 6-10 | 3-5 |

### Label System

Create a consistent label system:

**Type:**
- `bug` - Issues and defects
- `feature` - New functionality
- `refactor` - Code improvements
- `docs` - Documentation
- `chore` - Maintenance

**Area:**
- `frontend` - UI/UX work
- `backend` - API/server
- `infra` - DevOps/infrastructure
- `mobile` - Mobile-specific

**Status:**
- `blocked` - Waiting on something
- `needs-review` - Ready for review
- `wontfix` - Intentionally not fixing

---

## Keyboard Efficiency

### Speed Tips

1. **Stay on keyboard** - Avoid mouse for navigation
2. **Use quick priority** - `1-4` keys
3. **Chain commands** - `N` then type title, then `Enter`
4. **Master `Cmd+K`** - One shortcut for everything

### Custom Workflow

Set up shortcuts for your common actions:
1. Go to Settings > Keyboard
2. Identify frequent actions
3. Assign memorable shortcuts
4. Practice for a week

### Vim-Style Navigation

If you prefer vim:
- `h/j/k/l` for navigation
- `o` for new ticket below
- `O` for new ticket above
- `dd` for delete
- `/` for search

Enable in Settings > Keyboard > Vim Mode

---

## Automation Ideas

### Useful Rules

```
"When a ticket is labeled urgent, move it to In Progress"

"When a ticket is moved to Done, add the completed label"

"When a new high-priority ticket is created, notify me"

"When a ticket stays in Review for 3 days, add needs-attention label"
```

### Workflow Automation

1. **Auto-triage** - Let AI categorize new tickets
2. **Auto-archive** - Archive done items after 7 days
3. **Due date reminders** - Notify when deadlines approach
4. **WIP enforcement** - Prevent overloading columns

---

## Data Management

### Backup Your Data

1. Go to Settings > Data
2. Click "Export All"
3. Save JSON backup
4. Do this weekly

### Importing Data

From other tools:
1. Export from source (Trello, Jira, etc.)
2. Convert to Kanban AI format
3. Settings > Data > Import

### Bulk Operations

For major changes:
1. Switch to List view
2. Use filters to find tickets
3. Select multiple with `Cmd+Click`
4. Apply bulk action

---

## Performance Tips

### Keep Your Board Fast

1. **Archive completed work** - Don't let Done pile up
2. **Limit visible tickets** - Use filters
3. **Regular cleanup** - Weekly grooming
4. **Moderate attachments** - Large files slow things down

### When Things Slow Down

1. Archive old tickets
2. Clear browser cache
3. Restart the agent server
4. Check for updates

---

## Integration Tips

### With Git

Link tickets to commits:
```bash
git commit -m "Fix login bug (#ticket-123)"
```

### With Other Tools

- Export board as JSON for external processing
- Use API for custom integrations
- Webhooks for notifications (coming soon)

---

## Hidden Features

### Quick Ticket Clone

Hold `Opt` and drag a ticket to duplicate it.

### Collapse Columns

Double-click column header to collapse/expand.

### Ticket Preview

Hold `Space` over a ticket for quick preview without opening.

### Markdown Shortcuts

In description editor:
- Type `- ` for bullet list
- Type `1. ` for numbered list
- Type `## ` for heading
- Type `[text](url)` for link

### Time Tracking

Add time entries in ticket details:
- `2h` - 2 hours
- `30m` - 30 minutes
- `1d` - 1 day

---

## Troubleshooting Common Issues

### "AI Not Responding"

1. Check agent server is running
2. Verify API key in settings
3. Test network connectivity
4. Restart agent: `cd services/agent && uv run fastapi dev`

### "Slow Performance"

1. Archive completed tickets
2. Reduce visible tickets with filters
3. Close unused browser tabs
4. Check system resources

### "Data Not Saving"

1. Check disk space
2. Verify write permissions
3. Look for error in console
4. Restart application

### "Shortcuts Not Working"

1. Check focus is in app
2. Verify shortcut not overridden by system
3. Reset to defaults in Settings
4. Check for conflicting extensions

---

## Power User Checklist

Become a Kanban AI power user:

- [ ] Set up your ideal column structure
- [ ] Configure WIP limits
- [ ] Create a consistent label system
- [ ] Learn top 10 keyboard shortcuts
- [ ] Set up useful automation rules
- [ ] Enable AI triage
- [ ] Configure daily summary
- [ ] Set up backup routine
- [ ] Customize shortcuts for your workflow
- [ ] Master the command palette

---

## Related Documentation

- [Board Management](board-management.md) - Board fundamentals
- [AI Features](ai-features.md) - AI capabilities
- [Keyboard Shortcuts](keyboard-shortcuts.md) - Complete shortcut reference
