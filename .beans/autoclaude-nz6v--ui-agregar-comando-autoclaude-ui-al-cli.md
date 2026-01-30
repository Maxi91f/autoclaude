---
# autoclaude-nz6v
title: 'UI: Agregar comando ''autoclaude ui'' al CLI'
status: completed
type: task
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T19:48:04Z
updated_at: 2026-01-30T19:50:58Z
---

Actualmente la UI se corre con `python -m ui`. Debería integrarse al CLI principal.

## Checklist
- [x] Agregar comando `ui` en autoclaude/cli.py
- [x] Importar y llamar a ui.__main__.main()
- [x] Soportar los mismos flags (--host, --port, --reload)
- [x] Documentar en --help

## Ejemplo de uso esperado
```bash
autoclaude ui                    # Lanza en 0.0.0.0:8080
autoclaude ui --port 3000        # Puerto custom
autoclaude ui --reload           # Dev mode
```