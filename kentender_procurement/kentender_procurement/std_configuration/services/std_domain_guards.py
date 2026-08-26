# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §7 backbone domain guards (Phase 1 — structural invariants only).

Lifecycle transitions (Draft -> In review -> Active, §12) are Phase 3 scope and are
not implemented here. These guards only stop a record being saved into a shape the
domain model itself forbids, independent of who is allowed to do it or when.
"""

from __future__ import annotations

import frappe
from frappe import _

OPEN_DRAFT_STATES = ("Draft", "In review", "Returned")

# §7.6 — block_type -> whether this treatment stores locked_text (True) or a
# binding_key (False). Every value is exhaustive (Select fieldtype already rejects
# an undefined "Other" treatment at the framework level); this only enforces the
# locked_text/binding_key mutual exclusivity for the treatment actually chosen.
LOCKED_TEXT_BLOCK_TYPES = {"Locked text"}


def validate_std_cfg_draft(doc) -> None:
	"""§7.1 — "One open Draft maximum" per package.

	Source of truth is `STD Cfg Package.current_draft_id`, not a query over
	`STD Cfg Draft.state` — the latter was tried first and found wrong during
	Phase 3: a Draft's `state` enum (Draft/In review/Returned, §7.2) has no
	terminal value it moves to on activation, so a state-based query would
	permanently block a package from ever getting a new Draft after its first
	activation. The lifecycle engine (Phase 3) clears `current_draft_id` on
	activation; the Draft row itself is kept as-is, permanently, for history.
	"""
	if not doc.package_id:
		frappe.throw(_("Package is required"))
	if doc.is_new():
		current = frappe.db.get_value("STD Cfg Package", doc.package_id, "current_draft_id")
		if current:
			frappe.throw(
				_("Package {0} already has an open Draft ({1})").format(doc.package_id, current),
				frappe.ValidationError,
			)


def validate_std_cfg_version(doc) -> None:
	"""§7.1/§7.3 — one Active Version per package at a time (structural check only;
	the atomic activate-supersede transaction that flips the prior Active row to
	Superseded is Phase 7 — this guard only stops two rows being Active
	simultaneously, it does not perform supersession itself)."""
	if not doc.package_id:
		frappe.throw(_("Package is required"))
	if not doc.is_new():
		existing_package, existing_version_number = frappe.db.get_value(
			"STD Cfg Version", doc.name, ["package_id", "version_number"]
		) or (None, None)
		if existing_package and existing_package != doc.package_id:
			frappe.throw(_("Package cannot be changed once a Version is created"), frappe.ValidationError)
		if existing_version_number and int(existing_version_number) != int(doc.version_number or 0):
			frappe.throw(_("Version number cannot be changed once created"), frappe.ValidationError)
	if doc.status == "Active":
		clash = frappe.db.exists(
			"STD Cfg Version",
			{"package_id": doc.package_id, "status": "Active", "name": ["!=", doc.name or ""]},
		)
		if clash:
			frappe.throw(
				_("Package {0} already has an Active Version ({1})").format(doc.package_id, clash),
				frappe.ValidationError,
			)
	if frappe.db.exists(
		"STD Cfg Version",
		{
			"package_id": doc.package_id,
			"version_number": doc.version_number,
			"name": ["!=", doc.name or ""],
		},
	):
		frappe.throw(_("Version number {0} already exists for this package").format(doc.version_number))


def validate_std_cfg_section(doc) -> None:
	if doc.display_order is None or int(doc.display_order) <= 0:
		frappe.throw(_("Display order must be a positive number"))
	if doc.coverage_area_number is None or not (1 <= int(doc.coverage_area_number) <= 16):
		frappe.throw(_("Coverage area number must be between 1 and 16"))
	if not doc.is_new():
		prior_code, prior_required = frappe.db.get_value(
			"STD Cfg Section", doc.name, ["section_code", "is_required"]
		) or (None, None)
		if prior_required and (doc.has_value_changed("section_code") or doc.has_value_changed("title")):
			frappe.throw(
				_("Required Section {0} cannot be renamed or recoded by a Configurator").format(
					prior_code
				),
				frappe.ValidationError,
			)


def block_required_section_delete(doc) -> None:
	if doc.is_required:
		frappe.throw(
			_("Required Section {0} cannot be deleted").format(doc.section_code), frappe.ValidationError
		)


def validate_owning_reference(doc) -> None:
	"""Every PCFG schema/definition doctype (Phase 2) is Draft-scoped content that
	Phase 7's activation later carries into an immutable Version — same
	`reference_doctype`/`reference_name` Dynamic Link shape as `STD Cfg Source
	Document` (Phase 1), not a bespoke `draft_id` field per doctype."""
	if not doc.get("reference_doctype") or not doc.get("reference_name"):
		frappe.throw(_("Owning Draft or Version is required"))
	if not frappe.db.exists(doc.reference_doctype, doc.reference_name):
		frappe.throw(_("{0} {1} does not exist").format(doc.reference_doctype, doc.reference_name))


def validate_unique_key_within_reference(doc, key_field: str) -> None:
	"""§11.2 — 'duplicate binding key' is a named Blocking condition. Enforced here
	at the point of save (not deferred entirely to Phase 6's coverage engine)
	because a duplicate key is a structural defect the domain model itself should
	never persist, scoped to the same owning Draft/Version so two different Drafts
	(e.g. an Active Version's content and its in-progress next Draft) never clash."""
	key_value = doc.get(key_field)
	if not key_value:
		frappe.throw(_("{0} is required").format(frappe.unscrub(key_field)))
	clash = frappe.db.exists(
		doc.doctype,
		{
			"reference_doctype": doc.reference_doctype,
			"reference_name": doc.reference_name,
			key_field: key_value,
			"name": ["!=", doc.name or ""],
		},
	)
	if clash:
		frappe.throw(
			_("{0} {1} is already used in this {2}").format(
				frappe.unscrub(key_field), key_value, doc.reference_doctype
			),
			frappe.ValidationError,
		)


def validate_std_cfg_parameter_definition(doc) -> None:
	"""§7.7 — "Definitions without a render or downstream consumer are invalid."""
	if not ((doc.render_binding or "").strip() or (doc.downstream_binding or "").strip()):
		frappe.throw(
			_("Parameter {0} must have a render binding or a downstream binding").format(
				doc.parameter_key
			),
			frappe.ValidationError,
		)
	if doc.value_type == "Choice":
		if not (doc.allowed_values or "").strip():
			frappe.throw(_("Allowed values are required for a Choice parameter"))
	elif (doc.allowed_values or "").strip():
		frappe.throw(_("Allowed values may only be set for a Choice parameter"))


def validate_std_cfg_evaluation_schema(doc) -> None:
	"""§9.11 — "Weight [is] present only for scored criteria."

	§7.12's own `treatment` enum has 4 values (§9.11's own table names them):
	`Scored` always carries a weight; `Pass/Fail`/`Calculated financial result`
	never do; `Pass/Fail or scored` is a genuine hybrid — the package permits
	either treatment per criterion instance, so weight is optional there, not
	mandatory. A prior, case-sensitive `"Scored" in treatment` substring check
	silently missed this hybrid value entirely (`"Scored" in "Pass/Fail or
	scored"` is `False` — the enum value is lowercase "scored"), incorrectly
	forbidding a weight on a criterion type the spec explicitly allows one for.
	Found live while seeding the Phase 9 golden fixture, fixed here rather than
	worked around in the fixture data.
	"""
	treatment = doc.treatment or ""
	if treatment == "Scored" and not doc.weight:
		frappe.throw(_("Weight is required for a scored criterion"))
	if treatment in ("Pass/Fail", "Calculated financial result") and doc.weight:
		frappe.throw(_("Weight may only be set for a scored criterion"))


def validate_std_cfg_output_mapping(doc) -> None:
	"""§7.15 — one edge per (source_binding_key, target) pair. A definition may map
	to several targets, so uniqueness is on the pair, not the key alone."""
	clash = frappe.db.exists(
		"STD Cfg Output Mapping",
		{
			"reference_doctype": doc.reference_doctype,
			"reference_name": doc.reference_name,
			"source_binding_key": doc.source_binding_key,
			"target": doc.target,
			"name": ["!=", doc.name or ""],
		},
	)
	if clash:
		frappe.throw(
			_("{0} already maps to {1} in this {2}").format(
				doc.source_binding_key, doc.target, doc.reference_doctype
			),
			frappe.ValidationError,
		)


def validate_std_cfg_decision(doc) -> None:
	"""§7.17 — "Return requires one correction." Activation carries no free-text
	correction field at all (it is a decision, not a critique)."""
	if doc.decision == "Return for correction" and not (doc.correction_required or "").strip():
		frappe.throw(_("A correction is required to return the package"))
	if doc.decision == "Activate package" and (doc.correction_required or "").strip():
		frappe.throw(_("Correction text may only be set on a Return decision"))


def validate_std_cfg_tender_manifest(doc) -> None:
	"""§9.14 — "no missing, duplicated or unowned manifest item." Duplicate item_key
	within one manifest is checked here; cross-step completeness is Phase 7/9."""
	seen: set[str] = set()
	for row in doc.items or []:
		if row.item_key in seen:
			frappe.throw(
				_("Manifest item key {0} is duplicated ({1})").format(row.item_key, row.step_id),
				frappe.ValidationError,
			)
		seen.add(row.item_key)


def validate_std_cfg_content_block(doc) -> None:
	"""§4 four-content-treatment rule + §7.6 field-purpose guard.

	block_type is a closed Select enum (no undefined "Other" reaches here at all —
	Frappe rejects an out-of-list value before validate() runs). This only enforces
	that the *content* matches the *treatment actually chosen*: Locked text carries
	locked_text and nothing else; every other treatment carries a binding_key and no
	locked_text.
	"""
	if not doc.section_id:
		frappe.throw(_("Section is required"))
	if doc.display_order is None or int(doc.display_order) <= 0:
		frappe.throw(_("Display order must be a positive number"))
	duplicate = frappe.db.exists(
		"STD Cfg Content Block",
		{
			"section_id": doc.section_id,
			"display_order": doc.display_order,
			"reference_doctype": doc.reference_doctype,
			"reference_name": doc.reference_name,
			"name": ["!=", doc.name or ""],
		},
	)
	if duplicate:
		frappe.throw(
			_("Display order {0} is already used in this Section").format(doc.display_order),
			frappe.ValidationError,
		)

	if doc.block_type in LOCKED_TEXT_BLOCK_TYPES:
		if not (doc.locked_text or "").strip():
			frappe.throw(_("Locked text is required for a Locked text block"))
		if (doc.binding_key or "").strip():
			frappe.throw(_("A Locked text block cannot have a binding key"))
	else:
		if not (doc.binding_key or "").strip():
			frappe.throw(
				_("Binding key is required for a {0} block").format(doc.block_type), frappe.ValidationError
			)
		if (doc.locked_text or "").strip():
			frappe.throw(_("Only a Locked text block may carry locked text"))
