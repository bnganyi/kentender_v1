#!/usr/bin/env bash
# Apply tracked KenTender patches to the bench-local Frappe tree (not versioned in kentender_v1).
#
# Run from anywhere:
#   ./apps/kentender_v1/scripts/apply-frappe-patches.sh
#
# After applying JS patches, rebuild desk assets:
#   ./scripts/bench-with-node.sh build --app frappe
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KENTENDER_V1_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BENCH_ROOT="$(cd "${KENTENDER_V1_ROOT}/../.." && pwd)"
PATCH_DIR="${KENTENDER_V1_ROOT}/patches/frappe"
TARGET="${BENCH_ROOT}/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar_item.js"
MARKER='if (!workspaces) {'

if [[ ! -f "${TARGET}" ]]; then
	echo "apply-frappe-patches: Frappe sidebar_item.js not found at ${TARGET}" >&2
	exit 1
fi

if grep -q "${MARKER}" "${TARGET}"; then
	echo "apply-frappe-patches: sidebar workspace null guard already present"
	exit 0
fi

PATCH_FILE="${PATCH_DIR}/sidebar_item_workspace_null_guard.patch"
if [[ ! -f "${PATCH_FILE}" ]]; then
	echo "apply-frappe-patches: missing patch file ${PATCH_FILE}" >&2
	exit 1
fi

cd "${BENCH_ROOT}"
patch -p0 --forward --batch < "${PATCH_FILE}"
echo "apply-frappe-patches: applied sidebar_item workspace null guard"
echo "apply-frappe-patches: run ./scripts/bench-with-node.sh build --app frappe"
