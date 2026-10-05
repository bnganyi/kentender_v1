#!/usr/bin/env bash
# Which design-match (fidelity) gates does this change make due?
#
#   scripts/fidelity-affected.sh                  changes in the working tree (uncommitted + untracked)
#   scripts/fidelity-affected.sh --since <ref>    also everything committed since <ref> (a slice, a branch)
#   scripts/fidelity-affected.sh --run            run the gates due, on the test site, one after another
#
# A fidelity gate compares a module's screens with its artboards. It only has
# anything to say when that module's screen code, styles or boards changed, so
# a server-only change, or a change in another module, makes no gate due. Run
# this once when a slice is ready, not after each small fix (AGENTS.md §8).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

since=""; run=0
while [ "$#" -gt 0 ]; do
	case "$1" in
		--since) since="${2:?--since needs a ref}"; shift 2 ;;
		--run) run=1; shift ;;
		*) sed -n '2,10p' "$0" >&2; exit 2 ;;
	esac
done

changed="$( {
	git diff --name-only HEAD
	git ls-files --others --exclude-standard
	[ -n "$since" ] && git diff --name-only "$since"...HEAD
	true
} | sort -u)"

declare -A files_for=()   # gate -> triggering files
add() { files_for["$1"]+="$2"$'\n'; }

while IFS= read -r f; do
	[ -n "$f" ] || continue
	case "$f" in
		# Component tests do not change what a screen renders.
		*.spec.js|*.spec.ts|*.test.js|*.test.ts) continue ;;
		# A module's screens (JS/Vue/CSS under its public folder) and its boards.
		*/public/js/departmental_needs/*|*/public/js/nds_shared/*|*/public/js/departmental_needs_page.js|docs/mvp-1-r1/01_departmental_needs/design/*.dc.html)
			add ui-departmental-needs-fidelity-gate "$f" ;;
		kentender_strategy/*/public/*|docs/mvp-1-r1/02_strategy/design/*.dc.html)
			add ui-strategy-fidelity-gate "$f" ;;
		kentender_budget/*/public/*|docs/mvp-1-r1/03_budget/design/*.dc.html)
			add ui-budget-fidelity-gate "$f" ;;
		*/public/js/procurement_planning/*|*/public/js/pln_shared/*|docs/mvp-1-r1/04_planning/design/*.dc.html)
			add ui-planning-fidelity-gate "$f" ;;
		*/public/js/procurement_requisitions/*|*/public/js/req_shared/*|docs/mvp-1-r1/06_requisitions/design/*.dc.html)
			add ui-req-fidelity-gate "$f" ;;
		*/public/js/tenders/*|*/public/js/tnd_shared/*|docs/mvp-1-r1/11_tenders/design/*.dc.html)
			add ui-tenders-fidelity-gate "$f" ;;
		kentender_core/*/public/js/system_setup/*|docs/mvp-1-r1/09_unified_system_setup/design/*.dc.html)
			add ui-system-setup-fidelity-gate "$f" ;;
		*/public/js/bid_portal/*|docs/mvp-1-r1/12_bid_submission/design/*.dc.html)
			add ui-bds-fidelity-gate "$f" ;;
		*/public/js/bid_opening/*|docs/mvp-1-r1/14_bid_opening/design/*.dc.html)
			add ui-bop-fidelity-gate "$f" ;;
		*/public/js/award/*|docs/mvp-1-r1/16_award/design/*.dc.html)
			add ui-awd-fidelity-gate "$f" ;;
		kentender_core/*/public/js/home/*|kentender_core/*/public/js/home_page.js|docs/mvp-1-r1/18_home_page/design/Home/*.dc.html)
			add ui-home-fidelity-gate "$f" ;;
		# Bid Evaluation has no module gate of its own: its boards are covered by
		# the shared structure gate below.
		*/public/js/bid_evaluation/*|docs/mvp-1-r1/15_bid_evaluation/design/*.dc.html)
			add ui-structure-gate "$f" ;;
		# Shared screen runtime, tokens and chrome reach every module.
		kentender_core/*/public/js/kt_industry/*|kentender_core/*/public/js/kt_desk_page.js|kentender_core/*/public/css/*|tests/ui/fidelity/*|tests/ui/helpers/designFidelity.ts)
			add SHARED "$f" ;;
	esac
done <<< "$changed"

if [ "${#files_for[@]}" -eq 0 ]; then
	echo "No screen, style or board file changed: no fidelity gate is due."
	exit 0
fi

gates=()
for g in "${!files_for[@]}"; do [ "$g" = SHARED ] || gates+=("$g"); done
IFS=$'\n' gates=($(printf '%s\n' "${gates[@]:-}" | sed '/^$/d' | sort)); unset IFS

echo "Fidelity gates due (run each once, when the slice is ready):"
for g in "${gates[@]:-}"; do
	[ -n "$g" ] || continue
	n=$(printf '%s' "${files_for[$g]}" | sed '/^$/d' | wc -l)
	echo "  make $g   ($n file(s), e.g. $(printf '%s' "${files_for[$g]}" | head -1))"
done
if [ -n "${files_for[SHARED]:-}" ]; then
	echo "  SHARED screen runtime/styles changed ($(printf '%s' "${files_for[SHARED]}" | sed '/^$/d' | wc -l) file(s), e.g. $(printf '%s' "${files_for[SHARED]}" | head -1)):"
	echo "    make ui-fidelity-gate now (structure + provenance, no browser), and every module gate"
	echo "    is due once before the slice is called done, not after each edit."
	gates=(ui-fidelity-gate "${gates[@]:-}")
fi
echo
echo "Copy-only change in one screen? Run just that board's test instead:"
echo "  scripts/test-site.sh run npx playwright test tests/ui/smoke/design-fidelity/<module>-fidelity.spec.ts -g '<BOARD-ID>' --workers=1"

if [ "$run" -eq 1 ]; then
	for g in "${gates[@]:-}"; do
		[ -n "$g" ] || continue
		echo; echo "== make $g (test site)"
		scripts/test-site.sh run make "$g"
	done
fi
