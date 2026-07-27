# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Explicit compatibility boundary for legacy pack-10 bidder submission schema.

Until Phase 3 (manifest compiler) and Phase 6 (checklist projection cutover),
``schema_compiler.SECTION_KEYS`` and Website A2/A4 may continue to consume the
E1 pack-10 schema. That path is **not** the canonical Bidder Workspace Manifest
contract.

New G1 code must import schemas and NSSF fixture errata from this package.
Do not treat pack-10 as the runtime contract for new features.
"""

from __future__ import annotations

# Named boundary constant — import this when documenting or gating legacy use.
LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY = (
	"LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY"
)

LEGACY_PACK10_SCHEMA_RELATIVE_PATH = (
	"docs/std-prod-impl/IT-STD-Wizard-v3/E1-NSSF_Tender_PoC_Mapping_Pack/"
	"10_NSSF_Electronic_Bidder_Submission_Schema.json"
)

# Negative-fixture digest only (Phase 0 §7.1). Not a canonical manifest digest.
LEGACY_PACK10_SCHEMA_DIGEST = (
	"sha256:4d461f4901ef159578b441afd468125ce60b310d67575a81dc23d88ff4a6fa72"
)

LEGACY_PACK10_IS_CANONICAL_RUNTIME_CONTRACT = False
