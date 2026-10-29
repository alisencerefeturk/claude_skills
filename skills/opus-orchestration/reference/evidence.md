# Evidence behind the routing

Read this when revising the routing, or when the user asks why a rule is the
way it is. The numbers below are a snapshot. If `ajan-olcum` is installed,
`olcum rapor` gives the current figures; prefer them over this file.

## Field data (one project, 2026-09-28 → 2026-10-19; `olcum rapor`, 2026-10-28)

Source: a procurement web app (Next.js, PostgreSQL), 152 execution and 73
review records. Error points are weighted by where a bug was caught (review
1, manager/E2E 2, after acceptance 3; P0 doubles), then divided by a
difficulty score (risk × size × uncertainty) given at dispatch. Lower is
better. "Yeterli" means n ≥ 5; fewer is directional only.

### Executors

| Model | Effort | n | Error density | Minutes per difficulty point | First pass clean |
|---|---|---|---|---|---|
| Sonnet 5.5 | medium | 33 | 0.13 | 6.4 | 25% |
| Sonnet 5.5 | high | 46 | 0.26 | 14.3 | 38% |
| Opus 5.5 | high | 9 | 0.20 | 10.8 | 33% |
| Sol 6.1 | high | 34 | 0.37 | 29.5 | 8% |
| Sol 6.1 | medium | 6 | 0.64 | 6.7 | 0% |
| Luna | medium | 7 | 0.89 | 12.5 | 20% |
| Luna | high | 5 | 0.72 | 4.4 | 0% |

Reading it:

- **Luna** is clearly worst on code. Its tasks were mostly small, low-risk
  ones, and its bugs were the quiet kind found later: tests green only
  against a fake repository, validations passing for the wrong reason. It
  was clean on research and spikes. Its code data is only from before
  2026-10-07.
- **Sonnet 5.5 measured better than Sol 6.1** on both error density and
  time, at both effort levels. Its known weak spot is design/direction work
  (field note, 2026-10-02). Rule 5 still makes Sol the default on a single
  Claude account. That is a quota decision, not a quality one: every Sonnet
  worker draws from the manager's own 5h/7d windows. Where Claude quota is
  not the constraint (a separate executor account, or a Max plan), the data
  favours Sonnet.
- **Caveats.** Each family was reviewed by the other (Sonnet's code by Sol,
  Sol's by Claude), so first-pass-clean rates are not comparable across
  families. Most Sonnet runs were in a separate Claude account; most Sol
  runs were R3 work. One project, one codebase.

### Reviewers

| Model | Effort | n | Confirmed P0/P1 | False alarms | Missed | Break-it checks: broke / tried |
|---|---|---|---|---|---|---|
| Sol 6.1 | high | 40 | 27 | 0 | 0 | 62 / 66 |
| Opus 5.5 (`opus-worker-high`) | high | 16 | 14 | 0 | 1 | 131 / 144 |
| Sonnet 5.5 (`sonnet-worker-high`) | high | 14 | 6 | 0 | 0 | 81 / 87 |

A break-it check means the reviewer breaks a business rule on purpose and
confirms a test fails, then reverts. About nine in ten did, so most tests
were real.

### Cost lessons (same project)

- Appending an implementation phase to a design session with `--resume`:
  138 steps each re-read a ~350K-token history (~48M cached tokens); the 5h
  window filled in an hour.
- A 1M-context worker grew to 340K tokens uncompacted and used 25% of the
  5h window in four minutes.
- Each worker started at ~93K tokens of imported project files, most of it
  one 56 KB decisions file. The fix was importing a short summary instead
  and linking the full file.
- Six parallel Claude subagents on the manager's account took the 5h window
  from 3% to 90% in 45 minutes (about 15 points per worker).
- Branches green on their own broke when merged (migration order, shared
  fixtures, a test selector matching a new menu label). A cheap gate on the
  merged candidate before each merge, and a full gate daily and for every
  high-risk or shared-infrastructure change, caught them.

## Earlier executor test (2026-09-23, superseded)

Three orta tasks (bug fix with a second unreported bug, loose-brief feature,
cross-file code questions), identical prompts, hidden tests / answer key.
Luna 6/6, 5/7, 12/12; Sonnet **5** 4/6, 6/7, 12/12 but over the length
limit. One run per task on a small repo. This made Luna the default; the
field data above replaced it.

## Cross-family review (2026-09-23)

The most direct data is Greptile's "Model Inversion" study (Jul 2026, 1,000
PRs): a cross-family reviewer had higher recall on high-severity bugs in
both directions. GPT on Claude-authored PRs 60.0% vs Opus 53.7%; Opus on
Codex-authored PRs 62.0% vs GPT 50.5%. Vendor data, not independently
replicated. Self-preference papers are older and text-focused. No study
compares a fresh-context same-model reviewer against a cross-family one.
Most review products (Anthropic, OpenAI, Cursor, CodeRabbit) use their own
models and rely on verification filtering. So cross-family review is
required only where risk justifies the quota (R2/R3), not on every change.

