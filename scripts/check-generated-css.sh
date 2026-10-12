#!/usr/bin/env bash
# Are the generated design-system stylesheets what their generators build?
#
#   scripts/check-generated-css.sh          # check all three; exit 1 if any is out of date
#
# Three files are generated, never hand-edited or hand-merged:
#   kentender_core/.../public/css/kt_industry_tokens.css   <- scripts/industry_design_css.py
#   kentender_core/.../public/js/home/kt_home_ds.bundle.css      <- scripts/home_design_css.py
#   kentender_core/.../public/js/analytics/kt_analytics_ds.bundle.css <- scripts/home_design_css.py --target analytics
#
# Why this exists: on 6 Oct 2026 a merge conflict in kt_industry_tokens.css was resolved by
# keeping an older hand-written copy, which dropped the whole design-system stylesheet. Production
# then ran new markup against a stylesheet that defined none of it. Run by the pre-commit and
# pre-push hooks (`make install-git-hooks`), by `make design-css-check`, and after a production pull.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The bench's own Python has tinycss2; a plain python3 usually does not.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
	for candidate in "$ROOT/../../env/bin/python" "$ROOT/../env/bin/python" python3; do
		if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import tinycss2" >/dev/null 2>&1; then
			PY="$candidate"
			break
		fi
	done
fi
if [ -z "$PY" ]; then
	echo "check-generated-css: no Python with tinycss2 found (the bench env has it); set PYTHON=/path/to/python." >&2
	exit 2
fi

export PYTHONWARNINGS=ignore
failed=0
run() {
	local label="$1"
	shift
	if "$PY" "$@" --check >/dev/null 2>&1; then
		echo "  ok       $label"
	else
		echo "  STALE    $label   ->  regenerate: $PY ${*}" >&2
		failed=1
	fi
}

echo "Generated stylesheets:"
run "kt_industry_tokens.css (shared Industry stylesheet)" "$ROOT/scripts/industry_design_css.py"
run "kt_home_ds.bundle.css (Home)" "$ROOT/scripts/home_design_css.py"
run "kt_analytics_ds.bundle.css (Analytics)" "$ROOT/scripts/home_design_css.py" --target analytics

if [ "$failed" -ne 0 ]; then
	cat >&2 <<'MSG'

A generated stylesheet does not match its generator. Do not merge or edit these files by hand:
rerun the generator named above and commit the result. After a merge conflict in one of them,
take either side, then regenerate. (See AGENTS.md section 6.6, "Generated stylesheets".)
MSG
	exit 1
fi
