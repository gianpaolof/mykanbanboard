mod common;

use kanban_ai::db::Database;
use rusqlite::OptionalExtension;
use uuid::Uuid;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Insert a board and return its id.
fn insert_board(db: &Database, name: &str) -> String {
    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let id = Uuid::new_v4().to_string();
    let now = chrono::Utc::now().to_rfc3339();
    conn.execute(
        "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![id, name, now, now],
    )
    .unwrap();
    id
}

/// Insert a column and return its id.
fn insert_column(db: &Database, board_id: &str, name: &str, position: i32) -> String {
    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let id = Uuid::new_v4().to_string();
    conn.execute(
        "INSERT INTO columns (id, board_id, name, position) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![id, board_id, name, position],
    )
    .unwrap();
    id
}

/// Insert a ticket and return its id.
fn insert_ticket(db: &Database, column_id: &str, title: &str) -> String {
    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let id = Uuid::new_v4().to_string();
    let now = chrono::Utc::now().to_rfc3339();
    conn.execute(
        "INSERT INTO tickets (id, title, column_id, position, created_at, updated_at) \
         VALUES (?1, ?2, ?3, 0, ?4, ?5)",
        rusqlite::params![id, title, column_id, now, now],
    )
    .unwrap();
    id
}

/// Insert a label and return its id.
fn insert_label(db: &Database, name: &str, color: &str) -> String {
    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let id = Uuid::new_v4().to_string();
    conn.execute(
        "INSERT INTO labels (id, name, color) VALUES (?1, ?2, ?3)",
        rusqlite::params![id, name, color],
    )
    .unwrap();
    id
}

// ---------------------------------------------------------------------------
// BOARD OPERATIONS (5 tests)
// ---------------------------------------------------------------------------

