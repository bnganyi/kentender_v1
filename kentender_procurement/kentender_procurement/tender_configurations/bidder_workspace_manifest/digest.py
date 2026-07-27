# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Digest format helpers for Bidder Workspace Manifest contracts.

Authority (Phase 2):
- ``document_content_digest`` is required and authoritative for compile/content binding.
- ``archive_provenance_digest`` is optional separate provenance of legal source archives.
"""

from __future__ import annotations

import re

SHA256_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

DOCUMENT_CONTENT_DIGEST_FIELD = "document_content_digest"
ARCHIVE_PROVENANCE_DIGEST_FIELD = "archive_provenance_digest"


def is_sha256_digest(value: object) -> bool:
	return isinstance(value, str) and bool(SHA256_DIGEST_RE.fullmatch(value))


def assert_sha256_digest(value: object, *, field: str = "digest") -> str:
	if not is_sha256_digest(value):
		raise ValueError(f"{field} must match sha256:<64 lowercase hex>; got {value!r}")
	return str(value)
