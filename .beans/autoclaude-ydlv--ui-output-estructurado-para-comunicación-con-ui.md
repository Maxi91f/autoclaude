---
# autoclaude-ydlv
title: 'UI: Output estructurado para comunicación con UI'
status: completed
type: task
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T19:48:14Z
updated_at: 2026-01-30T20:10:05Z
---

El process_manager parsea el output de autoclaude buscando strings específicos como 'Starting iteration', 'no progress', etc. Esto es frágil.

## Problema
Si autoclaude cambia su formato de output, la UI se rompe.

## Solución propuesta
Agregar flag `--json-events` a autoclaude que emita eventos estructurados:

```json
{"event": "iteration_start", "iteration": 1, "performer": "task", "emoji": "🔧"}
{"event": "output", "type": "thinking", "content": "Analyzing..."}
{"event": "iteration_end", "result": "success", "tasks_completed": 1}
{"event": "rate_limited", "reset_time": "2024-01-15T08:00:00"}
```

## Checklist
- [x] Agregar flag --json-events en cli.py
- [x] Emitir eventos JSON en puntos clave del loop
- [x] Actualizar process_manager.py para parsear JSON
- [x] Mantener output normal cuando no se usa el flag