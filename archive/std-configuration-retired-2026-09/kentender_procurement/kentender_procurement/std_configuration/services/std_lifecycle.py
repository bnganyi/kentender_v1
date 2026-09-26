# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §12 lifecycle engine.

Table-driven in spirit, not in literal dict form: the 8-row §12 transition table
collapses to 5 orchestration functions because several rows share one function
(Submit/Resubmit both land "In review"; "Create new version" is `create_next_draft`
built on the same `create_draft` every Version-1 Draft uses).

Capability gating (§12: STD Configurator drives Draft/Returned/submit actions,
STD Reviewer drives return/activate) and maker-checker (submitter cannot activate
their own Draft) are wired via `std_authorization.py`'s `require_draft_capability`/
`require_package_configure_capability` at the top of each transition — Phase 4
work, added after Phase 3 first shipped these functions capability-free. Maker-
checker itself is not a separate check here: it falls out of the Separation of
Duties Rule `SOD-STD-CONFIGURE-REVIEW` the same authorization engine already
enforces (a submitter who also holds Reviewer capability is blocked by that rule
the moment they try to exercise CAP_REVIEW on a Draft they already exercised
CAP_CONFIGURE on — see `std_authorization.prior_actions_for_draft`).
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_configuration.services.std_authorization import (
	CAP_CONFIGURE,
	CAP_REVIEW,
	require_draft_capability,
	require_package_configure_capability,
)
from kentender_procurement.std_configuration.services.std_reference import ID_FIELD

# §7.9 doctypes whose rows are Draft/Version-scoped package *content* and must be
# cloned into a new Draft by `create_next_draft` / reassigned to a Version on
# activation. Deliberately excludes STD Cfg Validation Finding (derived, never
# authored), STD Cfg Assistance Batch/Review Task/Decision (transient process
# records, not package content) and STD Cfg Tender Manifest (Phase 7's own output,
# never Draft-authored).
REFERENCE_SCOPED_CONTENT_DOCTYPES = (
	"STD Cfg Content Block",
	"STD Cfg Parameter Definition",
	"STD Cfg Requirement Schema",
	"STD Cfg Schedule Schema",
	"STD Cfg Inventory Schema",
	"STD Cfg Price Schema",
	"STD Cfg Evaluation Schema",
	"STD Cfg Form Schema",
	"STD Cfg Contract Schema",
	"STD Cfg Output Mapping",
)


def check_expected_record_version(draft, expected_record_version) -> None:
	"""§7.2 `record_version` — optimistic concurrency (§13.3 `STD_DRAFT_CHANGED`).
	Callers (Phase 5's area-save commands, in particular) pass what they last
	read; a mismatch means someone else changed the Draft first."""
	if expected_record_version is None:
		return
	if int(expected_record_version) != int(draft.record_version or 0):
		from kentender_procurement.std_configuration.services.std_errors import (
			STD_DRAFT_CHANGED,
			std_throw,
		)

		std_throw(STD_DRAFT_CHANGED)


def create_draft(
	package_id, official_issue_label, based_on_version_id=None, official_source_file_id=None, actor=None
):
	"""§6.1/§6.2 step 1-2 — Version 1's first Draft, or a later revision's Draft.
	One-open-Draft and the generated id are enforced by the DocType itself
	(Phase 1); this only resolves `proposed_version_number`."""
	require_package_configure_capability(actor or frappe.session.user, package_id)
	proposed_version_number = 1
	if based_on_version_id:
		base_version_number = frappe.db.get_value("STD Cfg Version", based_on_version_id, "version_number")
		if not base_version_number:
			frappe.throw(_("Based-on Version {0} does not exist").format(based_on_version_id))
		proposed_version_number = int(base_version_number) + 1
	draft = frappe.get_doc(
		{
			"doctype": "STD Cfg Draft",
			"package_id": package_id,
			"based_on_version_id": based_on_version_id,
			"proposed_version_number": proposed_version_number,
			"official_issue_label": official_issue_label,
			"official_source_file_id": official_source_file_id,
		}
	)
	draft.insert(ignore_permissions=True)
	return draft


def _clone_reference_scoped_content(doctype: str, source_version_name: str, target_draft_name: str) -> None:
	id_field = ID_FIELD.get(doctype)
	rows = frappe.get_all(
		doctype,
		filters={"reference_doctype": "STD Cfg Version", "reference_name": source_version_name},
		pluck="name",
	)
	for row_name in rows:
		source = frappe.get_doc(doctype, row_name)
		clone = frappe.copy_doc(source)
		clone.reference_doctype = "STD Cfg Draft"
		clone.reference_name = target_draft_name
		if id_field:
			clone.set(id_field, None)
		clone.insert(ignore_permissions=True)


