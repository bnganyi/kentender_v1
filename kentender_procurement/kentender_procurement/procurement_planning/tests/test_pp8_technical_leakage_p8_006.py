# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-006 — Technical leakage scan (PP3 §18.3 prohibited ordinary UI strings)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.evidence_view_model import (
	get_evidence_view_model,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)
from kentender_procurement.procurement_planning.services.released_to_tender_summary_view_model import (
	get_released_package_summary,
)
from kentender_procurement.procurement_planning.tests.pp8_gate_constants import (
	P8_PROHIBITED_ORDINARY_UI,
)

_PP3_PUBLIC_JS = (
	"pp3_planning_work_list.js",
	"pp3_planning_selected_work_summary.js",
	"pp3_planning_released_list.js",
	"pp3_planning_release_summary.js",
	"pp3_planning_package_detail.js",
	"pp2_planning_include_plan_modal.js",
	"pp2_planning_create_package_modal.js",
)

_USER_FACING_KEY_RE = re.compile(
	r"(title|subtitle|message|label|name|facts|help|copy|description|blocker|headline|"
	r"status_label|next_action|state_label|primary_action|secondary_action|"
	r"demand_name|active_plan_name|category_label|method_label|value_label|funding_label|"
	r"package_title_default|existing_package_name|plan_title|procuring_entity|plan_name)$",
	re.IGNORECASE,
)


def _pkg_public(*parts: str) -> Path:
	return Path(frappe.get_app_path("kentender_procurement")).joinpath("public", *parts)


def _assert_no_prohibited_in_text(text: str, *, context: str = "") -> None:
	lower = (text or "").lower()
	for token in P8_PROHIBITED_ORDINARY_UI:
		if token.lower() in lower:
			raise AssertionError(f"P8-006 prohibited token {token!r} in {context or 'text'}")


def _walk_user_facing(value, *, path: str = "") -> None:
	if isinstance(value, dict):
		for key, nested in value.items():
			key_text = str(key)
			nested_path = f"{path}.{key_text}" if path else key_text
			if _USER_FACING_KEY_RE.search(key_text) or key_text in (
				"blockers",
				"facts",
				"items",
				"checks",
				"secondary_actions",
				"timeline",
				"records",
			):
				if isinstance(nested, str):
					_assert_no_prohibited_in_text(nested, context=nested_path)
				else:
					_walk_user_facing(nested, path=nested_path)
	elif isinstance(value, list):
		for idx, item in enumerate(value):
			_walk_user_facing(item, path=f"{path}[{idx}]")


_JS_SOURCE_FORBIDDEN = tuple(
	token
	for token in P8_PROHIBITED_ORDINARY_UI
	if token not in ("package_release", "handed_off", "P5", "stub")
)


class TestPP8TechnicalLeakageP8006Source(UnitTestCase):
	def test_pp8_006_pp3_public_js_has_no_prohibited_ordinary_tokens(self) -> None:
		for filename in _PP3_PUBLIC_JS:
			path = _pkg_public("js", filename)
			self.assertTrue(path.exists(), msg=f"missing {path}")
			source = path.read_text(encoding="utf-8", errors="replace")
			for token in _JS_SOURCE_FORBIDDEN:
				haystack = source
				if token == "package_release":
					haystack = source.replace("api.package_release", "")
				self.assertNotIn(token, haystack, msg=f"{filename} leaks {token!r}")


class TestPP8TechnicalLeakageP8006ViewModels(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		if not out.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {out}")

	def test_pp8_006_package_detail_and_release_summary_are_business_safe(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		detail = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(detail.get("ok"), detail)
		_walk_user_facing(detail)
		summary = get_released_package_summary(PKG_CODE, "Administrator")
		self.assertTrue(summary.get("ok"), summary)
		_walk_user_facing(summary)

	def test_pp8_006_evidence_ordinary_payload_hides_technical_refs(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), out)
		ordinary = {
			"title": out.get("title"),
			"timeline": out.get("timeline"),
			"records": out.get("records"),
		}
		_walk_user_facing(ordinary)
		serialized = json.dumps(ordinary).lower()
		for token in ("planincl-", "pkgrel-", "source_object_code", "technical_refs_json"):
			self.assertNotIn(token, serialized, msg=f"evidence ordinary payload leaks {token!r}")
