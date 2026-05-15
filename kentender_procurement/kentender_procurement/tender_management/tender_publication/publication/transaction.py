# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0600 — ``PublicationTransactionService``.

Delegates atomic ``publishTender`` to :func:`~kentender_procurement.tender_management.services.publish_tender.publish_tender`
(**TM2 Tender** only). Legacy ``Procurement Tender`` publication path removed.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _effective_actor(actor: str | None) -> str:
	return _strip(actor) or _strip(frappe.session.user) or "Administrator"


class PublicationTransactionService:
	"""Atomic tender publication (PUB-0600) — TM2 implementation."""

	@staticmethod
	def publishTender(tender_code: str, actor: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
		"""Publish via doc 9 §9.6 ``publish_tender`` (TM2)."""
		raw = _strip(tender_code)
		act = _effective_actor(actor)
		if not raw:
			frappe.throw(_("Tender code is required."), exc=frappe.ValidationError)
		tm2 = resolve_tm2_tender_document(raw)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(raw),
				frappe.DoesNotExistError,
			)
		business_tc = canonical_tm2_tender_code(tm2)
		ctx = dict(context or ())
		out = publish_tender(act, business_tc, context=ctx)
		if not out.get("ok"):
			frappe.throw(
				_strip(str(out.get("message") or _("Publication denied."))),
				exc=frappe.ValidationError,
			)
		si_name = _strip(
			str(
				frappe.db.get_value(
					"TM2 Tender STD Binding",
					{"tm2_tender": tm2.name, "is_active": 1},
					"tender_std_instance",
				)
				or ""
			)
		)
		return {
			"ok": True,
			"tender_code": business_tc,
			"tender_std_instance": si_name or None,
			"publication_snapshot": {
				"publication_snapshot_code": out.get("publication_snapshot_code"),
				"tm2_publication_record": out.get("tm2_publication_record"),
			},
			"tender_status": out.get("status") or "Published",
			"tm2_publication_record": out.get("tm2_publication_record"),
		}
