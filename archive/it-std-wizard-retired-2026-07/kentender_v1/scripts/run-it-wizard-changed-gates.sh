#!/usr/bin/env bash
# Run path-filtered IT Wizard Makefile gates (PR fast path).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BENCH_ROOT="${BENCH_ROOT:-$(cd "$REPO_ROOT/../.." && pwd)}"
SITE="${SITE:-kentender.midas.com}"
BASE_REF="${1:-}"

GATES="$("$SCRIPT_DIR/it-wizard-changed-gates.sh" "$BASE_REF")"
if [[ -z "$GATES" ]]; then
	echo "No IT Wizard gates matched changed paths."
	exit 0
fi

echo "Bench root: $BENCH_ROOT"
echo "Site: $SITE"
echo "Running gates: $GATES"

for gate in $GATES; do
	echo "=== make $gate SITE=$SITE ==="
	make -C "$REPO_ROOT" "$gate" SITE="$SITE" BENCH_ROOT="$BENCH_ROOT"
done

echo "All changed-path IT Wizard gates passed."
