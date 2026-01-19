use crate::db::Database;
use crate::error::AppError;
use crate::models::*;
use chrono::{DateTime, Utc};
use rusqlite::OptionalExtension;
use tauri::State;

// ===========================================
// BOARD COMMANDS
// ===========================================

#[tauri::command]
pub fn get_default_board(db: State<Database>) -> Result<String, String> {
    db.get_or_create_default_board().map_err(|e| e.into())
}

#[tauri::command]
pub fn get_boards(db: State<Database>) -> Result<Vec<BoardListItem>, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let mut stmt = conn
        .prepare(
            "SELECT b.id, b.name, b.updated_at,
                    (SELECT COUNT(*) FROM tickets t
                     INNER JOIN columns c ON t.column_id = c.id
                     WHERE c.board_id = b.id) as ticket_count
             FROM boards b
             ORDER BY b.updated_at DESC",
        )
        .map_err(AppError::from)?;

    let boards = stmt
        .query_map([], |row| {
            let updated_at_str: String = row.get(2)?;
            Ok(BoardListItem {
                id: row.get(0)?,
                name: row.get(1)?,
                updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
                    .unwrap()
                    .with_timezone(&Utc),
                ticket_count: row.get(3)?,
            })
        })
        .map_err(AppError::from)?
        .collect::<Result<Vec<_>, _>>()
        .map_err(AppError::from)?;

    Ok(boards)
}

#[tauri::command]
pub fn get_board(db: State<Database>, id: String) -> Result<Board, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let board = conn
        .query_row(
            "SELECT id, name, project_context, created_at, updated_at FROM boards WHERE id = ?1",
            [&id],
            |row| {
                let project_context_str: Option<String> = row.get(2)?;
                let created_at_str: String = row.get(3)?;
                let updated_at_str: String = row.get(4)?;

                // Parse project_context JSON if present
                let project_context = project_context_str.and_then(|json_str| {
                    serde_json::from_str::<ProjectContext>(&json_str).ok()
                });

                Ok(Board {
                    id: row.get(0)?,
                    name: row.get(1)?,
                    project_context,
                    created_at: DateTime::parse_from_rfc3339(&created_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                    updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                })
            },
        )
        .optional()
        .map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Board {} not found", id)))?;

    Ok(board)
}

#[tauri::command]
pub fn create_board(db: State<Database>, board: CreateBoard) -> Result<Board, String> {
    let conn = db.connection();
    let mut conn = conn.lock().unwrap();

    let id = uuid::Uuid::new_v4().to_string();
    let now = Utc::now();

    let tx = conn.savepoint().map_err(AppError::from)?;

    // Create board with no project_context initially
    tx.execute(
        "INSERT INTO boards (id, name, project_context, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5)",
        (&id, &board.name, rusqlite::types::Null, &now.to_rfc3339(), &now.to_rfc3339()),
    )
    .map_err(AppError::from)?;

    // Create default columns for the new board
    let default_columns = vec![
        ("Backlog", "#71717a", 0),
        ("To Do", "#3b82f6", 1),
        ("In Progress", "#f59e0b", 2),
        ("Review", "#a855f7", 3),
        ("Done", "#22c55e", 4),
    ];

    for (name, color, position) in default_columns {
        let col_id = uuid::Uuid::new_v4().to_string();
        tx.execute(
            "INSERT INTO columns (id, board_id, name, position, color) VALUES (?1, ?2, ?3, ?4, ?5)",
            (&col_id, &id, name, position, color),
        )
        .map_err(AppError::from)?;
    }

    tx.commit().map_err(AppError::from)?;

    Ok(Board {
        id,
        name: board.name,
        project_context: None,
        created_at: now,
        updated_at: now,
    })
}

#[tauri::command]
pub fn update_board(db: State<Database>, id: String, updates: UpdateBoard) -> Result<Board, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Check if board exists
    let exists: bool = conn
        .query_row("SELECT 1 FROM boards WHERE id = ?1", [&id], |_| Ok(true))
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !exists {
        return Err(AppError::NotFound(format!("Board {} not found", id)).into());
    }

    // Build dynamic UPDATE query
    let mut query = String::from("UPDATE boards SET updated_at = ?, ");
    let now = Utc::now().to_rfc3339();
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = vec![Box::new(now)];
    let mut updates_applied = false;

    if let Some(name) = &updates.name {
        query.push_str("name = ?, ");
        params.push(Box::new(name.clone()));
        updates_applied = true;
    }

    if !updates_applied {
        return Err(AppError::InvalidInput("No updates provided".to_string()).into());
    }

    // Remove trailing comma and space
    query.truncate(query.len() - 2);
    query.push_str(" WHERE id = ?");
    params.push(Box::new(id.clone()));

    let param_refs: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    conn.execute(&query, param_refs.as_slice())
        .map_err(AppError::from)?;

    // Fetch and return updated board
    drop(conn);
    get_board(db, id)
}

#[tauri::command]
pub fn delete_board(db: State<Database>, id: String) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Check if this is the last board
    let board_count: i32 = conn
        .query_row("SELECT COUNT(*) FROM boards", [], |row| row.get(0))
        .map_err(AppError::from)?;

    if board_count <= 1 {
        return Err(AppError::InvalidInput("Cannot delete the last board".to_string()).into());
    }

    // Delete board (columns and tickets cascade due to FK)
    let deleted = conn
        .execute("DELETE FROM boards WHERE id = ?1", [&id])
        .map_err(AppError::from)?;

    if deleted == 0 {
        return Err(AppError::NotFound(format!("Board {} not found", id)).into());
    }

    Ok(())
}

// ===========================================
// PROJECT CONTEXT COMMANDS
// ===========================================

/// Get project context for a board
#[tauri::command]
pub fn get_project_context(db: State<Database>, board_id: String) -> Result<Option<ProjectContext>, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let context_json: Option<String> = conn
        .query_row(
            "SELECT project_context FROM boards WHERE id = ?1",
            [&board_id],
            |row| row.get(0),
        )
        .optional()
        .map_err(AppError::from)?
        .flatten();

    match context_json {
        Some(json_str) => {
            let context: ProjectContext = serde_json::from_str(&json_str)
                .map_err(|e| AppError::InvalidInput(format!("Invalid project context JSON: {}", e)))?;
            Ok(Some(context))
        }
        None => Ok(None),
    }
}

