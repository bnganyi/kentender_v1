# Copyright (c) 2026, KenTender and contributors
"""Audit remediation for Strategy writes: AUD-XC-005 (command-only writes),
AUD-STR-001/002/003 (change-set confinement), AUD-STR-004 (open-ended
applicability), AUD-STR-008 (generated references), AUD-STR-011 (expired
applicability at approval)."""

from __future__ import annotations

import frappe

from kentender_core.services.command_write_guard import CommandWriteError, maintenance_write
from kentender_strategy.api import strategy_consumer_api as api
from kentender_strategy.services import strategy_consumer as consumer
from kentender_strategy.services.strategy_writes import (
	create_strategy_successor_version,
	save_strategy_plan_draft,
	save_strategy_structure_draft,
)
from kentender_strategy.tests.fixtures import ensure_fiscal_year
from kentender_strategy.tests.test_str_chg_001_phase4_contracts import Phase4TestBase

LIFECYCLE_DOCTYPES = (
	"Strategic Plan",
	"Strategic Plan Version",
	"Strategy Node",
	"Performance Indicator",
	"Performance Target",
)


class AudRemediationBase(Phase4TestBase):
	def _api_command(self, command, version):
		"""A Strategy command through its whitelisted endpoint, which requires the
		expected version and an idempotency key (STR §8, KT-STD-001 §11)."""
		key = f"aud-{command.__name__}-{version}-{self.suffix}"
		token = str(frappe.db.get_value("Strategic Plan Version", version, "modified"))
		try:
			return command(version, expected_version=token, idempotency_key=key)
		finally:
			name = frappe.db.get_value("Strategy Command Journal", {"idempotency_key": key}, "name")
			if name:
				self._cleanup.append(("Strategy Command Journal", name))

	def _api_submit(self, version):
		return self._api_command(api.submit_strategy_version, version)

	def _api_approve(self, version):
		return self._api_command(api.approve_strategy_version, version)

	def _author(self, label="author"):
		user = self._user(label)
		self._assign(user, "CAP-STRATEGY-AUTHOR")
		return user

	def _approver(self, label="approver"):
		user = self._user(label)
		self._assign(user, "CAP-STRATEGY-APPROVAL-AUTHORITY")
		return user

	def _active_with_successor_draft(self):
		"""Active V1 (full content) and an open Draft successor V2 made by the command."""
		author = self._author("succ")
		plan, v1 = self._plan_and_version()
		nodes = self._fill_hierarchy(v1)
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")
		frappe.set_user(author)
		v2 = create_strategy_successor_version(plan)["name"]
		frappe.set_user("Administrator")
		self._track_version_content(v2)
		return author, plan, v1, nodes, v2

	def _track_version_content(self, version):
		self._track(frappe.get_doc("Strategic Plan Version", version))
		for n in frappe.get_all("Strategy Node", filters={"plan_version_id": version}, pluck="name"):
			self._cleanup.append(("Strategy Node", n))
		for i in frappe.get_all("Performance Indicator", filters={"plan_version_id": version}, pluck="name"):
			self._cleanup.append(("Performance Indicator", i))
			for t in frappe.get_all("Performance Target", filters={"indicator_id": i}, pluck="name"):
				self._cleanup.append(("Performance Target", t))


