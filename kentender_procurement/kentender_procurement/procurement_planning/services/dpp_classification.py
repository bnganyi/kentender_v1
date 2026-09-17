# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §4.4 / §5.1.6 — accepted-classification provenance and
the Planning-owned correction of it.

Three rules shape everything here.

1. **The Planner selects only a requirement type.** The server derives the
   procurement category from that governed catalogue entry. A client-supplied
   category is rejected outright, never merely ignored (`PLN21-AC-001`).
2. **An accepted classification is never edited.** A correction appends an
   immutable `DPP Classification Correction` against the exact current evidence
   head and leaves the accepted decision, the certified departmental facts and
   every existing Plan Version exactly as they were.
3. **The corrected value governs new work only.** The effective-classification
   projection is the latest valid correction. It never rewrites an accepted
   decision, a stored allocation snapshot, a submitted Plan or the Active Plan.

The four recovery outcomes for whatever already consumed the source are in
`_affected_items` and are the whole point of the feature: an unallocated source
just becomes available with the corrected classification, a mutable Draft item
must be dissolved and re-formed, a governed or Active Plan keeps its exact
classification until a successor carries the change through full governance,
and a scope-locked item records the correction, holds new authorisation and
hands the user to the downstream owner's route.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, scope_lock
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER

REASON_MIN = 20
REASON_MAX = 500

#: Plan Version statuses whose content is still mutable by the Planner.
MUTABLE_PLAN_STATUSES = ("Draft",)

#: Recovery routes reported to the caller, in escalating severity.
RECOVERY_NONE = "none"
RECOVERY_REFORM_DRAFT = "dissolve_and_reform"
RECOVERY_PLAN_SUCCESSOR = "plan_successor"
RECOVERY_DOWNSTREAM_OWNER = "downstream_owner"


# --------------------------------------------------------------------------
# Governed catalogue
# --------------------------------------------------------------------------


def category_for(requirement_type: str) -> str:
	"""Derive the procurement category from the governed catalogue entry.

	§4.4: the finer type comes from the governed catalogue and the category is
	derived from that same entry. A missing or retired type is a configuration
	failure, not a silent default.
	"""
	requirement_type = cstr(requirement_type).strip()
	if not requirement_type:
		fail("PLN_CLASSIFICATION_INCOMPLETE")
	row = frappe.db.get_value(
		"Requirement Type", requirement_type, ["status", "procurement_category"], as_dict=True
	)
	if not row:
		fail(
			"PLN_REFERENCE_UNAVAILABLE",
			f"The requirement type {requirement_type} is not in the governed catalogue.",
		)
	if cstr(row.status) != "Active":
		fail(
			"PLN_REFERENCE_UNAVAILABLE",
			f"The requirement type {requirement_type} is no longer available for new classifications.",
		)
	category = cstr(row.procurement_category).strip()
	if not category:
		fail(
			"PLN_REFERENCE_UNAVAILABLE",
			f"The requirement type {requirement_type} has no procurement category configured.",
		)
	return category


def active_requirement_types() -> list[dict[str, str]]:
	"""The effective catalogue offered to the Planner, category included so the
	screen can show the derived value beside the selector without a round trip."""
	return [
		{"requirement_type": row.name, "procurement_category": cstr(row.procurement_category)}
		for row in frappe.get_all(
			"Requirement Type",
			filters={"status": "Active"},
			fields=["name", "procurement_category"],
			order_by="name asc",
		)
	]


def reject_client_category(payload: dict[str, Any] | None) -> None:
	"""§4.4 — "A client cannot submit a category independently."

	Rejecting rather than ignoring matters: silently dropping the field would
	let a caller believe it had set the category.
	"""
	if not payload:
		return
	for key in ("procurement_category", "category", "new_procurement_category"):
		if key in payload:
			fail(
				"PLN_CLASSIFICATION_INCOMPLETE",
				"Procurement category is derived from the requirement type and cannot be supplied.",
			)


# --------------------------------------------------------------------------
# Effective classification projection
# --------------------------------------------------------------------------


def _accepted_classification(dpp_submission: str, dpp_entry_id: str) -> dict[str, Any] | None:
	"""The original acceptance row for this entry, or None when the entry was
	excluded or the submission was never accepted."""
	import json

	decision = frappe.db.get_value(
		"Departmental Plan Validation Decision",
		{"submission": dpp_submission, "decision": "Accept departmental plan"},
		["name", "classifications", "actor", "decided_at"],
		as_dict=True,
	)
	if not decision:
		return None
	classifications = json.loads(decision.classifications or "{}")
	requirement_type = cstr(classifications.get(dpp_entry_id)).strip()
	if not requirement_type:
		return None
	return {
		"evidence_id": decision.name,
		"evidence_kind": "acceptance",
		"requirement_type": requirement_type,
		"procurement_category": category_for(requirement_type),
		"actor": decision.actor,
		"at": decision.decided_at,
	}


