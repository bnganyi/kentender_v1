# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright journey helpers for WORKS master package lifecycle transitions."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, today

from kentender_procurement.procurement_planning.api.package_release import (
	mark_pp_package_ready_for_release,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.release import (
	ensure_planning_release,
)


def ensure_works_master_package_schedule(
	package_code: str = PKG_CODE,
) -> dict[str, Any]:
	"""Set planned schedule dates required before submit/readiness on WORKS master package."""
	if not frappe.db.exists("Procurement Package", package_code):
		return {"ok": False, "error_code": "NOT_FOUND", "package_code": package_code}
	frappe.db.set_value(
		"Procurement Package",
		package_code,
		{"schedule_start": today(), "schedule_end": add_days(today(), 30)},
		update_modified=False,
	)
	frappe.db.commit()
	return {"ok": True, "package_code": package_code}


def get_works_master_package_status(
	package_code: str = PKG_CODE,
) -> dict[str, Any]:
	status = frappe.db.get_value("Procurement Package", package_code, "status") or ""
	return {"ok": True, "package_code": package_code, "status": status}


def approve_works_master_package_for_ui_journey(
	package_code: str = PKG_CODE,
	*,
	actor: str = "planning.reviewer@moh.test",
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.api.workflow import approve_package

	frappe.set_user(actor)
	out = approve_package(package_code)
	frappe.db.commit()
	return {"ok": True, **out}


def mark_works_master_package_ready_for_release(
	package_code: str = PKG_CODE,
	*,
	actor: str = "planning.reviewer@moh.test",
) -> dict[str, Any]:
	"""Approved + passing readiness → Ready for Release (no Package Detail UI action)."""
	frappe.set_user(actor)
	out = mark_pp_package_ready_for_release(package_code=package_code)
	frappe.db.commit()
	return out


def release_works_master_package_for_ui_journey(
	package_code: str = PKG_CODE,
) -> dict[str, Any]:
	"""Ready for Release → Released using canonical WORKS master seed release step."""
	del package_code
	out = ensure_planning_release()
	frappe.db.commit()
	return {"ok": True, **out}
