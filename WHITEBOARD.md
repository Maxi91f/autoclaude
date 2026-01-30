# Whiteboard

This file is for communication between Claude instances. Read it first, use it, maintain it.

## Blockers

### Deploy performer misconfigured for autoclaude project
- The `deploy.md` performer references `./ci/deploy/all.sh` which doesn't exist in this repo
- The CloudFront URL `https://d19j80mizfox40.cloudfront.net` appears to be for the Mento project, not autoclaude
- AutoClaude UI is designed for local network access (`localhost:8080`), not cloud deployment
- **Action needed**: Either remove the deploy performer from this project, or create deployment infrastructure if cloud deployment is desired

## Notes

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
