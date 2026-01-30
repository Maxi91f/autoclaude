---
# autoclaude-ugyy
title: 'UI: History view (historial de iteraciones)'
status: completed
type: feature
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T18:53:54Z
updated_at: 2026-01-30T19:32:28Z
parent: autoclaude-9q87
---

Vista de historial de iteraciones pasadas.

## Checklist
- [x] Schema SQLite para guardar historial
- [x] Guardar datos de cada iteración al terminar
- [x] Endpoint GET /api/history con paginación
- [x] Componente History con timeline
- [x] Agrupación por día
- [x] Info por iteración: performer, resultado, duración, tasks
- [x] Indicadores visuales de resultado (success, no_progress, error)
- [x] Paginación infinita (load more)
- [x] Filtros opcionales

## Archivos
- ui/server/history.py (SQLite - created new file)
- ui/frontend/src/components/History.tsx

## Datos por iteración
- iteration number
- performer name + emoji
- result (success/no_progress/error/rate_limited)
- tasks_before, tasks_after
- duration_seconds
- started_at, ended_at
- error_message (si aplica)