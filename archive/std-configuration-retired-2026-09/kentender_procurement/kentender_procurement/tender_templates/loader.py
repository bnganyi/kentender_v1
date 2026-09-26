# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §6.3 / STD-TPL-001 v0.5 §15 — the code-owned template
bundle loader.

The bundle under `it_equipment_open_v1/` is a byte-for-byte copy of the
approved curation workspace (`docs/mvp-1-r1/07_tender_templates/
it_equipment_open_v1`). `MANIFEST.sha256` lists every bundle file with its
SHA-256; the bundle digest is the SHA-256 of that manifest. `verify()`
recomputes every file digest and the official-source digest on demand — a
missing file, an altered byte or a register with an unresolved row makes the
template unavailable for new Tenders (TPR-AC-031/033; SMOKE-14). Nothing
here reads a database row or a user-editable field.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any

TEMPLATE_KEY = "IT-EQUIPMENT-OPEN-V1"
TEMPLATE_VERSION = "1.1"
BUNDLE_DIRNAME = "it_equipment_open_v1"
MANIFEST_NAME = "MANIFEST.sha256"

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUNDLE_ROOT = os.path.join(_HERE, BUNDLE_DIRNAME)


def _sha256_file(path: str) -> str:
	h = hashlib.sha256()
	with open(path, "rb") as fh:
		for chunk in iter(lambda: fh.read(1 << 20), b""):
			h.update(chunk)
	return h.hexdigest()


def _sha256_text(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Verification:
	ok: bool
	bundle_root: str
	bundle_digest: str
	source_digest: str
	source_digest_ok: bool
	missing: list[str] = field(default_factory=list)
	mismatched: list[str] = field(default_factory=list)
	unlisted: list[str] = field(default_factory=list)
	register_problems: list[str] = field(default_factory=list)
	notes: list[str] = field(default_factory=list)

	def summary(self) -> str:
		if self.ok:
			return f"bundle {self.bundle_digest[:12]} verified; source {self.source_digest[:12]} verified"
		parts = []
		if self.missing:
			parts.append(f"missing: {', '.join(self.missing)}")
		if self.mismatched:
			parts.append(f"digest mismatch: {', '.join(self.mismatched)}")
		if self.unlisted:
			parts.append(f"unlisted files: {', '.join(self.unlisted)}")
		if not self.source_digest_ok:
			parts.append("official source digest mismatch")
		parts.extend(self.register_problems)
		return "; ".join(parts) or "unverified"


def manifest_path(bundle_root: str = DEFAULT_BUNDLE_ROOT) -> str:
	return os.path.join(bundle_root, MANIFEST_NAME)


def read_manifest(bundle_root: str = DEFAULT_BUNDLE_ROOT) -> dict[str, str]:
	"""{relative path: sha256} as listed in MANIFEST.sha256."""
	path = manifest_path(bundle_root)
	if not os.path.isfile(path):
		return {}
	entries: dict[str, str] = {}
	with open(path, encoding="utf-8") as fh:
		for line in fh:
			line = line.rstrip("\n")
			if not line.strip():
				continue
			digest, _, rel = line.partition("  ")
			entries[rel.strip()] = digest.strip()
	return entries


def bundle_digest(bundle_root: str = DEFAULT_BUNDLE_ROOT) -> str:
	path = manifest_path(bundle_root)
	if not os.path.isfile(path):
		return ""
	return _sha256_file(path)


def metadata(bundle_root: str = DEFAULT_BUNDLE_ROOT) -> dict[str, Any]:
	with open(os.path.join(bundle_root, "metadata.json"), encoding="utf-8") as fh:
		return json.load(fh)


def source_record(bundle_root: str = DEFAULT_BUNDLE_ROOT) -> dict[str, Any]:
	with open(os.path.join(bundle_root, "source_record.json"), encoding="utf-8") as fh:
		return json.load(fh)


def read_text(rel: str, bundle_root: str = DEFAULT_BUNDLE_ROOT) -> str:
	with open(os.path.join(bundle_root, rel), encoding="utf-8") as fh:
		return fh.read()


def _actual_files(bundle_root: str) -> set[str]:
	out: set[str] = set()
	for root, _dirs, files in os.walk(bundle_root):
		if "__pycache__" in root:
			continue
		for name in files:
			if name == MANIFEST_NAME or name.endswith(".pyc"):
				continue
			out.add(os.path.relpath(os.path.join(root, name), bundle_root).replace(os.sep, "/"))
	return out


def _register_problems(bundle_root: str) -> list[str]:
	problems: list[str] = []
	coverage = os.path.join(bundle_root, "coverage_register.csv")
	if os.path.isfile(coverage):
		with open(coverage, encoding="utf-8", newline="") as fh:
			for row in csv.DictReader(fh):
				if (row.get("status") or "").strip() not in ("Reviewed", "Draft checked"):
					problems.append(f"coverage {row.get('coverage_id')} unresolved ({row.get('status')!r})")
				if "[insert" in (row.get("render_location") or ""):
					problems.append(f"coverage {row.get('coverage_id')} carries an [insert] render location")
	for rel in ("templates/invitation_to_tender.html", "templates/complete_tender.html"):
		path = os.path.join(bundle_root, rel)
		if os.path.isfile(path):
			text = open(path, encoding="utf-8").read()
			for token in ("[insert", "Manual Input", "Auto Populate", "select one", "delete if"):
				if token in text:
					problems.append(f"{rel} contains {token!r}")
	return problems


def verify(bundle_root: str = DEFAULT_BUNDLE_ROOT) -> Verification:
	listed = read_manifest(bundle_root)
	src = source_record(bundle_root) if os.path.isfile(os.path.join(bundle_root, "source_record.json")) else {}
	expected_source = (src.get("sha256") or "").lower()
	missing: list[str] = []
	mismatched: list[str] = []
	for rel, digest in sorted(listed.items()):
		path = os.path.join(bundle_root, rel)
		if not os.path.isfile(path):
			missing.append(rel)
			continue
		if _sha256_file(path) != digest:
			mismatched.append(rel)
	unlisted = sorted(_actual_files(bundle_root) - set(listed))
	source_rel = (metadata(bundle_root).get("source") or {}).get("file", "source/ppra_goods_std_official.pdf") if os.path.isfile(os.path.join(bundle_root, "metadata.json")) else "source/ppra_goods_std_official.pdf"
	source_path = os.path.join(bundle_root, source_rel)
	source_digest = _sha256_file(source_path) if os.path.isfile(source_path) else ""
	source_ok = bool(expected_source) and source_digest == expected_source and listed.get(source_rel) == expected_source
	register_problems = _register_problems(bundle_root)
	ok = bool(listed) and not missing and not mismatched and not unlisted and source_ok and not register_problems
	return Verification(
		ok=ok, bundle_root=bundle_root, bundle_digest=bundle_digest(bundle_root), source_digest=source_digest,
		source_digest_ok=source_ok, missing=missing, mismatched=mismatched, unlisted=unlisted,
		register_problems=register_problems,
	)


def compute_manifest_text(bundle_root: str = DEFAULT_BUNDLE_ROOT) -> str:
	"""What MANIFEST.sha256 should contain for the files currently on disk
	(used by the release tooling and the tamper tests, never at runtime)."""
	lines = [f"{_sha256_file(os.path.join(bundle_root, rel))}  {rel}" for rel in sorted(_actual_files(bundle_root))]
	return "\n".join(lines) + "\n"
