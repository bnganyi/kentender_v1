#!/usr/bin/env bash
# The platform a Contract Management result was obtained on (CM-CHG-001 v0.8 follow-up FU-CM-39; CM-ADVICE-001 section 7 step 1): the versions of what the native
# documents are made by, and the commit of this repository, so a result is read against the stack it came from and an upgrade is known to need the native
# gate again. Writes markdown to stdout; `make cm-platform-manifest` keeps it in artifacts/cm-platform-manifest.md. Needs no site.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH="${BENCH_ROOT:-$(cd "$ROOT/../.." && pwd)}"
PY="$BENCH/env/bin/python"
[ -x "$PY" ] || PY="python3"

versions="$("$PY" - <<'PYEOF' 2>/dev/null
import importlib
for name in ("frappe", "erpnext", "kentender_core", "kentender_suppliers", "kentender_budget", "kentender_procurement", "kentender_contracts"):
    try:
        print(f"{name}|{importlib.import_module(name).__version__}")
    except Exception:
        print(f"{name}|not installed in this environment")
PYEOF
)"

echo "# Contract Management platform manifest"
echo
echo "| | |"
echo "|---|---|"
echo "| Taken | $(date '+%Y-%m-%d %H:%M:%S %z') |"
echo "| Repository commit | \`$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)\` on \`$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)\` ($(git -C "$ROOT" status --porcelain 2>/dev/null | grep -c . || true) uncommitted paths) |"
while IFS='|' read -r name version; do
	[ -n "$name" ] && echo "| $name | $version |"
done <<<"$versions"
for app in frappe erpnext; do
	if git -C "$BENCH/apps/$app" rev-parse HEAD >/dev/null 2>&1; then
		echo "| $app commit | \`$(git -C "$BENCH/apps/$app" rev-parse --short HEAD)\` |"
	else
		echo "| $app commit | none: installed as a release, not a checkout; the version above is the pin |"
	fi
done
echo "| Python | $("$PY" --version 2>&1) |"
echo "| Node | $(node --version 2>/dev/null || echo unknown) |"
echo "| Database server | $( (mariadb --version || mysql --version) 2>/dev/null | head -1 | sed 's/ *using.*//' || echo unknown) |"
echo
echo "A change to any line above makes the earlier native, seams and release-evidence results stale for that line: run \`make cm-native-gate\` and \`make cm-seams-gate\` (and the whole \`make ui-cm-release-evidence-gate\` before a release) again, and say which line changed."
