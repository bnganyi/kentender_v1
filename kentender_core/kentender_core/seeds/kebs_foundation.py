"""Canonical KEBS foundation fixture — shared Configuration & Governance data.

The Kenya Bureau of Standards first slice appears as an approved, shared test
fact across the Departmental Needs, Procurement Planning, Requisitions and
Tender Preparation contracts. It is published **once, here**, and reused by
every module, so that no module invents its own KEBS records and no two modules
disagree about what KEBS is.

Records owned by this fixture:

| Record | Identity |
|---|---|
| Procuring Entity | `PE-KEBS` — Kenya Bureau of Standards |
| Organisation Unit | `OU-KEBS-ICT` — Coast Region — Administration and ICT |
| Financial Year | `FY-2026-2027` |
| PE Fiscal Year Context | `CTX-KEBS-2026-2027`, Active |

Rules this module exists to enforce:

- **Never created silently by a consuming module.** Departmental Needs,
  Planning and the rest read these records; they never write them. A module
  that creates its own KEBS entity would make its acceptance criteria pass
  against data it invented.
- **Never installed automatically.** There is no hook, patch or migrate step.
  Installation is an explicit act.
- **Never installed on production.** `install()` and `remove()` refuse unless
  the site is in developer mode, has `allow_tests`, or is running tests —
  the same guard the platform seeds use.
- **Absence fails clearly.** `verify()` names exactly which records are
  missing, so a consumer can say what to install rather than guessing.
"""

from __future__ import annotations

from typing import Any

import frappe

PE = "PE-KEBS"
PE_LEGAL_NAME = "Kenya Bureau of Standards"
PE_ENTITY_TYPE = "State Corporation"
PE_CURRENCY = "KES"

OU = "OU-KEBS-ICT"
OU_NAME = "Coast Region — Administration and ICT"

FY = "FY-2026-2027"
FY_LABEL = "2026/27"
FY_START = "2026-07-01"
FY_END = "2027-06-30"
FY_TIMEZONE = "Africa/Nairobi"

CONTEXT = "CTX-KEBS-2026-2027"

FIXTURE_NAMESPACE = "KENTENDER_KEBS_FOUNDATION"

#: What a consumer must find before it may build KEBS records of its own.
REQUIRED = (
	("Procuring Entity", PE),
	("Organisation Unit", OU),
	("Financial Year", FY),
	("PE Fiscal Year Context", CONTEXT),
)


def _guard() -> None:
	"""Refuse anywhere that is not explicitly a test or development site."""
	if frappe.in_test:
		return
	if frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"The KEBS foundation fixture is explicit test and demo data and refuses to "
		"run here. Enable developer_mode or allow_tests on a non-production site."
	)


def verify() -> dict[str, Any]:
	"""Report which canonical records are present. Never writes."""
	missing = [f"{doctype} {name}" for doctype, name in REQUIRED if not frappe.db.exists(doctype, name)]
	installed = not missing
	details: dict[str, Any] = {"installed": installed, "missing": missing}
	if installed:
		details["financial_year_status"] = frappe.db.get_value("Financial Year", FY, "record_status")
		details["context_status"] = frappe.db.get_value(
			"PE Fiscal Year Context", CONTEXT, "context_status"
		)
		details["entity_status"] = frappe.db.get_value("Procuring Entity", PE, "status")
		# A record that exists but is not usable is as good as absent to a
		# consumer, so say so rather than reporting a bare "installed".
		details["usable"] = (
			details["financial_year_status"] == "Available"
			and details["context_status"] == "Active"
			and details["entity_status"] == "Active"
		)
	return details


