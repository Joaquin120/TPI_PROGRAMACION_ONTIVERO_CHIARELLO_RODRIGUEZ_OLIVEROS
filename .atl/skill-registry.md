# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

---

## User Skills

| Trigger | Skill | Path |
|---|---|---|
| /poteto-mode, poteto, engineering rigor | `poteto-mode` | `/home/joaquin/.gemini/config/plugins/agystack/skills/poteto-mode/SKILL.md` |
| armar base de conocimiento, crear KB, documentar proyecto | `kb-creator` | `/home/joaquin/.gemini/config/skills/kb-creator/SKILL.md` |
| armar roadmap, CHANGES.md, plan de implementación | `roadmap-generator` | `/home/joaquin/.gemini/config/skills/roadmap-generator/SKILL.md` |
| generar AGENTS.md / CLAUDE.md, reglas de proyecto | `agent-instruction` | `/home/joaquin/.gemini/config/skills/agent-instruction/SKILL.md` |
| encontrar e instalar skills | `find-skill` | `/home/joaquin/.gemini/config/skills/find-skill/SKILL.md` |
| actualizar registry, skills disponibles | `skill-registry` | `/home/joaquin/.gemini/config/skills/skill-registry/SKILL.md` |
| loops de verificación automática hasta verde | `loop` | `/home/joaquin/.gemini/config/plugins/agystack/skills/loop/SKILL.md` |
| revisión adversarial y detección de fallas | `interrogate` | `/home/joaquin/.gemini/config/plugins/agystack/skills/interrogate/SKILL.md` |

---

## Compact Rules

Pre-digested rules per skill for delegators to inject into sub-agent prompts.

### poteto-mode
- Always verify work with real execution and tests before reporting success.
- Use unslopped, direct, concise prose; never use conversational filler.
- Respect separation of concerns: plan and verify in coordinator, write code in delegate.
- Keep commits atomic and verify clean git status.

### kb-creator
- Builds canonical 10 markdown files in `knowledge-base/` at project root.
- Ingest mode derives factual specifications without asking strategic questions.
- Never invent constraints or values; record open questions in `10_preguntas_abiertas.md`.

### roadmap-generator
- Emits `CHANGES.md` at project root with semantic phases, dependency tree, and GATES.
- Every change follows strict structure: Estado, Scope, Dependencias, Governance, Leer antes.
- Respect critical path and multi-agent workload balance.

### agent-instruction
- Emits canonical `AGENTS.md` and `CLAUDE.md` tailored strictly to project stack.
- Never repeats generic system prompts; enforces project hard rules and zero hardcoded secrets.

---

## Project Conventions

| File | Path | Notes |
|---|---|---|
| `consignas_global_evaluacion_y_despliegue.md` | `consignas_global_evaluacion_y_despliegue.md` | Consignas oficiales del TPI y rúbrica de evaluación |
| `CHANGES.md` | `CHANGES.md` | Hoja de ruta canónica de changes y dependencias |
| `knowledge-base/` | `knowledge-base/` | Base de conocimiento canónica (11 archivos + README) |
| `design-system/README.md` | `design-system/README.md` | Política visual aprobada (system-only / HTML y CSS nativos) |
