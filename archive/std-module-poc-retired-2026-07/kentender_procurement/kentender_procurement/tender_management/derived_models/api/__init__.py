# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted derived-model API handlers (DERIVED-1000)."""

from __future__ import annotations

from kentender_procurement.tender_management.derived_models.api.handlers import (
	std_engine_generate_all_outputs,
	std_engine_generate_output,
	std_engine_get_current_output,
	std_engine_get_output,
	std_engine_record_output_consumption,
	std_engine_validate_output_consumption,
)

__all__ = (
	"std_engine_generate_all_outputs",
	"std_engine_generate_output",
	"std_engine_get_current_output",
	"std_engine_get_output",
	"std_engine_validate_output_consumption",
	"std_engine_record_output_consumption",
)
