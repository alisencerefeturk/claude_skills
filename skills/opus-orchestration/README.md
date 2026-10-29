# opus-orchestration

A [Claude Code](https://claude.com/claude-code) skill and agent presets for running a **Claude Pro + ChatGPT Plus** stack cost-effectively: Opus orchestrates, and cheaper models do the work.

> **Claude Code only.** This needs Claude Code as the host. It won't work if you load it in Codex, Antigravity, or other agents. See [Compatibility](#compatibility).

| Tier | Where it runs | Role |
|---|---|---|
| **Opus (manager)** | main Claude Code session | Talks to the user, classifies and splits tasks, picks each worker's model and effort, synthesizes worker reports. The only dispatcher. |
| **Luna** (`gpt-6-luna`) | Codex CLI | Research, exploration, bulk and mechanical work, small low-risk code with a complete spec. |
| **Sol** (`gpt-6.1-sol`) | Codex CLI | Default executor for medium-tier code and precision work against a complete spec. |
| **Astra** (`gpt-6-astra`) | Codex CLI | Hard reasoning only. It burns quota fastest. |
| **Sonnet** | `sonnet-worker`, `sonnet-worker-high` presets | Claude-side tools, cross-family review of GPT code, fallback when GPT fails. |
| **Opus workers** | `opus-worker`, `opus-worker-high` presets | Detailed judgment-heavy work, highest-stakes and extra isolated reviews. |
| **Haiku** | `haiku-worker` preset | Fallback only, for simple work when GPT is unavailable. |

Key ideas:

- **Manager / worker.** You talk only to the top-level Opus session; workers report back to it when they finish.
- **Asks once per project.** The first time it runs in a project without an execution-regime section, the manager asks a few setup questions (executor lane, risk tiers, measurement, commit attribution) and writes the answers to the project's `AGENTS.md`. You don't need to remember the options.
- **Delegation is one level deep.** Only Opus dispatches work, so every call is auditable.
- **Effort is chosen per task.** The manager picks each worker's effort (Codex `model_reasoning_effort`, or the preset's `effort`).
- **Claude quota is read live.** `statusline.sh` writes it to `${CLAUDE_CONFIG_DIR:-~/.claude}/rate-limit-status.json` on every message, and Claude-side worker use (Sonnet and Opus) is gated on it.
- **Review family follows risk.** R2/R3 changes are reviewed by the other model family; routine work relies on tests, CI and break-it checks (rule 9, backed by Greptile's 2026 cross-family data).
- **Routing follows data.** Executor choice is based on field data from a real project (error density per difficulty point) plus published benchmarks, both in `reference/evidence.md`. With the optional `ajan-olcum` measurement skill (separate, not part of this repo), every dispatch is measured and `olcum rapor` keeps that data current.

The tier labels in the skill are Turkish: **basit** = simple, **orta** = medium, **zor** = hard.

## Contents

```
skills/opus-orchestration/SKILL.md   the policy (loaded as a Claude Code skill)
skills/opus-orchestration/reference/ details read on demand: codex.md (commands, pitfalls),
                                     review.md (review protocol, severity, verdicts),
                                     project-setup.md (setup questions, AGENTS.md template),
                                     evidence.md (field data, benchmarks, review study)
agents/sonnet-worker.md              Sonnet preset (medium effort)
agents/sonnet-worker-high.md         Sonnet preset (high effort)
agents/opus-worker.md                Opus worker preset (medium effort)
agents/opus-worker-high.md           Opus worker preset (high effort)
agents/haiku-worker.md               Haiku fallback preset
statusline/statusline.sh             statusLine hook that snapshots quota usage
install.sh                           symlinks everything into ~/.claude
```

## Install

Requirements: Claude Code on a Pro or Max plan (Pro/Max accounts are the only ones that expose `rate_limits`), [Codex CLI](https://github.com/openai/codex) signed in with ChatGPT, and Python 3.

### Option A: let Claude Code install it (easiest)

Paste this into a Claude Code session:

````text
Install the opus-orchestration skill from my skills repo (<skills-repo-url>, folder skills/opus-orchestration) for me:

1. Clone the repo to ~/skills. If that folder already exists and is this repo, run `git pull` in it instead.
2. Run ./install.sh from the repo root. It links every skill; for opus-orchestration it also symlinks the skill, the agent presets, and statusline.sh into ~/.claude and backs up any existing files first.
3. Add "statusLine": {"type": "command", "command": "~/.claude/statusline.sh"} to ~/.claude/settings.json. Merge it and keep every other setting as is. If a different statusLine is already configured, show it to me and ask before replacing it.
4. Check the prerequisites and report each one: `python3 --version`, `codex --version`, and whether Codex is logged in (`codex login status`). If something is missing, tell me how to fix it, but don't install it yourself.
5. Tell me to restart Claude Code, then summarize what was installed and anything I still need to do by hand.
````

### Option B: manual

```bash
git clone <skills-repo-url> ~/skills
~/skills/install.sh                              # every skill
# or only this one:
~/skills/skills/opus-orchestration/install.sh
```

`install.sh` symlinks the files into `~/.claude`, moving any existing files to `~/.claude/backups/opus-orchestration-<timestamp>/` first. Because they are symlinks, edits from either side show up in `git diff`.

Then enable the status line in `~/.claude/settings.json`:

```json
"statusLine": { "type": "command", "command": "~/.claude/statusline.sh" }
```

## Compatibility

| Host | Works? | Why |
|---|---|---|
| **Claude Code** (CLI, desktop, IDE extensions) | ✅ | This is what it was built for. |
| **OpenAI Codex CLI / ChatGPT** | ❌ | In this setup Codex is a worker that Claude Code calls, not the host. |
| **Google Antigravity, Cursor, other agents** | ❌ | They have no equivalent of the Claude Code features listed below. |

The policy relies on four Claude Code features:

- the `Agent` tool and `~/.claude/agents/` presets, for dispatching the `*-worker` presets;
- the `statusLine` hook, which provides `rate_limits` for live quota checks;
- Opus running as the top-level session model;
- Claude Code's skill loader.

Another agent might be able to read `SKILL.md` as plain text, but it can't apply the routing. The general ideas carry over to other stacks: a scarce orchestrator, cheap default workers, one-level delegation, and routing gated on quota. The implementation doesn't.

## Adapting it

Model IDs, quota thresholds (60% / 70% / 85%), and benchmark numbers reflect one account as of September 2026. Check `codex` → `/model` for the IDs available to you, and tune the thresholds to your own usage.

## License

MIT — see [LICENSE](LICENSE).
