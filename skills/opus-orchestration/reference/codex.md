# Codex CLI lanes: commands and pitfalls

Read this before the first `codex exec` of a session. The rules live in
`SKILL.md` (rules 7, 8, 10); this file is the how.

## Model IDs

Confirmed via `codex` → `/model`:

| Lane | ID | Notes |
|---|---|---|
| Luna | `gpt-6-luna` | No 6.1 version shipped. |
| Sol | `gpt-6.1-sol` | Released 2026-09-29, replaces `gpt-6-sol`. Accepts `low` through `xhigh` and `max`. |
| Astra | `gpt-6-astra` | Rule 6 only. No 6.1 version shipped. |

- `gpt-6.1-sol` needs codex-cli 0.159.0 or newer. On 0.158.0 it failed with
  "not supported when using Codex with a ChatGPT account". When a new model
  ID fails with that error, first update Codex (`npm i -g @openai/codex`) and
  check `~/.codex/models_cache.json`.
- `gpt-6-luna` / `gpt-6-sol` replaced `gpt-5.6-luna` / `gpt-5.6-sol`. The
  old Terra tier has no gpt-6 successor and is retired; if a gpt-6-terra
  ships, revisit the policy rather than silently adding it.

## Dispatch shape

```
codex exec --model <id> -c model_reasoning_effort=<level> \
  --skip-git-repo-check -s workspace-write \
  -o <scratch>/<task>-last-message.txt "<spec>" \
  < /dev/null > <scratch>/<task>.log 2>&1
```

- `-c model_reasoning_effort=<level>`: always set it (rule 10). The config
  default is `high`, so an omitted flag means high.
- `--skip-git-repo-check`: `codex exec` refuses outside a trusted git repo
  without it.
- `< /dev/null` is mandatory, especially in the background. `codex exec`
  checks stdin even when the prompt is an argument; left open, it blocks
  forever on "Reading additional input from stdin..." with no error (one
  18+ minute stall).
- `-o` + log redirect: read only the last-message file (and the files the
  spec asked for) into the manager's context, not the full transcript.
- Web research: add `-c web_search='"live"'`. Research runs outside the
  repo and changes no repo files; the manager moves the result in after
  reading it.
- Background runs: give the Bash call `timeout: 7200000` (2 hours, the
  maximum). The default (30 minutes) kills implementation and fix runs
  before they finish; this happened twice in one project.
- A cut-off run is resumed, not restarted: take the `session id` from the
  top of the log and run `codex exec resume <id>`.

## Review calls

- Tell the reviewer to write only its own review file
  (e.g. `reviews/<task>-codex-review.md`) and change nothing else.
- If the reviewer must run the project's local test gates (Docker,
  database, E2E), allow network in the sandbox:
  `-c sandbox_workspace_write.network_access=true`. This grants no right to
  push, deploy or write to outside systems.
- After the call, `git status`: only the review file may have changed. If
  anything else changed, revert it and treat the review as invalid.

## Sandbox limits

- The Codex sandbox cannot write to `.git`. The manager reviews Codex's
  changes and commits them.
- It cannot launch a browser (Chromium fails with
  `MachPortRendezvousServer Permission denied`) or other GUI processes
  (Electron smoke tests, `codesign` timestamping, `lsregister`,
  notarization). Its E2E "verification" is not independent: the manager runs
  browser and GUI checks outside the sandbox.

## Every Codex spec says

Sol and Luna execute a spec literally and don't fill gaps (rule 7). Besides
the task itself, every spec states:

- the files or folders it may touch, and that it must not change others;
- "do not commit" (the manager commits; the project's commit-attribution
  rule goes in here too);
- "only stop or kill processes started from your own worktree path" (a
  parallel executor once killed the manager's test run as a "leftover
  process");
- the test commands to run before reporting done;
- what the last message must contain (status, files changed, test results,
  open questions).
