# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Content-addressed store — opaque refs; Frappe private File for physical bytes."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.nfc import (
	nfc_normalize_tree,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_CONTENT_OBJECT,
	DT_MANIFEST_RESOURCE,
)

CONTENT_REF_PREFIX = "bwmf-cas:v1:"
_REF_RE = re.compile(r"^bwmf-cas:v1:([0-9a-f]{64})$")
STORAGE_PROFILE = "frappe_private_file_v1"
_CAS_FOLDER = "Home/BWMF-CAS"


def _ensure_cas_folder() -> None:
	"""Ensure private CAS folder exists (Frappe File folder path)."""
	if frappe.db.exists("File", {"file_name": "BWMF-CAS", "is_folder": 1, "folder": "Home"}):
		return
	folder = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": "BWMF-CAS",
			"is_folder": 1,
			"folder": "Home",
		}
	)
	folder.insert(ignore_permissions=True)


def canonical_json_bytes(value: Any) -> bytes:
	"""NFC + sorted-key compact JSON UTF-8 bytes (resource CAS preimage)."""
	normalized = nfc_normalize_tree(value)

	def sort_obj(o: Any) -> Any:
		if isinstance(o, dict):
			return {k: sort_obj(o[k]) for k in sorted(o.keys())}
		if isinstance(o, list):
			return [sort_obj(x) for x in o]
		return o

	text = json.dumps(sort_obj(normalized), ensure_ascii=False, separators=(",", ":"))
	return text.encode("utf-8")


def content_ref_for_bytes(data: bytes) -> str:
	return CONTENT_REF_PREFIX + hashlib.sha256(data).hexdigest()


def physical_digest_for_bytes(data: bytes) -> str:
	return "sha256:" + hashlib.sha256(data).hexdigest()


def assert_valid_content_ref(content_ref: str) -> str:
	"""Reject File URLs/paths/hosts; only opaque bwmf-cas refs are accepted."""
	ref = (content_ref or "").strip()
	if not ref:
		frappe.throw(_("Missing content_ref."), title="BWMF_CAS_REF")
	lower = ref.lower()
	if (
		lower.startswith("http://")
		or lower.startswith("https://")
		or lower.startswith("file:")
		or "/" in ref
		or "\\" in ref
		or ref.startswith(".")
	):
		frappe.throw(
			_("content_ref must be an opaque CAS address, not a URL or path."),
			title="BWMF_CAS_REF",
		)
	m = _REF_RE.fullmatch(ref)
	if not m:
		frappe.throw(_("Invalid content_ref format."), title="BWMF_CAS_REF")
	return m.group(1)


def _cas_path_for_hex(hex_digest: str) -> Path:
	"""Physical path is derived only from content digest — never from caller paths/URLs."""
	return Path(frappe.get_site_path("private", "files", f"bwmf-cas-{hex_digest}.json"))


def put_canonical_json(
	value: Any,
	*,
	organization: str = "ORG-UNSPECIFIED",
) -> dict[str, str]:
	"""Store exact canonical UTF-8 JSON bytes. Idempotent by content_ref."""
	data = canonical_json_bytes(value)
	content_ref = content_ref_for_bytes(data)
	physical = physical_digest_for_bytes(data)
	hex_digest = hashlib.sha256(data).hexdigest()
	existing = frappe.db.get_value(
		DT_CONTENT_OBJECT,
		{"content_ref": content_ref},
		["name", "physical_digest", "byte_size", "file_name"],
		as_dict=True,
	)
	if existing:
		if existing.physical_digest != physical or int(existing.byte_size) != len(data):
			frappe.throw(
				_("Content object integrity mismatch for {0}").format(content_ref),
				title="BWMF_CAS_CORRUPT",
			)
		# Re-verify physical bytes; never replace.
		get_verified(content_ref)
		return {
			"content_ref": content_ref,
			"physical_object_digest": physical,
			"byte_size": str(len(data)),
		}

	_ensure_cas_folder()
	internal_name = f"bwmf-cas-{hex_digest}.json"
	path = _cas_path_for_hex(hex_digest)
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_bytes(data)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": internal_name,
			"file_url": f"/private/files/{internal_name}",
			"folder": _CAS_FOLDER,
			"is_private": 1,
			"file_size": len(data),
		}
	)
	file_doc.flags.ignore_validate = True
	file_doc.flags.ignore_file_validate = True
	file_doc.insert(ignore_permissions=True)
	written = path.read_bytes()
	if content_ref_for_bytes(written) != content_ref:
		frappe.throw(_("CAS write verification failed."), title="BWMF_CAS_CORRUPT")
	frappe.get_doc(
		{
			"doctype": DT_CONTENT_OBJECT,
			"content_ref": content_ref,
			"physical_digest": physical,
			"byte_size": len(data),
			"file_name": file_doc.name,
			"immutable": 1,
			"organization": organization,
		}
	).insert(ignore_permissions=True)
	return {
		"content_ref": content_ref,
		"physical_object_digest": physical,
		"byte_size": str(len(data)),
	}


