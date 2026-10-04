# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`SupersedeSTDRelease`, `WithdrawSTDRelease`,
`ListTendersAffectedBySTDRelease` (STD-TPL-IMP-001 v1.0 §6, §9) and the site
switch (owner decision OD5).

Deployment-only commands that name the release owner (owner ruling R5).
Supersession needs no reason; withdrawal needs a reason, actor and time,
with an optional successor. Each transition writes an audit event carrying
the affected-Tender projection in the same transaction. No transition
rewrites a Tender Version, document, publication or Published Bid
Definition, deletes an asset, or rebinds a Tender.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.services import access, runtime

DOCTYPE = "Installed STD Release"


def affected_tenders(release_id: str) -> dict[str, Any]:
	if not frappe.db.table_exists("Tender") or not frappe.get_meta("Tender").has_field("template_release_id"):
		return {"unpublished": [], "published": [], "unpublished_count": 0, "published_count": 0}
	rows = frappe.get_all("Tender", filters={"template_release_id": release_id}, fields=["name", "tender_reference", "published_at"], order_by="creation asc", limit_page_length=0)
	unpublished = [{"tender": r.name, "reference": r.tender_reference} for r in rows if not r.published_at]
	published = [{"tender": r.name, "reference": r.tender_reference} for r in rows if r.published_at]
	return {"unpublished": unpublished, "published": published, "unpublished_count": len(unpublished), "published_count": len(published)}


def list_tenders_affected(release_id: str, *, user: str | None = None) -> dict[str, Any]:
	access.require_reader(user)
	runtime.release_doc(release_id)
	return {"outcome": "OK", "release_id": release_id, **affected_tenders(release_id)}


def _audit(release_id: str, action: str, metadata: dict[str, Any]) -> None:
	from kentender_core.services.audit_event_service import log_audit_event

	log_audit_event(event_type="STD Release", entity="STD Templates", document_type=DOCTYPE, document_name=release_id, action=action, metadata=metadata)


def supersede(release_id: str, release_owner: str, successor_release_id: str = "") -> dict[str, Any]:
	"""`bench --site <site> execute kentender_procurement.std_templates.services.lifecycle.supersede --kwargs ...`"""
	owner = cstr(release_owner).strip()
	if not owner:
		frappe.throw("Name the release owner.")
	release = runtime.release_doc(release_id)
	if release.lifecycle_status != "Available":
		fail("STD_RELEASE_NOT_AVAILABLE", "Only an Available release can be superseded.", identity=release.name)
	if successor_release_id:
		successor = runtime.release_doc(successor_release_id)
		if successor.template_key != release.template_key or successor.name == release.name:
			frappe.throw("The successor must be another release of the same Tender format.")
	release.lifecycle_status = "Superseded"
	release.superseded_by_release_id = successor_release_id or None
	release.superseded_at = now_datetime()
	release.superseded_by_actor = owner
	release.flags.kt_std_lifecycle = True
	release.save(ignore_permissions=True)
	affected = affected_tenders(release.name)
	_audit(release.name, "Superseded", {"release_owner": owner, "successor_release_id": successor_release_id, "affected": affected})
	frappe.db.commit()
	return {"ok": True, "release_id": release.name, "lifecycle_status": release.lifecycle_status, "affected": affected}


def withdraw(release_id: str, reason: str, release_owner: str, successor_release_id: str = "") -> dict[str, Any]:
	"""`bench --site <site> execute kentender_procurement.std_templates.services.lifecycle.withdraw --kwargs ...`"""
	owner = cstr(release_owner).strip()
	reason = cstr(reason).strip()
	if not owner or len(reason) < 10:
		frappe.throw("Name the release owner and state the withdrawal reason (at least 10 characters).")
	release = runtime.release_doc(release_id)
	if release.lifecycle_status not in ("Available", "Superseded"):
		fail("STD_RELEASE_NOT_AVAILABLE", "Only an Available or Superseded release can be withdrawn.", identity=release.name)
	if successor_release_id:
		successor = runtime.release_doc(successor_release_id)
		if successor.template_key != release.template_key or successor.name == release.name:
			frappe.throw("The successor must be another release of the same Tender format.")
	release.lifecycle_status = "Withdrawn"
	release.withdrawal_reason = reason
	release.withdrawn_by = owner
	release.withdrawn_at = now_datetime()
	release.withdrawal_successor_release_id = successor_release_id or None
	release.flags.kt_std_lifecycle = True
	release.save(ignore_permissions=True)
	affected = affected_tenders(release.name)
	_audit(release.name, "Withdrawn", {"release_owner": owner, "reason": reason, "successor_release_id": successor_release_id, "affected": affected})
	frappe.db.commit()
	return {"ok": True, "release_id": release.name, "lifecycle_status": release.lifecycle_status, "affected": affected}


def switch(release_id: str, state: str, actor: str) -> dict[str, Any]:
	"""Owner decision OD5: "Template release is purely an on and off switch on
	an affected site." Off stops new Tenders starting on the release; Tenders
	already started on it continue. `make std-release-switch SITE=<site>
	STATE=Off|On [RELEASE_ID=<id>] [ACTOR=<name>]`."""
	wanted = cstr(state).strip().capitalize()
	if wanted not in ("On", "Off"):
		frappe.throw("Switch a release On or Off.")
	actor = cstr(actor).strip()
	if not actor:
		frappe.throw("Name who is switching the release.")
	release = runtime.release_doc(release_id)
	if release.lifecycle_status != "Available":
		fail("STD_RELEASE_NOT_AVAILABLE", "Only a current release can be switched; a superseded or withdrawn release stays as it is.", identity=release.name)
	if release.site_switch == wanted:
		return {"ok": True, "release_id": release.name, "site_switch": wanted, "changed": False}
	previous = release.site_switch
	release.site_switch = wanted
	release.switched_by = actor
	release.switched_at = now_datetime()
	release.flags.kt_std_switch = True
	release.save(ignore_permissions=True)
	_audit(release.name, f"Switched {wanted}", {"actor": actor, "from": previous, "to": wanted})
	frappe.db.commit()
	return {"ok": True, "release_id": release.name, "site_switch": wanted, "changed": True}
