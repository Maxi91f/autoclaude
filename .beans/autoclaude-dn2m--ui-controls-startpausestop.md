---
# autoclaude-dn2m
title: 'UI: Controls (start/pause/stop)'
status: completed
type: feature
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T18:53:39Z
updated_at: 2026-01-30T19:06:15Z
parent: autoclaude-9q87
---

Controles para manejar la ejecución de AutoClaude.

## Checklist
- [x] Endpoint POST /api/start con opciones
- [x] Endpoint POST /api/stop (graceful y force)
- [x] Endpoint POST /api/pause y /api/resume
- [x] Componente Controls con botones
- [x] Estados visuales (running, paused, stopped, rate_limited)
- [x] Selector de performer para run específico
- [x] Input para max iterations
- [x] Feedback visual de transiciones de estado

## Archivos
- ui/frontend/src/components/Controls.tsx

## Estados del proceso
- stopped: botón Start habilitado
- running: botones Pause y Stop habilitados
- paused: botones Resume y Stop habilitados
- rate_limited: mostrar countdown