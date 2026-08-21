from __future__ import annotations

import hashlib
import io
import zipfile
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from werkzeug.datastructures import FileStorage

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import OU, PE, PLANNER, REQUESTER, upsert_departmental_needs
from kentender_procurement.departmental_needs.services.attachments import (
	download_attachment,
	list_attachments,
	mark_attachment_scanned,
	remove_attachment,
	upload_attachment,
)
from kentender_procurement.departmental_needs.services.lifecycle import create_need, submit_need

def _minimal_pdf_bytes() -> bytes:
	"""A structurally valid minimal PDF with a real, byte-accurate xref table —
	Frappe's own File controller runs a real pypdf-based content scan on
	upload, so a fake/truncated PDF byte string is rejected before this
	module's own code ever runs."""
	objects = [
		b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
		b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
		b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n",
	]
	header = b"%PDF-1.4\n"
	body = b""
	offsets = [0]
	for obj in objects:
		offsets.append(len(header) + len(body))
		body += obj
	xref_offset = len(header) + len(body)
	xref = b"xref\n0 4\n0000000000 65535 f \n"
	for off in offsets[1:]:
		xref += f"{off:010d} 00000 n \n".encode()
	trailer = f"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
	return header + body + xref + trailer


PDF_BYTES = _minimal_pdf_bytes()
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
EXE_BYTES = b"MZ" + b"\x00" * 32


def _minimal_docx_bytes() -> bytes:
	buf = io.BytesIO()
	with zipfile.ZipFile(buf, "w") as archive:
		archive.writestr(
			"[Content_Types].xml",
			'<?xml version="1.0"?><Types><Override PartName="/word/document.xml" '
			'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
		)
		archive.writestr("word/document.xml", "<document/>")
	return buf.getvalue()


