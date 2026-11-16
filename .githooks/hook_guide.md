# Git Hooks — Quick Guide

## Setup (once per clone)

`git config core.hooksPath .githooks`

`chmod +x .githooks/pre-commit`

That's it — git now runs hooks from `.githooks/` instead of `.git/hooks/`. Any hook added there by teammates is picked up automatically on the next `git pull`, no reinstall needed.

## Using an existing hook

Nothing to do — once `core.hooksPath` is set, hooks in `.githooks/` just run on the matching git action (`pre-commit`, `pre-push`, etc).

## Creating a new hook

1. Create a file named exactly after the git hook event (no extension): `.githooks/pre-commit`, `.githooks/pre-push`, `.githooks/commit-msg`, etc.
2. Exit code matters: `exit 0` = allow, non-zero = block the action.
3. Make it executable:
   chmod +x .githooks/<hook-name>
4. Commit and push — everyone gets it on next `pull`.

## Reference — supported hook names

pre-commit, commit-msg, pre-push, post-merge, pre-rebase, prepare-commit-msg (full list: `.sample` files in `.git/hooks/`).

## Gotchas

- `chmod +x` is required — a non-executable hook is silently skipped.
- `git diff --cached --name-only --diff-filter=ACM` excludes renames — use `ACMR` if the hook must catch renamed files too.
- Only files under `core.hooksPath` are used — a hook dropped in `.git/hooks/` while `core.hooksPath` is set is ignored.