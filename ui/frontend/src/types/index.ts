// Process status enum
export type ProcessStatus = 'stopped' | 'running' | 'paused' | 'rate_limited'

// Status response from /api/status
export interface StatusResponse {
  running: boolean
  paused: boolean
  iteration: number | null
  performer: string | null
  performer_emoji: string | null
  beans_pending: number
  beans_completed: number
  no_progress_count: number
  started_at: string | null
  rate_limited_until: string | null
}

// Request body for /api/start
export interface StartRequest {
  max_iterations?: number | null
  performer?: string | null
  start_hour?: number
  end_hour?: number
}

// Response from /api/start
export interface StartResponse {
  success: boolean
  pid?: number | null
  error?: string | null
}

// Request body for /api/stop
export interface StopRequest {
  force?: boolean
}

// Simple response for stop/pause/resume
export interface SimpleResponse {
  success: boolean
  error?: string | null
}

// Output line types from Claude
export type OutputLineType = 'text' | 'thinking' | 'tool_use' | 'tool_result' | 'error'

// WebSocket event types
export type WSEventType =
  | 'status_change'
  | 'iteration_start'
  | 'output_line'
  | 'iteration_end'
  | 'task_completed'
  | 'rate_limited'
  | 'error'
  | 'pong'

// WebSocket message from server
export interface WSMessage {
  event: WSEventType
  data: Record<string, unknown>
}

// WebSocket message from client
export interface WSClientMessage {
  action: string
}

// Output line data
export interface OutputLine {
  type: OutputLineType
  content: string
  timestamp: string
}

// Performer info
export interface PerformerInfo {
  name: string
  emoji: string
  description: string
}

// Response from /api/performers
export interface PerformersResponse {
  performers: PerformerInfo[]
}

// Task priority
export type TaskPriority = 'critical' | 'high' | 'normal' | 'low' | 'deferred'

// Task type
export type TaskType = 'feature' | 'bug' | 'task' | 'epic' | 'chore'

// Task status
export type TaskStatus = 'todo' | 'in-progress' | 'completed' | 'cancelled'

// Task info
export interface TaskInfo {
  id: string
  title: string
  status: string
  type: string
  priority: string
  body?: string | null
}

// Response from /api/tasks
export interface TasksResponse {
  tasks: TaskInfo[]
}

// Response from GET /api/whiteboard
export interface WhiteboardResponse {
  content: string
  last_modified: string | null
}

// Request body for POST /api/whiteboard
export interface WhiteboardUpdateRequest {
  content: string
}

// Iteration result types
export type IterationResult = 'success' | 'no_progress' | 'error' | 'rate_limited' | 'cancelled'

// Iteration info for history
export interface IterationInfo {
  id: number
  iteration_number: number
  performer_name: string
  performer_emoji: string
  result: IterationResult
  tasks_before: number
  tasks_after: number
  duration_seconds: number
  started_at: string
  ended_at: string
  error_message?: string | null
}

// Response from GET /api/history
export interface HistoryResponse {
  iterations: IterationInfo[]
  total: number
  has_more: boolean
}

// Response from GET /api/history/stats
export interface HistoryStatsResponse {
  total: number
  success_count: number
  no_progress_count: number
  error_count: number
  avg_duration_seconds: number
}

// Response from GET /api/history/performers
export interface HistoryPerformersResponse {
  performers: string[]
}

// Helper to derive process status from StatusResponse
export function getProcessStatus(status: StatusResponse): ProcessStatus {
  if (status.rate_limited_until) {
    return 'rate_limited'
  }
  if (status.paused) {
    return 'paused'
  }
  if (status.running) {
    return 'running'
  }
  return 'stopped'
}
