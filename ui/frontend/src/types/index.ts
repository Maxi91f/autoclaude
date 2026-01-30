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
