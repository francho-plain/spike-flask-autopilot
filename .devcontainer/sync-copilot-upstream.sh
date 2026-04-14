#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_URL="${COPILOT_UPSTREAM_URL:-https://github.com/francho-plain/francho-copilot.git}"
UPSTREAM_REF="${COPILOT_UPSTREAM_REF:-main}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CLONE_DIR="$HOME/.copilot-upstream/francho-copilot"
COPILOT_DIR="$HOME/.copilot"
PREFIX="common-"

# Clone once; pull on subsequent container rebuilds
if [[ -d "$CLONE_DIR/.git" ]]; then
  echo "[copilot-sync] Pulling upstream: $UPSTREAM_URL ($UPSTREAM_REF)"
  git -C "$CLONE_DIR" fetch --depth 1 origin "$UPSTREAM_REF"
  git -C "$CLONE_DIR" reset --hard FETCH_HEAD
else
  echo "[copilot-sync] Cloning upstream: $UPSTREAM_URL ($UPSTREAM_REF)"
  mkdir -p "$(dirname "$CLONE_DIR")"
  git clone --depth 1 --branch "$UPSTREAM_REF" "$UPSTREAM_URL" "$CLONE_DIR"
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# Sync each component from the upstream clone directly into ~/.copilot/.
# instructions go under .github/instructions/ so COPILOT_CUSTOM_INSTRUCTIONS_DIRS=~/.copilot
# lets the Copilot CLI discover them as .github/instructions/**/*.instructions.md.
components=(agents skills instructions prompts)

for component in "${components[@]}"; do
  src="$CLONE_DIR/$component"
  stage="$TMP_DIR/stage/$component"

  case "$component" in
    instructions) dest="$COPILOT_DIR/.github/instructions" ;;
    *)            dest="$COPILOT_DIR/$component" ;;
  esac

  mkdir -p "$dest"
  rm -rf "$stage"
  mkdir -p "$stage"

  if [[ -d "$src" ]]; then
    echo "[copilot-sync] Mirroring $component/ -> $dest"

    if [[ "$component" == "skills" ]]; then
      shopt -s nullglob
      for skill_dir in "$src"/*; do
        [[ -d "$skill_dir" ]] || continue
        skill_name="$(basename "$skill_dir")"
        staged_skill_dir="$stage/${PREFIX}${skill_name}"
        rsync -a "$skill_dir/" "$staged_skill_dir/"

        skill_file="$staged_skill_dir/SKILL.md"
        if [[ -f "$skill_file" ]]; then
          sed -i "s/^name:[[:space:]]*\"\{0,1\}${skill_name}\"\{0,1\}[[:space:]]*$/name: ${PREFIX}${skill_name}/" "$skill_file"
        fi
      done
      shopt -u nullglob
    else
      shopt -s nullglob
      for file_path in "$src"/*; do
        [[ -f "$file_path" ]] || continue
        file_name="$(basename "$file_path")"
        cp "$file_path" "$stage/${PREFIX}${file_name}"
      done
      shopt -u nullglob
    fi
  else
    echo "[copilot-sync] Upstream component missing, clearing managed entries for $component/"
  fi

  find "$dest" -maxdepth 1 -mindepth 1 -name "${PREFIX}*" -exec rm -rf {} +
  rsync -a "$stage/" "$dest/"
done

# --- Legacy cleanup ---

# Remove common-* files previously synced into the project .github/
for component in agents skills instructions prompts; do
  project_dest="$REPO_ROOT/.github/$component"
  if [[ -d "$project_dest" ]]; then
    find "$project_dest" -maxdepth 1 -mindepth 1 -name "${PREFIX}*" -exec rm -rf {} +
  fi
done

# Remove the old intermediate sync target (~/.copilot-upstream/…/.github/)
if [[ -d "$CLONE_DIR/.github" ]]; then
  echo "[copilot-sync] Removing legacy intermediate target: $CLONE_DIR/.github"
  rm -rf "$CLONE_DIR/.github"
fi

if [[ -e "$REPO_ROOT/.copilot/upstream/francho-copilot" ]]; then
  echo "[copilot-sync] Removing legacy unmanaged mirror: $REPO_ROOT/.copilot/upstream/francho-copilot"
  rm -rf "$REPO_ROOT/.copilot/upstream/francho-copilot"
fi

echo "[copilot-sync] Done. Upstream assets synced to: $COPILOT_DIR"
echo "[copilot-sync] Managed assets use prefix: ${PREFIX}"
