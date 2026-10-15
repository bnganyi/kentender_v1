# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.10 and HOME-CHG-001 v0.6 section 7 (plan Phase 10 and 11; tracker CM8-1103; FU-CM-68): contract work on the Home page, and the bell.

Home shows each person the contract work that is theirs, with the reason when it is blocked, who it is waiting on, what is coming up on a verified date, and what they recently did: read from the stored tasks and
filtered by the same authority as the contract's own list, so nobody sees work on a contract they may not read. The bell raises one alert for the person whose turn it has just become, linking to the step on its own
tab (and never to a Desk form); work that waits or is scheduled is not an alert."""

from __future__ import annotations

import frappe

from kentender_contracts.services import formation, home_provider, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase
from kentender_core.services import home_entries as he
from kentender_core.services import home_workspace


class HomeCase(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)
		world.ensure_workflow()
		cls.addClassCleanup(world.drop_workflow)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p = self.people
		self.tag = self.id().rsplit(".", 1)[-1][:24]
		self.t = tw.Thread(self.p, tag=self.tag, item=world.ITEM_PLAIN)
		out = tw.receive(self.p, contract_id=self.t.contract_id)
		self.case = self.t.case = out["contract"]

	def activate(self):
		"""The agreement is signed by both parties and in force."""
		formation.save_particulars(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("p"), actor=self.p["brian"], values=tw.package_particulars(self.p, False, self.t.item))
		formation.request_signatures(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("send"), actor=self.p["charles"])
		formation.sign_contract(self.case, party="Supplier", expected_version=self.t.version(), idempotency_key=self.t.key("ss"), actor=self.p["mary"])
		formation.sign_contract(self.case, party="Entity", expected_version=self.t.version(), idempotency_key=self.t.key("se"), actor=self.p["amina"])

	def entries(self, persona: str, region: str):
		found = home_provider.entries(user=self.p[persona], region=region)
		for entry in found or []:
			he.validate(entry)
		return found

	def mine(self, persona: str, region: str):
		return [e for e in (self.entries(persona, region) or []) if e["root"] == self.t.contract_id]

	def bells(self, persona: str):
		return frappe.get_all("Notification Log", filters={"for_user": self.p[persona], "document_type": "Contract Case", "document_name": self.case}, fields=["subject", "link", "type"], order_by="creation asc")


class TestMyWork(HomeCase):
	def test_the_head_of_procurement_has_the_step_on_the_contract_and_it_opens_on_its_own_tab(self):
		rows = self.mine("charles", he.MY_WORK)
		self.assertEqual(len(rows), 1)
		row = rows[0]
		self.assertEqual((row["action"], row["blocked"], row["reference"], row["owner"]), ("Review the contract and send it for signature.", False, self.t.contract_id, "contracts"))
		self.assertEqual(row["destination"], {"route": ["contracts", self.case, "agreement"], "route_options": {}})
		self.assertEqual(he.module_label(row["owner"]), "Contracts")

	def test_nothing_is_shown_for_a_contract_the_person_may_not_read_or_for_a_person_with_no_part_in_contracts(self):
		self.assertIsNone(home_provider.entries(user=self.p["stranger"], region=he.MY_WORK))
		self.assertEqual([e for e in (home_provider.entries(user=self.p["julia"], region=he.MY_WORK) or []) if e["root"] == self.t.contract_id], [], "an inspector not yet appointed reads nothing of it")

	def test_a_supplier_has_the_portal_and_no_home(self):
		for region in he.REGIONS:
			self.assertIsNone(home_provider.entries(user=self.p["mary"], region=region))

	def test_oversight_is_not_a_contract_concept_and_an_unknown_region_is_a_defect(self):
		self.assertIsNone(home_provider.entries(user=self.p["charles"], region=he.OVERSIGHT))
		with self.assertRaises(ValueError):
			home_provider.entries(user=self.p["charles"], region="nonsense")


class TestWaitingAndCompleted(HomeCase):
	def sent(self):
		formation.save_particulars(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("p"), actor=self.p["brian"], values=tw.package_particulars(self.p, False, self.t.item))
		formation.request_signatures(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("send"), actor=self.p["charles"])

	def test_the_sender_waits_on_the_supplier_signatory_and_is_told_who_and_since_when(self):
		self.sent()
		waiting = self.mine("charles", he.WAITING)
		self.assertEqual(len(waiting), 1)
		self.assertEqual(waiting[0]["holder"], "Mary Wanjiku")
		self.assertTrue(waiting[0]["since"])
		self.assertEqual(self.mine("charles", he.MY_WORK), [], "the head's own step is done")

	def test_a_person_s_own_recorded_acts_are_recently_completed_and_nobody_else_s(self):
		self.sent()
		formation.sign_contract(self.case, party="Supplier", expected_version=self.t.version(), idempotency_key=self.t.key("ss"), actor=self.p["mary"])
		formation.sign_contract(self.case, party="Entity", expected_version=self.t.version(), idempotency_key=self.t.key("se"), actor=self.p["amina"])
		done = self.mine("amina", he.COMPLETED)
		self.assertEqual([(e["action"], e["sentence"]) for e in done], [("Signed the agreement", "signed the agreement")])
		self.assertEqual(self.mine("charles", he.COMPLETED), [], "the head recorded no signing")


class TestComingUp(HomeCase):
	def test_a_scheduled_step_with_a_verified_date_is_coming_up_and_one_without_is_not_shown(self):
		self.activate()
		work.assign(self.case, "RecordWarrantyClaim", "Warranty for 10 accepted units", "warranty acceptance 1", 1, [self.p["julia"]], role="Contract owner", state="Scheduled", due="2028-07-20 00:00:00", due_verified=True)
		work.assign(self.case, "RecordWarrantyClaim", "An undated reminder", "warranty acceptance 2", 1, [self.p["julia"]], role="Contract owner", state="Scheduled")
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["julia"])
		self.t.appointed()
		coming = self.mine("julia", he.COMING_UP)
		self.assertEqual([e["action"] for e in coming], ["Warranty for 10 accepted units"])
		self.assertEqual(str(coming[0]["scheduled_at"].date() if hasattr(coming[0]["scheduled_at"], "date") else coming[0]["scheduled_at"]), "2028-07-20")


class TestTheBell(HomeCase):
	def test_a_step_that_becomes_the_person_s_turn_raises_one_alert_linking_to_its_own_tab(self):
		alerts = self.bells("charles")
		self.assertEqual([a["subject"] for a in alerts], ["Review the contract and send it for signature."])
		self.assertEqual(alerts[0]["link"], f"/desk/contracts/{self.case}/agreement")
		self.assertFalse(alerts[0]["link"].startswith("/app/contract-case"), "never a Desk form")

	def test_a_replay_and_a_waiting_item_raise_no_second_alert(self):
		before = len(self.bells("charles"))
		work.assign(self.case, "RequestContractSignatures", "Review the contract and send it for signature.", "agreement 1", 1, [self.p["charles"]])
		self.assertEqual(len(self.bells("charles")), before, "the same task again is the same item")
		work.assign(self.case, work.waiting_command("SignContractVersion", "supplier"), "Waiting for the supplier signature.", "agreement 1", 1, [self.p["charles"]], state="Waiting")
		self.assertEqual(len(self.bells("charles")), before, "waiting is not an alert")

	def test_the_next_holder_is_alerted_when_the_work_is_handed_on(self):
		formation.save_particulars(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("p"), actor=self.p["brian"], values=tw.package_particulars(self.p, False, self.t.item))
		formation.request_signatures(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("send"), actor=self.p["charles"])
		self.assertEqual([a["subject"] for a in self.bells("mary")], ["Review the agreement before signing."], "the supplier signatory is alerted when it is their turn")


class TestHomeAsTheHomePageReadsIt(HomeCase):
	def test_the_home_workspace_carries_the_contract_row_for_the_head_of_procurement(self):
		found = home_workspace.get_workspace(self.p["charles"], regions=["my_work"], providers=[home_provider.entries])
		rows = [row for row in found["regions"]["my_work"]["entries"] if row.get("reference") == self.t.contract_id]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["module"], "Contracts")
