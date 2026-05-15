# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-007 — **Technical references** JSON on Procurement Handoff Card (rectification pack §7.5).

Structured codes (tender, STD template/instance, publication snapshot, etc.) stay in
``technical_refs_json``, separate from user-facing ``locked_summary`` /
``passed_forward_summary`` / ``evidence_links_json``. Desk shows this block inside a
**collapsible** section (``procurement_handoff_card.json``) so it is **hidden by default**
(see ``layout.js`` ``refresh_section_collapse``).

Validation is intentionally lighter than evidence links: any JSON **object or array**,
bounded by serialized UTF-8 size so APIs cannot attach huge blobs.
"""

from __future__ import annotations

import json
from typing import Any, Final

TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES: Final[int] = 32_768


def parse_validate_technical_refs_json(raw: Any) -> dict | list | None:
	"""Return normalized JSON value for ``technical_refs_json``, or ``None`` when empty.

	Raises:
		ValueError: if not JSON object/array or if serialized size exceeds the cap.
	"""
	if raw is None or raw == "" or raw == {} or raw == []:
		return None
	if isinstance(raw, str):
		try:
			parsed: Any = json.loads(raw)
		except json.JSONDecodeError as exc:
			raise ValueError("technical_refs_json is not valid JSON") from exc
		return parse_validate_technical_refs_json(parsed)
	if isinstance(raw, (dict, list)):
		payload = json.dumps(raw, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
		if len(payload) > TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES:
			raise ValueError(
				f"technical_refs_json exceeds maximum size ({len(payload)} bytes > "
				f"{TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES} bytes)"
			)
		return raw
	raise ValueError("technical_refs_json must be a JSON object or array")
