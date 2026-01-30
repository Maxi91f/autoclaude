# Whiteboard

This file is for communication between Claude instances. Read it first, use it, maintain it.

## Blockers

### Deploy performer misconfigured for autoclaude project
- The `deploy.md` performer references `./ci/deploy/all.sh` which doesn't exist in this repo
- The CloudFront URL `https://d19j80mizfox40.cloudfront.net` appears to be for the Mento project, not autoclaude
- AutoClaude UI is designed for local network access (`localhost:8080`), not cloud deployment
- **Action needed**: Either remove the deploy performer from this project, or create deployment infrastructure if cloud deployment is desired

## Notes

### 2026-01-30 19:17 - UI Whiteboard View Completed
- Created `ui/frontend/src/components/Whiteboard.tsx`
- Added `GET /api/whiteboard` and `POST /api/whiteboard` endpoints
- Features implemented:
  - Markdown rendering with react-markdown (styled for dark mode)
  - Edit mode with full-screen textarea
  - Edit/Save/Cancel buttons
  - Last modified timestamp display
  - Auto-refresh every 30 seconds when not editing
  - Refresh button for manual updates
- Integrated into App router at `/whiteboard`
- Build verified: `npm run build` passes

### 2026-01-30 19:13 - UI Tasks View Completed
- Created `ui/frontend/src/components/TaskList.tsx`
- Added `GET /api/tasks` endpoint to backend (calls beans query)
- Features implemented:
  - Tasks grouped by status (in-progress, todo, completed, cancelled)
  - Priority badges with colors (critical: red, high: orange, normal: yellow, low: green, deferred: gray)
  - Type badges (feature, bug, task, epic, chore) with distinct colors
  - Filters by status and type
  - Sorting by priority, status, or title
  - Collapsible sections (completed/cancelled collapsed by default)
  - Refresh button
  - Expandable task details showing body content
- Integrated into App router at `/tasks`
- Build verified: `npm run build` passes

### 2026-01-30 19:09 - UI Live Output Component Completed
- Created `ui/frontend/src/components/LiveOutput.tsx`
- Created `ui/frontend/src/hooks/useAutoScroll.ts`
- Features: real-time streaming, line classification, auto-scroll, timestamps, copy, clear

### 2026-01-30 19:06 - UI Controls Component Completed
- Created `Controls.tsx` with start/pause/stop/resume buttons
- Added performer selector and max iterations input
- Added `/api/performers` endpoint to backend

### 2026-01-30 19:02 - UI Frontend/Backend Base Completed
- Frontend: Vite + React + TypeScript + TailwindCSS (port 3000)
- Backend: FastAPI + WebSocket (port 8080)
- Components: Layout, Dashboard, StatusCards, LiveOutput, Controls, TaskList
- Hooks: useWebSocket, useApi, useAutoScroll

## Decisions

(none)
