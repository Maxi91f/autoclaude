---
# autoclaude-iwqr
title: 'UI: Backend base (FastAPI + WebSocket)'
status: completed
type: feature
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T18:53:15Z
updated_at: 2026-01-30T18:58:02Z
parent: autoclaude-9q87
---

Configurar el backend base con FastAPI.

## Checklist
- [x] Crear estructura de carpetas ui/server/
- [x] FastAPI app con CORS configurado
- [x] Endpoint /api/status básico
- [x] WebSocket connection handler con broadcast
- [x] Process manager para controlar proceso autoclaude
- [x] Modelos Pydantic para API

## Archivos a crear
- ui/__init__.py
- ui/__main__.py
- ui/server/__init__.py
- ui/server/app.py
- ui/server/api.py
- ui/server/websocket.py
- ui/server/process_manager.py
- ui/server/models.py

## Dependencias
Agregar a pyproject.toml:
- fastapi>=0.109.0
- uvicorn[standard]>=0.27.0
- websockets>=12.0