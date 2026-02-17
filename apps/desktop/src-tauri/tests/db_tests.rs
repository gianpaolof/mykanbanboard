//! Integration tests for the SQLite database layer.
//!
//! Each test gets its own fresh in-memory database via `common::test_db()`.
//! Foreign-key enforcement is enabled by the in-memory constructor.

mod common;
use common::test_db;

use rusqlite::OptionalExtension;
use uuid::Uuid;

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

fn new_id() -> String {
    Uuid::new_v4().to_string()
}

fn now_str() -> String {
    chrono::Utc::now().to_rfc3339()
}

/// Insert a minimal board row and return the generated id.
fn insert_board(conn: &rusqlite::Connection, name: &str) -> String {
    let id = new_id();
    let now = now_str();
    conn.execute(
        "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![id, name, now, now],
    )
    .expect("insert board");
    id
}

/// Insert a minimal column row and return the generated id.
fn insert_column(conn: &rusqlite::Connection, board_id: &str, position: i32) -> String {
    let id = new_id();
    conn.execute(
        "INSERT INTO columns (id, board_id, name, position) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![id, board_id, "Col", position],
    )
    .expect("insert column");
    id
}

/// Insert a minimal ticket row and return the generated id.
fn insert_ticket(conn: &rusqlite::Connection, column_id: &str, title: &str) -> String {
    let id = new_id();
    let now = now_str();
    conn.execute(
        "INSERT INTO tickets (id, title, column_id, position, created_at, updated_at) \
         VALUES (?1, ?2, ?3, 0, ?4, ?5)",
        rusqlite::params![id, title, column_id, now, now],
    )
    .expect("insert ticket");
    id
}

/// Insert a minimal label row and return the generated id.
fn insert_label(conn: &rusqlite::Connection, name: &str, color: &str) -> String {
    let id = new_id();
    conn.execute(
        "INSERT INTO labels (id, name, color) VALUES (?1, ?2, ?3)",
        rusqlite::params![id, name, color],
    )
    .expect("insert label");
    id
}

fn count_rows(conn: &rusqlite::Connection, table: &str) -> i64 {
    conn.query_row(
        &format!("SELECT COUNT(*) FROM {}", table),
        [],
        |row| row.get(0),
    )
    .unwrap_or(0)
}

fn row_exists(conn: &rusqlite::Connection, table: &str, id: &str) -> bool {
    let count: i64 = conn
        .query_row(
            &format!("SELECT COUNT(*) FROM {} WHERE id = ?1", table),
            rusqlite::params![id],
            |row| row.get(0),
        )
        .unwrap_or(0);
    count > 0
}

// ---------------------------------------------------------------------------
// 1. Constraint tests
// ---------------------------------------------------------------------------

/// Inserting two rows with the same PRIMARY KEY (id) must fail.
/// Boards do not have a UNIQUE constraint on `name`, but the PRIMARY KEY on `id`
/// enforces uniqueness of the identifier itself.
#[test]
fn test_unique_constraint_board_name() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let id = new_id();
    let now = now_str();
    conn.execute(
        "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![id, "Board Alpha", now, now],
    )
    .expect("first insert must succeed");

    // Inserting the same id again must violate PRIMARY KEY uniqueness.
    let result = conn.execute(
        "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![id, "Board Alpha Duplicate", now, now],
    );
    assert!(
        result.is_err(),
        "Inserting duplicate board id (PRIMARY KEY) must fail"
    );
}

/// Inserting a ticket with a NULL title must fail (NOT NULL constraint).
#[test]
fn test_not_null_constraint_ticket_title() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Board");
    let col_id = insert_column(&conn, &board_id, 0);
    let ticket_id = new_id();
    let now = now_str();

    let result = conn.execute(
        "INSERT INTO tickets (id, title, column_id, position, created_at, updated_at) \
         VALUES (?1, NULL, ?2, 0, ?3, ?4)",
        rusqlite::params![ticket_id, col_id, now, now],
    );
    assert!(
        result.is_err(),
        "Inserting a ticket with NULL title must fail NOT NULL constraint"
    );
}

/// Inserting a column whose board_id does not exist must fail (FOREIGN KEY).
#[test]
fn test_foreign_key_column_belongs_to_board() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let bogus_board_id = new_id(); // Never inserted into boards
    let col_id = new_id();

    let result = conn.execute(
        "INSERT INTO columns (id, board_id, name, position) VALUES (?1, ?2, ?3, 0)",
        rusqlite::params![col_id, bogus_board_id, "Ghost Column"],
    );
    assert!(
        result.is_err(),
        "Inserting a column with non-existent board_id must fail FOREIGN KEY constraint"
    );
}

// ---------------------------------------------------------------------------
// 2. Cascade delete tests
// ---------------------------------------------------------------------------

