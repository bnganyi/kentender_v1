#!/usr/bin/env bash
# Map changed files to IT Wizard Makefile gate targets (space-separated, one line).
# Usage:
#   scripts/it-wizard-changed-gates.sh [base_ref]
# Default base_ref: merge-base with origin/master, else HEAD~1, else empty (working tree).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

BASE_REF="${1:-}"
if [[ -z "$BASE_REF" ]]; then
	if git rev-parse --verify origin/master >/dev/null 2>&1; then
		BASE_REF="$(git merge-base HEAD origin/master 2>/dev/null || echo "origin/master")"
	elif git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
		BASE_REF="HEAD~1"
	else
		BASE_REF=""
	fi
fi

if [[ -n "$BASE_REF" ]]; then
	CHANGED="$(git diff --name-only "$BASE_REF"...HEAD 2>/dev/null || git diff --name-only "$BASE_REF" HEAD)"
else
	CHANGED="$(git diff --name-only HEAD; git diff --name-only --cached HEAD; git ls-files --others --exclude-standard)"
fi

declare -A GATE_SET=()

add_gate() {
	GATE_SET["$1"]=1
}

matches() {
	local pattern="$1"
	while IFS= read -r path; do
		[[ -z "$path" ]] && continue
		if [[ "$path" =~ $pattern ]]; then
			return 0
		fi
	done <<<"$CHANGED"
	return 1
}

if [[ -z "$CHANGED" ]]; then
	exit 0
fi

# Shared engine/API touches multiple screens — run affected fast gates, not full regression.
if matches '(^|/)it_wizard_engine\.js$|(^|/)instance_api\.py$|(^|/)wizard_instance_service\.py$'; then
	add_gate "it-wizard-screen-01-gate"
	add_gate "it-wizard-screen-02-gate"
fi

if matches 'IT-STD-Wizard-v2/screen-01/|it_wizard_dashboard\.html|dashboard-desk-wiring|test_it_wizard_ui_dashboard_layout_guard|test_dashboard_kpi_service|test_it_wizard_dashboard_desk_wiring|it-tender-configuration-dashboard'; then
	add_gate "it-wizard-screen-01-gate"
fi

if matches 'IT-STD-Wizard-v2/screen-02/|it_wizard_std_config_overview\.html|overview-desk-wiring|test_it_wizard_ui_std_config_overview_layout_guard|test_wizard_overview_service|test_it_wizard_overview_desk_wiring|it-tender-configuration-overview'; then
	add_gate "it-wizard-screen-02-gate"
fi

if matches 'tender-profile-desk-wiring|test_wizard_tender_profile_service|test_it_wizard_tender_profile|it_wizard_tender_profile\.html|it-tender-configuration-tender-profile'; then
	add_gate "it-wizard-screens-03-06-gate"
fi

if matches 'tds-desk-wiring|test_wizard_tds_service|test_it_wizard_tds|it_wizard_tds\.html|it-tender-configuration-tds'; then
	add_gate "it-wizard-screens-03-06-gate"
fi

if matches 'it-requirements-desk-wiring|test_wizard_it_requirements_service|test_it_wizard_it_requirements|it_wizard_it_requirements\.html|it-tender-configuration-it-requirements'; then
	add_gate "it-wizard-screens-03-06-gate"
fi

if matches 'implementation-schedule-desk-wiring|test_wizard_implementation_schedule_service|test_it_wizard_implementation_schedule|it_wizard_implementation_schedule\.html|it-tender-configuration-implementation-schedule'; then
	add_gate "it-wizard-screens-03-06-gate"
fi

if matches 'test_instance_api\.py'; then
	add_gate "it-wizard-screens-03-06-gate"
fi

if matches 'downstream-desk-wiring|price-schedule-desk-wiring|it_wizard_downstream|test_it_wizard_downstream|test_wizard_price_schedule|it_wizard_price_schedule'; then
	add_gate "it-wizard-downstream-gate"
fi

if matches 'ownership-contract|test_it_wizard_ownership_contract|Screen_Ownership'; then
	add_gate "it-wizard-ownership-gate"
fi

if matches 'test_it_wizard_ui_.*_layout_guard|it_tender_wizard_impl/.*\.html$|IT-STD-Wizard/ui-designs/'; then
	add_gate "it-wizard-static-gate"
fi

if matches 'test_it_wizard_navigation_contract'; then
	add_gate "it-wizard-screen-01-gate"
fi

if [[ ${#GATE_SET[@]} -eq 0 ]]; then
	if matches 'it_tender_wizard/|tests/ui/smoke/it-std-wizard/|IT-STD-Wizard'; then
		add_gate "it-wizard-screen-01-gate"
	fi
fi

# Stable output order for CI logs.
for gate in it-wizard-screen-01-gate it-wizard-screen-02-gate it-wizard-screens-03-06-gate it-wizard-ownership-gate it-wizard-downstream-gate it-wizard-static-gate; do
	if [[ -n "${GATE_SET[$gate]:-}" ]]; then
		printf '%s ' "$gate"
	fi
done | sed 's/ $//'
