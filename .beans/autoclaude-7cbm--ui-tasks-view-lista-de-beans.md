---
# autoclaude-7cbm
title: 'UI: Tasks view (lista de Beans)'
status: completed
type: feature
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T18:53:45Z
updated_at: 2026-01-30T19:13:38Z
parent: autoclaude-9q87
---

Vista de tareas integrada con Beans.

## Checklist
- [x] Endpoint GET /api/tasks que llama a beans query
- [x] Componente TaskList
- [x] Agrupación por status (in-progress, pending, completed)
- [x] Badges de prioridad con colores
- [x] Badges de tipo (feature, bug, task)
- [x] Filtros por status y tipo
- [x] Ordenamiento por prioridad/fecha
- [x] Secciones colapsables
- [x] Botón refresh

## Archivos
- ui/frontend/src/components/TaskList.tsx

## Colores de prioridad
- critical: rojo
- high: naranja
- normal: amarillo
- low: verde
- deferred: gris