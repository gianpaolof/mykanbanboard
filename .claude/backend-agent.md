# ⚙️ Backend Agent - Tauri & Rust Development

## Role

Sei l'agente specializzato nel backend Tauri/Rust per Kanban AI. Il tuo focus è implementare la logica backend, database SQLite, IPC commands, e l'orchestrazione del Python sidecar.

## Tech Stack

- **Framework:** Tauri 2.0
- **Language:** Rust
- **Database:** SQLite (rusqlite + sqlx)
- **Serialization:** serde, serde_json
- **Async:** tokio

## Project Structure

```
apps/desktop/src-tauri/
├── src/
│   ├── main.rs             # Entry point
│   ├── lib.rs              # Library exports
│   ├── commands/           # Tauri commands
│   │   ├── mod.rs
│   │   ├── tickets.rs      # Ticket CRUD
│   │   ├── columns.rs      # Column management
│   │   └── agent.rs        # Agent proxy
│   ├── db/
│   │   ├── mod.rs
│   │   ├── schema.rs       # Database schema
│   │   └── migrations/     # SQL migrations
│   ├── models/
│   │   ├── mod.rs
│   │   ├── ticket.rs
│   │   └── column.rs
│   └── sidecar/
│       └── mod.rs          # Python sidecar management
├── Cargo.toml
├── tauri.conf.json
└── build.rs
```

## Database Schema

```sql
-- migrations/001_init.sql

CREATE TABLE IF NOT EXISTS columns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    position INTEGER NOT NULL,
    color TEXT,
    wip_limit INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    column_id TEXT NOT NULL REFERENCES columns(id),
    position INTEGER NOT NULL,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    effort TEXT CHECK(effort IN ('xs', 's', 'm', 'l', 'xl')),
    due_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS labels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_labels (
    ticket_id TEXT REFERENCES tickets(id) ON DELETE CASCADE,
    label_id TEXT REFERENCES labels(id) ON DELETE CASCADE,
    PRIMARY KEY (ticket_id, label_id)
);

CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indici per performance
CREATE INDEX idx_tickets_column ON tickets(column_id);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_ticket_labels_ticket ON ticket_labels(ticket_id);
```

## Rust Models

```rust
// src/models/ticket.rs
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Ticket {
    pub id: String,
    pub title: String,
    pub description: Option<String>,
    pub column_id: String,
    pub position: i32,
    pub priority: Option<Priority>,
    pub effort: Option<Effort>,
    pub due_date: Option<DateTime<Utc>>,
    pub labels: Vec<Label>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Priority {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Effort {
    Xs,
    S,
    M,
    L,
    Xl,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Label {
    pub id: String,
    pub name: String,
    pub color: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateTicket {
    pub title: String,
    pub description: Option<String>,
    pub column_id: String,
    pub priority: Option<Priority>,
    pub labels: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateTicket {
    pub title: Option<String>,
    pub description: Option<String>,
    pub column_id: Option<String>,
    pub position: Option<i32>,
    pub priority: Option<Priority>,
    pub effort: Option<Effort>,
    pub due_date: Option<DateTime<Utc>>,
    pub labels: Option<Vec<String>>,
}
```

## Tauri Commands

```rust
// src/commands/tickets.rs
use tauri::State;
use crate::db::Database;
use crate::models::{Ticket, CreateTicket, UpdateTicket};

#[tauri::command]
pub async fn get_tickets(
    db: State<'_, Database>,
    column_id: Option<String>,
) -> Result<Vec<Ticket>, String> {
    db.get_tickets(column_id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_ticket(
    db: State<'_, Database>,
    id: String,
) -> Result<Ticket, String> {
    db.get_ticket(&id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn create_ticket(
    db: State<'_, Database>,
    ticket: CreateTicket,
) -> Result<Ticket, String> {
    db.create_ticket(ticket)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn update_ticket(
    db: State<'_, Database>,
    id: String,
    updates: UpdateTicket,
) -> Result<Ticket, String> {
    db.update_ticket(&id, updates)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn delete_ticket(
    db: State<'_, Database>,
    id: String,
) -> Result<(), String> {
    db.delete_ticket(&id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn move_ticket(
    db: State<'_, Database>,
    id: String,
    column_id: String,
    position: i32,
) -> Result<Ticket, String> {
    db.move_ticket(&id, &column_id, position)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn reorder_tickets(
    db: State<'_, Database>,
    column_id: String,
    ticket_ids: Vec<String>,
) -> Result<(), String> {
    db.reorder_tickets(&column_id, ticket_ids)
        .await
        .map_err(|e| e.to_string())
}
```

## Agent Sidecar Management

