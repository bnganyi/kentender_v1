# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-006 / LV-R1-006-01 — **Procurement Handoff Evidence Link** contract (cursor pack §6.4).

**Storage decision (JSON vs child table):** we persist evidence on
:class:`~frappe.model.document.Document` **Procurement Handoff Card** in the
``evidence_links_json`` **JSON** field as::

    {"links": [<link>, ...]}

Frappe JSON columns reject a **top-level JSON array**, so the ``{"links": …}``
wrapper is mandatory on disk. Callers may pass a bare list; it is normalized
before validation. A dedicated **child table** DocType remains a future option
if we need row-level permissions or per-link workflow; it was deferred here to
keep R1-006 bounded and avoid extra DocType sync during PLC bootstrap.

**Size strategy:** cap link count and UTF-8 serialized payload size so Desk/API
cannot attach unbounded blobs to navigation artifacts (ADR-PLC-002).
"""

from __future__ import annotations

import json
from typing import Any, Final

# Cursor pack §6.4 — required keys on each link object.
EVIDENCE_LINK_REQUIRED_KEYS: Final[tuple[str, ...]] = (
	"label",
	"object_type",
	"object_code",
	"module",
	"route",
	"visibility",
)

# Visibility vocabulary (internal vs supplier-facing vs public). Extend deliberately.
EVIDENCE_LINK_VISIBILITY_VALUES: Final[frozenset[str]] = frozenset(
	("Internal", "Supplier", "Public"),
)

EVIDENCE_LINKS_JSON_STORAGE_DECISION: Final[str] = "json_object_with_links_array"

EVIDENCE_LINKS_MAX_LINKS: Final[int] = 50
EVIDENCE_LINKS_MAX_SERIALIZED_BYTES: Final[int] = 65_536
EVIDENCE_LINK_FIELD_MAX_CHARS: Final[int] = 2048


def normalize_evidence_links_raw(raw: Any) -> dict[str, Any]:
	"""Return ``{"links": [...]}`` from JSON field value, DB string, dict, or bare list.

	Raises:
		ValueError: if the payload cannot be interpreted as links data.
	"""
	if raw is None or raw == "":
		return {"links": []}
	if isinstance(raw, str):
		try:
			parsed: Any = json.loads(raw)
		except json.JSONDecodeError as exc:
			raise ValueError("evidence_links_json is not valid JSON") from exc
		return normalize_evidence_links_raw(parsed)
	if isinstance(raw, list):
		return {"links": raw}
	if isinstance(raw, dict):
		if "links" not in raw:
			raise ValueError("evidence_links_json object must include a 'links' array")
		return {"links": raw["links"]}
	raise ValueError("evidence_links_json must be a JSON object, array, or string")


def evidence_links_serialized_byte_length(wrapper: dict[str, Any]) -> int:
	"""UTF-8 byte length of canonical JSON (stable key order per link for rough stability)."""
	links = wrapper.get("links")
	if not isinstance(links, list):
		return 0
	canonical = {
		"links": [
			{k: item[k] for k in sorted(item.keys())} if isinstance(item, dict) else item for item in links
		]
	}
	return len(json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def validate_evidence_links_normalized(wrapper: dict[str, Any]) -> None:
	"""Validate ``{"links":[...]}`` after normalization (pack §6.4 + size caps).

	Raises:
		ValueError: on missing keys, bad types, unknown visibility, or limits exceeded.
	"""
	if not isinstance(wrapper, dict):
		raise ValueError("evidence_links_json must be a JSON object")
	links = wrapper.get("links")
	if not isinstance(links, list):
		raise ValueError("'links' must be a JSON array")
	if len(links) > EVIDENCE_LINKS_MAX_LINKS:
		raise ValueError(
			f"At most {EVIDENCE_LINKS_MAX_LINKS} evidence links are allowed (got {len(links)})"
		)
	for i, item in enumerate(links):
		if not isinstance(item, dict):
			raise ValueError(f"Evidence link {i} must be a JSON object")
		for key in EVIDENCE_LINK_REQUIRED_KEYS:
			if key not in item:
				raise ValueError(f"Evidence link {i} is missing required field {key!r}")
			val = item[key]
			if not isinstance(val, str):
				raise ValueError(f"Evidence link {i}: field {key!r} must be a string")
			stripped = val.strip()
			if not stripped:
				raise ValueError(f"Evidence link {i}: field {key!r} must be non-empty")
			if len(stripped) > EVIDENCE_LINK_FIELD_MAX_CHARS:
				raise ValueError(
					f"Evidence link {i}: field {key!r} exceeds {EVIDENCE_LINK_FIELD_MAX_CHARS} characters"
				)
			if key == "visibility" and stripped not in EVIDENCE_LINK_VISIBILITY_VALUES:
				raise ValueError(
					f"Evidence link {i}: visibility {stripped!r} must be one of "
					f"{sorted(EVIDENCE_LINK_VISIBILITY_VALUES)}"
				)
			item[key] = stripped

	byte_len = evidence_links_serialized_byte_length(wrapper)
	if byte_len > EVIDENCE_LINKS_MAX_SERIALIZED_BYTES:
		raise ValueError(
			f"Evidence links JSON exceeds maximum size ({byte_len} bytes > "
			f"{EVIDENCE_LINKS_MAX_SERIALIZED_BYTES} bytes)"
		)


def parse_validate_and_normalize_evidence_links(raw: Any) -> dict[str, Any]:
	"""Normalize then validate; returns a dict safe to assign to ``evidence_links_json``."""
	wrapper = normalize_evidence_links_raw(raw)
	validate_evidence_links_normalized(wrapper)
	return wrapper
