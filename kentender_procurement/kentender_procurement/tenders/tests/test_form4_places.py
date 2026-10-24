# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The declared places of Form No. 4, release 1.5 (CM-CHG-001 v0.11 section 19.4; CM-TPL-01; FU-CM-70). Pure text: no site is touched.

`ISSUED` is the Form No. 4 that release 1.5 issued for the canonical world's Year 0 workstations tender, as the issued tender document holds it."""

import re
import unittest

from kentender_procurement.tenders.services import form4_places as places

ISSUED = '<h3>Form No. 4 - Contract Agreement</h3>\n<p><em>To be completed by the successful Tenderer after contract award, in accordance with the instructions indicated.</em></p>\n<p>THIS AGREEMENT made the _______________________ day of _______________________, _______________________. BETWEEN (1) Ministry of Health, having its principal place of business at Afya House, Cathedral Road, Nairobi (hereinafter called &ldquo;the Procuring Entity&rdquo;), of the one part; and (2) _______________________, a corporation incorporated under the laws of _______________________ and having its principal place of business at _______________________ (hereinafter called &ldquo;the Supplier&rdquo;), of the other part.</p>\n<ol>\n  <li>WHEREAS the Procuring Entity invited Tenders for certain Goods and ancillary services, viz. Supply of staff workstation computers (TND-MOH-2025-001), and has accepted a Tender by the Supplier for the supply of those Goods and Services, the Procuring Entity and the Supplier agree as follows:\n    <ol type="i">\n      <li>In this Agreement words and expressions shall have the same meanings as are respectively assigned to them in the Contract documents referred to.</li>\n      <li>The following documents shall be deemed to form and be read and construed as part of this Agreement. This Agreement shall prevail over all other contract documents.\n        <ul>\n          <li>a) the Letter of Acceptance</li>\n          <li>b) the Letter of Tender</li>\n          <li>c) the Addenda Nos. _______________________ (if any)</li>\n          <li>d) Special Conditions of Contract</li>\n          <li>e) General Conditions of Contract</li>\n          <li>f) the Specification (including Schedule of Requirements and Technical Specifications)</li>\n          <li>g) the completed Schedules (including Price Schedules)</li>\n          <li>h) any other document listed in the GCC as forming part of the Contract</li>\n        </ul>\n      </li>\n      <li>In consideration of the payments to be made by the Procuring Entity to the Supplier as specified in this Agreement, the Supplier hereby covenants with the Procuring Entity to provide the Goods and Services and to remedy defects therein in conformity in all respects with the provisions of the Contract.</li>\n    </ol>\n  </li>\n  <li>The Procuring Entity hereby covenants to pay the Supplier in consideration of the provision of the Goods and Services and the remedying of defects therein, the Contract Price or such other sum as may become payable under the provisions of the Contract at the times and in the manner prescribed by the Contract.</li>\n  <li>IN WITNESS whereof the parties hereto have caused this Agreement to be executed in accordance with the laws of Kenya on the day, month and year indicated above.</li>\n</ol>\n<p>SIGNED ON _______________________ on behalf of Ministry of Health</p>\n<p>By _______________________ in the capacity of _______________________</p>\n<p>In the presence of _______________________</p>\n<p>SIGNED ON _______________________ on behalf of the Supplier</p>\n<p>By _______________________ in the capacity of _______________________</p>\n<p>In the presence of _______________________</p>\n\n\n'

PLACES = ["agreement_day", "agreement_month", "agreement_year", "entity_name", "entity_address", "supplier_name", "supplier_country", "supplier_address", "goods", "addenda", "entity_signatory",
	"entity_capacity", "supplier_signatory", "supplier_capacity"]


