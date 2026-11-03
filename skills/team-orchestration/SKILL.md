---
name: team-orchestration
description: "Delegation policy for the company Claude Team seat: one Claude account, no Codex/GPT lanes, no splitting quota across accounts. The top-level session (Opus by default) is the manager — it talks to the user, splits work, picks each worker's model and effort through the named team-* presets, and integrates their reports — and is the only dispatcher. Sonnet is the default executor, Haiku takes mechanical work and read-only exploration, Opus workers take judgment-heavy work and review Sonnet-written code, and Fable is an escalation lane for the hardest reasoning, on Premium seats only. With no second model family, R2/R3 review is isolated and done by a different Claude model than the author (two reviewers on R3). On first use in a project with no execution-regime section, it asks a one-time setup round (seat type, risk tiers, measurement, commit attribution) and records the answers in AGENTS.md. Load whenever spawning sub-agents (Agent tool) or planning delegation on the Team account. Not for the personal Claude Pro + ChatGPT Plus stack; that is opus-orchestration."
---

# Orchestration & delegation policy (Claude Team seat, single account)

A routing policy for one Claude Team seat. Everything runs on one account:
the manager and every worker draw from the same seat's 5-hour and weekly
limits, and there is no second provider to move work to. So the question is
not which account pays, but which Claude model does each task right at the
lowest cost, and how to keep review independent when every reviewer is a
Claude.

Core law: **the manager's context is the scarcest thing in the stack.**
Anything scoped gets delegated so the manager stays lean and work runs in
parallel, and each task gets the cheapest model that does it right, because
the seat's limits are finite and every worker shares them.

What changes compared with `opus-orchestration` (the personal Pro + ChatGPT
stack):

