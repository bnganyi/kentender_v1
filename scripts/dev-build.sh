#!/usr/bin/env bash
set -euo pipefail
# The bench is three levels above this script (<bench>/apps/kentender_v1/scripts).
cd "${BENCH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
bench build --apps kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_suppliers,kentender_contracts,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations,kentender_transparency