class TestCommandOnlyWrites(AudRemediationBase):
	"""AUD-XC-005 — a lifecycle record changes only through the Strategy commands."""

	def test_user_save_of_any_lifecycle_doctype_is_refused_even_for_administrator(self):
		plan, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		names = {
			"Strategic Plan": plan,
			"Strategic Plan Version": version,
			"Strategy Node": nodes["pillar"],
			"Performance Indicator": nodes["indicator"],
			"Performance Target": nodes["target"],
		}
		for doctype, name in names.items():
			doc = frappe.get_doc(doctype, name)
			doc.flags.kt_str_command = True  # a spoofed flag must change nothing
			with self.assertRaises(CommandWriteError) as caught:
				doc.save()
			self.assertEqual(caught.exception.code, "COMMAND_ONLY_WRITE", doctype)
			with self.assertRaises(CommandWriteError) as caught:
				frappe.delete_doc(doctype, name)
			self.assertEqual(caught.exception.code, "COMMAND_ONLY_DELETE", doctype)

	def test_user_insert_is_refused(self):
		with self.assertRaises(CommandWriteError):
			frappe.get_doc(
				{
					"doctype": "Strategic Plan",
					"title": f"Direct {self.suffix}",
					"plan_role": "Primary",
					"period_start": "2040-07-01",
					"period_end": "2045-06-30",
				}
			).insert()

	def test_author_cannot_activate_a_draft_over_rest(self):
		author = self._author()
		_, version = self._plan_and_version()
		frappe.set_user(author)
		for call in (
			lambda: frappe.client.set_value("Strategic Plan Version", version, "status", "Active"),
			lambda: frappe.get_doc("Strategic Plan Version", version).update({"status": "Active"}).save(),
		):
			with self.assertRaises(frappe.PermissionError):
				call()
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", version, "status"), "Draft")

	def test_author_cannot_edit_an_active_version_over_rest(self):
		author = self._author()
		_, version = self._plan_and_version()
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")
		before = str(frappe.db.get_value("Strategic Plan Version", version, "effective_to"))
		frappe.set_user(author)
		with self.assertRaises(frappe.PermissionError):
			frappe.client.set_value("Strategic Plan Version", version, "effective_to", "2044-01-01")
		frappe.set_user("Administrator")
		self.assertEqual(str(frappe.db.get_value("Strategic Plan Version", version, "effective_to")), before)

	def test_docperm_grants_no_write_create_or_delete_on_lifecycle_doctypes(self):
		author = self._author()
		for doctype in LIFECYCLE_DOCTYPES:
			for ptype in ("write", "create", "delete"):
				self.assertFalse(
					frappe.has_permission(doctype, ptype, user=author), f"Strategy Author {ptype} {doctype}"
				)
		perms = frappe.get_all(
			"DocPerm",
			filters={"parent": ["in", LIFECYCLE_DOCTYPES]},
			fields=["parent", "role", "write", "create", "delete"],
		)
		for row in perms:
			self.assertFalse(row.write or row.create or row.delete, f"{row.role} on {row.parent}")

	def test_commands_still_write(self):
		author = self._author()
		approver = self._approver()
		_, version = self._plan_and_version()
		self._fill_hierarchy(version)
		frappe.set_user(author)
		self.assertEqual(self._api_submit(version)["status"], "Submitted for approval")
		frappe.set_user(approver)
		self.assertEqual(self._api_approve(version)["status"], "Active")


class TestChangeSetConfinement(AudRemediationBase):
	"""AUD-STR-001 / AUD-STR-002."""

	def test_deletes_refuse_any_other_doctype(self):
		author = self._author()
		_, version = self._plan_and_version()
		todo = frappe.get_doc({"doctype": "ToDo", "description": f"keep me {self.suffix}"}).insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "ToDo", todo.name, force=True, ignore_permissions=True)
		audit = frappe.get_all("Audit Event", limit=1, pluck="name")
		frappe.set_user(author)
		for doctype, name in [("ToDo", todo.name)] + ([("Audit Event", audit[0])] if audit else []):
			with self.assertRaises(frappe.ValidationError):
				save_strategy_structure_draft(version, deletes=[{"doctype": doctype, "name": name}])
		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("ToDo", todo.name))
		if audit:
			self.assertTrue(frappe.db.exists("Audit Event", audit[0]))

	def test_delete_of_a_row_in_an_active_version_is_refused(self):
		author, _plan, _v1, v1_content, v2 = self._active_with_successor_draft()
		frappe.set_user(author)
		for doctype, key in (
			("Performance Target", "target"),
			("Performance Indicator", "indicator"),
			("Strategy Node", "objective"),
		):
			with self.assertRaises(frappe.ValidationError):
				save_strategy_structure_draft(v2, deletes=[{"doctype": doctype, "name": v1_content[key]}])
		frappe.set_user("Administrator")
		for doctype, key in (
			("Performance Target", "target"),
			("Performance Indicator", "indicator"),
			("Strategy Node", "objective"),
		):
			self.assertTrue(frappe.db.exists(doctype, v1_content[key]), doctype)

	def test_update_of_a_row_from_another_version_is_refused(self):
		author, _plan, v1, v1_content, v2 = self._active_with_successor_draft()
		v2_indicator = frappe.get_all("Performance Indicator", filters={"plan_version_id": v2}, pluck="name")[0]
		v2_node = frappe.get_all(
			"Strategy Node", filters={"plan_version_id": v2, "node_type": "Strategic Objective"}, pluck="name"
		)[0]
		frappe.set_user(author)
		attempts = [
			{"targets": [{"name": v1_content["target"], "indicator_id": v2_indicator}]},
			{"indicators": [{"name": v1_content["indicator"], "indicator_name": "Moved"}]},
			{"nodes": [{"name": v1_content["objective"], "title": "Moved", "display_order": 3}]},
			# a parent from the other version
			{"nodes": [{"node_type": "Strategic Objective", "title": "x", "display_order": 9, "parent_node_id": v1_content["programme"]}]},
			# an indicator measuring a node of the other version
			{"indicators": [{"measures_node_id": v1_content["objective"], "indicator_name": "Cross"}]},
			# a target on an indicator of the other version
			{"targets": [{"indicator_id": v1_content["indicator"], "fiscal_year": "2041-2042", "comparison": "At least", "target_value": 5}]},
		]
		for kwargs in attempts:
			with self.assertRaises(frappe.ValidationError, msg=str(kwargs)):
				save_strategy_structure_draft(v2, **kwargs)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Performance Target", v1_content["target"], "indicator_id"), v1_content["indicator"])
		self.assertEqual(frappe.db.get_value("Performance Indicator", v1_content["indicator"], "indicator_name"), "Indicator")
		self.assertEqual(frappe.db.get_value("Strategy Node", v1_content["objective"], "plan_version_id"), v1)
		self.assertEqual(frappe.db.get_value("Strategy Node", v1_content["objective"], "title"), "Objective")
		del v2_node

	def test_delete_of_the_versions_own_rows_still_works(self):
		author = self._author()
		_, version = self._plan_and_version()
		frappe.set_user(author)
		out = save_strategy_structure_draft(
			version, nodes=[{"client_id": "$p", "node_type": "Pillar", "title": "P", "display_order": 1}]
		)
		self._cleanup.extend(("Strategy Node", n) for n in out["nodes"])
		out2 = save_strategy_structure_draft(version, deletes=[{"doctype": "Strategy Node", "name": out["nodes"][0]}])
		self.assertEqual(out2["deleted"], out["nodes"])

	def test_structure_save_requires_a_draft_version(self):
		author = self._author()
		_, version = self._plan_and_version()
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")
		frappe.set_user(author)
		with self.assertRaises(frappe.ValidationError):
			save_strategy_structure_draft(version, deletes=[{"doctype": "Strategy Node", "name": "none"}])


