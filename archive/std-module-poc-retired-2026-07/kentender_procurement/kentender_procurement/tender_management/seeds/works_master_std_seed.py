# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-008 — WORKS master STD seed (seed data specification §12).

Ensures the ``STD Template`` record for the PPRA WORKS Building and Civil
Engineering Works STD (``KE-PPRA-WORKS-BLDG-2022-04-POC``) is present,
active, and cleared for tender creation — representing the availability of
the canonical STD version referenced as ``STDTV-WORKS-BUILDING-CIVIL-APR2022``
throughout the WORKS master seed chain.

No standalone ``STD Template Version`` DocType exists in this codebase;
the version business code is stored as a string reference on downstream
documents (``Procurement Journey.std_template_version_ref``,
``TM2 Tender.template_version``). This seed ensures the underlying
``STD Template`` record is ready for those references.

Steps:
  1. Call ``upsert_std_template()`` — idempotent load/update from the on-disk
     POC package; sets ``lifecycle_status = Active`` and
     ``allowed_for_tender_creation = 1`` (manifest declares these).
  2. Assert §16 post-conditions via ``verify_std_template_doc3_section_16()``.
  3. Update ``Procurement Template PTPL-WORKS-OPEN-R2007`` to point
     ``default_std_template`` at the loaded STD Template (if the planning
     template from R2-007 already exists).

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.tender_management.seeds.works_master_std_seed.upsert_works_master_std
"""

from __future__ import annotations

import frappe
from frappe.utils import cint

from kentender_procurement.tender_management.services.std_template_loader import (
    TEMPLATE_CODE,
    upsert_std_template,
)
from kentender_procurement.tender_management.services.std_library_package_projection import (
    backfill_std_template_library_display_metadata,
)
from kentender_procurement.procurement_planning.seeds.works_std_seed_requirements import (
    verify_std_template_doc3_section_16,
)

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

STD_TEMPLATE_CODE = TEMPLATE_CODE  # "KE-PPRA-WORKS-BLDG-2022-04-POC"

# Business version reference used in Journey / TM2 Tender (no standalone DocType).
STD_TEMPLATE_VERSION_REF = "STDTV-WORKS-BUILDING-CIVIL-APR2022"

# Procurement Template created in R2-007; linked to this STD after load.
_PLANNING_TEMPLATE_CODE = "PTPL-WORKS-OPEN-R2007"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def upsert_works_master_std() -> dict:
    """Load/verify WORKS master STD Template and link planning template.

    Idempotent: safe to run multiple times; ``upsert_std_template``
    updates the existing record if the package hash has not changed.

    Returns a result dict with ``ok``, ``action``, ``lifecycle_status``,
    ``allowed_for_tender_creation``, and traceability fields.
    """
    # Step 1 — load / update STD Template from on-disk POC package
    load_result = upsert_std_template()
    backfill_std_template_library_display_metadata(STD_TEMPLATE_CODE)

    # Step 2 — assert §16 post-conditions (raises on failure)
    std_name = verify_std_template_doc3_section_16(STD_TEMPLATE_CODE)

    # Step 3 — link Procurement Template R2-007 → this STD Template
    planning_tpl_name = frappe.db.get_value(
        "Procurement Template", {"template_code": _PLANNING_TEMPLATE_CODE}, "name"
    )
    planning_tpl_linked = False
    if planning_tpl_name:
        current = (
            frappe.db.get_value(
                "Procurement Template", planning_tpl_name, "default_std_template"
            )
            or ""
        )
        if current != std_name:
            frappe.db.set_value(
                "Procurement Template",
                planning_tpl_name,
                "default_std_template",
                std_name,
                update_modified=False,
            )
            planning_tpl_linked = True

    lifecycle_status = (
        frappe.db.get_value("STD Template", std_name, "lifecycle_status") or ""
    )
    atc = cint(
        frappe.db.get_value("STD Template", std_name, "allowed_for_tender_creation") or 0
    )
    tpl_version = (
        frappe.db.get_value("STD Template", std_name, "template_version") or ""
    )

    return {
        "ok": True,
        "action": load_result.get("action"),
        "std_template_code": STD_TEMPLATE_CODE,
        "std_template": std_name,
        "std_version_ref": STD_TEMPLATE_VERSION_REF,
        "template_version": tpl_version,
        "lifecycle_status": lifecycle_status,
        "allowed_for_tender_creation": atc,
        "planning_template_code": _PLANNING_TEMPLATE_CODE,
        "planning_template_linked": planning_tpl_linked,
    }
