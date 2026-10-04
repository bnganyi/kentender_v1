"""Rebuild the IT-EQUIPMENT-OPEN-V1 release candidate end to end (release 1.2
from 26 Sep 2026; STD-TPL-001 v0.10 §§13.4–13.9). Curation tooling, outside the pack.

Order matters because every golden vector binds the input bundle digest:

1. render the MoH Invitation and issued Tender (and PDFs with --pdf);
2. compile the MoH Published Bid Definition through the shared compiler;
3. write the five reservation-variant expectations;
4. run `06_runtime/validate_release.py` (writes the validation report, the
   generated change report and the gate results; stops on any Failed check);
5. write `06_runtime/release_manifest.json` and print its digest (its `status` field reads
   `Candidate` as §13.9 defines it; owner decision OD5 makes it evidence only).

    python docs/mvp-1-r1/07_tender_templates/tools/rebuild_release.py [--pdf] \
        [--built-by NAME] [--built-at ISO] [--manifest-only]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[1] / "it_equipment_open_v1"
APP_ROOT = Path(os.environ.get("KENTENDER_PROCUREMENT_APP", PACK.parents[3] / "kentender_procurement"))
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(PACK / "04_fixture"))
sys.path.insert(0, str(PACK / "06_runtime"))

from kentender_procurement.std_templates.compiler import assets as release_assets  # noqa: E402
from kentender_procurement.std_templates.compiler.canonical import pretty_json  # noqa: E402
from kentender_procurement.std_templates.release import bundle, coverage, gates, manifest  # noqa: E402

import build_definition_fixture as cli  # noqa: E402
import validate_release as validator  # noqa: E402


def run(args: list[str]) -> None:
	print("$", " ".join(args))
	subprocess.run([sys.executable] + args, cwd=PACK, check=True)


def build_outputs(pdf: bool) -> None:
	render = ["04_fixture/render_fixture.py", "--input", "04_fixture/moh_input.json", "--output-dir", "04_fixture"]
	if pdf:
		render += ["--renderer-profile", "BDS-GOODS-IT-V1", "--write-pdf"]
	run(render)
	run(["04_fixture/build_definition_fixture.py", "--input", "04_fixture/moh_input.json", "--runtime-dir", "06_runtime", "--output", "06_runtime/moh_published_bid_definition_expected.json"])
	for variant in validator.VARIANTS:
		status, reason = validator.VARIANT_STATUS.get(variant, ("Complete", ""))
		run(
			[
				"04_fixture/build_definition_fixture.py", "--variant-summary", "--release-status", status, "--incomplete-reason", reason,
				"--input", f"04_fixture/reservation_variants/{variant}_input.json", "--runtime-dir", "06_runtime",
				"--output", f"04_fixture/reservation_variants/{variant}_expected.json",
			]
		)


def git_commit() -> str:
	result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PACK, capture_output=True, text=True, check=False)
	return result.stdout.strip() or "unknown"


def build_manifest(built_by: str, built_at: str) -> str:
	report = json.loads((PACK / "05_review/validation_report.json").read_text(encoding="utf-8"))
	if report["summary"]["blocking"]:
		raise SystemExit("validation report has Failed checks; no manifest is created")
	files = {name: (PACK / rel).read_bytes() for name, rel in release_assets.ASSET_FILES.items()}
	profile = json.loads(files["product_profile"])
	rules = json.loads(files["response_rules"])["rules"]
	mappings = json.loads(files["downstream_rules"])["mappings"]
	gates_doc = json.loads((PACK / "05_review/release_gates.json").read_text(encoding="utf-8"))
	gate_rows = gates_doc["gates"]
	_, cov = coverage.read_csv((PACK / "03_registers/coverage_register.csv").read_bytes())
	_, ins = coverage.read_csv((PACK / "03_registers/insertion_points.csv").read_bytes())
	_, forms = coverage.read_csv((PACK / "03_registers/forms_register.csv").read_bytes())
	definition = json.loads((PACK / "06_runtime/moh_published_bid_definition_expected.json").read_text(encoding="utf-8"))
	moh = json.loads((PACK / "04_fixture/moh_input.json").read_text(encoding="utf-8"))
	variants = []
	incomplete = []
	for variant in validator.VARIANTS:
		expected = json.loads((PACK / f"04_fixture/reservation_variants/{variant}_expected.json").read_text(encoding="utf-8"))
		variants.append({"variant": variant, "expected_result": expected["expected_result"], "release_status": expected["release_status"], "reason": expected["incomplete_reason"]})
		if expected["release_status"] != "Complete":
			incomplete.append({"variant": variant, "reason": expected["incomplete_reason"]})
	variants.insert(0, {"variant": "youth (MoH fixture)", "expected_result": "Publishable", "release_status": "Complete", "reason": ""})
	decisions, _ = validator._open_items()
	source_review = next((r for r in gate_rows if r["gate_id"] == "GATE-SOURCE"), None)
	record = (PACK / "01_source/source_record.md").read_text(encoding="utf-8")
	entries = bundle.inventory(PACK)
	sizes = {rel: (PACK / rel).stat().st_size for rel, _ in entries}
	summary = coverage.summary(cov, ins, forms)
	env = {k: profile[k] for k in release_assets.ENVELOPE}
	data = {
		"schema_version": 1,
		"release_id": env["release_id"],
		"template_key": env["template_key"],
		"template_release": env["template_release"],
		"display_name": profile["display_name"],
		"product_profile_id": env["product_profile_id"],
		"renderer_profile_id": env["renderer_profile_id"],
		"supported_renderer_version": env["supported_renderer_version"],
		"status": "Candidate",
		"supported_use": profile["supported_use"],
		"rejected_use": profile["rejected_use"],
		"official_source_title": "PPRA Standard Tender Document for Procurement of Goods",
		"official_source_digest": bundle.file_digest(PACK / "01_source/ppra_goods_std_official.pdf"),
		"source_retrieved_at": "2026-08-28",
		"repository_commit": git_commit(),
		"tool_versions": report["tool_versions"],
		"assets": manifest.asset_rows(entries, sizes),
		"document_summary": manifest.document_summary(summary, ins, forms),
		"response_summary": manifest.response_summary(profile, rules, definition, moh),
		"evaluation_summary": manifest.evaluation_summary(profile, rules, mappings),
		"contract_summary": manifest.contract_summary(profile, mappings),
		"reservation_support": manifest.reservation_support(profile, mappings, variants),
		"verification_results": gates.verification_results(gate_rows),
		"blockers": gates.blockers(gate_rows, decisions, incomplete),
		"source_checked_by": source_review["checked_by"] if source_review else "",
		"source_checked_at": source_review["checked_at"] if source_review else "",
		"source_check_outcome": source_review["result"] if source_review else "Pending",
		"release_gates_digest": bundle.file_digest(PACK / "05_review/release_gates.json"),
		"release_change_report_digest": bundle.file_digest(PACK / "05_review/release_change_report.json"),
		"validation_report_digest": bundle.file_digest(PACK / "05_review/validation_report.json"),
		"bundle_digest": bundle.bundle_digest(entries),
		"built_by": built_by,
		"built_at": built_at,
		"product_profile_digest": bundle.file_digest(PACK / release_assets.ASSET_FILES["product_profile"]),
		"response_rules_digest": bundle.file_digest(PACK / release_assets.ASSET_FILES["response_rules"]),
		"downstream_rules_digest": bundle.file_digest(PACK / release_assets.ASSET_FILES["downstream_rules"]),
		"addendum_identity_rules_digest": bundle.file_digest(PACK / release_assets.ASSET_FILES["addendum_identity_rules"]),
		"input_bundle_digest": bundle.candidate_bundle_digest(PACK),
	}
	assert "Official title" in record
	manifest.validate_shape(data)
	target = PACK / bundle.MANIFEST_PATH
	target.write_text(pretty_json(data), encoding="utf-8", newline="\n")
	digest = bundle.file_digest(target)
	print(f"manifest {bundle.MANIFEST_PATH}: bundle_digest {data['bundle_digest']} manifest_digest {digest}")
	return digest


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
	parser.add_argument("--pdf", action="store_true", help="also regenerate the fixture PDFs")
	parser.add_argument("--built-by", default=os.environ.get("USER", "unknown"))
	parser.add_argument("--built-at", required=True, help="ISO date-time recorded as the manifest build time")
	parser.add_argument("--manifest-only", action="store_true")
	args = parser.parse_args(argv)
	if not args.manifest_only:
		build_outputs(args.pdf)
		result = subprocess.run([sys.executable, "06_runtime/validate_release.py", "--root", ".", "--write-report", "05_review/validation_report.json"], cwd=PACK, check=False)
		if result.returncode != 0:
			print("validator reported a Failed check; stopping before the manifest", file=sys.stderr)
			return result.returncode
	build_manifest(args.built_by, args.built_at)
	return 0


if __name__ == "__main__":
	sys.exit(main())
