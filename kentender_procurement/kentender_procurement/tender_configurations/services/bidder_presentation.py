# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bidder-facing presentation boundary — explicit allowlists, no internal package leakage.

Rule: Bidder-facing screens and APIs must expose only information needed to understand
or complete a bidder task. Internal hashes, digests, schema names, manifest identifiers,
configuration references, database IDs, artifact types and audit metadata must never
appear in bidder-visible HTML, API DTOs, accessibility text, tooltips, filenames or
error messages.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote

from frappe.utils import cstr

# Technical tokens that must not appear in bidder-facing DTO values or rendered HTML.
# Prefer specific internal labels over broad words like "schema" alone.
FORBIDDEN_BIDDER_PRESENTATION_PATTERNS = (
	re.compile(r"\bpackage\s*artifact\b", re.I),
	re.compile(r"\bsha-?256\b", re.I),
	re.compile(r"\bdocument_hash\b", re.I),
	re.compile(r"\baddenda_set_digest\b", re.I),
	re.compile(r"\bconfiguration_version\b", re.I),
	re.compile(r"\bpackage_context\b", re.I),
	re.compile(r"\bpackage_summary\b", re.I),
	re.compile(r"\bconfirmed_package\b", re.I),
	re.compile(r"\breadiness report\b", re.I),
	re.compile(r"\bbidder submission schema\b", re.I),
	re.compile(r"\bevaluation schema\b", re.I),
	re.compile(r"\bprice schedule schema\b", re.I),
	re.compile(r"\bforms/evidence schema\b", re.I),
	re.compile(r"\bcontract carry-forward\b", re.I),
	re.compile(r"\btender configuration reference\b", re.I),
	re.compile(r"\bprocurement package reference\b", re.I),
	re.compile(r"\bstd version record\b", re.I),
	re.compile(r"\bconfiguration version record\b", re.I),
	re.compile(r"\bbwmf\b", re.I),
	re.compile(r"\bmanifest\b", re.I),
	re.compile(r"(?i)(?:digest|hash)\s*[:=]"),
	re.compile(r"(?i)current package\s*:"),
)

# Hex digests (not public PUB-* business refs).
_HEX_DIGEST_RE = re.compile(r"^[a-f0-9]{32,}$", re.I)
_HASH_IN_TEXT_RE = re.compile(r"\b[a-f0-9]{40,}\b", re.I)

BIDDER_DOCUMENT_ROW_KEYS = frozenset(
	{
		"document_key",
		"name",
		"title",
		"category",
		"version_label",
		"published_at",
		"published_at_display",
		"type",
		"size",
		"icon",
		"can_view",
		"can_download",
		"view_url",
		"download_url",
		"acknowledgement_required",
		"acknowledgement_status",
	}
)

BIDDER_ADDENDUM_ROW_KEYS = frozenset(
	{
		"id",
		"title",
		"ref",
		"summary",
		"published_at",
		"issued_at",
		"version_label",
		"requires_acknowledgement",
		"acknowledgement_status",
		"acknowledged",
		"is_new",
		"attachment_name",
		"attachment_url",
		"view_url",
	}
)

# Top-level keys allowed on the A3 documents/addenda bidder DTO.
BIDDER_DOCUMENTS_DTO_KEYS = frozenset(
	{
		"published_tender_ref",
		"tender_title",
		"procuring_entity",
		"workspace_url",
		"documents_url",
		"overview_url",
		"submission_deadline",
		"submission_deadline_display",
		"time_remaining_label",
		"documents",
		"primary_pdf_url",
		"addenda",
		"addenda_empty",
		"addenda_empty_message",
		"acknowledgement_status",
		"section_status",
		"documents_acknowledged",
		"acknowledgement_stale",
		"addenda_block_submission",
		"readiness",
		"acknowledge_label",
		"acknowledge_enabled",
		"continue_label",
		"continue_enabled",
		"continue_url",
		"back_to_checklist_label",
		"back_to_checklist_url",
		# Shell fields shared with A2 sidebar include (presentation only).
		"section_key",
		"section_title",
	}
)

# Keys that must never appear on bidder-facing A0–A4 DTOs.
BIDDER_FORBIDDEN_DTO_KEYS = frozenset(
	{
		"package_summary",
		"package_context",
		"package_display",
		"confirmed_package",
		"document_hash",
		"configuration_version",
		"addenda_set_digest",
		"package_id",
		"publication_id",
		"configuration_id",
		"configuration_ref",
		"desk_bridge_url",
		"desk_bridge_next_url",
		"desk_section_bridge_url",
		"acknowledgement_history_count",
		"acknowledgement_history",
		"schema_hash",
		"bid_id",
	}
)


def looks_like_technical_hash(value: Any) -> bool:
	text = cstr(value or "").strip()
	if not text:
		return False
	if text.upper().startswith("PUB-"):
		return False
	if _HEX_DIGEST_RE.match(text):
		return True
	# Mixed labels that embed a long hex digest.
	return bool(_HASH_IN_TEXT_RE.search(text))


def human_version_label(raw: Any, *, fallback: str = "") -> str:
	"""Return a formal human version label, never a technical hash."""
	label = cstr(raw or "").strip()
	if not label or looks_like_technical_hash(label):
		return cstr(fallback or "").strip()
	return label


def published_tender_pdf_url(published_tender_ref: str) -> str:
	"""Bidder PDF download keyed by public publication_ref (no configuration_id)."""
	ref = quote(cstr(published_tender_ref or "").strip(), safe="")
	return (
		"/api/method/kentender_procurement.tender_configurations"
		f".download_published_tender_document_pdf?published_tender_ref={ref}"
	)