def correction_history(dpp_submission: str, dpp_entry_id: str) -> list[dict[str, Any]]:
	"""Every correction against this entry, oldest first."""
	return [
		{
			"evidence_id": row.name,
			"evidence_kind": "correction",
			"correction_id": row.correction_id,
			"supersedes_evidence_id": row.supersedes_evidence_id,
			"previous_requirement_type": row.previous_requirement_type,
			"previous_procurement_category": row.previous_procurement_category,
			"requirement_type": row.new_requirement_type,
			"procurement_category": row.new_procurement_category,
			"reason": row.reason,
			"actor": row.corrected_by,
			"at": row.corrected_at,
		}
		for row in frappe.get_all(
			"DPP Classification Correction",
			filters={"dpp_submission": dpp_submission, "dpp_entry_id": dpp_entry_id},
			fields=[
				"name",
				"correction_id",
				"supersedes_evidence_id",
				"previous_requirement_type",
				"previous_procurement_category",
				"new_requirement_type",
				"new_procurement_category",
				"reason",
				"corrected_by",
				"corrected_at",
			],
			order_by="corrected_at asc, creation asc",
		)
	]


def effective_classification(dpp_submission: str, dpp_entry_id: str) -> dict[str, Any] | None:
	"""The classification new Planning work must use: the latest correction if
	one exists, otherwise the original acceptance."""
	accepted = _accepted_classification(dpp_submission, dpp_entry_id)
	if not accepted:
		return None
	history = correction_history(dpp_submission, dpp_entry_id)
	current = dict(history[-1]) if history else dict(accepted)
	current["original"] = accepted
	current["corrections"] = history
	current["corrected"] = bool(history)
	return current


def effective_for_entry(dpp_entry: str) -> dict[str, Any] | None:
	"""Same projection keyed by the `Departmental Plan Entry` record, which is
	what formation and the read models hold."""
	row = frappe.db.get_value(
		"Departmental Plan Entry", dpp_entry, ["entry_id", "dpp_version"], as_dict=True
	)
	if not row:
		return None
	submission = frappe.db.get_value(
		"Departmental Plan Submission", {"dpp_version": row.dpp_version}, "name"
	)
	if not submission:
		return None
	return effective_classification(submission, row.entry_id)


# --------------------------------------------------------------------------
# Affected work
# --------------------------------------------------------------------------


def _affected_items(dpp_entry_id: str) -> dict[str, Any]:
	"""Everything that already consumed this source, grouped by the recovery
	route the Planner must take. §5.1.6 items 6–8."""
	from kentender_procurement.procurement_planning.services import plan_read

	entries = frappe.get_all(
		"Departmental Plan Entry", filters={"entry_id": dpp_entry_id}, pluck="name"
	)
	lineage: set[str] = set()
	for entry in entries:
		lineage.update(plan_read.same_source_lineage(entry))
	if not lineage:
		return {"recovery": RECOVERY_NONE, "draft_items": [], "governed_items": [], "locked_items": []}

	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"dpp_entry": ("in", list(lineage)), "allocation_state": ("!=", "Released")},
		fields=["name", "plan_item", "plan_item_id", "plan_version"],
	)
	draft_items: list[dict[str, Any]] = []
	governed_items: list[dict[str, Any]] = []
	locked_items: list[dict[str, Any]] = []
	for allocation in allocations:
		version_status = cstr(
			frappe.db.get_value("Annual Plan Version", allocation.plan_version, "version_status")
		)
		item = frappe.db.get_value(
			"Annual Plan Item",
			allocation.plan_item,
			["name", "plan_item_id", "title", "requirement_type", "procurement_category"],
			as_dict=True,
		)
		if not item:
			continue
		row = {
			"plan_item": item.name,
			"plan_item_id": item.plan_item_id,
			"title": item.title,
			"plan_version": allocation.plan_version,
			"plan_version_status": version_status,
			"plan_uses_requirement_type": item.requirement_type,
			"plan_uses_procurement_category": item.procurement_category,
		}
		if scope_lock.is_locked(item.plan_item_id):
			row.update(scope_lock.status(item.plan_item_id))
			locked_items.append(row)
		elif version_status in MUTABLE_PLAN_STATUSES:
			draft_items.append(row)
		else:
			governed_items.append(row)

	if locked_items:
		recovery = RECOVERY_DOWNSTREAM_OWNER
	elif draft_items:
		recovery = RECOVERY_REFORM_DRAFT
	elif governed_items:
		recovery = RECOVERY_PLAN_SUCCESSOR
	else:
		recovery = RECOVERY_NONE
	return {
		"recovery": recovery,
		"draft_items": draft_items,
		"governed_items": governed_items,
		"locked_items": locked_items,
	}


