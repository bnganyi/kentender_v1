# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Resolving, verifying and freezing the contract's source material (CM-CHG-001 v0.8 section 19.4; plan D20; CM-R-04, CM-R-18).

Award hands over **references**, not copies. At preparation every one of the twelve required sources (S1 to S12) is described and fetched through the core seam
(`kentender_core.services.contract_source_contract`); the bytes must hash to what the owner described **and** to what the Award package recorded, so a source that changed after the award fails
instead of being silently used. A source that cannot be resolved is reported by number with its owner, and nothing is generated from the rest. When the preparer sends the agreement for signature the
verified material is frozen as a **manifest**: each document's category, source number, version, digest and size, and the digest of the whole. The bytes stay with their owners and stay
retrievable by the reference; the manifest is what each signature is bound to."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from kentender_contracts.services import records
from kentender_contracts.services.errors import fail
from kentender_core.services import contract_source_contract as seam

REQUIRED = tuple(f"S{n}" for n in range(1, 13))
CATEGORIES = {
	"S1": "Issued tender and template release", "S2": "Accepted tender and clarifications", "S3": "Price schedule", "S4": "Schedule of requirements and technical specifications",
	"S5": "General and special conditions", "S6": "Inspection and acceptance criteria", "S7": "Form No. 4, Contract Agreement", "S8": "Award notification and signing window",
	"S9": "Funding lineage", "S10": "Procuring entity", "S11": "Supplier identity and signatories", "S12": "Restrictions and award event",
}
#: the incorporated documents of the agreement, in the order the artboard lists them (D02-S): label, source number, where it comes from
INCORPORATED = (
	("Form No. 4, Contract Agreement", "S7", "Issued terms"), ("Form of tender", "S2", "Award package"), ("Price schedule", "S3", "Award package"),
	("Schedule of requirements", "S4", "Issued terms"), ("Technical specifications", "S4", "Issued terms"), ("General Conditions of Contract", "S5", "Issued terms"),
	("Special Conditions of Contract", "S5", "Issued terms"), ("Notification of award", "S8", "Award package"),
)


def sha(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def gather(handoff: list[dict[str, Any]]) -> dict[str, Any]:
	"""Every required source, fetched and verified. Returns `{"sources": {S1: {...row, data}}, "failed": [{source, reason, owner}]}`; never raises for a bad source."""
	by_number = {row["source"]: row for row in handoff or []}
	sources, failed = {}, []
	for number in REQUIRED:
		row = by_number.get(number)
		if not row:
			failed.append({"source": number, "category": CATEGORIES[number], "reason": "The award did not supply this source.", "owner": ""})
			continue
		owner = row.get("owner", "")
		described, fetched = seam.describe(row["reference"]), seam.fetch(row["reference"])
		if not described or not fetched:
			failed.append({"source": number, "category": CATEGORIES[number], "reason": "Its owner cannot supply it now.", "owner": owner})
			continue
		content = fetched.get("content")
		actual = sha(bytes(content)) if isinstance(content, (bytes, bytearray)) else ""
		if not actual or actual != described.get("sha256") or actual != fetched.get("digest"):
			failed.append({"source": number, "category": CATEGORIES[number], "reason": "What its owner supplies does not match the digest it described.", "owner": owner})
			continue
		if row.get("sha256") and row["sha256"] != actual:
			failed.append({"source": number, "category": CATEGORIES[number], "reason": "It changed after the award was made.", "owner": owner})
			continue
		media = described.get("media_type") or row.get("media_type", "")
		data = json.loads(content) if media == "application/json" else bytes(content).decode("utf-8")
		sources[number] = {**row, "version": described.get("version", row.get("version")), "sha256": actual, "size": len(content), "media_type": media, "data": data}
	return {"sources": sources, "failed": failed}


def require(handoff: list[dict[str, Any]]) -> dict[str, Any]:
	"""The verified sources, or `CM_SOURCE` naming every one that is missing or does not verify."""
	found = gather(handoff)
	if found["failed"]:
		fail("CM_SOURCE", failed=found["failed"], reason="A required source cannot be verified, so no agreement is generated from the rest.")
	return found["sources"]


def manifest(sources: dict[str, Any]) -> dict[str, Any]:
	"""The frozen package: one entry per source and the digest of the whole."""
	entries = [{"source": n, "category": CATEGORIES[n], "reference": s["reference"], "version": s["version"], "sha256": s["sha256"], "size": s["size"], "owner": s.get("owner", ""),
		"provider": s.get("provider", "")} for n, s in sorted(sources.items(), key=lambda kv: int(kv[0][1:]))]
	documents = [{"label": label, "source": number, "from": origin} for label, number, origin in INCORPORATED]
	return {"entries": entries, "documents": documents, "package_digest": records.digest({"entries": entries, "documents": documents})}


_INSERTION = re.compile(r'<span data-insertion="([a-z_]+)">.*?</span>', re.S)


def render(form: str, values: dict[str, str]) -> tuple[str, list[str]]:
	"""Fill only the declared insertions of Form No. 4; its covenant and precedence text is untouched. Returns the text and the insertions still empty."""
	import html

	missing: list[str] = []

	def fill(match):
		key = match.group(1)
		value = values.get(key)
		if value in (None, ""):
			missing.append(key)
			return match.group(0)
		return f'<span data-insertion="{key}">{html.escape(str(value))}</span>'

	return _INSERTION.sub(fill, form), missing
