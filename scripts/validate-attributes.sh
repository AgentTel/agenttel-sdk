#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Validate attribute parity across the JVM, Go, Node.js and Python SDKs
# against the canonical attributes.json schema.
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors (no-op if not a terminal)
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  CYAN='\033[0;36m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
fi

pass() { echo -e "${GREEN}PASS${RESET} $1"; }
fail() { echo -e "${RED}FAIL${RESET} $1"; }
warn() { echo -e "${YELLOW}WARN${RESET} $1"; }
info() { echo -e "${CYAN}INFO${RESET} $1"; }

CANONICAL_FILE="$REPO_ROOT/attributes.json"
EXIT_CODE=0

# ─────────────────────────────────────────────────────────────────────────────
# 1. Parse canonical attributes from attributes.json
# ─────────────────────────────────────────────────────────────────────────────
if [ ! -f "$CANONICAL_FILE" ]; then
  fail "attributes.json not found at $CANONICAL_FILE"
  exit 1
fi

echo -e "\n${BOLD}Canonical Attribute Schema Validation${RESET}"
echo "────────────────────────────────────────────────────────────"

# Attribute keys plus event names: the SDKs define constants for both
CANONICAL=$(jq -r '(.namespaces[].attributes[].key), (.events | keys[])' "$CANONICAL_FILE" | sort -u)
CANONICAL_COUNT=$(echo "$CANONICAL" | wc -l | tr -d ' ')
info "Canonical attributes: $CANONICAL_COUNT keys and event names from attributes.json"

# Write canonical to temp file
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
echo "$CANONICAL" > "$TMPDIR/canonical.txt"
jq -r '.namespaces[].attributes[] | "\(.key) \(.type)"' "$CANONICAL_FILE" | sort -u > "$TMPDIR/canonical-types.txt"

