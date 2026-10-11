# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Project Owner, 10 October 2026: "System Manager status alone must not grant access" to Opening incident records
or the identifiers they link. The incident, exception, decision-item, entry and register-request records are sealed
(no DocPerm row, deny hooks, a controller that refuses a read, no technical-search resolver); the opening page shows
an incident only to the committee, the Accounting Officer and the Opening access support holder."""

from __future__ import annotations

import json

import frappe

from kentender_core.tests import v16_fixtures as fx
from kentender_procurement.bid_opening.services import export, incident_access, incidents, reads, simulation
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, OUTSIDER, SUPPORT, OpeningCase
from kentender_procurement.bid_submission.services.sealed import SEALED_DOCTYPES, SealedRecordMixin
from kentender_procurement.bid_submission.tests.support import key

OPENING_SEALED = ("Opening Incident Access Event", "Opening Access Incident", "Opening Exception", "Opening Decision Item", "Opening Entry", "Opening Register Request")
SYSTEM_MANAGER = "kt.test.bop.sealed.sysmgr@example.test"  # what `fx.user` returns for this local part


def as_user(user, fn, *args, **kwargs):
	frappe.set_user(user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user("Administrator")


def attempt(fn, *args, **kwargs):
	try:
		return {"ok": fn(*args, **kwargs)}
	except (frappe.PermissionError, frappe.DoesNotExistError) as exc:
		return {"refused": type(exc).__name__}


class IncidentCase(OpeningCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		assert fx.user("bop.sealed.sysmgr", "BOP Sealed System Manager", roles=("System Manager",)) == SYSTEM_MANAGER

	def ready(self):
		self.prepared()
		self.at(self.minutes_before(0.5))
		for user in (CHAIR, MEMBER, INDEPENDENT):
			self.join(user)
		self.close_box()
		self.heartbeat_all()
		return self.receive()

	def raise_incident(self):
		self.ready()
		simulation.set_controls(opening_profile_down=1, notify_outcome="Deliver")
		self.at(self.minutes_after(5 / 60))
		self.heartbeat_all()
		self.assertEqual(self.sweep()["incidents"], 1)
		case = frappe.db.get_value("Bid Opening Case", {"tender": self.name})
		[incident] = incidents.open_incidents(case)
		return case, incident


class TestIncidentRecordsAreSealed(IncidentCase):
	def test_the_records_are_sealed_families_with_no_docperm(self):
		self.assertTrue(set(OPENING_SEALED) <= set(SEALED_DOCTYPES))
		for doctype in OPENING_SEALED:
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).permissions, [], doctype)
				self.assertTrue(issubclass(frappe.get_doc({"doctype": doctype}).__class__, SealedRecordMixin), doctype)
				self.assertTrue(frappe.get_hooks("has_permission")[doctype])
				self.assertTrue(frappe.get_hooks("permission_query_conditions")[doctype])

	def test_administrator_and_system_manager_read_no_incident_by_any_path(self):
		from frappe.client import get, get_count, get_list

		_case, incident = self.raise_incident()
		for user in ("Administrator", SYSTEM_MANAGER):
			with self.subTest(user=user):
				self.assertEqual(attempt(as_user, user, get, "Opening Access Incident", incident.name), {"refused": "PermissionError"})
				self.assertIn(attempt(as_user, user, get_count, "Opening Access Incident"), ({"ok": 0}, {"refused": "PermissionError"}))
				self.assertIn(attempt(as_user, user, get_list, "Opening Access Incident", fields=["name"]), ({"ok": []}, {"refused": "PermissionError"}))
				doc = frappe.get_doc("Opening Access Incident", incident.name)
				frappe.set_user(user)
				try:
					self.assertFalse(doc.has_permission("read"))
				finally:
					frappe.set_user("Administrator")

	def test_the_technical_record_search_finds_no_incident(self):
		from kentender_core.services import technical_search

		_case, incident = self.raise_incident()
		for user in ("Administrator", SYSTEM_MANAGER):
			text = json.dumps(technical_search.search(query=incident.incident_id, user=user))
			self.assertNotIn(incident.incident_id, text)
			self.assertNotIn("Opening access incident", text)

	def test_the_opening_page_shows_an_incident_only_to_those_who_may(self):
		case, incident = self.raise_incident()
		for user in (CHAIR, SUPPORT):
			with self.subTest(user=user):
				self.assertEqual([i["incident_id"] for i in reads.get_opening(tender=self.name, user=user)["incidents"]], [incident.incident_id])
		for user in ("Administrator", SYSTEM_MANAGER):
			with self.subTest(user=user):
				view = reads.get_opening(tender=self.name, user=user)
				self.assertEqual(view["incidents"], [])
				self.assertIsNone(view["decision"])
				self.assertIsNone(view["technical_status"]["incidents"])  # not a count of zero: the reader is not told
		self.assertEqual(reads.get_opening(tender=self.name, user=SUPPORT)["technical_status"]["incidents"], 1)

	def test_the_notice_to_support_never_links_to_the_incident_record(self):
		case, incident = self.raise_incident()
		logs = frappe.get_all("Notification Log", filters={"for_user": SUPPORT}, fields=["subject", "document_type", "document_name", "link"] if frappe.get_meta("Notification Log").has_field("link") else ["subject", "document_type", "document_name"])
		text = json.dumps(logs, default=str)
		self.assertNotIn("opening-access-incident", text)
		self.assertNotIn(incident.incident_id, json.dumps([l for l in logs if l.get("document_type") == "Opening Access Incident"], default=str))


class TestIncidentDetailReadsAreAudited(IncidentCase):
	"""Project Owner, 10 October 2026: reading an incident's details, and exporting it, record who, when, which incident, what action,
	for what purpose and with what outcome; no incident content is in the event; the trail is read by the Auditor and the Accounting
	Officer only; a page refresh records nothing."""

	PURPOSE = "Investigate the problem"

	def events(self):
		return frappe.get_all(incident_access.EVENT, fields=["incident_id", "action", "purpose", "actor", "actor_role", "outcome", "request_key"], order_by="creation asc")

	def details(self, user, incident, purpose=None, request_key=None):
		return incident_access.get_details(tender=self.name, incident=incident.incident_id, purpose=purpose or self.PURPOSE, idempotency_key=request_key or key(), user=user)

	def test_the_supporter_reads_the_details_with_the_envelope_and_one_event_records_it(self):
		_case, incident = self.raise_incident()
		before = len(self.events())
		first = self.details(SUPPORT, incident, request_key="req-support-1")
		self.assertTrue(first["ok"])
		self.assertEqual(first["capacity"], incident_access.SUPPORT)
		self.assertIn("envelope", first["details"])
		self.assertEqual(self.details(SUPPORT, incident, request_key="req-support-1"), first)  # the same request again records nothing more
		new = self.events()[before:]
		self.assertEqual(len(new), 1)
		self.assertEqual((new[0].incident_id, new[0].action, new[0].purpose, new[0].actor, new[0].actor_role, new[0].outcome), (incident.incident_id, "View details", self.PURPOSE, SUPPORT, "Opening access support", "Allowed"))

	def test_the_chair_and_the_accounting_officer_read_details_without_the_envelope(self):
		_case, incident = self.raise_incident()
		for user, capacity in ((CHAIR, "Chair"), (AO, "Accounting Officer")):
			with self.subTest(user=user):
				result = self.details(user, incident)
				self.assertTrue(result["ok"])
				self.assertEqual(result["capacity"], capacity)
				self.assertNotIn("envelope", result["details"])

	def test_a_purpose_is_required_and_a_read_without_one_records_nothing(self):
		_case, incident = self.raise_incident()
		before = len(self.events())
		refused = incident_access.get_details(tender=self.name, incident=incident.incident_id, purpose="", idempotency_key=key(), user=SUPPORT)
		self.assertEqual((refused["ok"], sorted(refused["errors"])), (False, ["purpose"]))
		self.assertEqual(len(self.events()), before)

	def test_everyone_else_is_refused_in_the_masked_words_and_the_refusal_is_recorded(self):
		_case, incident = self.raise_incident()
		for user in (MEMBER, OUTSIDER, AUDITOR, "Administrator", SYSTEM_MANAGER):
			with self.subTest(user=user):
				before = len(self.events())
				with self.assertRaises(frappe.DoesNotExistError):
					self.details(user, incident)
				recorded = self.events()[before:]
				self.assertEqual([(r.actor, r.outcome) for r in recorded], [(user, "Refused")])

	def test_a_refresh_of_the_opening_page_records_no_read(self):
		self.raise_incident()
		before = len(self.events())
		for user in (CHAIR, SUPPORT, AO):
			for _ in range(3):
				reads.get_opening(tender=self.name, user=user)
		self.assertEqual(len(self.events()), before)

	def test_the_event_holds_no_incident_content(self):
		_case, incident = self.raise_incident()
		self.details(SUPPORT, incident)
		text = json.dumps(self.events(), default=str)
		for word in (incident.envelope_id or "ENV-NONE-XYZ", "Package", "resolution"):
			self.assertNotIn(word, text)

	def test_an_export_records_one_event_per_incident_it_includes(self):
		_case, incident = self.raise_incident()
		before = len(self.events())
		bundle = export.export_opening(tender=self.name, user=AO)
		self.assertEqual([r["incident_id"] for r in bundle["incidents"]], [incident.incident_id])
		new = self.events()[before:]
		self.assertEqual([(r.action, r.purpose, r.actor, r.actor_role) for r in new], [("Export", incident_access.EXPORT_PURPOSE, AO, "Accounting Officer")])

	def test_only_the_auditor_and_the_accounting_officer_read_the_trail(self):
		_case, incident = self.raise_incident()
		self.details(SUPPORT, incident)
		for user in (AO, AUDITOR):
			with self.subTest(user=user):
				rows = incident_access.trail(tender=self.name, user=user)["rows"]
				self.assertEqual([(r["incident_id"], r["action"], r["capacity"], r["outcome"]) for r in rows], [(incident.incident_id, "View details", "Opening access support", "Allowed")])
				self.assertEqual(set(rows[0]), {"incident_id", "action", "purpose", "actor", "capacity", "at_label", "outcome"})
		for user in (CHAIR, SUPPORT, MEMBER, OUTSIDER, "Administrator", SYSTEM_MANAGER):
			with self.subTest(refused=user), self.assertRaises(frappe.DoesNotExistError):
				incident_access.trail(tender=self.name, user=user)

	def test_an_access_event_is_never_changed_or_read_by_desk(self):
		_case, incident = self.raise_incident()
		self.details(SUPPORT, incident)
		name = frappe.get_all(incident_access.EVENT, pluck="name")[0]
		doc = frappe.get_doc(incident_access.EVENT, name)
		doc.flags.kt_bop_command = True
		doc.outcome = "Refused"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		from frappe.client import get

		self.assertEqual(attempt(as_user, SYSTEM_MANAGER, get, incident_access.EVENT, name), {"refused": "PermissionError"})

	def test_the_opening_page_tells_who_may_read_details(self):
		self.raise_incident()
		for user, expected in ((SUPPORT, True), (CHAIR, True), (AO, True), (MEMBER, False), (SYSTEM_MANAGER, False)):
			with self.subTest(user=user):
				self.assertEqual(reads.get_opening(tender=self.name, user=user)["viewer"]["can_read_incident_details"], expected)
