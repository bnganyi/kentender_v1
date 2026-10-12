# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release 1.5 of IT-EQUIPMENT-OPEN-V1 makes the bidder's tender-security evidence follow the Tender's own submission method
(Project Owner, 10 October 2026), through two named applicability rules, never through a different renderer:

| Submission method                          | Response behaviour                                                     |
| Bidder uploads an electronic instrument    | the details and the instrument attachment are required                 |
| Issuer supplies the instrument directly    | the details are required, no instrument attachment (no duplicate)      |
| Paper instrument requiring an original     | the details and the prescribed electronic copy are required            |
| (the Tender states none, or no security)   | earlier behaviour: upload group; or no security group at all           |
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler import assets as release_assets
from kentender_procurement.std_templates.compiler.definition import compile_published_bid_definition
from kentender_procurement.std_templates.renderers import registry

PACK = Path(__file__).resolve().parents[4] / "docs" / "mvp-1-r1" / "07_tender_templates" / "it_equipment_open_v1"
UPLOAD, ISSUER, PAPER = "Bidder uploads an electronic instrument", "Issuer supplies the instrument directly", "Paper instrument requiring an original"
UPLOAD_RULE, ISSUER_RULE = "RR-TENDER-SECURITY", "RR-TENDER-SECURITY-ISSUER"


def compile_with(**security):
	manifest = json.loads((PACK / "06_runtime/release_manifest.json").read_text(encoding="utf-8"))
	files = {name: (PACK / rel).read_bytes() for name, rel in release_assets.ASSET_FILES.items()}
	assets = release_assets.load(files, official_source_digest=manifest["official_source_digest"], bundle_digest=manifest["bundle_digest"])
	projection = json.loads((PACK / "04_fixture/moh_input.json").read_text(encoding="utf-8"))
	projection = copy.deepcopy(projection)
	projection["tender"]["tender_security"] = {**{k: v for k, v in projection["tender"]["tender_security"].items() if k in ("amount", "currency", "required")}, **security}
	caps = registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", "1.2.0")
	return compile_published_bid_definition(assets, projection, renderer_capabilities=caps)


def security_groups(definition):
	out = {}
	for section in definition["sections"]:
		for group in section["groups"]:
			if group["rule_id"] in (UPLOAD_RULE, ISSUER_RULE):
				rows = {r["response_id"]: r for r in definition["response_rows"]}
				out[group["rule_id"]] = [rows[i]["field"]["field_key"] for i in group["response_ids"]]
	return out


class TestRelease15Security(IntegrationTestCase):
	def test_the_release_is_1_5(self):
		self.assertEqual(compile_with(required=True)["template_release_id"][:5], "stdr-")
		manifest = json.loads((PACK / "06_runtime/release_manifest.json").read_text(encoding="utf-8"))
		self.assertEqual(manifest["template_release"], "1.5")

	def test_an_uploaded_instrument_requires_the_attachment(self):
		groups = security_groups(compile_with(required=True, submission_method=UPLOAD, original_delivery="Required"))
		self.assertEqual(list(groups), [UPLOAD_RULE])
		self.assertIn("security_evidence", groups[UPLOAD_RULE])

	def test_an_issuer_supplied_instrument_has_no_bidder_upload(self):
		groups = security_groups(compile_with(required=True, submission_method=ISSUER, original_delivery="Not required"))
		self.assertEqual(list(groups), [ISSUER_RULE])
		self.assertNotIn("security_evidence", groups[ISSUER_RULE])
		self.assertEqual(set(groups[ISSUER_RULE]), {"security_form", "issuer", "guarantee_reference", "instrument_amount", "bank_guarantee_valid_until", "insurance_guarantee_valid_until"})

	def test_a_paper_instrument_requires_the_prescribed_electronic_copy(self):
		groups = security_groups(compile_with(required=True, submission_method=PAPER, original_delivery="Required"))
		self.assertEqual(list(groups), [UPLOAD_RULE])
		self.assertIn("security_evidence", groups[UPLOAD_RULE])

	def test_a_projection_that_states_no_method_keeps_the_upload_behaviour(self):
		groups = security_groups(compile_with(required=True))
		self.assertEqual(list(groups), [UPLOAD_RULE])

	def test_no_security_required_hides_every_security_input_and_the_upload(self):
		self.assertEqual(security_groups(compile_with(required=False)), {})

	def test_the_issuer_group_is_a_distinct_identity_so_a_method_change_is_classified_not_guessed(self):
		upload, issuer = compile_with(required=True, submission_method=UPLOAD), compile_with(required=True, submission_method=ISSUER)
		stable = lambda d, rule: {r["stable_key"] for r in d["response_rows"] if r["identity"]["rule_id"] == rule} if "rule_id" in next(iter(d["response_rows"]))["identity"] else set()  # noqa: E731
		upload_keys = {r["stable_key"] for r in upload["response_rows"]}
		issuer_keys = {r["stable_key"] for r in issuer["response_rows"]}
		self.assertTrue(upload_keys - issuer_keys, "the upload group's rows are removed by the change")
		self.assertTrue(issuer_keys - upload_keys, "the issuer group's rows are new")
