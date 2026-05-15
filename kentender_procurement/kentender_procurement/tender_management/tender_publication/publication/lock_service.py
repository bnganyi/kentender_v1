# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0610 — ``PublicationLockService`` (pack §14).

Facades ``StdPublicationLockService`` for instance-level rules and adds tender-aware gates,
``markPublishedLocked`` binding to a **Final** ``Tender Publication Snapshot``, and stable
``POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED`` audit via ``StdAuthorizationService`` paths.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.std_instance.authorization import StdAuthorizationService
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.publication_lock import (
	ADDENDUM_REQUIRED_INSTANCE_STATUSES,
	EDITABLE_INSTANCE_STATUSES,
	StdPublicationLockService,
)


def _strip(value: str | None) -> str:
	return (value or "").strip()


class PublicationLockService:
	"""Post-publication immutability and addendum-required denials (pack §14)."""

	@staticmethod
	def _resolve_instance_and_tender(tender_code_or_instance_code: str) -> tuple[str, str | None]:
		"""Return ``(instance_name, tender_link)`` where ``tender_link`` is TM2 name or PT name when present."""
		c = _strip(tender_code_or_instance_code)
		if not c:
			frappe.throw(_("Tender or instance code is required."), exc=frappe.ValidationError)
		if frappe.db.exists("Tender STD Instance", c):
			row = frappe.db.get_value(
				"Tender STD Instance",
				c,
				["tm2_tender"],
				as_dict=True,
			) or {}
			tm2_id = _strip(row.get("tm2_tender"))
			tn = tm2_id or None
			return c, tn
		tm2 = resolve_tm2_tender_document(c)
		if tm2:
			si = TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2.name)
			if not si:
				frappe.throw(
					_("No Tender STD Instance is bound to TM2 Tender {0}.").format(tm2.name),
					frappe.ValidationError,
				)
			return si.name, tm2.name
		frappe.throw(
			_("{0} is not a TM2 Tender or Tender STD Instance.").format(c),
			frappe.DoesNotExistError,
		)

	@staticmethod
	def assertNotPublishedLocked(tender_code_or_instance_code: str) -> None:
		"""Raise when the tender is published or the instance is in a post-publication lock state."""
		inst, tender = PublicationLockService._resolve_instance_and_tender(tender_code_or_instance_code)
		st = _strip(frappe.db.get_value("Tender STD Instance", inst, "instance_status"))
		tender_st = None
		if tender:
			if frappe.db.exists("TM2 Tender", tender):
				tender_st = _strip(frappe.db.get_value("TM2 Tender", tender, "status"))
		if tender_st == "Published" or st in ADDENDUM_REQUIRED_INSTANCE_STATUSES:
			PublicationLockService.assertAddendumRequired(inst, "direct_mutation")

	@staticmethod
	def assertCanEditPrePublication(instance_code: str, actor: str | None = None) -> None:
		"""Pack §14 — allow edits only in pre-publication editable phases for ``actor``."""
		ic = _strip(instance_code)
		if not ic or not frappe.db.exists("Tender STD Instance", ic):
			frappe.throw(_("Tender STD Instance {0} does not exist.").format(ic), frappe.DoesNotExistError)
		st = _strip(frappe.db.get_value("Tender STD Instance", ic, "instance_status"))
		if st in ADDENDUM_REQUIRED_INSTANCE_STATUSES:
			PublicationLockService.assertAddendumRequired(ic, "pre_publication_edit_gate")
		if st not in EDITABLE_INSTANCE_STATUSES:
			frappe.throw(
				_("STD Instance cannot be edited while status is {0}.").format(st or "Unknown"),
				title=_("STD Instance Locked"),
			)
		prev = frappe.session.user
		act = _strip(actor) or prev
		if act:
			frappe.set_user(act)
		try:
			StdAuthorizationService.assert_can_edit_draft_instance(
				ic,
				attempted_change="pre_publication_edit",
			)
		finally:
			frappe.set_user(prev)

	@staticmethod
	def assertAddendumRequired(instance_code: str, attempted_change: str) -> None:
		"""Deny direct mutation; raises with addendum guidance and publication audit (pack §14)."""
		ic = _strip(instance_code)
		if not ic:
			frappe.throw(_("Instance code is required."), exc=frappe.ValidationError)
		StdAuthorizationService.assert_can_mutate_published(
			ic,
			attempted_change=_strip(attempted_change) or "unknown_change",
		)

	@staticmethod
	def markPublishedLocked(
		instance_code: str,
		publication_snapshot_code: str,
		actor: str | None = None,
		*,
		ignore_permissions: bool = True,
	) -> Document:
		"""Transition instance to **Published Locked** only when bound to the given Final tender snapshot."""
		ic = _strip(instance_code)
		psc = _strip(publication_snapshot_code)
		if not ic or not frappe.db.exists("Tender STD Instance", ic):
			frappe.throw(_("Tender STD Instance {0} does not exist.").format(ic), frappe.DoesNotExistError)
		if not psc or not frappe.db.exists("Tender Publication Snapshot", psc):
			frappe.throw(
				_("Tender Publication Snapshot {0} does not exist.").format(psc or "—"),
				frappe.DoesNotExistError,
			)
		pub = frappe.get_doc("Tender Publication Snapshot", psc)
		if _strip(pub.tender_std_instance) != ic:
			frappe.throw(
				_("Publication snapshot {0} does not belong to instance {1}.").format(psc, ic),
				exc=frappe.ValidationError,
			)
		if _strip(pub.snapshot_status) != "Final":
			frappe.throw(
				_("Publication snapshot {0} must be Final before publication lock.").format(psc),
				exc=frappe.ValidationError,
			)
		act = _strip(actor) or _strip(frappe.session.user) or "Administrator"
		return StdPublicationLockService.lock_for_publication(
			ic,
			user=act,
			ignore_permissions=ignore_permissions,
		)
