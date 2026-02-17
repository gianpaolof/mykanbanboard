//! Shared test utilities for integration tests.

use kanban_ai::db::Database;

/// Create a fresh in-memory database for each test.
pub fn test_db() -> Database {
    Database::new_in_memory().expect("Failed to create in-memory test database")
}
