-- Kanban AI SQLite Schema

-- ===========================================
-- BOARDS
-- ===========================================

CREATE TABLE IF NOT EXISTS boards (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ===========================================
-- COLUMNS
-- ===========================================

CREATE TABLE IF NOT EXISTS columns (
    id TEXT PRIMARY KEY NOT NULL,
    board_id TEXT NOT NULL,
    name TEXT NOT NULL,
    position INTEGER NOT NULL,
    color TEXT,
    wip_limit INTEGER,
    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);
CREATE INDEX IF NOT EXISTS idx_columns_position ON columns(position);

-- ===========================================
-- TICKETS
-- ===========================================

CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    column_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    effort TEXT CHECK(effort IN ('xs', 's', 'm', 'l', 'xl')),
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tickets_column_id ON tickets(column_id);
CREATE INDEX IF NOT EXISTS idx_tickets_position ON tickets(position);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_due_date ON tickets(due_date);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);

-- ===========================================
-- LABELS
-- ===========================================

CREATE TABLE IF NOT EXISTS labels (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_labels_name ON labels(name);

-- ===========================================
-- TICKET_LABELS (Many-to-Many)
-- ===========================================

CREATE TABLE IF NOT EXISTS ticket_labels (
    ticket_id TEXT NOT NULL,
    label_id TEXT NOT NULL,
    PRIMARY KEY (ticket_id, label_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ticket_labels_ticket_id ON ticket_labels(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_labels_label_id ON ticket_labels(label_id);

-- ===========================================
-- COMMENTS
-- ===========================================

CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY NOT NULL,
    ticket_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_comments_ticket_id ON comments(ticket_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at);

-- ===========================================
-- SUBTASKS
-- ===========================================

CREATE TABLE IF NOT EXISTS subtasks (
    id TEXT PRIMARY KEY NOT NULL,
    parent_ticket_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    completed INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (parent_ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subtasks_parent_ticket_id ON subtasks(parent_ticket_id);
CREATE INDEX IF NOT EXISTS idx_subtasks_position ON subtasks(position);

-- ===========================================
-- TRIGGERS (Auto-update updated_at)
-- ===========================================

CREATE TRIGGER IF NOT EXISTS update_boards_timestamp
AFTER UPDATE ON boards
FOR EACH ROW
BEGIN
    UPDATE boards SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_tickets_timestamp
AFTER UPDATE ON tickets
FOR EACH ROW
BEGIN
    UPDATE tickets SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_subtasks_timestamp
AFTER UPDATE ON subtasks
FOR EACH ROW
BEGIN
    UPDATE subtasks SET updated_at = datetime('now') WHERE id = NEW.id;
END;