/// Update project context for a board
#[tauri::command]
pub fn update_project_context(
    db: State<Database>,
    board_id: String,
    context: UpdateProjectContext,
) -> Result<ProjectContext, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Get current context (if any)
    let current_json: Option<String> = conn
        .query_row(
            "SELECT project_context FROM boards WHERE id = ?1",
            [&board_id],
            |row| row.get(0),
        )
        .optional()
        .map_err(AppError::from)?
        .flatten();

    // Build new context by merging with existing
    let mut new_context = match current_json {
        Some(ref json_str) => {
            serde_json::from_str::<ProjectContext>(json_str).unwrap_or_default()
        }
        None => ProjectContext::default(),
    };

    // Apply updates
    if let Some(tech_stack) = context.tech_stack {
        new_context.tech_stack = tech_stack;
    }
    if let Some(conventions) = context.conventions {
        new_context.conventions = Some(conventions);
    }
    if let Some(priority_rules) = context.priority_rules {
        new_context.priority_rules = Some(priority_rules);
    }
    if let Some(architecture) = context.architecture {
        new_context.architecture = Some(architecture);
    }
    if let Some(description) = context.description {
        new_context.description = Some(description);
    }
    if let Some(default_labels) = context.default_labels {
        new_context.default_labels = default_labels;
    }

    // Serialize to JSON
    let json_str = serde_json::to_string(&new_context)
        .map_err(|e| AppError::InvalidInput(format!("Failed to serialize project context: {}", e)))?;

    // Update database
    let updated = conn
        .execute(
            "UPDATE boards SET project_context = ?1, updated_at = datetime('now') WHERE id = ?2",
            [&json_str, &board_id],
        )
        .map_err(AppError::from)?;

    if updated == 0 {
        return Err(AppError::NotFound(format!("Board {} not found", board_id)).into());
    }

    Ok(new_context)
}

/// Set project context for a board (replaces entire context)
#[tauri::command]
pub fn set_project_context(
    db: State<Database>,
    board_id: String,
    context: ProjectContext,
) -> Result<ProjectContext, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Serialize to JSON
    let json_str = serde_json::to_string(&context)
        .map_err(|e| AppError::InvalidInput(format!("Failed to serialize project context: {}", e)))?;

    // Update database
    let updated = conn
        .execute(
            "UPDATE boards SET project_context = ?1, updated_at = datetime('now') WHERE id = ?2",
            [&json_str, &board_id],
        )
        .map_err(AppError::from)?;

    if updated == 0 {
        return Err(AppError::NotFound(format!("Board {} not found", board_id)).into());
    }

    Ok(context)
}

/// Delete project context for a board
#[tauri::command]
pub fn delete_project_context(db: State<Database>, board_id: String) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let updated = conn
        .execute(
            "UPDATE boards SET project_context = NULL, updated_at = datetime('now') WHERE id = ?1",
            [&board_id],
        )
        .map_err(AppError::from)?;

    if updated == 0 {
        return Err(AppError::NotFound(format!("Board {} not found", board_id)).into());
    }

    Ok(())
}

// ===========================================
// COLUMN COMMANDS
// ===========================================

#[tauri::command]
pub fn get_columns(db: State<Database>, board_id: Option<String>) -> Result<Vec<Column>, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let query = if board_id.is_some() {
        "SELECT id, name, position, color, wip_limit FROM columns WHERE board_id = ?1 ORDER BY position ASC"
    } else {
        "SELECT id, name, position, color, wip_limit FROM columns ORDER BY position ASC"
    };

    let mut stmt = conn.prepare(query).map_err(AppError::from)?;

    let columns = if let Some(bid) = board_id {
        stmt.query_map([bid], |row| {
            Ok(Column {
                id: row.get(0)?,
                name: row.get(1)?,
                position: row.get(2)?,
                color: row.get(3)?,
                wip_limit: row.get(4)?,
            })
        })
        .map_err(AppError::from)?
        .collect::<Result<Vec<_>, _>>()
        .map_err(AppError::from)?
    } else {
        stmt.query_map([], |row| {
            Ok(Column {
                id: row.get(0)?,
                name: row.get(1)?,
                position: row.get(2)?,
                color: row.get(3)?,
                wip_limit: row.get(4)?,
            })
        })
        .map_err(AppError::from)?
        .collect::<Result<Vec<_>, _>>()
        .map_err(AppError::from)?
    };

    Ok(columns)
}

#[tauri::command]
pub fn create_column(db: State<Database>, board_id: Option<String>, column: CreateColumn) -> Result<Column, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Get board_id (use provided or default to first board)
    let board_id: String = if let Some(bid) = board_id {
        bid
    } else {
        conn.query_row("SELECT id FROM boards LIMIT 1", [], |row| row.get(0))
            .map_err(AppError::from)?
    };

    // Get max position
    let max_position: Option<i32> = conn
        .query_row(
            "SELECT MAX(position) FROM columns WHERE board_id = ?1",
            [&board_id],
            |row| row.get(0),
        )
        .optional()
        .map_err(AppError::from)?
        .flatten();

    let position = max_position.map(|p| p + 1).unwrap_or(0);
    let id = uuid::Uuid::new_v4().to_string();

    conn.execute(
        "INSERT INTO columns (id, board_id, name, position, color, wip_limit) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        (&id, &board_id, &column.name, &position, &column.color, &column.wip_limit),
    )
    .map_err(AppError::from)?;

    Ok(Column {
        id,
        name: column.name,
        position,
        color: column.color,
        wip_limit: column.wip_limit,
    })
}

