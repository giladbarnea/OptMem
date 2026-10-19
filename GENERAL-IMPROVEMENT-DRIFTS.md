# General improvement drift

## Configurable environment metadata (#em01)

added:: 2026-10-19
code:: `memo`, `test_environment_metadata.py`
what:: A per-store `ENV_METADATA` mapping prepends selected environment values as inline tags to new notes without changing `memo note` arguments.
why:: Runtime identity should come from the process running the tool, not an agent copying an identifier into every note. Missing required values fail before the note is written. Size errors expose the metadata overhead and available text budget. Historical imports and summaries remain unchanged.
upstream:: VictorTaelin/OptMem `1fb164cf39028047781f72ac3bb1e5a691c1dcb0` checked on 2026-10-19; no equivalent setting or automatic metadata exists.
retirement:: Adopt an upstream implementation when it preserves automatic per-call metadata, fail-before-write behavior, and unchanged historical sources.
downstream:: Avidor's production launcher configures `PI_SESSION_ID` as `sid`; see `~/dev/avidor-optmem/FORK.md`.
