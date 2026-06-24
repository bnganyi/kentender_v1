# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-009 — Golden-path ordinary flow hides PLANINCL / source-target technical labels."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.api.approved_demands import (
	include_pp_demand_in_procurement_plan,
)
from kentender_procurement.procurement_planning.api.planning_inclusion import (
	get_pp_create_package_modal_drawer,
)
from kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path import (
	ensure_pp5_needs_planning_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.services.approved_demand_drawer import (
	get_approved_demand_planning_drawer,
)
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	get_workbench_item_view_model,
)

_FORBIDDEN_ORDINARY_COPY = (
	"PLANINCL-",
	"source_object_code",
	"target_object_code",
	"source object",
	"target object",
	"technical_refs_json",
	"locked_summary_json",
	"passed_forward_summary_json",
	"audit_event_ref",
)

_USER_FACING_KEY_RE = re.compile(
	r"(title|subtitle|message|label|name|facts|help|copy|description|blocker_message|"
	r"demand_name|active_plan_name|category_label|method_label|value_label|funding_label|"
	r"package_title_default|existing_package_name|state_label|next_action_label|plan_title|"
	r"procuring_entity|status_label|plan_name|next_action|includeSuccessMessage|"
	r"createPackageSuccessMessage)$",
	re.IGNORECASE,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


def _assert_no_forbidden_in_user_facing(value: Any, *, path: str = "") -> None:
	if isinstance(value, dict):
		for key, nested in value.items():
			key_text = str(key)
			nested_path = f"{path}.{key_text}" if path else key_text
			if _USER_FACING_KEY_RE.search(key_text):
				if isinstance(nested, str):
					for token in _FORBIDDEN_ORDINARY_COPY:
						self_msg = f"{nested_path}={nested!r}"
						assert token.lower() not in nested.lower(), (
							f"P5-009 user-facing copy must not contain {token!r} ({self_msg})"
						)
				elif isinstance(nested, list):
					for idx, item in enumerate(nested):
						_assert_no_forbidden_in_user_facing(item, path=f"{nested_path}[{idx}]")
				else:
					_assert_no_forbidden_in_user_facing(nested, path=nested_path)
			elif key_text in ("blockers", "facts", "items", "checks", "secondary_actions"):
				_assert_no_forbidden_in_user_facing(nested, path=nested_path)
	elif isinstance(value, list):
		for idx, item in enumerate(value):
			_assert_no_forbidden_in_user_facing(item, path=f"{path}[{idx}]")


class TestPP5NoTechnicalLeakageP5009Contract(UnitTestCase):
	def _read_js(self, *parts: str) -> str:
		path = _pkg_public(*parts)
		self.assertTrue(path.exists(), msg=f"missing {path}")
		return path.read_text(encoding="utf-8", errors="replace")

	def _block(self, source: str, start: str, end: str) -> str:
		return source.split(start, 1)[1].split(end, 1)[0]

	def test_include_plan_modal_ordinary_html_has_no_forbidden_tokens(self) -> None:
		source = self._read_js("js", "pp2_planning_include_plan_modal.js")
		context_block = self._block(source, "function businessContextHtml", "function buildIncludePlanDialogFields")
		for token in _FORBIDDEN_ORDINARY_COPY:
			self.assertNotIn(token, context_block, msg=f"include modal context leaks {token!r}")
		self.assertIn("hasTechnicalLeakage", source, msg="include modal must sanitize technical API errors")

	def test_create_package_modal_ordinary_html_has_no_forbidden_tokens(self) -> None:
		source = self._read_js("js", "pp2_planning_create_package_modal.js")
		context_block = self._block(source, "function businessContextHtml", "function showDuplicatePackageDialog")
		duplicate_block = self._block(source, "function showDuplicatePackageDialog", "function showCreatePackageBlocker")
		blocker_block = self._block(source, "function showCreatePackageBlocker", "function open")
		for token in _FORBIDDEN_ORDINARY_COPY:
			self.assertNotIn(token, context_block, msg=f"create modal context leaks {token!r}")
			self.assertNotIn(token, duplicate_block, msg=f"duplicate dialog leaks {token!r}")
			self.assertNotIn(token, blocker_block, msg=f"create blocker leaks {token!r}")

	def test_workbench_selected_summary_ordinary_html_has_no_forbidden_tokens(self) -> None:
		source = self._read_js("js", "pp3_planning_selected_work_summary.js")
		include_block = self._block(source, "function includeSuccessHtml", "function secondaryActionsHtml")
		create_block = self._block(source, "function createPackageSuccessHtml", "function includeSuccessHtml")
		summary_block = self._block(source, "function html(opts)", "function bindActions")
		for token in _FORBIDDEN_ORDINARY_COPY:
			self.assertNotIn(token, include_block, msg=f"include success summary leaks {token!r}")
			self.assertNotIn(token, create_block, msg=f"create success summary leaks {token!r}")
			self.assertNotIn(token, summary_block, msg=f"selected summary leaks {token!r}")

	def test_work_list_row_html_has_no_forbidden_tokens(self) -> None:
		source = self._read_js("js", "pp3_planning_work_list.js")
		if "function rowHtml" in source:
			row_block = self._block(source, "function rowHtml", "function ")
		else:
			row_block = source
		for token in _FORBIDDEN_ORDINARY_COPY:
			self.assertNotIn(token, row_block, msg=f"work list row leaks {token!r}")


class TestPP5NoTechnicalLeakageP5009GoldenPath(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		out = ensure_pp5_needs_planning_ready(force_reset=True)
		self.assertTrue(out.get("ok"), out)

	def test_golden_path_view_models_have_no_ordinary_leakage(self) -> None:
		"""PP5-009-BE-001: Needs Planning → Include → Create Package payloads stay business-safe."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		needs_planning = get_workbench_item_view_model(
			queue="needs_planning",
			actor="planner@moh.test",
			limit=200,
			start=0,
		)
		self.assertTrue(needs_planning.get("ok"), needs_planning)
		_assert_no_forbidden_in_user_facing(needs_planning)

		drawer = get_approved_demand_planning_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
			actor="planner@moh.test",
		)
		self.assertTrue(drawer.get("ok"), drawer)
		_assert_no_forbidden_in_user_facing(drawer)

		include_out = include_pp_demand_in_procurement_plan(
			demand_code=DEMAND_CODE,
			procurement_plan_code=PLAN_CODE,
			demand_item_codes=f'["{DEMAND_ITEM_CODE}"]',
		)
		self.assertTrue(include_out.get("ok"), include_out)
		_assert_no_forbidden_in_user_facing(
			{key: include_out.get(key) for key in ("message", "title", "next_action", "demand_code")}
		)

		modal = get_pp_create_package_modal_drawer(
			demand_code=DEMAND_CODE,
			plan_code=PLAN_CODE,
			inclusion_code=str(include_out.get("inclusion_code") or "").strip(),
		)
		self.assertTrue(modal.get("ok"), modal)
		_assert_no_forbidden_in_user_facing(
			{
				key: modal.get(key)
				for key in (
					"demand_name",
					"active_plan_name",
					"category_label",
					"method_label",
					"value_label",
					"funding_label",
					"package_title_default",
					"blocker_message",
					"existing_package_name",
				)
			}
		)

		draft_packages = get_workbench_item_view_model(
			queue="draft_packages",
			actor="planner@moh.test",
			limit=200,
			start=0,
		)
		self.assertTrue(draft_packages.get("ok"), draft_packages)
		_assert_no_forbidden_in_user_facing(draft_packages)

	def test_golden_path_json_serialization_has_no_forbidden_substrings_in_labels(self) -> None:
		"""PP5-009-BE-002: serialized user-facing labels remain free of technical handoff tokens."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_workbench_item_view_model(
			queue="needs_planning",
			actor="planner@moh.test",
			limit=50,
			start=0,
		)
		label_blob = json.dumps(
			[
				{
					"title": item.get("title"),
					"subtitle": item.get("subtitle"),
					"state_label": item.get("state_label"),
					"next_action_label": item.get("next_action_label"),
				}
				for item in out.get("items") or []
			]
		)
		for token in _FORBIDDEN_ORDINARY_COPY:
			self.assertNotIn(token.lower(), label_blob.lower(), msg=f"workbench labels leak {token!r}")