#[tauri::command]
pub fn update_column(
    db: State<Database>,
    id: String,
    updates: UpdateColumn,
) -> Result<Column, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Check if column exists
    let exists: bool = conn
        .query_row("SELECT 1 FROM columns WHERE id = ?1", [&id], |_| Ok(true))
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !exists {
        return Err(AppError::NotFound(format!("Column {} not found", id)).into());
    }

    // Build dynamic UPDATE query
    let mut query = String::from("UPDATE columns SET ");
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
    let mut updates_applied = false;

    if let Some(name) = &updates.name {
        query.push_str("name = ?, ");
        params.push(Box::new(name.clone()));
        updates_applied = true;
    }

    if let Some(position) = updates.position {
        query.push_str("position = ?, ");
        params.push(Box::new(position));
        updates_applied = true;
    }

    if let Some(color) = &updates.color {
        query.push_str("color = ?, ");
        params.push(Box::new(color.clone()));
        updates_applied = true;
    }

    if let Some(wip_limit) = updates.wip_limit {
        query.push_str("wip_limit = ?, ");
        params.push(Box::new(wip_limit));
        updates_applied = true;
    }

    if !updates_applied {
        return Err(AppError::InvalidInput("No updates provided".to_string()).into());
    }

    // Remove trailing comma and space
    query.truncate(query.len() - 2);
    query.push_str(" WHERE id = ?");
    params.push(Box::new(id.clone()));

    // Convert params to references
    let param_refs: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();

    conn.execute(&query, param_refs.as_slice())
        .map_err(AppError::from)?;

    // Fetch and return updated column
    let column = conn
        .query_row(
            "SELECT id, name, position, color, wip_limit FROM columns WHERE id = ?1",
            [&id],
            |row| {
                Ok(Column {
                    id: row.get(0)?,
                    name: row.get(1)?,
                    position: row.get(2)?,
                    color: row.get(3)?,
                    wip_limit: row.get(4)?,
                })
            },
        )
        .map_err(AppError::from)?;

    Ok(column)
}

#[tauri::command]
pub fn delete_column(db: State<Database>, id: String) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Check if column has tickets
    let ticket_count: i32 = conn
        .query_row(
            "SELECT COUNT(*) FROM tickets WHERE column_id = ?1",
            [&id],
            |row| row.get(0),
        )
        .map_err(AppError::from)?;

    if ticket_count > 0 {
        return Err(
            AppError::InvalidInput("Cannot delete column with tickets".to_string()).into(),
        );
    }

    let deleted = conn
        .execute("DELETE FROM columns WHERE id = ?1", [&id])
        .map_err(AppError::from)?;

    if deleted == 0 {
        return Err(AppError::NotFound(format!("Column {} not found", id)).into());
    }

    Ok(())
}

#[tauri::command]
pub fn reorder_columns(db: State<Database>, column_ids: Vec<String>) -> Result<(), String> {
    let conn = db.connection();
    let mut conn = conn.lock().unwrap();

    let tx = conn.savepoint().map_err(AppError::from)?;

    for (position, column_id) in column_ids.iter().enumerate() {
        tx.execute(
            "UPDATE columns SET position = ?1 WHERE id = ?2",
            rusqlite::params![position as i32, column_id],
        )
        .map_err(AppError::from)?;
    }

    tx.commit().map_err(AppError::from)?;

    Ok(())
}

// ===========================================
// TICKET COMMANDS
// ===========================================

#[tauri::command]
pub fn get_tickets(db: State<Database>, board_id: Option<String>, column_id: Option<String>) -> Result<Vec<Ticket>, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Build query based on filters
    let (query, params): (&str, Vec<String>) = match (&board_id, &column_id) {
        (Some(bid), Some(cid)) => (
            "SELECT t.id, t.title, t.description, t.column_id, t.position, t.priority, t.effort, t.due_date, t.created_at, t.updated_at
             FROM tickets t
             INNER JOIN columns c ON t.column_id = c.id
             WHERE c.board_id = ?1 AND t.column_id = ?2
             ORDER BY t.position ASC",
            vec![bid.clone(), cid.clone()],
        ),
        (Some(bid), None) => (
            "SELECT t.id, t.title, t.description, t.column_id, t.position, t.priority, t.effort, t.due_date, t.created_at, t.updated_at
             FROM tickets t
             INNER JOIN columns c ON t.column_id = c.id
             WHERE c.board_id = ?1
             ORDER BY t.position ASC",
            vec![bid.clone()],
        ),
        (None, Some(cid)) => (
            "SELECT id, title, description, column_id, position, priority, effort, due_date, created_at, updated_at
             FROM tickets WHERE column_id = ?1 ORDER BY position ASC",
            vec![cid.clone()],
        ),
        (None, None) => (
            "SELECT id, title, description, column_id, position, priority, effort, due_date, created_at, updated_at
             FROM tickets ORDER BY position ASC",
            vec![],
        ),
    };

    let mut stmt = conn.prepare(query).map_err(AppError::from)?;

    let tickets: Vec<Ticket> = match params.len() {
        0 => stmt.query_map([], parse_ticket_row)
            .map_err(AppError::from)?
            .collect::<Result<Vec<_>, _>>()
            .map_err(AppError::from)?,
        1 => stmt.query_map([&params[0]], parse_ticket_row)
            .map_err(AppError::from)?
            .collect::<Result<Vec<_>, _>>()
            .map_err(AppError::from)?,
        2 => stmt.query_map([&params[0], &params[1]], parse_ticket_row)
            .map_err(AppError::from)?
            .collect::<Result<Vec<_>, _>>()
            .map_err(AppError::from)?,
        _ => vec![],
    };

    let mut result = Vec::new();
    for mut ticket in tickets {
        // Load labels
        ticket.labels = get_ticket_labels(&conn, &ticket.id)?;
        // Load comments
        ticket.comments = get_ticket_comments(&conn, &ticket.id)?;

        result.push(ticket);
    }

    Ok(result)
}

#[tauri::command]
pub fn get_ticket(db: State<Database>, id: String) -> Result<Ticket, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let mut ticket = conn
        .query_row(
            "SELECT id, title, description, column_id, position, priority, effort, due_date, created_at, updated_at
             FROM tickets WHERE id = ?1",
            [&id],
            parse_ticket_row,
        )
        .optional()
        .map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Ticket {} not found", id)))?;

    ticket.labels = get_ticket_labels(&conn, &ticket.id)?;
    ticket.comments = get_ticket_comments(&conn, &ticket.id)?;

    Ok(ticket)
}

