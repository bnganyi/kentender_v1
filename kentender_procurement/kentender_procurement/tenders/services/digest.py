# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.2/§4.6–4.10 — canonical digests. One canonicalisation
used everywhere a digest is created: sorted keys, no whitespace, ISO/str for
anything JSON cannot natively encode. Identical recorded inputs therefore
produce the recorded digest (TPR08-AC-024).
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _default(value: Any) -> Any:
	if isinstance(value, (datetime, date)):
		return value.isoformat()
	if isinstance(value, Decimal):
		return str(value)
	return str(value)


def canonical_json(payload: Any) -> str:
	return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_default)


def sha256_hex(payload: Any) -> str:
	return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
	return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
