---
# autoclaude-iomp
title: 'UI: Implementar pause/resume con señales'
status: completed
type: task
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T19:48:21Z
updated_at: 2026-01-30T20:05:31Z
---

La UI envía SIGUSR1/SIGUSR2 para pause/resume pero autoclaude no las maneja.

## Estado actual
- autoclaude solo maneja SIGTERM (graceful shutdown)
- La UI asume que SIGUSR1 = pause, SIGUSR2 = resume

## Checklist
- [x] Agregar handler para SIGUSR1 en autoclaude (pause after current iteration)
- [x] Agregar handler para SIGUSR2 en autoclaude (resume execution)
- [x] Agregar estado 'paused' al loop principal
- [x] Mostrar indicador visual cuando está pausado
- [x] Testear que pause espera a que termine la iteración actual

## Implementación
- `autoclaude/cli.py`: Added `paused` state variable and signal handlers for SIGUSR1/SIGUSR2
- SIGUSR1 sets `paused = True` and prints "⏸ Pausing after current iteration..."
- SIGUSR2 sets `paused = False` and prints "▶ Resuming..."
- Main loop waits in pause loop at start of each iteration if paused
- Visual indicator "(Paused)" shown in yellow in output prefix when paused
- All 90 backend tests pass, frontend build succeeds