def create_next_draft(package_id, official_issue_label, official_source_file_id=None, actor=None):
	"""§6.2 step 2 / `CreateNextSTDDraft` — "The Configurator creates the next Draft
	by copying the Active Version." Copies every reference-scoped content row;
	does not alter the Active Version (each clone is a fresh row)."""
	require_package_configure_capability(actor or frappe.session.user, package_id)
	package = frappe.get_doc("STD Cfg Package", package_id)
	if not package.current_active_version_id:
		frappe.throw(_("Package {0} has no Active Version to create the next Draft from").format(package_id))
	if package.current_draft_id:
		frappe.throw(_("Package {0} already has an open Draft ({1})").format(package_id, package.current_draft_id))

	draft = create_draft(
		package_id,
		official_issue_label,
		based_on_version_id=package.current_active_version_id,
		official_source_file_id=official_source_file_id,
		actor=actor,
	)
	for doctype in REFERENCE_SCOPED_CONTENT_DOCTYPES:
		_clone_reference_scoped_content(doctype, package.current_active_version_id, draft.name)
	return draft


def submit_for_review(draft_name, reviewer, expected_record_version=None, actor=None):
	"""§12 rows "Submit for review" and "Resubmit" — both land `In review` from
	`Draft` or `Returned`; the acting Configurator picks the user-facing label,
	the engine doesn't need two functions for one transition.

	§6.1 step 7 — "Zero Blocking findings are required to submit." §16.4 —
	"Submit for review repeats the complete check." Both satisfied by running
	Phase 6's `run_complete_check` here, not by trusting a client-side check.
	"""
	draft = frappe.get_doc("STD Cfg Draft", draft_name)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_CONFIGURE, draft)
	check_expected_record_version(draft, expected_record_version)
	if draft.state not in ("Draft", "Returned"):
		frappe.throw(_("Only a Draft or Returned package can be submitted for review"))
	if not draft.official_source_file_id:
		frappe.throw(_("Official source is required before submission (§7.2)"))

	from kentender_procurement.std_configuration.services import std_coverage
	from kentender_procurement.std_configuration.services.std_errors import (
		STD_VALIDATION_BLOCKED,
		std_throw,
	)

	check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
	if check["blocking_count"]:
		std_throw(
			STD_VALIDATION_BLOCKED,
			_("{0} Blocking finding(s) remain. Open the Readiness Report.").format(check["blocking_count"]),
		)

	draft.state = "In review"
	draft.record_version = (draft.record_version or 0) + 1
	draft.save(ignore_permissions=True)

	task = frappe.get_doc(
		{
			"doctype": "STD Cfg Review Task",
			"draft_id": draft.name,
			"reviewer": reviewer,
			"submitted_by": actor,
			"submitted_at": frappe.utils.now_datetime(),
			"snapshot_record_version": draft.record_version,
		}
	)
	task.insert(ignore_permissions=True)
	return task


# Same transition, the other §12-named label — not a separate implementation.
resubmit_for_review = submit_for_review


def _assert_snapshot_unchanged(draft, task) -> None:
	"""§16.4 — "Review tabs always read the submitted snapshot... never fall back
	to the current Draft." A Draft cannot normally change while `In review` (no
	area-save command accepts that state), so this is defense in depth, not the
	only guard. §13.3 `STD_REVIEW_CHANGED`."""
	if int(draft.record_version or 0) != int(task.snapshot_record_version or 0):
		from kentender_procurement.std_configuration.services.std_errors import (
			STD_REVIEW_CHANGED,
			std_throw,
		)

		std_throw(STD_REVIEW_CHANGED)


def return_for_correction(review_task_name, correction_required, actor=None):
	"""§12 "Return for correction" — In review -> Returned."""
	task = _load_open_task(review_task_name)
	draft = frappe.get_doc("STD Cfg Draft", task.draft_id)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_REVIEW, draft)
	_assert_snapshot_unchanged(draft, task)
	if draft.state != "In review":
		frappe.throw(_("Only a Draft In review can be returned"))

	draft.state = "Returned"
	draft.save(ignore_permissions=True)

	task.status = "Decided"
	task.save(ignore_permissions=True)

	decision = frappe.get_doc(
		{
			"doctype": "STD Cfg Decision",
			"review_task_id": task.name,
			"decision": "Return for correction",
			"correction_required": correction_required,
			"decided_by": actor,
			"decided_at": frappe.utils.now_datetime(),
		}
	)
	decision.insert(ignore_permissions=True)
	return decision


def _load_open_task(review_task_name):
	task = frappe.get_doc("STD Cfg Review Task", review_task_name)
	if task.status != "Open":
		frappe.throw(_("Review task {0} is already decided").format(review_task_name))
	return task