#[tauri::command]
pub fn create_ticket(db: State<Database>, ticket: CreateTicket) -> Result<Ticket, String> {
    let conn = db.connection();
    let mut conn = conn.lock().unwrap();

    // Verify column exists
    let column_exists: bool = conn
        .query_row(
            "SELECT 1 FROM columns WHERE id = ?1",
            [&ticket.column_id],
            |_| Ok(true),
        )
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !column_exists {
        return Err(AppError::NotFound(format!(
            "Column {} not found",
            ticket.column_id
        ))
        .into());
    }

    // Get max position in column
    let max_position: Option<i32> = conn
        .query_row(
            "SELECT MAX(position) FROM tickets WHERE column_id = ?1",
            [&ticket.column_id],
            |row| row.get(0),
        )
        .optional()
        .map_err(AppError::from)?
        .flatten();

    let position = max_position.map(|p| p + 1).unwrap_or(0);
    let id = uuid::Uuid::new_v4().to_string();
    let now = Utc::now();

    // Parse due_date if provided
    let due_date = ticket
        .due_date
        .as_ref()
        .and_then(|d| DateTime::parse_from_rfc3339(d).ok())
        .map(|d| d.with_timezone(&Utc));

    let tx = conn.savepoint().map_err(AppError::from)?;

    tx.execute(
        "INSERT INTO tickets (id, title, description, column_id, position, priority, effort, due_date, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
        (
            &id,
            &ticket.title,
            &ticket.description,
            &ticket.column_id,
            &position,
            &ticket.priority.as_ref().map(|p| p.as_str()),
            &ticket.effort.as_ref().map(|e| e.as_str()),
            &due_date.map(|d| d.to_rfc3339()),
            &now.to_rfc3339(),
            &now.to_rfc3339(),
        ),
    )
    .map_err(AppError::from)?;

    // Add labels if provided
    if let Some(label_ids) = &ticket.labels {
        for label_id in label_ids {
            tx.execute(
                "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
                (&id, label_id),
            )
            .map_err(AppError::from)?;
        }
    }

    tx.commit().map_err(AppError::from)?;

    // Fetch and return complete ticket
    get_ticket(db, id)
}

#[tauri::command]
pub fn update_ticket(
    db: State<Database>,
    id: String,
    updates: UpdateTicket,
) -> Result<Ticket, String> {
    let conn = db.connection();
    let mut conn = conn.lock().unwrap();

    // Check if ticket exists
    let exists: bool = conn
        .query_row("SELECT 1 FROM tickets WHERE id = ?1", [&id], |_| Ok(true))
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !exists {
        return Err(AppError::NotFound(format!("Ticket {} not found", id)).into());
    }

    let tx = conn.savepoint().map_err(AppError::from)?;

    // Build dynamic UPDATE query
    let mut query = String::from("UPDATE tickets SET ");
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
    let mut updates_applied = false;

    if let Some(title) = &updates.title {
        query.push_str("title = ?, ");
        params.push(Box::new(title.clone()));
        updates_applied = true;
    }

    if let Some(description) = &updates.description {
        query.push_str("description = ?, ");
        params.push(Box::new(description.clone()));
        updates_applied = true;
    }

    if let Some(column_id) = &updates.column_id {
        query.push_str("column_id = ?, ");
        params.push(Box::new(column_id.clone()));
        updates_applied = true;
    }

    if let Some(position) = updates.position {
        query.push_str("position = ?, ");
        params.push(Box::new(position));
        updates_applied = true;
    }

    if let Some(priority) = &updates.priority {
        query.push_str("priority = ?, ");
        params.push(Box::new(priority.as_str().to_string()));
        updates_applied = true;
    }

    if let Some(effort) = &updates.effort {
        query.push_str("effort = ?, ");
        params.push(Box::new(effort.as_str().to_string()));
        updates_applied = true;
    }

    if let Some(due_date_str) = &updates.due_date {
        let due_date = if due_date_str.is_empty() || due_date_str == "null" {
            None
        } else {
            DateTime::parse_from_rfc3339(due_date_str)
                .ok()
                .map(|d| d.with_timezone(&Utc).to_rfc3339())
        };
        query.push_str("due_date = ?, ");
        params.push(Box::new(due_date));
        updates_applied = true;
    }

    if updates_applied {
        // Remove trailing comma and space
        query.truncate(query.len() - 2);
        query.push_str(" WHERE id = ?");
        params.push(Box::new(id.clone()));

        let param_refs: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
        tx.execute(&query, param_refs.as_slice())
            .map_err(AppError::from)?;
    }

    // Update labels if provided
    if let Some(label_ids) = &updates.labels {
        // Remove existing labels
        tx.execute("DELETE FROM ticket_labels WHERE ticket_id = ?1", [&id])
            .map_err(AppError::from)?;

        // Add new labels
        for label_id in label_ids {
            tx.execute(
                "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
                (&id, label_id),
            )
            .map_err(AppError::from)?;
        }
    }

    tx.commit().map_err(AppError::from)?;

    // Fetch and return updated ticket
    drop(conn); // Release lock before calling get_ticket
    get_ticket(db, id)
}

#[tauri::command]
pub fn delete_ticket(db: State<Database>, id: String) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let deleted = conn
        .execute("DELETE FROM tickets WHERE id = ?1", [&id])
        .map_err(AppError::from)?;

    if deleted == 0 {
        return Err(AppError::NotFound(format!("Ticket {} not found", id)).into());
    }

    Ok(())
}

#[tauri::command]
pub fn move_ticket(
    db: State<Database>,
    id: String,
    column_id: String,
    position: i32,
) -> Result<Ticket, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Verify column exists
    let column_exists: bool = conn
        .query_row("SELECT 1 FROM columns WHERE id = ?1", [&column_id], |_| {
            Ok(true)
        })
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !column_exists {
        return Err(AppError::NotFound(format!("Column {} not found", column_id)).into());
    }

    conn.execute(
        "UPDATE tickets SET column_id = ?1, position = ?2 WHERE id = ?3",
        (&column_id, &position, &id),
    )
    .map_err(AppError::from)?;

    drop(conn);
    get_ticket(db, id)
}