# ─────────────────────────────────────────────────────────────────────────────
# 1b. Schema metadata: every entry must say how it maps to OTel upstream.
#     Field meanings are in docs/reference/attribute-schema.md.
# ─────────────────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}Schema metadata${RESET}"
METADATA_ERRORS=$(jq -r '
  def check($where; $cond; $msg): if $cond then empty else "\($where): \($msg)" end;
  def check_upstream($where):
    .upstream as $u
    | check($where; $u != null; "missing upstream"),
      (if $u then
         check($where; ($u.status | IN("candidate", "later", "otel_existing", "out_of_scope", "internal")); "bad upstream.status \($u.status)"),
         (if ($u.status | IN("candidate", "later")) then
            check($where; ($u.key // "" | startswith("reliability.")); "upstream.key must start with reliability.")
          elif $u.status == "otel_existing" then
            check($where; ($u.key // "") != ""; "otel_existing needs upstream.key")
          else
            check($where; $u.key == null; "\($u.status) must not set upstream.key")
          end)
       else empty end);
  (.namespaces[].attributes[] | .key as $k |
    check($k; (.type | IN("string", "int", "double", "boolean", "string[]")); "bad type \(.type)"),
    check($k; (.stability | IN("development", "stable", "deprecated")); "bad stability \(.stability)"),
    check($k; (.kind | IN("declared", "derived", "hybrid", "observed")); "bad kind \(.kind)"),
    check($k; (.level | IN("resource", "span", "event")); "bad level \(.level)"),
    check_upstream($k)),
  (.events | to_entries[] | .key as $k | .value |
    check($k; (.stability | IN("development", "stable", "deprecated")); "bad stability \(.stability)"),
    check_upstream($k)),
  ([.namespaces[].attributes[].key] | group_by(.)[] | select(length > 1) | "\(.[0]): duplicate key"),
  # Attribute and event names live in separate OTel registries, so check each on its own
  ([.namespaces[].attributes[].upstream | select(.status | IN("candidate", "later")) | .key]
    | group_by(.)[] | select(length > 1) | "\(.[0]): upstream.key used twice"),
  ([.events[].upstream | select(.status | IN("candidate", "later")) | .key]
    | group_by(.)[] | select(length > 1) | "\(.[0]): upstream event name used twice")
' "$CANONICAL_FILE")

if [ -z "$METADATA_ERRORS" ]; then
  pass "Every attribute and event has valid stability, kind, level and upstream metadata"
  info "Upstream status: $(jq -r '[(.namespaces[].attributes[], .events[]) | .upstream.status] | group_by(.) | map("\(.[0])=\(length)") | join(", ")' "$CANONICAL_FILE")"
else
  fail "Schema metadata errors:"
  echo "$METADATA_ERRORS" | while read -r line; do
    echo "    ! $line"
  done
  EXIT_CODE=1
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2. Extract attributes from each SDK
# ─────────────────────────────────────────────────────────────────────────────

# --- Go SDK ---
echo -e "\n${BOLD}Go SDK${RESET}"
GO_ATTRS_FILE="$REPO_ROOT/agenttel-go/attributes/attributes.go"
GO_AGENTIC_FILE="$REPO_ROOT/agenttel-go/attributes/agentic.go"

if [ -f "$GO_ATTRS_FILE" ] && [ -f "$GO_AGENTIC_FILE" ]; then
  # Extract all quoted strings matching agenttel.* or gen_ai.*
  {
    grep -oE '"agenttel\.[^"]*"' "$GO_ATTRS_FILE" | tr -d '"'
    grep -oE '"gen_ai\.[^"]*"' "$GO_ATTRS_FILE" | tr -d '"'
    grep -oE '"agenttel\.[^"]*"' "$GO_AGENTIC_FILE" | tr -d '"'
    grep -oE '"gen_ai\.[^"]*"' "$GO_AGENTIC_FILE" 2>/dev/null | tr -d '"' || true
  } | sort -u > "$TMPDIR/go.txt"

  GO_COUNT=$(wc -l < "$TMPDIR/go.txt" | tr -d ' ')
  info "Go attributes: $GO_COUNT keys"

  # Diff: missing from Go (in canonical but not in Go)
  GO_MISSING=$(comm -23 "$TMPDIR/canonical.txt" "$TMPDIR/go.txt")
  GO_EXTRA=$(comm -13 "$TMPDIR/canonical.txt" "$TMPDIR/go.txt")

  if [ -z "$GO_MISSING" ] && [ -z "$GO_EXTRA" ]; then
    pass "Go SDK — all $CANONICAL_COUNT attributes match canonical"
  else
    if [ -n "$GO_MISSING" ]; then
      MISSING_COUNT=$(echo "$GO_MISSING" | wc -l | tr -d ' ')
      fail "Go SDK — $MISSING_COUNT attributes MISSING from Go:"
      echo "$GO_MISSING" | while read -r key; do
        echo "    - $key"
      done
      EXIT_CODE=1
    fi
    if [ -n "$GO_EXTRA" ]; then
      EXTRA_COUNT=$(echo "$GO_EXTRA" | wc -l | tr -d ' ')
      warn "Go SDK — $EXTRA_COUNT EXTRA attributes not in canonical:"
      echo "$GO_EXTRA" | while read -r key; do
        echo "    + $key"
      done
      EXIT_CODE=1
    fi
  fi
else
  warn "Go SDK — attribute files not found, skipping"
fi

# --- Node.js SDK ---
echo -e "\n${BOLD}Node.js SDK${RESET}"
NODE_ATTRS_FILE="$REPO_ROOT/agenttel-node/src/attributes.ts"
NODE_AGENTIC_FILE="$REPO_ROOT/agenttel-node/src/agentic-attributes.ts"

if [ -f "$NODE_ATTRS_FILE" ] && [ -f "$NODE_AGENTIC_FILE" ]; then
  # Extract all quoted strings matching agenttel.* or gen_ai.* (single quotes)
  {
    grep -oE "'agenttel\.[^']*'" "$NODE_ATTRS_FILE" | tr -d "'"
    grep -oE "'gen_ai\.[^']*'" "$NODE_ATTRS_FILE" | tr -d "'"
    grep -oE "'agenttel\.[^']*'" "$NODE_AGENTIC_FILE" | tr -d "'"
    grep -oE "'gen_ai\.[^']*'" "$NODE_AGENTIC_FILE" 2>/dev/null | tr -d "'" || true
  } | sort -u > "$TMPDIR/node.txt"

  NODE_COUNT=$(wc -l < "$TMPDIR/node.txt" | tr -d ' ')
  info "Node.js attributes: $NODE_COUNT keys"

  # Diff: missing from Node.js (in canonical but not in Node.js)
  NODE_MISSING=$(comm -23 "$TMPDIR/canonical.txt" "$TMPDIR/node.txt")
  NODE_EXTRA=$(comm -13 "$TMPDIR/canonical.txt" "$TMPDIR/node.txt")

  if [ -z "$NODE_MISSING" ] && [ -z "$NODE_EXTRA" ]; then
    pass "Node.js SDK — all $CANONICAL_COUNT attributes match canonical"
  else
    if [ -n "$NODE_MISSING" ]; then
      MISSING_COUNT=$(echo "$NODE_MISSING" | wc -l | tr -d ' ')
      fail "Node.js SDK — $MISSING_COUNT attributes MISSING from Node.js:"
      echo "$NODE_MISSING" | while read -r key; do
        echo "    - $key"
      done
      EXIT_CODE=1
    fi
    if [ -n "$NODE_EXTRA" ]; then
      EXTRA_COUNT=$(echo "$NODE_EXTRA" | wc -l | tr -d ' ')
      warn "Node.js SDK — $EXTRA_COUNT EXTRA attributes not in canonical:"
      echo "$NODE_EXTRA" | while read -r key; do
        echo "    + $key"
      done
      EXIT_CODE=1
    fi
  fi
else
  warn "Node.js SDK — attribute files not found, skipping"
fi

# --- Python SDK ---
echo -e "\n${BOLD}Python SDK${RESET}"
PY_ATTRS_FILE="$REPO_ROOT/agenttel-python/src/agenttel/attributes.py"
PY_AGENTIC_FILE="$REPO_ROOT/agenttel-python/src/agenttel/agentic_attributes.py"
PY_GENAI_FILE="$REPO_ROOT/agenttel-python/src/agenttel/genai/attributes.py"

PY_FILES_FOUND=0
PY_FILES=()
for f in "$PY_ATTRS_FILE" "$PY_AGENTIC_FILE" "$PY_GENAI_FILE"; do
  if [ -f "$f" ]; then
    PY_FILES_FOUND=$((PY_FILES_FOUND + 1))
    PY_FILES+=("$f")
  fi
done

if [ "$PY_FILES_FOUND" -gt 0 ]; then
  # Extract all quoted strings matching agenttel.* or gen_ai.* (double quotes)
  {
    for f in "${PY_FILES[@]}"; do
      grep -oE '"agenttel\.[^"]*"' "$f" 2>/dev/null | tr -d '"' || true
      grep -oE '"gen_ai\.[^"]*"' "$f" 2>/dev/null | tr -d '"' || true
    done
  } | sort -u > "$TMPDIR/python.txt"

  PY_COUNT=$(wc -l < "$TMPDIR/python.txt" | tr -d ' ')
  info "Python attributes: $PY_COUNT keys (from $PY_FILES_FOUND files)"

  # Diff: missing from Python (in canonical but not in Python)
  PY_MISSING=$(comm -23 "$TMPDIR/canonical.txt" "$TMPDIR/python.txt")
  PY_EXTRA=$(comm -13 "$TMPDIR/canonical.txt" "$TMPDIR/python.txt")

  if [ -z "$PY_MISSING" ] && [ -z "$PY_EXTRA" ]; then
    pass "Python SDK — all $CANONICAL_COUNT attributes match canonical"
  else
    if [ -n "$PY_MISSING" ]; then
      MISSING_COUNT=$(echo "$PY_MISSING" | wc -l | tr -d ' ')
      fail "Python SDK — $MISSING_COUNT attributes MISSING from Python:"
      echo "$PY_MISSING" | while read -r key; do
        echo "    - $key"
      done
      EXIT_CODE=1
    fi
    if [ -n "$PY_EXTRA" ]; then
      EXTRA_COUNT=$(echo "$PY_EXTRA" | wc -l | tr -d ' ')
      warn "Python SDK — $EXTRA_COUNT EXTRA attributes not in canonical:"
      echo "$PY_EXTRA" | while read -r key; do
        echo "    + $key"
      done
      EXIT_CODE=1
    fi
  fi
else
  warn "Python SDK — attribute files not found, skipping"
fi

# --- JVM SDK ---
echo -e "\n${BOLD}JVM SDK${RESET}"
JVM_FILES=(
  "$REPO_ROOT/agenttel-api/src/main/java/io/agenttel/api/attributes/AgentTelAttributes.java"
  "$REPO_ROOT/agenttel-api/src/main/java/io/agenttel/api/attributes/AgenticAttributes.java"
  "$REPO_ROOT/agenttel-api/src/main/java/io/agenttel/api/events/AgentTelEvents.java"
  "$REPO_ROOT/agenttel-genai/src/main/java/io/agenttel/genai/conventions/GenAiAttributes.java"
  "$REPO_ROOT/agenttel-genai/src/main/java/io/agenttel/genai/conventions/AgentTelGenAiAttributes.java"
)

JVM_FOUND=()
for f in "${JVM_FILES[@]}"; do
  [ -f "$f" ] && JVM_FOUND+=("$f")
done

if [ "${#JVM_FOUND[@]}" -gt 0 ]; then
  # Keys: every quoted agenttel.* or gen_ai.* string (attribute keys and event names)
  cat "${JVM_FOUND[@]}" | grep -oE '"(agenttel|gen_ai)\.[^"]*"' | tr -d '"' | sort -u > "$TMPDIR/jvm.txt"

  # Types: AttributeKey.<type>Key("...") declarations, which may wrap across lines
  cat "${JVM_FOUND[@]}" | tr -d '\n' \
    | grep -oE 'AttributeKey\.[a-zA-Z]+Key\([[:space:]]*"[^"]+"' \
    | sed -E 's/AttributeKey\.([a-zA-Z]+)Key\([[:space:]]*"([^"]+)"/\2 \1/' \
    | sed -E 's/ string$/ string/; s/ long$/ int/; s/ double$/ double/; s/ boolean$/ boolean/; s/ stringArray$/ string[]/' \
    | sort -u > "$TMPDIR/jvm-types.txt"

  JVM_COUNT=$(wc -l < "$TMPDIR/jvm.txt" | tr -d ' ')
  info "JVM attributes: $JVM_COUNT keys (from ${#JVM_FOUND[@]} files)"

  JVM_MISSING=$(comm -23 "$TMPDIR/canonical.txt" "$TMPDIR/jvm.txt")
  JVM_EXTRA=$(comm -13 "$TMPDIR/canonical.txt" "$TMPDIR/jvm.txt")
  # Keys present on both sides whose declared types differ
  JVM_TYPE_DIFF=$(join "$TMPDIR/canonical-types.txt" "$TMPDIR/jvm-types.txt" | awk '$2 != $3 { print $1 " (schema " $2 ", JVM " $3 ")" }')

  if [ -z "$JVM_MISSING" ] && [ -z "$JVM_EXTRA" ] && [ -z "$JVM_TYPE_DIFF" ]; then
    pass "JVM SDK — all $CANONICAL_COUNT attributes match canonical, with matching types"
  else
    if [ -n "$JVM_MISSING" ]; then
      MISSING_COUNT=$(echo "$JVM_MISSING" | wc -l | tr -d ' ')
      fail "JVM SDK — $MISSING_COUNT attributes MISSING from JVM:"
      echo "$JVM_MISSING" | while read -r key; do
        echo "    - $key"
      done
      EXIT_CODE=1
    fi
    if [ -n "$JVM_EXTRA" ]; then
      EXTRA_COUNT=$(echo "$JVM_EXTRA" | wc -l | tr -d ' ')
      warn "JVM SDK — $EXTRA_COUNT EXTRA attributes not in canonical:"
      echo "$JVM_EXTRA" | while read -r key; do
        echo "    + $key"
      done
      EXIT_CODE=1
    fi
    if [ -n "$JVM_TYPE_DIFF" ]; then
      DIFF_COUNT=$(echo "$JVM_TYPE_DIFF" | wc -l | tr -d ' ')
      fail "JVM SDK — $DIFF_COUNT attributes with a different type:"
      echo "$JVM_TYPE_DIFF" | while read -r line; do
        echo "    ~ $line"
      done
      EXIT_CODE=1
    fi
  fi
else
  warn "JVM SDK — attribute files not found, skipping"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 3. Summary
# ─────────────────────────────────────────────────────────────────────────────
echo -e "\n────────────────────────────────────────────────────────────"
if [ "$EXIT_CODE" -eq 0 ]; then
  pass "${BOLD}All SDKs match the canonical attribute schema${RESET}"
else
  fail "${BOLD}Attribute parity check failed — see mismatches above${RESET}"
fi

exit "$EXIT_CODE"
