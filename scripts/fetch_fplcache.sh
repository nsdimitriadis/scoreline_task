#!/usr/bin/env bash
set -euo pipefail

# Fetch a sparse copy of the fplcache repository with only cache years.

VERBOSE="${VERBOSE:-0}"
log() {
  if [ "${VERBOSE}" = "1" ]; then
    echo "$@"
  fi
}

DEST="${FPLCACHE_DIR:-vendor/fplcache}"
REPO="https://github.com/Randdalf/fplcache.git"
FPLCACHE_COMMIT="${FPLCACHE_COMMIT:-}"

log "Fetching fplcache into: ${DEST}"

# Guard: directory exists but not a git repo
if [ -d "${DEST}" ] && [ ! -d "${DEST}/.git" ]; then
  echo "Error: ${DEST} exists but is not a git repo. Delete it or set FPLCACHE_DIR." >&2
  exit 1
fi

if [ -d "${DEST}/.git" ]; then
  log "fplcache already present at ${DEST} — tightening sparse checkout to cache/2023-2025"
  cd "${DEST}"
  # Switch to non-cone mode and explicitly restrict to cache years.
  git sparse-checkout init --no-cone >/dev/null 2>&1 || true
  printf "/cache/2023/*\n/cache/2024/*\n/cache/2025/*\n" | git sparse-checkout set --stdin >/dev/null
  git sparse-checkout reapply >/dev/null 2>&1 || true
  # Optionally pin to a specific commit/ref
  if [ -n "${FPLCACHE_COMMIT}" ]; then
    git fetch -q --depth=1 origin "${FPLCACHE_COMMIT}" || true
    if ! git checkout -q "${FPLCACHE_COMMIT}"; then
      echo "Error: failed to checkout ${FPLCACHE_COMMIT}. Ensure the ref exists on origin." >&2
      exit 1
    fi
  else
    # Re-apply current branch to update working tree
    git checkout -q "$(git rev-parse --abbrev-ref HEAD)" >/dev/null 2>&1 || true
  fi
  echo "fplcache cache already available at: ${DEST}/cache"
  exit 0
fi

mkdir -p "$(dirname "${DEST}")"

# Shallow, partial clone with no checkout to avoid materializing root files.
git clone -q --depth=1 --filter=blob:none --no-checkout "${REPO}" "${DEST}"

cd "${DEST}"

# Use non-cone mode with explicit patterns for only the desired paths.
git sparse-checkout init --no-cone >/dev/null
printf "/cache/2023/*\n/cache/2024/*\n/cache/2025/*\n" | git sparse-checkout set --stdin >/dev/null

# Checkout after patterns are in place to materialize only the sparse paths.
if [ -n "${FPLCACHE_COMMIT}" ]; then
  git fetch -q --depth=1 origin "${FPLCACHE_COMMIT}" || true
  if ! git checkout -q "${FPLCACHE_COMMIT}"; then
    echo "Error: failed to checkout ${FPLCACHE_COMMIT}. Ensure the ref exists on origin." >&2
    exit 1
  fi
else
  DEFAULT_BRANCH="$(git remote show origin | awk '/HEAD branch/ {print $NF}')"
  git checkout -q "${DEFAULT_BRANCH}"
fi

echo "fplcache cache available at: ${DEST}/cache"


