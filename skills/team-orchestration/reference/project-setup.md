# Project setup: questions and template

Used by "Project setup" in `SKILL.md` when a project has no execution-regime
section. Ask in one round, in the user's language, recommended default
first (`AskUserQuestion` where available). Explain each choice in one plain
sentence; the user may be new to this policy.

## Questions

1. **Seat type.** Skip if the user's global `CLAUDE.md` already records it.
   - *Premium:* Fable is included up to 50% of the weekly limits, so
     `team-fable-worker` is available for rule 6 work and as the second R3
     reviewer.
   - *Standard:* every Fable call bills usage credits; Fable runs only when
     the user OKs it for a task.
   - *Not sure:* treat it as Standard. The user can check under claude.ai
     settings or ask the Team admin.
   Offer to record the answer once in the global `CLAUDE.md`
   (`${CLAUDE_CONFIG_DIR:-~/.claude}/CLAUDE.md`) as
   `Claude Team seat: Premium|Standard`, so other projects don't ask again.
2. **Risk tiers.** *Default:* the R0–R3 table in `SKILL.md`. *Alternative:*
   the project's own definition (ask where it lives). If the project uses
   `ajan-olcum`, its tiers must map to R0–R3, since the difficulty score
   uses them.
3. **Measurement.** Only if the `ajan-olcum` skill is installed: record
   every dispatch with it? (Recommended: yes; it is what tells whether
   Haiku and Fable earn a wider lane.) Ask for the project name to use in
   `olcum ... --proje`.
4. **Commit attribution.** May commits and PRs carry AI co-author or
   "Generated with" lines? Company repos often have a rule; if not allowed,
   every brief says so.

## Template

Write into the project's `AGENTS.md` (create it if missing; if only
`CLAUDE.md` exists, add it there). Show it to the user; don't commit unless
asked.

```markdown
## Execution regime (team-orchestration, set up YYYY-MM-DD)
- Seat: Premium (Fable lane on) | Standard (Fable only with the user's OK per task)
- Risk tiers: default R0–R3 | <path to project definition>
- Measurement: ajan-olcum (`--proje <name>`) | none
- Commit attribution: no AI co-author or "Generated with" lines | allowed
This section overrides team-orchestration where they conflict.
```
