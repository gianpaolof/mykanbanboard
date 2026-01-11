use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

// ===========================================
// ENUMS
// ===========================================

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Priority {
    Low,
    Medium,
    High,
    Critical,
}

impl Priority {
    pub fn as_str(&self) -> &str {
        match self {
            Priority::Low => "low",
            Priority::Medium => "medium",
            Priority::High => "high",
            Priority::Critical => "critical",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "low" => Some(Priority::Low),
            "medium" => Some(Priority::Medium),
            "high" => Some(Priority::High),
            "critical" => Some(Priority::Critical),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Effort {
    Xs,
    S,
    M,
    L,
    Xl,
}

impl Effort {
    pub fn as_str(&self) -> &str {
        match self {
            Effort::Xs => "xs",
            Effort::S => "s",
            Effort::M => "m",
            Effort::L => "l",
            Effort::Xl => "xl",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "xs" => Some(Effort::Xs),
            "s" => Some(Effort::S),
            "m" => Some(Effort::M),
            "l" => Some(Effort::L),
            "xl" => Some(Effort::Xl),
            _ => None,
        }
    }
}

// ===========================================
// CORE MODELS
// ===========================================

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Board {
    pub id: String,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Column {
    pub id: String,
    pub name: String,
    pub position: i32,
    pub color: Option<String>,
    pub wip_limit: Option<i32>,
}

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
    pub comments: Vec<Comment>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
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
pub struct Comment {
    pub id: String,
    pub ticket_id: String,
    pub content: String,
    pub created_at: DateTime<Utc>,
}

// ===========================================
// DTOs (Data Transfer Objects)
// ===========================================

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateTicket {
    pub title: String,
    pub description: Option<String>,
    pub column_id: String,
    pub priority: Option<Priority>,
    pub effort: Option<Effort>,
    pub labels: Option<Vec<String>>,
    pub due_date: Option<String>, // ISO 8601 string
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateTicket {
    pub title: Option<String>,
    pub description: Option<String>,
    pub column_id: Option<String>,
    pub position: Option<i32>,
    pub priority: Option<Priority>,
    pub effort: Option<Effort>,
    pub labels: Option<Vec<String>>,
    pub due_date: Option<String>, // ISO 8601 string or null
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateColumn {
    pub name: String,
    pub color: Option<String>,
    pub wip_limit: Option<i32>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateColumn {
    pub name: Option<String>,
    pub position: Option<i32>,
    pub color: Option<String>,
    pub wip_limit: Option<i32>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateLabel {
    pub name: String,
    pub color: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateLabel {
    pub name: Option<String>,
    pub color: Option<String>,
}

// ===========================================
// BOARD DTOs
// ===========================================

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BoardListItem {
    pub id: String,
    pub name: String,
    pub ticket_count: i32,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateBoard {
    pub name: String,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateBoard {
    pub name: Option<String>,
    pub description: Option<String>,
}

// ===========================================
// SUBTASK
// ===========================================

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Subtask {
    pub id: String,
    pub parent_ticket_id: String,
    pub title: String,
    pub description: Option<String>,
    pub completed: bool,
    pub position: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateSubtask {
    pub parent_ticket_id: String,
    pub title: String,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateSubtask {
    pub title: Option<String>,
    pub description: Option<String>,
    pub completed: Option<bool>,
    pub position: Option<i32>,
}

// ===========================================
// AUTOMATION RULES
// ===========================================

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TriggerType {
    TicketCreated,
    TicketMoved,
    TicketUpdated,
    LabelAdded,
    LabelRemoved,
    DueDateApproaching,
    PriorityChanged,
}

impl TriggerType {
    pub fn as_str(&self) -> &str {
        match self {
            TriggerType::TicketCreated => "ticket_created",
            TriggerType::TicketMoved => "ticket_moved",
            TriggerType::TicketUpdated => "ticket_updated",
            TriggerType::LabelAdded => "label_added",
            TriggerType::LabelRemoved => "label_removed",
            TriggerType::DueDateApproaching => "due_date_approaching",
            TriggerType::PriorityChanged => "priority_changed",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "ticket_created" => Some(TriggerType::TicketCreated),
            "ticket_moved" => Some(TriggerType::TicketMoved),
            "ticket_updated" => Some(TriggerType::TicketUpdated),
            "label_added" => Some(TriggerType::LabelAdded),
            "label_removed" => Some(TriggerType::LabelRemoved),
            "due_date_approaching" => Some(TriggerType::DueDateApproaching),
            "priority_changed" => Some(TriggerType::PriorityChanged),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ActionType {
    MoveTicket,
    SetPriority,
    AddLabel,
    RemoveLabel,
    SetDueDate,
    Notify,
    AutoTriage,
}

impl ActionType {
    pub fn as_str(&self) -> &str {
        match self {
            ActionType::MoveTicket => "move_ticket",
            ActionType::SetPriority => "set_priority",
            ActionType::AddLabel => "add_label",
            ActionType::RemoveLabel => "remove_label",
            ActionType::SetDueDate => "set_due_date",
            ActionType::Notify => "notify",
            ActionType::AutoTriage => "auto_triage",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "move_ticket" => Some(ActionType::MoveTicket),
            "set_priority" => Some(ActionType::SetPriority),
            "add_label" => Some(ActionType::AddLabel),
            "remove_label" => Some(ActionType::RemoveLabel),
            "set_due_date" => Some(ActionType::SetDueDate),
            "notify" => Some(ActionType::Notify),
            "auto_triage" => Some(ActionType::AutoTriage),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AutomationRule {
    pub id: String,
    pub board_id: String,
    pub name: String,
    pub description: String,
    pub enabled: bool,
    pub trigger_type: TriggerType,
    pub trigger_config: serde_json::Value,
    pub action_type: ActionType,
    pub action_config: serde_json::Value,
    pub last_triggered_at: Option<DateTime<Utc>>,
    pub trigger_count: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateAutomationRule {
    pub board_id: String,
    pub name: String,
    pub description: String,
    pub trigger_type: TriggerType,
    pub trigger_config: Option<serde_json::Value>,
    pub action_type: ActionType,
    pub action_config: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateAutomationRule {
    pub name: Option<String>,
    pub description: Option<String>,
    pub enabled: Option<bool>,
    pub trigger_type: Option<TriggerType>,
    pub trigger_config: Option<serde_json::Value>,
    pub action_type: Option<ActionType>,
    pub action_config: Option<serde_json::Value>,
}

/// Payload for parsing natural language rules via AI
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ParseRuleRequest {
    pub board_id: String,
    pub natural_language: String,
}
