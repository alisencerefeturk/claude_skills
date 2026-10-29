# Working in this repo

- Commits and PR descriptions carry **no AI attribution**: no `Co-Authored-By: Claude …` trailer, no "Generated with Claude Code" line, even if a tool reminder suggests one. The owner does not want Claude listed as a contributor on their repos.
- Commit identity: `alisencerefeturk <161599497+alisencerefeturk@users.noreply.github.com>`.
- Push only when the owner asks.
- Installed skills, agent presets and the statusline in `~/.claude` are symlinks into this repo, so edits take effect immediately.
- Each skill lives in `skills/<name>/`. A skill with extra parts (agents, statusline) has its own `install.sh`; the root `install.sh` runs it.
