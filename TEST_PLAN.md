# Kanban AI - Test Plan

Comprehensive test plan covering all features of the Kanban AI application.

## Test Environment Setup

### Prerequisites
- [ ] Node.js 18+ installed
- [ ] Rust toolchain installed
- [ ] Python 3.11+ with uv installed
- [ ] Tauri CLI installed

### Start Application
```bash
# Terminal 1: Start frontend dev server
cd apps/desktop && pnpm tauri dev

# Terminal 2: Start AI agent (optional, for AI features)
cd services/agent && uv run fastapi dev
```

---

## 1. Board Management

### 1.1 Default Board
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Default board created on first launch | Launch app for first time | "My Board" appears with 5 default columns |
| Default columns exist | Check columns | Backlog, To Do, In Progress, Review, Done |

### 1.2 Multi-Board Support
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Create new board | Click board switcher > "New Board" | Modal opens, can enter name |
| Board appears in list | Create board "Test Board" | New board shows in switcher dropdown |
| Switch between boards | Click different board in switcher | Board context changes, tickets update |
| Board isolation | Create tickets in Board A, switch to Board B | Board B doesn't show Board A tickets |
| Rename board | Click board menu > Rename | Board name updates in header and sidebar |
| Delete board | Click board menu > Delete > Confirm | Board removed, switches to another board |
| Cannot delete last board | Try to delete when only 1 board exists | Error message, delete blocked |

### 1.3 Board Switcher UI
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Dropdown opens | Click board name in header | Dropdown shows all boards |
| Board count shown | Check dropdown items | Each board shows ticket count |
| Search boards | Type in search field (if exists) | Boards filter by name |
| Create from dropdown | Click "+ New Board" in dropdown | Create modal opens |

---

## 2. Column Management

### 2.1 Column CRUD
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Add column | Click "+" or "Add Column" button | New column appears at end |
| Rename column | Double-click column name or use menu | Can edit column name inline |
| Delete empty column | Delete column with no tickets | Column removed |
| Delete column with tickets | Try to delete column with tickets | Error: must move tickets first |
| Column color | Set column color | Column header shows color |

### 2.2 Column Reordering
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Drag column left | Drag "In Progress" before "To Do" | Columns reorder, persists on reload |
| Drag column right | Drag first column to end | Order updates correctly |
| Cancel drag | Press Escape during drag | Column returns to original position |

### 2.3 WIP Limits (if implemented)
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Set WIP limit | Set column WIP to 3 | Limit indicator shown |
| Exceed WIP limit | Add 4th ticket to column with WIP=3 | Warning shown, column highlighted |

---

## 3. Ticket Management

### 3.1 Ticket CRUD
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Create ticket (modal) | Click "+" in column or ⌘N | Modal opens with form |
| Create with title only | Enter title, leave description empty | Ticket created successfully |
| Create with all fields | Fill title, description, priority, effort, labels, due date | All fields saved |
| Open ticket modal | Click on ticket | Modal opens showing all details |
| Edit ticket title | Edit title in modal | Title updates, visible in board |
| Edit ticket description | Edit description (markdown) | Description saves |
| Delete ticket | Click delete in modal/context menu > Confirm | Ticket removed from board |

### 3.2 Ticket Properties
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Set priority | Select Low/Medium/High/Critical | Priority badge shows with correct color |
| Set effort | Select XS/S/M/L/XL | Effort indicator appears |
| Set due date | Pick date in calendar | Due date shown, color codes by urgency |
| Clear due date | Remove date | Due date indicator removed |
| Add labels | Select existing labels or create new | Labels appear as colored chips |
| Remove labels | Click X on label | Label removed from ticket |

### 3.3 Drag & Drop
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Move within column | Drag ticket up/down in same column | Position updates |
| Move to different column | Drag ticket to another column | Ticket moves, status implied by column |
| Drop at specific position | Drag between two tickets | Ticket inserted at correct position |
| Cancel drag | Press Escape or drop outside | Ticket returns to original position |
| Visual feedback | Start dragging | Ghost preview, drop zones highlighted |

---

## 4. Subtasks/Checklists

### 4.1 Subtask CRUD
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Add subtask | Open ticket modal > Add subtask | New subtask input appears |
| Create subtask | Type title, press Enter | Subtask created with checkbox |
| Toggle subtask | Click checkbox | Subtask marked complete/incomplete |
| Edit subtask | Click on subtask title | Can edit inline |
| Delete subtask | Click X or delete button | Subtask removed |

### 4.2 Subtask Progress
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Progress bar | Complete 2 of 4 subtasks | Progress bar shows 50% |
| All complete | Complete all subtasks | Progress bar shows 100% |
| Progress on card | Check ticket card on board | Subtask count/progress visible |

### 4.3 AI Decompose
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Decompose ticket | Click "AI Decompose" button | AI generates subtasks |
| Subtasks created | Wait for AI response | 3-7 subtasks added to ticket |
| Subtask details | Check generated subtasks | Each has title, optional description |

---

## 5. Labels

