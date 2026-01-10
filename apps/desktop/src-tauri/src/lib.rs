mod agent;
mod commands;
mod db;
mod error;
mod models;

use agent::{start_agent, stop_agent, AgentProcess};
use db::Database;
use std::path::PathBuf;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Get app data directory
            let app_data_dir = app
                .path()
                .app_data_dir()
                .expect("Failed to get app data directory");

            // Create database path
            let db_path: PathBuf = app_data_dir.join("kanban.db");

            println!("Database path: {:?}", db_path);

            // Initialize database
            let db = Database::new(db_path).expect("Failed to initialize database");

            // Ensure default board exists
            db.get_or_create_default_board()
                .expect("Failed to create default board");

            // Store database in app state
            app.manage(db);

            // Initialize agent process state
            app.manage(AgentProcess::new());

            // Start Python agent sidecar
            if let Err(e) = start_agent(app.handle()) {
                eprintln!("Failed to start agent: {}", e);
                eprintln!("Agent features will be unavailable");
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            // Stop agent when window is destroyed
            if let tauri::WindowEvent::Destroyed = event {
                stop_agent(window.app_handle());
            }
        })
        .invoke_handler(tauri::generate_handler![
            // Board commands
            commands::get_default_board,
            // Column commands
            commands::get_columns,
            commands::create_column,
            commands::update_column,
            commands::delete_column,
            commands::reorder_columns,
            // Ticket commands
            commands::get_tickets,
            commands::get_ticket,
            commands::create_ticket,
            commands::update_ticket,
            commands::delete_ticket,
            commands::move_ticket,
            // Label commands
            commands::get_labels,
            commands::create_label,
            commands::update_label,
            commands::delete_label,
            commands::add_label_to_ticket,
            commands::remove_label_from_ticket,
            // Agent commands
            agent::agent_triage,
            agent::agent_decompose,
            agent::agent_chat,
            agent::agent_daily_summary,
            agent::agent_search,
            agent::agent_health,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
