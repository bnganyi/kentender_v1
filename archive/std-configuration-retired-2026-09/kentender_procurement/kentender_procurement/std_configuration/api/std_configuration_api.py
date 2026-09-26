# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §13 service contracts — whitelisted API surface.

Thin dispatchers only: every rule lives in the domain guards (Phase 1/2),
`std_lifecycle.py` (Phase 3) or `std_authorization.py` (Phase 4). Nothing here
re-implements a check those layers already own (AGENTS.md §4.2 — API validates
input, authorizes the actor, and calls services).

Not every §13.1/§13.2 name is implemented here yet — several genuinely depend on
engines later phases build (§6's coverage/readiness engine, §7's real manifest
generation, §8's assistance engine). Those are listed and explicitly blocked
with `STD_NOT_YET_IMPLEMENTED`, not silently omitted or faked — see the
`_BLOCKED_ON_LATER_PHASE` map and this module's own tracker row (STD-50x) for
exactly which phase each one is waiting on.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_configuration.services import (
	std_assistance,
	std_coverage,
	std_lifecycle,
	std_reuse_transformation,
)
from kentender_procurement.std_configuration.services.std_authorization import (
	CAP_CONFIGURE,
	require_draft_capability,
)
from kentender_procurement.std_configuration.services.std_idempotency import run_idempotent

# PCFG area -> the Draft/Version-scoped content doctype(s) it owns (§8). PCFG-01
# is deliberately absent — it updates the Draft's own fields, not a separate
# content doctype (see `save_std_source_and_profile`).
_AREA_DOCTYPES: dict[str, tuple[str, ...]] = {
	"PCFG-02": ("STD Cfg Content Block",),
	"PCFG-03": ("STD Cfg Parameter Definition",),
	"PCFG-04": ("STD Cfg Requirement Schema",),
	"PCFG-05": ("STD Cfg Schedule Schema", "STD Cfg Inventory Schema"),
	"PCFG-06": ("STD Cfg Price Schema",),
	"PCFG-07": ("STD Cfg Evaluation Schema",),
	"PCFG-08": ("STD Cfg Form Schema",),
	"PCFG-09": ("STD Cfg Contract Schema", "STD Cfg Output Mapping"),
}

_BLOCKED_ON_LATER_PHASE: dict[str, str] = {
	# The Render manifest itself now exists (Phase 7 follow-up), but an actual
	# rendered preview needs composition/formatting logic over its sections and
	# blocks, not just a pass-through of raw manifest data — that belongs to
	# Phase 11's UI-preview work (STD-WF-03), not a quick add-on here.
	"GetSTDPreview": "Phase 11 (complete package preview UI/composition)",
}


def _not_yet_implemented(name: str) -> None:
	frappe.throw(
		_("{0} is not implemented yet — blocked on {1}.").format(name, _BLOCKED_ON_LATER_PHASE[name]),
		frappe.ValidationError,
		title="STD_NOT_YET_IMPLEMENTED",
	)


# --- §13.1 reads --------------------------------------------------------------


@frappe.whitelist()
def list_std_packages() -> list[dict]:
	packages = frappe.get_all(
		"STD Cfg Package",
		fields=["name", "package_code", "official_title", "requirement_profile", "current_active_version_id", "current_draft_id"],
	)
	for pkg in packages:
		pkg["state"] = _package_state(pkg)
	return packages


def _package_state(pkg: dict) -> str:
	if pkg.get("current_draft_id"):
		draft_state = frappe.db.get_value("STD Cfg Draft", pkg["current_draft_id"], "state")
		if draft_state == "In review":
			return "In review"
		return "Draft in progress"
	if pkg.get("current_active_version_id"):
		return "Active"
	return "Not configured"


@frappe.whitelist()
def get_std_package_home(package_id: str) -> dict:
	package = frappe.get_doc("STD Cfg Package", package_id).as_dict()
	package["state"] = _package_state(package)
	return package


@frappe.whitelist()
def get_std_configuration_area(reference_doctype: str, reference_name: str, area: str) -> dict:
	"""One PCFG area's current content for one Draft/Version. Coverage/readiness
	verdicts are Phase 6's `GetSTDCoverageReport`/`GetSTDReadinessReport`, not
	this read — this is raw content only."""
	doctypes = _AREA_DOCTYPES.get(area)
	if not doctypes:
		frappe.throw(_("Unknown configuration area: {0}").format(area))
	items: dict[str, list] = {}
	for doctype in doctypes:
		items[doctype] = frappe.get_all(
			doctype,
			filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
			fields=["*"],
		)
	return {"area": area, "reference_doctype": reference_doctype, "reference_name": reference_name, "items": items}


@frappe.whitelist()
def get_std_coverage_report(reference_doctype: str, reference_name: str) -> list[dict]:
	return std_coverage.coverage_report(reference_doctype, reference_name)


@frappe.whitelist()
def get_std_readiness_report(reference_doctype: str, reference_name: str) -> dict:
	return std_coverage.readiness_report(reference_doctype, reference_name)


@frappe.whitelist()
def get_std_review_workspace(review_task_id: str) -> dict:
	task = frappe.get_doc("STD Cfg Review Task", review_task_id).as_dict()
	draft = frappe.db.get_value(
		"STD Cfg Draft",
		task["draft_id"],
		["package_id", "official_issue_label", "official_source_file_id"],
		as_dict=True,
	)
	decisions = frappe.get_all(
		"STD Cfg Decision",
		filters={"review_task_id": review_task_id},
		fields=["decision", "correction_required", "decided_by", "decided_at"],
	)
	return {"task": task, "draft": draft, "decisions": decisions}


@frappe.whitelist()
def get_std_preview(reference_doctype: str, reference_name: str):
	_not_yet_implemented("GetSTDPreview")


@frappe.whitelist()
def get_std_version_comparison(version_a: str, version_b: str) -> dict:
	"""Minimal §15.20-shaped diff: which reference-scoped doctypes changed row
	count between two Versions. A structured field-level diff (e.g. "Tender
	validity minimum 120 days -> 150 days") is real additional work belonging to
	whichever phase builds the Version Comparison UI (STD-WF-05, Phase 11) —
	this read proves the two Versions are independently queryable and gives a
	genuine, if coarse, changed/unchanged signal now."""
	changed = []
	unchanged = []
	for doctype in std_lifecycle.REFERENCE_SCOPED_CONTENT_DOCTYPES:
		count_a = frappe.db.count(doctype, {"reference_doctype": "STD Cfg Version", "reference_name": version_a})
		count_b = frappe.db.count(doctype, {"reference_doctype": "STD Cfg Version", "reference_name": version_b})
		(changed if count_a != count_b else unchanged).append(
			{"doctype": doctype, "count_a": count_a, "count_b": count_b}
		)
	return {"version_a": version_a, "version_b": version_b, "changed": changed, "unchanged": unchanged}


@frappe.whitelist()
def get_active_std_version(package_id: str) -> dict | None:
	version_id = frappe.db.get_value("STD Cfg Package", package_id, "current_active_version_id")
	if not version_id:
		return None
	return frappe.get_doc("STD Cfg Version", version_id).as_dict()


@frappe.whitelist()
def get_runtime_manifest(std_version_id: str) -> dict:
	from kentender_procurement.std_configuration.services.std_errors import STD_VERSION_NOT_ACTIVE, std_throw

	status = frappe.db.get_value("STD Cfg Version", std_version_id, "status")
	if status != "Active":
		std_throw(STD_VERSION_NOT_ACTIVE)
	manifest_name = frappe.db.get_value("STD Cfg Tender Manifest", {"std_version_id": std_version_id}, "name")
	if not manifest_name:
		# Phase 7 has not yet populated a real manifest for this Version.
		return {"std_version_id": std_version_id, "manifest": None}
	return {"std_version_id": std_version_id, "manifest": frappe.get_doc("STD Cfg Tender Manifest", manifest_name).as_dict()}


@frappe.whitelist()
def get_assistance_proposal(batch_id: str) -> dict:
	return frappe.get_doc("STD Cfg Assistance Batch", batch_id).as_dict()


@frappe.whitelist()
def list_std_reviewers() -> list[dict]:
	"""Phase 11 support read — §16.4's "Submit for review" needs a reviewer to
	route to; not itself named in §13.1 since that registry lists the
	package-authoring reads, but the STD Reviewer role is the same one
	`std_authorization.py` already checks capability against."""
	rows = frappe.get_all(
		"Has Role",
		filters={"role": "STD Reviewer", "parenttype": "User"},
		fields=["parent as user"],
	)
	users = [r["user"] for r in rows]
	if not users:
		return []
	return frappe.get_all(
		"User",
		filters={"name": ["in", users], "enabled": 1},
		fields=["name", "full_name"],
	)


# --- §13.2 commands — area saves ----------------------------------------------


def _save_area_items(draft_name: str, doctype: str, items: list[dict], *, actor: str | None = None) -> list[str]:
	draft = frappe.get_doc("STD Cfg Draft", draft_name)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_CONFIGURE, draft)
	# This module's `from __future__ import annotations` makes every function's
	# annotations plain strings at runtime, which makes typing_validations.py's
	# argument-type validation a silent no-op for every whitelisted command here
	# (a `str` annotation short-circuits its check) — confirmed live: a real
	# browser call sends a list arg as a JSON string (frappe.call's own
	# convention for object/array args), and with validation bypassed nothing
	# ever decodes it back, so `items` arrives as a raw string here and gets
	# iterated character-by-character. `frappe.parse_json` is the fix: a no-op
	# for an already-real list (every existing Python-level test call), a real
	# decode for the JSON-string form every live HTTP call actually sends.
	items = frappe.parse_json(items)
	saved = []
	for raw_item in items:
		item = dict(raw_item)
		row_name = item.pop("name", None)
		if row_name:
			doc = frappe.get_doc(doctype, row_name)
			doc.update(item)
			doc.save(ignore_permissions=True)
		else:
			item.setdefault("reference_doctype", "STD Cfg Draft")
			item.setdefault("reference_name", draft.name)
			doc = frappe.get_doc({"doctype": doctype, **item})
			doc.insert(ignore_permissions=True)
		saved.append(doc.name)
	draft.db_set("record_version", (draft.record_version or 0) + 1, update_modified=False)
	return saved


