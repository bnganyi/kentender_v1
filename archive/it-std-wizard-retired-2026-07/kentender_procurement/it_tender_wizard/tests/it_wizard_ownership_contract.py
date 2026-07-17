# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Screen Ownership Matrix contract helpers for IT Wizard UI/layout gates."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Field source types from Matrix 99 / Correction Plan 98.
FIELD_SOURCE_TYPES = (
	"USER_ENTERED",
	"TEMPLATE_PREFILLED",
	"DERIVED",
	"OWNED_ELSEWHERE",
	"STD_LOCKED",
	"NOT_CONFIGURED",
)

# Magical / fixture patterns that must not appear as live configuration values
# in design or deployed inventory summary hosts (Matrix Immediate — System Inventory).
INVENTORY_FORBIDDEN_MAGICAL_PATTERNS = (
	"2,500 Concurrent Users",
	"42 Locations (East/West)",
	"180 VPN Managed Devices",
	"Access via Portal only",
	"RBAC / MFA",
	"On-Premise",
	"Access Logic",
	"Data Residency",
	"REVIEW DISCLOSURE GUIDANCE",
	"Primary HQ",
	"7/10 Items",
	"2 Pending",
	"1 Identified",
	"2 Required",
	"1 Warning",
)

# Cross-screen fixture residue that must not ship in static hosts.
CROSS_SCREEN_FORBIDDEN_MAGICAL_PATTERNS = (
	"TNT/024/2024",
	"Data Center Hardware Refresh",
	"National Treasury",
	"Ministry of Finance, P.O. Box",
	"procurement@finance.go.ke",
	"Sarah M.",
	"John K.",
	"John Doe",
	"85/100",
	"20 marks",
	"15 marks",
	"14/18",
	"Technical score total is 85/100",
	"Scored (15%)",
	"Evidence Set",
	"Acceptance Set",
	"REQ-042: Auto-scaling Efficiency",
	"Last Run: 2024-10-12 14:22",
)

# Requirements composer must never reintroduce evaluation-score presentation.
REQUIREMENTS_FORBIDDEN_LABELS = (
	"Scored (15%)",
	"Evidence Set",
	"Acceptance Set",
)

# Commercial pricing fields must not appear on System Inventory.
INVENTORY_FORBIDDEN_PRICING_LABELS = (
	"Quantity",
	"Unit of Measure",
	"Pricing Class",
	"Unit Price",
	"Total Price",
)

# Stable ownership hooks expected on System Inventory after OWN-007.
INVENTORY_OWNERSHIP_HOOKS = (
	"data-itw-inv-summary-host",
	"data-itw-inv-security-host",
	"data-itw-inv-source",
	"data-itw-inv-edit-source",
	"data-itw-inv-security-value=\"title\"",
	"data-itw-inv-security-value=\"classification\"",
	"data-itw-inv-security-value=\"required_action\"",
	"data-itw-inv-security-value=\"bidder_consideration\"",
	"Not configured",
)

SCREEN_ASSET_PAIRS = (
	("01 dashboard", "it_wizard_dashboard.html"),
	("02 std-config-overview", "it_wizard_std_config_overview.html"),
	("03 tender-profile", "it_wizard_tender_profile.html"),
	("04 tds", "it_wizard_tds.html"),
	("05 it-requirements", "it_wizard_it_requirements.html"),
	("06 implementation-schedule", "it_wizard_implementation_schedule.html"),
	("07 system-inventory", "it_wizard_system_inventory.html"),
	("08 price-schedule", "it_wizard_price_schedule.html"),
	("09 evaluation-setup", "it_wizard_evaluation_setup.html"),
	("10 forms-and-evidence", "it_wizard_forms_and_evidence.html"),
	("11 scc", "it_wizard_scc.html"),
	("12 validation-report", "it_wizard_validation_report.html"),
	("13 review-and-approval", "it_wizard_review_and_approval.html"),
	("14 render-preview", "it_wizard_render_preview.html"),
	("15 publication-readiness", "it_wizard_publication_readiness.html"),
)


def assert_none_present(html: str, patterns: Iterable[str], *, context: str) -> None:
	for pattern in patterns:
		assert pattern not in html, f"{context}: forbidden ownership pattern present: {pattern!r}"


def assert_all_present(html: str, patterns: Iterable[str], *, context: str) -> None:
	for pattern in patterns:
		assert pattern in html, f"{context}: required ownership marker missing: {pattern!r}"


def assert_inventory_ownership_html(html: str, *, context: str = "system inventory") -> None:
	assert_none_present(html, INVENTORY_FORBIDDEN_MAGICAL_PATTERNS, context=context)
	assert_none_present(html, INVENTORY_FORBIDDEN_PRICING_LABELS, context=context)
	assert_all_present(html, INVENTORY_OWNERSHIP_HOOKS, context=context)


def assert_requirements_ownership_html(html: str, *, context: str = "it requirements") -> None:
	assert_none_present(html, REQUIREMENTS_FORBIDDEN_LABELS, context=context)


def assert_price_schedule_ownership_html(html: str, *, context: str = "price schedule") -> None:
	"""Owned price fields must not carry Not configured source chrome (Matrix 99)."""
	assert "Source: Not configured" not in html, (
		f"{context}: owned Price Schedule fields must not use Source: Not configured"
	)
	assert 'data-itw-price-drawer="1"' in html, f"{context}: missing price drawer hook"
	assert 'data-itw-price-owned="1"' in html, f"{context}: missing owned-field markers"
	assert "Reference: System Inventory" in html, f"{context}: missing inventory reference chrome"
	assert "Source: Tender Profile" in html, f"{context}: currency must cite Tender Profile"
	assert "translate-x-full" in html, f"{context}: drawer must start closed"


def assert_cross_screen_ownership_html(html: str, *, context: str) -> None:
	assert_none_present(html, CROSS_SCREEN_FORBIDDEN_MAGICAL_PATTERNS, context=context)
	assert_none_present(html, REQUIREMENTS_FORBIDDEN_LABELS, context=context)
	if "itw-price-drawer" in html or "Price Item Detail" in html:
		assert_price_schedule_ownership_html(html, context=context)


def iter_screen_html_paths(kentender_v1_root: Path) -> list[tuple[str, Path, Path]]:
	design_root = kentender_v1_root / "docs" / "std-prod-impl" / "IT-STD-Wizard" / "ui-designs"
	v2_dashboard = (
		kentender_v1_root / "docs" / "std-prod-impl" / "IT-STD-Wizard-v2" / "screen-01" / "code.html"
	)
	deploy_root = (
		kentender_v1_root
		/ "kentender_procurement"
		/ "kentender_procurement"
		/ "public"
		/ "it_tender_wizard_impl"
	)
	rows: list[tuple[str, Path, Path]] = []
	for design_dir, deploy_name in SCREEN_ASSET_PAIRS:
		design_path = (
			v2_dashboard
			if design_dir == "01 dashboard"
			else design_root / design_dir / "code.html"
		)
		rows.append(
			(
				design_dir,
				design_path,
				deploy_root / deploy_name,
			)
		)
	return rows
