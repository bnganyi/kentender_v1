# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared validation context for STD validators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kentender_procurement.std_engine.package_import.package_reader import PackageInspectionResult


@dataclass
class ValidationContext:
	package_id: str
	dry_report: dict[str, Any] | None = None
	inspection: PackageInspectionResult | None = None
	db_checks_enabled: bool = True
	extra: dict[str, Any] = field(default_factory=dict)
