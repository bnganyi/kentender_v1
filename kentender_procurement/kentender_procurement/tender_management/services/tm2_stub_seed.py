# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §8.4 / §20.1–20.2 — TM2 Works open-tender **stub** fixture (no full STD engine).

This module loads ``tender_management/fixtures/tm2_seed_works_open_tender.json`` for
deterministic constants used in CI and tests when the database is not seeded with the
full N-pack loader (doc 9 §20.3).

**Stub limitations (must stay explicit):**

- JSON is **not** inserted into Frappe; it does not replace ``Tender STD Instance``,
  ``Tender STD Generated Output``, or TM2 DocTypes.
- Production :mod:`tm2_std_adapter` continues to resolve from the database; this file
  supplies **reference shapes and business codes** only.
- ``output_refs_v83.snapshot_hash`` follows the doc 9 §8.3 illustrative ``HASH-PUBSNAP-…``
  string; live adapter hashing remains SHA-256 hex (see P3-05 / P3-07).

Tests: ``tender_management.tests.test_p3_08_stub_mode_pack``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# doc 9 §20.2 — minimum codes that must appear in the stub JSON (subset enforced in tests).
TM2_STUB_SEED_REQUIRED_CODES: frozenset[str] = frozenset(
	{
		"TND-MOH-2026-001",
		"PKG-MOH-2026-001",
		"STDTV-WORKS-BUILDING-CIVIL-APR2022",
		"WORKS-PROFILE-BUILDING-CIVIL",
		"STDINST-TND-MOH-2026-001",
		"GB-TND-MOH-2026-001-V2",
		"DSM-TND-MOH-2026-001-V2",
		"DOM-TND-MOH-2026-001-V2",
		"DEM-TND-MOH-2026-001-V2",
		"DCM-TND-MOH-2026-001-V2",
		"PUBSNAP-TND-MOH-2026-001-V2",
		"ADD-TND-MOH-2026-001-01",
		"SUP-ALPHA",
		"SUP-BETA",
		"SUP-GAMMA",
		"SUP-DELTA",
	}
)

_FIXTURE_REL = Path("fixtures") / "tm2_seed_works_open_tender.json"


def tm2_stub_fixture_path() -> Path:
	"""Absolute path to :file:`tm2_seed_works_open_tender.json` under ``tender_management``."""
	return Path(__file__).resolve().parent.parent / _FIXTURE_REL


@lru_cache(maxsize=1)
def load_tm2_works_open_tender_fixture() -> dict[str, Any]:
	"""Load and parse the stub JSON (cached process-local)."""
	path = tm2_stub_fixture_path()
	if not path.is_file():
		raise FileNotFoundError(f"TM2 stub fixture missing: {path}")
	with path.open(encoding="utf-8") as fh:
		return json.load(fh)


def get_stub_output_refs_v83() -> dict[str, str]:
	"""Return doc 9 §8.3 eight-key slice from the stub fixture (string values)."""
	data = load_tm2_works_open_tender_fixture()
	inner = data.get("output_refs_v83")
	if not isinstance(inner, dict):
		raise ValueError("stub fixture: missing or invalid output_refs_v83 object")
	out: dict[str, str] = {}
	for k, v in inner.items():
		out[str(k)] = str(v) if v is not None else ""
	return out


def assert_stub_fixture_contains_required_codes() -> None:
	"""Fail loudly if any §20.2 code is missing from the serialized fixture."""
	blob = json.dumps(load_tm2_works_open_tender_fixture(), sort_keys=True)
	missing = sorted(c for c in TM2_STUB_SEED_REQUIRED_CODES if c not in blob)
	if missing:
		raise ValueError(f"TM2 stub fixture missing required codes: {missing}")