class TestDepartmentalNeedsAttachments(IntegrationTestCase):
	"""NDS-CHG-002 §3.3 supporting documents (Phase 4)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def _key(self, label: str) -> str:
		return f"TEST-NDS-ATT-{label}-{uuid4().hex}"

	def _current_fy(self):
		return next(row for row in enabled_fiscal_years() if row["is_current"])

	def _draft(self):
		fy = self._current_fy()
		return create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Attachment need {uuid4().hex[:8]}", idempotency_key=self._key("CREATE"), user=REQUESTER,
		)

	def _upload(self, need_result, *, filename="doc.pdf", content=PDF_BYTES, content_type="application/pdf", label="UPLOAD"):
		frappe.local.request = frappe._dict(files={"file": FileStorage(stream=io.BytesIO(content), filename=filename, content_type=content_type)})
		try:
			return upload_attachment(
				need=need_result["need"], expected_token=need_result["concurrency_token"],
				idempotency_key=self._key(label), user=REQUESTER,
			)
		finally:
			frappe.local.request = None

	def test_upload_pdf_succeeds_and_stores_metadata(self):
		need = self._draft()
		result = self._upload(need)
		self.assertTrue(result["ok"])
		self.assertEqual(result["mime_type"], "application/pdf")
		self.assertEqual(result["scan_status"], "Pending")
		att = frappe.get_doc("Departmental Need Attachment", result["attachment"])
		self.assertEqual(att.sha256_digest, hashlib.sha256(PDF_BYTES).hexdigest())
		self.assertEqual(att.file_size, len(PDF_BYTES))
		self.assertTrue(att.is_active)
		self.assertTrue(frappe.db.exists("File", {"file_url": att.file}))

	def test_upload_docx_succeeds_via_content_types_manifest(self):
		need = self._draft()
		content = _minimal_docx_bytes()
		result = self._upload(need, filename="plan.docx", content=content, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
		self.assertTrue(result["ok"])
		self.assertEqual(result["mime_type"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

	def test_upload_rejects_disallowed_extension(self):
		need = self._draft()
		with self.assertRaises(DepartmentalNeedError):
			self._upload(need, filename="malware.exe", content=EXE_BYTES, content_type="application/octet-stream")

	def test_upload_rejects_signature_mismatch(self):
		need = self._draft()
		with self.assertRaises(DepartmentalNeedError):
			self._upload(need, filename="fake.pdf", content=PNG_BYTES, content_type="application/pdf")

	def test_upload_rejects_oversized_file(self):
		need = self._draft()
		oversized = PDF_BYTES + (b"0" * (20 * 1024 * 1024 + 1))
		with self.assertRaises(DepartmentalNeedError):
			self._upload(need, content=oversized)

	def test_upload_enforces_ten_active_file_limit(self):
		need = self._draft()
		for i in range(10):
			self._upload(need, filename=f"doc{i}.pdf", label=f"LIMIT-{i}")
		with self.assertRaises(DepartmentalNeedError):
			self._upload(need, filename="doc11.pdf", label="LIMIT-11")

	def test_upload_blocked_once_need_is_submitted(self):
		need = self._draft()
		from kentender_procurement.departmental_needs.services.lifecycle import update_need
		update_need(
			need=need["need"], title="Attachment lock need", business_justification="A justification long enough to satisfy the fifty character minimum here.",
			required_by_date=self._current_fy()["end_date"], delivery_or_use_location="MOH",
			items=[{"description": "Item", "indicative_quantity": 1, "unit_code": "Each"}],
			expected_token=need["concurrency_token"], idempotency_key=self._key("UPDATE"), user=REQUESTER,
		)
		fresh = frappe.db.get_value("Departmental Need", need["need"], "concurrency_token")
		submit_need(need=need["need"], expected_token=fresh, idempotency_key=self._key("SUBMIT"), user=REQUESTER)
		fresh2 = frappe.db.get_value("Departmental Need", need["need"], "concurrency_token")
		with self.assertRaises(DepartmentalNeedError):
			self._upload({"need": need["need"], "concurrency_token": fresh2}, label="LOCKED")

	def test_quarantine_blocks_submission_but_not_draft(self):
		need = self._draft()
		from kentender_procurement.departmental_needs.services.lifecycle import update_need
		att = self._upload(need)
		fresh = frappe.db.get_value("Departmental Need", need["need"], "concurrency_token")
		updated = update_need(
			need=need["need"], title="Quarantine need", business_justification="A justification long enough to satisfy the fifty character minimum here.",
			required_by_date=self._current_fy()["end_date"], delivery_or_use_location="MOH",
			items=[{"description": "Item", "indicative_quantity": 1, "unit_code": "Each"}],
			expected_token=fresh, idempotency_key=self._key("UPDATE"), user=REQUESTER,
		)
		with self.assertRaises(DepartmentalNeedError):
			submit_need(need=need["need"], expected_token=updated["concurrency_token"], idempotency_key=self._key("SUBMIT-BLOCKED"), user=REQUESTER)
		mark_attachment_scanned(attachment=att["attachment"], clean=True)
		submitted = submit_need(need=need["need"], expected_token=updated["concurrency_token"], idempotency_key=self._key("SUBMIT-OK"), user=REQUESTER)
		self.assertTrue(submitted["ok"])

	def test_remove_attachment_is_logical_delete_not_hard_delete(self):
		need = self._draft()
		att = self._upload(need)
		fresh = frappe.db.get_value("Departmental Need", need["need"], "concurrency_token")
		result = remove_attachment(
			need=need["need"], attachment=att["attachment"], expected_token=fresh,
			idempotency_key=self._key("REMOVE"), reason="No longer needed", user=REQUESTER,
		)
		self.assertFalse(result["is_active"])
		row = frappe.get_doc("Departmental Need Attachment", att["attachment"])
		self.assertFalse(row.is_active)
		self.assertEqual(row.removed_by, REQUESTER)
		self.assertIsNotNone(row.removed_at)

	def test_remove_attachment_blocked_once_need_is_submitted(self):
		need = self._draft()
		att = self._upload(need)
		from kentender_procurement.departmental_needs.services.lifecycle import update_need
		fresh = frappe.db.get_value("Departmental Need", need["need"], "concurrency_token")
		updated = update_need(
			need=need["need"], title="Remove lock need", business_justification="A justification long enough to satisfy the fifty character minimum here.",
			required_by_date=self._current_fy()["end_date"], delivery_or_use_location="MOH",
			items=[{"description": "Item", "indicative_quantity": 1, "unit_code": "Each"}],
			expected_token=fresh, idempotency_key=self._key("UPDATE"), user=REQUESTER,
		)
		mark_attachment_scanned(attachment=att["attachment"], clean=True)
		submitted = submit_need(need=need["need"], expected_token=updated["concurrency_token"], idempotency_key=self._key("SUBMIT"), user=REQUESTER)
		with self.assertRaises(DepartmentalNeedError):
			remove_attachment(
				need=need["need"], attachment=att["attachment"], expected_token=submitted["concurrency_token"],
				idempotency_key=self._key("REMOVE-BLOCKED"), user=REQUESTER,
			)

	def test_download_requires_clean_and_active(self):
		need = self._draft()
		att = self._upload(need)
		with self.assertRaises(DepartmentalNeedError):
			download_attachment(need=need["need"], attachment=att["attachment"], user=REQUESTER)
		mark_attachment_scanned(attachment=att["attachment"], clean=True)
		frappe.local.response = frappe._dict()
		download_attachment(need=need["need"], attachment=att["attachment"], user=REQUESTER)
		self.assertEqual(frappe.local.response.filecontent, PDF_BYTES)
		self.assertEqual(frappe.local.response.filename, "doc.pdf")

	def test_download_denied_to_unauthorized_user(self):
		need = self._draft()
		att = self._upload(need)
		mark_attachment_scanned(attachment=att["attachment"], clean=True)
		with self.assertRaises(DepartmentalNeedError):
			download_attachment(need=need["need"], attachment=att["attachment"], user=PLANNER)

	def test_list_attachments_only_shows_active(self):
		need = self._draft()
		att1 = self._upload(need, filename="one.pdf", label="LIST-1")
		self._upload(need, filename="two.pdf", label="LIST-2")
		fresh = frappe.db.get_value("Departmental Need", need["need"], "concurrency_token")
		remove_attachment(need=need["need"], attachment=att1["attachment"], expected_token=fresh, idempotency_key=self._key("REMOVE"), user=REQUESTER)
		rows = list_attachments(need=need["need"], user=REQUESTER)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].original_filename, "two.pdf")
