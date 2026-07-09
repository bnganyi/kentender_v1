# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SHA-256 helpers for STD package import reports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def compute_file_sha256(path: str | Path) -> str:
	file_path = Path(path)
	digest = hashlib.sha256()
	with file_path.open("rb") as handle:
		for chunk in iter(lambda: handle.read(65536), b""):
			digest.update(chunk)
	return digest.hexdigest()


def compute_manifest_hash(manifest: dict[str, Any]) -> str:
	canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