def _save_area(draft_name: str, area: str, items_by_doctype: dict[str, list[dict]], idempotency_key: str | None) -> dict:
	def _do():
		saved: dict[str, list[str]] = {}
		for doctype, items in items_by_doctype.items():
			saved[doctype] = _save_area_items(draft_name, doctype, items)
		return {"draft_id": draft_name, "area": area, "saved": saved}

	return run_idempotent(idempotency_key, "STD Cfg Draft", draft_name, f"save_{area}", _do)


@frappe.whitelist()
def save_std_source_and_profile(
	draft_name: str,
	official_issue_label: str | None = None,
	official_source_file_id: str | None = None,
	idempotency_key: str | None = None,
) -> dict:
	"""PCFG-01 — updates the Draft's own fields, not a separate content doctype
	(§8: PCFG-01 owns "Official identity, issue, source file, requirement
	profile")."""

	def _do():
		draft = frappe.get_doc("STD Cfg Draft", draft_name)
		require_draft_capability(frappe.session.user, CAP_CONFIGURE, draft)
		if official_issue_label is not None:
			draft.official_issue_label = official_issue_label
		if official_source_file_id is not None:
			draft.official_source_file_id = official_source_file_id
		draft.save(ignore_permissions=True)
		return {"draft_id": draft.name, "record_version": draft.record_version}

	return run_idempotent(idempotency_key, "STD Cfg Draft", draft_name, "save_source_and_profile", _do)


