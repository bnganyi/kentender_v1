# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — the Tenders owner's provider for Procurement Analytics (kind `tenders`).

Registered on the `kt_analytics_providers` hook as this module; core never imports this app. It exposes the contract's two
functions (`kentender_core.services.analytics_contract`):

- ``applies(*, user, at)`` — ``{"tenders"}`` for the readers Tenders already has (the four Site-wide responsibilities, the
  technical readers including a Technical Operator, and an Organisation-Unit-scoped Departmental Author or Head of User
  Department), otherwise the empty set. A cheap responsibility check, no scan of Tenders.
- ``facts(*, user, kind, at)`` — one record per Tender root the actor may know. A Tender whose existence the actor may not
  know contributes nothing.

What a record carries: identity and route (the module's own `/app/tenders/<reference>`), the Fiscal Year and units (lead
first), the authorised value of the exact Requisition Version the Tender consumed by contributing department (read from the
immutable Authorised Requisition Handoff, never summed from a different source), the instants Tenders owns (`started_at`, the
handoff's consumption; `published_at`; each cancellation decision), the instants the stage owners own, the one §5.2 bucket
with the owner's wording of the position, and at most one outstanding matter (the latest stage that holds it).

The three stage owners answer through `facts_for(*, user, tender_names, at)`:
`bid_opening.services.analytics_facts`, `bid_evaluation.services.analytics_facts` and `award.services.analytics_facts`. They
are imported when called, so a missing module is a failed read for the Tenders that need it and never an import error. When a
call raises for a batch it is repeated Tender by Tender, so one failure makes only that Tender Status unavailable (the
classifier decides whether the failed stage was needed). A read here changes nothing: it never calls `submission_close` and
never calls a function that logs and omits (`stage_summary`) or that writes (`refresh_obligation_statuses`).

The Head of User Department and the other departmental readers keep their existing visibility (a Tender whose lead or
contributing unit is within their scope) and are never given an award amount. The pictured Tender rows (ANL §10A.4, §10A.10)
show them the same position and outstanding text as everyone else, with two limits from OVS-CHG-001 v0.6 §4.1 (the Head of User
Department's added Award read is scoped status and the final decision, never the professional opinion or unissued notices): no
Award outstanding matter, and an Award position that says only "decision recorded" once a decision exists. Evaluation's administrative
progress before delivery is kept. Site-wide and technical readers are unchanged.
"""

from __future__ import annotations

import importlib
from datetime import datetime
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import analytics_contract as contract
from kentender_core.services.authorization import PURPOSE_READ, authorise_record, permitted_ou_scopes
from kentender_core.services.home_viewer import is_technical_reader
from kentender_procurement.tenders.services import analytics_buckets as buckets
from kentender_procurement.tenders.services import handoffs, serializer
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.tender_roles import DEPARTMENTAL_ROLES, SITE_WIDE_ROLES

PAGE = "tenders"
TECHNICAL, SITE, DEPARTMENT = "technical", "site", "department"
HANDOFF_DOCTYPE = "Authorised Requisition Handoff"
STAGE_MODULES = {
	"opening": "kentender_procurement.bid_opening.services.analytics_facts",
	"evaluation": "kentender_procurement.bid_evaluation.services.analytics_facts",
	"award": "kentender_procurement.award.services.analytics_facts",
}
TENDER_FIELDS = [
	"name", "tender_reference", "requirement_title", "requisition_handoff", "fiscal_year", "overall_status", "current_version", "approved_version", "published_at",
	"submission_deadline", "lead_org_unit", "contributing_org_unit_ids", "creation",
]
TASK_FIELDS = ["name", "tender", "task_type", "business_role", "holder", "sender", "comment", "subject_type", "subject_id", "creation", "tender_version"]


# --------------------------------------------------------------------------
# who may read
# --------------------------------------------------------------------------


def audience(user: str, at: datetime) -> tuple[str, set[str]]:
	"""``(mode, units)``: `technical` (Administrator, System Manager, Technical Operator: every Tender), `site` (a Site-wide
	Tenders responsibility: every Tender), `department` (the Organisation Units, with descendants, of a Departmental Author or
	Head of User Department) or ``""`` (no Tenders responsibility). One verdict per read, resolved at `at`."""
	if not user or user == "Guest":
		return "", set()
	if is_technical_reader(user, at):
		return TECHNICAL, set()
	for role in SITE_WIDE_ROLES:
		if authorise_record(user=user, business_role=role, organisation_unit="", at=at, purpose=PURPOSE_READ).allowed:
			return SITE, set()
	units: set[str] = set()
	for role in DEPARTMENTAL_ROLES:
		units |= permitted_ou_scopes(user, role, at) or set()
	return (DEPARTMENT, units) if units else ("", set())


def applies(*, user: str, at: datetime) -> set[str]:
	return {contract.TENDERS} if audience(user, at)[0] else set()


# --------------------------------------------------------------------------
# the stage owners
# --------------------------------------------------------------------------


def stage_facts(stage: str, *, user: str, tender_names: list[str], at: datetime) -> dict[str, Any]:
	"""One owner's `facts_for`, imported now. The one indirection tests replace with fake owners."""
	return importlib.import_module(STAGE_MODULES[stage]).facts_for(user=user, tender_names=tender_names, at=at)


def _instant(value: Any) -> datetime | None:
	return get_datetime(value) if value else None


def _matter(value: Any) -> dict[str, Any] | None:
	"""A stage owner's outstanding matter, rebuilt through the contract so an unusable one is a failed read."""
	if value is None:
		return None
	if not isinstance(value, dict):
		raise ValueError("outstanding is not a mapping")
	since = _instant(value.get("since"))
	if not since or not cstr(value.get("text")).strip():
		raise ValueError("outstanding needs text and a since instant")
	return contract.outstanding(cstr(value["text"]).strip(), cstr(value.get("holder")), since)


def _shape(stage: str, value: Any) -> dict[str, Any] | None:
	"""One owner's facts for one Tender in the types the contract wants; None is "this owner has no case". Raises on anything
	that is not usable, which the caller turns into `FAILED` for that Tender."""
	if value is None:
		return None
	if not isinstance(value, dict):
		raise ValueError(f"{stage} facts are not a mapping")
	out = dict(value)
	if stage == "opening":
		out["opening_complete_at"] = _instant(value.get("opening_complete_at"))
	elif stage == "evaluation":
		out["report_sent_at"] = _instant(value.get("report_sent_at"))
		out["opening_completed_at"] = _instant(value.get("opening_completed_at"))
		out["outstanding"] = _matter(value.get("outstanding"))
	else:
		outcome = value.get("decision_outcome") or None
		if outcome not in (None, contract.OUTCOME_AWARD, contract.OUTCOME_NO_AWARD):
			raise ValueError(f"award decision outcome {outcome!r}")
		out.update({
			"received_at": _instant(value.get("received_at")), "decision_at": _instant(value.get("decision_at")), "decision_outcome": outcome,
			"decision_events": [get_datetime(x) for x in value.get("decision_events") or []], "outstanding": _matter(value.get("outstanding")),
			"award_amount": contract.money(value["award_amount"]) if value.get("award_amount") is not None else None,
			"award_amount_visible": bool(value.get("award_amount_visible")),
		})
	return out


def _read_stage(stage: str, user: str, names: list[str], at: datetime) -> dict[str, Any]:
	"""``{tender: facts | None | FAILED}`` for `names`. A batch that raises is repeated Tender by Tender."""
	if not names:
		return {}
	try:
		batch = stage_facts(stage, user=user, tender_names=list(names), at=at)
		if not isinstance(batch, dict):
			raise ValueError(f"{stage} facts_for returned {type(batch).__name__}")
	except Exception:
		frappe.logger("kentender.analytics").warning(f"{stage} facts failed for a batch of {len(names)} Tender(s); reading one at a time", exc_info=True)
		batch = {}
		for name in names:
			try:
				one = stage_facts(stage, user=user, tender_names=[name], at=at)
				if not isinstance(one, dict):
					raise ValueError(f"{stage} facts_for returned {type(one).__name__}")
				batch[name] = one.get(name)
			except Exception:
				frappe.logger("kentender.analytics").warning(f"{stage} facts failed for {name}", exc_info=True)
				batch[name] = buckets.FAILED
	out: dict[str, Any] = {}
	for name in names:
		value = batch.get(name)
		if value is buckets.FAILED:
			out[name] = buckets.FAILED
			continue
		try:
			out[name] = _shape(stage, value)
		except Exception:
			frappe.logger("kentender.analytics").warning(f"{stage} facts for {name} are not usable", exc_info=True)
			out[name] = buckets.FAILED
	return out


# --------------------------------------------------------------------------
# facts read once per call
# --------------------------------------------------------------------------


def _units(root) -> list[str]:
	"""Lead first, then the contributing units in the order recorded."""
	import json

	out = [cstr(root.lead_org_unit)] if root.lead_org_unit else []
	try:
		for unit in json.loads(root.contributing_org_unit_ids or "[]"):
			if unit and cstr(unit) not in out:
				out.append(cstr(unit))
	except (TypeError, ValueError):
		pass
	return out


def _title(root, versions: dict[str, Any]) -> str:
	"""The officer's title on the approved (else current) Version, as the later stages show it, then the Requisition's."""
	version = versions.get(cstr(root.approved_version or root.current_version))
	state = serializer.officer_state(frappe._dict(officer_payload_json=version.officer_payload_json if version else None)) if version else {}
	return cstr(state.get("tender_title") or root.requirement_title or root.tender_reference or root.name).strip()


def _handoffs(roots: list[Any]) -> dict[str, Any]:
	names = sorted({cstr(r.requisition_handoff) for r in roots if r.requisition_handoff})
	rows = {h.name: h for h in frappe.get_all(HANDOFF_DOCTYPE, filters={"name": ("in", names)}, fields=["name", "payload_json", "consumed_at"])} if names else {}
	for root in roots:
		if cstr(root.requisition_handoff) not in rows:
			# an authorised value that cannot be read is a failed read, never a zero
			raise ValueError(f"Tender {root.tender_reference or root.name}: its Requisition handoff {root.requisition_handoff or '(none)'} cannot be read")
	return rows


def _authorised_lines(root, handoff) -> list[dict[str, Any]]:
	"""The authorised value of the consumed Requisition Version, one line per contributing department (money is a Data string)."""
	import json

	totals: dict[str, Decimal] = {}
	for row in json.loads(handoff.payload_json or "{}").get("drawdown_lines") or []:
		unit = cstr(row.get("contributing_org_unit"))
		if not unit:
			raise ValueError(f"Tender {root.tender_reference or root.name}: a drawdown line names no contributing unit")
		totals[unit] = totals.get(unit, Decimal(0)) + contract.money(row.get("requested_value"))
	return [contract.line(unit, amount) for unit, amount in totals.items()]


def _versions(roots: list[Any]) -> dict[str, Any]:
	ids = {cstr(v) for r in roots for v in (r.current_version, r.approved_version) if v}
	fields = ["name", "status", "predecessor_version", "officer_payload_json", "returned_at", "return_affected_task"]
	rows = {v.name: v for v in frappe.get_all("Tender Version", filters={"name": ("in", sorted(ids))}, fields=fields)} if ids else {}
	predecessors = {cstr(v.predecessor_version) for v in rows.values() if v.predecessor_version} - set(rows)
	if predecessors:
		rows.update({v.name: v for v in frappe.get_all("Tender Version", filters={"name": ("in", sorted(predecessors))}, fields=fields)})
	return rows


def _cancellations(names: list[str]) -> dict[str, list[datetime]]:
	out: dict[str, list[datetime]] = {}
	for row in frappe.get_all("Tender Cancellation", filters={"tender": ("in", names)}, fields=["tender", "decided_at", "name"], order_by="decided_at asc, creation asc"):
		if not row.decided_at:
			raise ValueError(f"cancellation {row.name} records no decision instant")
		out.setdefault(row.tender, []).append(get_datetime(row.decided_at))
	return out


def _open_tasks(names: list[str]) -> dict[str, list[Any]]:
	"""Each Tender's open register items, newest last."""
	out: dict[str, list[Any]] = {}
	for task in frappe.get_all("Tender Task", filters={"tender": ("in", names), "status": "Open"}, fields=TASK_FIELDS, order_by="creation asc"):
		if task.task_type in handoffs.REGISTER:
			out.setdefault(task.tender, []).append(task)
	return out


# --------------------------------------------------------------------------
# the Tender's own wording and outstanding matter
# --------------------------------------------------------------------------


def _someone(names: list[str], role: str) -> str:
	return " or ".join(names) if names and len(names) <= 2 else f"{'an' if cstr(role)[:1] in 'AEIOU' else 'a'} {role}"


def _people(names: list[str], role: str) -> str:
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


def _note(root, versions: dict[str, Any], tasks: list[Any]) -> str:
	"""The owner's wording for a Tender in preparation: a return names the affected task, a reopen and the Accounting Officer's
	return or a withdrawn authorisation use the register's own words. Nothing else is said."""
	version = versions.get(cstr(root.current_version))
	predecessor = versions.get(cstr(version.predecessor_version)) if version and version.predecessor_version else None
	kinds = {t.task_type: t for t in tasks}
	if cstr(root.overall_status) == "Draft":
		if predecessor and predecessor.status == "Returned":
			affected = buckets.lower_first(cstr(predecessor.return_affected_task))
			return f"{affected} returned for correction" if affected else "returned for correction"
		if handoffs.CORRECT_REOPENED in kinds:
			return "reopened for correction"
	for kind in (handoffs.RETURNED_BY_AO, handoffs.REVIEW_WITHDRAWN):
		if kind in kinds and cstr(root.overall_status) == "Approved":
			return buckets.lower_first(handoffs.HOME_TEXT[kind][2])
	return ""


def _returned_at(task) -> Any:
	predecessor = frappe.db.get_value("Tender Version", task.tender_version, "predecessor_version") if task.tender_version else None
	return frappe.db.get_value("Tender Version", predecessor, "returned_at") if predecessor else None


def _task_matter(root, task) -> dict[str, Any] | None:
	"""The register item as one outstanding matter, in the owner's words and without the instant. A returned or reopened Tender
	reads "<the return comment>. Awaiting correction by <holder>." from the instant of the return."""
	names = [handoffs.full_name(user) for user in handoffs.holders_of(task)]
	kind = cstr(task.task_type)
	holder = _people(names, cstr(task.business_role))
	since = task.creation
	if kind in (handoffs.CORRECT_RETURNED, handoffs.CORRECT_REOPENED):
		comment = cstr(task.comment).strip().rstrip(".").strip()
		text = f"{comment + '. ' if comment else ''}Awaiting correction by {holder}."
		if kind == handoffs.CORRECT_RETURNED:
			since = _returned_at(task) or since
		if not comment:
			text = f"{'Returned' if kind == handoffs.CORRECT_RETURNED else 'Reopened'} for correction. Awaiting correction by {holder}."
	else:
		text = handoffs.home_line_for(root, task, _someone(names, cstr(task.business_role))).strip().rstrip(".") + "."
	return contract.outstanding(text, holder, get_datetime(since)) if text and since else None


def _own_matter(root, tasks: list[Any]) -> dict[str, Any] | None:
	for task in reversed(tasks):
		matter = _task_matter(root, task)
		if matter:
			return matter
	return None


def _outstanding(root, tasks: list[Any], award: Any, evaluation: Any, cancelled: bool, *, department: bool = False) -> dict[str, Any] | None:
	"""At most one matter, from the latest stage that holds one. A cancelled Tender has only its own follow-up (cancellation
	compliance): the stage owners' matters ended with the proceeding. A department-limited reader is given no Award matter (it names the
	professional opinion and unissued notices, outside OVS-CHG-001 v0.6 §4.1); Evaluation's administrative progress is kept."""
	if not cancelled:
		for facts in ((evaluation,) if department else (award, evaluation)):
			if isinstance(facts, dict) and facts.get("outstanding"):
				return facts["outstanding"]
	return _own_matter(root, tasks)


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def _record(root, *, mode: str, at: datetime, versions, handoff, cancellations, tasks, opening, evaluation, award) -> dict[str, Any]:
	cancelled = cstr(root.overall_status) == buckets.CANCELLED or bool(cancellations)
	# the owners' facts only count where the owner was asked; a Tender in preparation or open has none
	facts = {
		"status": cstr(root.overall_status), "at": at, "submission_deadline": _instant(root.submission_deadline), "cancelled": cancelled,
		"cancellation_complete": (not any(t.task_type == handoffs.CANCELLATION_COMPLIANCE for t in tasks)) if cancellations else None,
		"note": _note(root, versions, tasks), "department": mode == DEPARTMENT, "opening": opening, "evaluation": evaluation, "award": award,
	}
	verdict = buckets.classify(facts)
	opened = isinstance(opening, dict) and opening.get("outcome") == "Bids opened"
	has_award = isinstance(award, dict)
	if mode == DEPARTMENT or award is buckets.FAILED:
		amount, visible = None, False
	elif has_award:
		visible = bool(award.get("award_amount_visible"))
		amount = award.get("award_amount") if visible else None
	else:
		amount, visible = None, True
	reference = cstr(root.tender_reference) or root.name
	return contract.record(
		contract.TENDERS, id=root.name, title=_title(root, versions), reference=cstr(root.tender_reference), fiscal_year=cstr(root.fiscal_year), org_units=_units(root),
		route=[PAGE, reference], outstanding=_outstanding(root, tasks, award, evaluation, cancelled, department=mode == DEPARTMENT), bucket=verdict["bucket"], position=verdict["position"],
		authorised_lines=_authorised_lines(root, handoff), started_at=_instant(handoff.consumed_at), published_at=_instant(root.published_at),
		cancelled_at=cancellations[0] if cancellations else None, opening_complete_at=opening.get("opening_complete_at") if opened else None,
		report_sent_at=evaluation.get("report_sent_at") if isinstance(evaluation, dict) else None,
		award_received_at=award.get("received_at") if has_award else None, decision_at=award.get("decision_at") if has_award else None,
		decision_outcome=award.get("decision_outcome") if has_award else None, decision_events=list(award.get("decision_events") or []) if has_award else [],
		award_amount=amount, award_amount_visible=visible, cancellation_events=list(cancellations),
	)


def facts(*, user: str, kind: str = contract.TENDERS, at: datetime, **params: Any) -> dict[str, Any]:
	if kind != contract.TENDERS:
		raise ValueError(f"the Tenders provider has no {kind!r} facts")
	mode, units = audience(user, at)
	if not mode:
		return contract.facts_result([])
	roots = [frappe._dict(row) for row in frappe.get_all("Tender", fields=TENDER_FIELDS, order_by="creation asc, name asc", limit_page_length=0)]
	if mode == DEPARTMENT:
		# the existing rule (`tender_authorization.reader_mode`): a Tender whose lead or contributing unit is within the actor's scope
		roots = [r for r in roots if units & authz.contributing_units_of(r)]
	if not roots:
		return contract.facts_result([])
	names = [r.name for r in roots]
	versions, handoff_rows, cancellations, tasks = _versions(roots), _handoffs(roots), _cancellations(names), _open_tasks(names)
	for_stage = [
		r.name for r in roots
		if buckets.needs_stage_reads({
			"status": cstr(r.overall_status), "at": at, "submission_deadline": _instant(r.submission_deadline),
			"cancelled": cstr(r.overall_status) == buckets.CANCELLED or r.name in cancellations,
		})
	]
	stages = {stage: _read_stage(stage, user, for_stage, at) for stage in STAGE_MODULES}
	records = [
		_record(
			root, mode=mode, at=at, versions=versions, handoff=handoff_rows[cstr(root.requisition_handoff)], cancellations=cancellations.get(root.name, []),
			tasks=tasks.get(root.name, []), opening=stages["opening"].get(root.name), evaluation=stages["evaluation"].get(root.name), award=stages["award"].get(root.name),
		)
		for root in roots
	]
	return contract.facts_result(records)
