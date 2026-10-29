---
name: opus-orchestration
description: "Delegation policy for a Claude Pro + ChatGPT Plus stack (no Fable/Max access) where the top-level Opus session acts as a manager — it talks to the user, dispatches workers, picks each worker's effort level, and integrates their reports — and is the only dispatcher. On the GPT side (via Codex CLI) Sol is the default executor for orta code and precision work, Luna takes research, exploration, bulk and low-risk work, and Astra is reserved for hard reasoning only. Sonnet is the Claude-side lane for work needing Claude-side tools, cross-family review of GPT code, and fallback when GPT fails; Opus workers take detailed judgment-heavy work and extra/high-stakes reviews; all Claude-side dispatch is gated by ${CLAUDE_CONFIG_DIR:-~/.claude}/rate-limit-status.json. Opus classifies tasks inline (no Haiku triage gate); Haiku is a fallback only. On first use in a project with no execution-regime section, it asks the user a one-time setup round (executor lane, risk tiers, measurement, commit attribution) and records the answers in AGENTS.md. Load whenever spawning sub-agents (Agent tool) or Codex CLI lanes, or planning any delegation."
---

# Orchestration & delegation policy (Claude Pro + ChatGPT Plus stack)

A routing policy for a stack with **one scarce top-tier model (Opus, capped by
Claude Pro's baseline quota)** and cheaper delegate tiers split across two
providers: Luna / Sol / Astra on the GPT side (Codex CLI, billed against the
ChatGPT Plus quota) carry most execution, with Sol as the default for code
and Luna for research and low-risk work; Sonnet on the Claude side covers
what needs Claude-side tools, review, and GPT fallback. Haiku is a fallback
lane only.

Core law: **Opus's quota is the tightest constraint in the whole stack, so it
must never do work that is cheaper to delegate.** Its turns buy judgment, not
throughput.

Reference files (in this skill's `reference/` folder), read when needed:

- `codex.md` — before the first `codex exec` of a session: model IDs,
  dispatch shape, timeouts, resume, sandbox limits, review calls, what every
  Codex spec must say.
- `review.md` — before the first review dispatch of a task: break-it
  scenario, break-the-rule check, rounds, severity, NEEDS-FACT verdict,
  review header, quota reserve.
- `project-setup.md` — when running "Project setup" below.
- `evidence.md` — when revising the routing, or when the user asks why: field
  data, benchmarks, the review study.

## Manager / worker model

The user talks only to the top-level Opus session. That session is the
**manager**, like a manager in a company with a team under it:

- It takes the request, splits it into tasks, picks a worker (lane + model +
  effort level) for each, writes the brief, and dispatches.
- Workers do the work and **report back when they finish**. Claude-side
  workers run in the background and the manager is notified on completion;
  `codex exec` lanes run as background Bash commands and notify on exit. The
  manager does not poll and does not redo a worker's job.
- The manager reads each report, decides the next step (accept, send back
  with a correction, escalate to review, ask the user), integrates the
  result, and tells the user in short status lines what is running, what
  finished, and what needs their decision.
- Independent tasks can run in parallel (read-only exploration freely; at
  most one worker editing the same files at a time; Claude-side workers
  capped per "Claude worker cost hygiene" rule 7).

## Project setup (once per project, before the first dispatch)

The defaults here fit a single Claude account. Projects differ, and the user
may not know (or may forget) which choices exist, so the manager asks
instead of assuming.

1. **Look for the project's regime.** Search the project's agent
   instructions (`AGENTS.md`, `CLAUDE.md` and what they import) for an
   execution-regime section (a heading such as "Execution regime",
   "Yürütme düzeni" or "Yürütme rejimi", or a working agreement that names
   executors and review rules). If one exists, follow it — it overrides this
   policy where they conflict (rule 5) — and skip the rest of this section.
2. **If there is none, ask before dispatching anything:** executor lane,
   risk tiers, measurement, commit attribution. Wording, defaults and the
   terms-risk note for a separate executor account: `reference/project-setup.md`.
3. **Write the answers** as a short section in the project's `AGENTS.md`
   (template in the same file) and show it to the user. Don't commit it
   unless they ask. From then on step 1 finds it and nobody is asked again.

**Default risk tiers.** Difficulty (basit / orta / zor) picks the executor;
risk picks the review and how much the human must sign off.

| Tier | What | Review |
|---|---|---|
| R0 | Mechanical, cheap to revert | Tests/CI |
| R1 | Routine CRUD, UI, docs | Tests/CI and a short break-it scenario (5–8 items, written before the code); AI review optional, any family |
| R2 | Multi-module business rules; migrations that only add (tables, columns, indexes) | Isolated review from the other family (same family only if the other is out of quota, noted in the review) |
| R3 | Auth/permissions, money, security, external-access tokens, untrusted files, migrations that delete or transform data, deploy | Isolated review from the other family, plus explicit human acceptance |

## The hard rules

1. **Opus classifies inline — no separate triage agent.** Opus labels each
   task **basit / orta / zor** as it reads it and routes per "Routing flow".
   A task so small that writing its spec would cost more than doing it (a
   one-line edit, a single file read to answer a question) Opus does inline.
2. **Opus orchestrates, never executes anything cheaper to delegate.**
   Architecture, task decomposition, spec-writing, synthesis of results,
   conflict resolution, final judgment calls — done by Opus, kept lean.
   Anything scoped and larger than the rule 1 threshold gets delegated, even
   if Opus "could" do it faster itself.
3. **Delegation is one level deep; Opus is the only dispatcher.** Only the
   top-level Opus session spawns agents or runs `codex exec`. Workers (all
   `*-worker` presets, including the Opus ones) never spawn agents and never
   call Codex CLI. If a worker's task needs GPT-side execution, the worker
   drafts the spec and returns it; Opus re-reads it and dispatches. This
   keeps every dispatch auditable and the quota check in one place.
4. **Dispatch through the named presets, not a raw model override.** Claude-
   side workers are `sonnet-worker`, `sonnet-worker-high`, `opus-worker`,
   `opus-worker-high` and (fallback only) `haiku-worker`, defined in
   `~/.claude/agents/`. Each preset fixes model and effort, so the choice of
   preset *is* the effort choice (rule 10). Don't use generic types
   (`general-purpose`, `Explore`, `Plan`, `claude`): with no model set they
   inherit Opus at the manager's effort. Don't use `fork` for review — it
   inherits the manager's whole conversation, so it isn't isolated (rule 9).
   If a preset is unavailable, give an explicit `model:` — never omit it. A
   project's separate executor account (`claude -p` with another
   `CLAUDE_CONFIG_DIR`) is the one exception, since a preset can't select an
   account.
5. **Sol executes orta code; Luna does research and low-risk work; Sonnet
   is the exception** — unless the project's execution regime ("Project
   setup") says otherwise; then that regime wins.
   - **Luna:** research, codebase exploration, bulk and mechanical edits,
     basit tasks, and small routine code with a complete spec (R0/R1). Not
     multi-module business logic, and nothing touching auth, money, data
     migration or security. Field data: worst error density on code by a
     wide margin, clean on research.
   - **Sol:** the default for orta implementation and bug fixing, and for
     every precise, contract-bound job. Effort per rule 10.
   - **Sonnet** (`sonnet-worker*`) takes a code task only when it needs
     Claude-side tools or context Codex can't reach (WebFetch on a site Codex
     can't use, files outside the Codex sandbox, a browser/GUI run), or when
     GPT-side dispatches are failing or out of quota (see "Continuity"). Its
     other job is cross-family review of GPT-written code (rule 9). This is
     a quota choice, not a quality one: in the field Sonnet 5.5 measured as
     good as or better than Sol 6.1 on code, but on a single Claude account
     every Sonnet worker draws from the manager's own 5h/7d windows. Where
     Claude quota isn't the constraint (a separate executor account), the
     project regime should make Sonnet the main executor.
   - **Quota balance:** work leans to the side with more quota left. Before
     sending anything to a Claude-side worker (Sonnet or Opus), read
     `${CLAUDE_CONFIG_DIR:-~/.claude}/rate-limit-status.json`: if
     `five_hour.used_percentage >= 60` OR `seven_day.used_percentage >= 70`,
     skip optional Claude-side work (second opinions, extra reviews) and send
     any orta code that was headed to Sonnet to Sol. A review that rule 9
     makes mandatory is not skipped by this gate. Thresholds are a starting
     point; tune them in practice.
   - Numbers and caveats: `reference/evidence.md`. With measurement on,
     check `olcum rapor` before changing this rule (see "Measurement").
6. **Astra is for hard reasoning only.** It burns Codex quota fastest. Use it
   only when the difficulty is the reasoning itself — tricky algorithm/math
   design, a subtle root cause Luna and Sol have both failed to find, a
   correctness argument — and only after Sol at `xhigh` has tried. Not for
   terminal-heavy, computer-use, bulk or long-context work.
7. **Spec quality gates every Codex CLI dispatch.** Sol and Luna execute a
   spec precisely but don't fill gaps. A vague spec costs a wasted retry and
   GPT quota. Whoever drafts it (Opus, or a worker returning a draft per
   rule 3), Opus re-reads it once before dispatching. What every Codex spec
   must state: `reference/codex.md`.
8. **GPT is a tool call, not a native agent.** Luna (`gpt-6-luna`), Sol
   (`gpt-6.1-sol`) and Astra (`gpt-6-astra`) run through Codex CLI as a Bash
   call, authenticated with the ChatGPT Plus login. Every call follows the
   dispatch shape in `reference/codex.md`: effort always set, stdin closed
   (`< /dev/null`), last message to a file, a 2-hour timeout in the
   background, `codex exec resume` for a cut-off run.
9. **Review family follows risk, not every change.** For R2 and R3, the
   reviewer comes from the **other family** than the executor: Claude wrote
   it → Sol reviews; GPT wrote it → `sonnet-worker-high` on R2,
   `opus-worker-high` on R3 (field data: Opus reviews confirmed more P0/P1
   than Sonnet, on different tasks, so directional). The manager never
   counts its own reading as the independent review: it knows the author's
   reasoning, so an Opus review is always a separate `opus-worker*`
   dispatch. The manager may add an extra isolated review whenever it judges
   a change risky enough. For R0/R1, tests, CI and the break-it scenario
   are the safeguard; an AI review is optional and any family will do. If a
   project defines its own tiers, follow them. The protocol is in
   `reference/review.md`:
   - A break-it scenario is written into the contract before the code (R1+);
     on R2/R3 the reviewer also breaks a critical rule and confirms a test
     fails.
   - Isolated context: contract, diff and test output only, never the
     author's conversation or rationale.
   - At most two review rounds per task; each review is a file with a fixed
     header, written only by the reviewer and checked with `git status`.
   - R2/R3: any change after ACCEPT, the manager's included, gets a narrow
     second look from the reviewer before acceptance is asked for.
   - P0/P1 need evidence (failing test, repro steps, or `file:line` + input →
     wrong output), otherwise they drop to P2. A missing second layer where
     another layer already prevents the failure is a P2 hardening note.
   - Third verdict NEEDS-FACT when the decisive fact is outside the repo
     (deployed config, identity policy): no severity, exact missing fact,
     goes to the human. Never a parking place for a speculation.
   - Reserve quota for the mandatory R2/R3 reviews before starting a batch
     of executors; a task ends either done or explicitly incomplete with its
     reason, never silently half-way.
   - If the other family is out of quota, a same-family isolated review may
     substitute on R2; note it in the review. On R3, wait or escalate to the
     human.
10. **The manager picks every worker's effort level, per task.** Choose the
    lowest level that will do the job right; raise it when a first attempt
    fails for lack of reasoning, not by default.
    - **Codex lanes:** `-c model_reasoning_effort=<level>` on every call
      (omitted means `high`). Mechanical/bulk/simple lookup → `low`; scoped
      implementation, bug fix, research → `medium`; contract-bound precise
      execution, migrations, tricky debugging, isolated review → `high`;
      Sol before Astra (rule 6) → `xhigh`; `max` only for a retry after
      `xhigh` failed. Astra → `high`, or `xhigh` if accepted.
    - **Claude-side:** pick the preset. `sonnet-worker` (medium) for routine
      work; `sonnet-worker-high` for harder Sonnet work and R2 cross-family
      review; `opus-worker` (medium) for detailed, judgment-heavy execution
      and extra reviews; `opus-worker-high` for the hardest work and R3
      reviews. `haiku-worker` has no effort knob. If a level is needed that
      has no preset, add a preset rather than a raw override.
    - State lane + model + effort in one line when dispatching.

## Lanes at a glance

| Lane | How | Use for |
|---|---|---|
| Luna | `codex exec --model gpt-6-luna` | Research (`web_search`), exploration, bulk/mechanical, basit, small R0/R1 code with a full spec. Cheapest by far |
| Sol | `codex exec --model gpt-6.1-sol` | Orta code and bug fixing (default), precise contract-bound work, migrations, tests against a contract; reviewer of Claude-written code |
| Astra | `codex exec --model gpt-6-astra` | Hard reasoning only (rule 6) |
| Sonnet | `sonnet-worker` / `sonnet-worker-high` (alias resolves to Sonnet 5.5) | Claude-side tools, review of GPT-written code, fallback when GPT fails; main executor only under a project regime with a separate account |
| Opus workers | `opus-worker` / `opus-worker-high` | Detailed work where judgment can't be specified up front; highest-stakes and extra isolated reviews. Same quota gate as Sonnet |
| Haiku | `haiku-worker` | Fallback only: basit Claude-side work when GPT is down. 200K context |

## Routing flow

1. Opus classifies inline: **basit / orta / zor** (rule 1), and notes the
   risk tier.
2. **basit** → below the inline threshold, Opus does it. Otherwise Luna
   (Haiku if GPT is failing).
3. **orta** → Opus writes a spec and dispatches code to Sol; research,
   exploration and mechanical parts go to Luna. Sonnet only for rule 5's
   exceptions, after reading the quota snapshot. Effort per rule 10.
4. **zor / mimari-hassas** → Opus handles the judgment part directly (spec,
   architecture, synthesis) and delegates the rest: Sol for precise
   execution, Luna for exploration, Astra only if the core difficulty is
   reasoning, `opus-worker(-high)` for detailed work where judgment can't be
   fully specified. Opus always owns final integration on this tier.
5. Review and sign-off follow the risk tier (rule 9 and the tier table).

## Merging parallel work: gates

Branches that are green on their own can break once merged (migration
order, shared fixtures, a test selector matching a new label). The manager
owns merging and runs the gates; command names come from the project.

- **One writer per file set.** Each executor works in its own worktree and
  task branch. "Same files" also covers shared modules, schema files, the
  migration sequence number, entry-point manifests and shared test
  fixtures/config: two tasks that both need one of them run in sequence, or
  the shared part is merged first as its own small task.
- **Cheap gate before every merge, on the merged candidate.** Merge current
  `main` into the branch first; a green result on an old base doesn't count.
  Run format, lint, typecheck, unit tests, the E2E files for what the branch
  touched, and migration tests when it touches the database. Executor specs
  list the same gates, migration tests included.
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
  covered, result, and breaks the cheap gate missed. That count tells
  whether the full gate can run less often or must run more.

## Measurement (when the project uses `ajan-olcum`)

`ajan-olcum` is a separate skill and CLI (`olcum`) that records every
dispatch and compares models on error and time per difficulty point. This
policy doesn't require it; when the project regime turns it on:

- Start every dispatch through `olcum run` (Codex and `claude -p` lanes are
  wrapped; for `*-worker` presets record with `olcum add`). Give risk, size
  and uncertainty **at dispatch time**; they never change afterwards. A
  score given later favours whoever made the mistakes.
- After the review, record the outcome with `olcum bitir <run_id> ...`:
  P0/P1 counts by where they were caught, rounds, result. Leave unknowns
  blank; never invent a count.
- Before changing rule 5 or rule 10, run `olcum rapor` and use roles with
  n ≥ 5. When its picture contradicts this policy, raise it with the user
  rather than silently changing course.
- The data stays in `~/.ajan-olcum/data`. Publishing a project's `olcum/`
  folder, committing or pushing it is the user's call.

## Claude worker cost hygiene

Every turn of a Claude session re-reads its whole history, and those reads
count against the 5h/7d windows. Most of the cost of a long worker is the
history it keeps re-reading, not the text it writes. These rules apply to
every Claude-side worker (`*-worker` presets, and `claude -p` lanes). The
field lessons behind them: `reference/evidence.md`.

1. **One phase, one fresh session.** Each new phase (design, implementation,
   fix round) starts a new worker with a short spec. `--resume` only
   continues the same phase after it was cut off.
2. **Compaction is a backstop, not the plan.** With rule 1, workers rarely
   grow enough to compact. Compaction turns old turns into a summary and can
   drop exact paths, test output or the reason for a decision, so:
   - On a 1M-context model, set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` so it
     triggers around 200–300K tokens (20–30). On a 200K-context model leave
     the default: the same percentage there would compact far too early.
   - Every spec tells the worker to write progress and decisions to a file
     as it goes (the task file or a notes file), so after a compaction it
     re-reads the file instead of guessing. The file is the source of truth,
     not the chat.
3. **No tools the task doesn't use.** Headless `claude -p` workers run with
   `--strict-mcp-config` (no MCP servers) and an explicit `--allowedTools`
   list.
4. **Context budget in every spec.** Find code with Grep and read only the
   relevant range (offset/limit), not whole large files, and nothing the task
   doesn't need.
5. **Screenshots: when needed, few and targeted.** A worker on visual work
   (layout, PDF output) may take and look at screenshots. Verify with text
   first where it can (tests, DOM or accessibility tree, error messages);
   when an image is needed, capture the relevant region and don't reopen it.
   Each image stays in the history and is re-read every turn. Final visual
   acceptance is the manager's (and Codex workers can't open a browser).
6. **Lean startup files, nothing hidden.** What a project's `CLAUDE.md` /
   `AGENTS.md` imports is loaded into every worker. Import only the short
   rules every session needs; link decision archives, logs and long docs with
   a one-line "read this when…" note. If a fresh session's first turn is well
   above ~50K tokens, review the imports. Don't trim so hard that a worker
   loses a rule it needs: consistency beats a few thousand tokens.
7. **Parallel Claude workers: up to 5, gated each time.** Up to five may run
   at once when the work splits cleanly. Read the quota snapshot before
   starting each additional one; at `five_hour.used_percentage >= 60` start
   no more and send the remaining work to Sol. Roughly 15 points of the 5h
   window per worker per 45 minutes, so 4–5 workers can spend 60–75% of the
   window in under an hour.

## Continuity under quota exhaustion

Claude Code gives the agent no tool for its own rate-limit usage, but the
`statusLine` hook receives `rate_limits.five_hour` / `seven_day.used_percentage`
(Pro/Max only) on every assistant message. `~/.claude/statusline.sh` writes
a snapshot to `${CLAUDE_CONFIG_DIR:-~/.claude}/rate-limit-status.json`
(`model`, `context_used_percentage`, `rate_limits.five_hour` /
`seven_day.used_percentage` and `resets_at`). Codex CLI has no equivalent,
so GPT-side quota is reactive only.

- **Check the snapshot before every Claude-side dispatch** (rule 5), as a
  fixed step of routing. A project with a separate executor account checks
  that account's own snapshot.
- **85%+ on either window is a harder signal:** wrap up the current unit of
  work and checkpoint rather than starting another large one. If the file is
  missing or stale, fall back to continuous checkpointing.
- **Checkpoint continuously regardless.** After each meaningful step, write
  progress (done, left, key decisions) to `.orchestration-checkpoint.md` in
  the project (or its own task-tracking convention).
- **A failed `codex exec` is GPT's real signal.** On a rate-limit or quota
  error, retry once on a different GPT tier if the task allows it (Luna
  instead of Sol only for work rule 5 allows on Luna; never escalate to
  Astra for quota reasons). If every GPT tier fails, fall back to Claude-side
  execution (Sonnet for orta, Haiku for basit) and note the substitution in
  the checkpoint.
- **Stop cleanly when both sides are exhausted** (Claude near its cap, GPT
  failing on every tier): finish the checkpoint, say what's done and what's
  left, and end the turn.

## Exceptions

- If the user explicitly names a model for a scoped task, honor it for that
  task only, then return to this policy.
- The user can override any of this per session; absent that, this policy
  stands.

## Future: Max/Fable migration

If Claude Max is purchased later, Fable becomes the orchestrator and Opus
moves down to be a primary executor (absorbing most of what Sol does now,
since Opus's quota expands under Max while GPT stays on Plus). That is a new
version of this policy, not a patch to this file.