def source_correction_required(plan_item_id: str) -> bool:
	"""True when a Draft item still carries a classification that a later
	correction superseded — the `Source correction required` state in §5.1.6.6.

	Derived, never a stored flag: a stored flag would drift the moment a
	further correction landed.
	"""
	item = frappe.db.get_value(
		"Annual Plan Item",
		{"plan_item_id": plan_item_id, "item_state": ("!=", "Dissolved")},
		["name", "requirement_type", "procurement_category", "plan_version"],
		as_dict=True,
		order_by="creation desc",
	)
	if not item:
		return False
	if cstr(frappe.db.get_value("Annual Plan Version", item.plan_version, "version_status")) not in MUTABLE_PLAN_STATUSES:
		return False
	for allocation in frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": ("!=", "Released")},
		fields=["dpp_entry"],
	):
		effective = effective_for_entry(allocation.dpp_entry)
		if not effective:
			continue
		if cstr(effective["requirement_type"]) != cstr(item.requirement_type):
			return True
		if cstr(effective["procurement_category"]) != cstr(item.procurement_category):
			return True
	return False


# --------------------------------------------------------------------------
# Reads
# --------------------------------------------------------------------------


def get_accepted_dpp_classification(
	*, dpp_submission: str, dpp_entry_id: str = "", user: str | None = None
) -> dict[str, Any]:
	"""§7.1 `GetAcceptedDPPClassification`."""
	actor = authz.actor(user)
	if not frappe.db.exists("Departmental Plan Submission", dpp_submission):
		authz.not_found()
	# A technical reader passes the read gate but is never offered the command.
	authz.require_site_read((ROLE_PROCUREMENT_PLANNER,), actor)
	rows = _classification_rows(dpp_submission, only_entry=cstr(dpp_entry_id).strip())
	return {
		"ok": True,
		"dpp_submission": dpp_submission,
		"rows": rows,
		"requirement_types": active_requirement_types(),
		"can_correct": authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor),
	}


def _classification_rows(dpp_submission: str, *, only_entry: str = "") -> list[dict[str, Any]]:
	import json

	snapshots = json.loads(
		frappe.db.get_value("Departmental Plan Submission", dpp_submission, "entry_snapshots") or "[]"
	)
	rows: list[dict[str, Any]] = []
	for snapshot in snapshots:
		entry_id = cstr(snapshot.get("entry_id"))
		if only_entry and entry_id != only_entry:
			continue
		excluded = bool(cstr(snapshot.get("not_proceeding_reason")).strip())
		effective = None if excluded else effective_classification(dpp_submission, entry_id)
		affected = _affected_items(entry_id) if effective else {"recovery": RECOVERY_NONE}
		rows.append(
			{
				"dpp_entry_id": entry_id,
				"title": snapshot.get("title"),
				"excluded": excluded,
				"not_proceeding_reason": snapshot.get("not_proceeding_reason"),
				"classification": effective,
				"affected": affected,
				# §10.5: an excluded row shows Not applicable and offers no action.
				"can_correct": bool(effective) and not excluded,
			}
		)
	return rows


# --------------------------------------------------------------------------
# Command
# --------------------------------------------------------------------------