@frappe.whitelist()
def save_std_source_document(draft_name: str, file_id: str, official_title: str | None = None, official_issue_label: str | None = None) -> dict:
	"""Phase 11 support command — `official_source_file_id` (Draft/Version)
	links to `STD Cfg Source Document`, not a raw Frappe File (confirmed by
	the doctype's own field options); a Vue file picker only ever produces a
	File name, so this wraps one as the real linked record. Upserts one row
	per reference (a Draft has exactly one official source) rather than
	accumulating duplicates on repeated "Replace"."""
	draft = frappe.get_doc("STD Cfg Draft", draft_name)
	require_draft_capability(frappe.session.user, CAP_CONFIGURE, draft)
	existing = frappe.db.get_value(
		"STD Cfg Source Document", {"reference_doctype": "STD Cfg Draft", "reference_name": draft_name}, "name"
	)
	if existing:
		doc = frappe.get_doc("STD Cfg Source Document", existing)
		doc.file_id = file_id
		if official_title is not None:
			doc.official_title = official_title
		if official_issue_label is not None:
			doc.official_issue_label = official_issue_label
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Source Document",
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft_name,
				"file_id": file_id,
				"official_title": official_title,
				"official_issue_label": official_issue_label,
			}
		)
		doc.insert(ignore_permissions=True)
	return {"source_document_id": doc.name}


