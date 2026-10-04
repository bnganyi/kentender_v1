# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Controlled-asset inventory and digests (STD-TPL-001 v0.10 §13.9;
STD-TPL-IMP-001 v1.0 §5.2).

`bundle_digest` is SHA-256 over the UTF-8 sequence of each bytewise-sorted
relative path, a NUL byte, its lowercase SHA-256 and a newline. The manifest
itself and the two post-manifest review files (`05_review/review_record.md`,
`05_review/owner_decision.json`) are outside the inventory, so no digest
refers to itself.

A generated golden vector cannot contain the digest of the bundle that
contains it, so every curation vector is compiled against the *input*
digest: the same algorithm over every asset except the generated outputs
(owner ruling R13). Pure Python: no Frappe import.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
from pathlib import Path, PurePosixPath

from kentender_procurement.std_templates.compiler.errors import fail

MANIFEST_PATH = "06_runtime/release_manifest.json"
REVIEW_RECORD_PATH = "05_review/review_record.md"
OWNER_DECISION_PATH = "05_review/owner_decision.json"

#: Never inventoried: the manifest, the post-manifest review files, caches.
INVENTORY_EXCLUSIONS: tuple[str, ...] = (MANIFEST_PATH, REVIEW_RECORD_PATH, OWNER_DECISION_PATH)
_TRANSIENT = ("*/__pycache__/*", "__pycache__/*", "*.pyc", "*.pyo", "*/.DS_Store", ".DS_Store", "*~", "*.swp")

#: Generated outputs: inventoried in the bundle, excluded from the input digest.
GENERATED_OUTPUTS: tuple[str, ...] = (
	"04_fixture/*_expected.html",
	"04_fixture/*_expected.pdf",
	"04_fixture/reservation_variants/*_expected.json",
	"06_runtime/*_expected.json",
	"05_review/validation_report.json",
	"05_review/release_gates.json",
	"05_review/release_change_report.json",
)


def file_digest(path: str | os.PathLike) -> str:
	h = hashlib.sha256()
	with open(path, "rb") as fh:
		for chunk in iter(lambda: fh.read(1 << 20), b""):
			h.update(chunk)
	return h.hexdigest()


def bytes_digest(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def is_transient(rel: str) -> bool:
	return any(fnmatch.fnmatch(rel, pattern) for pattern in _TRANSIENT)


def is_generated(rel: str) -> bool:
	return any(fnmatch.fnmatch(rel, pattern) for pattern in GENERATED_OUTPUTS)


def safe_relative(rel: str) -> str:
	"""Reject absolute paths, parent traversal, empty segments, backslashes
	and control characters; return the normalised POSIX relative path."""
	if not isinstance(rel, str) or not rel or "\x00" in rel or "\\" in rel or any(ord(c) < 32 for c in rel):
		fail("STD_RELEASE_INTEGRITY_FAILED", "An asset path is not a plain relative path.", identity=str(rel)[:120])
	path = PurePosixPath(rel)
	if path.is_absolute() or any(part in ("", ".", "..") for part in rel.split("/")):
		fail("STD_RELEASE_INTEGRITY_FAILED", "An asset path leaves the package root.", identity=rel)
	return str(path)


def inventory(root: str | os.PathLike) -> list[tuple[str, str]]:
	"""Every controlled file under `root` as (relative path, sha256), sorted
	bytewise. Symbolic links anywhere in the tree are refused."""
	base = Path(root)
	out: list[tuple[str, str]] = []
	for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
		for name in list(dirnames):
			if os.path.islink(os.path.join(dirpath, name)):
				fail("STD_RELEASE_INTEGRITY_FAILED", "The package contains a symbolic link.", identity=os.path.relpath(os.path.join(dirpath, name), base))
		for name in filenames:
			full = os.path.join(dirpath, name)
			rel = os.path.relpath(full, base).replace(os.sep, "/")
			if os.path.islink(full):
				fail("STD_RELEASE_INTEGRITY_FAILED", "The package contains a symbolic link.", identity=rel)
			if rel in INVENTORY_EXCLUSIONS or is_transient(rel):
				continue
			out.append((safe_relative(rel), file_digest(full)))
	out.sort(key=lambda entry: entry[0].encode("utf-8"))
	return out


def bundle_digest(entries: list[tuple[str, str]]) -> str:
	seen: set[str] = set()
	h = hashlib.sha256()
	for rel, digest in sorted(entries, key=lambda entry: entry[0].encode("utf-8")):
		if rel in seen:
			fail("STD_RELEASE_INTEGRITY_FAILED", "Duplicate asset path.", identity=rel)
		seen.add(rel)
		h.update(rel.encode("utf-8") + b"\x00" + digest.lower().encode("ascii") + b"\n")
	return h.hexdigest()


def input_entries(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
	return [(rel, digest) for rel, digest in entries if not is_generated(rel)]


def candidate_bundle_digest(root: str | os.PathLike) -> str:
	"""The input digest every curation golden vector is compiled against."""
	return bundle_digest(input_entries(inventory(root)))
