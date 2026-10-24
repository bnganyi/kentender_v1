# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.21 §7.5 — `GetTenderCancellationRecoveryBasis.v1`: the Tender owner's verified answer to Requisitions' question 'may the
allowance this cancelled Tender drew be restored?'.

Registered on `kt_tender_cancellation_recovery_basis` (`kentender_core.services.cancellation_recovery_contract`); Requisitions asks through
that seam and never imports this module. The answer is taken at the moment of consequence, under the same locks the cancellation itself
takes — the Tender root, then Award's case (a locking read) — so a cancellation or a notice issue racing the recovery is waited for and
seen. Caller assertion, a cached projection and a null lookup are never positive:

- `positive`    the Tender is Cancelled by exactly this cancellation (its digest and time are returned); the lineage it consumed — Requisition,
                Version, handoff and the drawdown-line → reservation mapping of its own approved snapshot — is returned for Requisitions to
                compare with the lineage it registered; and Award, which owns the pre-award-notification guard and any downstream use,
                says no notice was issued or is being issued and no contracting package was prepared or delivered;
- `negative`    Award proves a notice or a package exists, or the Tender is not the cancelled Tender it was registered as: the recovery needs
                attention and nothing is restored;
- `unavailable` Award could not say, or notices are being issued: the recovery stays Pending and is retried.

Contract Management is not asked and not imported (it must run without the tendering apps): a contract for a Tender's award can exist only
after Award has issued its notices and delivered its package, which is exactly what Award's disposition reports, and Budget independently
refuses any reservation that has a commitment."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import cancellation_recovery_contract as seam
from kentender_procurement.tenders.services import award_seam, digest, envelope, snapshot as snap


class Provider:
	def recovery_basis(self, *, tender: str, cancellation: str, recovery_id: str) -> dict[str, Any]:
		return recovery_basis(tender=tender, cancellation=cancellation, recovery_id=recovery_id)


def provider() -> Provider:
	return Provider()


def _answer(verdict: str, reason: str, **facts) -> dict[str, Any]:
	return {"verdict": verdict, "reason": reason, "evidence": facts.pop("evidence", []), **facts}


def recovery_basis(*, tender: str, cancellation: str, recovery_id: str) -> dict[str, Any]:
	if not tender or not frappe.db.exists("Tender", tender):
		return _answer(seam.NEGATIVE, "The Tender is not recorded.")
	# Lock order: the Tender root, then Award's case (inside `downstream_disposition`), exactly as `cancel_tender` takes them.
	root = envelope.locked("Tender", tender)
	if root.overall_status != "Cancelled" or cstr(root.cancellation) != cstr(cancellation):
		return _answer(seam.NEGATIVE, "The Tender is not cancelled by the cancellation this recovery was registered for.", tender_status=cstr(root.overall_status))
	record = frappe.db.get_value(
		"Tender Cancellation", cancellation, ["name", "cancellation_digest", "decided_at", "ground", "tender"], as_dict=True,
	)
	if not record or cstr(record.tender) != root.name:
		return _answer(seam.NEGATIVE, "The cancellation record does not belong to this Tender.")

	disposition = award_seam.downstream_disposition(tender)
	if not disposition.get("known"):
		return _answer(seam.UNAVAILABLE, "Award could not confirm whether any notice was issued. The recovery will be tried again.", evidence=[{"owner": "Award", "state": "unknown"}])
	notification = cstr(disposition.get("notification_status"))
	if notification in ("Issue in progress", "Unknown"):
		return _answer(seam.UNAVAILABLE, "Award notices are being issued or their state is unknown. The recovery will be tried again.", evidence=[{"owner": "Award", "state": notification}])
	if notification != "Not issued" or disposition.get("package_delivered") or cstr(disposition.get("package_status")):
		return _answer(
			seam.NEGATIVE, "Award notices or a contracting package exist for this Tender, so its allowance is not restored automatically.",
			evidence=[{"owner": "Award", "notification_status": notification, "package_status": cstr(disposition.get("package_status")), "case": cstr(disposition.get("case"))}],
		)

	version_name = root.approved_version or root.current_version
	if not version_name:
		return _answer(seam.UNAVAILABLE, "The Tender's approved Version could not be read.")
	loaded = snap.load(frappe.get_doc("Tender Version", version_name))
	sources = [
		{"drawdown_line_id": cstr(line.get("drawdown_line_id")), "reservation_id": cstr(line.get("reservation_id")), "plan_item_line_id": cstr(line.get("plan_item_line_id"))}
		for line in loaded.get("drawdown_lines") or [] if line.get("drawdown_line_id")
	]
	evidence = [
		{"owner": "Tenders", "cancellation": record.name, "cancellation_digest": cstr(record.cancellation_digest)},
		{"owner": "Award", "notification_status": notification, "case": cstr(disposition.get("case")), "source": cstr(disposition.get("source"))},
	]
	basis = {
		"tender": root.name, "cancellation": record.name, "cancellation_digest": cstr(record.cancellation_digest), "cancelled_at": cstr(record.decided_at),
		"lineage": {"requisition": cstr(root.requisition), "requisition_version": cstr(root.requisition_version), "handoff": cstr(root.requisition_handoff), "sources": sources},
		"award": {"notification_status": notification, "case": cstr(disposition.get("case"))},
	}
	return _answer(seam.POSITIVE, "", evidence=evidence, revision=digest.sha256_hex(basis), **basis)
