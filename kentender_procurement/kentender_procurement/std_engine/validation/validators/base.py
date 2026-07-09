# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validator protocol for STD Engine."""

from __future__ import annotations

from typing import Protocol

from kentender_procurement.std_engine.validation.finding_spec import ValidationFindingSpec
from kentender_procurement.std_engine.validation.validators.context import ValidationContext


class StdValidator(Protocol):
	validator_code: str

	def validate(self, context: ValidationContext) -> list[ValidationFindingSpec]:
		...