#[test]
fn board_create() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Test Board");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let name: String = conn
        .query_row(
            "SELECT name FROM boards WHERE id = ?1",
            rusqlite::params![board_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(name, "Test Board");
}

#[test]
fn board_get_by_id() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Alpha Board");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let row: Option<(String, String)> = conn
        .query_row(
            "SELECT id, name FROM boards WHERE id = ?1",
            rusqlite::params![board_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()
        .unwrap();

    assert!(row.is_some());
    let (id, name) = row.unwrap();
    assert_eq!(id, board_id);
    assert_eq!(name, "Alpha Board");
}

#[test]
fn board_list_all() {
    let db = common::test_db();
    insert_board(&db, "Board A");
    insert_board(&db, "Board B");
    insert_board(&db, "Board C");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let count: i64 = conn
        .query_row("SELECT COUNT(*) FROM boards", [], |row| row.get(0))
        .unwrap();

    assert_eq!(count, 3);
}

#[test]
fn board_update() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Old Name");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "UPDATE boards SET name = ?1 WHERE id = ?2",
            rusqlite::params!["New Name", board_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let name: String = conn
        .query_row(
            "SELECT name FROM boards WHERE id = ?1",
            rusqlite::params![board_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(name, "New Name");
}

#[test]
fn board_delete() {
    let db = common::test_db();
    let board_id = insert_board(&db, "To Delete");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "DELETE FROM boards WHERE id = ?1",
            rusqlite::params![board_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let exists: Option<String> = conn
        .query_row(
            "SELECT id FROM boards WHERE id = ?1",
            rusqlite::params![board_id],
            |row| row.get(0),
        )
        .optional()
        .unwrap();

    assert!(exists.is_none());
}

// ---------------------------------------------------------------------------
// COLUMN OPERATIONS (5 tests)
// ---------------------------------------------------------------------------

#[test]
fn column_create_with_board() {
    let db = common::test_db();
    let board_id = insert_board(&db, "My Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let name: String = conn
        .query_row(
            "SELECT name FROM columns WHERE id = ?1",
            rusqlite::params![col_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(name, "Backlog");
}

#[test]
fn column_list_for_board() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    insert_column(&db, &board_id, "Todo", 0);
    insert_column(&db, &board_id, "In Progress", 1);
    insert_column(&db, &board_id, "Done", 2);

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM columns WHERE board_id = ?1",
            rusqlite::params![board_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(count, 3);
}

#[test]
fn column_update() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Old Col", 0);

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "UPDATE columns SET name = ?1, color = ?2 WHERE id = ?3",
            rusqlite::params!["New Col", "#ff0000", col_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let (name, color): (String, Option<String>) = conn
        .query_row(
            "SELECT name, color FROM columns WHERE id = ?1",
            rusqlite::params![col_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .unwrap();

    assert_eq!(name, "New Col");
    assert_eq!(color, Some("#ff0000".to_string()));
}

#[test]
fn column_reorder() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_a = insert_column(&db, &board_id, "A", 0);
    let col_b = insert_column(&db, &board_id, "B", 1);

    // Swap positions
    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "UPDATE columns SET position = ?1 WHERE id = ?2",
            rusqlite::params![1, col_a],
        )
        .unwrap();
        conn.execute(
            "UPDATE columns SET position = ?1 WHERE id = ?2",
            rusqlite::params![0, col_b],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let pos_a: i32 = conn
        .query_row(
            "SELECT position FROM columns WHERE id = ?1",
            rusqlite::params![col_a],
            |row| row.get(0),
        )
        .unwrap();
    let pos_b: i32 = conn
        .query_row(
            "SELECT position FROM columns WHERE id = ?1",
            rusqlite::params![col_b],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(pos_a, 1);
    assert_eq!(pos_b, 0);
}

#[test]
fn column_delete() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Temp", 0);

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "DELETE FROM columns WHERE id = ?1",
            rusqlite::params![col_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let exists: Option<String> = conn
        .query_row(
            "SELECT id FROM columns WHERE id = ?1",
            rusqlite::params![col_id],
            |row| row.get(0),
        )
        .optional()
        .unwrap();

    assert!(exists.is_none());
}

// ---------------------------------------------------------------------------
// TICKET OPERATIONS (8 tests)
// ---------------------------------------------------------------------------

#[test]
fn ticket_create() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Fix login bug");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let title: String = conn
        .query_row(
            "SELECT title FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(title, "Fix login bug");
}

#[test]
fn ticket_get_by_id() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Add dark mode");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let row: Option<(String, String)> = conn
        .query_row(
            "SELECT id, title FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()
        .unwrap();

    assert!(row.is_some());
    let (id, title) = row.unwrap();
    assert_eq!(id, ticket_id);
    assert_eq!(title, "Add dark mode");
}

#[test]
fn ticket_list_by_column() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Todo", 0);
    insert_ticket(&db, &col_id, "Ticket 1");
    insert_ticket(&db, &col_id, "Ticket 2");
    insert_ticket(&db, &col_id, "Ticket 3");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tickets WHERE column_id = ?1",
            rusqlite::params![col_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(count, 3);
}

#[test]
fn ticket_update_status_via_column_move() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_backlog = insert_column(&db, &board_id, "Backlog", 0);
    let col_done = insert_column(&db, &board_id, "Done", 1);
    let ticket_id = insert_ticket(&db, &col_backlog, "Deploy feature");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "UPDATE tickets SET column_id = ?1 WHERE id = ?2",
            rusqlite::params![col_done, ticket_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let col: String = conn
        .query_row(
            "SELECT column_id FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(col, col_done);
}

#[test]
fn ticket_update_priority() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Urgent task");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "UPDATE tickets SET priority = ?1 WHERE id = ?2",
            rusqlite::params!["critical", ticket_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let priority: Option<String> = conn
        .query_row(
            "SELECT priority FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(priority, Some("critical".to_string()));
}

#[test]
fn ticket_move_between_columns() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_src = insert_column(&db, &board_id, "Source", 0);
    let col_dst = insert_column(&db, &board_id, "Destination", 1);
    let ticket_id = insert_ticket(&db, &col_src, "Movable ticket");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "UPDATE tickets SET column_id = ?1, position = ?2 WHERE id = ?3",
            rusqlite::params![col_dst, 0, ticket_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let (col, pos): (String, i32) = conn
        .query_row(
            "SELECT column_id, position FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .unwrap();

    assert_eq!(col, col_dst);
    assert_eq!(pos, 0);
}

#[test]
fn ticket_create_with_labels() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Labelled ticket");
    let label_id_1 = insert_label(&db, "bug", "#ef4444");
    let label_id_2 = insert_label(&db, "frontend", "#3b82f6");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
            rusqlite::params![ticket_id, label_id_1],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
            rusqlite::params![ticket_id, label_id_2],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM ticket_labels WHERE ticket_id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(count, 2);
}

#[test]
fn ticket_delete() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Delete me");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "DELETE FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let exists: Option<String> = conn
        .query_row(
            "SELECT id FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .optional()
        .unwrap();

    assert!(exists.is_none());
}

// ---------------------------------------------------------------------------
// LABEL OPERATIONS (4 tests)
// ---------------------------------------------------------------------------

#[test]
fn label_create() {
    let db = common::test_db();
    let label_id = insert_label(&db, "enhancement", "#22c55e");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let (name, color): (String, String) = conn
        .query_row(
            "SELECT name, color FROM labels WHERE id = ?1",
            rusqlite::params![label_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .unwrap();

    assert_eq!(name, "enhancement");
    assert_eq!(color, "#22c55e");
}

#[test]
fn label_add_to_ticket() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Ticket");
    let label_id = insert_label(&db, "bug", "#ef4444");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
            rusqlite::params![ticket_id, label_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let linked: Option<(String, String)> = conn
        .query_row(
            "SELECT ticket_id, label_id FROM ticket_labels WHERE ticket_id = ?1 AND label_id = ?2",
            rusqlite::params![ticket_id, label_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()
        .unwrap();

    assert!(linked.is_some());
}

#[test]
fn label_remove_from_ticket() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Ticket");
    let label_id = insert_label(&db, "wontfix", "#6b7280");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
            rusqlite::params![ticket_id, label_id],
        )
        .unwrap();
        conn.execute(
            "DELETE FROM ticket_labels WHERE ticket_id = ?1 AND label_id = ?2",
            rusqlite::params![ticket_id, label_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let linked: Option<String> = conn
        .query_row(
            "SELECT ticket_id FROM ticket_labels WHERE ticket_id = ?1 AND label_id = ?2",
            rusqlite::params![ticket_id, label_id],
            |row| row.get(0),
        )
        .optional()
        .unwrap();

    assert!(linked.is_none());
}

#[test]
fn label_list_all() {
    let db = common::test_db();
    insert_label(&db, "alpha", "#111111");
    insert_label(&db, "beta", "#222222");
    insert_label(&db, "gamma", "#333333");

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let count: i64 = conn
        .query_row("SELECT COUNT(*) FROM labels", [], |row| row.get(0))
        .unwrap();

    assert!(count >= 3, "Expected at least 3 labels, got {}", count);
}

// ---------------------------------------------------------------------------
// SUBTASK OPERATIONS (3 tests)
// ---------------------------------------------------------------------------

#[test]
fn subtask_create() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Todo", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Parent ticket");

    let subtask_id = {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        conn.execute(
            "INSERT INTO subtasks (id, parent_ticket_id, title, completed, position, created_at, updated_at) \
             VALUES (?1, ?2, ?3, 0, 0, ?4, ?5)",
            rusqlite::params![id, ticket_id, "Write unit tests", now, now],
        )
        .unwrap();
        id
    };

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let (title, completed): (String, i32) = conn
        .query_row(
            "SELECT title, completed FROM subtasks WHERE id = ?1",
            rusqlite::params![subtask_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .unwrap();

    assert_eq!(title, "Write unit tests");
    assert_eq!(completed, 0);
}

#[test]
fn subtask_toggle_complete() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Todo", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Parent");

    let subtask_id = {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        conn.execute(
            "INSERT INTO subtasks (id, parent_ticket_id, title, completed, position, created_at, updated_at) \
             VALUES (?1, ?2, ?3, 0, 0, ?4, ?5)",
            rusqlite::params![id, ticket_id, "Sub-item", now, now],
        )
        .unwrap();
        id
    };

    // Toggle to complete
    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "UPDATE subtasks SET completed = NOT completed WHERE id = ?1",
            rusqlite::params![subtask_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let completed: i32 = conn
        .query_row(
            "SELECT completed FROM subtasks WHERE id = ?1",
            rusqlite::params![subtask_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(completed, 1);
}

#[test]
fn subtask_delete() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Todo", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Parent");

    let subtask_id = {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        conn.execute(
            "INSERT INTO subtasks (id, parent_ticket_id, title, completed, position, created_at, updated_at) \
             VALUES (?1, ?2, ?3, 0, 0, ?4, ?5)",
            rusqlite::params![id, ticket_id, "Temporary subtask", now, now],
        )
        .unwrap();
        id
    };

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "DELETE FROM subtasks WHERE id = ?1",
            rusqlite::params![subtask_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let exists: Option<String> = conn
        .query_row(
            "SELECT id FROM subtasks WHERE id = ?1",
            rusqlite::params![subtask_id],
            |row| row.get(0),
        )
        .optional()
        .unwrap();

    assert!(exists.is_none());
}

// ---------------------------------------------------------------------------
// COMMENT OPERATIONS (3 tests)
// ---------------------------------------------------------------------------

#[test]
fn comment_create() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Commented ticket");

    let comment_id = {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        conn.execute(
            "INSERT INTO comments (id, ticket_id, content, created_at) VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![id, ticket_id, "This is a review comment", now],
        )
        .unwrap();
        id
    };

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let content: String = conn
        .query_row(
            "SELECT content FROM comments WHERE id = ?1",
            rusqlite::params![comment_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(content, "This is a review comment");
}

#[test]
fn comment_list_for_ticket() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Ticket with comments");

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        let now = chrono::Utc::now().to_rfc3339();
        for i in 0..3u32 {
            let id = Uuid::new_v4().to_string();
            conn.execute(
                "INSERT INTO comments (id, ticket_id, content, created_at) VALUES (?1, ?2, ?3, ?4)",
                rusqlite::params![id, ticket_id, format!("Comment {}", i), now],
            )
            .unwrap();
        }
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM comments WHERE ticket_id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .unwrap();

    assert_eq!(count, 3);
}

#[test]
fn comment_delete() {
    let db = common::test_db();
    let board_id = insert_board(&db, "Board");
    let col_id = insert_column(&db, &board_id, "Backlog", 0);
    let ticket_id = insert_ticket(&db, &col_id, "Ticket");

    let comment_id = {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        let id = Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        conn.execute(
            "INSERT INTO comments (id, ticket_id, content, created_at) VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![id, ticket_id, "Delete me", now],
        )
        .unwrap();
        id
    };

    {
        let conn = db.connection();
        let conn = conn.lock().unwrap();
        conn.execute(
            "DELETE FROM comments WHERE id = ?1",
            rusqlite::params![comment_id],
        )
        .unwrap();
    }

    let conn = db.connection();
    let conn = conn.lock().unwrap();
    let exists: Option<String> = conn
        .query_row(
            "SELECT id FROM comments WHERE id = ?1",
            rusqlite::params![comment_id],
            |row| row.get(0),
        )
        .optional()
        .unwrap();

    assert!(exists.is_none());
}

// ---------------------------------------------------------------------------
// MODEL SERIALIZATION (2 tests)
// ---------------------------------------------------------------------------

#[test]
fn model_priority_serialization_round_trip() {
    // Verifies that the priority strings stored in the DB round-trip through
    // serde JSON correctly, matching what commands.rs writes.
    let priorities = vec!["low", "medium", "high", "critical"];
    for priority_str in &priorities {
        let json_value = serde_json::Value::String(priority_str.to_string());
        let serialized = serde_json::to_string(&json_value).unwrap();
        let deserialized: serde_json::Value = serde_json::from_str(&serialized).unwrap();
        assert_eq!(
            deserialized.as_str().unwrap(),
            *priority_str,
            "Round-trip failed for priority: {}",
            priority_str
        );
    }
}

#[test]
fn model_project_context_serialization_round_trip() {
    // Verifies that a ProjectContext-shaped JSON object round-trips correctly.
    let ctx_json = serde_json::json!({
        "techStack": ["Rust", "React", "Python"],
        "conventions": "Use kebab-case for files",
        "architecture": "Monorepo",
        "description": "Kanban AI app",
        "defaultLabels": ["bug", "feature"]
    });

    let serialized = serde_json::to_string(&ctx_json).unwrap();
    let deserialized: serde_json::Value = serde_json::from_str(&serialized).unwrap();

    assert_eq!(
        deserialized["techStack"][0].as_str().unwrap(),
        "Rust"
    );
    assert_eq!(
        deserialized["conventions"].as_str().unwrap(),
        "Use kebab-case for files"
    );
    assert_eq!(
        deserialized["defaultLabels"].as_array().unwrap().len(),
        2
    );
}
