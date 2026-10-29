# Review protocol (single model family)

Read this before the first review dispatch of a task. `SKILL.md` rule 9 says
who reviews; this file says how. Parts are adapted from Cloudflare's
MIT-licensed `security-audit` skill
(github.com/cloudflare/security-audit-skill), scaled down from a full audit
to a per-task review.

## 0. Why the rules are stricter than in opus-orchestration

On the personal stack the R2/R3 reviewer comes from the other model family,
and a cross-family reviewer has measurably higher recall on high-severity
bugs (`evidence.md`). A Team seat has only Claude models, so that check is
gone. No study compares a fresh-context same-family reviewer against a
cross-family one; until there is data, the gap is covered by:

- **a different model than the author** (Opus reviews Sonnet's code, Sonnet
  reviews Opus's), so the reviewer doesn't share the author's exact habits;
- **strict isolation**: the reviewer never sees the author's reasoning;
- **the break-the-rule check** (§2), which tests the tests instead of trusting
  a reading;
- **a second reviewer on R3** (§3). Cloudflare reports that one run of its
  audit found about half of what repeated runs found in total, so one review
  is not exhaustive.

## 1. Break-it scenario (R1 and up, written before the code)

The manager writes a short verification scenario into the task contract
**before** any code exists (5–8 items for R1; more for R2/R3). It doesn't stop
at the happy path. It tries what applies of:

- invalid input and boundary values;
- empty or missing fields;
- duplicate records;
- unauthorized access (no session, wrong role);
- special characters and locale quirks (Turkish İ/ı/ş/ğ, Unicode, long text);
- violation of the business rule the task exists to enforce.

The executor may not change or weaken the scenario. If it needs a change, it
returns to the manager.

## 2. Break-the-rule check (R2/R3, done by the reviewer)

The reviewer temporarily breaks a critical business rule, confirms a test
fails, then reverts. It records tried / broke in the review file. A rule
whose break no test notices is a test gap and a finding. (Field data: 274 of
297 checks broke a test.)

## 3. Who reviews, isolation, rounds, record

| Risk | Author | Reviewer(s) |
|---|---|---|
| R2 | Sonnet or Haiku | `team-opus-worker-high` |
| R2 | Opus | `team-sonnet-worker-high` |
| R2 | Fable | `team-opus-worker-high` |
| R3 | Sonnet or Haiku | `team-opus-worker-high` + `team-fable-worker` (Premium) or `team-sonnet-worker-high` |
| R3 | Opus | `team-sonnet-worker-high` + `team-fable-worker` (Premium) or `team-opus-worker-high` |
| R3 | Fable | `team-opus-worker-high` + `team-sonnet-worker-high` |

- On R3 the two reviewers run independently: neither sees the other's file
  until both are filed. A reviewer of the author's own model (the last
  fallback above) is noted in its header as `same-model`.
- **Isolated:** each reviewer gets only the task contract, the diff and the
  test output path, never the author's conversation or rationale. Dispatch
  through a preset, never `fork`.
- **At most two rounds per task**, contract and code together. A separate
  contract review happens only on R3 and is one round. If the disagreement
  continues, it goes to the human with a short decision note.
- **Kept on file:** each review is written to
  `reviews/<task>-<reviewer>-review.md` (`<reviewer>` = `opus`, `sonnet` or
  `fable`). The reviewer writes only that file. After the call the manager
  runs `git status` and checks that nothing else changed; otherwise it
  reverts the change and treats the review as invalid.
- **After ACCEPT, any change goes back:** on R2/R3, if anything changes after
  ACCEPT (by anyone, the manager included), the reviewer takes a narrow
  second look at that diff before acceptance is asked for. The manager never
  calls its own post-ACCEPT fix "reviewed".

## 4. Severity

| Level | Meaning | Examples |
|---|---|---|
| P0 | A real boundary or data failure with concrete damage | data loss, authorization bypass, security-control bypass, wrong money calculation |
| P1 | Wrong behavior a user or operator will hit | rule not enforced, wrong result on valid input, test green only against a fake |
| P2 | Improvement | test gap, hardening, naming, style |
| P3 | Nit | |

- P0/P1 need evidence: a failing test, repro steps, or a concrete
  `file:line` + input → wrong output. Without it the finding drops to P2.
- If another layer already prevents the attack or failure, the missing second
  layer is a hardening note (P2), not a defect.
- Only evidenced findings get a severity. "I couldn't verify it" is not P1
  (see §5).

## 5. Third verdict: NEEDS-FACT

Besides ACCEPT and REVISE, a reviewer may return NEEDS-FACT when the decisive
fact is **not in the repository or the local test run**: a deployed proxy
setting, an identity-provider policy, a production config, an external
service's behavior.

- It names the exact missing fact, who can observe it (the user, or someone
  at the company with access), and a safe check (a local fixture or a lookup
  on their side).
- It carries **no severity** and is not a low-confidence P1.
- It is not a parking place: if the repository or a local test refutes the
  suspicion, the finding is dropped; if it is answerable locally, the
  reviewer answers it.
- Open NEEDS-FACT items go to the human with the R3 acceptance list.

## 6. Review header (fixed format)

The first lines of every review file:

```
Task: <id>   Round: <1|2>   Author: <model>   Reviewer: <model, effort>[, same-model]
Decision: ACCEPT | REVISE | NEEDS-FACT
Findings: P0=<n> P1=<n> P2=<n> NEEDS-FACT=<n>
Break-the-rule: tried=<n> broke=<n>
Looked at: <files and checks reviewed>
Not looked at: <what was out of reach, or "none">
```

"Looked at / Not looked at" keeps an ACCEPT honest: it says what was
reviewed, so "no problem found" is never mistaken for "everything checked".
A malformed review (missing header, prose-wrapped result) is not repaired by
the manager; the reviewer is re-run fresh. The counts are what
`olcum bitir` needs when measurement is on (copied by the manager; the tool
does not parse the header).

## 7. Plan the batch around its reviews

The seat has one pool and usually no live gauge (`SKILL.md` rule 8). Before
starting parallel executors, the manager counts the mandatory reviews they
will need (one reviewer per R2 task, two per R3 task, two rounds at most)
and keeps the batch small enough that those reviews still fit in the
parallel cap and the window. A change that can't be reviewed isn't done.

## 8. Finish or say "incomplete"

A task ends in one of two states: done (merged candidate passes the gates and
required reviews are filed), or explicitly **incomplete**: a short note in the
checkpoint says what is missing and why (limit reached, blocked fact,
waiting on a human). It never stalls silently half-way, and an incomplete
task never counts as accepted.

## 9. Security-sensitive R3 (optional)

For R3 work on auth, permissions, tenant isolation or other security
boundaries, a reviewer may use Cloudflare's `security-audit` skill in
guidance mode (focused attack classes, no full audit run). Install it only
if the user wants it (on a company machine, check the company's rules on
third-party tooling first):
`npx skills add https://github.com/cloudflare/security-audit-skill --skill security-audit`.