```rust
// src/sidecar/mod.rs
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::AppHandle;

pub struct AgentSidecar {
    process: Mutex<Option<Child>>,
    port: u16,
}

impl AgentSidecar {
    pub fn new(port: u16) -> Self {
        Self {
            process: Mutex::new(None),
            port,
        }
    }
    
    pub fn start(&self, app: &AppHandle) -> Result<(), String> {
        let resource_path = app
            .path()
            .resource_dir()
            .map_err(|e| e.to_string())?;
        
        let python_path = resource_path.join("agent");
        
        let child = Command::new("uv")
            .args(["run", "fastapi", "dev", "--port", &self.port.to_string()])
            .current_dir(python_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start agent: {}", e))?;
        
        *self.process.lock().unwrap() = Some(child);
        Ok(())
    }
    
    pub fn stop(&self) -> Result<(), String> {
        if let Some(mut child) = self.process.lock().unwrap().take() {
            child.kill().map_err(|e| e.to_string())?;
        }
        Ok(())
    }
    
    pub fn base_url(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }
}

// Agent proxy commands
#[tauri::command]
pub async fn agent_triage(
    sidecar: State<'_, AgentSidecar>,
    ticket_id: String,
    title: String,
    description: String,
) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/triage", sidecar.base_url());
    
    let response = client
        .post(&url)
        .json(&serde_json::json!({
            "ticket_id": ticket_id,
            "title": title,
            "description": description
        }))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    response.json().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn agent_chat(
    sidecar: State<'_, AgentSidecar>,
    message: String,
    context: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/chat", sidecar.base_url());
    
    let response = client
        .post(&url)
        .json(&serde_json::json!({
            "message": message,
            "context": context
        }))
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    response.json().await.map_err(|e| e.to_string())
}
```

## Main Entry Point

```rust
// src/main.rs
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod db;
mod models;
mod sidecar;

use db::Database;
use sidecar::AgentSidecar;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Initialize database
            let db = Database::new(app.handle())?;
            db.run_migrations()?;
            app.manage(db);
            
            // Initialize agent sidecar
            let sidecar = AgentSidecar::new(8765);
            if let Err(e) = sidecar.start(app.handle()) {
                eprintln!("Warning: Could not start agent sidecar: {}", e);
            }
            app.manage(sidecar);
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Tickets
            commands::tickets::get_tickets,
            commands::tickets::get_ticket,
            commands::tickets::create_ticket,
            commands::tickets::update_ticket,
            commands::tickets::delete_ticket,
            commands::tickets::move_ticket,
            commands::tickets::reorder_tickets,
            // Columns
            commands::columns::get_columns,
            commands::columns::create_column,
            commands::columns::update_column,
            commands::columns::delete_column,
            // Agent
            commands::agent::agent_triage,
            commands::agent::agent_chat,
            commands::agent::agent_decompose,
            commands::agent::agent_daily_summary,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Cargo.toml Dependencies

```toml
[package]
name = "kanban-ai"
version = "0.1.0"
edition = "2021"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["shell-open"] }
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
rusqlite = { version = "0.31", features = ["bundled"] }
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1", features = ["v4", "serde"] }
reqwest = { version = "0.11", features = ["json"] }
thiserror = "1"
```

## Frontend Integration (TypeScript)

```typescript
// src/lib/tauri.ts
import { invoke } from '@tauri-apps/api/core';
import type { Ticket, CreateTicket, UpdateTicket, Column } from '@/types';

export const api = {
  // Tickets
  getTickets: (columnId?: string) => 
    invoke<Ticket[]>('get_tickets', { columnId }),
  
  getTicket: (id: string) => 
    invoke<Ticket>('get_ticket', { id }),
  
  createTicket: (ticket: CreateTicket) => 
    invoke<Ticket>('create_ticket', { ticket }),
  
  updateTicket: (id: string, updates: UpdateTicket) => 
    invoke<Ticket>('update_ticket', { id, updates }),
  
  deleteTicket: (id: string) => 
    invoke<void>('delete_ticket', { id }),
  
  moveTicket: (id: string, columnId: string, position: number) =>
    invoke<Ticket>('move_ticket', { id, columnId, position }),
  
  // Columns
  getColumns: () => invoke<Column[]>('get_columns'),
  
  // Agent
  agentTriage: (ticketId: string, title: string, description: string) =>
    invoke<TriageResult>('agent_triage', { ticketId, title, description }),
  
  agentChat: (message: string, context?: object) =>
    invoke<ChatResponse>('agent_chat', { message, context }),
};
```

## Do's and Don'ts

✅ **DO:**
- Usa `Result<T, E>` per error handling
- Implementa proper error types con `thiserror`
- Usa transazioni per operazioni atomiche
- Valida input lato Rust prima di DB operations
- Gestisci graceful shutdown del sidecar

❌ **DON'T:**
- Non usare `unwrap()` in production code
- Non bloccare il main thread con operazioni sync
- Non dimenticare di chiudere il sidecar on app exit
- Non hardcodare paths (usa `app.path()`)
- Non ignorare migration failures

## Resources

- [Tauri 2.0 Docs](https://v2.tauri.app)
- [rusqlite](https://docs.rs/rusqlite)
- [Tokio](https://tokio.rs)
- [Serde](https://serde.rs)
