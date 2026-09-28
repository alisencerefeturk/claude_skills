---
name: opus-orchestration
description: "Delegation policy for a Claude Pro + ChatGPT Plus stack (no Fable/Max access) where the top-level Opus session acts as a manager — it talks to the user, dispatches workers, picks each worker's effort level, and integrates their reports — and is the only dispatcher. On the GPT side (via Codex CLI) Luna is the default executor for basit and orta work (bulk, research, scoped implementation), Sol does precision execution, and Astra is reserved for hard reasoning only. Sonnet is the Claude-side lane for work needing Claude-side tools, second-opinion review, and fallback when GPT fails; Opus workers take detailed judgment-heavy work and extra/high-stakes reviews; all Claude-side dispatch is gated by ~/.claude/rate-limit-status.json. Opus classifies tasks inline (no Haiku triage gate); Haiku is a fallback only. Load whenever spawning sub-agents (Agent tool) or Codex CLI lanes, or planning any delegation."
---

# Orchestration & delegation policy (Claude Pro + ChatGPT Plus stack)

A routing policy for a stack with **one scarce top-tier model (Opus, capped by
Claude Pro's baseline quota)** and cheaper delegate tiers split across two
providers: Luna / Sol / Astra on the GPT side (reached through Codex CLI,
billed against the ChatGPT Plus quota) carry most execution, with Luna as the
default; Sonnet on the Claude side covers what needs Claude-side tools,
review, and GPT fallback. Haiku is kept only as a fallback lane (see
"Choosing the delegate").

This policy assumes **no Claude Max and no Fable access**. If that changes,
see "Future: Max/Fable migration" at the bottom before continuing to use this
policy as-is.

Core law: **Opus's quota is the tightest constraint in the whole stack, so it
must never do work that is cheaper to delegate.** Its turns buy judgment, not
throughput.

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
  most one worker editing the same files at a time).

## The hard rules

1. **Opus classifies inline — no separate triage agent.** Every task already
   arrives at Opus first, so spawning another model just to classify it costs
   more than classifying it. Opus labels each task **basit / orta / zor** as
   it reads it and routes per "Routing flow". One exception to delegation:
   a task so small that writing its spec would cost more than doing it (a
   one-line edit, a single file read to answer a question) Opus does inline.
2. **Opus orchestrates, never executes anything cheaper to delegate.**
   Architecture, task decomposition, spec-writing, synthesis of results,
   conflict resolution, final judgment calls — done by Opus, kept lean.
   Anything scoped and larger than the rule 1 inline threshold gets
   delegated, even if Opus "could" do it faster itself.
3. **Delegation is one level deep; Opus is the only dispatcher.** Only the
   top-level Opus session spawns agents or runs `codex exec`. Workers
   (all `*-worker` presets, including the Opus ones) never spawn agents and
   never call Codex CLI.
   If a worker's task needs GPT-side execution, the worker drafts the spec and
   returns it; Opus re-reads it and dispatches. This keeps every dispatch
   auditable, and keeps the quota check (rule 5) in the one place that reads
   `~/.claude/rate-limit-status.json`.
4. **Dispatch through the named presets, not a raw model override.** Claude-
   side workers are `sonnet-worker`, `sonnet-worker-high`, `opus-worker`,
   `opus-worker-high` and (fallback only) `haiku-worker`, defined in
   `~/.claude/agents/`. Each preset fixes both model and effort, so the
   choice of preset *is* the effort choice (rule 10), and a dispatch can
   never silently inherit the manager's model and effort. Don't use generic
   types (`general-purpose`, `Explore`, `Plan`, `claude`): with no model
   set they inherit Opus at the manager's effort, unplanned. Don't use
   `fork` for review — a fork inherits the manager's whole conversation, so
   it isn't isolated (rule 9); use it only when a task genuinely needs that
   full context, knowing it runs on Opus at the manager's effort. If a
   preset is unavailable, fall back to an explicit `model:` field — never
   omit it.
