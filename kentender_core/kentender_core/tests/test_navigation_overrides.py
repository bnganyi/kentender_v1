"""The shared-rail seam (FU-CM-58): an installed app takes over a Planned placeholder in a shared rail through the `kt_navigation_overrides` hook, without
editing the rail's owner's file. The rail's owner reads it at boot; core owns only the contract."""

from contextlib import contextmanager
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import navigation_overrides as nav

PLACEHOLDER = {"label": "Contract Management", "link_to": "coming-soon", "link_type": "Page", "route_options": '{"feature": "Contract Management"}', "suffix": "Planned", "icon": "file"}
TENDERS = {"label": "Tenders", "link_to": "tenders", "link_type": "Page"}


def contributes_the_live_page():
	return {"Procurement": {"items": {"Contract Management": {"link_to": "contracts", "link_type": "Page", "route_options": None}}, "routes": ["contracts"]}}


def contributes_more_routes():
	return {"Procurement": {"routes": ["contracts", "other"]}}


def contributes_forbidden_fields():
	return {"Procurement": {"items": {"Contract Management": {"link_to": "contracts", "label": "Hijacked", "type": "Section Break", "suffix": "x"}}}}


def fails():
	raise RuntimeError("down")


@contextmanager
def contributors(*functions):
	paths = [f"{__name__}.{fn.__name__}" for fn in functions]
	real = frappe.get_hooks
	with mock.patch.object(frappe, "get_hooks", side_effect=lambda hook=None, *a, **k: paths if hook == nav.HOOK else real(hook, *a, **k)):
		yield


class TestNavigationOverrides(IntegrationTestCase):
	def test_with_no_app_contributing_a_placeholder_is_untouched(self):
		with contributors():
			self.assertEqual(nav.apply_to_items("Procurement", [dict(PLACEHOLDER)]), [PLACEHOLDER])
			self.assertEqual(nav.for_sidebar("Procurement"), {"items": {}, "routes": []})

	def test_an_installed_app_replaces_the_placeholder_with_its_live_page_and_the_planned_badge_goes(self):
		with contributors(contributes_the_live_page):
			replaced, other = nav.apply_to_items("Procurement", [dict(PLACEHOLDER), dict(TENDERS)])
		self.assertEqual((replaced["link_to"], replaced["link_type"], replaced["route_options"], "suffix" in replaced, replaced["label"], replaced["icon"]), ("contracts", "Page", None, False, "Contract Management", "file"))
		self.assertEqual(other, TENDERS)

	def test_only_the_named_label_in_the_named_rail_is_replaced(self):
		with contributors(contributes_the_live_page):
			self.assertEqual(nav.apply_to_items("Planning module navigation", [dict(PLACEHOLDER)]), [PLACEHOLDER])

	def test_the_routes_an_app_contributes_are_collected_per_rail_without_duplicates(self):
		with contributors(contributes_the_live_page, contributes_more_routes):
			self.assertEqual(nav.for_sidebar("Procurement")["routes"], ["contracts", "other"])

	def test_only_link_fields_may_be_overridden_never_the_label_or_the_type(self):
		with contributors(contributes_forbidden_fields):
			out = nav.apply_to_items("Procurement", [dict(PLACEHOLDER)])[0]
		self.assertEqual((out["label"], out["link_to"], "suffix" in out), ("Contract Management", "contracts", False))
		self.assertNotIn("type", out)

	def test_a_contributor_that_fails_never_breaks_the_rail(self):
		with contributors(fails, contributes_the_live_page), mock.patch.object(frappe, "log_error") as logged:
			self.assertEqual(nav.for_sidebar("Procurement")["routes"], ["contracts"])
		logged.assert_called_once()