class TestPlanDraftSave(AudRemediationBase):
	"""AUD-STR-003."""

	def _expect_state_error(self, payload):
		with self.assertRaises(frappe.ValidationError) as caught:
			save_strategy_plan_draft(payload)
		return caught

	def test_active_version_cannot_be_edited_through_the_draft_command(self):
		author = self._author()
		plan, version = self._plan_and_version()
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")
		frappe.set_user(author)
		self._expect_state_error({"plan_id": plan, "plan_version_id": version, "effective_from": "2041-01-01"})
		frappe.set_user("Administrator")
		self.assertEqual(str(frappe.db.get_value("Strategic Plan Version", version, "effective_from")), "2040-07-01")

	def test_a_version_of_another_plan_is_refused(self):
		author = self._author()
		plan_a, version_a = self._plan_and_version()
		_plan_b, version_b = self._plan_and_version()
		frappe.set_user(author)
		self._expect_state_error({"plan_id": plan_a, "plan_version_id": version_b, "title": "Hijack"})
		frappe.set_user("Administrator")
		self.assertNotEqual(frappe.db.get_value("Strategic Plan", plan_a, "title"), "Hijack")
		del version_a

	def test_identity_of_a_plan_with_an_active_version_is_not_rewritten(self):
		author, plan, _v1, _content, v2 = self._active_with_successor_draft()
		title = frappe.db.get_value("Strategic Plan", plan, "title")
		frappe.set_user(author)
		self._expect_state_error({"plan_id": plan, "plan_version_id": v2, "title": "Renamed", "period_end": "2044-06-30"})
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Strategic Plan", plan, "title"), title)
		self.assertEqual(str(frappe.db.get_value("Strategic Plan", plan, "period_end")), "2045-06-30")

	def test_successor_draft_dates_and_unchanged_identity_can_be_saved(self):
		author, plan, _v1, _content, v2 = self._active_with_successor_draft()
		title = frappe.db.get_value("Strategic Plan", plan, "title")
		frappe.set_user(author)
		out = save_strategy_plan_draft(
			{"plan_id": plan, "plan_version_id": v2, "title": title, "effective_from": "2042-07-01"}
		)
		self.assertEqual(out["version"]["effective_from"], "2042-07-01")


