# Fork: per-project OptMem

## Purpose and justification

This fork adapts OptMem to Gilad's project-based agent work. Each project needs its own durable memory, shared by all its Git worktrees, with optional automatic commits and explicit project opt-in.

The fork keeps that installation and agent-policy integration separate from upstream's global installation. It also carries reusable improvements and bug fixes that can be contributed upstream.

## Place in the chain

1. **Parent:** [VictorTaelin/OptMem](https://github.com/VictorTaelin/OptMem). Its [README](https://github.com/VictorTaelin/OptMem/blob/main/README.md) describes upstream's memory tool and installation.
2. **This fork:** [giladbarnea/OptMem](https://github.com/giladbarnea/OptMem), at `~/dev/optmem`.

There are no known child forks. Projects that use the installed `memo` wrapper are consumers, not child forks. Their memory contents and project rules remain their own.

## Responsibility boundary

This fork owns the per-project launcher, worktree sharing, optional Git commits, project opt-in, and the shared agent-prompt template in [agents-block.md](agents-block.md).

The memory engine and storage behavior remain general-purpose. Reusable improvements and bug fixes belong here rather than in copies maintained separately by each consumer. Prefer upstream implementations when they provide equivalent or better behavior.

Client-specific facts, metadata conventions, and memory policies belong in the consuming project. They do not belong in the shared library or prompt template.

## Change triage

Follow the [shared fork guide](/Users/giladbarnea/.agents/skills/open-source-contribution-attitude/references/fork.md) for category definitions, placement, retirement, and contribution protocols.

The per-project launcher and agent-policy integration are intentional product drift. Configurable per-memory record width is a general improvement. Non-mutating CLI help is a bug fix. Do not treat all differences as permanent merely because this fork currently carries them.

## Fork installation and behavior

Install this fork with `./install.sh`. Update it by pulling this checkout. The installation instructions in the root README describe upstream's distribution.

- `./install.sh` (this fork) writes a wrapper to `~/.local/bin/memo` that runs
  this repo's `memo` directly. The wrapper sets `MEMORY_DIR` to
  `<main checkout>/.optmem/memory`, so every git project gets one store, shared
  by all its worktrees.
- `git config optmem.commit true` in a repo makes the wrapper commit
  `.optmem/memory` in the main checkout after every `note`, `nap`, `forget`,
  `import` and `config`.
- The record width is per memory. An empty memory takes it from `ENTRY_CHARS`
  (`memo config ENTRY_CHARS=560` before the first note), and its first record
  fixes it. To widen a memory that has records, replay it into a new one.
- `memo init` also appends the agent prompt (`agents-block.md`) to the repo's
  `AGENTS.md`, idempotently.
- No global prompt injection: only projects whose AGENTS.md carries the block
  use the memory.
- `.githooks/pre-commit` (enabled via `git config core.hooksPath .githooks`)
  prints a yellow warning when origin is behind upstream; it never blocks.
