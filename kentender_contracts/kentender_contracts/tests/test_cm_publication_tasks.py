# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FU-CM-108 and FU-CM-79 (the Project Owner's decision of 16 October 2026): "Use Duties plus actionable tasks. Duties preserves the obligation and evidence. Create a task when someone can act; while
requirements are unresolved, give the responsible owner a resolution task rather than an endlessly blocked publishing task."

The publication duty stays in the contract's Duties. Where the requirement is verified the head of procurement has a task to record the publication as it happened (channel, day, evidence); where it is not, the head
has a task to put the legal source in front of the legal owner, which ends when source evidence is recorded; a requirement verified later brings the recording task."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import obligations, work
from kentender_contracts.tests import dead_end
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

UNVERIFIED, VERIFIED = "KE-PPADA-2015", "SYNTHETIC-ILLUSTRATIVE"
RESOLVE_TITLE = "Resolve the publication requirement: the legal and reporting owner must confirm it."


class PublicationCase(ContractCase):
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
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active(publication_open=True)
		self.row = obligations.get(self.case, "Publication", "publication")

	def profile(self, name: str) -> None:
		frappe.db.set_value("Contract Case", self.case, "legal_profile", name)
		obligations.reconcile_tasks(self.case)

	def live(self, command: str, who: str = "charles") -> list[dict]:
		return [t for t in work.live(self.case) if t["command"] == command and t["holder"] == self.p[who]]

	def bells(self, who: str = "charles") -> list[str]:
		return [r.subject for r in frappe.get_all("Notification Log", filters={"for_user": self.p[who], "document_name": self.case}, fields=["subject"], order_by="creation asc")]

	def board(self, who: str = "charles") -> dict:
		return router.board_for(self.case, self.p[who], tab="Obligations", subject=("publication",))


class TestWhileTheRequirementIsUnresolved(PublicationCase):
	def test_the_head_has_a_resolution_task_not_a_publishing_task_and_the_board_offers_the_source_evidence(self):
		self.profile(UNVERIFIED)
		self.assertEqual([t["title"] for t in self.live(obligations.RESOLVE)], [RESOLVE_TITLE])
		self.assertEqual(self.live(obligations.PUBLISH), [], "no publishing task nobody can do")
		self.assertIn(RESOLVE_TITLE, self.bells(), "the table notifies the responsible holder at the duty")
		board = self.board()
		self.assertEqual((board["id"], board["p"], board["st"]), ("D15-L", "Record source evidence", "Needs review"))
		dead_end.assert_sound(self, board, "charles")

	def test_recording_the_source_ends_the_resolution_task_and_leaves_the_waiting_item(self):
		self.profile(UNVERIFIED)
		obligations.record_source_evidence(self.case, obligation=self.row.name, reference="PPRA circular 4/2027", dated="2027-06-30", copy="", notes="", expected_version=self.t.version(), idempotency_key=self.t.key("e"),
			actor=self.p["charles"])
		self.assertEqual(self.live(obligations.RESOLVE), [], "done: the source is with the legal owner")
		self.assertTrue([t for t in work.live(self.case) if t["command"] == work.waiting_command(obligations.PUBLISH, "legal")])
		obligations.reconcile_tasks(self.case)
		self.assertEqual(self.live(obligations.RESOLVE), [], "it does not come back while the evidence stands and the rule is still unverified")

	def test_reconciling_again_makes_no_second_task(self):
		self.profile(UNVERIFIED)
		obligations.reconcile_tasks(self.case)
		obligations.reconcile_tasks(self.case)
		self.assertEqual(len(self.live(obligations.RESOLVE)), 1)


class TestOnceTheRequirementIsVerified(PublicationCase):
	def test_the_head_has_a_task_to_record_the_publication_and_the_board_offers_it(self):
		self.profile(UNVERIFIED)
		self.profile(VERIFIED)
		self.assertEqual(self.live(obligations.RESOLVE), [], "the resolution task is superseded")
		self.assertEqual([t["title"] for t in self.live(obligations.PUBLISH)], ["Record the award publication."])
		self.assertIn("Record the award publication.", self.bells())
		board = self.board()
		self.assertEqual((board["id"], board["p"], board["st"]), ("D15-L", "Record publication", "Ready to record"))
		dialog = str(board["dialogs"]["publish"])
		self.assertTrue(all(name in dialog for name in ("channel", "published_on", "evidence", "RecordContractAwardPublication")), "the dialog asks for the channel, the day and the evidence")
		dead_end.assert_sound(self, board, "charles")

	def test_recording_it_ends_the_task_and_the_duty_is_satisfied_with_its_trigger_untouched(self):
		self.profile(VERIFIED)
		trigger = str(self.row.trigger_at)
		out = obligations.record_publication(self.case, obligation=self.row.name, channel="Notice board and website", published_on="2027-07-05", evidence=[{"label": "Notice board photograph", "file": "/private/files/board.jpg"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("p"), actor=self.p["charles"])
		self.assertEqual(out["state"], "Satisfied")
		self.assertEqual(self.live(obligations.PUBLISH), [])
		obligations.reconcile_tasks(self.case)
		self.assertEqual(self.live(obligations.PUBLISH), [], "a satisfied duty has no task")
		self.assertEqual(str(obligations.get(self.case, "Publication", "publication").trigger_at), trigger)
		board = self.board()
		self.assertEqual((board["p"], board["st"]), ("", "Published"))

	def test_a_requirement_verified_after_the_duty_opened_brings_the_task_on_the_daily_sweep(self):
		self.profile(UNVERIFIED)
		self.assertEqual(self.live(obligations.PUBLISH), [])
		frappe.db.set_value("Contract Case", self.case, "legal_profile", VERIFIED)  # the profile was verified since, with no event of its own
		self.assertGreaterEqual(obligations.reconcile_all(), 1)
		self.assertEqual(len(self.live(obligations.PUBLISH)), 1)
		self.assertEqual(self.live(obligations.RESOLVE), [])
