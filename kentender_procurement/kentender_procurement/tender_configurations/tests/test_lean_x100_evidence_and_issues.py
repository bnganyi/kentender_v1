# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""X100 — Evidence Register and Issues foundations prove-list."""

from __future__ import annotations

import base64
import json
import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, cstr, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.bidder_presentation import (
	assert_no_forbidden_bidder_keys,
	dto_as_scan_text,
	scan_bidder_presentation_text,
)
from kentender_procurement.tender_configurations.services.bid_evidence import (
	EVIDENCE_STATUS_CURRENT,
	EVIDENCE_STATUS_MISSING_METADATA,
	EVIDENCE_STATUS_SUPERSEDED,
	freeze_evidence_for_seal,
	get_evidence_register,
	link_evidence,
	replace_evidence,
	upload_evidence,
)
from kentender_procurement.tender_configurations.services.bid_issues import (
	clear_issue_blockers_denied,
	get_issue_register,
)
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.electronic_bid import _get_bid
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	resolve_published_tender_backend,
)
from kentender_procurement.tender_configurations.services.section_status import (
	SEVERITY_BLOCKER,
	issue_item,
)


def _prep_and_publish() -> tuple[str, str, str]:
	ensure_active_canonical_ppra_it_std(force_reimport=False)
	seed = seed_ui00_dashboard(clear=True)
	cfg_id = seed["configurations"][0]
	frappe.db.set_value(
		"Tender Configuration",
		cfg_id,
		{
			"std_version": CANONICAL_PACKAGE_ID,
			"short_scope_summary": "X100 evidence and issues foundation scope.",
		},
	)
	_approve(cfg_id)
	_seed_bidder_facing_config(cfg_id)
	for name in frappe.get_all(
		"Electronic Bid Submission",
		filters={"configuration": cfg_id},
		pluck="name",
	):
		frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
	frappe.db.commit()

	gen = generate_document_preview(cfg_id)
	assert cstr(gen.get("preview_status")) == "Generated", gen.get("render_exception")
	conf = confirm_document_preview(cfg_id, {"confirm_ready_for_handoff": 1})
	pub_id = conf["publication_id"]
	now = now_datetime()
	save_publication_setup(
		pub_id,
		{
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "X100 evidence notice.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=14)),
			"opening_datetime": str(add_to_date(now, days=15, hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": 1,
			"acknowledgement_confirmed": 1,
		},
	)
	published = publish_tender_for_development_preview(pub_id)
	ref = cstr(published.get("publication_ref") or "") or cstr(
		frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
	)
	return cfg_id, pub_id, ref


def _pdf_b64(size: int = 64) -> str:
	"""Valid minimal PDF — Frappe File.before_insert runs pypdf on application/pdf."""
	from io import BytesIO

	from pypdf import PdfWriter

	writer = PdfWriter()
	writer.add_blank_page(width=72 + (size % 20), height=72)
	writer.add_metadata({"/Title": f"x100-evidence-{size}"})
	buf = BytesIO()
	writer.write(buf)
	return base64.b64encode(buf.getvalue()).decode("ascii")


class TestLeanX100EvidenceAndIssues(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.cfg_id, self.pub_id, self.ref = _prep_and_publish()

	def test_file_validation_rejects_disallowed(self):
		with self.assertRaises(frappe.ValidationError):
			upload_evidence(
				self.ref,
				title="Bad exe",
				evidence_type="supporting_document",
				filename="malware.exe",
				content_b64=base64.b64encode(b"MZ").decode("ascii"),
				content_type="application/octet-stream",
			)
		with self.assertRaises(frappe.ValidationError):
			upload_evidence(
				self.ref,
				title="Empty",
				evidence_type="supporting_document",
				filename="empty.pdf",
				content_b64=base64.b64encode(b"").decode("ascii"),
				content_type="application/pdf",
			)

	def test_upload_replace_versions(self):
		first = upload_evidence(
			self.ref,
			title="Tax clearance",
			evidence_type="certificate",
			filename="tax-v1.pdf",
			content_b64=_pdf_b64(),
			content_type="application/pdf",
			metadata={
				"issuer": "KRA",
				"reference_number": "TC-1",
				"issue_date": "2026-01-01",
				"expiry_or_validity": "2026-12-31",
				"language": "en",
			},
		)
		eid = first["item"]["evidence_id"]
		self.assertEqual(first["item"]["status"], EVIDENCE_STATUS_CURRENT)
		self.assertEqual(int(first["item"]["version"]), 1)

		second = replace_evidence(
			self.ref,
			evidence_id=eid,
			filename="tax-v2.pdf",
			content_b64=_pdf_b64(80),
			content_type="application/pdf",
		)
		self.assertEqual(second["item"]["evidence_id"], eid)
		self.assertEqual(int(second["item"]["version"]), 2)
		reg = get_evidence_register(self.ref)
		versions = [i for i in reg["items"] if i["evidence_id"] == eid or i.get("superseded_by") == eid]
		# Current v2 + superseded v1 share family via evidence_id lineage.
		current = [i for i in reg["items"] if i["evidence_id"] == eid and i["status"] == EVIDENCE_STATUS_CURRENT]
		superseded = [i for i in reg["items"] if i.get("status") == EVIDENCE_STATUS_SUPERSEDED]
		self.assertEqual(len(current), 1)
		self.assertEqual(int(current[0]["version"]), 2)
		self.assertTrue(superseded)

		snap = freeze_evidence_for_seal(resolve_published_tender_backend(self.ref)["bid_id"])
		self.assertTrue(snap.get("versions"))
		self.assertIn(eid, {v.get("evidence_id") for v in snap["versions"]})

	def test_evidence_reuse_across_obligations(self):
		up = upload_evidence(
			self.ref,
			title="Audited accounts",
			evidence_type="supporting_document",
			filename="accounts.pdf",
			content_b64=_pdf_b64(),
			content_type="application/pdf",
		)
		eid = up["item"]["evidence_id"]
		link_evidence(
			self.ref,
			evidence_id=eid,
			target_kind="obligation",
			target_key="IT-BSO-PRE-001",
		)
		link_evidence(
			self.ref,
			evidence_id=eid,
			target_kind="obligation",
			target_key="IT-BSO-QUAL-001",
		)
		reg = get_evidence_register(self.ref)
		item = next(i for i in reg["items"] if i["evidence_id"] == eid)
		keys = {cstr(l.get("target_key")) for l in (item.get("links") or [])}
		self.assertEqual(keys, {"IT-BSO-PRE-001", "IT-BSO-QUAL-001"})

	def test_required_metadata_marks_missing(self):
		up = upload_evidence(
			self.ref,
			title="Certificate without meta",
			evidence_type="certificate",
			filename="cert.pdf",
			content_b64=_pdf_b64(),
			content_type="application/pdf",
			metadata={},
		)
		self.assertEqual(up["item"]["status"], EVIDENCE_STATUS_MISSING_METADATA)
		issues = get_issue_register(self.ref)
		codes = {cstr(i.get("code")) for i in (issues.get("issues") or [])}
		self.assertIn("evidence_missing_metadata", codes)

	def test_cross_bidder_denial(self):
		up = upload_evidence(
			self.ref,
			title="Owned evidence",
			evidence_type="supporting_document",
			filename="owned.pdf",
			content_b64=_pdf_b64(),
			content_type="application/pdf",
		)
		eid = up["item"]["evidence_id"]
		bid_a = resolve_published_tender_backend(self.ref)["bid_id"]
		email = "x100.bidder.b@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "X100",
					"last_name": "BidderB",
					"send_welcome_email": 0,
					"user_type": "Website User",
				}
			)
			user.insert(ignore_permissions=True)
			user.new_password = "X100BidderB1!"
			user.save(ignore_permissions=True)
		frappe.set_user(email)
		reg_b = get_evidence_register(self.ref)
		self.assertEqual(reg_b.get("items") or [], [])
		with self.assertRaises(frappe.PermissionError):
			link_evidence(
				self.ref,
				evidence_id=eid,
				target_kind="obligation",
				target_key="IT-BSO-PRE-001",
			)
		with self.assertRaises(frappe.PermissionError):
			_get_bid(bid_a)

	def test_server_derived_issues_and_correction_routes(self):
		upload_evidence(
			self.ref,
			title="Cert incomplete",
			evidence_type="certificate",
			filename="cert2.pdf",
			content_b64=_pdf_b64(),
			content_type="application/pdf",
		)
		reg = get_issue_register(self.ref)
		self.assertTrue(reg.get("issues"))
		for issue in reg["issues"]:
			self.assertIn(issue.get("severity"), ("blocker", "warning", "information"))
			self.assertTrue(issue.get("code"))
			self.assertTrue(issue.get("message"))
			self.assertTrue(cstr(issue.get("correction_route") or "").startswith("/tenders/"))
			self.assertNotIn("configuration_id=", cstr(issue.get("correction_route")))
		# Client cannot clear authoritative blockers.
		with self.assertRaises(frappe.PermissionError):
			clear_issue_blockers_denied(self.ref)
		sample = issue_item(
			code="demo",
			severity=SEVERITY_BLOCKER,
			message="Demo",
			correction_route=f"/tenders/{self.ref}/evidence",
		)
		self.assertEqual(sample["severity"], SEVERITY_BLOCKER)
		self.assertEqual(sample["resolved"], 0)

	def test_bidder_dto_presentation_boundary(self):
		upload_evidence(
			self.ref,
			title="Safe dto",
			evidence_type="supporting_document",
			filename="safe.pdf",
			content_b64=_pdf_b64(),
			content_type="application/pdf",
		)
		ev = get_evidence_register(self.ref)
		iss = get_issue_register(self.ref)
		for label, payload in (("evidence", ev), ("issues", iss)):
			violations = assert_no_forbidden_bidder_keys(payload)
			self.assertFalse(violations, f"{label}: {violations}")
			hits = scan_bidder_presentation_text(dto_as_scan_text(payload), include_hex_digests=True)
			self.assertFalse(hits, f"{label}: {hits}")
			blob = dto_as_scan_text(payload)
			self.assertNotIn("file_id", blob)
			self.assertNotIn("configuration_id", blob)


class TestLeanX100EvidenceAndIssuesWeb(IntegrationTestCase):
	def setUp(self):
		clear_website_cache()
		frappe.set_user("Administrator")
		self.cfg_id, self.pub_id, self.ref = _prep_and_publish()

	def tearDown(self):
		if hasattr(frappe.local, "request"):
			delattr(frappe.local, "request")
		frappe.set_user("Administrator")

	def _get(self, path: str):
		set_request(method="GET", path=path)
		return get_response()

	def test_evidence_and_issues_pages_render(self):
		for path, testid, title in (
			(f"/tenders/{self.ref}/evidence", "kt-x100-evidence-root", "Evidence Register"),
			(f"/tenders/{self.ref}/issues", "kt-x100-issues-root", "Issues"),
		):
			resp = self._get(path)
			self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
			body = frappe.safe_decode(resp.get_data())
			self.assertIn(f'data-testid="{testid}"', body)
			self.assertIn(title, body)
			self.assertIn('data-testid="kt-a2-nav-evidence"', body)
			self.assertIn('data-testid="kt-a2-nav-issues"', body)
			# Not checklist progress rows
			self.assertNotIn("Evidence Register</td>", body)
			hits = scan_bidder_presentation_text(body, include_hex_digests=False)
			self.assertFalse(hits, hits)
			self.assertNotIn("configuration_id=", body)


if __name__ == "__main__":
	unittest.main()
