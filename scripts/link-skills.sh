#!/usr/bin/env bash
set -euo pipefail

# Links all skills in the repository to local Claude and Codex skill dirs.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTS=(
  "$HOME/.claude/skills"
  "${CODEX_HOME:-$HOME/.codex}/skills"
)

ensure_dest() {
  local dest="$1"

  # If the destination is a symlink into this repo, we'd end up writing the
  # per-skill symlinks back into the repo's own skills/ tree.
  if [ -L "$dest" ]; then
    local resolved
    resolved="$(readlink -f "$dest")"
    case "$resolved" in
      "$REPO"|"$REPO"/*)
        echo "error: $dest is a symlink into this repo ($resolved)." >&2
        echo "Remove it (rm \"$dest\") and re-run; the script will recreate it as a real dir." >&2
        exit 1
        ;;
    esac
  fi

  mkdir -p "$dest"
}

for dest in "${DESTS[@]}"; do
  ensure_dest "$dest"
done

find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/deprecated/*' -print0 |
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"

  for dest in "${DESTS[@]}"; do
    target="$dest/$name"

    if [ -e "$target" ] && [ ! -L "$target" ]; then
      rm -rf "$target"
    fi

    ln -sfn "$src" "$target"
    echo "linked $name -> $target"
  done
done
