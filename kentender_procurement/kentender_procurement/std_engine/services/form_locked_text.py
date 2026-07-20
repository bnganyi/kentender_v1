# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Load official IT STD form / contract-form locked legal text into STD Clause rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.std_engine.constants import (
	CANONICAL_FAMILY_CODE,
	CANONICAL_PACKAGE_ID,
	LEGAL_REVIEW_APPROVED,
)
from kentender_procurement.std_engine.paths import std_prod_data_dir

FORMS_SECTION = f"{CANONICAL_PACKAGE_ID}.section.forms"
CONTRACT_FORMS_SECTION = f"{CANONICAL_PACKAGE_ID}.section.contract_forms"
MIN_FORM_BODY_CHARS = 200


def form_locked_bodies_path() -> Path:
	return (
		std_prod_data_dir()
		/ "KE-PPRA-IT-2022-04_seed_package_v1_1"
		/ "forms"
		/ "form_locked_bodies.json"
	)


def load_form_locked_bodies() -> dict[str, Any]:
	path = form_locked_bodies_path()
	if not path.is_file():
		frappe.throw(
			f"Form locked bodies artifact missing: {path}",
			title="LOCKED_STD_TEXT_UNAVAILABLE",
		)
	payload = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(payload, dict):
		frappe.throw("form_locked_bodies.json must be an object.", title="LOCKED_STD_TEXT_UNAVAILABLE")
	return payload


def inventory_form_locked_text(package_id: str | None = None) -> dict[str, Any]:
	"""Return coverage of locked legal text for standard forms + contract forms."""
	package_id = (package_id or CANONICAL_PACKAGE_ID).strip()
	payload = load_form_locked_bodies()
	expected_forms = payload.get("forms") or []
	expected_contract = payload.get("contract_forms") or []

	form_clauses = frappe.get_all(
		"STD Clause",
		filters={"package_id": package_id, "section": FORMS_SECTION},
		fields=["name", "clause_key", "title", "clause_text"],
	)
	contract_clauses = frappe.get_all(
		"STD Clause",
		filters={"package_id": package_id, "section": CONTRACT_FORMS_SECTION},
		fields=["name", "clause_key", "title", "clause_text"],
	)

	missing: list[str] = []
	short: list[str] = []
	by_key = {cstr(r.clause_key): r for r in form_clauses}
	for form in expected_forms:
		key = _form_clause_key(form)
		row = by_key.get(key)
		body = cstr(row.clause_text if row else "")
		if not row:
			missing.append(cstr(form.get("form_code") or key))
		elif len(body.strip()) < MIN_FORM_BODY_CHARS:
			short.append(cstr(form.get("form_code") or key))

	contract_ok = False
	for row in contract_clauses:
		if len(cstr(row.clause_text).strip()) >= MIN_FORM_BODY_CHARS:
			contract_ok = True
			break
	if expected_contract and not contract_ok:
		missing.append("contract_forms")

	complete = not missing and not short
	return {
		"packageId": package_id,
		"expectedFormCount": len(expected_forms),
		"formClauseCount": len(form_clauses),
		"contractClauseCount": len(contract_clauses),
		"missing": missing,
		"shortBodies": short,
		"complete": complete,
	}


