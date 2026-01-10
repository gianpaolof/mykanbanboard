use crate::error::AppResult;
use rusqlite::{Connection, OptionalExtension};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

pub struct Database {
    conn: Arc<Mutex<Connection>>,
}

impl Database {
    pub fn new(db_path: PathBuf) -> AppResult<Self> {
        // Ensure parent directory exists
        if let Some(parent) = db_path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        let conn = Connection::open(&db_path)?;

        // Enable foreign keys
        conn.execute_batch("PRAGMA foreign_keys = ON;")?;

        let db = Database {
            conn: Arc::new(Mutex::new(conn)),
        };

        db.run_migrations()?;

        Ok(db)
    }

    pub fn connection(&self) -> Arc<Mutex<Connection>> {
        Arc::clone(&self.conn)
    }

    fn run_migrations(&self) -> AppResult<()> {
        let conn = self.conn.lock().unwrap();

        // Read and execute schema
        let schema = include_str!("schema.sql");
        conn.execute_batch(schema)?;

        Ok(())
    }

    // Helper method to check if default board exists
    pub fn get_or_create_default_board(&self) -> AppResult<String> {
        let conn = self.conn.lock().unwrap();

        // Check if any board exists
        let board_id: Option<String> = conn
            .query_row("SELECT id FROM boards LIMIT 1", [], |row| row.get(0))
            .optional()?;

        if let Some(id) = board_id {
            return Ok(id);
        }

        // Create default board with default columns
        let board_id = uuid::Uuid::new_v4().to_string();
        let now = chrono::Utc::now().to_rfc3339();

        conn.execute(
            "INSERT INTO boards (id, name, created_at, updated_at) VALUES (?1, ?2, ?3, ?4)",
            (&board_id, "My Board", &now, &now),
        )?;

        // Create default columns
        let columns = vec![
            ("Backlog", 0, "#6b7280"),
            ("To Do", 1, "#3b82f6"),
            ("In Progress", 2, "#f59e0b"),
            ("Review", 3, "#8b5cf6"),
            ("Done", 4, "#22c55e"),
        ];

        for (name, position, color) in columns {
            let col_id = uuid::Uuid::new_v4().to_string();
            conn.execute(
                "INSERT INTO columns (id, board_id, name, position, color) VALUES (?1, ?2, ?3, ?4, ?5)",
                (&col_id, &board_id, name, &position, color),
            )?;
        }

        Ok(board_id)
    }
}

// Implement Clone for Database to allow sharing across Tauri state
impl Clone for Database {
    fn clone(&self) -> Self {
        Database {
            conn: Arc::clone(&self.conn),
        }
    }
}