5. **Luna is the default for orta work; Sonnet is the exception.** Claude
   Pro quota is the scarcer side of the stack, and Sonnet load is what drives
   the Claude 5h/7d windows up fastest. Orta tasks go to Luna unless one of
   these applies, in which case Sonnet takes it:
   - the task needs Claude-side tools or context Luna can't reach (e.g.
     WebFetch on a site Codex can't use, files outside the Codex sandbox);
   - a second-opinion review of a Luna result is worth the Claude quota
     (high-stakes change, Luna's output looks off);
   - GPT-side dispatches are failing (see "Continuity").
   Before sending anything to a Claude-side worker (Sonnet or Opus), read
   `~/.claude/rate-limit-status.json`: if `five_hour.used_percentage >= 60`
   OR `seven_day.used_percentage >= 70`, skip optional Claude-side work
   (second-opinion and extra reviews) and keep Claude-side workers only for
   work that genuinely can't run on Luna. Thresholds are a starting
   point — tune them in practice.
   - **Basis:** a 2026-09-23 head-to-head on three orta tasks (bug fix with a
     second unreported bug, loose-brief feature, cross-file code questions),
     identical prompts, graded by hidden tests / answer key. Luna 6/6, 5/7
     (lost 2 only on an under-specified output format), 12/12 within the
     length limit; Sonnet 4/6 (missed the unreported bug), 6/7 (crashed on
     invalid input), 12/12 but over the length limit. Similar token use.
     One run per task on a small repo — directional, not conclusive; revisit
     if Luna underperforms on real work. This test used **Sonnet 5**; Sonnet
     5.5 (2026-09-28) has not been re-tested against Luna.
6. **Astra is for hard reasoning only.** Astra burns Codex quota fastest
   (API price 5× Sol, 100× Luna). Use it only when the task's difficulty is
   the reasoning itself — tricky algorithm/math design, a subtle root cause
   Luna and Sol have both failed to find, a correctness argument. Not for
   terminal-heavy, computer-use, bulk, or long-context work: published
   numbers show Opus 5.5 ahead of Astra on Terminal-Bench 4.0 and OSWorld
   2.0, and every GPT tier already has a ~1M context.
7. **Spec quality gates every Codex CLI dispatch.** Sol and Luna execute a
   spec precisely but don't fill gaps well. A vague spec costs a wasted retry
   (and wasted GPT quota). Whoever drafts the spec (Opus, or Sonnet returning
   a draft per rule 3), Opus re-reads it once before dispatching.
8. **GPT is a tool call, not a native agent.** Sol/Luna/Astra are invoked
   through Codex CLI as a Bash tool call, authenticated against the ChatGPT
   Plus login. Real model IDs (confirmed via `codex` → `/model`):

   - Luna: `codex exec --model gpt-6-luna "<spec>"`
   - Sol: `codex exec --model gpt-6-sol "<spec>"`
   - Astra: `codex exec --model gpt-6-astra "<spec>"` (rule 6 only)

   `gpt-6-luna` / `gpt-6-sol` replaced `gpt-5.6-luna` / `gpt-5.6-sol`. The
   old Terra tier has no gpt-6 successor and is retired from this policy; if
   a gpt-6-terra ships, revisit the policy rather than silently adding it.

   Every dispatch uses this shape:

   ```
   codex exec --model <id> -c model_reasoning_effort=<level> \
     --skip-git-repo-check -s workspace-write \
     -o <scratch>/<task>-last-message.txt "<spec>" \
     < /dev/null > <scratch>/<task>.log 2>&1
   ```

   - `-c model_reasoning_effort=<level>`: always set it (rule 10).
   - `--skip-git-repo-check`: `codex exec` refuses outside a trusted git repo
     without it.
   - `< /dev/null` is mandatory, especially for background runs. `codex exec`
     checks stdin even when the prompt is an argument; left open, it blocks
     forever on "Reading additional input from stdin..." with no error. This
     already cost one 18+ minute stall.
   - `-o` + log redirect: read only the last-message file (and the files the
     spec asked for) into Opus's context, not the full transcript.
   - For web research add `-c web_search='"live"'`.
9. **Review family follows risk, not every change.** For high-risk work
   (auth/permissions, money, security, data-destroying migrations, deploy,
   external access), the reviewer must come from the **other family** than
   the executor: Claude wrote it → Sol reviews; GPT wrote it →
   `sonnet-worker-high` reviews, or `opus-worker-high` for the
   highest-stakes calls. The manager never reviews its own integration as
   "the independent review": it knows the author's reasoning, so it isn't
   isolated — an Opus review is always a separate `opus-worker*` dispatch.
   The manager may add an extra isolated `opus-worker` review on top of the
   required one whenever it judges the change risky enough. For routine work, tests, CI
   and a break-it verification scenario are the primary safeguard. An AI
   review is optional there, isolated, and from any family, so the cheapest
   suitable reviewer is fine. If a project defines its own risk tiers,
   follow them.
   - Every reviewer gets an isolated context: the task contract, the diff
     and the test output, never the author's conversation or rationale.
   - P0/P1 findings need evidence: a failing test, repro steps, or a
     concrete `file:line` + input → wrong output. Otherwise they are
     downgraded, which keeps false-positive churn down.
   - If the other family is unavailable (quota), a same-family isolated
     review may substitute on medium-risk work; note it in the review. On
     high-risk work, wait or escalate to the human.
   - **Basis (2026-09-23):** The most direct data is Greptile's "Model
     Inversion" study (Jul 2026, 1,000 PRs). A cross-family reviewer had
     higher recall on high-severity bugs in both directions: GPT on
     Claude-authored PRs 60.0% vs Opus 53.7%, and Opus on Codex-authored PRs
     62.0% vs GPT 50.5%. It is vendor data and not independently
     replicated. Self-preference papers are older and text-focused. No study
     compares a fresh-context same-model reviewer against a cross-family
     one. Most review products (Anthropic, OpenAI, Cursor, CodeRabbit) use
     their own models and rely on verification filtering instead. Since
     most execution now runs on GPT, mandatory cross-family review on
     routine work would spend scarce Claude quota for unproven gain.

10. **The manager picks every worker's effort level, per task.** Effort is
    part of the routing decision, not a fixed default. Choose the lowest
    level that will do the job right; raise it when a first attempt fails
    for lack of reasoning, not by default.
    - **Codex lanes:** add `-c model_reasoning_effort=<level>` to every
      `codex exec` call (the config default is `high`, so an omitted flag
      means high). Guide: mechanical/bulk/simple lookup → `low`; scoped
      implementation, bug fix, research → `medium`; contract-bound precise
      execution, migrations, tricky debugging, isolated review → `high`;
      Astra's hard reasoning → `high`, or `xhigh` if the model accepts it
      (fall back to `high` if Codex rejects the value).
    - **Claude-side:** pick the preset. `sonnet-worker` (medium) for routine
      Claude-side work; `sonnet-worker-high` for harder Sonnet work and
      medium-risk cross-family review; `opus-worker` (medium) for detailed,
      judgment-heavy execution and extra reviews; `opus-worker-high` for the
      hardest work and high-risk reviews. `haiku-worker` has no effort knob
      and stays fallback-only. If a level is needed that has no preset
      (e.g. low or xhigh), add a preset rather than using a raw override.
    - State lane + model + effort in one line when dispatching, so the user
      and the checkpoint can see the choice.

## Choosing the delegate

- **Luna** (Codex CLI) — default lane for basit and orta work: bulk,
  research, codebase exploration, scoped implementation and bug fixing,
  including work over large inputs (API USD 0.10 / 0.50 per 1M tokens — by far
  the cheapest tier). See rule 5.
- **Sonnet** (`sonnet-worker` / `sonnet-worker-high`) — Claude-side lane per
  rule 5's exceptions: work needing Claude-side tools, cross-family review
  of GPT output (rule 9), optional second opinions, and orta fallback when
  GPT is failing. Quota-gated by the snapshot file. The presets use the
  `sonnet` alias, which resolves to **Sonnet 5.5** (`claude-sonnet-5-5`,
  released 2026-09-28; verified 2026-09-29).
  - **Sonnet 5.5 executor trial (2026-09-29):** Sonnet 5.5 is a large jump
    over Sonnet 5 (Terminal-Bench 4.0 70.6% vs 10.3%, above Opus 5.5's
    66.4%), but on the only coding benchmark with a Sol number (FrontierCode
    1.1) Sol leads: 49.3% / 52.1% Xhigh vs Sonnet 5.5's 46.2%. All vendor
    data. So Sol is not replaced wholesale. Instead, the next medium-risk
    implementation task runs on `sonnet-worker-high`, with Sol as the
    cross-family reviewer (rule 9). Compare review P0/P1 count, bugs caught
    by E2E/the manager, fix rounds and wall time against Sol's recent tasks.
    If Sonnet 5.5 does better, revise rule 5 and the Sol entry below; until
    then high-risk implementation stays on Sol.
- **Opus workers** (`opus-worker` / `opus-worker-high`) — detailed work that
  needs judgment inside the execution (where a spec can't pin every
  decision), highest-stakes isolated reviews, and extra reviews the manager
  judges worthwhile. Allowed by the owner's decision (2026-09-26): Opus 5.5
  tends to finish a job with fewer tokens, which offsets its higher
  per-token price (API 4/20 vs Sonnet 2/10), so on judgment-heavy work it
  can cost the same or less. Same quota gate as Sonnet; Luna stays the
  default for plain basit/orta work.
- **Sol** (Codex CLI) — precision execution once a complete spec exists:
  hard implementation, migrations, test-writing against a defined contract.
- **Astra** (Codex CLI) — hard reasoning only, per rule 6.
- **Haiku** (`haiku-worker`) — fallback only: basit Claude-side work when
  GPT-side dispatches are failing (quota/outage). Note its 200K context
  limit.

## Routing flow

1. Opus classifies inline: **basit / orta / zor** (rule 1).
2. **basit** → below the inline threshold, Opus does it. Otherwise Luna
   (Haiku if GPT is failing).
3. **orta** → Opus writes a brief/spec and dispatches to Luna (Sol if the
   work needs precise, contract-bound execution). Sonnet only for rule 5's
   exceptions, after reading `~/.claude/rate-limit-status.json`. Pick the
   effort level per rule 10.
4. **zor / mimari-hassas** → Opus handles the judgment part directly (spec,
   architecture, synthesis) and delegates the mechanical portions: Sol for
   precise execution, Luna for exploration, Astra only if the core
   difficulty is reasoning, `opus-worker(-high)` for detailed work where
   judgment can't be fully specified up front. The review follows rule 9: for high-risk work,
   the reviewer comes from the other family. Opus always owns final
   integration on this tier.

## Continuity under quota exhaustion

Claude Code doesn't give the agent a tool to check its own rate-limit usage,
but the `statusLine` hook receives `rate_limits.five_hour.used_percentage`
and `rate_limits.seven_day.used_percentage` (Pro/Max only) on every
assistant message. `~/.claude/statusline.sh` is configured as the global
`statusLine` command and writes a snapshot to
`~/.claude/rate-limit-status.json` (`model`, `context_used_percentage`,
`rate_limits.five_hour` / `seven_day.used_percentage` and `resets_at`). Read
that file directly to get current Claude-side quota usage.

Codex CLI has no equivalent: only per-thread token counts, no account-wide
quota, and `/status` is interactive-only. GPT-side quota stays reactive-only.

- **Check the snapshot file before every Claude-side dispatch** (rule 5), as a
  fixed step of routing, not "at milestones".
- **Treat 85%+ on either window as a harder signal** — wrap up the current
  unit of work and checkpoint rather than starting another large one. If the
  file is missing or stale, fall back to continuous checkpointing.
- **Checkpoint continuously regardless.** After each meaningful step, write
  progress (done, left, key decisions) to `.orchestration-checkpoint.md` in
  the project (or its own task-tracking convention).
- **Treat a failed `codex exec` call as GPT's real signal.** On a rate-limit
  or quota error: retry once on a different GPT tier if the task allows it
  (e.g. luna instead of sol — never escalate to Astra for quota reasons). If
  every GPT tier is failing, fall back to Claude-side execution (Sonnet for
  orta, Haiku for basit) and note the substitution in the checkpoint.
- **Stop cleanly when both sides are confirmed exhausted** (Claude near its
  cap per the snapshot or user, and GPT failing on every tier): finish the
  checkpoint, state what's done and what's left, and end the turn.

## Benchmark basis (2026-09-23, Sonnet 5.5 added 2026-09-29)

Published numbers this routing is based on (vendor sources, differing effort
levels — treat as directional):

| Model | Notable published results | Context | API $/1M in/out |
|---|---|---|---|
| Opus 5.5 | Terminal-Bench 4.0 66.4%, OSWorld 2.0 81.8% partial, HLE (tools) 67.7%, FrontierCode 1.1 54.4%, CursorBench 4.0 57.8% | 1M | 4 / 20 |
| Sonnet 5.5 | Terminal-Bench 4.0 70.6%, FrontierCode 1.1 46.2% (Max), CursorBench 4.0 55.5%, OSWorld 2.1 80.1% partial, HLE (tools) 64.5%; vendor claims 30%+ faster output than Sonnet 5 and up to 30% lower cost per task; Vals AI (independent) #2 of 66, 69.22% | 1M (128K out) | 2 / 10 |
| Sonnet 5 | Terminal-Bench 4.0 10.3%, FrontierCode 1.1 42.4%, CursorBench 4.0 34.1% (from the Sonnet 5.5 launch page) | 1M | 2 / 10 |
| Haiku 4.5 | SWE-bench Verified 73.3% | 200K | 1 / 5 |
| gpt-6-sol | FrontierCode 1.1 49.3% / 52.1% Xhigh (reported on Anthropic's Sonnet 5.5 page); no OpenAI-published coding numbers | 1.05M | 2 / 10 |
| gpt-6-luna | none published yet | 1.05M | 0.10 / 0.50 |
| gpt-6-astra | GPQA 96.0%, ARC-AGI-2 95.0%, BrowseComp 91.5%, Terminal-Bench 4.0 57.9%, OSWorld 2.0 72.6% partial | 1.05M | 10 / 50 |

Neither vendor publishes per-model subscription quota multipliers, so API
price is only a rough proxy for quota burn. Re-check when Sol/Luna benchmarks
appear.

## Exceptions

- If the user explicitly names a model for a scoped task, honor it for that
  task only, then return to this policy.
- The user can override any of this per session; absent that, this policy
  stands.

## Future: Max/Fable migration

If Claude Max is purchased later, Fable becomes the orchestrator and Opus
moves down to be a primary executor (absorbing most of what Sol currently
does, since Opus's quota expands under Max while GPT stays on Plus). Rule 1
(triage gate) and rule 6 (spec quality) carry over unchanged; rule 2 shifts
from Opus to Fable; Opus's role in "Choosing the delegate" changes from
orchestrator to "hard/precise execution, given a spec." This is a separate
policy revision, not a patch to this file — write a new version rather than
editing this one in place when that happens.
