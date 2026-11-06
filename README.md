# Agentic Academy

Plataforma web para aprender ingeniería de agentes de IA de forma estructurada, progresiva y práctica.
Proyecto desarrollado con **Spec-Driven Development** ([GitHub Spec Kit](https://github.com/github/spec-kit)).

## Qué incluye el MVP

- **Ruta introductoria completa** «Foundations of Agentic AI Engineering» (5 módulos, inglés): lecciones con
  código, diagramas y etiquetas de madurez; test de conocimientos y reto de código por módulo.
- **Retos evaluados automáticamente** en un entorno aislado (gVisor, sin red, con límites).
- **Laboratorio** que reproduce trazas de agentes (eventos, llamadas a herramientas, estado, resúmenes de decisión), con comparación de patrones y aprobación humana. Sin llamadas a modelos.
- **Progreso basado en competencias demostradas**, panel, vista de competencias con evidencias y reinicio de ruta.
- **Catálogo** con la hoja de ruta completa (rutas planificadas) y cuentas con verificación de email.

## Stack

| Pieza | Tecnología |
|-------|------------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17 |
| Runner | Python 3.13, Docker + gVisor (`runsc`), cola en PostgreSQL con funciones `SECURITY DEFINER` |
| Frontend | React 19, TypeScript, Vite, TanStack Query, react-i18next, Shiki, Mermaid, CodeMirror 6 |
| Contenido | Markdown/YAML/JSON en `content/`, validado y publicado como paquetes inmutables |
| Tests | pytest, Vitest, Playwright + axe-core |

## Estructura

```text
backend/    API (módulos auth, content, catalog, assessments, challenges, lab, progress)
runner/     worker de evaluación + imagen del entorno aislado (academy_sim)
frontend/   SPA
content/    temario (competencias, rutas, módulos, retos, escenarios del laboratorio)
specs/      especificación, plan, contratos, quickstart y tareas (Spec Kit)
docs/       ADRs, seguridad, rendimiento, accesibilidad, revisión de contenido
```

## Puesta en marcha

Guía completa (variables de entorno, excepciones solo de desarrollo, escenarios de validación):
[`specs/001-agentic-academy-mvp/quickstart.md`](specs/001-agentic-academy-mvp/quickstart.md).

```bash
make setup
```

```bash
make up
```

```bash
make test
```

```bash
make e2e
```

## Documentación clave

- Especificación: [`specs/001-agentic-academy-mvp/spec.md`](specs/001-agentic-academy-mvp/spec.md)
- Plan y revisión de arquitectura: [`plan.md`](specs/001-agentic-academy-mvp/plan.md), [`architecture-review.md`](specs/001-agentic-academy-mvp/architecture-review.md)
- Contratos: [`contracts/`](specs/001-agentic-academy-mvp/contracts/)
- ADRs: [`docs/adr/`](docs/adr/)
- Seguridad del runner y riesgos aceptados (D1, D2): [`docs/security/runner-host.md`](docs/security/runner-host.md)

## Flujo Spec Kit

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`.
