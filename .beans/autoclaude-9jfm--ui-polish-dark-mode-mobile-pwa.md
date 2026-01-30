---
# autoclaude-9jfm
title: 'UI: Polish (dark mode, mobile, PWA)'
status: completed
type: feature
priority: normal
tags:
    - autoclaude
created_at: 2026-01-30T18:54:10Z
updated_at: 2026-01-30T19:26:19Z
parent: autoclaude-9q87
---

Mejoras finales de UX y soporte mobile.

## Checklist
- [x] Dark mode toggle (detectar preferencia del sistema)
- [x] Persistir preferencia en localStorage
- [x] Optimizaciones mobile (touch targets 44px, responsive)
- [x] Bottom navigation en mobile
- [x] PWA manifest.json
- [x] Service worker básico
- [x] Icono de app
- [x] Error handling global con toast/snackbar
- [x] Loading states en todas las vistas
- [ ] Notificaciones browser (opcional)

## Archivos
- ui/frontend/public/manifest.json
- ui/frontend/public/sw.js
- ui/frontend/public/icon-192.svg
- ui/frontend/public/icon-512.svg

## Breakpoints responsive
- sm: 640px (teléfonos landscape)
- md: 768px (tablets)
- lg: 1024px (desktop)