def project_bidder_document_row(
	row: dict[str, Any] | None,
	*,
	published_tender_ref: str = "",
	published_at: str = "",
	published_at_display: str = "",
) -> dict[str, Any]:
	src = row if isinstance(row, dict) else {}
	title = cstr(src.get("name") or src.get("title") or "").strip() or "Official Tender Document"
	can_view = bool(src.get("can_view") if "can_view" in src else src.get("view_url"))
	can_download = bool(src.get("can_download") if "can_download" in src else src.get("download_url"))
	pdf = published_tender_pdf_url(published_tender_ref) if published_tender_ref else ""
	view_url = cstr(src.get("view_url") or "")
	download_url = cstr(src.get("download_url") or "")
	if pdf and (
		src.get("document_key") == "tender_pdf"
		or cstr(src.get("type")).upper() == "PDF"
		or "configuration_id=" in view_url
		or "configuration_id=" in download_url
	):
		view_url = pdf if can_view or src.get("document_key") == "tender_pdf" else view_url
		download_url = pdf if can_download or src.get("document_key") == "tender_pdf" else download_url
		can_view = bool(view_url)
		can_download = bool(download_url)

	version_label = human_version_label(src.get("version_label") or src.get("version"))
	# Never use a hash as the version; prefer publication date or omit.
	if not version_label and published_at_display:
		version_label = ""

	out = {
		"document_key": cstr(src.get("document_key") or ""),
		"name": title,
		"title": title,
		"category": cstr(src.get("category") or "Official tender document"),
		"version_label": version_label,
		"published_at": cstr(src.get("published_at") or published_at or ""),
		"published_at_display": cstr(src.get("published_at_display") or published_at_display or ""),
		"type": cstr(src.get("type") or ""),
		"size": cstr(src.get("size") or "") or "—",
		"icon": cstr(src.get("icon") or "description"),
		"can_view": 1 if can_view else 0,
		"can_download": 1 if can_download else 0,
		"view_url": view_url,
		"download_url": download_url,
		"acknowledgement_required": 1 if src.get("acknowledgement_required") else 0,
		"acknowledgement_status": cstr(src.get("acknowledgement_status") or ""),
	}
	return {k: out[k] for k in BIDDER_DOCUMENT_ROW_KEYS if k in out}


def project_bidder_addendum_row(row: dict[str, Any] | None) -> dict[str, Any]:
	src = row if isinstance(row, dict) else {}
	acked = bool(src.get("acknowledged"))
	requires = bool(src.get("requires_acknowledgement"))
	version_label = human_version_label(
		src.get("version_label") or src.get("version"),
		fallback="",
	)
	# Prefer addendum business id/ref over hash-like version fields.
	ref = cstr(src.get("ref") or src.get("id") or "").strip()
	if looks_like_technical_hash(ref):
		ref = ""
	out = {
		"id": cstr(src.get("id") or "").strip(),
		"title": cstr(src.get("title") or src.get("name") or "").strip(),
		"ref": ref,
		"summary": cstr(src.get("summary") or ""),
		"published_at": cstr(src.get("published_at") or src.get("issued_at") or ""),
		"issued_at": cstr(src.get("issued_at") or src.get("published_at") or ""),
		"version_label": version_label,
		"requires_acknowledgement": 1 if requires else 0,
		"acknowledgement_status": "Acknowledged" if acked else ("Action Required" if requires else ""),
		"acknowledged": 1 if acked else 0,
		"is_new": 1 if src.get("is_new") else 0,
		"attachment_name": cstr(src.get("attachment_name") or ""),
		"attachment_url": cstr(src.get("attachment_url") or ""),
		"view_url": cstr(src.get("view_url") or ""),
	}
	return {k: out[k] for k in BIDDER_ADDENDUM_ROW_KEYS if k in out}


def allowlist_dict(payload: dict[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
	return {k: payload[k] for k in allowed if k in payload}


def assert_no_forbidden_bidder_keys(payload: Any, *, path: str = "root") -> list[str]:
	"""Return list of violation messages for forbidden keys nested in a DTO."""
	violations: list[str] = []
	if isinstance(payload, dict):
		for key, value in payload.items():
			here = f"{path}.{key}"
			if key in BIDDER_FORBIDDEN_DTO_KEYS:
				violations.append(f"forbidden key {here}")
			violations.extend(assert_no_forbidden_bidder_keys(value, path=here))
	elif isinstance(payload, list):
		for idx, item in enumerate(payload):
			violations.extend(assert_no_forbidden_bidder_keys(item, path=f"{path}[{idx}]"))
	return violations


def scan_bidder_presentation_text(text: str, *, include_hex_digests: bool = False) -> list[str]:
	"""Return matched forbidden presentation patterns in DTO JSON or rendered HTML.

	Hex digests are checked for API DTOs by default. Full HTML pages often contain
	asset content hashes, so callers should pass include_hex_digests=False for HTML
	and assert the known package digest separately.
	"""
	blob = cstr(text or "")
	hits: list[str] = []
	for pattern in FORBIDDEN_BIDDER_PRESENTATION_PATTERNS:
		if pattern.search(blob):
			hits.append(pattern.pattern)
	if include_hex_digests:
		for match in _HASH_IN_TEXT_RE.findall(blob):
			if not match.upper().startswith("PUB"):
				hits.append(f"hex_digest:{match[:12]}…")
	return hits


def dto_as_scan_text(payload: Any) -> str:
	try:
		return json.dumps(payload, ensure_ascii=False, default=str)
	except (TypeError, ValueError):
		return cstr(payload)