def _reassign_reference_scoped_content(doctype: str, from_name: str, to_name: str) -> None:
	frappe.db.set_value(
		doctype,
		{"reference_doctype": "STD Cfg Draft", "reference_name": from_name},
		{"reference_doctype": "STD Cfg Version", "reference_name": to_name},
		update_modified=False,
	)


def activate_package(review_task_name, actor=None):
	"""§12 "Activate package" — In review -> Active Version created.

	§11.3/§16.4 — atomic: creating the Version, superseding the prior Active
	Version, reassigning content, and clearing the package's open-Draft pointer
	all happen in one request/transaction; Frappe's own request lifecycle commits
	or rolls back the whole thing (AGENTS.md §4.4 — no manual commit here).

	Maker-checker (submitter != reviewer, §12) is enforced by
	`require_draft_capability`'s underlying SoD check (`SOD-STD-CONFIGURE-REVIEW`),
	not a bespoke identity comparison here — the same authorization engine that
	gates every other capability check in this module.
	"""
	task = _load_open_task(review_task_name)
	draft = frappe.get_doc("STD Cfg Draft", task.draft_id)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_REVIEW, draft)
	_assert_snapshot_unchanged(draft, task)
	if draft.state != "In review":
		frappe.throw(_("Only a Draft In review can be activated"))
	if not draft.official_source_file_id:
		frappe.throw(_("Official source is required before activation (§11.3)"))

	# §11.3 — activation itself re-requires zero Blocking findings and full
	# coverage, not just at submission. `_assert_snapshot_unchanged` already
	# proves the Draft hasn't moved since its (already-checked) submission, so
	# this is defense in depth against a guard being bypassed, not the only gate.
	from kentender_procurement.std_configuration.services import std_coverage
	from kentender_procurement.std_configuration.services.std_errors import (
		STD_VALIDATION_BLOCKED,
		std_throw,
	)

	check = std_coverage.run_complete_check("STD Cfg Draft", draft.name)
	if check["blocking_count"]:
		std_throw(STD_VALIDATION_BLOCKED)

	package = frappe.get_doc("STD Cfg Package", draft.package_id)

	prior_active = frappe.db.get_value(
		"STD Cfg Version", {"package_id": draft.package_id, "status": "Active"}, "name"
	)
	if prior_active:
		# Flip the prior Active row first — `validate_std_cfg_version`'s
		# one-Active-per-package guard would otherwise reject the new insert.
		frappe.db.set_value("STD Cfg Version", prior_active, "status", "Superseded")

	version = frappe.get_doc(
		{
			"doctype": "STD Cfg Version",
			"package_id": draft.package_id,
			"version_number": draft.proposed_version_number,
			"status": "Active",
			"official_issue_label": draft.official_issue_label,
			"official_source_file_id": draft.official_source_file_id,
		}
	)
	version.insert(ignore_permissions=True)

	for doctype in REFERENCE_SCOPED_CONTENT_DOCTYPES:
		_reassign_reference_scoped_content(doctype, draft.name, version.name)

	# §9.2/§10 — all seven runtime manifests, one call, one atomic activation.
	# Tender Configuration keeps its own dedicated DocType (Phase 2/7); the
	# other six share `STD Cfg Runtime Manifest` (Phase 7 follow-up, per user
	# decision 2026-08-26) — see `std_runtime_manifest.py`'s own docstring.
	from kentender_procurement.std_configuration.services.std_runtime_manifest import (
		generate_all_manifests,
	)

	generate_all_manifests(version.name, draft.package_id, package.official_title, draft.official_issue_label)

	frappe.db.set_value("STD Cfg Package", package.name, "current_active_version_id", version.name)
	frappe.db.set_value("STD Cfg Package", package.name, "current_draft_id", None)

	task.status = "Decided"
	task.save(ignore_permissions=True)

	decision = frappe.get_doc(
		{
			"doctype": "STD Cfg Decision",
			"review_task_id": task.name,
			"decision": "Activate package",
			"decided_by": actor,
			"decided_at": frappe.utils.now_datetime(),
		}
	)
	decision.insert(ignore_permissions=True)
	return version


def available_actions(draft) -> list[str]:
	"""§12 — server-computed action set from state alone (AGENTS.md §6.2: never a
	client-side status-to-action map). Capability/role narrowing is layered on top
	by Phase 4, not duplicated here."""
	if draft.state in ("Draft", "Returned"):
		return ["save_area", "run_complete_check", "submit_for_review"]
	if draft.state == "In review":
		return ["return_for_correction", "activate_package"]
	return []