def get_verified(content_ref: str) -> bytes:
	"""Load and verify stored bytes against content_ref / physical digest.

	Resolution is only through this authorized adapter — never via File URL/path.
	"""
	hex_digest = assert_valid_content_ref(content_ref)
	row = frappe.db.get_value(
		DT_CONTENT_OBJECT,
		{"content_ref": content_ref},
		["name", "physical_digest", "byte_size", "file_name"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Missing content object."), title="BWMF_CAS_MISSING")
	if not row.file_name or not frappe.db.exists("File", row.file_name):
		frappe.throw(_("Missing content file."), title="BWMF_CAS_MISSING")
	path = _cas_path_for_hex(hex_digest)
	try:
		data = path.read_bytes()
	except FileNotFoundError:
		frappe.throw(_("Missing physical bytes."), title="BWMF_CAS_MISSING")
	expected_ref = content_ref_for_bytes(data)
	physical = physical_digest_for_bytes(data)
	if expected_ref != content_ref or physical != row.physical_digest or len(data) != int(row.byte_size):
		frappe.throw(_("Stored byte corruption detected."), title="BWMF_CAS_CORRUPT")
	return data


def assert_content_not_deletable(content_ref: str) -> None:
	"""Reject delete/replace while referenced by a Manifest Resource or binding."""
	if frappe.db.exists(DT_MANIFEST_RESOURCE, {"content_ref": content_ref}):
		frappe.throw(
			_("Content object is referenced by a Manifest Resource."),
			title="BWMF_CAS_REFERENCED",
		)
	if frappe.db.exists(DT_ARTIFACT_RESOURCE_BINDING, {"content_ref": content_ref}):
		frappe.throw(
			_("Content object is referenced by an artifact binding."),
			title="BWMF_CAS_REFERENCED",
		)


def assert_content_not_replaceable(content_ref: str) -> None:
	"""Referenced content objects are immutable — replace is forbidden."""
	assert_content_not_deletable(content_ref)
	if frappe.db.exists(DT_CONTENT_OBJECT, {"content_ref": content_ref}):
		frappe.throw(
			_("Content object cannot be replaced."),
			title="BWMF_CAS_REPLACE",
		)


def delete_content_via_repository(content_ref: str) -> None:
	"""Authorized delete path — fails closed when referenced."""
	assert_valid_content_ref(content_ref)
	assert_content_not_deletable(content_ref)
	row = frappe.db.get_value(
		DT_CONTENT_OBJECT,
		{"content_ref": content_ref},
		["name", "file_name"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Missing content object."), title="BWMF_CAS_MISSING")
	if row.file_name and frappe.db.exists("File", row.file_name):
		frappe.delete_doc("File", row.file_name, force=1, ignore_permissions=True)
	frappe.delete_doc(DT_CONTENT_OBJECT, row.name, force=1, ignore_permissions=True)


def prevent_cas_file_trash(doc, method=None) -> None:
	"""doc_events hook: block trash of Files backing referenced Content Objects."""
	if frappe.flags.get("bwmf_force_clear"):
		return
	if doc.is_folder or (doc.folder or "") != _CAS_FOLDER:
		return
	content_ref = frappe.db.get_value(DT_CONTENT_OBJECT, {"file_name": doc.name}, "content_ref")
	if content_ref:
		assert_content_not_deletable(content_ref)


def parse_content_ref(content_ref: str) -> str:
	return assert_valid_content_ref(content_ref)