def require_installed() -> None:
	"""Fail with an actionable message when the canonical fixture is absent.

	Consumers call this instead of testing for the records themselves, so every
	module reports the same missing prerequisite the same way.
	"""
	state = verify()
	if state["installed"] and state.get("usable"):
		return
	problem = (
		f"missing: {', '.join(state['missing'])}"
		if state["missing"]
		else "present but not usable (the entity, financial year or context is not active)"
	)
	frappe.throw(
		f"The canonical KEBS foundation fixture is not installed ({problem}). "
		"Install it with "
		"`bench --site <site> execute kentender_core.seeds.kebs_foundation.install "
		"--kwargs \"{'commit':True}\"`. It is shared Configuration & Governance "
		"test data and is never created by a consuming module."
	)


def _unit_type() -> str:
	for candidate in ("OUT-DIRECTORATE", "OUT-STATE-DEPT", "OUT-COUNTY-DEPT"):
		if frappe.db.exists("Organisation Unit Type", candidate):
			return candidate
	frappe.throw(
		"No Organisation Unit Type is configured; the KEBS foundation fixture "
		"does not invent one."
	)


def install(*, commit: bool = False) -> dict[str, Any]:
	"""Publish the canonical KEBS records. Idempotent."""
	_guard()
	created: list[str] = []

	if not frappe.db.exists("Procuring Entity", PE):
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": PE,
				"legal_name": PE_LEGAL_NAME,
				"entity_name": PE_LEGAL_NAME,
				"short_name": "KEBS",
				"entity_type": PE_ENTITY_TYPE,
				"reporting_currency": PE_CURRENCY,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		created.append(PE)
	else:
		frappe.db.set_value("Procuring Entity", PE, "status", "Active", update_modified=False)

	if not frappe.db.exists("Financial Year", FY):
		doc = frappe.get_doc(
			{
				"doctype": "Financial Year",
				"start_year": 2026,
				"label": FY_LABEL,
				"start_date": FY_START,
				"end_date": FY_END,
				"timezone": FY_TIMEZONE,
				"record_status": "Available",
			}
		)
		doc.name = FY
		doc.insert(ignore_permissions=True)
		created.append(FY)
	else:
		# The year may already exist as Draft; publishing it is part of making
		# the canonical context usable.
		frappe.db.set_value("Financial Year", FY, "record_status", "Available", update_modified=False)

	if not frappe.db.exists("Organisation Unit", OU):
		frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": OU,
				"unit_name": OU_NAME,
				"unit_type": _unit_type(),
				"procuring_entity": PE,
				"status": "Active",
				"fixture_namespace": FIXTURE_NAMESPACE,
			}
		).insert(ignore_permissions=True)
		created.append(OU)
	else:
		frappe.db.set_value("Organisation Unit", OU, "status", "Active", update_modified=False)

	if not frappe.db.exists("PE Fiscal Year Context", CONTEXT):
		frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": PE,
				"financial_year": FY,
				"context_status": "Active",
				"active_from": f"{FY_START} 00:00:00",
				"active_to": f"{FY_END} 23:59:59",
			}
		).insert(ignore_permissions=True)
		created.append(CONTEXT)
	else:
		frappe.db.set_value(
			"PE Fiscal Year Context", CONTEXT, "context_status", "Active", update_modified=False
		)

	if commit:
		frappe.db.commit()
	return {"created": created, **verify()}


def remove(*, commit: bool = False) -> dict[str, Any]:
	"""Remove the canonical records, newest dependency first.

	Refuses while any record still depends on them, rather than cascading: a
	fixture shared by four modules must not silently delete another module's
	work.
	"""
	_guard()
	dependants = frappe.get_all(
		"Departmental Need", filters={"procuring_entity": PE}, pluck="name"
	) if frappe.db.exists("DocType", "Departmental Need") else []
	if dependants:
		frappe.throw(
			f"{len(dependants)} Departmental Need records still reference {PE}. "
			"Reset the consuming module's profile before removing the foundation fixture."
		)
	removed = []
	for doctype, name in reversed(REQUIRED):
		if doctype == "Financial Year":
			# Shared with every other entity's contexts; never removed here.
			continue
		if frappe.db.exists(doctype, name):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			removed.append(name)
	if commit:
		frappe.db.commit()
	return {"removed": removed, **verify()}
