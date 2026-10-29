# Project setup: questions and template

Used by "Project setup" in `SKILL.md` when a project has no execution-regime
section. Ask in one round, in the user's language, recommended default
first (`AskUserQuestion` where available). Explain each choice in one plain
sentence; the user may be new to this policy.

## Questions

1. **Executor lane.**
   - *Default (recommended for a single Claude account):* Sol writes orta
     code, Luna does research and low-risk work, Sonnet is the exception
     (rule 5).
   - *Separate Claude executor account:* a second account runs headless as
     `claude -p` with its own `CLAUDE_CONFIG_DIR`; Sonnet becomes the main
     executor and Sol reviews its code. If chosen, ask for the config
     directory (its quota snapshot is `<dir>/rate-limit-status.json`) and
     say plainly: Anthropic's terms do not clearly allow using several paid
     accounts in turn to get past usage limits, and users have reported
     suspensions; it is the user's call. Record that they chose it knowingly,
     with the date.
2. **Risk tiers.** *Default:* the R0–R3 table in `SKILL.md`. *Alternative:*
   the project's own definition (ask where it lives). If the project uses
   `ajan-olcum`, its tiers must map to R0–R3, since the difficulty score
   uses them.
3. **Measurement.** Only if the `ajan-olcum` skill is installed: record
   every dispatch with it? (Recommended: yes; it is what keeps rule 5 honest.)
   Ask for the project name to use in `olcum run --proje`.
4. **Commit attribution.** May commits and PRs carry AI co-author or
   "Generated with" lines? If not, every executor spec says so.

## Template

Write into the project's `AGENTS.md` (create it if missing; if only
`CLAUDE.md` exists, add it there). Show it to the user; don't commit unless
asked.

```markdown
## Execution regime (opus-orchestration, set up YYYY-MM-DD)
- Executor lane: default (rule 5) | separate Claude account: `CLAUDE_CONFIG_DIR=<dir>`, quota file `<dir>/rate-limit-status.json` (owner chose this knowing the terms risk, YYYY-MM-DD)
- Risk tiers: default R0–R3 | <path to project definition>
- Measurement: ajan-olcum (`olcum run --proje <name>`) | none
- Commit attribution: no AI co-author or "Generated with" lines | allowed
This section overrides opus-orchestration where they conflict.
```