class TestOpenEndedApplicability(AudRemediationBase):
	"""AUD-STR-004 — a blank 'Use until' is open-ended, never non-overlapping."""

	def test_open_ended_active_version_resolves(self):
		_, version = self._plan_and_version(effective_to=None)
		self._fill_hierarchy(version)
		frappe.db.set_value("Strategic Plan Version", version, "status", "Active")
		ensure_fiscal_year(2041)
		ctx = consumer.resolve_strategy_context(as_of_date="2043-01-01")
		self.assertEqual(ctx["primary_plan"]["version_id"], version)
		self.assertEqual(consumer.resolve_strategy_context(fiscal_year="2041-2042")["primary_plan"]["version_id"], version)

	def test_second_open_ended_primary_overlaps(self):
		_, v1 = self._plan_and_version(effective_to=None)
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")
		_, v2 = self._plan_and_version(effective_to=None)
		doc = frappe.get_doc("Strategic Plan Version", v2)
		doc.status = "Active"
		with maintenance_write("Strategy", reason="test"), self.assertRaises(frappe.ValidationError) as caught:
			doc.save()
		self.assertIn("overlapping", str(caught.exception))

	def test_dated_primary_overlaps_an_open_ended_one(self):
		_, v1 = self._plan_and_version(effective_to=None)
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")
		_, v2 = self._plan_and_version()
		doc = frappe.get_doc("Strategic Plan Version", v2)
		doc.status = "Active"
		with maintenance_write("Strategy", reason="test"), self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_approving_a_successor_with_blank_until_keeps_context_resolvable(self):
		author = self._author("open_a")
		approver = self._approver("open_b")
		plan, v1 = self._plan_and_version()
		self._fill_hierarchy(v1)
		frappe.db.set_value("Strategic Plan Version", v1, "status", "Active")
		frappe.set_user(author)
		v2 = create_strategy_successor_version(plan)["name"]
		frappe.set_user("Administrator")
		self._track_version_content(v2)
		frappe.set_user(author)
		save_strategy_plan_draft(
			{"plan_id": plan, "plan_version_id": v2, "effective_from": "2043-01-01", "effective_to": None}
		)
		self._api_submit(v2)
		frappe.set_user(approver)
		self.assertEqual(self._api_approve(v2)["status"], "Active")
		frappe.set_user("Administrator")
		ctx = consumer.resolve_strategy_context(as_of_date="2043-06-01")
		self.assertEqual(ctx["primary_plan"]["version_id"], v2)


class TestGeneratedReferences(AudRemediationBase):
	"""AUD-STR-008."""

	def test_caller_cannot_supply_a_generated_reference(self):
		author = self._author()
		_, version = self._plan_and_version()
		frappe.set_user(author)
		first = save_strategy_structure_draft(
			version, nodes=[{"node_type": "Pillar", "title": "P", "display_order": 1}]
		)
		self._cleanup.extend(("Strategy Node", n) for n in first["nodes"])
		existing_ref = frappe.db.get_value("Strategy Node", first["nodes"][0], "strategy_node_id")
		with self.assertRaises(frappe.ValidationError):
			save_strategy_structure_draft(
				version,
				nodes=[{"node_type": "Pillar", "title": "Q", "display_order": 2, "strategy_node_id": existing_ref}],
			)
		with self.assertRaises(frappe.ValidationError):
			save_strategy_structure_draft(
				version, nodes=[{"name": first["nodes"][0], "strategy_node_id": "MOH-NODE-9999"}]
			)
		self.assertEqual(
			frappe.db.count("Strategy Node", {"strategy_node_id": existing_ref}), 1
		)

	def test_a_duplicate_reference_is_refused_by_the_record_itself(self):
		_, version = self._plan_and_version()
		nodes = self._fill_hierarchy(version)
		ref = frappe.db.get_value("Strategy Node", nodes["pillar"], "strategy_node_id")
		with maintenance_write("Strategy", reason="test"), self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": version,
					"node_type": "Pillar",
					"title": "Dup",
					"display_order": 50,
					"strategy_node_id": ref,
				}
			).insert()


class TestExpiredApplicability(AudRemediationBase):
	"""AUD-STR-011."""

	def test_approval_refuses_a_version_that_has_already_expired(self):
		author = self._author("exp_a")
		approver = self._approver("exp_b")
		_, version = self._plan_and_version(effective_from="2040-07-01", effective_to="2041-06-30")
		self._fill_hierarchy(version)
		frappe.set_user(author)
		self._api_submit(version)
		frappe.set_user(approver)
		with self.assertRaises(frappe.ValidationError) as caught:
			self._api_approve(version)
		self.assertIn("ended", str(caught.exception))
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", version, "status"), "Submitted for approval")