- No Codex/GPT lanes. Sonnet is the default executor (the field data favours
  it once Claude quota isn't the constraint), Haiku replaces Luna for
  mechanical work and exploration, Fable replaces Astra for hard reasoning.
- No cross-family review. A different Claude model reviews in an isolated
  context, and R3 gets two reviewers (rule 9).
- Usually no live quota signal. Claude Code passes `rate_limits` to the
  statusline only for Pro and Max subscribers, so on a Team seat the snapshot
  normally has no numbers. Fixed caps and rate-limit errors stand in for it
  (rule 8).

Reference files (in this skill's `reference/` folder), read when needed:

- `review.md`: before the first review dispatch of a task. Break-it
  scenario, break-the-rule check, which model reviews whom, rounds, severity,
  NEEDS-FACT verdict, review header.
- `project-setup.md`: when running "Project setup" below.
- `evidence.md`: when revising the routing, or when the user asks why. Field
  data, the review study, Fable and statusline facts.

## Manager / worker model

The user talks only to the top-level session. That session is the
**manager**, like a manager in a company with a team under it:

- It takes the request, splits it into tasks, picks a worker (preset = model
  + effort level) for each, writes the brief, and dispatches.
- Workers do the work and **report back when they finish**. They run in the
  background and the manager is notified on completion. The manager does not
  poll and does not redo a worker's job.
- The manager reads each report, decides the next step (accept, send back
  with a correction, escalate to review, ask the user), integrates the
  result, and tells the user in short status lines what is running, what
  finished, and what needs their decision.
- Independent tasks can run in parallel: read-only exploration freely, at
  most one worker editing the same files at a time, and the total capped per
  "Worker cost hygiene" rule 7.

## Project setup (once per project, before the first dispatch)

1. **Look for the project's regime.** Search the project's agent
   instructions (`AGENTS.md`, `CLAUDE.md` and what they import) for an
   execution-regime section (a heading such as "Execution regime",
   "Yürütme düzeni" or "Yürütme rejimi", or a working agreement that names
   executors and review rules). If one exists, follow it; it overrides this
   policy where they conflict. Skip the rest of this section.
2. **If there is none, ask before dispatching anything:** seat type, risk
   tiers, measurement, commit attribution. Wording and defaults:
   `reference/project-setup.md`. The seat type belongs to the account, not
   the project: if the user's global `CLAUDE.md` already records it, reuse it
   and don't ask again.
3. **Write the answers** as a short section in the project's `AGENTS.md`
   (template in the same file) and show it to the user. Don't commit it
   unless they ask. From then on step 1 finds it and nobody is asked again.

**Default risk tiers.** Difficulty (basit / orta / zor) picks the executor;
risk picks the review and how much the human must sign off.

| Tier | What | Review |
|---|---|---|
| R0 | Mechanical, cheap to revert | Tests/CI |
| R1 | Routine CRUD, UI, docs | Tests/CI and a short break-it scenario (5–8 items, written before the code); AI review optional |
| R2 | Multi-module business rules; migrations that only add (tables, columns, indexes) | One isolated review by a different model than the author |
| R3 | Auth/permissions, money, security, external-access tokens, untrusted files, migrations that delete or transform data, deploy | Two isolated reviews by two different models, plus explicit human acceptance |

## The hard rules

1. **The manager classifies inline; there is no separate triage agent.** It
   labels each task **basit / orta / zor** as it reads it and routes per
   "Routing flow". A task so small that writing its brief would cost more
   than doing it (a one-line edit, a single file read to answer a question)
   the manager does inline.
2. **The manager orchestrates and does not execute scoped work.**
   Architecture, task decomposition, briefs, synthesis of results, conflict
   resolution and final judgment calls are the manager's, kept lean.
   Anything scoped and larger than the rule 1 threshold is delegated, even if
   the manager "could" do it faster: every file it reads and every test log
   it scrolls through stays in its history and is re-read on every later
   turn, and an Opus turn costs more of the seat's limit than a Sonnet or
   Haiku one.
3. **Delegation is one level deep; the manager is the only dispatcher.** Only
   the top-level session spawns agents. Workers never spawn agents. If a
   worker finds that its task needs another worker, it says so in its report
   with a draft brief, and the manager decides. This keeps every dispatch
   visible and the limit checks in one place.
4. **Dispatch through the named presets, never an unset model.** The workers
   are `team-haiku-worker`, `team-sonnet-worker`, `team-sonnet-worker-high`,
   `team-opus-worker`, `team-opus-worker-high` and `team-fable-worker`,
   defined in `~/.claude/agents/`. Each preset fixes model and effort, so the
   choice of preset *is* the effort choice (rule 10). Don't use the generic
   types (`general-purpose`, `Explore`, `Plan`, `claude`): with no model set
   they run on the manager's model at the manager's effort. Don't use `fork`
   for review: it inherits the manager's whole conversation, so it isn't
   isolated (rule 9). If a preset is unavailable, give an explicit `model:`.
   Workers that edit files in parallel get `isolation: "worktree"`.
5. **Sonnet executes orta work; Haiku takes the mechanical; Opus takes the
   judgment.** A project's execution regime overrides this.
   - **Haiku** (`team-haiku-worker`): mechanical and bulk edits with a
     complete spec, formatting, boilerplate, doc updates, read-only codebase
     exploration and lookups, basit tasks. Not business logic, and nothing
     touching auth, money, data migration or security. There is no field
     data on Haiku 5.5 yet; widen its lane only on measured results.
   - **Sonnet** (`team-sonnet-worker`, `-high`): the default for orta
     implementation and bug fixing, tests against a contract, and web
     research. In the field Sonnet 5.5 had the lowest error density of every
     executor measured, and beat Sol 6.1 on both error density and time at
     both effort levels. Its known weak spot is design and direction work.
   - **Opus workers** (`team-opus-worker`, `-high`): work where judgment
     can't be fully specified up front, such as design or direction choices
     inside a task, multi-file changes with open decisions, or an ambiguous
     root cause. They also review Sonnet- and Haiku-written code (rule 9).
   - Numbers and caveats: `reference/evidence.md`. With measurement on,
     check `olcum rapor` before changing this rule.
6. **Fable is an escalation lane, and only where the seat includes it.** On a
   Premium seat Fable is part of the plan up to 50% of the weekly limits;
   past that it bills usage credits. On a Standard seat every Fable call
   bills usage credits, which is company money. So:
   - Use `team-fable-worker` only when the difficulty is the reasoning
     itself (a tricky algorithm or correctness argument, a subtle root cause
     that Sonnet and `team-opus-worker-high` have both missed), normally
     after `team-opus-worker-high` has tried. It is also the natural second
     reviewer on R3 (rule 9).
   - Not for bulk, exploration, routine code, or as a faster Opus.
   - On a Standard seat, an unknown seat, or once the Fable allowance is
     used up, dispatch Fable only with the user's explicit OK for that task.
7. **Brief quality gates every dispatch.** A worker starts with nothing but
   its brief and the project's startup files, and Haiku in particular does
   exactly what the brief says and fills no gaps. The manager re-reads every
   brief once before dispatching (also a draft returned by a worker). Every
   brief that changes files states:
   - the goal, and the files or folders it may touch (nothing else);
   - "do not commit" (the manager commits; the project's commit-attribution
     rule goes here too);
   - "only stop or kill processes you started yourself" (a parallel worker
     once killed the manager's test run as a "leftover process");
   - the test commands to run before reporting done;
   - to write progress and decisions to a named file as it goes (see "Worker
     cost hygiene" rule 2);
   - what the report must contain: status, files changed, test results,
     open questions.
8. **One seat, one budget: read the snapshot if it has numbers, otherwise
   use fixed caps.** Before dispatching an Opus or Fable worker, or a batch
   of workers, read `${CLAUDE_CONFIG_DIR:-~/.claude}/rate-limit-status.json`.
   - **It has numbers** (`five_hour.used_percentage` / `seven_day.used_percentage`
     are not null): at `five_hour >= 60` or `seven_day >= 70`, skip optional
     work (second opinions, extra reviews, Fable escalations) and give work
     that both Sonnet and Opus could do to Sonnet. At 85%+ on either window,
     wrap up the current unit and checkpoint rather than starting a large
     new one.
   - **It's missing or has nulls** (the normal case on a Team seat): there
     is no live signal. Keep the parallel cap ("Worker cost hygiene" rule 7),
     and before a batch of four or more workers or a long Opus/Fable run, tell
     the user in one line so they can glance at `/usage`. A rate-limit error
     is the real signal (see "Continuity").
   - Mandatory reviews (rule 9) are never skipped by this gate.
   - If any message says usage now bills to usage credits or extra usage,
     stop optional work and ask the user before continuing.
9. **Review: a different model, in an isolated context.** There is no other
   model family to review with, so independence comes from a different
   model, strict isolation, a break-the-rule check, and on R3 a second
   reviewer. The manager never counts its own reading as a review: it knows
   the author's reasoning.
   - **R2:** one isolated review. Sonnet or Haiku wrote it →
     `team-opus-worker-high`. Opus wrote it → `team-sonnet-worker-high`.
   - **R3:** two isolated reviews by two different models, plus human
     acceptance. Sonnet or Haiku wrote it → `team-opus-worker-high` and
     `team-fable-worker` (Premium) or else `team-sonnet-worker-high` in a fresh
     context. Opus wrote it → `team-sonnet-worker-high` and
     `team-fable-worker` (Premium) or else `team-opus-worker-high` in a fresh
     context. A fresh session of the author's model is the weakest choice;
     note it in the review file when it is used.
   - **R0/R1:** tests, CI and the break-it scenario are the safeguard; an AI
     review is optional. The manager may add an isolated review whenever it
     judges a change risky enough.
   - The protocol is in `reference/review.md`: break-it scenario before the
     code, break-the-rule check on R2/R3, contract + diff + test output only,
     at most two rounds, a review file with a fixed header written only by
     the reviewer and checked with `git status`, a narrow second look after
     any post-ACCEPT change, evidence for P0/P1, NEEDS-FACT for facts outside
     the repo, and every task ends done or explicitly incomplete.
10. **The manager picks every worker's effort level, per task.** Choose the
    lowest level that will do the job right; go up a level when a first
    attempt fails for lack of reasoning, not by default.
    - `team-haiku-worker` (medium): mechanical work, lookups, exploration.
    - `team-sonnet-worker` (medium): routine orta implementation, fixes,
      research.
    - `team-sonnet-worker-high`: harder Sonnet work (tricky debugging,
      contract-bound migrations) and R2 review of Opus-written code.
    - `team-opus-worker` (medium): detailed, judgment-heavy execution.
    - `team-opus-worker-high`: the hardest work and R2/R3 review of Sonnet-
      or Haiku-written code.
    - `team-fable-worker` (high): rule 6 only.
    - If a level is needed that has no preset, add a preset rather than an
      ad-hoc override. State preset + model + effort in one line when
      dispatching.

## Lanes at a glance

| Lane | Preset | Use for |
|---|---|---|
| Haiku | `team-haiku-worker` | Mechanical/bulk edits with a full spec, formatting, docs, read-only exploration, lookups, basit work. Cheapest |
| Sonnet | `team-sonnet-worker` / `-high` | Orta code and bug fixing (default), tests against a contract, web research; R2 reviewer of Opus-written code |
| Opus workers | `team-opus-worker` / `-high` | Work where judgment can't be specified up front; reviewer of Sonnet/Haiku-written code |
| Fable | `team-fable-worker` | Hard reasoning after Opus tried; second R3 reviewer. Premium seats only, otherwise with the user's OK (rule 6) |

## Routing flow

1. The manager classifies inline: **basit / orta / zor** (rule 1), and notes
   the risk tier.
2. **basit** → below the inline threshold, the manager does it. Otherwise
   `team-haiku-worker`.
3. **orta** → the manager writes a brief and dispatches code to
   `team-sonnet-worker` (`-high` if it is tricky); exploration and mechanical
   parts go to `team-haiku-worker`. Effort per rule 10.
4. **zor / mimari-hassas** → the manager handles the judgment part directly
   (brief, architecture, synthesis) and delegates the rest: Sonnet for
   well-specified execution, Haiku for exploration, `team-opus-worker(-high)`
   for detailed work whose judgment can't be fully specified, Fable only if
   the core difficulty is reasoning (rule 6). The manager always owns final
   integration on this tier.
5. Review and sign-off follow the risk tier (rule 9 and the tier table).

## Merging parallel work: gates

Branches that are green on their own can break once merged (migration
order, shared fixtures, a test selector matching a new label). The manager
owns merging and runs the gates; command names come from the project.

- **One writer per file set.** Each parallel executor works in its own
  worktree and task branch. "Same files" also covers shared modules, schema
  files, the migration sequence number, entry-point manifests and shared
  test fixtures/config: two tasks that both need one of them run in
  sequence, or the shared part is merged first as its own small task.
- **Cheap gate before every merge, on the merged candidate.** Merge current
  `main` into the branch first; a green result on an old base doesn't count.
  Run format, lint, typecheck, unit tests, the E2E files for what the branch
  touched, and migration tests when it touches the database. Briefs list the
  same gates, migration tests included.
- **Full gate** (all unit + migration + full E2E, every target browser): on
  accumulated `main` once a day (twice on busy days), recording the commit
  it ran on.
- **Full gate always, before the merge:** before a deploy (on the commit to
  be deployed); for R2/R3 work; for changes to shared test infrastructure,
  shared components, user-visible text or selectors, routing, or
  dependencies.
- **If the full gate breaks:** stop merging, bisect the merges since the
  last green gate, and nothing counts as done until `main` is green again.
  Rerun a failing test once to separate flaky from broken; note flaky tests.
- **Test habits that prevent merge breaks:** select by label with exact
  matching; tests that write shared state (rate-limit buckets, global
  settings, ports) clean it up afterwards; E2E runs pick free ports.
- With measurement on, record each full gate (`olcum add kapi ...`): merges
  covered, result, and breaks the cheap gate missed.

## Measurement (when the project uses `ajan-olcum`)

`ajan-olcum` is a separate skill and CLI (`olcum`) that records every
dispatch and compares models on error and time per difficulty point. This
policy doesn't require it; when the project regime turns it on:

- Record every dispatch: `olcum add` for `team-*` presets, `olcum run` for
  headless `claude -p` lanes. Give risk, size and uncertainty **at dispatch
  time**; they never change afterwards. A score given later favours whoever
  made the mistakes.
- After the review, record the outcome with `olcum bitir <run_id> ...`:
  P0/P1 counts by where they were caught, rounds, result. Leave unknowns
  blank; never invent a count.
- Before changing rule 5 or rule 10, run `olcum rapor` and use roles with
  n ≥ 5. When its picture contradicts this policy, raise it with the user
  rather than silently changing course. Haiku 5.5 and Fable have no rows
  yet; their first runs are the ones worth recording.
- The data stays in `~/.ajan-olcum/data`. Publishing a project's `olcum/`
  folder, committing or pushing it is the user's call; on company projects,
  ask before anything leaves the company repo.

## Worker cost hygiene

Every turn of a Claude session re-reads its whole history, and those reads
count against the seat's limits. Most of the cost of a long worker is the
history it keeps re-reading, not the text it writes. The field lessons
behind these rules: `reference/evidence.md`.

1. **One phase, one fresh worker.** Each new phase (design, implementation,
   fix round) starts a new worker with a short brief. Resuming a worker only
   continues the same phase after it was cut off.
2. **Compaction is a backstop, not the plan.** With rule 1, workers rarely
   grow enough to compact. Compaction turns old turns into a summary and can
   drop exact paths, test output or the reason for a decision, so:
   - On a 1M-context model, make it trigger around 200–300K tokens
     (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=20`–`30` for headless runs, or
     `autoCompactWindow` in a preset). On a smaller context window leave the
     default.
   - Every brief tells the worker to write progress and decisions to a file
     as it goes, so after a compaction it re-reads the file instead of
     guessing. The file is the source of truth, not the chat.
3. **No tools the task doesn't use.** Presets list their tools. Headless
   `claude -p` workers run with `--strict-mcp-config` and an explicit
   `--allowedTools` list.
4. **Context budget in every brief.** Find code with Grep and read only the
   relevant range, not whole large files, and nothing the task doesn't need.
5. **Screenshots: when needed, few and targeted.** Verify with text first
   where possible (tests, DOM or accessibility tree, error messages); when an
   image is needed, capture the relevant region and don't reopen it. Each
   image stays in the history and is re-read every turn. Final visual
   acceptance is the manager's.
6. **Lean startup files, nothing hidden.** What a project's `CLAUDE.md` /
   `AGENTS.md` imports is loaded into every worker. Import only the short
   rules every session needs; link decision archives, logs and long docs with
   a one-line "read this when…" note. If a fresh session's first turn is well
   above ~50K tokens, review the imports. Don't trim so hard that a worker
   loses a rule it needs.
7. **Parallel workers: up to 5, counted honestly.** Up to five may run at
   once when the work splits cleanly; mandatory reviewers count toward the
   five, so plan a batch with room for its reviews. With numbers in the
   snapshot, read it before each additional worker and start no more at
   `five_hour >= 60`. Without numbers, tell the user before a batch of four or
   more (rule 8). On a Pro seat six parallel workers took the 5h window from
   3% to 90% in 45 minutes; a Team seat's pool is a different size, but
   parallel workers drain it the same way.
8. **No command a worker can't finish in 10 minutes.** The Bash tool stops a
   foreground command at 10 minutes; the worker then polls the log and every
   poll re-reads its history. A worker spec names only the tests the change
   touches; the full E2E and the full gate are the manager's, run in the
   background (`run_in_background`) on the merged candidate. Field data: one
   Sonnet worker hit the limit 12 times on one task (181 active minutes, 188
   API calls), running the sharded full E2E itself.

## Continuity when limits run out

There is no second provider to fall back to, so the manager plans to stop
cleanly instead.

- **Checkpoint continuously.** At the end of each turn in which the state
  changed, write progress (done, left, key decisions, running workers) once
  to the project's handoff file (`docs/DEVIR.md` "▶ BURADAN DEVAM ET",
  `STATUS.md` or its own convention). Only a project with no handoff file
  gets `.orchestration-checkpoint.md`; never keep both, since two files drift
  apart and each write is a tool call.
- **A rate-limit error is the signal.** Read what it says:
  - A model-specific limit (the Fable allowance, a per-model weekly cap):
    move the work down one model if the task allows it (Fable → Opus,
    Opus → Sonnet; Haiku only for work rule 5 allows on Haiku) and note the
    substitution in the checkpoint. Never move work up to Fable because of a
    limit.
  - The seat's 5-hour or weekly limit: everything on the seat stops, workers
    included. Finish the checkpoint, tell the user what is done, what is
    left and when the window resets (if the message says), and end the turn.
- **Don't spill into paid usage silently.** If the org has extra usage or
  usage credits enabled, a hit limit may keep running on company money. Ask
  the user before continuing past that point.

## Exceptions

- If the user explicitly names a model for a scoped task, honor it for that
  task only, then return to this policy.
- The user can override any of this per session; absent that, this policy
  stands.
- If the user runs the manager itself on Fable (`/model fable`), the rules
  are the same, but the long manager session draws on the Fable allowance
  and `team-fable-worker` adds nothing (it is the same model). Opus is the
  recommended manager.
- Install only one orchestration skill per Claude config directory. If
  `opus-orchestration` is also loaded, this policy is the one for the Team
  account; tell the user both are installed.
