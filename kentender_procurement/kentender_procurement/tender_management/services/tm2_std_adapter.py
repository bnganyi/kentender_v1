# Copyright (c) 2026, KenTender and contributors
"""IT STD Wizard retired stub — TM2 STD adapter unavailable until replacement module."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

RETIRED_MESSAGE = _(
	"The IT Tender Configuration Wizard has been retired. Tender-specific document setup is unavailable until a replacement module ships."
)
RETIRED_CODE = "IT_STD_WIZARD_RETIRED"

STD_ADAPTER_OUTPUT_REFS_V83_KEYS: tuple[str, ...] = (
	"bundle_output_code",
	"dsm_output_code",
	"dom_output_code",
	"dem_output_code",
	"dcm_output_code",
)


def _retired(**extra: Any) -> dict[str, Any]:
	out: dict[str, Any] = {
		"ok": False,
		"error_code": RETIRED_CODE,
		"denial_code": RETIRED_CODE,
		"message": RETIRED_MESSAGE,
		"retired": True,
	}
	out.update(extra)
	return out


def load_procurement_package_by_code(package_code: str) -> dict[str, Any] | None:
	if not package_code:
		return None
	if not frappe.db.exists("Procurement Package", package_code):
		name = frappe.db.get_value("Procurement Package", {"package_code": package_code}, "name")
		if not name or not frappe.db.exists("Procurement Package", name):
			return None
		package_code = name
	return frappe.db.get_value(
		"Procurement Package",
		package_code,
		["name", "package_code", "package_title", "status", "procurement_method"],
		as_dict=True,
	)


def get_eligible_std_templates(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
	return []


def getEligibleStdTemplates(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
	return get_eligible_std_templates(*args, **kwargs)


def assert_std_eligible_for_package(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def create_tender_std_instance(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def createTenderStdInstance(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return create_tender_std_instance(*args, **kwargs)


def validate_tender_std_readiness(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired(status="Blocked", blockers=[], warnings=[])


def validateTenderStdReadiness(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return validate_tender_std_readiness(*args, **kwargs)


def _retired_output(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def get_current_bundle(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired_output()


def get_current_dsm(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired_output()


def get_current_dom(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired_output()


def get_current_dem(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired_output()


def get_current_dcm(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired_output()


def getCurrentDem(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return get_current_dem(*args, **kwargs)


def create_or_get_publication_snapshot(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def create_or_get_publication_snapshot_for_tm2(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def createOrGetPublicationSnapshot(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return create_or_get_publication_snapshot(*args, **kwargs)


def analyze_addendum_impact(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def analyzeAddendumImpact(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return analyze_addendum_impact(*args, **kwargs)


def regenerate_outputs_for_addendum(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def regenerateOutputsForAddendum(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return regenerate_outputs_for_addendum(*args, **kwargs)


def get_tender_std_output_refs(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return _retired()


def getTenderStdOutputRefs(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return get_tender_std_output_refs(*args, **kwargs)


def extract_std_output_refs_contract_v83(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return {key: "" for key in STD_ADAPTER_OUTPUT_REFS_V83_KEYS}
