# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Test Scanner (BDS-CHG-001 v0.8 owner decision OD-C; plan D16), on the
`kt_file_scanners` hook of kentender_core file_integrity.

On a test environment it answers every file: the EICAR test signature is
Infected, anything else Clean, and both verdicts name the simulation. On any
other site it returns nothing, so a file stays "Not scanned — no scanner
configured" there. It is not malware protection; the production scanner is an
owner decision (FU-V08-16, FU-V08-30)."""

from __future__ import annotations

from kentender_procurement.bid_submission.services import simulation

EICAR_MARKER = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"
CLEAN = "Clean — test scanner (simulation)"
INFECTED = "Infected — test scanner (simulation): EICAR test signature"


def scan(*, content: bytes, filename: str) -> str | None:
	if not simulation.enabled():
		return None
	return INFECTED if EICAR_MARKER in (content or b"") else CLEAN
