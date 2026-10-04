# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release 1.4 of IT-EQUIPMENT-OPEN-V1 is frozen (STD-TPL-001 v0.15).

Tenders started on 1.4 keep it for life (no rebind path), so its assets must
keep loading and compiling byte for byte whatever later releases change. The
frozen copies in `vectors/release_1_4/` are the exact 1.4 bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler import assets as release_assets
from kentender_procurement.std_templates.compiler.canonical import pretty_json
from kentender_procurement.std_templates.compiler.definition import compile_published_bid_definition
from kentender_procurement.std_templates.renderers import registry

VECTORS = Path(__file__).resolve().parent / "vectors" / "release_1_4"
EXPECTED = json.loads((VECTORS / "moh_published_bid_definition_expected.json").read_text(encoding="utf-8"))


class TestRelease14Unchanged(IntegrationTestCase):
	def test_the_frozen_release_1_4_still_compiles_byte_for_byte(self):
		files = {name: (VECTORS / Path(rel).name).read_bytes() for name, rel in release_assets.ASSET_FILES.items()}  # exact bytes: the digests bind them
		assets = release_assets.load(files, official_source_digest=EXPECTED["official_source_digest"], bundle_digest=EXPECTED["bundle_digest"])
		self.assertEqual((assets.envelope["template_release"], assets.envelope["supported_renderer_version"]), ("1.4", "1.2.0"))
		projection = json.loads((VECTORS / "moh_input.json").read_text(encoding="utf-8"))
		caps = registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", "1.2.0")
		definition = compile_published_bid_definition(assets, projection, renderer_capabilities=caps)
		self.assertEqual(pretty_json(definition), (VECTORS / "moh_published_bid_definition_expected.json").read_text(encoding="utf-8"))