class TestForm4Places(unittest.TestCase):
	def test_release_1_5_declares_every_place_the_agreement_fills_and_changes_no_word(self):
		marked, keys = places.mark(ISSUED, "1.5")
		self.assertEqual(sorted(keys), sorted(PLACES))
		self.assertEqual(places.unmark(marked), ISSUED)  # the issued prose is exactly what it was
		for key in PLACES:
			self.assertEqual(marked.count(f'data-insertion="{key}"'), 1, key)

	def test_each_place_wraps_what_the_form_already_holds_there(self):
		marked, _ = places.mark(ISSUED, "1.5")
		held = dict(re.findall(r'<span data-insertion="([a-z_]+)">(.*?)</span>', marked))
		self.assertEqual(held["entity_name"], "Ministry of Health")
		self.assertEqual(held["entity_address"], "Afya House, Cathedral Road, Nairobi")
		self.assertEqual(held["goods"], "Supply of staff workstation computers (TND-MOH-2025-001)")
		for key in ("agreement_day", "agreement_month", "agreement_year", "supplier_name", "supplier_country", "supplier_address", "addenda", "entity_signatory", "entity_capacity", "supplier_signatory", "supplier_capacity"):
			self.assertRegex(held[key], r"^_+$", key)

	def test_the_blanks_the_agreement_does_not_fill_are_left_alone(self):
		marked, _ = places.mark(ISSUED, "1.5")
		self.assertEqual(marked.count("SIGNED ON _______________________"), 2)  # the signing dates and the witnesses belong to the execution, not to the agreement's particulars
		self.assertEqual(marked.count("In the presence of _______________________"), 2)

	def test_a_form_that_does_not_read_as_reviewed_is_refused_by_the_place_it_misses(self):
		changed = ISSUED.replace("a corporation incorporated under the laws of", "a company incorporated under the laws of")
		with self.assertRaisesRegex(places.Undeclared, "supplier_name"):
			places.mark(changed, "1.5")
		with self.assertRaisesRegex(places.Undeclared, "agreement_day"):
			places.mark(ISSUED.replace("THIS AGREEMENT made", "THIS AGREEMENT is made"), "1.5")

	def test_a_place_found_twice_is_refused(self):
		twice = ISSUED + "<p>THIS AGREEMENT made the _______________________ day of _______________________, _______________________. BETWEEN</p>"
		with self.assertRaisesRegex(places.Undeclared, "2 times"):
			places.mark(twice, "1.5")

	def test_a_release_with_no_declaration_declares_no_place(self):
		self.assertFalse(places.declared("9.9"))
		with self.assertRaisesRegex(places.Undeclared, "template release 9.9"):
			places.mark(ISSUED, "9.9")


class TestAdvanceSentence(unittest.TestCase):
	"""CM-R-18: release 1.5 prints one sentence about an advance, and that sentence is the typed value; anything else gives none."""

	SENTENCE = "No advance payment is offered or payable under this Contract."

	def read(self, html: str, release: str = "1.5", digest: str | None = None):
		import hashlib
		import unittest.mock

		import frappe

		data = html.encode("utf-8")
		document = frappe._dict(html_file="file", digest=digest or hashlib.sha256(data).hexdigest())
		from kentender_procurement.tenders.services import contract_seam

		with unittest.mock.patch.object(contract_seam, "_document", return_value=document), unittest.mock.patch("kentender_core.services.file_integrity.read_bytes", return_value=data):
			return contract_seam._advance("TENDER", release)

	def test_the_sentence_is_the_typed_value_and_names_where_it_was_read(self):
		found = self.read(f"<p>payment within 30 days. {self.SENTENCE} GCC 18.1 A Performance Security is required.</p>")
		self.assertEqual(found["allowed"], False)
		self.assertIn(self.SENTENCE, found["source"])
		self.assertIn("template release 1.5", found["source"])

	def test_no_sentence_or_two_or_a_changed_document_or_another_release_gives_no_value(self):
		self.assertIsNone(self.read("<p>payment within 30 days.</p>"))
		self.assertIsNone(self.read(f"<p>{self.SENTENCE}</p><p>{self.SENTENCE}</p>"))
		self.assertIsNone(self.read(f"<p>{self.SENTENCE}</p>", digest="0" * 64))
		self.assertIsNone(self.read(f"<p>{self.SENTENCE}</p>", release="9.9"))
