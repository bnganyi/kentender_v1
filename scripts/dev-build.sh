#!/usr/bin/env bash
set -euo pipefail
cd /home/midasuser/frappe-bench
bench build --apps kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_suppliers,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations,kentender_transparency
