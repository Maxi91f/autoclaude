---
# autoclaude-22wc
title: 'UI: Agregar tests para backend y frontend'
status: completed
type: task
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T19:48:28Z
updated_at: 2026-01-30T20:01:46Z
---

La UI no tiene tests.

## Backend (pytest)
- [x] Tests para api.py endpoints
- [x] Tests para process_manager.py (mock subprocess)
- [x] Tests para websocket.py (mock connections)
- [x] Tests para history.py (SQLite operations)
- [x] Crear ui/server/tests/ con conftest.py

## Frontend (vitest o jest)
- [x] Tests para hooks (useApi, useWebSocket)
- [x] Tests para componentes principales
- [x] Configurar vitest en vite.config.ts
- [x] Crear ui/frontend/src/__tests__/

## CI
- [x] Agregar step en CI para correr tests de UI