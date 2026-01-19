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
            commands::get_boards,
            commands::get_board,
            commands::create_board,
            commands::update_board,
            commands::delete_board,
            // Project context commands
            commands::get_project_context,
            commands::update_project_context,
            commands::set_project_context,
            commands::delete_project_context,
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
            // Subtask commands
            commands::get_subtasks,
            commands::create_subtask,
            commands::update_subtask,
            commands::delete_subtask,
            commands::toggle_subtask,
            commands::reorder_subtasks,
            // Automation rule commands
            commands::get_automation_rules,
            commands::get_automation_rule,
            commands::create_automation_rule,
            commands::update_automation_rule,
            commands::delete_automation_rule,
            commands::toggle_automation_rule,
            commands::record_automation_trigger,
            // Agent commands
            agent::agent_triage,
            agent::agent_decompose,
            agent::agent_chat,
            agent::agent_daily_summary,
            agent::agent_search,
            agent::agent_health,
            // Agent context/sync commands
            agent::agent_sync_tickets,
            agent::agent_sync_status,
            agent::agent_invalidate_cache,
            agent::agent_cache_stats,
            agent::agent_index_ticket,
            agent::agent_remove_from_index,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
