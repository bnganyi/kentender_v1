# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FU-CM-123 (the Project Owner's decision of 16 October 2026): the bell follows the approved notification table of CM-CHG-001 v0.8 section 5.10 and nothing beyond it.

Every command the services assign is either one the table notifies (`notifications.NOTIFY`, with the row that names it) or named quiet with its reason (`notifications.QUIET`); a task of a quiet command, a waiting item and a
scheduled item raise no alert, and the alert of a task that does links to the step on its own tab."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import notifications, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

APP = Path(frappe.get_app_path("kentender_contracts"))
SPEC = APP.resolve().parents[1] / "docs/mvp-1-r1/21_contract_management/KenTender_CM-CHG-001_Contract_Management_v0_8.md"
ASSIGNED = (
	re.compile(r"work\.assign\(\s*[^,]+,\s*\"(\w+)\""),
	re.compile(r"_hop_task\(\s*\w+,\s*\"(\w+)\""),
	re.compile(r"work\.incident\(\s*[^,]+,\s*\"(\w+)\""),
)


def sources() -> str:
	return "\n".join(path.read_text() for path in [*sorted((APP / "services").glob("*.py")), APP / "award_receiver.py"])


class TestEveryTaskIsClassified(IntegrationTestCase):
	def test_every_command_the_services_assign_is_in_the_table_or_named_quiet_and_no_command_is_both(self):
		text = sources()
		assigned = {name for pattern in ASSIGNED for name in pattern.findall(text)}
		self.assertGreater(len(assigned), 40, "the scan found the assignments")
		unclassified = sorted(assigned - set(notifications.NOTIFY) - set(notifications.QUIET))
		self.assertEqual(unclassified, [], "a new kind of task is placed in the table (NOTIFY) or named quiet with its reason (QUIET)")
		self.assertEqual(sorted(set(notifications.NOTIFY) & set(notifications.QUIET)), [])

	def test_nothing_in_either_list_is_a_command_no_service_assigns(self):
		text = sources()
		stale = sorted(command for command in [*notifications.NOTIFY, *notifications.QUIET] if f'"{command}"' not in text)
		self.assertEqual(stale, [], "an entry whose task was removed is removed with it")

	def test_every_row_a_command_cites_is_a_row_of_the_specifications_table(self):
		lines = SPEC.read_text().split("\n")
		start = next(i for i, line in enumerate(lines) if line.startswith("### 5.10"))
		end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("### "))
		events = {line.split("|")[1].strip() for line in lines[start:end] if line.startswith("| ") and not line.startswith("| Event") and not line.startswith("|---")}
		self.assertGreaterEqual(len(events), 30)
		wrong = {command: row for command, row in notifications.NOTIFY.items() if row not in events}
		self.assertEqual(wrong, {}, "each command names the Event cell of the row that notifies its holder")

	def test_a_waiting_item_is_never_an_alert(self):
		self.assertFalse(notifications.raises_alert(work.waiting_command("SignContractVersion", "supplier")))
		self.assertTrue(notifications.raises_alert("SignContractVersion"))
		self.assertFalse(notifications.raises_alert("ResolveDeliveryException"))
		self.assertFalse(notifications.raises_alert("SomethingNobodyAssigns"), "an unknown command is quiet; the scan above is what catches it")


class TestTheBellFollowsTheTable(ContractCase):
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
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=world.ITEM_PLAIN)
		self.case = self.t.case = tw.receive(self.p, contract_id=self.t.contract_id)["contract"]

	def bells(self, persona: str) -> list[str]:
		return [row.subject for row in frappe.get_all("Notification Log", filters={"for_user": self.p[persona], "document_type": "Contract Case", "document_name": self.case}, fields=["subject"], order_by="creation asc")]

	def test_a_task_the_table_names_alerts_its_holder_and_one_it_does_not_name_alerts_nobody(self):
		before = len(self.bells("julia"))
		work.assign(self.case, "ResolveDeliveryException", "Review the delivery: it has exceptions.", "arrival 91", 1, [self.p["julia"]], role="Contract owner")
		self.assertEqual(len(self.bells("julia")), before, "no row names it")
		work.assign(self.case, "SignAcceptanceReport", "Sign the acceptance report.", "acceptance 91", 1, [self.p["julia"]], role="Contract inspection")
		self.assertEqual(self.bells("julia")[before:], ["Sign the acceptance report."])

	def test_a_scheduled_item_and_a_waiting_item_are_not_alerts(self):
		before = len(self.bells("charles"))
		work.assign(self.case, "ActivateContractChange", "Bring amendment 91 into effect.", "amendment 91", 1, [self.p["charles"]], role=work.HOP, state="Scheduled")
		work.assign(self.case, work.waiting_command("SignContractVersion", "entity"), "Waiting for the entity signature.", "agreement 91", 1, [self.p["charles"]], role=work.HOP, state="Waiting")
		self.assertEqual(len(self.bells("charles")), before)
