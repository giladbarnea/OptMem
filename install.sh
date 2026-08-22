#!/bin/sh
# OptMem (fork) installer: per-project memory scoping via a PATH wrapper.
#
# Layout, unlike upstream's ~/.optmem:
#   ~/.local/share/optmem/memo            -> symlink into this repo
#   ~/.local/share/optmem/agents-block.md -> symlink into this repo
#   ~/.local/bin/memo                     -> wrapper; sets MEMORY_DIR to
#                                            <git-root>/.optmem/memory
# Re-running is idempotent. Updating = git pull in this repo.
set -e

dir="$(cd "$(dirname "$0")" && pwd)"
share="${HOME}/.local/share/optmem"
bin_dir="${HOME}/.local/bin"

mkdir -p "$share" "$bin_dir"
ln -sf "$dir/memo" "$share/memo"
ln -sf "$dir/agents-block.md" "$share/agents-block.md"

cat > "$bin_dir/memo" << 'EOF'
#!/bin/sh
# OptMem launcher: scopes the memory store to the enclosing git project.
root="$(git rev-parse --show-toplevel 2>/dev/null)" || root="$PWD"
export MEMORY_DIR="$root/.optmem/memory"

if [ "$1" = "init" ]; then
  python3 "$HOME/.local/share/optmem/memo" init || exit $?
  block="$HOME/.local/share/optmem/agents-block.md"
  agents="$root/AGENTS.md"
  if [ ! -f "$agents" ]; then
    echo "No AGENTS.md at $root. To opt a project in, create one and paste $block."
  elif grep -qs 'Your memory is OptMem' "$agents"; then
    echo "AGENTS.md already has the Memory section; nothing appended."
  else
    printf '\n\n---\n\n' >> "$agents"
    cat "$block" >> "$agents"
    echo "Appended the Memory section to $agents."
  fi
  exit 0
fi

exec python3 "$HOME/.local/share/optmem/memo" "$@"
EOF
chmod +x "$bin_dir/memo"

case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *) printf 'NOTE: %s is not on PATH; add it to use bare `memo`.\n' "$bin_dir" >&2 ;;
esac

echo "Installed: $bin_dir/memo (wrapper) -> $share/memo -> $dir"
echo "Each git project gets its own store at <repo>/.optmem/memory."
echo "Opt a project in with: cd <project> && memo init"
