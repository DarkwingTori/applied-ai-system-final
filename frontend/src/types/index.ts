// ── API response types ────────────────────────────────────────────────────────

export interface AskResponse {
  answer: string;
  confidence: number;
  sources: string[];
  low_confidence: boolean;
}

export interface ScheduledTask {
  title: string;
  task_type: "walk" | "feeding" | "medication" | "enrichment" | "grooming";
  duration_minutes: number;
  priority: "low" | "medium" | "high";
  pet_name: string;
  start_time: string;
  completed: boolean;
}

export interface ScheduleResponse {
  scheduled_tasks: ScheduledTask[];
  reasoning: string[];
  total_scheduled_time: number;
}

// ── Chat types ────────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  confidence?: number;
  sources?: string[];
  low_confidence?: boolean;
  timestamp: Date;
}
