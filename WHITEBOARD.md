# Whiteboard

This file is for communication between Claude instances. Read it first, use it, maintain it.

## Blockers

(none)

## Notes

### 2026-01-30 19:09 - UI Live Output Component Completed
- Created `ui/frontend/src/components/LiveOutput.tsx`
- Created `ui/frontend/src/hooks/useAutoScroll.ts`
- Features implemented:
  - Real-time output streaming via WebSocket (`output_line` events)
  - Line classification by type: thinking, tool_use, tool_result, error, text
  - Visual differentiation with colors and border highlights per type
  - Auto-scroll that pauses when user scrolls up, resumes on toggle
  - Timestamps toggle (HH:MM:SS format)
  - Copy all output to clipboard
  - Clear output button
  - Connection status indicator
  - Line count and error count stats
- Integrated into Dashboard with fixed height (h-96)
- Build verified: `npm run build` passes

### 2026-01-30 19:06 - UI Controls Component Completed
- Created `Controls.tsx` with start/pause/stop/resume buttons
- Added performer selector dropdown (fetches from `/api/performers`)
- Added max iterations input field
- Visual states for: stopped, running, paused, rate_limited
- Loading spinners during state transitions
- Options panel toggles when stopped
- Integrated Controls into Dashboard
- Added `/api/performers` endpoint to backend

### 2026-01-30 19:02 - UI Frontend Base + Dashboard Completed
- Created `ui/frontend/` with Vite + React + TypeScript + TailwindCSS
- Frontend runs with: `cd ui/frontend && npm run dev` (port 3000)
- Vite proxy configured for `/api` and `/ws` to localhost:8080
- Components created:
  - `Layout.tsx` - main layout with desktop nav and mobile bottom nav
  - `Dashboard.tsx` - main dashboard with status cards
  - `StatusCards.tsx` - status display with iteration, performer, tasks
- Hooks created:
  - `useWebSocket.ts` - WebSocket with auto-reconnection
  - `useApi.ts` - REST API calls with convenience hooks
- Types in `src/types/index.ts` matching backend models
- Build verified: `npm run build` works

### 2026-01-30 18:58 - UI Backend Base Completed
- Created `ui/server/` with FastAPI app
- Server runs with: `uv run python -m ui --port 8080`
- Available endpoints:
  - `GET /` - health check
  - `GET /api/status` - process status
  - `POST /api/start` - start autoclaude
  - `POST /api/stop` - stop autoclaude
  - `POST /api/pause` / `POST /api/resume` - pause/resume
  - `WS /ws` - WebSocket for real-time updates

## Decisions

(none)
