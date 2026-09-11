# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §5.10/D14 — supporting-material file checks."""

from __future__ import annotations

import base64

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import files
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError

# A minimal, genuinely valid one-pixel PNG.
_ONE_PIXEL_PNG = base64.b64decode(
	"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
_MINIMAL_PDF = (
	b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n"
	b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page "
	b"/Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\nxref\n0 4\n"
	b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
	b"0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n186\n%%EOF"
)  # a genuinely valid single-page PDF (correct xref/trailer) — Frappe's own
# File.check_content() parses every uploaded PDF with pypdf and rejects one
# that doesn't parse, before this module's own check_file() ever runs.


class TestFileChecks(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._created: list[str] = []

	def tearDown(self):
		for name in self._created:
			if frappe.db.exists("File", name):
				frappe.delete_doc("File", name, force=1, ignore_permissions=True)

	def _make_file(self, filename: str, content: bytes) -> str:
		doc = frappe.get_doc(
			{"doctype": "File", "file_name": filename, "content": content, "is_private": 1}
		).insert(ignore_permissions=True)
		self._created.append(doc.name)
		return doc.name

	def test_a_valid_pdf_passes_with_a_digest(self):
		name = self._make_file("spec.pdf", _MINIMAL_PDF)
		result = files.check_file(name)
		self.assertEqual(len(result["digest"]), 64)
		self.assertEqual(result["check_result"], "Not scanned — no scanner configured")

	def test_a_valid_png_passes(self):
		name = self._make_file("photo.png", _ONE_PIXEL_PNG)
		result = files.check_file(name)
		self.assertEqual(len(result["digest"]), 64)

	def test_a_disallowed_extension_is_rejected(self):
		name = self._make_file("spec.exe", _MINIMAL_PDF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			files.check_file(name)
		self.assertEqual(ctx.exception.code, "REQ_FILE_INVALID")

	def test_content_not_matching_the_declared_extension_is_rejected(self):
		# A real Frappe `File.insert()` for "spec.pdf" containing PNG bytes
		# never reaches this module's own check: Frappe's own `check_content()`
		# already tries to pypdf-parse it by the (wrong) declared extension and
		# raises first. The sniffing logic itself is tested directly instead —
		# pure, no DB, exactly the check `check_file` runs after a real insert
		# has already succeeded (e.g. a correctly-named .png containing PDF bytes,
		# which Frappe's own PDF-only guard does not intercept).
		name = self._make_file("spec.png", _MINIMAL_PDF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			files.check_file(name)
		self.assertEqual(ctx.exception.code, "REQ_FILE_INVALID")

	def test_scanner_hook_absence_is_reported_visibly_not_silently_clean(self):
		name = self._make_file("spec.pdf", _MINIMAL_PDF)
		result = files.check_file(name)
		self.assertIn("no scanner configured", result["check_result"])
