#!/usr/bin/env bash
# Rerun the linked Demo Platform seed (MOH IT STD chain) on the canonical site.
set -euo pipefail
SITE="${SITE:-kentender.midas.com}"
BENCH_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$BENCH_ROOT"
echo "Seeding demo platform on ${SITE} (reset=true)…"
bench --site "$SITE" execute kentender_core.seeds.seed_demo_platform.run --kwargs '{"reset": True}'
echo "Done. Validate with:"
echo "  bench --site ${SITE} execute kentender_core.seeds.seed_demo_platform.validate"
