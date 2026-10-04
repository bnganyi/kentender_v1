"""Curation CLI adapter over the shared `CompilePublishedBidDefinition`
(STD-TPL-001 v0.10 §13.7; STD-TPL-IMP-001 v1.0 §7).

Loads the four runtime assets and one `TenderVersionProjection v1` input from
files, then calls the exact compiler the production Tenders service calls and
writes the canonical Published Bid Definition. It contains no compilation
logic of its own and is never called in production.

    python 04_fixture/build_definition_fixture.py \
      --input 04_fixture/moh_input.json \
      --runtime-dir 06_runtime \
      --output 06_runtime/moh_published_bid_definition_expected.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
APP_ROOT = Path(os.environ.get("KENTENDER_PROCUREMENT_APP", PACK.parents[3] / "kentender_procurement"))
sys.path.insert(0, str(APP_ROOT))

from kentender_procurement.std_templates.compiler import assets as release_assets  # noqa: E402
from kentender_procurement.std_templates.compiler.canonical import pretty_json  # noqa: E402
from kentender_procurement.std_templates.compiler.definition import compile_published_bid_definition  # noqa: E402
from kentender_procurement.std_templates.compiler.errors import STDTemplateError  # noqa: E402
from kentender_procurement.std_templates.release import bundle  # noqa: E402
from kentender_procurement.std_templates.renderers import registry  # noqa: E402


def load_assets(runtime_dir: Path) -> release_assets.ReleaseAssets:
	files = {name: (runtime_dir / Path(rel).name).read_bytes() for name, rel in release_assets.ASSET_FILES.items()}
	return release_assets.load(
		files,
		official_source_digest=bundle.file_digest(PACK / "01_source/ppra_goods_std_official.pdf"),
		bundle_digest=bundle.candidate_bundle_digest(PACK),
	)


def build(input_path: Path, runtime_dir: Path) -> dict:
	assets = load_assets(runtime_dir)
	env = assets.envelope
	capabilities = registry.bid_workspace_capabilities(env["renderer_profile_id"], env["supported_renderer_version"])
	projection = json.loads(input_path.read_text(encoding="utf-8"))
	return compile_published_bid_definition(assets, projection, renderer_capabilities=capabilities)


def variant_summary(input_path: Path, runtime_dir: Path, *, release_status: str, incomplete_reason: str) -> dict:
	"""The §13.7 reservation-variant expectation: document anchors, response
	rules, evidence requirements, eligibility mappings, award/reporting
	treatment and the construction result, all taken from the one compiler."""
	summary = {
		"schema_version": 1,
		"input": input_path.name,
		"release_status": release_status,
		"incomplete_reason": incomplete_reason,
	}
	try:
		definition = build(input_path, runtime_dir)
	except STDTemplateError as exc:
		summary.update(
			{
				"expected_result": "Blocking",
				"expected_error": {"code": exc.code, "identity": exc.identity},
				"definition_digest": None,
				"reservation_treatment": None,
				"response_rule_ids": [],
				"reservation_document_anchors": [],
				"reservation_evidence_requirements": [],
				"eligibility_mappings": [],
			}
		)
		return summary
	reservation_rules = {m["response_rule_id"] for m in definition["evaluation_mappings"]} & {"RR-RESERVATION"}
	rows = [r for r in definition["response_rows"] if r["identity"]["source_family"] in ("reservation", "county_residents")]
	summary.update(
		{
			"expected_result": "Publishable",
			"expected_error": None,
			"definition_digest": definition["definition_digest"],
			"reservation_treatment": definition["reservation_treatment"],
			"response_rule_ids": sorted({m["response_rule_id"] for m in definition["evaluation_mappings"]}),
			"reservation_document_anchors": sorted({r["document_anchor"] for r in rows}),
			"reservation_evidence_requirements": [
				{"field_key": r["field"]["field_key"], "evidence_type": r["evidence"]["evidence_type"], "mandatory": r["evidence"]["mandatory"]}
				for r in rows
				if r["evidence"]
			],
			"eligibility_mappings": [
				{"mapping_id": m["mapping_id"], "evaluation_treatment": m["evaluation_treatment"], "evaluation_group_id": m["evaluation_group_id"]}
				for m in definition["evaluation_mappings"]
				if m["response_rule_id"] in reservation_rules
			],
		}
	)
	return summary


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
	parser.add_argument("--input", required=True)
	parser.add_argument("--runtime-dir", required=True)
	parser.add_argument("--output", required=True)
	parser.add_argument("--variant-summary", action="store_true", help="write a reservation-variant expectation instead of a definition")
	parser.add_argument("--release-status", default="Complete", choices=("Complete", "Incomplete"))
	parser.add_argument("--incomplete-reason", default="")
	args = parser.parse_args(argv)
	if args.variant_summary:
		summary = variant_summary(Path(args.input), Path(args.runtime_dir), release_status=args.release_status, incomplete_reason=args.incomplete_reason)
		Path(args.output).write_text(pretty_json(summary), encoding="utf-8", newline="\n")
		print(f"wrote {args.output} ({summary['expected_result']})")
		return 0
	try:
		definition = build(Path(args.input), Path(args.runtime_dir))
	except STDTemplateError as exc:
		print(f"{exc.code}: {exc.message} [{exc.identity}]", file=sys.stderr)
		return 1
	Path(args.output).write_text(pretty_json(definition), encoding="utf-8", newline="\n")
	print(f"wrote {args.output} ({len(definition['response_rows'])} responses, digest {definition['definition_digest']})")
	return 0


if __name__ == "__main__":
	sys.exit(main())