@frappe.whitelist()
def save_std_document_structure(draft_name: str, content_blocks: list[dict], idempotency_key: str | None = None) -> dict:
	return _save_area(draft_name, "PCFG-02", {"STD Cfg Content Block": content_blocks}, idempotency_key)


@frappe.whitelist()
def save_std_parameters(draft_name: str, parameters: list[dict], idempotency_key: str | None = None) -> dict:
	return _save_area(draft_name, "PCFG-03", {"STD Cfg Parameter Definition": parameters}, idempotency_key)


@frappe.whitelist()
def save_std_requirement_schema(draft_name: str, categories: list[dict], idempotency_key: str | None = None) -> dict:
	return _save_area(draft_name, "PCFG-04", {"STD Cfg Requirement Schema": categories}, idempotency_key)


@frappe.whitelist()
def save_std_schedule_inventory_background(
	draft_name: str,
	schedule_rows: list[dict] | None = None,
	inventory_rows: list[dict] | None = None,
	idempotency_key: str | None = None,
) -> dict:
	return _save_area(
		draft_name,
		"PCFG-05",
		{
			"STD Cfg Schedule Schema": schedule_rows or [],
			"STD Cfg Inventory Schema": inventory_rows or [],
		},
		idempotency_key,
	)


@frappe.whitelist()
def save_std_price_schemas(draft_name: str, price_schemas: list[dict], idempotency_key: str | None = None) -> dict:
	return _save_area(draft_name, "PCFG-06", {"STD Cfg Price Schema": price_schemas}, idempotency_key)


@frappe.whitelist()
def save_std_evaluation_schema(draft_name: str, criteria: list[dict], idempotency_key: str | None = None) -> dict:
	return _save_area(draft_name, "PCFG-07", {"STD Cfg Evaluation Schema": criteria}, idempotency_key)


@frappe.whitelist()
def save_std_form_schemas(draft_name: str, forms: list[dict], idempotency_key: str | None = None) -> dict:
	return _save_area(draft_name, "PCFG-08", {"STD Cfg Form Schema": forms}, idempotency_key)


@frappe.whitelist()
def save_std_contract_and_outputs(
	draft_name: str,
	contract_values: list[dict] | None = None,
	output_mappings: list[dict] | None = None,
	idempotency_key: str | None = None,
) -> dict:
	return _save_area(
		draft_name,
		"PCFG-09",
		{
			"STD Cfg Contract Schema": contract_values or [],
			"STD Cfg Output Mapping": output_mappings or [],
		},
		idempotency_key,
	)


# --- §13.2 commands — assistance (§16.2) ---------------------------------------
#
# `proposed_items` is supplied by the caller in both commands — this module
# owns the proposal *contract* (validate/store/accept/reject), not proposal
# *production*. In production, the Phase 10 reuse/transformation utility (see
# `run_std_reuse_transformation` below) or an AI-calling adapter sources this
# list; the AI-calling adapter is still future work (tracker STD-802), so
# `prepare_ai_assisted_draft_proposal` is real and usable today only for a
# caller that already has a candidate list in the proposal shape.


