#!/usr/bin/env bash
# Capture the Bid Evaluation component fixtures from the browser worlds
# (EVL-CHG-001 v0.4 plan Phase 11): one world is walked along the ordinary
# path and captured at every stage; each branch is built once. Writes
# public/js/bid_evaluation/fixtures/<stage>.json and restores the site.
# Never run while a Python test module or a Playwright run is using the site.
set -euo pipefail
BENCH_ROOT="$(cd "$(dirname "$0")/../../../../../.." && pwd)"
cd "$BENCH_ROOT"
bench --site "${UI_SITE:-kentender.midas.com}" execute kentender_procurement.bid_evaluation.seeds.playwright_ui_fixtures.capture_all | tail -1
