# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — canonical content and handoff digests (§5.2, §5.5,
§5.12). One canonicalisation used everywhere a digest is created: sorted
keys, no whitespace, ISO/str for anything JSON can't natively encode.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any


def _default(value: Any) -> Any:
	if isinstance(value, (datetime, date)):
		return value.isoformat()
	return str(value)


def canonical_json(payload: dict[str, Any]) -> str:
	return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_default)


def sha256_hex(payload: dict[str, Any]) -> str:
	return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
