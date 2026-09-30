# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The small lifecycle (EVL-CHG-001 v0.4 §7.1): Preparing, Reviewing,
Signing, Report sent, No evaluation required, Cancelled. Checking, waiting,
overdue and suspended are conditions, never states.

`roster_changed` applies §3 and §5.5: "A roster change before report
delivery withdraws that report version from signing and requires a new
version signed by the current roster." After delivery the delivered report
stays and the correction process applies instead."""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import records

REPORT = "Evaluation Report Version"


def signing_report(doc) -> str | None:
	return frappe.db.get_value(REPORT, {"evaluation_case": doc.name, "state": "Signing"}, "name")


def withdraw_signing(doc, *, kind: str, reason: str, idempotency_key: str, actor: str | None) -> str | None:
	"""End signature collection for the current version (old signatures stay
	historical) and return the case to Reviewing. `actor` is the person whose
	recorded action caused it; None when Proceedings supersedes the version
	itself (a cancellation aborts the whole record)."""
	name = signing_report(doc)
	if not name:
		return None
	from kentender_procurement.bid_evaluation.services import prc, prc_owner
	from kentender_procurement.proceedings.services import record_versions

	report = frappe.get_doc(REPORT, name)
	if report.record_version_reference and actor:
		with prc_owner.acting(doc.name):
			record_versions.supersede_record(**prc.ref(doc), record_version=report.record_version_reference, reason=cstr(reason),
				idempotency_key=prc.key(idempotency_key, f"supersede-{name}"), actor=actor)
	report.state, report.supersession_kind, report.supersession_reason = "Superseded", kind, cstr(reason)
	from kentender_procurement.bid_evaluation.services import clock

	report.superseded_at = clock.now()
	records.save(report)
	if doc.state == "Signing":
		records.bump(doc, state="Reviewing")
	return name


def roster_changed(doc, *, reason: str, idempotency_key: str, actor: str) -> str | None:
	return withdraw_signing(doc, kind="Roster change", reason=reason, idempotency_key=idempotency_key, actor=actor)
