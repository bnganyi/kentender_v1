#!/usr/bin/env bash
set -euo pipefail
SITE="${1:-kentender.midas.com}"
# The bench is three levels above this script (<bench>/apps/kentender_v1/scripts).
cd "${BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
bench --site "$SITE" migrate
bench build --apps kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_suppliers,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations,kentender_transparency
bench --site "$SITE" clear-cache
bench --site "$SITE" clear-website-cache
