# Evidence behind the routing

Read this when revising the routing, or when the user asks why a rule is the
way it is. The field numbers come from the personal stack
(`opus-orchestration/reference/evidence.md` has the full tables, GPT lanes
included). If `ajan-olcum` is installed, `olcum rapor` gives current
figures; prefer them over this file.

## Field data, Claude rows (one project, 2026-09-28 → 2026-10-19)

Source: a procurement web app (Next.js, PostgreSQL). Error points are
weighted by where a bug was caught (review 1, manager/E2E 2, after
acceptance 3; P0 doubles), then divided by a difficulty score (risk × size ×
uncertainty) given at dispatch. Lower is better. n ≥ 5 is "enough"; fewer is
directional only.

### Executors

| Model | Effort | n | Error density | Minutes per difficulty point | First pass clean |
|---|---|---|---|---|---|
| Sonnet 5.5 | medium | 33 | 0.13 | 6.4 | 25% |
| Sonnet 5.5 | high | 46 | 0.26 | 14.3 | 38% |
| Opus 5.5 | high | 9 | 0.20 | 10.8 | 33% |
| Sol 6.1 (for comparison) | high | 34 | 0.37 | 29.5 | 8% |

- Sonnet 5.5 had the lowest error density of every executor measured
  (GPT lanes included) and beat Sol 6.1 on time at both effort levels,
  which is why it is the default executor here. On the personal stack Sol stayed the default
  only because every Sonnet worker drew from the manager's own Pro quota; on
  a single Team seat that reason is gone.
- Sonnet's known weak spot is design and direction work (field note,
  2026-10-02). That is where Opus workers come in.
- Caveats: Sonnet's code was reviewed by Sol (another family), so
  first-pass-clean rates aren't directly comparable with a same-family
  review. Opus has few runs. One project, one codebase. Haiku 5.5 and Fable
  have no field data at all.

### Reviewers

| Model | Effort | n | Confirmed P0/P1 | False alarms | Missed | Break-it checks: broke / tried |
|---|---|---|---|---|---|---|
| Opus 5.5 | high | 16 | 14 | 0 | 1 | 131 / 144 |
| Sonnet 5.5 | high | 14 | 6 | 0 | 0 | 81 / 87 |

Opus reviews confirmed more P0/P1 than Sonnet's, on different tasks, so this
is directional. It is why Opus reviews Sonnet's code, and why the weaker
direction (Sonnet reviewing Opus) gets a second reviewer on R3.

## Cross-family vs same-family review

Greptile's "Model Inversion" study (Jul 2026, 1,000 PRs): a cross-family
reviewer had higher recall on high-severity bugs in both directions. GPT on
Claude-authored PRs 60.0% vs Opus 53.7%; Opus on Codex-authored PRs 62.0% vs
GPT 50.5%. Vendor data, not independently replicated. No study compares a
fresh-context same-family reviewer (or a different model of the same
family) against a cross-family one. Cloudflare reports one run of its
security audit found about half of what repeated runs found in total. So on
a single-family seat the policy uses a different model, strict isolation,
break-the-rule checks, and two reviewers on R3, and measurement should
tell whether that is enough.

## Team seat facts (checked 2026-10-29)

- **Fable on Team** (Anthropic support article "Claude Fable 5 on your
  plan", 2026-09-02): on Premium seats Fable 5 and 5.1 are a standard part
  of the plan, and up to 50% of the weekly usage limits can go to Fable at no
  extra cost; past that, usage credits or another model. On Standard seats
  Fable isn't included in the plan's limits and runs on usage credits from
  the start. Fable 5.1 needs Claude Code 2.1.255 or later.
- **No live quota signal** (Claude Code statusline docs): `rate_limits`
  "appears only for claude.ai Pro and Max subscribers, or behind a Claude
  apps gateway that sets a spend limit". A Team seat isn't listed, so the
  snapshot normally has no numbers. If it ever does, rule 8's gate applies
  as written.
- **Default model:** `default` resolves to Opus 5.5 on Team (Claude Code
  model config docs), so the manager is Opus unless the user picks
  otherwise. Subagent `model:` accepts `sonnet`, `opus`, `haiku`, `fable`, a
  full model ID, or `inherit`; generic built-in agents run on the main
  conversation's model, which is why rule 4 requires the presets.

## Cost lessons (personal stack, same project)

- Appending an implementation phase to a design session with `--resume`:
  138 steps each re-read a ~350K-token history (~48M cached tokens); the 5h
  window filled in an hour.
- A 1M-context worker grew to 340K tokens uncompacted and used 25% of the
  5h window in four minutes.
- Each worker started at ~93K tokens of imported project files, most of it
  one 56 KB decisions file. The fix was importing a short summary instead
  and linking the full file.
- Six parallel Claude subagents took the 5h window from 3% to 90% in 45
  minutes (about 15 points per worker).
- Branches green on their own broke when merged (migration order, shared
  fixtures, a test selector matching a new menu label). A cheap gate on the
  merged candidate before each merge, and a full gate daily and for every
  high-risk or shared-infrastructure change, caught them.

## Published benchmarks (Claude rows, 2026-09-23)

Vendor sources, differing effort levels — directional only.

| Model | Notable published results | Context | API $/1M in/out |
|---|---|---|---|
| Opus 5.5 | Terminal-Bench 4.0 66.4%, OSWorld 2.0 81.8% partial, HLE (tools) 67.7%, FrontierCode 1.1 54.4%, CursorBench 4.0 57.8% | 1M | 4 / 20 |
| Sonnet 5.5 | Terminal-Bench 4.0 70.6%, FrontierCode 1.1 46.2% (Max), CursorBench 4.0 55.5%, OSWorld 2.1 80.1% partial, HLE (tools) 64.5%; Vals AI (independent) #2 of 66, 69.22% | 1M (128K out) | 2 / 10 |

No Haiku 5.5 or Fable figures are recorded here yet. Anthropic doesn't
publish per-model subscription quota multipliers, so API price is only a
rough proxy for how fast a model drains the seat.
