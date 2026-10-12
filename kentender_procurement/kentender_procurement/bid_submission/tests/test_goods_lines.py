# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.12 §4.4.9 and §10.10A: a Tender with several goods lines answers every line.
The Requirements task draws one Offered goods form per line, names each line's rows by its description,
and the Review preview and blockers say which line they mean. Pure logic: no database."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase

from kentender_procurement.bid_submission.services import projection, requirements_view, review_view


def goods_row(key, description, status="Complete"):
	facts = [{"label": "Description", "value": description}, {"label": "Quantity", "value": "20"}, {"label": "Unit", "value": "Each"},
		{"label": "Delivery location", "value": "Afya House, Nairobi"}, {"label": "Latest delivery", "value": "6 Nov 2026"}]
	return {"key": key, "label": "Offered goods", "status": status, "facts": facts, "fields": [{"handle": f"{key}-model", "kind": "short_text"}], "evidence": ""}


class TestGoodsLines(TestCase):
	def test_every_line_becomes_a_form_with_its_description_and_published_facts(self):
		lines = requirements_view.goods_lines([goods_row("g1", "Office laptops"), goods_row("g2", "Monitors for office laptops")])
		self.assertEqual([l["heading"] for l in lines], ["Office laptops", "Monitors for office laptops"])
		self.assertEqual([f["handle"] for f in lines[1]["fields"]], ["g2-model"])
		self.assertEqual([p["label"] for p in lines[0]["published"]], ["Quantity · published", "Delivery location · published", "Latest delivery · published"])

	def test_no_goods_line_means_no_form(self):
		self.assertEqual(requirements_view.goods_lines([]), [])

	def test_with_several_lines_each_row_is_named_by_its_line_so_a_fault_says_which(self):
		rows = [goods_row("g1", "Office laptops"), goods_row("g2", "Monitors for office laptops", "Not started")]
		requirements_view.name_goods_rows(rows)
		self.assertEqual([r["label"] for r in rows], ["Office laptops", "Monitors for office laptops"])

	def test_with_one_line_the_row_keeps_its_published_name(self):
		rows = [goods_row("g1", "Office laptops")]
		requirements_view.name_goods_rows(rows)
		self.assertEqual(rows[0]["label"], "Offered goods")

	def test_a_requirement_row_says_which_lines_it_applies_to(self):
		facts = [{"label": "Applies to", "value": "Monitors for office laptops"}]
		self.assertEqual(requirements_view.applies_to(facts), "Monitors for office laptops")
		self.assertEqual(requirements_view.applies_to([]), "")


def field(key, label, group):
	return SimpleNamespace(field_key=key, label=label, label_parameters=[], control_id="CTL-SHORT-TEXT", group=group, handle=key)


def group(composition, facts, fields=()):
	g = SimpleNamespace(composition_id=composition, published_facts=facts, fields=[])
	g.fields = [field(k, l, g) for k, l in fields]
	return g


class FakeCtx:
	def __init__(self, groups, values=None):
		self.model = SimpleNamespace(groups_of=lambda task: groups)
		self._values = values or {}

	def value(self, f):
		return self._values.get(f.field_key)


class TestReviewNamesTheLine(TestCase):
	def two_lines(self):
		fields = (("offered_make_model", "Offered make and model"), ("offered_delivery_date", "Offered delivery date"))
		return [group("COMP-GOODS-OFFER", {"description": "Office laptops", "quantity": "20", "unit": "Each"}, fields),
			group("COMP-GOODS-OFFER", {"description": "Monitors for office laptops", "quantity": "20", "unit": "Each"}, fields)]

	def test_a_blocker_on_a_goods_field_names_the_line_when_there_are_several(self):
		groups = self.two_lines()
		ctx = FakeCtx(groups)
		self.assertEqual(projection.blocker_label(ctx, groups[1].fields[0]), "Monitors for office laptops: Offered make and model")

	def test_a_blocker_on_a_one_line_tender_keeps_the_field_label(self):
		groups = self.two_lines()[:1]
		ctx = FakeCtx(groups)
		self.assertEqual(projection.blocker_label(ctx, groups[0].fields[0]), "Offered make and model")

	def test_the_preview_groups_what_is_offered_by_line_and_keeps_one_line_flat(self):
		groups = self.two_lines()
		values = {}
		ctx = FakeCtx(groups, values)
		rows = review_view.offering(ctx)
		self.assertEqual([(r.get("line"), r["label"]) for r in rows], [
			("Office laptops", "Offered model"), ("Office laptops", "Quantity"), ("Office laptops", "Delivery"),
			("Monitors for office laptops", "Offered model"), ("Monitors for office laptops", "Quantity"), ("Monitors for office laptops", "Delivery")])
		single = review_view.offering(FakeCtx(groups[:1], values))
		self.assertTrue(all("line" not in r for r in single))