def correct_accepted_requirement_classification(
	*,
	dpp_submission: str,
	dpp_entry_id: str,
	expected_evidence_id: str,
	new_requirement_type: str,
	reason: str,
	idempotency_key: str,
	user: str | None = None,
	**unexpected: Any,
) -> dict[str, Any]:
	"""§7.2 `CorrectAcceptedRequirementClassification`.

	Everything is rechecked inside one transaction: the submission is still
	accepted, the entry is still proceeding, the caller still holds the Planner
	assignment, the presented evidence head is still current, the new type is
	still governed, and the derived category actually differs. A stale or
	concurrent attempt changes nothing at all.
	"""
	reject_client_category(unexpected)
	actor = authz.actor(user)
	dpp_entry_id = cstr(dpp_entry_id).strip()
	reason = cstr(reason).strip()
	payload = {
		"dpp_submission": dpp_submission,
		"dpp_entry_id": dpp_entry_id,
		"expected_evidence_id": cstr(expected_evidence_id).strip(),
		"new_requirement_type": cstr(new_requirement_type).strip(),
		"reason": reason,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	if not frappe.db.exists("Departmental Plan Submission", dpp_submission):
		authz.not_found()
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)

	version = frappe.db.get_value("Departmental Plan Submission", dpp_submission, "dpp_version")
	version_status = cstr(frappe.db.get_value("Departmental Plan Version", version, "version_status"))
	if version_status not in ("Accepted", "Superseded"):
		fail(
			"PLN_CLASSIFICATION_CORRECTION_BLOCKED",
			"Only an accepted departmental plan carries a classification that can be corrected.",
		)

	# Serialise on the departmental root so two Planners cannot both append a
	# correction against the same evidence head.
	root = frappe.db.get_value("Departmental Plan Version", version, "departmental_plan")
	envelope.locked("Departmental Plan", root)

	current = effective_classification(dpp_submission, dpp_entry_id)
	if not current:
		fail(
			"PLN_CLASSIFICATION_CORRECTION_BLOCKED",
			"This requirement was not accepted as proceeding, so it has no procurement classification to correct.",
		)
	if cstr(expected_evidence_id).strip() != cstr(current["evidence_id"]):
		fail("PLN_CLASSIFICATION_CORRECTION_STALE")

	new_requirement_type = cstr(new_requirement_type).strip()
	new_category = category_for(new_requirement_type)
	if new_requirement_type == cstr(current["requirement_type"]):
		fail("PLN_CLASSIFICATION_UNCHANGED")
	if not (REASON_MIN <= len(reason) <= REASON_MAX):
		fail(
			"PLN_ENTRY_INCOMPLETE",
			f"State why the classification is wrong, in {REASON_MIN} to {REASON_MAX} characters.",
		)

	affected = _affected_items(dpp_entry_id)

	correction = frappe.get_doc(
		{
			"doctype": "DPP Classification Correction",
			"correction_id": _correction_id(dpp_submission, dpp_entry_id),
			"dpp_submission": dpp_submission,
			"dpp_entry_id": dpp_entry_id,
			"supersedes_evidence_id": current["evidence_id"],
			"previous_requirement_type": current["requirement_type"],
			"previous_procurement_category": current["procurement_category"],
			"new_requirement_type": new_requirement_type,
			"new_procurement_category": new_category,
			"reason": reason,
			"corrected_by": actor,
			"authority_snapshot": authz.authority_snapshot(assignment),
			"corrected_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(frappe.db.get_value("Departmental Plan", root, "fixture_namespace")),
		}
	).insert(ignore_permissions=True)

	# §5.1.6.8 — a scope-locked item cannot be reclassified through Planning, so
	# new authorisation for it is held until the downstream owner resolves it.
	for row in affected["locked_items"]:
		stable = frappe.db.get_value("Plan Item", {"plan_item_id": row["plan_item_id"]}, "name")
		if stable:
			scope_lock.recompute_hold(frappe.get_doc("Plan Item", stable))

	result = {
		"ok": True,
		"idempotent": False,
		"action": "classification_corrected",
		"correction_id": correction.correction_id,
		"dpp_submission": dpp_submission,
		"dpp_entry_id": dpp_entry_id,
		"previous_requirement_type": current["requirement_type"],
		"previous_procurement_category": current["procurement_category"],
		"new_requirement_type": new_requirement_type,
		"new_procurement_category": new_category,
		"recovery": affected["recovery"],
		"draft_items": affected["draft_items"],
		"governed_items": affected["governed_items"],
		"locked_items": affected["locked_items"],
	}
	envelope.record_command(
		idempotency_key=idempotency_key,
		command="CorrectAcceptedRequirementClassification",
		payload=payload,
		result=result,
		document_type="DPP Classification Correction",
		document_name=correction.name,
		actor=actor,
		fixture_namespace=cstr(correction.fixture_namespace),
	)
	return result


def _correction_id(dpp_submission: str, dpp_entry_id: str) -> str:
	prefix = f"DPPC-{cstr(dpp_entry_id).removeprefix('DPPE-')}-"
	existing = frappe.get_all(
		"DPP Classification Correction",
		filters={"dpp_submission": dpp_submission, "dpp_entry_id": dpp_entry_id},
		pluck="correction_id",
		limit_page_length=0,
	)
	seq = max(
		[int(ref[len(prefix):]) for ref in existing if cstr(ref)[len(prefix):].isdigit()] or [0]
	) + 1
	return f"{prefix}{seq:02d}"
