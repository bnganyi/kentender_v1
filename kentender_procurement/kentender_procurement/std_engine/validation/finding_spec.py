# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validation finding proposal contract."""

from __future__ import annotations

from dataclasses import dataclass


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
		return f"{package_id}.{self.finding_code}.{self.object_id}"