// ===========================================
// LABEL COMMANDS
// ===========================================

#[tauri::command]
pub fn get_labels(db: State<Database>) -> Result<Vec<Label>, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let mut stmt = conn
        .prepare("SELECT id, name, color FROM labels ORDER BY name ASC")
        .map_err(AppError::from)?;

    let labels = stmt
        .query_map([], |row| {
            Ok(Label {
                id: row.get(0)?,
                name: row.get(1)?,
                color: row.get(2)?,
            })
        })
        .map_err(AppError::from)?
        .collect::<Result<Vec<_>, _>>()
        .map_err(AppError::from)?;

    Ok(labels)
}

#[tauri::command]
pub fn create_label(db: State<Database>, label: CreateLabel) -> Result<Label, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let id = uuid::Uuid::new_v4().to_string();

    conn.execute(
        "INSERT INTO labels (id, name, color) VALUES (?1, ?2, ?3)",
        (&id, &label.name, &label.color),
    )
    .map_err(|e| {
        if e.to_string().contains("UNIQUE") {
            AppError::InvalidInput(format!("Label '{}' already exists", label.name))
        } else {
            AppError::from(e)
        }
    })?;

    Ok(Label {
        id,
        name: label.name,
        color: label.color,
    })
}

#[tauri::command]
pub fn update_label(
    db: State<Database>,
    id: String,
    updates: UpdateLabel,
) -> Result<Label, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Check if label exists
    let exists: bool = conn
        .query_row("SELECT 1 FROM labels WHERE id = ?1", [&id], |_| Ok(true))
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !exists {
        return Err(AppError::NotFound(format!("Label {} not found", id)).into());
    }

    // Build dynamic UPDATE query
    let mut query = String::from("UPDATE labels SET ");
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
    let mut updates_applied = false;

    if let Some(name) = &updates.name {
        query.push_str("name = ?, ");
        params.push(Box::new(name.clone()));
        updates_applied = true;
    }

    if let Some(color) = &updates.color {
        query.push_str("color = ?, ");
        params.push(Box::new(color.clone()));
        updates_applied = true;
    }

    if !updates_applied {
        return Err(AppError::InvalidInput("No updates provided".to_string()).into());
    }

    query.truncate(query.len() - 2);
    query.push_str(" WHERE id = ?");
    params.push(Box::new(id.clone()));

    let param_refs: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();

    conn.execute(&query, param_refs.as_slice())
        .map_err(AppError::from)?;

    // Fetch and return updated label
    let label = conn
        .query_row(
            "SELECT id, name, color FROM labels WHERE id = ?1",
            [&id],
            |row| {
                Ok(Label {
                    id: row.get(0)?,
                    name: row.get(1)?,
                    color: row.get(2)?,
                })
            },
        )
        .map_err(AppError::from)?;

    Ok(label)
}

#[tauri::command]
pub fn delete_label(db: State<Database>, id: String) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let deleted = conn
        .execute("DELETE FROM labels WHERE id = ?1", [&id])
        .map_err(AppError::from)?;

    if deleted == 0 {
        return Err(AppError::NotFound(format!("Label {} not found", id)).into());
    }

    Ok(())
}

#[tauri::command]
pub fn add_label_to_ticket(
    db: State<Database>,
    ticket_id: String,
    label_id: String,
) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    conn.execute(
        "INSERT INTO ticket_labels (ticket_id, label_id) VALUES (?1, ?2)",
        (&ticket_id, &label_id),
    )
    .map_err(|e| {
        if e.to_string().contains("UNIQUE") || e.to_string().contains("PRIMARY") {
            AppError::InvalidInput("Label already added to ticket".to_string())
        } else {
            AppError::from(e)
        }
    })?;

    Ok(())
}

#[tauri::command]
pub fn remove_label_from_ticket(
    db: State<Database>,
    ticket_id: String,
    label_id: String,
) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let deleted = conn
        .execute(
            "DELETE FROM ticket_labels WHERE ticket_id = ?1 AND label_id = ?2",
            (&ticket_id, &label_id),
        )
        .map_err(AppError::from)?;

    if deleted == 0 {
        return Err(AppError::NotFound("Label not found on ticket".to_string()).into());
    }

    Ok(())
}

// ===========================================
// HELPER FUNCTIONS
// ===========================================

fn parse_ticket_row(row: &rusqlite::Row) -> rusqlite::Result<Ticket> {
    let priority_str: Option<String> = row.get(5)?;
    let effort_str: Option<String> = row.get(6)?;
    let due_date_str: Option<String> = row.get(7)?;
    let created_at_str: String = row.get(8)?;
    let updated_at_str: String = row.get(9)?;

    Ok(Ticket {
        id: row.get(0)?,
        title: row.get(1)?,
        description: row.get(2)?,
        column_id: row.get(3)?,
        position: row.get(4)?,
        priority: priority_str.and_then(|s| Priority::from_str(&s)),
        effort: effort_str.and_then(|s| Effort::from_str(&s)),
        due_date: due_date_str.and_then(|s| DateTime::parse_from_rfc3339(&s).ok())
            .map(|d| d.with_timezone(&Utc)),
        labels: Vec::new(), // Loaded separately
        comments: Vec::new(), // Loaded separately
        created_at: DateTime::parse_from_rfc3339(&created_at_str)
            .unwrap()
            .with_timezone(&Utc),
        updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
            .unwrap()
            .with_timezone(&Utc),
    })
}

fn get_ticket_labels(
    conn: &rusqlite::Connection,
    ticket_id: &str,
) -> Result<Vec<Label>, AppError> {
    let mut stmt = conn.prepare(
        "SELECT l.id, l.name, l.color
         FROM labels l
         INNER JOIN ticket_labels tl ON l.id = tl.label_id
         WHERE tl.ticket_id = ?1
         ORDER BY l.name ASC",
    )?;

    let labels = stmt
        .query_map([ticket_id], |row| {
            Ok(Label {
                id: row.get(0)?,
                name: row.get(1)?,
                color: row.get(2)?,
            })
        })?
        .collect::<Result<Vec<_>, _>>()?;

    Ok(labels)
}

