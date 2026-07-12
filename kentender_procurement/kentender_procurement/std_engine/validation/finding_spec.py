# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validation finding proposal contract."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

FINDING_KEY_MAX_LEN = 140


@dataclass(frozen=True)
class ValidationFindingSpec:
	finding_code: str
	severity: str
	object_type: str
	object_id: str
	description: str
	lifecycle_gate: str
	suggested_fix: str | None = None

	def finding_key(self, package_id: str) -> str:
		raw = f"{package_id}.{self.finding_code}.{self.object_id}"
		if len(raw) <= FINDING_KEY_MAX_LEN:
			return raw
		digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
		return f"{package_id}.{self.finding_code}.{digest}"
