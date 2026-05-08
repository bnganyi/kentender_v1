# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD template governance — constants and package hash helpers (doc 7 §§11–12, STD-GOV-004).

``canonicalize_std_package_payload`` + ``compute_std_package_hash`` implement governance
**V1** canonical JSON (sorted object keys at every depth, stable list order) and
**SHA-256** hex digests over UTF-8 encoding of that string.

This is distinct from ``std_template_loader.compute_package_hash``, which hashes raw
on-disk files with fixed separators for the WORKS POC loader (doc 7 / Step 10 §7).
Import/replace services (STD-GOV-007+) should use this module for payload-level hashes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# --- §11 lifecycle / validation status ----------------------------------------

STATUS_IMPORTED = "Imported"
STATUS_VALIDATION_FAILED = "Validation Failed"
STATUS_VALIDATED = "Validated"
STATUS_SUBMITTED = "Submitted for Approval"
STATUS_RETURNED = "Returned for Correction"
STATUS_REJECTED = "Rejected"
STATUS_APPROVED = "Approved"
STATUS_ACTIVE = "Active"
STATUS_SUSPENDED = "Suspended"
STATUS_SUPERSEDED = "Superseded"
STATUS_RETIRED = "Retired"
STATUS_ARCHIVED = "Archived"

VALIDATION_NOT_RUN = "Not Run"
VALIDATION_PASS = "Pass"
VALIDATION_PASS_WARNINGS = "Pass with Warnings"
VALIDATION_BLOCKED = "Blocked"
VALIDATION_FAILED = "Failed"

HASH_ALGORITHM = "SHA-256"
CANONICALIZATION_VERSION = "V1"

PROTECTED_STATES: frozenset[str] = frozenset(
	{
		STATUS_SUBMITTED,
		STATUS_REJECTED,
		STATUS_APPROVED,
		STATUS_ACTIVE,
		STATUS_SUSPENDED,
		STATUS_SUPERSEDED,
		STATUS_RETIRED,
		STATUS_ARCHIVED,
	}
)

CONTROLLED_REPLACEMENT_STATES: frozenset[str] = frozenset(
	{
		STATUS_IMPORTED,
		STATUS_VALIDATION_FAILED,
		STATUS_VALIDATED,
		STATUS_RETURNED,
	}
)

HISTORICAL_LIFECYCLE_STATUSES: frozenset[str] = frozenset(
	{STATUS_SUPERSEDED, STATUS_RETIRED, STATUS_ARCHIVED}
)

# Doc 7 §19 — server-side package immutability (fieldnames match ``STD Template``;
# ``package_json`` / ``manifest_json`` are the repo equivalents of ``package_payload_json`` /
# ``package_manifest_json`` in the written spec).
PROTECTED_PACKAGE_FIELD_NAMES: frozenset[str] = frozenset(
	{
		"template_code",
		"template_family",
		"procurement_category",
		"template_version",
		"package_version",
		"package_json",
		"manifest_json",
		"package_hash",
		"package_hash_algorithm",
		"canonicalization_version",
		"source_authority",
		"source_document_code",
	}
)

# --- §12 audit / lifecycle event codes ----------------------------------------

EVT_IMPORTED = "STD_TEMPLATE_IMPORTED"
EVT_PACKAGE_REPLACED = "STD_TEMPLATE_PACKAGE_REPLACED"
EVT_VALIDATION_STARTED = "STD_TEMPLATE_VALIDATION_STARTED"
EVT_VALIDATION_COMPLETED = "STD_TEMPLATE_VALIDATION_COMPLETED"
EVT_SUBMITTED = "STD_TEMPLATE_SUBMITTED_FOR_APPROVAL"
EVT_RETURNED = "STD_TEMPLATE_RETURNED_FOR_CORRECTION"
EVT_REJECTED = "STD_TEMPLATE_REJECTED"
EVT_APPROVED = "STD_TEMPLATE_APPROVED"
EVT_ACTIVATED = "STD_TEMPLATE_ACTIVATED"
EVT_SUSPENDED = "STD_TEMPLATE_SUSPENDED"
EVT_REINSTATED = "STD_TEMPLATE_REINSTATED"
EVT_SUPERSEDED = "STD_TEMPLATE_SUPERSEDED"
EVT_RETIRED = "STD_TEMPLATE_RETIRED"
EVT_ARCHIVED = "STD_TEMPLATE_ARCHIVED"
EVT_USED_FOR_TENDER = "STD_TEMPLATE_USED_FOR_TENDER"
EVT_USAGE_BLOCKED = "STD_TEMPLATE_USAGE_BLOCKED"
EVT_MUTATION_BLOCKED = "STD_TEMPLATE_MUTATION_BLOCKED"
EVT_DELETE_BLOCKED = "STD_TEMPLATE_DELETE_BLOCKED"
EVT_OVERRIDE_USED = "STD_TEMPLATE_OVERRIDE_USED"
EVT_SNAPSHOT_GENERATED = "STD_TEMPLATE_SNAPSHOT_GENERATED"
EVT_ACTIVE_CONFLICT_BLOCKED = "STD_TEMPLATE_ACTIVE_CONFLICT_BLOCKED"
EVT_HASH_MISMATCH_BLOCKED = "STD_TEMPLATE_HASH_MISMATCH_BLOCKED"
EVT_PERMISSION_BLOCKED = "STD_TEMPLATE_PERMISSION_BLOCKED"


def _normalize_to_json_tree(value: Any) -> Any:
	"""Return a structure made only of dict/list/str/int/float/bool/None."""
	if value is None or isinstance(value, (str, int, float, bool)):
		return value
	if isinstance(value, dict):
		return {str(k): _normalize_to_json_tree(v) for k, v in value.items()}
	if isinstance(value, (list, tuple)):
		return [_normalize_to_json_tree(v) for v in value]
	raise TypeError(
		f"package_payload contains non-JSON-serializable type {type(value).__name__!r}"
	)


def canonicalize_std_package_payload(package_payload: Any) -> str:
	"""Deterministic canonical JSON string for ``package_payload`` (governance V1).

	Accepts a ``dict``/``list`` tree or a **UTF-8 JSON string** of an object/array.
	Dict keys are sorted at every object level; list order is preserved.
	Uses compact separators (``,`` / ``:``) and ``ensure_ascii=False``.
	"""
	if isinstance(package_payload, (bytes, bytearray)):
		package_payload = bytes(package_payload).decode("utf-8")

	if isinstance(package_payload, str):
		stripped = package_payload.strip()
		try:
			parsed: Any = json.loads(stripped)
		except json.JSONDecodeError as exc:
			raise ValueError("package_payload string is not valid JSON") from exc
		package_payload = parsed

	tree = _normalize_to_json_tree(package_payload)
	return json.dumps(tree, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_std_package_hash(package_payload: Any) -> str:
	"""SHA-256 hex digest of the UTF-8 bytes of ``canonicalize_std_package_payload``."""
	body = canonicalize_std_package_payload(package_payload)
	return hashlib.sha256(body.encode("utf-8")).hexdigest()