fn get_ticket_comments(
    conn: &rusqlite::Connection,
    ticket_id: &str,
) -> Result<Vec<Comment>, AppError> {
    let mut stmt = conn.prepare(
        "SELECT id, ticket_id, content, created_at
         FROM comments
         WHERE ticket_id = ?1
         ORDER BY created_at ASC",
    )?;

    let comments = stmt
        .query_map([ticket_id], |row| {
            let created_at_str: String = row.get(3)?;
            Ok(Comment {
                id: row.get(0)?,
                ticket_id: row.get(1)?,
                content: row.get(2)?,
                created_at: DateTime::parse_from_rfc3339(&created_at_str)
                    .unwrap()
                    .with_timezone(&Utc),
            })
        })?
        .collect::<Result<Vec<_>, _>>()?;

    Ok(comments)
}

// ===========================================
// SUBTASK COMMANDS
// ===========================================

#[tauri::command]
pub fn get_subtasks(db: State<Database>, parent_ticket_id: String) -> Result<Vec<Subtask>, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let mut stmt = conn
        .prepare(
            "SELECT id, parent_ticket_id, title, description, completed, position, created_at, updated_at
             FROM subtasks
             WHERE parent_ticket_id = ?1
             ORDER BY position ASC",
        )
        .map_err(AppError::from)?;

    let subtasks = stmt
        .query_map([&parent_ticket_id], |row| {
            let created_at_str: String = row.get(6)?;
            let updated_at_str: String = row.get(7)?;
            let completed: i32 = row.get(4)?;
            Ok(Subtask {
                id: row.get(0)?,
                parent_ticket_id: row.get(1)?,
                title: row.get(2)?,
                description: row.get(3)?,
                completed: completed != 0,
                position: row.get(5)?,
                created_at: DateTime::parse_from_rfc3339(&created_at_str)
                    .unwrap()
                    .with_timezone(&Utc),
                updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
                    .unwrap()
                    .with_timezone(&Utc),
            })
        })
        .map_err(AppError::from)?
        .collect::<Result<Vec<_>, _>>()
        .map_err(AppError::from)?;

    Ok(subtasks)
}

#[tauri::command]
pub fn create_subtask(db: State<Database>, subtask: CreateSubtask) -> Result<Subtask, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Verify parent ticket exists
    let ticket_exists: bool = conn
        .query_row(
            "SELECT 1 FROM tickets WHERE id = ?1",
            [&subtask.parent_ticket_id],
            |_| Ok(true),
        )
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !ticket_exists {
        return Err(AppError::NotFound(format!(
            "Ticket {} not found",
            subtask.parent_ticket_id
        ))
        .into());
    }

    // Get max position
    let max_position: Option<i32> = conn
        .query_row(
            "SELECT MAX(position) FROM subtasks WHERE parent_ticket_id = ?1",
            [&subtask.parent_ticket_id],
            |row| row.get(0),
        )
        .optional()
        .map_err(AppError::from)?
        .flatten();

    let position = max_position.map(|p| p + 1).unwrap_or(0);
    let id = uuid::Uuid::new_v4().to_string();
    let now = Utc::now();

    conn.execute(
        "INSERT INTO subtasks (id, parent_ticket_id, title, description, completed, position, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, 0, ?5, ?6, ?7)",
        (
            &id,
            &subtask.parent_ticket_id,
            &subtask.title,
            &subtask.description,
            &position,
            &now.to_rfc3339(),
            &now.to_rfc3339(),
        ),
    )
    .map_err(AppError::from)?;

    Ok(Subtask {
        id,
        parent_ticket_id: subtask.parent_ticket_id,
        title: subtask.title,
        description: subtask.description,
        completed: false,
        position,
        created_at: now,
        updated_at: now,
    })
}

#[tauri::command]
pub fn update_subtask(
    db: State<Database>,
    id: String,
    updates: UpdateSubtask,
) -> Result<Subtask, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Check if subtask exists
    let exists: bool = conn
        .query_row("SELECT 1 FROM subtasks WHERE id = ?1", [&id], |_| Ok(true))
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !exists {
        return Err(AppError::NotFound(format!("Subtask {} not found", id)).into());
    }

    // Build dynamic UPDATE query
    let mut query = String::from("UPDATE subtasks SET ");
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
    let mut updates_applied = false;

    if let Some(title) = &updates.title {
        query.push_str("title = ?, ");
        params.push(Box::new(title.clone()));
        updates_applied = true;
    }

    if let Some(description) = &updates.description {
        query.push_str("description = ?, ");
        params.push(Box::new(description.clone()));
        updates_applied = true;
    }

    if let Some(completed) = updates.completed {
        query.push_str("completed = ?, ");
        params.push(Box::new(if completed { 1i32 } else { 0i32 }));
        updates_applied = true;
    }

    if let Some(position) = updates.position {
        query.push_str("position = ?, ");
        params.push(Box::new(position));
        updates_applied = true;
    }

    if !updates_applied {
        return Err(AppError::InvalidInput("No updates provided".to_string()).into());
    }

    query.truncate(query.len() - 2);
    query.push_str(" WHERE id = ?");
    params.push(Box::new(id.clone()));

    let param_refs: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    conn.execute(&query, param_refs.as_slice())
        .map_err(AppError::from)?;

    // Fetch and return updated subtask
    let subtask = conn
        .query_row(
            "SELECT id, parent_ticket_id, title, description, completed, position, created_at, updated_at
             FROM subtasks WHERE id = ?1",
            [&id],
            |row| {
                let created_at_str: String = row.get(6)?;
                let updated_at_str: String = row.get(7)?;
                let completed: i32 = row.get(4)?;
                Ok(Subtask {
                    id: row.get(0)?,
                    parent_ticket_id: row.get(1)?,
                    title: row.get(2)?,
                    description: row.get(3)?,
                    completed: completed != 0,
                    position: row.get(5)?,
                    created_at: DateTime::parse_from_rfc3339(&created_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                    updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                })
            },
        )
        .map_err(AppError::from)?;

    Ok(subtask)
}

