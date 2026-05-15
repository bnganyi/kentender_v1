# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Admin Console — STD Template facade (TM2-only; no legacy Procurement Tender)."""

from __future__ import annotations

from typing import Any

from kentender_procurement.kentender_procurement.doctype.std_template import (
	std_template as _std_template,
)

__all__ = (
	"get_template_package_summary",
	"get_template_package_component",
	"reimport_std_template_package",
	"validate_std_package",
	"trace_std_rules_for_sample",
	"trace_std_rules_for_tender",
	"create_or_open_std_demo_tender",
)


def get_template_package_summary(template_name: str) -> dict:
	return _std_template.get_template_package_summary(template_name)


def get_template_package_component(template_name: str, component_name: str) -> dict:
	return _std_template.get_template_package_component(template_name, component_name)


def reimport_std_template_package(template_name: str | None = None) -> dict:
	return _std_template.reimport_std_template_package(template_name)


def validate_std_package(template_name: str) -> dict[str, Any]:
	return _std_template.validate_std_package(template_name)


def trace_std_rules_for_sample(template_name: str, variant_code: str | None = None) -> dict[str, Any]:
	return _std_template.trace_std_rules_for_sample(template_name, variant_code)


def trace_std_rules_for_tender(tender_name: str) -> dict[str, Any]:
	return _std_template.trace_std_rules_for_tender(tender_name)


def create_or_open_std_demo_tender(
	template_name: str,
	variant_code: str | None = None,
) -> dict[str, Any]:
	return _std_template.create_or_open_std_demo_tender(template_name, variant_code)
