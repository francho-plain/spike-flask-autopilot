#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_URL="${COPILOT_UPSTREAM_URL:-https://github.com/francho-plain/francho-copilot.git}"
UPSTREAM_REF="${COPILOT_UPSTREAM_REF:-main}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CLONE_DIR="$HOME/.copilot-upstream/francho-copilot"
GITHUB_ROOT="$CLONE_DIR/.github"
PROJECT_GITHUB_ROOT="$REPO_ROOT/.github"
LEGACY_TARGET_ROOT="$REPO_ROOT/.copilot/upstream/francho-copilot"
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

mkdir -p "$GITHUB_ROOT"

components=(agents skills instructions prompts)

for component in "${components[@]}"; do
  src="$CLONE_DIR/$component"
  dest="$GITHUB_ROOT/$component"
  stage="$TMP_DIR/stage/$component"
  project_dest="$PROJECT_GITHUB_ROOT/$component"

  mkdir -p "$dest"
  rm -rf "$stage"
  mkdir -p "$stage"

  if [[ -d "$src" ]]; then
    echo "[copilot-sync] Mirroring $component/"

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

  # Remove any common-* files that were previously synced into the project .github/
  if [[ -d "$project_dest" ]]; then
    find "$project_dest" -maxdepth 1 -mindepth 1 -name "${PREFIX}*" -exec rm -rf {} +
  fi
done

if [[ -e "$LEGACY_TARGET_ROOT" ]]; then
  echo "[copilot-sync] Removing legacy unmanaged mirror: $LEGACY_TARGET_ROOT"
  rm -rf "$LEGACY_TARGET_ROOT"
fi

echo "[copilot-sync] Done. Published assets under: $GITHUB_ROOT"
echo "[copilot-sync] Copilot discovers them via the extra workspace folder: $CLONE_DIR"
echo "[copilot-sync] Managed assets use prefix: ${PREFIX}"