#[tauri::command]
pub fn delete_subtask(db: State<Database>, id: String) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let deleted = conn
        .execute("DELETE FROM subtasks WHERE id = ?1", [&id])
        .map_err(AppError::from)?;

    if deleted == 0 {
        return Err(AppError::NotFound(format!("Subtask {} not found", id)).into());
    }

    Ok(())
}

#[tauri::command]
pub fn toggle_subtask(db: State<Database>, id: String) -> Result<Subtask, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Toggle the completed status
    conn.execute(
        "UPDATE subtasks SET completed = NOT completed WHERE id = ?1",
        [&id],
    )
    .map_err(AppError::from)?;

    // Fetch and return updated subtask
    let subtask = conn
        .query_row(
            "SELECT id, parent_ticket_id, title, description, completed, position, created_at, updated_at
             FROM subtasks WHERE id = ?1",
            [&id],
            |row| {
                let created_at_str: String = row.get(6)?;
                let updated_at_str: String = row.get(7)?;
                let completed: i32 = row.get(4)?;
                Ok(Subtask {
                    id: row.get(0)?,
                    parent_ticket_id: row.get(1)?,
                    title: row.get(2)?,
                    description: row.get(3)?,
                    completed: completed != 0,
                    position: row.get(5)?,
                    created_at: DateTime::parse_from_rfc3339(&created_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                    updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                })
            },
        )
        .optional()
        .map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Subtask {} not found", id)))?;

    Ok(subtask)
}

#[tauri::command]
pub fn reorder_subtasks(db: State<Database>, subtask_ids: Vec<String>) -> Result<(), String> {
    let conn = db.connection();
    let mut conn = conn.lock().unwrap();

    let tx = conn.savepoint().map_err(AppError::from)?;

    for (position, subtask_id) in subtask_ids.iter().enumerate() {
        tx.execute(
            "UPDATE subtasks SET position = ?1 WHERE id = ?2",
            rusqlite::params![position as i32, subtask_id],
        )
        .map_err(AppError::from)?;
    }

    tx.commit().map_err(AppError::from)?;

    Ok(())
}

// ===========================================
// AUTOMATION RULE COMMANDS
// ===========================================

#[tauri::command]
pub fn get_automation_rules(db: State<Database>, board_id: String) -> Result<Vec<AutomationRule>, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let mut stmt = conn
        .prepare(
            "SELECT id, board_id, name, description, enabled, trigger_type, trigger_config,
                    action_type, action_config, last_triggered_at, trigger_count, created_at, updated_at
             FROM automation_rules
             WHERE board_id = ?1
             ORDER BY created_at DESC",
        )
        .map_err(AppError::from)?;

    let rules = stmt
        .query_map([&board_id], |row| {
            let enabled: i32 = row.get(4)?;
            let trigger_type_str: String = row.get(5)?;
            let trigger_config_str: String = row.get(6)?;
            let action_type_str: String = row.get(7)?;
            let action_config_str: String = row.get(8)?;
            let last_triggered_at_str: Option<String> = row.get(9)?;
            let created_at_str: String = row.get(11)?;
            let updated_at_str: String = row.get(12)?;

            Ok(AutomationRule {
                id: row.get(0)?,
                board_id: row.get(1)?,
                name: row.get(2)?,
                description: row.get(3)?,
                enabled: enabled != 0,
                trigger_type: TriggerType::from_str(&trigger_type_str)
                    .unwrap_or(TriggerType::TicketCreated),
                trigger_config: serde_json::from_str(&trigger_config_str)
                    .unwrap_or(serde_json::json!({})),
                action_type: ActionType::from_str(&action_type_str)
                    .unwrap_or(ActionType::Notify),
                action_config: serde_json::from_str(&action_config_str)
                    .unwrap_or(serde_json::json!({})),
                last_triggered_at: last_triggered_at_str
                    .and_then(|s| DateTime::parse_from_rfc3339(&s).ok())
                    .map(|d| d.with_timezone(&Utc)),
                trigger_count: row.get(10)?,
                created_at: DateTime::parse_from_rfc3339(&created_at_str)
                    .unwrap()
                    .with_timezone(&Utc),
                updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
                    .unwrap()
                    .with_timezone(&Utc),
            })
        })
        .map_err(AppError::from)?
        .collect::<Result<Vec<_>, _>>()
        .map_err(AppError::from)?;

    Ok(rules)
}

#[tauri::command]
pub fn get_automation_rule(db: State<Database>, id: String) -> Result<AutomationRule, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let rule = conn
        .query_row(
            "SELECT id, board_id, name, description, enabled, trigger_type, trigger_config,
                    action_type, action_config, last_triggered_at, trigger_count, created_at, updated_at
             FROM automation_rules WHERE id = ?1",
            [&id],
            |row| {
                let enabled: i32 = row.get(4)?;
                let trigger_type_str: String = row.get(5)?;
                let trigger_config_str: String = row.get(6)?;
                let action_type_str: String = row.get(7)?;
                let action_config_str: String = row.get(8)?;
                let last_triggered_at_str: Option<String> = row.get(9)?;
                let created_at_str: String = row.get(11)?;
                let updated_at_str: String = row.get(12)?;

                Ok(AutomationRule {
                    id: row.get(0)?,
                    board_id: row.get(1)?,
                    name: row.get(2)?,
                    description: row.get(3)?,
                    enabled: enabled != 0,
                    trigger_type: TriggerType::from_str(&trigger_type_str)
                        .unwrap_or(TriggerType::TicketCreated),
                    trigger_config: serde_json::from_str(&trigger_config_str)
                        .unwrap_or(serde_json::json!({})),
                    action_type: ActionType::from_str(&action_type_str)
                        .unwrap_or(ActionType::Notify),
                    action_config: serde_json::from_str(&action_config_str)
                        .unwrap_or(serde_json::json!({})),
                    last_triggered_at: last_triggered_at_str
                        .and_then(|s| DateTime::parse_from_rfc3339(&s).ok())
                        .map(|d| d.with_timezone(&Utc)),
                    trigger_count: row.get(10)?,
                    created_at: DateTime::parse_from_rfc3339(&created_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                    updated_at: DateTime::parse_from_rfc3339(&updated_at_str)
                        .unwrap()
                        .with_timezone(&Utc),
                })
            },
        )
        .optional()
        .map_err(AppError::from)?
        .ok_or_else(|| AppError::NotFound(format!("Automation rule {} not found", id)))?;

    Ok(rule)
}

