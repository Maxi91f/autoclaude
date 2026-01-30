---
# autoclaude-9q87
title: AutoClaude Web UI
status: completed
type: epic
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T18:53:07Z
updated_at: 2026-01-30T19:33:19Z
---

Interfaz web para monitorear y controlar AutoClaude desde browser o móvil en red local.

## Objetivo
Crear una UI que permita:
- Ver estado en tiempo real (iteración, tasks, performer)
- Ver output streaming de Claude
- Controlar ejecución (start/pause/stop)
- Ver lista de tareas de Beans
- Ver historial de iteraciones
- Ver/editar whiteboard

## Stack
- Backend: FastAPI + uvicorn + WebSocket
- Frontend: React + Vite + TailwindCSS
- Estado: SQLite
- Comunicación: REST + WebSocket

## Plan detallado
Ver local/UI_PLAN.md