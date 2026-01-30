---
# autoclaude-3ojm
title: 'UI: Live Output streaming'
status: completed
type: feature
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T18:53:32Z
updated_at: 2026-01-30T19:09:29Z
parent: autoclaude-9q87
---

Componente de output en tiempo real de Claude.

## Checklist
- [x] Endpoint WebSocket para streaming de output
- [x] Parsear y clasificar líneas (thinking, tool_use, text, error)
- [x] Componente LiveOutput con auto-scroll
- [x] Formateo visual diferenciado por tipo (colores, iconos)
- [x] Hook useAutoScroll
- [x] Botón copy to clipboard
- [x] Timestamps en cada línea

## Archivos
- ui/frontend/src/components/LiveOutput.tsx
- ui/frontend/src/hooks/useAutoScroll.ts

## Tipos de output a manejar
- 💭 thinking (gris/italic)
- 🔧 tool_use (azul)
- ✅ tool_result success (verde)
- ❌ tool_result error (rojo)
- texto normal