# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The supplier's award notice in the public portal (AWD-CHG-001 v0.4 §9
"Supplier notice /supplier/awards/{notice_id}"; plan D14; boards D04, V13,
V14, V22, X01, X02, X11).

Registered on `kt_portal_surfaces` for the `/supplier/awards` prefix. A
supplier user sees only their own organisation's notice — never the
internal record, another recipient's letter or the internal tracker; a
guest is asked to sign in; anything else is the portal's Not found."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

PREFIX = "/supplier/awards"


def resolve(*, path: str, query: dict | None = None, user: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import supplier

	user = user or frappe.session.user
	if not user or user == "Guest":
		return {"verdict": "SIGN_IN", "title": "Sign in", "payload": {}}
	rest = cstr(path).strip("/").split("/")[2:]
	if not rest:
		return {"verdict": "OK", "title": "Award notices", "payload": {"screen": "award-notices", "data": {"notices": supplier.my_notices(user=user)}}}
	try:
		data = supplier.notice_view(notice=rest[0], user=user)
	except frappe.DoesNotExistError:
		return {"verdict": "NOT_FOUND", "title": "Not found", "payload": {"screen": "not-found"}}
	return {"verdict": "OK", "title": data.get("statement") or "Award notice", "payload": {"screen": "award-notice", "data": data}}


def tender_links(*, tender_reference: str, user: str) -> list[dict[str, str]]:
	"""The supplier's own award notices for this tender, on the Tender page."""
	from kentender_procurement.award.services import supplier

	if not user or user == "Guest":
		return []
	return [{"label": "Award notice", "value": n["result"], "href": f"{PREFIX}/{n['notice']}", "text": n["label"]} for n in supplier.my_notices(user=user)
		if n["tender_reference"] == tender_reference and n["current"]]