### 5.1 Label CRUD
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Create label | In ticket modal or label manager | New label with name and color |
| Edit label | Change label name/color | All tickets with label updated |
| Delete label | Remove label | Label removed from all tickets |
| Label colors | Create labels with different colors | Colors display correctly |

### 5.2 Label Assignment
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Add label to ticket | Select label in ticket modal | Label appears on ticket card |
| Multiple labels | Add 3+ labels | All labels shown (or +N indicator) |
| Remove label | Unselect or click X | Label removed from ticket |
| Filter by label | Click label in filter | Only tickets with label shown |

---

## 6. Search & Filter

### 6.1 Text Search
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Search by title | Type in search bar | Tickets matching title shown |
| Search by description | Search for text in description | Matching tickets found |
| Clear search | Click X or clear input | All tickets visible again |
| No results | Search for non-existent text | "No results" message |

### 6.2 Filters
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Filter by priority | Select "High" priority | Only high priority tickets shown |
| Filter by multiple priorities | Select High + Critical | Both shown |
| Filter by label | Select specific label | Only labeled tickets shown |
| Combine filters | Priority=High AND Label="bug" | Intersection shown |
| Clear filters | Click "Clear" or remove selections | All tickets visible |
| Filter persists | Apply filter, switch views | Filter remains active |

---

## 7. Calendar View

### 7.1 Calendar Display
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Switch to calendar | Click Calendar view or ⌘4 | Month grid displayed |
| Current month | Open calendar view | Current month shown with today highlighted |
| Navigate months | Click prev/next arrows | Month changes correctly |
| Today button | Click "Today" | Returns to current month, today highlighted |

### 7.2 Tickets on Calendar
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Tickets on due dates | Create ticket with due date | Ticket appears on that date |
| Multiple tickets same day | 3 tickets due same day | All shown or "+N" indicator |
| Priority colors | Tickets with different priorities | Color-coded by priority |
| Click date | Click on a date | Sidebar shows tickets for that date |
| Unscheduled tickets | Tickets without due date | Shown in "Unscheduled" sidebar section |

### 7.3 Calendar Interactions
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Click ticket in calendar | Click on ticket indicator | Ticket modal opens |
| Quick add from date | Click "+" on date (if exists) | Create ticket with that due date |

---

## 8. Views & Navigation

### 8.1 View Switching
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Board view (⌘1) | Press ⌘1 or click Board | Kanban board displayed |
| List view (⌘2) | Press ⌘2 or click List | List view displayed (or "coming soon") |
| Timeline view (⌘3) | Press ⌘3 or click Timeline | Timeline displayed (or "coming soon") |
| Calendar view (⌘4) | Press ⌘4 or click Calendar | Calendar month grid displayed |
| View persists | Change view, reload app | Same view shown |

### 8.2 Sidebar
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Toggle sidebar (⌘/) | Press ⌘/ | Sidebar collapses/expands |
| Sidebar shows boards | Check sidebar | All boards listed |
| Quick board switch | Click board in sidebar | Board changes |

---

## 9. Command Palette

### 9.1 Open & Close
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Open palette | Press ⌘K | Command palette modal opens |
| Close palette | Press Escape or click outside | Palette closes |
| Close on action | Select a command | Palette closes, action executes |

### 9.2 Commands
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Search commands | Type "new" | "New Ticket" and similar commands shown |
| Create ticket | Select "New Ticket" | Create ticket modal opens |
| Switch board | Select a board name | Board switches |
| Change view | Select "Calendar View" | View changes |
| Open AI | Select "Ask AI" or ⌘⇧A | AI panel opens |

---

## 10. AI Agent Features

### 10.1 Agent Connectivity
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Agent running | Start agent server | Health check returns true |
| Agent not running | Stop agent server | Graceful fallback, error shown |
| Agent reconnect | Stop then start agent | Features work again |

### 10.2 Auto-Triage
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Triage new ticket | Create ticket > "AI Triage" | Priority, effort, labels assigned |
| Triage accuracy | Check assigned values | Reasonable for ticket content |
| Triage explanation | Check reasoning | AI provides reasoning |

### 10.3 AI Chat
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Open AI panel | Press ⌘⇧A or click AI button | Chat panel opens |
| Send message | Type and send message | AI responds |
| Action execution | "Create a ticket called Test" | Ticket created via AI |
| Context awareness | "Move this to Done" with ticket selected | Correct ticket moved |
| Conversation history | Multiple back-and-forth | Context maintained |

### 10.4 Daily Summary
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Request summary | ⌘⇧S or "Daily Summary" | Summary generated |
| Summary content | Check summary | Lists focus areas, blockers, quick wins |

### 10.5 Semantic Search
| Test | Steps | Expected Result |
|------|-------|-----------------|
| AI search | Use AI search feature | Semantically similar tickets found |
| Relevance | Search "login issues" | Auth/login tickets ranked high |

---

## 11. Automation Rules

### 11.1 Rules Panel
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Open rules panel | Click Automations/Zap icon | Automation panel opens |
| Empty state | No rules created | "No rules" message, add button |
| Close panel | Click X or outside | Panel closes |

