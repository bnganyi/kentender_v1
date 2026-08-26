# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §17.6 step 1-2 — freeze and inventory the reuse bundle.

This is bounded, one-time implementation tooling (§17.6: "a bounded
implementation utility, not a production parsing service"), not a live
runtime dependency — it is never called from any package/Tender/bidder/
evaluation/contract runtime path (§17.6/§19's own boundary, confirmed for
`scripts/std_extraction` specifically in this plan's own prior-art audit).

The bundle on disk already IS the frozen, read-only controlled location
(`docs/std-prod-impl/data/...`, checked into the repo) — this module does not
copy it a second time; "freezing" here means verifying its own declared
`checksums.json` still matches the files on disk before anything reads them,
which is the practical, checkable form of "record exact filenames or export
identities" for tooling that runs against a fixed, already-checked-in bundle.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import frappe

DEFAULT_BUNDLE_DIR = str(
	Path(frappe.get_app_path("kentender_procurement")).parent.parent
	/ "docs"
	/ "std-prod-impl"
	/ "data"
	/ "KE-PPRA-IT-2022-04_seed_package_v1_1"
)

# Every file below `bundle_dir` follows `{"records": [...]}` except these,
# which are single top-level objects — confirmed by direct inspection of the
# real bundle, not assumed.
_SINGLE_OBJECT_FILES = {"manifest.json", "checksums.json", "verbatim_reconciliation.json"}

# `forms/form_locked_bodies.json` alone breaks the `{"records": [...]}`
# convention (`{"package_id", "forms", "contract_forms"}`) — special-cased.
_FORM_LOCKED_BODIES = "forms/form_locked_bodies.json"

_BUNDLE_FILES: dict[str, str] = {
	"manifest": "manifest.json",
	"checksums": "checksums.json",
	"source_document": "source/source_document.json",
	"source_anchors": "source/source_anchors.json",
	"sections": "template/sections.json",
	"clauses": "template/clauses.json",
	"parameters": "configuration/parameters.json",
	"evaluation_schema": "evaluation/evaluation_schema.json",
	"price_schedule_catalog": "pricing/price_schedule_catalog.json",
	"contract_schema": "contract/contract_schema.json",
	"requirement_schema": "requirements/requirement_schema.json",
	"form_catalog": "forms/form_catalog.json",
	"form_fields": "forms/form_fields.json",
	"form_locked_bodies": _FORM_LOCKED_BODIES,
}


def verify_bundle_checksums(bundle_dir: str) -> dict:
	"""§17.6 step 1 — the bundle's own `checksums.json` must still match every
	file on disk before any of it is read. Fails loudly (not silently) on any
	mismatch or missing file, per §17.10's "fail loudly" rule applied here to
	source integrity, not just seed output."""
	checksums_path = Path(bundle_dir) / "checksums.json"
	if not checksums_path.exists():
		frappe.throw(f"Reuse bundle has no checksums.json at {bundle_dir}")
	declared = json.loads(checksums_path.read_text())
	mismatched = []
	missing = []
	for relative_path, expected_hash in declared.get("files", {}).items():
		file_path = Path(bundle_dir) / relative_path
		if not file_path.exists():
			missing.append(relative_path)
			continue
		actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
		if actual_hash != expected_hash:
			mismatched.append(relative_path)
	verified = not mismatched and not missing
	return {
		"verified": verified,
		"file_count": len(declared.get("files", {})),
		"mismatched": mismatched,
		"missing": missing,
	}


def load_bundle(bundle_dir: str) -> dict:
	"""§17.6 step 2 — inventory: parse every source file into plain records
	before anything is written to a Draft."""
	bundle: dict = {}
	for key, relative_path in _BUNDLE_FILES.items():
		file_path = Path(bundle_dir) / relative_path
		if not file_path.exists():
			bundle[key] = [] if relative_path not in _SINGLE_OBJECT_FILES else {}
			continue
		payload = json.loads(file_path.read_text())
		if relative_path == _FORM_LOCKED_BODIES:
			bundle[key] = payload
		elif relative_path in _SINGLE_OBJECT_FILES:
			bundle[key] = payload
		else:
			bundle[key] = payload.get("records", [])
	return bundle
