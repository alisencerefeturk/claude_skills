# team-orchestration

A [Claude Code](https://claude.com/claude-code) skill and agent presets for orchestrating work on **one Claude Team seat**: the top-level session manages, cheaper Claude models do the work. It is the single-account sibling of [opus-orchestration](../opus-orchestration/README.md) (Claude Pro + ChatGPT Plus): no Codex/GPT lanes and no splitting work across accounts by quota.

| Tier | Where it runs | Role |
|---|---|---|
| **Manager** (Opus, the Team default) | main Claude Code session | Talks to the user, classifies and splits tasks, picks each worker's preset (model + effort), integrates reports. The only dispatcher. |
| **Haiku** | `team-haiku-worker` | Mechanical and bulk edits with a full brief, docs, read-only exploration, lookups. |
| **Sonnet** | `team-sonnet-worker`, `team-sonnet-worker-high` | Default executor for medium-tier code, bug fixes, tests, research; reviews Opus-written code. |
| **Opus workers** | `team-opus-worker`, `team-opus-worker-high` | Judgment-heavy work (design/direction choices, open multi-file decisions); reviews Sonnet/Haiku-written code. |
| **Fable** | `team-fable-worker` | Hard reasoning after Opus tried, and the second R3 reviewer. Premium seats only (Standard seats pay usage credits for it). |

Key ideas:

- **Manager / worker, one level deep.** You talk only to the top-level session; only it dispatches, and workers report back when they finish.
- **Sonnet is the default executor.** Field data from a real project measured Sonnet 5.5 with the lowest error density of any executor, and better than GPT's Sol 6.1 on both errors and time. On the personal stack it stayed second to GPT only to save Pro quota, and that reason is gone on a Team seat.
- **Review without a second model family.** R2 changes get an isolated review by a different Claude model than the author; R3 gets two reviewers of two different models, plus a break-the-rule check and human acceptance.
- **Fable is gated by seat type.** On a Premium seat Fable is included up to 50% of the weekly limits; on a Standard seat every call bills usage credits, so it runs only with your OK.
- **No live quota gauge, by design of the platform.** Claude Code gives `rate_limits` to the statusline only on Pro and Max, so on a Team seat the policy uses a fixed parallel cap, tells you before big batches so you can check `/usage`, and treats rate-limit errors as the signal. If a snapshot with numbers ever shows up, the gate in rule 8 uses it.
- **Asks once per project.** With no execution-regime section in a project, the manager asks seat type, risk tiers, measurement and commit attribution, and writes the answers to `AGENTS.md`.

The tier labels are Turkish: **basit** = simple, **orta** = medium, **zor** = hard.

## Contents

```
SKILL.md                      the policy (loaded as a Claude Code skill)
reference/review.md           review protocol for a single model family
reference/project-setup.md    setup questions, AGENTS.md template
reference/evidence.md         Claude field data, review study, Team seat facts
agents/team-*.md              worker presets (Haiku, Sonnet ×2, Opus ×2, Fable)
install.sh                    symlinks the skill, presets and statusline into the config dir
```

The statusline script is shared with opus-orchestration (`../opus-orchestration/statusline/statusline.sh`); there is one copy.

## Install

Install **one** orchestration skill per Claude config directory; both describe themselves as the policy for spawning sub-agents. On the company machine:

```bash
git clone <skills-repo-url> ~/skills
```

```bash
~/skills/install.sh team-orchestration ajan-olcum
```

If the company account uses its own config directory on a machine that also has your personal account, point the install at it:

```bash
CLAUDE_CONFIG_DIR=~/.claude-work ~/skills/install.sh team-orchestration
```

`install.sh` symlinks the files, moving existing ones to `<config dir>/backups/team-orchestration-<timestamp>/` first, adds the status line to `settings.json` if none is set (it shows model, context and effort), and stops if `opus-orchestration` is installed in the same place.

Requirements: Claude Code on a Team seat (Fable 5.1 needs Claude Code 2.1.255 or later), Python 3 for the statusline.

## Adapting it

The thresholds (parallel cap 5, gates at 60% / 70% / 85% when numbers exist) and the field data reflect one project as of October 2026. Haiku 5.5 and Fable have no field data yet; with `ajan-olcum` on, their first runs show whether their lanes should widen.
