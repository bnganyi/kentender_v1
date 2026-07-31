# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Machine gate — every Stitch *_code.html must have a contract that the port satisfies.

Contracts are authored from Stitch (regions/classes/testids), not reverse-fitted to
lazy Jinja. Soft string layout guards are insufficient for UI Done.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_V1_ROOT = Path(__file__).resolve().parents[4]
_APP_PKG = Path(__file__).resolve().parents[2]

_FINAL_SUBMISSION_PACK = (
	_V1_ROOT
	/ "docs"
	/ "std-prod-impl"
	/ "IT-STD-Wizard-v3"
	/ "G1-IT-STD-Canonical-Config-Recovery"
	/ "12_Final_Submission"
)

# Register packs here as contracts are authored. Gate fails closed for listed packs.
_CONTRACT_PACKS: tuple[Path, ...] = (_FINAL_SUBMISSION_PACK,)


def _code_stems(pack: Path) -> list[str]:
	stems: list[str] = []
	for path in sorted(pack.glob("*_code.html")):
		# 01_code.html → 01 ; step_02_code.html → step_02
		name = path.name
		if name.endswith("_code.html"):
			stems.append(name[: -len("_code.html")])
	return stems


def _load_contract(path: Path) -> dict:
	return json.loads(path.read_text(encoding="utf-8"))


def _concat_impl(repo_root: Path, rel_paths: list[str]) -> str:
	chunks: list[str] = []
	for rel in rel_paths:
		full = repo_root / rel
		if not full.is_file():
			raise FileNotFoundError(f"Contract implementation_files missing: {rel}")
		chunks.append(full.read_text(encoding="utf-8"))
	return "\n".join(chunks)


def _assert_contract(case: unittest.TestCase, pack: Path, contract_path: Path) -> None:
	contract = _load_contract(contract_path)
	stitch = pack / str(contract.get("stitch_file") or "")
	case.assertTrue(stitch.is_file(), f"{contract_path.name}: stitch_file missing ({stitch.name})")

	impl_files = contract.get("implementation_files") or []
	case.assertTrue(impl_files, f"{contract_path.name}: implementation_files required")
	blob = _concat_impl(_V1_ROOT, impl_files)

	for marker in contract.get("required_markers") or []:
		case.assertIn(
			marker,
			blob,
			f"{contract.get('surface_id')}: missing required_marker {marker!r}",
		)
	for cls in contract.get("required_classes") or []:
		case.assertIn(
			cls,
			blob,
			f"{contract.get('surface_id')}: missing required_class {cls!r}",
		)
	for text in contract.get("required_text") or []:
		case.assertIn(
			text,
			blob,
			f"{contract.get('surface_id')}: missing required_text {text!r}",
		)
	for bad in contract.get("forbidden_markers") or []:
		case.assertNotIn(
			bad,
			blob,
			f"{contract.get('surface_id')}: forbidden_marker present {bad!r}",
		)


class TestBidderStitchContractGate(unittest.TestCase):
	def test_registered_packs_have_contract_per_stitch_file(self) -> None:
		for pack in _CONTRACT_PACKS:
			self.assertTrue(pack.is_dir(), f"Pack missing: {pack}")
			stems = _code_stems(pack)
			self.assertTrue(stems, f"No *_code.html in {pack}")
			for stem in stems:
				contract = pack / f"{stem}.contract.json"
				self.assertTrue(
					contract.is_file(),
					f"Missing contract for Stitch surface {stem}_code.html → expected {contract.name}",
				)

	def test_final_submission_contracts_match_implementation(self) -> None:
		pack = _FINAL_SUBMISSION_PACK
		for stem in _code_stems(pack):
			_assert_contract(self, pack, pack / f"{stem}.contract.json")

	def test_contract_schema_doc_present(self) -> None:
		self.assertTrue((_FINAL_SUBMISSION_PACK / "CONTRACT_SCHEMA.md").is_file())