## Opus workers (owner's decision, 2026-09-26)

Opus 5.5 tends to finish a job with fewer tokens, which offsets its higher
per-token price (API 4/20 vs Sonnet 2/10), so on judgment-heavy work it can
cost the same or less. Hence `opus-worker*` for work where judgment can't be
fully specified up front.

## Astra vs Sol 6.1

Astra's API price is 5× Sol and 100× Luna. Published numbers show Opus 5.5
ahead of Astra on Terminal-Bench 4.0 and OSWorld 2.0, and every GPT tier has
a ~1M context, so Astra is not for terminal-heavy, computer-use, bulk or
long-context work. OpenAI reports Sol 6.1 matching Astra on DeepSWE v1.1 and
within 2.1 points of it on OSWorld 2.0 at one-fifth the price; Astra still
leads on scientific work (Terminal-Bench Science 68.1%). Hence: Sol `xhigh`
before Astra, Astra for hard math, science and correctness reasoning.

## Published benchmarks (2026-09-23; Sonnet 5.5 and Sol 6.1 added 2026-09-29)

Vendor sources, differing effort levels — directional only.

| Model | Notable published results | Context | API $/1M in/out |
|---|---|---|---|
| Opus 5.5 | Terminal-Bench 4.0 66.4%, OSWorld 2.0 81.8% partial, HLE (tools) 67.7%, FrontierCode 1.1 54.4%, CursorBench 4.0 57.8% | 1M | 4 / 20 |
| Sonnet 5.5 | Terminal-Bench 4.0 70.6%, FrontierCode 1.1 46.2% (Max), CursorBench 4.0 55.5%, OSWorld 2.1 80.1% partial, HLE (tools) 64.5%; Vals AI (independent) #2 of 66, 69.22% | 1M (128K out) | 2 / 10 |
| Sonnet 5 | Terminal-Bench 4.0 10.3%, FrontierCode 1.1 42.4%, CursorBench 4.0 34.1% | 1M | 2 / 10 |
| Haiku 4.5 | SWE-bench Verified 73.3% | 200K | 1 / 5 |
| gpt-6.1-sol | OpenAI launch, relative figures only: DeepSWE v1.1 matches Astra, +6.4 over gpt-6-sol; AutomationBench +2.2 vs Opus 5.5 at ~1/3 cost; OSWorld 2.0 within 2.1 of Astra; factual errors 11.4% → 7.7%. No independent results yet | 1.05M (128K out) | 2 / 10 |
| gpt-6-sol | FrontierCode 1.1 49.3% / 52.1% Xhigh (reported on Anthropic's Sonnet 5.5 page) | 1.05M | 2 / 10 |
| gpt-6-luna | none published | 1.05M | 0.10 / 0.50 |
| gpt-6-astra | GPQA 96.0%, ARC-AGI-2 95.0%, BrowseComp 91.5%, Terminal-Bench 4.0 57.9%, OSWorld 2.0 72.6% partial | 1.05M | 10 / 50 |

Neither vendor publishes per-model subscription quota multipliers, so API
price is only a rough proxy for quota burn.
