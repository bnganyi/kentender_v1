#!/usr/bin/env bash
# Generate ARCHIVE_MANIFEST.md for STD Module POC retirement.
# Run from repo root (apps/kentender_v1) before git mv operations.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVE_ROOT="${REPO_ROOT}/archive/std-module-poc-retired-2026-07"
MANIFEST="${ARCHIVE_ROOT}/ARCHIVE_MANIFEST.md"
SNAPSHOT="${ARCHIVE_ROOT}/SNAPSHOT_COMMIT.txt"

mkdir -p "${ARCHIVE_ROOT}"

if git -C "${REPO_ROOT}" rev-parse HEAD >/dev/null 2>&1; then
  git -C "${REPO_ROOT}" rev-parse HEAD > "${SNAPSHOT}"
else
  echo "unknown" > "${SNAPSHOT}"
fi

{
  echo "# STD Module POC — Archive Manifest"
  echo ""
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Snapshot commit: $(cat "${SNAPSHOT}")"
  echo ""
  echo "| # | Original path | Bucket |"
  echo "|---|---------------|--------|"
} > "${MANIFEST}"

idx=0
add_file() {
  local path="$1"
  local bucket="$2"
  if [[ -e "${REPO_ROOT}/${path}" || -e "${path}" ]]; then
    idx=$((idx + 1))
    local rel="${path#${REPO_ROOT}/}"
    echo "| ${idx} | \`${rel}\` | ${bucket} |" >> "${MANIFEST}"
  fi
}

add_glob() {
  local pattern="$1"
  local bucket="$2"
  local base="${REPO_ROOT}"
  while IFS= read -r -d '' f; do
    idx=$((idx + 1))
    local rel="${f#${base}/}"
    echo "| ${idx} | \`${rel}\` | ${bucket} |" >> "${MANIFEST}"
  done < <(find "${base}" -path "${base}/archive/std-module-poc-retired-2026-07" -prune -o -path "${base}/node_modules" -prune -o -path "${base}/.git" -prune -o -path "${pattern}" -print 2>/dev/null | sort -z)
}

KP="kentender_procurement/kentender_procurement"

# --- Desk UI pages ---
for page in std_library std_configurator std_engine std_engine_advanced; do
  add_glob "${KP}/kentender_procurement/page/${page}/*" "UI:Desk pages"
done

# --- Public JS/CSS ---
add_glob "${KP}/public/js/std_library/*" "UI:JS std_library"
add_glob "${KP}/public/js/std_config/*" "UI:JS std_config"
add_glob "${KP}/public/js/std_engine*" "UI:JS std_engine"
add_file "${KP}/public/js/std_config_workspace.js" "UI:JS workspace"
add_glob "${KP}/public/css/std_library*" "UI:CSS std_library"
add_glob "${KP}/public/css/std_config*" "UI:CSS std_config"
add_glob "${KP}/public/css/std_configurator*" "UI:CSS std_configurator"

# --- APIs ---
for api in std_configurator std_library_templates std_library_summary std_instance; do
  add_file "${KP}/tender_management/api/${api}.py" "API"
done
add_glob "${KP}/tender_management/api/std_library_*.py" "API"
add_glob "${KP}/tender_management/api/works_completion.py" "API:works_completion"

# --- Services ---
STD_SERVICES=(
  std_configurator_service std_config_section_schema std_config_roles
  std_config_ui_feature std_config_legacy_projection std_library_package_projection
  std_template_governance std_template_governance_lifecycle std_template_governance_roles
  std_template_loader std_template_engine std_template_handoff_resolution
  std_admin_console std_package_viewer std_package_validation
  officer_tender_config bind_tender_std_instance tm2_std_adapter
  planning_tender_handoff_xmv
)
for svc in "${STD_SERVICES[@]}"; do
  add_file "${KP}/tender_management/services/${svc}.py" "Services"
done
add_glob "${KP}/tender_management/services/std_template_governance*.py" "Services"

# --- std_instance package ---
add_glob "${KP}/tender_management/std_instance/*" "Instance runtime"

# --- DocTypes ---
add_glob "${KP}/kentender_procurement/doctype/std_*/*" "DocTypes:std_*"
add_glob "${KP}/kentender_procurement/doctype/tender_std_*/*" "DocTypes:tender_std_*"
add_glob "${KP}/kentender_procurement/doctype/tm2_tender_std_*/*" "DocTypes:tm2_std"

# --- Templates & seeds ---
add_glob "${KP}/tender_management/std_templates/*" "Templates"
add_glob "${KP}/tender_management/seeds/*std*" "Seeds"
add_glob "${KP}/tender_management/seeds/works_master_std*" "Seeds"
add_glob "${KP}/procurement_planning/seeds/seed_works_stdint*" "Seeds"
add_glob "${KP}/patches/std_*" "Patches"
add_glob "${KP}/patches/stdinst_*" "Patches"
add_glob "${KP}/patches/std_gov_*" "Patches"
add_glob "${KP}/patches/std_cfg_*" "Patches"

# --- Backend tests ---
add_glob "${KP}/tender_management/tests/test_std_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_stdinst_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_std_inst_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_std_config_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_std_library_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_std_admin_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_std_gov_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_works_comp_*" "Tests:backend"
add_glob "${KP}/tender_management/tests/test_r2_008_*" "Tests:backend"
add_glob "${KP}/setup/tests/test_r*std*" "Tests:backend"
add_glob "${KP}/procurement_lifecycle/tests/test_r*std*" "Tests:backend"
add_glob "${KP}/procurement_planning/tests/test_*std*" "Tests:backend"
add_glob "${KP}/procurement_planning/tests/test_pw4_wizard_document_std_path.py" "Tests:backend"
add_glob "${KP}/procurement_planning/tests/test_pp2_reg_*std*" "Tests:backend"

# --- kentender_v1 tests, frontend, docs ---
add_glob "tests/ui/smoke/std-config/*" "Tests:Playwright"
add_glob "tests/ui/smoke/procurement/std-*" "Tests:Playwright"
add_glob "frontend/src/modules/std-engine/*" "Frontend:std-engine"
add_glob "docs/prompts/std config/*" "Docs"
add_glob "docs/prompts/std poc/*" "Docs"
add_glob "docs/prompts/std-production-readiness/*" "Docs"
add_glob "docs/std prod/*" "Docs"

# --- Cursor rules (bench root) ---
BENCH_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
for rule in kentender-std-poc-implementation.mdc kentender-std-admin-console-implementation.mdc kentender-std-config-workbench-density.mdc; do
  if [[ -f "${BENCH_ROOT}/.cursor/rules/${rule}" ]]; then
    idx=$((idx + 1))
    echo "| ${idx} | \`.cursor/rules/${rule}\` | Cursor rules |" >> "${MANIFEST}"
  fi
done

{
  echo ""
  echo "## Summary"
  echo ""
  echo "Total files inventoried: **${idx}**"
} >> "${MANIFEST}"

echo "Wrote ${MANIFEST} (${idx} files)"
echo "Snapshot: $(cat "${SNAPSHOT}")"
