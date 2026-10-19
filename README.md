# OptMem

Permanent memory for AI agents. A 426-token prompt, a script, plug and play.

![how OptMem works](anim/optmem.gif)

## Fork notes (giladbarnea)

This is Gilad's per-project fork. Its purpose, responsibility boundaries, installation, and behavior are in [FORK.md](FORK.md). The upstream quickstart follows below.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/VictorTaelin/OptMem/main/install.sh | sh
```

It prints a `## Memory` block. Paste that at the top of your agent's
`AGENTS.md` (or `CLAUDE.md`), and you are done. Run the same line again to
update.

The tool lands at `~/.optmem/memo`; put `~/.optmem` on `PATH` to type `memo`.

## Commands

| | |
|---|---|
| `memo wake` | read the memory — the first command of every session |
| `memo note "..."` | record one memory: one line, up to 280 bytes |
| `memo nap` | answer the merges that came due |
| `memo recall <regex>` | search every memory ever recorded, word for word |
| `memo zoom <lo>-<hi>` | open a tree node into its two halves |
| `memo forget <lo>-<hi>` | drop a bad summary; the next nap rebuilds it |

Merges arrive one at a time, in the output of `note`. Nothing ever runs in the
background.

## Files

```
~/.optmem/
  memo          the tool: one file of Python 3, no dependencies
  memory/
    LOG.txt     every memory, one per line, append-only, never edited
    TREE/       the summaries: a cache, rebuildable from the log alone
    config      the sizes, written by `memo config`
```

```sh
memo config                  # show the sizes
memo config WAKE_LINES=300   # how many lines wake prints (96 ≈ 8k tokens)
memo config WAKE_LINES=      # back to the default
```

`WAKE_LINES` is the only size worth touching, and it is a reading budget, not
a storage budget: change it whenever, in either direction, and nothing is
recomputed.

Records are fixed width, so position *is* identity and every lookup is one
seek. At a million memories (608 MB), `wake` takes 0.03s.

Set `$MEMORY_DIR` to keep `memory/` elsewhere — a synced folder, a git repo.

## Automatic environment metadata

Configure a store to copy selected environment values into new notes:

```sh
memo config 'ENV_METADATA={"PI_SESSION_ID":"sid"}'
memo note "A useful fact."
# Stored: #0 YYYY-MM-DD sid:<current-session-id> A useful fact.
```

The mapping is opt-in and defaults to `{}`. It is not specific to Pi. Every configured variable must be present and nonempty when `note` runs. Values must be single tokens. Invalid configuration or missing values fail before appending a note.

Tags are ordinary inline text immediately after the date. They count toward `ENTRY_CHARS` and can be searched with `recall`. A too-long note reports the automatic metadata bytes and the remaining note-text budget. The host must supply the current environment for each command; setting a shared server's process environment per session is not safe.

`import` preserves its prepared historical text and does not stamp the importing process's metadata. `nap` also leaves the supplied summary unchanged. Clear the mapping with `memo config ENV_METADATA=`.

Tests: `uv run -p python3 test.py` and `uv run -p python3 test_environment_metadata.py`.

## The prompt

This is what the installer prints, and the whole of the integration.

```markdown
## Memory

Your memory is OptMem:
- The tool is `~/.optmem/memo`
- Your memories are in `~/.optmem/memory`

OptMem outlives every session, compaction, model and vendor change.
Without it you do not know who you are, or what was decided and tried.

### At startup: activating OptMem (mandatory)

Run `~/.optmem/memo wake` before any other tool call, in every session, and
then do exactly what it prints, to the end of its output.

### While working: register memories (mandatory)

Call `~/.optmem/memo note "<1 line, max 280 bytes>"` whenever you learn
something new, or something worth keeping happens. That covers a task
worth real effort, a fact or insight the user teaches you, anything you
learn about their life (even indirectly), any event of lasting effect.

Do not register redundant memories.

If `~/.optmem/memo note` asks a compression: do it before your next action.

Never edit or delete anything under `~/.optmem/memory`: the tool manages it.

### When you need an old memory: search, or navigate

`~/.optmem/memo recall <regex>` searches every memory, word for word.

Your memories also form a binary tree: #0-1, #2-3 ... exist as one-line
summaries, pairs of those as #0-3, and so on -- every `#a-b` line wake
prints is one node of it. `~/.optmem/memo zoom <a-b>` opens a node into its
two halves, down to the raw memories.

### If you're a subagent: skip everything above

Parallel sessions on this machine are all you, and may all write memories.
A subagent is not: it must never run `memo`, because it cannot judge what
is already known, and its notes would arrive duplicated and incorrectly.
When you spawn one, write: `You are a subagent. Don't run memo.`
```
