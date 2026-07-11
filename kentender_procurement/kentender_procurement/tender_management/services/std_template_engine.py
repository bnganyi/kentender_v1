# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Thin compatibility shim after STD Module POC archive.

Planning-to-tender handoff audit still needs deterministic configuration hashing.
The full template engine lives under ``archive/std-module-poc-retired-2026-07/``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def hash_config(config: dict[str, Any]) -> str:
	"""Deterministic SHA-256 hex digest over the full configuration dictionary."""
	payload = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()