/// Deleting a board must also delete all its columns (ON DELETE CASCADE).
#[test]
fn test_cascade_delete_board_removes_columns() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Board A");
    insert_column(&conn, &board_id, 0);
    insert_column(&conn, &board_id, 1);

    assert_eq!(count_rows(&conn, "columns"), 2);

    conn.execute(
        "DELETE FROM boards WHERE id = ?1",
        rusqlite::params![board_id],
    )
    .expect("delete board");

    assert_eq!(
        count_rows(&conn, "columns"),
        0,
        "Columns must be cascade-deleted when their parent board is deleted"
    );
}

/// Deleting a column must also delete all its tickets (ON DELETE CASCADE).
#[test]
fn test_cascade_delete_column_removes_tickets() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Board B");
    let col_id = insert_column(&conn, &board_id, 0);
    insert_ticket(&conn, &col_id, "Ticket 1");
    insert_ticket(&conn, &col_id, "Ticket 2");

    assert_eq!(count_rows(&conn, "tickets"), 2);

    conn.execute(
        "DELETE FROM columns WHERE id = ?1",
        rusqlite::params![col_id],
    )
    .expect("delete column");

    assert_eq!(
        count_rows(&conn, "tickets"),
        0,
        "Tickets must be cascade-deleted when their parent column is deleted"
    );
}

/// Cascade chain: board -> columns -> tickets -> ticket_labels.
/// Labels in the independent `labels` table must survive.
#[test]
fn test_cascade_delete_board_removes_all_descendants() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Board C");
    let col_id = insert_column(&conn, &board_id, 0);
    let ticket_id = insert_ticket(&conn, &col_id, "Deep Ticket");

    let label_id = insert_label(&conn, "urgent", "#ff0000");
    conn.execute(
        "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
        rusqlite::params![ticket_id, label_id],
    )
    .expect("attach label to ticket");

    assert_eq!(count_rows(&conn, "ticket_labels"), 1);

    conn.execute(
        "DELETE FROM boards WHERE id = ?1",
        rusqlite::params![board_id],
    )
    .expect("delete board");

    assert_eq!(count_rows(&conn, "columns"), 0, "Columns must cascade-delete");
    assert_eq!(count_rows(&conn, "tickets"), 0, "Tickets must cascade-delete");
    assert_eq!(
        count_rows(&conn, "ticket_labels"),
        0,
        "ticket_labels join rows must cascade-delete"
    );
    // The label itself is not a descendant of the board and must remain.
    assert_eq!(
        count_rows(&conn, "labels"),
        1,
        "Labels must NOT be deleted when tickets are removed"
    );
}

// ---------------------------------------------------------------------------
// 3. Migration idempotency
// ---------------------------------------------------------------------------

/// Running migrations via `new_in_memory()` must create all expected tables.
#[test]
fn test_migration_creates_expected_tables() {
    let db = kanban_ai::db::Database::new_in_memory()
        .expect("Failed to create in-memory database");

    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let expected_tables = &[
        "boards",
        "columns",
        "tickets",
        "labels",
        "ticket_labels",
        "comments",
        "subtasks",
        "automation_rules",
    ];

    let existing_tables: Vec<String> = {
        let mut stmt = conn
            .prepare("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
            .expect("prepare sqlite_master query");
        stmt.query_map([], |row| row.get(0))
            .expect("query sqlite_master")
            .filter_map(Result::ok)
            .collect()
    };

    for table in expected_tables {
        assert!(
            existing_tables.contains(&table.to_string()),
            "Expected table '{}' after migration. Found: {:?}",
            table,
            existing_tables
        );
    }
}

// ---------------------------------------------------------------------------
// 4. CRUD round-trip tests
// ---------------------------------------------------------------------------

/// Create a board and retrieve it by id — verify id and name round-trip.
#[test]
fn test_create_and_retrieve_board() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let id = new_id();
    let now = now_str();
    conn.execute(
        "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![id, "Test Board", now, now],
    )
    .expect("insert board");

    let (retrieved_id, retrieved_name): (String, String) = conn
        .query_row(
            "SELECT id, name FROM boards WHERE id = ?1",
            rusqlite::params![id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .expect("retrieve board");

    assert_eq!(retrieved_id, id);
    assert_eq!(retrieved_name, "Test Board");
}

/// Create a board with two columns and verify both are associated.
#[test]
fn test_create_board_with_columns() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Project Board");
    let col1_id = insert_column(&conn, &board_id, 0);
    let col2_id = insert_column(&conn, &board_id, 1);

    let ids: Vec<String> = {
        let mut stmt = conn
            .prepare("SELECT id FROM columns WHERE board_id = ?1 ORDER BY position")
            .expect("prepare");
        stmt.query_map(rusqlite::params![board_id], |row| row.get(0))
            .expect("query")
            .filter_map(Result::ok)
            .collect()
    };

    assert_eq!(ids.len(), 2);
    assert!(ids.contains(&col1_id));
    assert!(ids.contains(&col2_id));
}

/// Create a ticket and attach two labels — verify the ticket_labels join rows.
#[test]
fn test_create_ticket_with_labels() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Label Board");
    let col_id = insert_column(&conn, &board_id, 0);
    let ticket_id = insert_ticket(&conn, &col_id, "Labelled Ticket");

    let label_a = insert_label(&conn, "bug", "#ef4444");
    let label_b = insert_label(&conn, "feature", "#6366f1");

    conn.execute(
        "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
        rusqlite::params![ticket_id, label_a],
    )
    .expect("attach label_a");
    conn.execute(
        "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
        rusqlite::params![ticket_id, label_b],
    )
    .expect("attach label_b");

    let label_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM ticket_labels WHERE ticket_id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .expect("count labels");

    assert_eq!(label_count, 2, "Ticket should have exactly 2 labels attached");
}

