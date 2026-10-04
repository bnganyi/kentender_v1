# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Calling the shared Proceedings service for one opening case (BOP-CHG-001
v0.10 §7.1 binding register). Each call carries the Proceeding's current
version and a key derived from the Bid Opening command's own key, so a
replayed Bid Opening command never writes a second Proceedings fact."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.bid_opening.services.prc_owner import OWNER_TYPE
from kentender_procurement.proceedings.services.owners import SYSTEM_ACTOR  # noqa: F401  (re-exported)


def ref(case: str) -> dict[str, Any]:
	version = frappe.db.get_value("Proceeding", {"owner_key": f"{OWNER_TYPE}:{case}"}, "record_version")
	return {"owner_type": OWNER_TYPE, "owner_id": case, "expected_version": cint(version)}


def owner(case: str) -> dict[str, str]:
	return {"owner_type": OWNER_TYPE, "owner_id": case}


def key(base: str, step: str) -> str:
	return f"{base}:{step}"


def state(case: str) -> str:
	return frappe.db.get_value("Proceeding", {"owner_key": f"{OWNER_TYPE}:{case}"}, "state") or ""
