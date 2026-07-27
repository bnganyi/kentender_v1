# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RFC 8785 JSON Canonicalization Scheme (JCS) + SHA-256 digest helpers.

Not ``json.dumps(..., sort_keys=True)`` alone — implements JCS string escaping,
lexicographic key order, and reject rules for floats / non-finite numbers.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from typing import Any


class JcsError(ValueError):
	"""Raised when a value cannot be JCS-canonicalized."""


_CTRL_ESCAPE = {
	0x08: "\\b",
	0x09: "\\t",
	0x0A: "\\n",
	0x0C: "\\f",
	0x0D: "\\r",
}


def jcs_canonicalize(value: Any) -> str:
	"""Return the RFC 8785 JCS string for ``value`` (UTF-8 text, no trailing newline)."""
	return _serialize(value)


def jcs_sha256_digest(value: Any) -> str:
	"""Return ``sha256:<hex>`` of UTF-8 encoded JCS bytes.

	BWMF contract §10.1 requires Unicode NFC normalization before JCS.
	Canonically equivalent strings (NFC vs NFD) therefore share a digest.
	"""
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.nfc import (
		nfc_normalize_tree,
	)

	canonical = jcs_canonicalize(nfc_normalize_tree(value))
	digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
	return f"sha256:{digest}"


def pack_equivalent_digest(value: Any) -> str:
	"""Pack §8.2 recovery normalization (NFC + sorted keys + compact separators).

	Used only for golden projection / diagnostic oracle comparison against pack digests.
	Production full-payload digests must use :func:`jcs_sha256_digest`.
	"""

	def norm(o: Any) -> Any:
		if isinstance(o, dict):
			return {k: norm(o[k]) for k in sorted(o.keys())}
		if isinstance(o, list):
			return [norm(x) for x in o]
		if isinstance(o, str):
			return unicodedata.normalize("NFC", o)
		if isinstance(o, float):
			raise JcsError("float values are not permitted in pack-equivalent digests")
		return o

	text = json_compact(norm(value))
	text = unicodedata.normalize("NFC", text)
	return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def json_compact(value: Any) -> str:
	"""Compact JSON with sorted object keys (arrays preserve order)."""
	import json

	return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _serialize(value: Any) -> str:
	if value is None:
		return "null"
	if value is True:
		return "true"
	if value is False:
		return "false"
	if isinstance(value, str):
		return _serialize_string(value)
	if isinstance(value, int) and not isinstance(value, bool):
		return str(value)
	if isinstance(value, float):
		raise JcsError("IEEE-754 float values are rejected; use decimal strings for money")
	if isinstance(value, dict):
		return _serialize_object(value)
	if isinstance(value, list):
		return "[" + ",".join(_serialize(v) for v in value) + "]"
	raise JcsError(f"unsupported JCS type: {type(value).__name__}")


def _utf16_code_units(s: str) -> tuple[int, ...]:
	"""RFC 8785 §3.2.3 — lexicographic order by UTF-16 code units."""
	units: list[int] = []
	for ch in s:
		cp = ord(ch)
		if cp >= 0x10000:
			cp -= 0x10000
			units.append(0xD800 + (cp >> 10))
			units.append(0xDC00 + (cp & 0x3FF))
		else:
			units.append(cp)
	return tuple(units)


def _serialize_object(obj: dict[str, Any]) -> str:
	parts: list[str] = []
	for key in sorted(obj.keys(), key=_utf16_code_units):
		if not isinstance(key, str):
			raise JcsError("object keys must be strings")
		parts.append(_serialize_string(key) + ":" + _serialize(obj[key]))
	return "{" + ",".join(parts) + "}"


def _serialize_string(s: str) -> str:
	# Escapes follow JSON + RFC 8785 §3.2.2.2.
	out = ['"']
	for ch in s:
		o = ord(ch)
		if ch == '"':
			out.append('\\"')
		elif ch == "\\":
			out.append("\\\\")
		elif o in _CTRL_ESCAPE:
			out.append(_CTRL_ESCAPE[o])
		elif o < 0x20:
			out.append(f"\\u{o:04x}")
		else:
			out.append(ch)
	out.append('"')
	return "".join(out)


def assert_no_float(value: Any, *, path: str = "$") -> None:
	"""Walk a structure and reject float / non-finite numbers."""
	if isinstance(value, float):
		if not math.isfinite(value):
			raise JcsError(f"{path}: non-finite number")
		raise JcsError(f"{path}: float not permitted")
	if isinstance(value, dict):
		for k, v in value.items():
			assert_no_float(v, path=f"{path}.{k}")
	elif isinstance(value, list):
		for i, v in enumerate(value):
			assert_no_float(v, path=f"{path}[{i}]")


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def is_sha256_digest(value: str) -> bool:
	return bool(_SHA256_RE.fullmatch(value or ""))
