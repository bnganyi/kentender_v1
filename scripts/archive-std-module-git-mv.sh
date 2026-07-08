#!/usr/bin/env bash
# git mv STD Module POC artefacts into archive/std-module-poc-retired-2026-07/
# Run from apps/kentender_v1 after inventory script.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVE="${REPO_ROOT}/archive/std-module-poc-retired-2026-07"
KP="kentender_procurement/kentender_procurement"
BENCH_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"

cd "${REPO_ROOT}"

mv_path() {
  local src="$1"
  if [[ ! -e "${src}" ]]; then
    return 0
  fi
  local rel="${src}"
  if [[ "${rel}" == "${REPO_ROOT}/"* ]]; then
    rel="${rel#${REPO_ROOT}/}"
  fi
  local dest="${ARCHIVE}/${rel}"
  mkdir -p "$(dirname "${dest}")"
  if git ls-files --error-unmatch "${src}" >/dev/null 2>&1; then
    git mv "${src}" "${dest}"
  else
    mv "${src}" "${dest}"
  fi
}

mv_v1_path() {
  local src="$1"
  if [[ ! -e "${src}" ]]; then
    return 0
  fi
  local rel="${src}"
  if [[ "${rel}" == "${REPO_ROOT}/"* ]]; then
    rel="${rel#${REPO_ROOT}/}"
  fi
  local dest="${ARCHIVE}/kentender_v1/${rel}"
  mkdir -p "$(dirname "${dest}")"
  if git ls-files --error-unmatch "${src}" >/dev/null 2>&1; then
    git mv "${src}" "${dest}"
  else
    mv "${src}" "${dest}"
  fi
}

mv_glob() {
  local pattern="$1"
  shopt -s nullglob
  local files=(${pattern})
  shopt -u nullglob
  for f in "${files[@]}"; do
    mv_path "${f}"
  done
}

# Desk pages
for page in std_library std_configurator std_engine std_engine_advanced; do
  mv_path "${KP}/kentender_procurement/page/${page}"
done

# Public assets
if [[ -d "${KP}/public/js/std_library" ]]; then
  mv_path "${KP}/public/js/std_library"
fi
if [[ -d "${KP}/public/js/std_config" ]]; then
  mv_path "${KP}/public/js/std_config"
fi
for f in ${KP}/public/js/std_engine*; do mv_path "$f"; done
mv_path "${KP}/public/js/std_config_workspace.js"
for f in ${KP}/public/css/std_library* ${KP}/public/css/std_config* ${KP}/public/css/std_configurator*; do
  mv_path "$f"
done

# APIs
for f in ${KP}/tender_management/api/std_*.py ${KP}/tender_management/api/works_completion.py; do
  mv_path "$f"
done

# Services (explicit list)
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
  mv_path "${KP}/tender_management/services/${svc}.py"
done

# std_instance
mv_path "${KP}/tender_management/std_instance"

# DocTypes
for dt in ${KP}/kentender_procurement/doctype/std_* ${KP}/kentender_procurement/doctype/tender_std_* ${KP}/kentender_procurement/doctype/tm2_tender_std_*; do
  mv_path "$dt"
done

# Templates
mv_path "${KP}/tender_management/std_templates"

# Seeds
for f in ${KP}/tender_management/seeds/*std* ${KP}/tender_management/seeds/works_master_std*; do
  mv_path "$f"
done
mv_path "${KP}/procurement_planning/seeds/seed_works_stdint_s01.py"

# Patches
for f in ${KP}/patches/std_* ${KP}/patches/stdinst_* ${KP}/patches/std_gov_* ${KP}/patches/std_cfg_*; do
  mv_path "$f"
done

# Backend tests
for f in ${KP}/tender_management/tests/test_std_* ${KP}/tender_management/tests/test_stdinst_* ${KP}/tender_management/tests/test_std_inst_* ${KP}/tender_management/tests/test_std_config_* ${KP}/tender_management/tests/test_std_library_* ${KP}/tender_management/tests/test_std_admin_* ${KP}/tender_management/tests/test_std_gov_* ${KP}/tender_management/tests/test_works_comp_* ${KP}/tender_management/tests/test_r2_008_*; do
  mv_path "$f"
done
for f in ${KP}/setup/tests/test_r*std* ${KP}/procurement_lifecycle/tests/test_r*std*; do
  mv_path "$f"
done
for f in ${KP}/procurement_planning/tests/test_*std* ${KP}/procurement_planning/tests/test_pw4_wizard_document_std_path.py ${KP}/procurement_planning/tests/test_pp2_reg_*std*; do
  mv_path "$f"
done

# kentender_v1: tests, frontend, docs
mv_v1_path "tests/ui/smoke/std-config"
for f in tests/ui/smoke/procurement/std-*; do mv_v1_path "$f"; done
mv_v1_path "frontend/src/modules/std-engine"
mv_v1_path "docs/prompts/std config"
mv_v1_path "docs/prompts/std poc"
mv_v1_path "docs/prompts/std-production-readiness"
mv_v1_path "docs/std prod"

# Cursor rules (bench root — copy if not in git)
for rule in kentender-std-poc-implementation.mdc kentender-std-admin-console-implementation.mdc kentender-std-config-workbench-density.mdc; do
  if [[ -f "${BENCH_ROOT}/.cursor/rules/${rule}" ]]; then
    mkdir -p "${ARCHIVE}/.cursor/rules"
    cp -a "${BENCH_ROOT}/.cursor/rules/${rule}" "${ARCHIVE}/.cursor/rules/${rule}"
    rm -f "${BENCH_ROOT}/.cursor/rules/${rule}"
  fi
done

echo "Archive git mv complete."