#[tauri::command]
pub fn create_automation_rule(
    db: State<Database>,
    rule: CreateAutomationRule,
) -> Result<AutomationRule, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Verify board exists
    let board_exists: bool = conn
        .query_row("SELECT 1 FROM boards WHERE id = ?1", [&rule.board_id], |_| {
            Ok(true)
        })
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !board_exists {
        return Err(AppError::NotFound(format!("Board {} not found", rule.board_id)).into());
    }

    let id = uuid::Uuid::new_v4().to_string();
    let now = Utc::now();
    let trigger_config = rule.trigger_config.unwrap_or(serde_json::json!({}));
    let action_config = rule.action_config.unwrap_or(serde_json::json!({}));

    conn.execute(
        "INSERT INTO automation_rules (id, board_id, name, description, enabled, trigger_type, trigger_config,
                                       action_type, action_config, trigger_count, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, 1, ?5, ?6, ?7, ?8, 0, ?9, ?10)",
        (
            &id,
            &rule.board_id,
            &rule.name,
            &rule.description,
            rule.trigger_type.as_str(),
            serde_json::to_string(&trigger_config).unwrap(),
            rule.action_type.as_str(),
            serde_json::to_string(&action_config).unwrap(),
            &now.to_rfc3339(),
            &now.to_rfc3339(),
        ),
    )
    .map_err(AppError::from)?;

    Ok(AutomationRule {
        id,
        board_id: rule.board_id,
        name: rule.name,
        description: rule.description,
        enabled: true,
        trigger_type: rule.trigger_type,
        trigger_config,
        action_type: rule.action_type,
        action_config,
        last_triggered_at: None,
        trigger_count: 0,
        created_at: now,
        updated_at: now,
    })
}

#[tauri::command]
pub fn update_automation_rule(
    db: State<Database>,
    id: String,
    updates: UpdateAutomationRule,
) -> Result<AutomationRule, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Check if rule exists
    let exists: bool = conn
        .query_row(
            "SELECT 1 FROM automation_rules WHERE id = ?1",
            [&id],
            |_| Ok(true),
        )
        .optional()
        .map_err(AppError::from)?
        .unwrap_or(false);

    if !exists {
        return Err(AppError::NotFound(format!("Automation rule {} not found", id)).into());
    }

    // Build dynamic UPDATE query
    let mut query = String::from("UPDATE automation_rules SET ");
    let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
    let mut updates_applied = false;

    if let Some(name) = &updates.name {
        query.push_str("name = ?, ");
        params.push(Box::new(name.clone()));
        updates_applied = true;
    }

    if let Some(description) = &updates.description {
        query.push_str("description = ?, ");
        params.push(Box::new(description.clone()));
        updates_applied = true;
    }

    if let Some(enabled) = updates.enabled {
        query.push_str("enabled = ?, ");
        params.push(Box::new(if enabled { 1i32 } else { 0i32 }));
        updates_applied = true;
    }

    if let Some(trigger_type) = &updates.trigger_type {
        query.push_str("trigger_type = ?, ");
        params.push(Box::new(trigger_type.as_str().to_string()));
        updates_applied = true;
    }

    if let Some(trigger_config) = &updates.trigger_config {
        query.push_str("trigger_config = ?, ");
        params.push(Box::new(serde_json::to_string(trigger_config).unwrap()));
        updates_applied = true;
    }

    if let Some(action_type) = &updates.action_type {
        query.push_str("action_type = ?, ");
        params.push(Box::new(action_type.as_str().to_string()));
        updates_applied = true;
    }

    if let Some(action_config) = &updates.action_config {
        query.push_str("action_config = ?, ");
        params.push(Box::new(serde_json::to_string(action_config).unwrap()));
        updates_applied = true;
    }

    if !updates_applied {
        return Err(AppError::InvalidInput("No updates provided".to_string()).into());
    }

    query.truncate(query.len() - 2);
    query.push_str(" WHERE id = ?");
    params.push(Box::new(id.clone()));

    let param_refs: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    conn.execute(&query, param_refs.as_slice())
        .map_err(AppError::from)?;

    // Fetch and return updated rule
    drop(conn);
    get_automation_rule(db, id)
}

#[tauri::command]
pub fn delete_automation_rule(db: State<Database>, id: String) -> Result<(), String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let deleted = conn
        .execute("DELETE FROM automation_rules WHERE id = ?1", [&id])
        .map_err(AppError::from)?;

    if deleted == 0 {
        return Err(AppError::NotFound(format!("Automation rule {} not found", id)).into());
    }

    Ok(())
}

#[tauri::command]
pub fn toggle_automation_rule(db: State<Database>, id: String) -> Result<AutomationRule, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    // Toggle the enabled status
    conn.execute(
        "UPDATE automation_rules SET enabled = NOT enabled WHERE id = ?1",
        [&id],
    )
    .map_err(AppError::from)?;

    drop(conn);
    get_automation_rule(db, id)
}

#[tauri::command]
pub fn record_automation_trigger(db: State<Database>, id: String) -> Result<AutomationRule, String> {
    let conn = db.connection();
    let conn = conn.lock().unwrap();

    let now = Utc::now();

    conn.execute(
        "UPDATE automation_rules SET last_triggered_at = ?1, trigger_count = trigger_count + 1 WHERE id = ?2",
        (&now.to_rfc3339(), &id),
    )
    .map_err(AppError::from)?;

    drop(conn);
    get_automation_rule(db, id)
}