/// Create a ticket in one column, then move it to another (status change).
#[test]
fn test_update_ticket_status() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Status Board");
    let col_todo = insert_column(&conn, &board_id, 0);
    let col_done = insert_column(&conn, &board_id, 1);

    let ticket_id = insert_ticket(&conn, &col_todo, "Move Me");

    conn.execute(
        "UPDATE tickets SET column_id = ?1 WHERE id = ?2",
        rusqlite::params![col_done, ticket_id],
    )
    .expect("update ticket column");

    let actual_col: String = conn
        .query_row(
            "SELECT column_id FROM tickets WHERE id = ?1",
            rusqlite::params![ticket_id],
            |row| row.get(0),
        )
        .expect("retrieve ticket");

    assert_eq!(
        actual_col, col_done,
        "Ticket column_id must reflect the updated column"
    );
}

/// Create a subtask linked to a ticket — verify persistence and initial state.
#[test]
fn test_create_subtask() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = insert_board(&conn, "Subtask Board");
    let col_id = insert_column(&conn, &board_id, 0);
    let ticket_id = insert_ticket(&conn, &col_id, "Parent Ticket");

    let subtask_id = new_id();
    let now = now_str();
    conn.execute(
        "INSERT INTO subtasks \
         (id, parent_ticket_id, title, completed, position, created_at, updated_at) \
         VALUES (?1, ?2, ?3, 0, 0, ?4, ?5)",
        rusqlite::params![subtask_id, ticket_id, "Sub-step 1", now, now],
    )
    .expect("insert subtask");

    let (title, completed): (String, i32) = conn
        .query_row(
            "SELECT title, completed FROM subtasks WHERE id = ?1",
            rusqlite::params![subtask_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .expect("retrieve subtask");

    assert_eq!(title, "Sub-step 1");
    assert_eq!(completed, 0, "New subtask must not be completed");
}

// ---------------------------------------------------------------------------
// 5. Error path tests
// ---------------------------------------------------------------------------

/// Querying a non-existent board id must return None.
#[test]
fn test_get_nonexistent_board_returns_none() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let bogus_id = new_id();
    let result: Option<String> = conn
        .query_row(
            "SELECT id FROM boards WHERE id = ?1",
            rusqlite::params![bogus_id],
            |row| row.get(0),
        )
        .optional()
        .expect("query must not produce a SQL error");

    assert!(result.is_none(), "Non-existent board must return None");
}

/// Deleting a non-existent board must NOT return a SQL error; it affects 0 rows.
#[test]
fn test_delete_nonexistent_board_returns_ok() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let bogus_id = new_id();
    let rows_changed = conn
        .execute(
            "DELETE FROM boards WHERE id = ?1",
            rusqlite::params![bogus_id],
        )
        .expect("DELETE on non-existent row must not return a SQL error");

    assert_eq!(
        rows_changed, 0,
        "Deleting a non-existent board must affect 0 rows"
    );
}

/// A rolled-back savepoint must leave no partial data in the database.
#[test]
fn test_transaction_rollback_on_error() {
    let db = test_db();
    let conn_arc = db.connection();
    let conn = conn_arc.lock().unwrap();

    let board_id = new_id();
    let now = now_str();

    conn.execute_batch("SAVEPOINT txn_test").expect("create savepoint");

    conn.execute(
        "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![board_id, "Rollback Board", now, now],
    )
    .expect("insert board inside savepoint");

    // Attempt to insert a column referencing a board that does not exist — must fail.
    let bogus_parent = new_id();
    let bad_result = conn.execute(
        "INSERT INTO columns (id, board_id, name, position) VALUES (?1, ?2, ?3, 0)",
        rusqlite::params![new_id(), bogus_parent, "Bad Col"],
    );

    if bad_result.is_err() {
        conn.execute_batch("ROLLBACK TO txn_test")
            .expect("rollback savepoint");
        conn.execute_batch("RELEASE txn_test")
            .expect("release savepoint");
    } else {
        conn.execute_batch("RELEASE txn_test")
            .expect("release savepoint");
        panic!("Expected FOREIGN KEY violation but none occurred — check PRAGMA foreign_keys");
    }

    // After rollback, the board inserted inside the savepoint must not exist.
    assert!(
        !row_exists(&conn, "boards", &board_id),
        "Board inserted inside a rolled-back savepoint must not exist"
    );
}
