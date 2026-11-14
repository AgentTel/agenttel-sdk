#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Check the reliability.* Weaver registry in model/ (generated from
# attributes.json by scripts/generate-semconv-registry.py) with OTel Weaver:
#
#   1. Weaver resolves and checks the registry on its own.
#   2. The registry passes the semantic-conventions repository's own policy
#      check when copied into its model/ directory.
#   3. Schema freeze: nothing changes incompatibly against the registry at the
#      baseline git ref (removed attributes, changed types, removed enum members).
#
# Usage: scripts/check-semconv-registry.sh [baseline-ref]   (default: origin/main)
# Needs docker and git. Versions match the semantic-conventions repository's CI.
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASELINE_REF="${1:-origin/main}"

WEAVER=otel/weaver:v0.28.0@sha256:5857bb81d8cc7ed608cdcae37c4b459eb020f21dd4acade35f7933cd6762fbcc
SEMCONV_REPO=https://github.com/open-telemetry/semantic-conventions.git
SEMCONV_COMMIT=45b690d4a7af791c8c21956c1c8d78ec29295ea9
SEMCONV_BASELINE=https://github.com/open-telemetry/semantic-conventions/archive/refs/tags/v1.45.0.zip[model]
PACKAGES=https://github.com/open-telemetry/opentelemetry-weaver-packages.git@ce835bca2ef577c73cd0cff5da811e9d0b26527d

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
# Weaver caches the registries it downloads here; the container user may differ from ours
mkdir -p "$WORK/cache" && chmod 777 "$WORK/cache"

weaver() {
  docker run --rm --env USER=weaver --env HOME=/home/weaver -v "$WORK/cache":/home/weaver/.weaver "$@"
}

echo "== 1. Weaver check: model/"
weaver -v "$ROOT/model":/registry:ro "$WEAVER" registry check --registry=/registry --future

echo "== 2. semantic-conventions policy check with model/reliability added"
git init -q "$WORK/semconv"
git -C "$WORK/semconv" fetch -q --depth 1 "$SEMCONV_REPO" "$SEMCONV_COMMIT"
git -C "$WORK/semconv" checkout -q FETCH_HEAD
cp -R "$ROOT/model/reliability" "$WORK/semconv/model/reliability"
weaver \
  --mount type=bind,source="$WORK/semconv/policies",target=/home/weaver/policies,readonly \
  --mount type=bind,source="$WORK/semconv/model",target=/home/weaver/source,readonly \
  --mount type=bind,source="$WORK/semconv/.weaver.toml",target=/home/weaver/.weaver.toml,readonly \
  "$WEAVER" registry check --v2 \
  --config=/home/weaver/.weaver.toml \
  --registry=/home/weaver/source \
  --baseline-registry="$SEMCONV_BASELINE" \
  --policy=/home/weaver/policies \
  --policy="${PACKAGES}[policies/check/naming_conventions]" \
  --policy="${PACKAGES}[policies/check/stability]" \
  --policy="${PACKAGES}[policies/check/entity_associations]" \
  --policy="${PACKAGES}[policies/check/backwards-compatibility]"

echo "== 3. Schema freeze against $BASELINE_REF"
if ! git -C "$ROOT" cat-file -e "$BASELINE_REF:model/manifest.yaml" 2>/dev/null; then
  echo "No registry at $BASELINE_REF; nothing to compare."
  exit 0
fi
mkdir -p "$WORK/baseline"
git -C "$ROOT" archive "$BASELINE_REF" model | tar -x -C "$WORK/baseline"
weaver -v "$ROOT/model":/registry:ro -v "$WORK/baseline/model":/baseline:ro "$WEAVER" registry check --v2 \
  --registry=/registry \
  --baseline-registry=/baseline \
  --policy="${PACKAGES}[policies/check/backwards-compatibility]"
