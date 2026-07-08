#!/usr/bin/env bash
# Fail if active STD POC surfaces remain outside archive + approved stubs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KP="${REPO_ROOT}/kentender_procurement/kentender_procurement"
ARCHIVE="${REPO_ROOT}/archive/std-module-poc-retired-2026-07"

if [[ ! -d "${ARCHIVE}" ]]; then
  echo "verify-std-archived: missing archive root ${ARCHIVE}" >&2
  exit 1
fi

# Patterns that must NOT appear in active procurement app (except stubs/placeholder).
FORBIDDEN=(
  'std-library'
  'std-configurator'
  'std_engine_advanced'
  'std_configurator_service'
  'std_library_templates'
  'std_library_shell'
  'std_configurator_page'
  'tender_management/std_instance'
  'tender_management/works_completion'
)

ALLOW=(
  'std-module-retired'
  'std_template_handoff_resolution'
  'std_template_loader'
  'works_master_std_seed'
  'planning_tender_handoff_xmv'
  'tm2_std_adapter'
  'std_template_governance_seed'
  'STD_MODULE_RETIRED'
  'std_module_retired'
)

fail=0
for pat in "${FORBIDDEN[@]}"; do
  while IFS= read -r hit; do
    [[ -z "${hit}" ]] && continue
    allowed=0
    for a in "${ALLOW[@]}"; do
      if [[ "${hit}" == *"${a}"* ]]; then
        allowed=1
        break
      fi
    done
    if [[ "${allowed}" -eq 0 ]]; then
      echo "verify-std-archived: forbidden active hit for '${pat}': ${hit}" >&2
      fail=1
    fi
  done < <(rg -l "${pat}" "${KP}" --glob '!archive/**' 2>/dev/null || true)
done

manifest_count=$(find "${ARCHIVE}" -type f ! -name 'ARCHIVE_MANIFEST.md' ! -name 'README.md' ! -name 'SNAPSHOT_COMMIT.txt' | wc -l)
if [[ "${manifest_count}" -lt 300 ]]; then
  echo "verify-std-archived: expected 300+ archived files, found ${manifest_count}" >&2
  fail=1
fi

if [[ "${fail}" -ne 0 ]]; then
  exit 1
fi

echo "verify-std-archived: OK (${manifest_count} archived files, no forbidden active STD surfaces)"