@frappe.whitelist()
def prepare_prior_configuration_proposal(draft_name: str, input_reference: str, proposed_items: list[dict]) -> dict:
	# See _save_area_items's comment: `from __future__ import annotations` makes
	# argument-type validation a no-op, so a real HTTP call's JSON-stringified
	# list arg must be decoded explicitly here.
	batch = std_assistance.prepare_proposal(draft_name, "Prior configuration", input_reference, frappe.parse_json(proposed_items))
	return {"batch_id": batch.name, "proposal_count": len(batch.proposals)}


@frappe.whitelist()
def prepare_ai_assisted_draft_proposal(draft_name: str, input_reference: str, proposed_items: list[dict]) -> dict:
	batch = std_assistance.prepare_proposal(draft_name, "AI-assisted draft", input_reference, frappe.parse_json(proposed_items))
	return {"batch_id": batch.name, "proposal_count": len(batch.proposals)}


@frappe.whitelist()
def accept_assistance_items(batch_id: str, item_names: list[str]) -> dict:
	return std_assistance.accept_items(batch_id, frappe.parse_json(item_names))


@frappe.whitelist()
def reject_assistance_items(batch_id: str, item_names: list[str]) -> dict:
	return std_assistance.reject_items(batch_id, frappe.parse_json(item_names))


# --- §13.2 commands — reuse/transformation (§17) -------------------------------


@frappe.whitelist()
def run_std_reuse_transformation(draft_name: str, bundle_dir: str | None = None) -> dict:
	run = std_reuse_transformation.run_reuse_transformation(draft_name, bundle_dir=bundle_dir)
	return {
		"run_id": run.name,
		"register": [
			{
				"reuse_item_id": row.reuse_item_id,
				"content_class": row.content_class,
				"disposition": row.disposition,
				"proposed_row_count": row.proposed_row_count,
				"unresolved_count": row.unresolved_count,
				"assistance_batch_id": row.assistance_batch_id,
			}
			for row in run.register
		],
	}


@frappe.whitelist()
def get_std_reuse_reconciliation_report(run_id: str) -> dict:
	return std_reuse_transformation.reconciliation_report(run_id)


# --- §13.2 commands — check / lifecycle ---------------------------------------


@frappe.whitelist()
def run_std_complete_check(draft_name: str) -> dict:
	draft = frappe.get_doc("STD Cfg Draft", draft_name)
	require_draft_capability(frappe.session.user, CAP_CONFIGURE, draft)
	return std_coverage.run_complete_check("STD Cfg Draft", draft_name)


@frappe.whitelist()
def submit_std_for_review(
	draft_name: str, reviewer: str, expected_record_version: int | None = None, idempotency_key: str | None = None
) -> dict:
	def _do():
		task = std_lifecycle.submit_for_review(
			draft_name, reviewer, expected_record_version=expected_record_version
		)
		return {"review_task_id": task.name, "reviewer": task.reviewer, "state": "In review"}

	return run_idempotent(idempotency_key, "STD Cfg Draft", draft_name, "submit_for_review", _do)


@frappe.whitelist()
def return_std_for_correction(review_task_id: str, correction_required: str, idempotency_key: str | None = None) -> dict:
	def _do():
		decision = std_lifecycle.return_for_correction(review_task_id, correction_required)
		return {"decision_id": decision.name, "decision": decision.decision}

	return run_idempotent(idempotency_key, "STD Cfg Review Task", review_task_id, "return_for_correction", _do)


@frappe.whitelist()
def activate_std_version(review_task_id: str, idempotency_key: str | None = None) -> dict:
	def _do():
		version = std_lifecycle.activate_package(review_task_id)
		return {"version_id": version.name, "version_number": version.version_number, "status": version.status}

	return run_idempotent(idempotency_key, "STD Cfg Review Task", review_task_id, "activate_package", _do)


@frappe.whitelist()
def create_next_std_draft(
	package_id: str, official_issue_label: str, official_source_file_id: str | None = None, idempotency_key: str | None = None
) -> dict:
	def _do():
		draft = std_lifecycle.create_next_draft(package_id, official_issue_label, official_source_file_id)
		return {"draft_id": draft.name, "based_on_version_id": draft.based_on_version_id}

	return run_idempotent(idempotency_key, "STD Cfg Package", package_id, "create_next_draft", _do)
