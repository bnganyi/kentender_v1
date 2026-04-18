#!/usr/bin/env bash
set -euo pipefail
SITE="${1:-kentender.midas.com}"
cd /home/midasuser/frappe-bench
bench --site "$SITE" migrate
bench build --apps kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations
bench --site "$SITE" clear-cache
bench --site "$SITE" clear-website-cache
