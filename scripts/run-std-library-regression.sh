#!/usr/bin/env bash
# Sequential STD library + Works POC + governance smoke regression for site kentender.midas.com.
# Run from anywhere; resolves Frappe bench root as parent of apps/ (sibling of this repo under apps/kentender_v1/scripts).
# Avoids parallel bench modules mutating STD Template (lock timeout / TimestampMismatchError).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BENCH_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$BENCH_ROOT"
SITE="${STD_LIB_REGRESSION_SITE:-kentender.midas.com}"
APP="kentender_procurement"
BASE=(bench --site "$SITE" run-tests --app "$APP" --module)

echo "Bench root: $BENCH_ROOT"
echo "Using site=$SITE (override with STD_LIB_REGRESSION_SITE)"
"${BASE[@]}" kentender_procurement.tender_management.tests.test_std_works_poc_step9_doctypes
"${BASE[@]}" kentender_procurement.tender_management.tests.test_std_works_poc_step10_loader
"${BASE[@]}" kentender_procurement.tender_management.tests.test_std_works_poc_step11_engine
"${BASE[@]}" kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8
echo "All sequential modules completed OK."