### 11.2 Create Rules (Natural Language)
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Open create form | Click "+ Add Rule" | NL input form appears |
| Parse rule | Type "When ticket moves to Done, add completed label" | AI parses trigger & action |
| Rule created | Confirm creation | Rule appears in list |
| Parsing error | Enter gibberish | Error message, retry option |

### 11.3 Rule Examples
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Ticket moved trigger | "When moved to Done, add done label" | trigger: ticket_moved, action: add_label |
| Priority change trigger | "When priority set to critical, notify me" | trigger: priority_changed, action: notify |
| Ticket created trigger | "When ticket created, run triage" | trigger: ticket_created, action: auto_triage |
| Due date trigger | "When due in 2 days, add urgent label" | trigger: due_date_approaching, action: add_label |

### 11.4 Rule Management
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Toggle rule on/off | Click power icon | Rule enabled/disabled |
| Delete rule | Click trash icon > Confirm | Rule removed |
| Rule stats | Check rule card | Shows trigger count, last triggered |

### 11.5 Rule Execution (if implemented)
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Rule triggers | Move ticket to Done (with matching rule) | Action executes automatically |
| Multiple rules | Create multiple matching rules | All applicable rules execute |
| Disabled rule | Disable rule, trigger event | Rule does not execute |

---

## 12. Keyboard Shortcuts

| Shortcut | Action | Test |
|----------|--------|------|
| ⌘K | Command Palette | Opens command palette |
| ⌘N | New Ticket | Opens create ticket modal |
| ⌘⇧A | AI Chat | Opens AI panel |
| ⌘⇧S | Daily Summary | Generates daily summary |
| ⌘1 | Board View | Switches to board |
| ⌘2 | List View | Switches to list |
| ⌘3 | Timeline View | Switches to timeline |
| ⌘4 | Calendar View | Switches to calendar |
| ⌘, | Settings | Opens settings |
| ⌘/ | Toggle Sidebar | Collapses/expands sidebar |
| Escape | Close Modal | Closes any open modal |

---

## 13. Data Persistence

### 13.1 Local Storage
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Tickets persist | Create ticket, reload app | Ticket still exists |
| Boards persist | Create board, reload | Board still exists |
| Labels persist | Create labels, reload | Labels still exist |
| Column order persists | Reorder columns, reload | Order maintained |
| Subtasks persist | Create subtasks, reload | Subtasks still exist |
| Automation rules persist | Create rule, reload | Rule still exists |

### 13.2 Data Integrity
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Cascade delete column | Delete column (empty) | Column removed, no orphans |
| Cascade delete ticket | Delete ticket | Subtasks deleted, labels unlinked |
| Cascade delete board | Delete board | All columns, tickets deleted |
| Cascade delete rule | Delete rule on board | Rule removed |

---

## 14. Error Handling

### 14.1 User Feedback
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Success toast | Create ticket | "Ticket created" toast shown |
| Error toast | Force an error | Red error toast with message |
| Loading states | Slow operation | Loading spinner shown |
| Empty states | Empty board | Helpful empty state message |

### 14.2 Edge Cases
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Very long title | 500+ character title | Truncated display, full on hover |
| Special characters | Title with <>&"' | Characters escaped, display correctly |
| Concurrent edits | Edit same ticket in 2 windows | Last write wins, no crash |
| Offline mode | Disconnect network | Graceful handling (local app) |

---

## 15. Performance

### 15.1 Load Testing
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Many tickets | Create 100 tickets | App remains responsive |
| Many columns | Create 20 columns | Scrolling smooth |
| Many boards | Create 20 boards | Switcher loads quickly |
| Many subtasks | 50 subtasks on ticket | Modal loads quickly |
| Many rules | 50 automation rules | Rules panel loads quickly |

### 15.2 Memory
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Long session | Use app for 1 hour | No memory leaks |
| View switching | Switch views 50 times | No slowdown |

---

## 16. Theme & UI

### 16.1 Theme Toggle
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Toggle dark/light | Click theme toggle | Theme switches |
| Theme persists | Change theme, reload | Theme maintained |
| Consistent colors | Check all components | Colors consistent with theme |

### 16.2 Responsive Design
| Test | Steps | Expected Result |
|------|-------|-----------------|
| Resize window | Make window smaller | Layout adapts |
| Minimum size | Resize to minimum | Content still usable |
| Column scrolling | Many columns | Horizontal scroll works |

---

## Test Execution Log

| Date | Tester | Section | Pass/Fail | Notes |
|------|--------|---------|-----------|-------|
|      |        |         |           |       |

---

## Known Issues / Limitations

1. List and Timeline views show "coming soon"
2. Automation rule execution not yet integrated into ticket actions
3. WIP limits UI not implemented
4. Offline sync not implemented

---

## Regression Testing

After any code change, run these critical paths:
1. Create board > Create ticket > Move ticket > Delete ticket
2. Switch boards > Verify isolation
3. Add subtasks > Toggle complete > Delete
4. Open calendar > Navigate months > Check tickets
5. Create automation rule > Toggle enable/disable
6. AI triage on new ticket (if agent running)
