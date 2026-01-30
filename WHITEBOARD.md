# Whiteboard

This file is for communication between Claude instances. Read it first, use it, maintain it.

## Blockers

### Deploy performer misconfigured for autoclaude project
- The `deploy.md` performer references `./ci/deploy/all.sh` which doesn't exist in this repo
- The CloudFront URL `https://d19j80mizfox40.cloudfront.net` appears to be for the Mento project, not autoclaude
- AutoClaude UI is designed for local network access (`localhost:8080`), not cloud deployment
- **Action needed**: Either remove the deploy performer from this project, or create deployment infrastructure if cloud deployment is desired
- **2026-01-30 20:15**: Verified again - no `ci/` directory exists. This performer cannot execute for autoclaude project. Exiting without completing test.

## Notes

### 2026-01-30 20:10 - JSON Events for UI Communication Implemented
- Added `--json-events` flag to `autoclaude run` command
- Created `autoclaude/json_events.py` module with emit functions for all event types:
  - `iteration_start` - emitted at start of each iteration with performer info and task counts
  - `iteration_end` - emitted after each iteration with result, task counts, and optional error message
  - `rate_limited` - emitted when rate limit is hit, includes reset time if available
  - `paused` / `resumed` - emitted on SIGUSR1/SIGUSR2 signals
  - `completed` - emitted when loop ends normally (all tasks done, max iterations, no progress, outside hours)
  - `terminated` - emitted when user terminates with Ctrl+C
  - `error` - emitted on exceptions
- Updated `ui/server/process_manager.py`:
  - Now passes `--json-events` flag when starting autoclaude
  - Added `_handle_json_event()` method to parse structured JSON events
  - Renamed old parsing method to `_parse_output_line_legacy()` for backwards compatibility
  - JSON events are tried first; falls back to legacy parsing if line is not valid JSON
- This makes UI communication robust to changes in text output format
- All 90 backend tests still pass

### 2026-01-30 20:05 - Pause/Resume Signal Handlers Implemented
- Added SIGUSR1 and SIGUSR2 signal handlers to `autoclaude/cli.py`
- SIGUSR1 pauses after current iteration (graceful pause)
- SIGUSR2 resumes execution
- The UI can now properly pause/resume autoclaude via the pause/resume buttons
- Visual indicator "(Paused)" shown in yellow in the output prefix when paused
- Allows termination while paused (Ctrl+C works)

### 2026-01-30 20:01 - UI Tests Added
- Backend tests (90 tests, pytest):
  - `ui/server/tests/conftest.py` - fixtures for temp DB, mocked subprocess, mocked WebSocket
  - `ui/server/tests/test_history.py` - SQLite operations (init_db, save_iteration, get_iterations, etc.)
  - `ui/server/tests/test_websocket.py` - ConnectionManager, classify_output_line, output handler
  - `ui/server/tests/test_api.py` - All REST endpoints (status, start, stop, pause, resume, tasks, etc.)
  - `ui/server/tests/test_process_manager.py` - ProcessManager (start, stop, pause, resume, output parsing)
- Frontend tests (42 tests, vitest):
  - `ui/frontend/src/__tests__/setup.ts` - Test setup with mocked WebSocket and fetch
  - `ui/frontend/src/__tests__/hooks/useApi.test.ts` - useApi hook and convenience hooks
  - `ui/frontend/src/__tests__/hooks/useWebSocket.test.ts` - WebSocket hook connection, send, reconnect
  - `ui/frontend/src/__tests__/components/StatusCards.test.tsx` - StatusCards component rendering
  - `ui/frontend/src/__tests__/types.test.ts` - getProcessStatus helper function
- CI workflow added: `.github/workflows/test.yml`
  - Runs backend tests with uv + pytest
  - Runs frontend tests with npm + vitest
  - Builds frontend to verify no breakage
- Test dependencies added to `pyproject.toml` (pytest, pytest-asyncio, httpx)
- Vitest configured in `ui/frontend/vite.config.ts`
- All tests passing: 90 backend + 42 frontend = 132 total tests

### 2026-01-30 19:51 - CLI 'ui' Command Added
- Added `autoclaude ui` command to launch the web UI server
- Supports `--host`, `--port`, and `--reload` flags
- Now users can run `autoclaude ui` instead of `python -m ui`

### 2026-01-30 19:32 - UI History View Completed
- Created `ui/server/history.py` - SQLite-based history storage
  - Database stored at `~/.autoclaude/history.db`
  - Schema: iterations table with iteration_number, performer, result, task counts, duration, timestamps
  - Functions: init_db, save_iteration, get_iterations (with pagination/filters), get_performers, get_stats
- Updated `ui/server/process_manager.py` to track iterations:
  - Added `IterationData` dataclass to track current iteration state
  - Parses output lines to detect iteration start/end
  - Saves iteration history on completion, error, rate limit, no progress, or cancellation
  - Counts beans before/after each iteration for task tracking
- Added API endpoints in `ui/server/api.py`:
  - `GET /api/history` - paginated iteration history with optional filters (result, performer)
  - `GET /api/history/stats` - summary statistics (total, success rate, errors, avg duration)
  - `GET /api/history/performers` - list of unique performers from history
- Created `ui/frontend/src/components/History.tsx`:
  - Timeline view with iterations grouped by day
  - Stats cards: total iterations, success rate, errors, avg duration
  - Iteration cards show: performer emoji/name, iteration #, time, duration, task changes
  - Visual result indicators (success=green, error=red, no_progress=yellow, rate_limited=orange, cancelled=gray)
  - Expandable error messages
  - Filters by result type and performer
  - "Load more" pagination
  - Collapsible day groups
- Updated navigation in Layout.tsx to include History link
- Build verified: `npm run build` passes

### 2026-01-30 19:26 - UI Polish (dark mode, mobile, PWA) Completed
- Implemented dark mode toggle with system preference detection
  - Created `ui/frontend/src/context/ThemeContext.tsx` for theme state management
  - Created `ui/frontend/src/components/ThemeToggle.tsx` with light/dark/system options
  - Updated all components to use `dark:` Tailwind variants for proper light/dark support
- Dark mode preference persisted in localStorage (`autoclaude-theme` key)
- Mobile optimizations:
  - All buttons and touch targets have min-h-[44px] for proper touch
  - Bottom navigation with larger icons and proper spacing
  - Responsive layouts with md: breakpoints
- PWA support:
  - Created `ui/frontend/public/manifest.json`
  - Created `ui/frontend/public/sw.js` (service worker with caching strategy)
  - Created SVG app icons (icon-192.svg, icon-512.svg)
  - Updated index.html with manifest link, theme-color, and SW registration
- Global error handling:
  - Created `ui/frontend/src/context/ToastContext.tsx` with success/error/warning/info toasts
  - Toasts auto-dismiss after 5 seconds
  - Positioned above mobile nav bar
- Build verified: `npm run build` passes

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

## Decisions

(none)
