# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`kentender_core.services.file_integrity` (TPR-CHG-001 v0.8 plan D10):
media sniffing, size, digest, and the truthful scanner verdict — with a
test double proving the infected path, the clean path and the absent-scanner
path all resolve the way the calling module's own code expects."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import file_integrity



def _image(kind: str) -> bytes:
	"""Frappe's File controller runs every image through Pillow on insert,
	so the fixtures are real 1×1 images, not magic-byte stubs."""
	from io import BytesIO

	from PIL import Image

	buffer = BytesIO()
	Image.new("RGB", (1, 1), (255, 255, 255)).save(buffer, format="PNG" if kind == "png" else "JPEG")
	return buffer.getvalue()


PNG = _image("png")
JPG = _image("jpg")


class _Refused(Exception):
	pass


def _fail(message: str) -> None:
	raise _Refused(message)


def _scanner_infected(*, content: bytes, filename: str) -> str:
	return "Infected: EICAR-Test-File"


def _scanner_clean(*, content: bytes, filename: str) -> str:
	return "Clean — test scanner"


def _hooks_with(scanners: list[str]):
	"""Patch only the scanner hook; every other hook keeps its real value."""
	real = frappe.get_hooks

	def _get_hooks(hook=None, *args, **kwargs):
		if hook == "kt_file_scanners":
			return scanners
		return real(hook, *args, **kwargs)

	return patch.object(frappe, "get_hooks", side_effect=_get_hooks)


class TestFileIntegrity(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._files: list[str] = []

	def tearDown(self):
		for name in self._files:
			if frappe.db.exists("File", name):
				frappe.delete_doc("File", name, force=True, ignore_permissions=True)
		super().tearDown()

	def _file(self, file_name: str, content: bytes) -> str:
		doc = frappe.get_doc({"doctype": "File", "file_name": file_name, "is_private": 1, "content": content}).insert(ignore_permissions=True)
		self._files.append(doc.name)
		return doc.name

	def test_a_valid_png_yields_a_digest_and_the_truthful_not_scanned_verdict(self):
		name = self._file("NB-MOH-2027-033.png", PNG)
		with _hooks_with([]):
			result = file_integrity.check_file(name, fail=_fail)
		self.assertEqual(len(result["digest"]), 64)
		self.assertEqual(result["check_result"], file_integrity.NOT_SCANNED)
		self.assertEqual(result["media_type"], "png")

	def test_an_extension_outside_the_allow_list_is_refused(self):
		name = self._file("PPIP-MOH-2027-035.exe", PNG)
		with self.assertRaises(_Refused) as ctx:
			file_integrity.check_file(name, fail=_fail)
		self.assertIn("not permitted", str(ctx.exception))

	def test_content_that_does_not_match_the_declared_type_is_refused(self):
		# Frappe re-encodes a `.jpg`-named PNG to JPEG on insert but stores a
		# `.png`-named JPEG as-is, so the mismatch fixture is the latter.
		name = self._file("evidence.png", JPG)
		with self.assertRaises(_Refused) as ctx:
			file_integrity.check_file(name, fail=_fail)
		self.assertIn("does not match", str(ctx.exception))

	def test_a_registered_scanner_that_reports_infected_refuses_the_file(self):
		name = self._file("evidence.jpg", JPG)
		with _hooks_with(["kentender_core.tests.test_file_integrity._scanner_infected"]):
			with self.assertRaises(_Refused) as ctx:
				file_integrity.check_file(name, fail=_fail)
		self.assertIn("malware", str(ctx.exception))

	def test_a_registered_scanner_that_reports_clean_is_recorded_verbatim(self):
		name = self._file("evidence.jpg", JPG)
		with _hooks_with(["kentender_core.tests.test_file_integrity._scanner_clean"]):
			result = file_integrity.check_file(name, fail=_fail)
		self.assertEqual(result["check_result"], "Clean — test scanner")

	def test_a_missing_file_is_refused(self):
		with self.assertRaises(_Refused):
			file_integrity.check_file("no-such-file", fail=_fail)
