#!/usr/bin/env bash
set -euo pipefail
SITE="${1:-kentender.midas.com}"
# The bench is three levels above this script (<bench>/apps/kentender_v1/scripts).
cd "${BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
bench --site "$SITE" migrate
