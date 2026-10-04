"""Curation-only fixture renderer for IT-EQUIPMENT-OPEN-V1 (STD-TPL-001 v0.10 §13.4).

Reads one `TenderVersionProjection v1` input, derives the document context
through the shared KenTender compiler package, renders both masters with Jinja
auto-escaping and StrictUndefined through the registered document adapter,
and writes only the expected Invitation and issued-Tender HTML (and, with
--write-pdf, their PDFs through the same adapter). It fails on an unknown or
missing value. This file is never imported or installed by KenTender.

    python 04_fixture/render_fixture.py --input 04_fixture/moh_input.json --output-dir 04_fixture
    python 04_fixture/render_fixture.py --input 04_fixture/moh_input.json \
      --output-dir 04_fixture --renderer-profile BDS-GOODS-IT-V1 --write-pdf
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

from kentender_procurement.std_templates.compiler import projection  # noqa: E402
from kentender_procurement.std_templates.compiler.errors import STDTemplateError  # noqa: E402
from kentender_procurement.std_templates.renderers import registry  # noqa: E402
from kentender_procurement.std_templates.renderers.document import INVITATION, ISSUED_TENDER, MASTER_PATHS, PRINT_CSS  # noqa: E402


def output_names(input_path: Path) -> tuple[str, str]:
	stem = input_path.stem[: -len("_input")] if input_path.stem.endswith("_input") else input_path.stem
	return f"{stem}_invitation_expected", f"{stem}_expected"


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
	parser.add_argument("--input", required=True)
	parser.add_argument("--output-dir", required=True)
	parser.add_argument("--renderer-profile")
	parser.add_argument("--write-pdf", action="store_true")
	args = parser.parse_args(argv)

	profile = json.loads((PACK / "06_runtime/product_profile.json").read_text(encoding="utf-8"))
	if args.renderer_profile and args.renderer_profile != profile["renderer_profile_id"]:
		print(f"renderer profile {args.renderer_profile} is not this release's {profile['renderer_profile_id']}", file=sys.stderr)
		return 2
	input_path = Path(args.input)
	data = json.loads(input_path.read_text(encoding="utf-8"))
	try:
		context = projection.document_context(data, profile["document_constants"])
		adapter = registry.document_adapter(profile["renderer_profile_id"], profile["supported_renderer_version"])
		masters = {name: (PACK / rel).read_text(encoding="utf-8") for name, rel in MASTER_PATHS.items()}
		out = adapter.render_html(masters, context)
	except STDTemplateError as exc:
		print(f"{exc.code}: {exc.message} [{exc.identity}]", file=sys.stderr)
		return 1
	if out["problems"]:
		for problem in out["problems"]:
			print(problem, file=sys.stderr)
		return 1
	invitation_name, issued_name = output_names(input_path)
	target = Path(args.output_dir)
	(target / f"{invitation_name}.html").write_text(out["invitation_html"], encoding="utf-8", newline="\n")
	(target / f"{issued_name}.html").write_text(out["issued_tender_html"], encoding="utf-8", newline="\n")
	if args.write_pdf:
		css = masters[PRINT_CSS]
		footer = f"{data['tender']['reference']} — Page [page] of [topage]"
		(target / f"{invitation_name}.pdf").write_bytes(adapter.render_pdf(out["invitation_html"], css))
		(target / f"{issued_name}.pdf").write_bytes(adapter.render_pdf(out["issued_tender_html"], css, footer_center=footer))
	print(f"rendered {invitation_name} and {issued_name}" + (" with PDFs" if args.write_pdf else ""))
	return 0


if __name__ == "__main__":
	sys.exit(main())
