# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The only door from Award to the facts it does not own (AWD-CHG-001 v0.4 §3;
plan D4, OD-B).

One interface, two providers, registered on `kt_award_source_providers`:

- `Evaluation` wraps the published seams (Bid Evaluation, Tenders, Bid
  Submission — plan D5). This is the provider every real award uses.
- `Synthetic` (`award/test_services/sources.py`) serves the §10.1/§13 fixture
  facts so Award's own tests and browser worlds need no tender, bid, opening
  or evaluation. It answers only on a test environment, and a case built on
  it says so (`source_kind`).

After receipt a case reads its own frozen snapshot of the report; live calls
happen only for live facts (validity, cancellation, audience, contacts,
authority). An unavailable source is reported as unavailable, never as a
negative fact (§5.1, §7)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

EVALUATION = "Evaluation"
SYNTHETIC = "Synthetic"


class SourceUnavailable(Exception):
	"""A live fact could not be read (status service or seam failure)."""


def providers() -> dict[str, Any]:
	out = {}
	for path in frappe.get_hooks("kt_award_source_providers") or []:
		provider = frappe.get_attr(path)()
		if provider is not None:
			out[provider.kind] = provider
	return out


def provider(kind: str):
	found = providers().get(cstr(kind) or EVALUATION)
	if found is None:
		raise SourceUnavailable(f"No {kind} source is available on this site.")
	return found


def for_case(doc):
	return provider(doc.source_kind or EVALUATION)


class EvaluationSource:
	"""The real provider over the owners' published seams."""

	kind = EVALUATION

	# -- the delivered report (AWD-IF-01) --------------------------------------
	def delivered_report(self, delivery: str) -> dict[str, Any] | None:
		from kentender_procurement.bid_evaluation.services import award_seam

		snapshot = award_seam.delivered_report(delivery)
		if snapshot:
			try:
				facts = self.tender_facts(snapshot["tender"]) or {}
				validity = self.validity(snapshot["tender"])
			except SourceUnavailable:
				facts, validity = {}, {"validity_end": None, "rule": None, "unavailable": True}
			snapshot.update(tender_title=facts.get("title", ""), lot=facts.get("lot", "1"), procuring_entity=facts.get("procuring_entity", ""),
				award_method=facts.get("award_method", ""), validity=validity)
		return snapshot

	def pending_deliveries(self) -> list[str]:
		from kentender_procurement.bid_evaluation.services import award_seam

		return award_seam.pending_deliveries()

	def take_up(self, delivery: str) -> None:
		from kentender_procurement.bid_evaluation.services import award_seam

		award_seam.take_up(delivery)

	def return_report(self, *, delivery: str, comment: str, idempotency_key: str, user: str) -> dict[str, Any]:
		from kentender_procurement.bid_evaluation.services import award_seam

		return award_seam.return_report(delivery=delivery, comment=comment, idempotency_key=idempotency_key, user=user)

	def return_for_correction(self, *, delivery: str, comment: str, instruction: str, authorised_by: str, idempotency_key: str) -> dict[str, Any]:
		from kentender_procurement.bid_evaluation.services import award_seam

		return award_seam.return_for_correction(delivery=delivery, comment=comment, instruction=instruction, authorised_by=authorised_by,
			idempotency_key=idempotency_key)

	def corrections_after(self, tender: str) -> list[dict[str, Any]]:
		from kentender_procurement.bid_evaluation.services import award_seam

		return award_seam.corrections_after(tender)

	def take_up_correction(self, reference: str) -> None:
		from kentender_procurement.bid_evaluation.services import award_seam

		award_seam.take_up_correction(reference)

	# -- the Tender (AWD-IF-02) --------------------------------------------------
	def tender_facts(self, tender: str) -> dict[str, Any] | None:
		from kentender_procurement.tenders.services import award_seam

		try:
			return award_seam.tender_facts(tender)
		except Exception as exc:
			raise SourceUnavailable(str(exc)) from exc

	def validity(self, tender: str) -> dict[str, Any]:
		from kentender_procurement.tenders.services import award_seam

		try:
			return award_seam.validity(tender)
		except Exception as exc:
			raise SourceUnavailable(str(exc)) from exc

	def status_events(self, tender: str) -> list[dict[str, Any]]:
		from kentender_procurement.tenders.services import award_seam

		try:
			return award_seam.status_events(tender)
		except Exception as exc:
			raise SourceUnavailable(str(exc)) from exc

	def funding(self, tender: str) -> dict[str, Any]:
		"""The current funding position at this moment (AWD-IF-07), read through
		Budget's published `get_funding_lineage`. Never a guess: when the
		reservations cannot be named or Budget cannot answer, `known` is False
		and the caller treats it as unavailable, never as "not restricted"."""
		from decimal import Decimal

		from kentender_procurement.tenders.services import award_seam

		try:
			reservations = award_seam.funding_reservations(tender)
			if not reservations:
				return {"known": False, "reason": "The tender has no recorded budget reservation."}
			from kentender_budget.services.budget_downstream_contracts import get_funding_lineage

			total, codes = Decimal("0"), []
			for reservation in reservations:
				rows = get_funding_lineage(reservation=reservation).get("rows") or []
				if not rows:
					return {"known": False, "reason": "Budget could not confirm a reservation of this tender."}
				for row in rows:
					res = row["reservation"]
					if res.get("status") in ("Active", "Partially Converted", "Converted"):
						total += Decimal(cstr(res.get("remaining_amount") or 0))
					codes.append(cstr(res.get("code")))
		except Exception as exc:
			frappe.log_error(title="Award funding read unavailable")
			return {"known": False, "reason": cstr(exc)[:140] or "Budget did not answer."}
		return {"known": True, "available": str(total.quantize(Decimal("0.01"))), "reservations": codes, "source": "Budget"}

	# -- bidders and suppliers (AWD-IF-03) ---------------------------------------
	def audience(self, tender: str) -> list[dict[str, Any]]:
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.audience(tender)

	def notice_contact(self, bidder_arrangement: str) -> dict[str, Any]:
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.notice_contact(bidder_arrangement)

	def signatory(self, user: str, organisation: str, *, at=None) -> dict[str, Any] | None:
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.signatory(user, organisation, at=at)

	def acting_for(self, user: str, organisation: str, *, at=None) -> dict[str, Any] | None:
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.acting_for(user, organisation, at=at)

	def organisations_of(self, user: str, *, at=None) -> list[str]:
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.organisations_of(user, at=at)

	def organisation_users(self, organisation: str, *, at=None) -> list[dict[str, Any]]:
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.organisation_users(organisation, at=at)

	def status_available(self) -> bool:
		return True


def evaluation_provider() -> EvaluationSource:
	return EvaluationSource()
