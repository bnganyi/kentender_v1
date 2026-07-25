# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Readable structural validator for curated PPRA IT STD electronic templates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from kentender_procurement.tender_configurations.electronic_std_templates import (
	ALLOWED_RENDERERS,
	CANONICAL_SECTION_KEYS,
	LIFECYCLE_STATUSES,
	PPRA_IT_STD_V1_APPROVAL_PATH,
	PPRA_IT_STD_V1_PATH,
	TEMPLATE_ID_PPRA_IT_STD,
	TEMPLATE_VERSION_V1,
)

REQUIRED_TOP_KEYS = ("template_id", "template_version", "std_family", "source", "sections")
REQUIRED_SECTION_KEYS = (
	"section_key",
	"title",
	"order",
	"renderer",
	"bidder_instructions",
	"source_refs",
	"required",
)


class TemplateValidationError(Exception):
	"""Raised when a curated electronic STD template fails structural checks."""

	def __init__(self, errors: list[str]):
		self.errors = errors
		super().__init__("; ".join(errors))


def load_json(path: Path | str) -> dict[str, Any]:
	raw = Path(path).read_text(encoding="utf-8")
	data = json.loads(raw)
	if not isinstance(data, dict):
		raise TemplateValidationError(["Template root must be a JSON object."])
	return data


def load_ppra_it_std_v1() -> dict[str, Any]:
	return load_json(PPRA_IT_STD_V1_PATH)


def load_ppra_it_std_v1_approval() -> dict[str, Any]:
	return load_json(PPRA_IT_STD_V1_APPROVAL_PATH)


def validate_template(template: dict[str, Any]) -> list[str]:
	"""Return a list of structural errors (empty = valid). Does not require Approved."""
	errors: list[str] = []
	if not isinstance(template, dict):
		return ["Template must be a dict."]

	for key in REQUIRED_TOP_KEYS:
		if key not in template:
			errors.append(f"Missing top-level key: {key}")

	if template.get("template_id") != TEMPLATE_ID_PPRA_IT_STD:
		errors.append(f"template_id must be {TEMPLATE_ID_PPRA_IT_STD}")
	if str(template.get("template_version") or "") != TEMPLATE_VERSION_V1:
		errors.append(f"template_version must be {TEMPLATE_VERSION_V1}")

	for bad in ("resources", "chunks", "rules_ast", "expression_ast"):
		if bad in template:
			errors.append(f"Forbidden generic shape key present: {bad}")

	sections = template.get("sections")
	if not isinstance(sections, list) or not sections:
		errors.append("sections must be a non-empty list")
		return errors

	keys = [str(s.get("section_key") or "") for s in sections if isinstance(s, dict)]
	if len(keys) != len(set(keys)):
		errors.append("Duplicate section_key values are not allowed")
	if tuple(keys) != CANONICAL_SECTION_KEYS:
		errors.append(
			"sections must contain the canonical registry keys in order; "
			f"got {keys!r}"
		)

	seen_orders: set[int] = set()
	for sec in sections:
		if not isinstance(sec, dict):
			errors.append("Each section must be an object")
			continue
		for key in REQUIRED_SECTION_KEYS:
			if key not in sec:
				errors.append(f"Section {sec.get('section_key')}: missing {key}")
		refs = sec.get("source_refs")
		if not isinstance(refs, list) or not refs:
			errors.append(f"Section {sec.get('section_key')}: source_refs required")
		renderer = str(sec.get("renderer") or "")
		if renderer and renderer not in ALLOWED_RENDERERS:
			errors.append(
				f"Section {sec.get('section_key')}: unsupported renderer {renderer!r}"
			)
		try:
			order = int(sec.get("order"))
		except (TypeError, ValueError):
			errors.append(f"Section {sec.get('section_key')}: invalid order")
			continue
		if order in seen_orders:
			errors.append(f"Duplicate order value: {order}")
		seen_orders.add(order)

	return errors


def validate_approval_metadata(
	approval: dict[str, Any],
	*,
	template_file_hash: str | None = None,
	require_approved: bool = False,
) -> list[str]:
	"""Validate lifecycle metadata. Approved is only required when require_approved=True."""
	errors: list[str] = []
	if not isinstance(approval, dict):
		return ["Approval metadata must be an object"]
	for key in ("template_id", "template_version", "status", "prepared_by", "template_file_hash"):
		if not approval.get(key):
			errors.append(f"Approval missing {key}")
	status = str(approval.get("status") or "")
	if status not in LIFECYCLE_STATUSES:
		errors.append(f"Approval status must be one of {LIFECYCLE_STATUSES} (got {status!r})")
	if require_approved and status != "Approved":
		errors.append(f"Approval status must be Approved for ordinary publication (got {status!r})")
	prep = str(approval.get("prepared_by") or "").strip().lower()
	appr = str(approval.get("approved_by") or "").strip().lower()
	if require_approved:
		if not appr:
			errors.append("Approval missing approved_by")
		if prep and appr and prep == appr:
			errors.append("Preparer must not be the final approver")
	elif prep and appr and prep == appr:
		errors.append("Preparer must not be the final approver")
	if template_file_hash and str(approval.get("template_file_hash") or "") != template_file_hash:
		errors.append("Approval template_file_hash does not match template file")
	return errors


# Back-compat alias used by older callers.
def validate_approval(approval: dict[str, Any], *, template_file_hash: str | None = None) -> list[str]:
	return validate_approval_metadata(approval, template_file_hash=template_file_hash, require_approved=False)


def assert_approved_for_ordinary_publication(approval: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Fail closed unless template approval status is Approved (ordinary publish)."""
	approval = approval if approval is not None else load_ppra_it_std_v1_approval()
	raw = PPRA_IT_STD_V1_PATH.read_bytes()
	file_hash = hashlib.sha256(raw).hexdigest()
	errors = validate_approval_metadata(
		approval, template_file_hash=file_hash, require_approved=True
	)
	if errors:
		raise TemplateValidationError(errors)
	return {"approval": approval, "template_file_hash": file_hash}


def assert_valid_ppra_it_std_v1(*, require_approved: bool = False) -> dict[str, Any]:
	"""Load and validate the curated v1 template; raise TemplateValidationError on failure."""
	raw = PPRA_IT_STD_V1_PATH.read_bytes()
	file_hash = hashlib.sha256(raw).hexdigest()
	template = json.loads(raw.decode("utf-8"))
	errors = validate_template(template)
	approval = load_ppra_it_std_v1_approval()
	errors.extend(
		validate_approval_metadata(
			approval, template_file_hash=file_hash, require_approved=require_approved
		)
	)
	if errors:
		raise TemplateValidationError(errors)
	return {"template": template, "approval": approval, "template_file_hash": file_hash}
