# Agentic Academy

Proyecto preparado para **Spec-Driven Development** con [GitHub Spec Kit](https://github.com/github/spec-kit) y Claude Code.

## Requisitos

- [uv](https://docs.astral.sh/uv/)
- Git
- Claude Code

Instala el CLI de Spec Kit:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

## Estructura

- `.specify/` — plantillas, scripts (`sh`), workflow y memoria del proyecto (`memory/constitution.md`).
- `.claude/skills/speckit-*` — skills de Spec Kit para Claude Code.
- `specs/` — se creará una carpeta por funcionalidad (`specs/001-.../`) al usar `/speckit-specify`.

## Flujo de trabajo

1. `/speckit-constitution` — definir los principios del proyecto.
2. `/speckit-specify` — describir qué se quiere construir y por qué.
3. `/speckit-clarify` *(opcional)* — resolver ambigüedades.
4. `/speckit-plan` — plan técnico de implementación.
5. `/speckit-checklist` *(opcional)* — checklist de calidad de requisitos.
6. `/speckit-tasks` — desglosar en tareas.
7. `/speckit-analyze` *(opcional)* — análisis de consistencia entre artefactos.
8. `/speckit-implement` — ejecutar la implementación.
9. `/speckit-converge` — evaluar el código y añadir el trabajo pendiente como tareas.
