# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Unicode NFC normalization for BWMF digests (contract §10.1)."""

from __future__ import annotations

import unicodedata
from typing import Any


def nfc_normalize_tree(value: Any) -> Any:
	"""Recursively NFC-normalize all strings in a JSON-like structure."""
	if isinstance(value, str):
		return unicodedata.normalize("NFC", value)
	if isinstance(value, dict):
		return {nfc_normalize_tree(k) if isinstance(k, str) else k: nfc_normalize_tree(v) for k, v in value.items()}
	if isinstance(value, list):
		return [nfc_normalize_tree(v) for v in value]
	return value
