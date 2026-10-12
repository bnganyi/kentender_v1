# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-ACCESS-REV-001 AR-15 — a supplier's registration documents are private files.

The upload endpoint reads the browser's multipart request, which a unit test cannot supply cheaply, so
this guards the contract at its source: the one `save_file` call for `KTSM Supplier Document` makes the
file private, as the supplier-accounts module already does."""

from __future__ import annotations

import inspect
import re

from frappe.tests import IntegrationTestCase

from kentender_suppliers.api import smw_public


class TestKtsmDocumentPrivacy(IntegrationTestCase):
	def test_the_registration_document_upload_stores_a_private_file(self):
		source = inspect.getsource(smw_public)
		calls = re.findall(r'save_file\([^)]*"KTSM Supplier Document"[^)]*\)', source)
		self.assertTrue(calls, "the upload call moved; update this guard")
		for call in calls:
			self.assertIn("is_private=1", call, call)
			self.assertNotIn("is_private=0", call, call)
