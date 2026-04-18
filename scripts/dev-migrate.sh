#!/usr/bin/env bash
set -euo pipefail
SITE="${1:-kentender.midas.com}"
cd /home/midasuser/frappe-bench
bench --site "$SITE" migrate
