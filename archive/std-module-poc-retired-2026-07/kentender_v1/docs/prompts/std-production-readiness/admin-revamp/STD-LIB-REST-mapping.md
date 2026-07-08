# Pack REST shapes → Frappe whitelist mapping (Desk delivery)

**Purpose:** Doc **2** describes canonical **`/api/std-engine/...`** HTTP shapes. This bench implements **`kentender_procurement`** **whitelisted** methods consumed via **`frappe.call`** from Desk JS (`std_library_api.js`, adapters). There is **no** separate public REST router at those paths unless product adds one later.

**Implementation review:** [`STD-LIB-0700_implementation_review_report.md`](STD-LIB-0700_implementation_review_report.md)

| Pack-style route (conceptual) | Python module | Whitelist method(s) |
|-------------------------------|---------------|----------------------|
| `GET /api/std-engine/action-availability` | `std_library_action_availability.py` | `get_std_library_action_availability` |
| `GET /api/std-engine/library/summary` | `std_library_summary.py` | `get_std_library_summary_counts` |
| `GET /api/std-engine/library/templates` | `std_library_templates.py` | `get_std_library_templates` |
| `GET /api/std-engine/library/templates/{version_code}` | `std_library_templates.py` | `get_std_library_template_detail` |
| `GET .../package-sources` | `std_library_import_wizard.py` | `get_std_library_package_sources` |
| `POST .../select-package` | `std_library_import_wizard.py` | `select_std_library_import_package` |
| `POST .../source-evidence` | `std_library_import_wizard.py` | `save_std_library_source_evidence` |
| `GET .../detected-structure` | `std_library_import_wizard.py` | `get_std_library_detected_structure` |
| `POST .../validate` (import) | `std_library_import_wizard.py` | `run_std_library_import_validation` |
| `GET .../validation` (import) | `std_library_import_wizard.py` | `get_std_library_import_validation` |
| `POST .../generate-bundle-preview` | `std_library_import_wizard.py` | `generate_std_library_bundle_preview` |
| `GET .../bundle-preview` (import) | `std_library_import_wizard.py` | `get_std_library_bundle_preview` |
| `GET .../placeholder-list` | `std_library_import_wizard.py` | `get_std_library_placeholder_list` |
| `GET .../final-review` | `std_library_import_wizard.py` | `get_std_library_import_final_review` |
| `POST .../submit-review` | `std_library_import_wizard.py` | `submit_std_library_import_review` |
| `POST .../activate` (import) | `std_library_import_wizard.py` | `activate_std_library_import` |
| `GET .../validation-summary` (library) | `std_library_import_wizard.py` | `get_std_library_validation_summary` |
| `POST .../validate` (library-wide) | `std_library_import_wizard.py` | `run_std_library_validation` |
| `POST .../source-documents` | `std_library_import_wizard.py` | `register_std_library_source_document` |

Detail payloads (`detail.validation`, `detail.bundle_preview`, `detail.usage`, etc.) are composed inside **`get_std_library_template_detail`** rather than separate HTTP resources per sub-tab.

**Calling convention:** `frappe.call({ method: 'kentender_procurement.tender_management.api.<module>.<function>', args: { ... } })` (exact path per Frappe app layout).