def ensure_form_locked_clauses(package_id: str | None = None) -> dict[str, Any]:
	"""Insert/update STD Clause rows for every standard form + contract forms section.

	Must run while the STD Version is mutable (DRAFT), before activation.
	"""
	package_id = (package_id or CANONICAL_PACKAGE_ID).strip()
	if not frappe.db.exists("STD Version", package_id):
		frappe.throw(f"STD Version {package_id} not found.", title="STD_VERSION_NOT_FOUND")

	lifecycle = cstr(frappe.db.get_value("STD Version", package_id, "lifecycle_state"))
	immutable = int(frappe.db.get_value("STD Version", package_id, "is_immutable") or 0)
	if lifecycle == "ACTIVE" or immutable:
		frappe.throw(
			f"Cannot load form locked text into immutable/ACTIVE package {package_id}.",
			title="STD_IMMUTABLE",
		)

	payload = load_form_locked_bodies()
	upserted = 0
	for form in payload.get("forms") or []:
		_upsert_clause(
			package_id=package_id,
			clause_key=_form_clause_key(form),
			clause_code=cstr(form.get("form_code") or ""),
			title=cstr(form.get("display_title") or form.get("form_code") or "Form"),
			section=cstr(form.get("section_key") or FORMS_SECTION),
			body=cstr(form.get("full_clause_text") or ""),
			content_hash=cstr(form.get("content_hash") or ""),
			metadata=form,
		)
		upserted += 1

	for contract in payload.get("contract_forms") or []:
		_upsert_clause(
			package_id=package_id,
			clause_key=cstr(contract.get("clause_key") or f"{package_id}.clause.contract_forms"),
			clause_code=cstr(contract.get("clause_code") or "IT-CONTRACT-FORMS"),
			title=cstr(contract.get("display_title") or "Contract Forms"),
			section=cstr(contract.get("section_key") or CONTRACT_FORMS_SECTION),
			body=cstr(contract.get("full_clause_text") or ""),
			content_hash=cstr(contract.get("content_hash") or ""),
			metadata=contract,
		)
		upserted += 1

	frappe.db.commit()
	inventory = inventory_form_locked_text(package_id)
	if not inventory.get("complete"):
		frappe.throw(
			"Form locked legal text incomplete after load: "
			f"missing={inventory.get('missing')} short={inventory.get('shortBodies')}",
			title="LOCKED_STD_TEXT_UNAVAILABLE",
		)
	return {"packageId": package_id, "upserted": upserted, "inventory": inventory}


def assert_form_locked_text_complete(package_id: str | None = None) -> dict[str, Any]:
	inventory = inventory_form_locked_text(package_id)
	if not inventory.get("complete"):
		missing = inventory.get("missing") or inventory.get("shortBodies") or ["forms"]
		section = cstr(missing[0])
		frappe.throw(
			f"Locked STD text unavailable for {section}. "
			"Load approved STD Engine text before generating preview.",
			title="LOCKED_STD_TEXT_UNAVAILABLE",
		)
	return inventory


def _form_clause_key(form: dict[str, Any]) -> str:
	explicit = cstr(form.get("clause_key") or "").strip()
	if explicit:
		return explicit
	form_key = cstr(form.get("form_key") or "").strip()
	if form_key:
		return form_key.replace(".form.", ".clause.form.")
	code = cstr(form.get("form_code") or "FORM").strip()
	return f"{CANONICAL_PACKAGE_ID}.clause.form.{code.lower().replace('-', '_')}"


def _upsert_clause(
	*,
	package_id: str,
	clause_key: str,
	clause_code: str,
	title: str,
	section: str,
	body: str,
	content_hash: str,
	metadata: dict[str, Any],
) -> None:
	body = (body or "").strip()
	if len(body) < MIN_FORM_BODY_CHARS:
		frappe.throw(
			f"Locked STD text unavailable for {clause_code or clause_key}. "
			"Load approved STD Engine text before generating preview.",
			title="LOCKED_STD_TEXT_UNAVAILABLE",
		)
	meta = dict(metadata or {})
	meta["mutability_type"] = "LOCKED_LEGAL_TEXT"
	meta["source"] = "form_locked_bodies.json"
	values = {
		"doctype": "STD Clause",
		"package_id": package_id,
		"family_code": CANONICAL_FAMILY_CODE,
		"version_code": package_id,
		"clause_key": clause_key,
		"section": section,
		"object_key": clause_code or clause_key,
		"title": title,
		"clause_text": body,
		"content_hash": content_hash or None,
		"validation_status": LEGAL_REVIEW_APPROVED,
		"metadata_json": json.dumps(meta, ensure_ascii=False, sort_keys=True),
	}
	existing = frappe.db.get_value("STD Clause", {"package_id": package_id, "clause_key": clause_key}, "name")
	if existing:
		doc = frappe.get_doc("STD Clause", existing)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(values).insert(ignore_permissions=True)
