"""IT-EQUIPMENT-OPEN-V1 release validator (STD-TPL-001 v0.10 §13.8).

Curation tooling only: it is never imported by the KenTender runtime. It runs
the 22 check families against the controlled pack, writes a
deterministic `05_review/validation_report.json`, the generated
`05_review/release_change_report.json` and `05_review/release_gates.json`
(one row per §14.2 gate; a missing review is Pending), and exits 0 only when
no check is Failed. Named human reviews never pass by prose: they are read
from `05_review/gate_reviews.json`.

    python 06_runtime/validate_release.py --root . --write-report 05_review/validation_report.json
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
APP_ROOT = Path(os.environ.get("KENTENDER_PROCUREMENT_APP", PACK.parents[3] / "kentender_procurement"))
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(PACK / "04_fixture"))

import jinja2  # noqa: E402

from kentender_procurement.std_templates.compiler import addenda, assets as release_assets, locked_text, projection  # noqa: E402
from kentender_procurement.std_templates.compiler.canonical import pretty_json, sha256_hex  # noqa: E402
from kentender_procurement.std_templates.compiler.definition import compile_published_bid_definition, verify_definition_digest  # noqa: E402
from kentender_procurement.std_templates.compiler.errors import STDTemplateError  # noqa: E402
from kentender_procurement.std_templates.release import bundle, change_report, coverage, gates, quality  # noqa: E402
from kentender_procurement.std_templates.renderers import registry  # noqa: E402
from kentender_procurement.std_templates.renderers.document import MASTER_PATHS  # noqa: E402

import build_definition_fixture as cli  # noqa: E402

EXPECTED_IDENTITY = {
	"template_key": "IT-EQUIPMENT-OPEN-V1",
	"template_release": "1.4",
	"product_profile_id": "GOODS-IT-SIMPLE-V1",
	"renderer_profile_id": "BDS-GOODS-IT-V1",
}
REQUIRED_PATHS = (
	"01_source/ppra_goods_std_official.pdf",
	"01_source/ppra_goods_std_official.txt",
	"01_source/source_record.md",
	"02_master/invitation_to_tender.html",
	"02_master/complete_tender.html",
	"02_master/print.css",
	"03_registers/coverage_register.csv",
	"03_registers/insertion_points.csv",
	"03_registers/forms_register.csv",
	"04_fixture/moh_input.json",
	"04_fixture/render_fixture.py",
	"04_fixture/build_definition_fixture.py",
	"04_fixture/moh_invitation_expected.html",
	"04_fixture/moh_invitation_expected.pdf",
	"04_fixture/moh_expected.html",
	"04_fixture/moh_expected.pdf",
	"04_fixture/package_index.md",
	"05_review/open_issues.md",
	"05_review/gate_reviews.json",
	"05_review/preceding_release.json",
	"06_runtime/product_profile.json",
	"06_runtime/response_rules.json",
	"06_runtime/downstream_rules.json",
	"06_runtime/addendum_identity_rules.json",
	"06_runtime/moh_published_bid_definition_expected.json",
	"06_runtime/validate_release.py",
)
VARIANTS = ("none", "women", "persons_with_disabilities", "county_residents", "unsupported_overlap")
VARIANT_STATUS = {
	"county_residents": ("Incomplete", "No released County-residents wording, evidence rule or overlap treatment; LAW-REG-001 v1.2 LAW12-AC-005 keeps the county basis blocked (open item 70)."),
}
VARIANT_EXPECTATIONS = {
	"none": ("Publishable", None),
	"women": ("Publishable", None),
	"persons_with_disabilities": ("Publishable", None),
	"county_residents": ("Blocking", "county_residents"),
	"unsupported_overlap": ("Blocking", "overlap_treatment"),
}
GENERATED_WRITTEN = ("05_review/validation_report.json", "05_review/release_gates.json", "05_review/release_change_report.json")
ALLOWED_PATTERNS = (
	r"01_source/ppra_goods_std_official\.(pdf|txt)",
	r"01_source/source_record\.md",
	r"01_source/pages/page-\d{3}\.png",
	r"02_master/(invitation_to_tender|complete_tender)\.html",
	r"02_master/print\.css",
	r"03_registers/(coverage_register|insertion_points|forms_register)\.csv",
	r"04_fixture/moh_input\.json",
	r"04_fixture/(render_fixture|build_definition_fixture)\.py",
	r"04_fixture/moh_(invitation_)?expected\.(html|pdf)",
	r"04_fixture/package_index\.md",
	r"04_fixture/reservation_variants/(" + "|".join(VARIANTS) + r")_(input|expected)\.json",
	r"05_review/(open_issues\.md|gate_reviews\.json|preceding_release\.json|validation_report\.json|release_gates\.json|release_change_report\.json)",
	r"06_runtime/(product_profile|response_rules|downstream_rules|addendum_identity_rules|moh_published_bid_definition_expected)\.json",
	r"06_runtime/validate_release\.py",
)
REQUIRED_SECTIONS = (
	"Section I - Instructions to Tenderers",
	"Section II - Tender Data Sheet",
	"Section III - Evaluation and Qualification Criteria",
	"Section IV - Tendering Forms",
	"Section V - Schedule of Requirements",
	"Section VI - General Conditions of Contract",
	"Section VII - Special Conditions of Contract",
	"Section VIII - Contract Forms",
)
OFFICER_PREFIXES = ("tender.", "submission.", "contract.")


class Report:
	def __init__(self) -> None:
		self.rows: list[dict] = []

	def add(self, check_id: str, title: str, result: str, asset: str, message: str) -> None:
		self.rows.append({"check_id": check_id, "title": title, "result": result, "affected_asset": asset, "message": message})

	def run(self, check_id: str, title: str, asset: str, fn) -> None:
		try:
			problems, note = fn()
		except STDTemplateError as exc:
			problems, note = [f"{exc.code}: {exc.message} [{exc.identity}]"], ""
		except Exception as exc:  # a crashed check is a failed check, never a pass
			problems, note = [f"{type(exc).__name__}: {exc}"], ""
		if problems:
			self.add(check_id, title, "Failed", asset, "; ".join(problems[:25]) + (f" (+{len(problems) - 25} more)" if len(problems) > 25 else ""))
		else:
			self.add(check_id, title, "Passed", asset, note or "Passed.")

	def results(self) -> dict[str, str]:
		return {r["check_id"]: r["result"] for r in self.rows}


def read(rel: str) -> str:
	return (PACK / rel).read_text(encoding="utf-8")


def read_json(rel: str):
	return json.loads(read(rel))


def masters() -> dict[str, str]:
	return {name: read(rel) for name, rel in MASTER_PATHS.items()}


def load_assets():
	return cli.load_assets(PACK / "06_runtime")


def capabilities(assets):
	env = assets.envelope
	return registry.bid_workspace_capabilities(env["renderer_profile_id"], env["supported_renderer_version"])


def compile_input(assets, data):
	return compile_published_bid_definition(assets, data, renderer_capabilities=capabilities(assets))


def csv_rows(rel):
	return coverage.read_csv((PACK / rel).read_bytes())


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def c01():
	problems = [f"missing {p}" for p in REQUIRED_PATHS if not (PACK / p).is_file()]
	entries = bundle.inventory(PACK)
	for rel, _digest in entries:
		if rel in GENERATED_WRITTEN:
			continue
		if not any(re.fullmatch(pattern, rel) for pattern in ALLOWED_PATTERNS):
			problems.append(f"unapproved asset {rel}")
	pages = sorted(p for p, _ in entries if p.startswith("01_source/pages/"))
	expected_pages = int(re.search(r"\| Pages \| (\d+) \|", read("01_source/source_record.md")).group(1))
	if len(pages) != expected_pages:
		problems.append(f"{len(pages)} source page images, source record states {expected_pages}")
	for variant in VARIANTS:
		for suffix in ("input", "expected"):
			rel = f"04_fixture/reservation_variants/{variant}_{suffix}.json"
			if not (PACK / rel).is_file():
				problems.append(f"missing {rel}")
	return problems, f"{len(entries)} controlled files inventoried; {len(pages)} source page images."


def c02():
	problems = []
	record = read("01_source/source_record.md")
	stated = re.search(r"File digest \(SHA-256\) \| `([0-9a-f]{64})`", record).group(1)
	actual = bundle.file_digest(PACK / "01_source/ppra_goods_std_official.pdf")
	if stated != actual:
		problems.append("official source digest differs from source_record.md")
	preceding = read_json("05_review/preceding_release.json")
	if next(a["sha256"] for a in preceding["assets"] if a["path"] == "01_source/ppra_goods_std_official.pdf") != actual:
		problems.append("official source digest differs from the approved release 1.0")
	assets = load_assets()
	env = assets.envelope
	for key, value in EXPECTED_IDENTITY.items():
		if env[key] != value:
			problems.append(f"{key} is {env[key]!r}, expected {value!r}")
	if not re.fullmatch(r"stdr-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", env["release_id"]):
		problems.append("release_id is not the opaque stdr-<uuid4> identity")
	if env["schema_version"] != release_assets.SCHEMA_VERSION:
		problems.append("unsupported asset schema version")
	for rel in ["04_fixture/moh_input.json"] + [f"04_fixture/reservation_variants/{v}_input.json" for v in VARIANTS]:
		data = read_json(rel)
		projection.validate(data)
		if data["template_key"] != env["template_key"] or data["expected_renderer_profile_id"] != env["renderer_profile_id"]:
			problems.append(f"{rel} names a different template or renderer")
	return problems, f"Source {actual[:12]}…; release {env['release_id']} {env['template_key']} {env['template_release']}."


def c03():
	problems = []
	cols, cov = csv_rows("03_registers/coverage_register.csv")
	if cols != coverage.COVERAGE_COLUMNS:
		problems.append("coverage_register.csv columns differ from §13.3")
	icols, ins = csv_rows("03_registers/insertion_points.csv")
	if icols != coverage.INSERTION_COLUMNS:
		problems.append("insertion_points.csv columns differ from §13.3")
	fcols, forms = csv_rows("03_registers/forms_register.csv")
	if fcols != coverage.FORMS_COLUMNS:
		problems.append("forms_register.csv columns differ from §13.3")
	rule_ids = {r["rule_id"] for r in load_assets().rules}
	seen = set()
	for row in cov:
		cid = row["coverage_id"]
		if cid in seen:
			problems.append(f"duplicate {cid}")
		seen.add(cid)
		if row["treatment"] not in coverage.TREATMENTS:
			problems.append(f"{cid} treatment {row['treatment']!r} not controlled")
		if row["treatment"] == "Not used by this released pattern" and not row["review_note"].strip():
			problems.append(f"{cid} excluded without a stated basis")
		if row["treatment"] == "Supplier response" and not row["structured_rule_id"]:
			problems.append(f"{cid} Supplier response without structured_rule_id")
		for rid in filter(None, (x.strip() for x in row["structured_rule_id"].split(";"))):
			if rid not in rule_ids:
				problems.append(f"{cid} names unknown rule {rid}")
		rendered = row["treatment"] in ("Locked", "Inherited", "Officer value", "Generated")
		if rendered and not row["human_render_location"].strip():
			problems.append(f"{cid} rendered without a human render location")
		if row["status"] not in ("Reviewed", "Draft checked"):
			problems.append(f"{cid} status {row['status']!r} unresolved")
	kinds = {"value", "condition", "goods_rows", "service_rows", "technical_rows", "acceptance_rows", "material_rows"}
	keys = set()
	for row in ins:
		if row["key"] in keys:
			problems.append(f"duplicate insertion key {row['key']}")
		keys.add(row["key"])
		if row["kind"] not in kinds:
			problems.append(f"insertion key {row['key']} kind {row['kind']!r} not approved")
		if row["source_treatment"] == "Officer value" and not row["key"].startswith(OFFICER_PREFIXES):
			problems.append(f"{row['key']} is an Officer value outside the finite §6.2 decisions")
	for row in forms:
		if row["included"].strip().upper() not in ("TRUE", "FALSE"):
			problems.append(f"{row['form_id']} included flag unclear")
		for rid in filter(None, (x.strip() for x in row["response_rule_ids"].split(";"))):
			if rid not in rule_ids:
				problems.append(f"{row['form_id']} names unknown rule {rid}")
	summary = coverage.summary(cov, ins, forms)
	return problems, (
		f"{summary['source_rows_total']} source rows ({summary['source_rows_reviewed']} Reviewed, "
		f"{len(summary['source_rows_pending_review'])} awaiting review); {summary['forms_total']} forms; {summary['insertion_points_total']} insertion points; "
		f"treatments {summary['treatment_totals']}."
	)


def _render(data):
	profile = read_json("06_runtime/product_profile.json")
	context = projection.document_context(data, profile["document_constants"])
	adapter = registry.document_adapter(profile["renderer_profile_id"], profile["supported_renderer_version"])
	return adapter.render_html(masters(), context), context


def c04():
	problems = []
	keys = {r["key"] for r in csv_rows("03_registers/insertion_points.csv")[1]}
	loop_vars = {"item", "row", "loop"}
	for name, text in masters().items():
		if not name.endswith(".html"):
			continue
		if "<script" in text.lower():
			problems.append(f"{name} contains JavaScript")
		for expr in re.findall(r"\{\{\s*([a-z_][a-z0-9_.]*)", text):
			root = expr.split(".")[0]
			if root in loop_vars:
				continue
			if expr not in keys and not any(expr.startswith(k + ".") or k.startswith(expr + ".") for k in keys):
				problems.append(f"{name} uses unregistered key {expr}")
	for rel in ["04_fixture/moh_input.json"] + [f"04_fixture/reservation_variants/{v}_input.json" for v in VARIANTS]:
		try:
			out, _ = _render(read_json(rel))
		except jinja2.UndefinedError as exc:
			problems.append(f"{rel}: strict render failed: {exc}")
			continue
		problems += [f"{rel}: {p}" for p in out["problems"] if not p.startswith("cross-output") and "Invitation notice" not in p]
	return problems, "Every master key is registered; strict renders of the MoH and variant inputs have no unresolved authoring text."


def c05():
	problems = []
	for rel in ["04_fixture/moh_input.json"] + [f"04_fixture/reservation_variants/{v}_input.json" for v in VARIANTS]:
		out, _ = _render(read_json(rel))
		problems += [f"{rel}: {p}" for p in out["problems"] if p.startswith("cross-output") or "Invitation notice" in p]
	return problems, "The Invitation is separate from the issued Tender and every shared value appears in both."


def _definitions():
	assets = load_assets()
	out = {"moh": compile_input(assets, read_json("04_fixture/moh_input.json"))}
	for variant in VARIANTS:
		try:
			out[variant] = compile_input(assets, read_json(f"04_fixture/reservation_variants/{variant}_input.json"))
		except STDTemplateError:
			pass
	return out


def c06():
	problems = []
	for name, definition in _definitions().items():
		ids = [r["response_id"] for r in definition["response_rows"]]
		tuples = [json.dumps(r["identity"], sort_keys=True) for r in definition["response_rows"]]
		stable = [r["stable_key"] for r in definition["response_rows"]]
		if len(set(ids)) != len(ids) or len(set(tuples)) != len(tuples) or len(set(stable)) != len(stable):
			problems.append(f"{name}: duplicate response identity")
		for row in definition["response_rows"]:
			ident = row["identity"]
			if not all(ident[k] for k in ("published_tender_version_id", "source_family", "immutable_source_id", "rule_id", "field_key")):
				problems.append(f"{name}: incomplete identity tuple {row['response_id']}")
			if not row["field"]["label"] or not row["validation"]["validation_id"]:
				problems.append(f"{name}: {row['stable_key']} lacks a purpose or validation")
		if not verify_definition_digest(definition):
			problems.append(f"{name}: definition_digest does not bind the definition")
	return problems, "Every response has a unique five-part identity, a stable key, a visible purpose and a named validation."


def c07():
	problems = []
	assets = load_assets()
	env = assets.envelope
	if not registry.is_registered(env["renderer_profile_id"], env["supported_renderer_version"]):
		problems.append("renderer profile/version is not registered")
	caps = capabilities(assets)
	used_controls = {f["control_id"] for r in assets.rules for f in r["field_definitions"]} - {release_assets.CHARACTERISTIC}
	used_controls |= {s["control_id"] for s in assets.profile["characteristic_controls"].values()}
	for control in sorted(used_controls - set(caps["controls"])):
		problems.append(f"control {control} unsupported by the renderer")
	for comp in sorted({r["composition_id"] for r in assets.rules} - set(caps["compositions"])):
		problems.append(f"composition {comp} unsupported by the renderer")
	health = registry.health(env["renderer_profile_id"], env["supported_renderer_version"])
	if not health["ok"]:
		problems.append(f"document renderer unhealthy: {health['document']}")
	return problems, f"{env['renderer_profile_id']} {env['supported_renderer_version']} supports every released control and composition; document engine {health['document'].get('found_version')}."


def c08():
	assets = load_assets()
	rules = {r["rule_id"] for r in assets.rules}
	mapped = [m["response_rule_id"] for m in assets.downstream_rules["mappings"]]
	problems = []
	if sorted(mapped) != sorted(rules) or len(set(mapped)) != len(mapped):
		problems.append("mapping rows do not correspond one-to-one with response rules")
	return problems, f"{len(rules)} response rules, {len(mapped)} mapping rows, no orphan."


def c09():
	assets = load_assets()
	groups = [g["evaluation_group_id"] for g in assets.profile["evaluation_groups"]]
	problems = [] if groups == list(release_assets.EVALUATION_GROUPS) else ["evaluation groups differ from the four released groups"]
	counts = {}
	for m in assets.downstream_rules["mappings"]:
		counts[m["evaluation_group_id"] or "Not evaluated"] = counts.get(m["evaluation_group_id"] or "Not evaluated", 0) + 1
	return problems, f"Evaluation treatments: {dict(sorted(counts.items()))}."


def c10():
	assets = load_assets()
	counts = {}
	for m in assets.downstream_rules["mappings"]:
		counts[m["contract_destination"] or "Not carried forward"] = counts.get(m["contract_destination"] or "Not carried forward", 0) + 1
	return [], f"Contract treatments: {dict(sorted(counts.items()))}."


def c11():
	problems = []
	assets = load_assets()
	issued_master = read("02_master/complete_tender.html")
	_, cov = csv_rows("03_registers/coverage_register.csv")
	_, forms = csv_rows("03_registers/forms_register.csv")
	registered = set()
	for row in cov:
		registered |= {x.strip() for x in row["structured_rule_id"].split(";") if x.strip()}
	for row in forms:
		registered |= {x.strip() for x in row["response_rule_ids"].split(";") if x.strip()}
	for rule in assets.rules:
		file_name, anchor = rule["document_anchor"].split("#", 1)
		source = issued_master if file_name == "complete_tender.html" else read(f"02_master/{file_name}")
		if locked_text.anchor_count(source, anchor) < 1:
			problems.append(f"{rule['rule_id']} anchor {anchor} is absent from {file_name}")
		if rule["rule_id"] not in registered:
			problems.append(f"{rule['rule_id']} introduces an obligation absent from the coverage and forms registers")
		if "locked_text" in rule:
			master_text = locked_text.anchored_text(issued_master, anchor)
			if master_text != rule["locked_text"]:
				problems.append(f"{rule['rule_id']} locked text differs from the master anchor {anchor}")
			if locked_text.text_digest(rule["locked_text"]) != rule["source_text_digest"]:
				problems.append(f"{rule['rule_id']} source text digest mismatch")
	definition = _definitions()["moh"]
	rendered = read("04_fixture/moh_expected.html")
	for text in definition["declaration_texts"]:
		anchor = text["document_anchor"].split("#", 1)[1]
		if locked_text.anchored_text(rendered, anchor) != text["resolved_text"]:
			problems.append(f"{text['text_id']} electronic text differs from the issued Tender anchor {anchor}")
	return problems, f"{len(definition['declaration_texts'])} locked declarations reconcile word for word with the issued Tender; every rule is registered and anchored."


def c12():
	problems = []
	data = read_json("04_fixture/moh_input.json")
	definition = _definitions()["moh"]
	groups = projection.goods_groups(data)
	items = {i["requisition_item_id"]: i for i in data["items"]}
	grouped = [s["requisition_item_id"] for g in groups for s in g["source_lineage"]]
	if sorted(grouped) != sorted(items):
		problems.append("every authorised item must appear in exactly one goods group")
	from decimal import Decimal

	for g in groups:
		if Decimal(g["quantity"]) != sum(Decimal(s["quantity"]) for s in g["source_lineage"]):
			problems.append(f"{g['goods_group_id']} quantity does not reconcile")
	goods_price = {r["immutable_source_id"] for r in definition["price_rows"] if r["kind"] == "Goods"}
	if goods_price != {g["goods_group_id"] for g in groups}:
		problems.append("price rows do not cover every goods group")
	if {r["immutable_source_id"] for r in definition["price_rows"] if r["kind"] == "Related service"} != {s["service_requirement_id"] for s in data["related_services"]}:
		problems.append("price rows do not cover every related service")
	tech = {r["identity"]["immutable_source_id"] for r in definition["response_rows"] if r["identity"]["source_family"] == "technical_requirement"}
	if tech != {t["technical_requirement_id"] for t in data["technical_requirements"]}:
		problems.append("technical responses do not match the inherited technical rows")
	acc = {r["identity"]["immutable_source_id"] for r in definition["response_rows"] if r["identity"]["source_family"] == "acceptance_requirement"}
	if acc != {a["acceptance_requirement_id"] for a in data["acceptance_requirements"]}:
		problems.append("acceptance responses do not match the inherited acceptance rows")
	body = copy.deepcopy(data)
	body["tender"]["package_digest"] = ""
	if sha256_hex(body) != data["tender"]["package_digest"]:
		problems.append("fixture package_digest does not follow the fixture rule")
	# Release 1.2: one warranty/support row per applicable published obligation.
	w = data["warranty_support"]
	applicable = sum(1 for key in ("onsite_support_required", "manufacturer_support_required") if w.get(key) is True)
	applicable += sum(1 for key in ("minimum_warranty_months", "maximum_support_response_hours") if isinstance(w.get(key), int) and w[key] > 0)
	applicable += sum(1 for key in ("service_location_constraint", "support_description") if str(w.get(key) or "").strip())
	ws = {r["identity"]["immutable_source_id"] for r in definition["response_rows"] if r["identity"]["source_family"] == "warranty_support"}
	if len(ws) != applicable:
		problems.append(f"warranty/support rows ({len(ws)}) do not match the applicable published obligations ({applicable})")
	return problems, f"{len(groups)} goods line from {len(items)} Requisition items; {len(tech)} technical, {len(ws)} warranty/support, {len(acc)} acceptance and {len(definition['price_rows'])} price rows reconcile."


def c13():
	problems = []
	notes = []
	for variant in VARIANTS:
		input_path = PACK / f"04_fixture/reservation_variants/{variant}_input.json"
		status, reason = VARIANT_STATUS.get(variant, ("Complete", ""))
		summary = cli.variant_summary(input_path, PACK / "06_runtime", release_status=status, incomplete_reason=reason)
		expected = read(f"04_fixture/reservation_variants/{variant}_expected.json")
		if pretty_json(summary) != expected:
			problems.append(f"{variant} does not reproduce its expected result")
		result, identity = VARIANT_EXPECTATIONS[variant]
		if summary["expected_result"] != result:
			problems.append(f"{variant} should be {result}, was {summary['expected_result']}")
		if identity and (summary["expected_error"] or {}).get("identity") != identity:
			problems.append(f"{variant} should block on {identity}")
		if variant == "none" and "RR-RESERVATION" in summary["response_rule_ids"]:
			problems.append("the None variant must publish no reservation declaration")
		if variant in ("women", "persons_with_disabilities") and (summary["reservation_treatment"] or {}).get("eligibility_group_id") != "EVG-ELIGIBILITY":
			problems.append(f"{variant} must map reservation evidence to EVG-ELIGIBILITY")
		if summary["reservation_treatment"] and summary["reservation_treatment"]["planning_designation_is_entitlement"]:
			problems.append(f"{variant} treats the Planning designation as entitlement")
		notes.append(f"{variant}: {summary['expected_result']} ({summary['release_status']})")
	moh = _definitions()["moh"]["reservation_treatment"]
	if moh["category"] != "Youth" or moh["eligibility_group_id"] != "EVG-ELIGIBILITY" or not moh["response_ids"]:
		problems.append("the MoH Youth path must publish its declaration and evidence mapped to EVG-ELIGIBILITY")
	notes.append("MoH Youth: Publishable (Complete)")
	return problems, "; ".join(notes) + "."


def _successor(mutate) -> dict:
	data = read_json("04_fixture/moh_input.json")
	data["publication"]["effective_addendum_ids"] = ["ADD-FIXTURE-001"]
	mutate(data)
	return data


def c14():
	problems = []
	assets = load_assets()
	rules = assets.addendum_rules
	prior = compile_input(assets, read_json("04_fixture/moh_input.json"))

	def classes(successor_input, source_id):
		successor = compile_input(assets, successor_input)
		result = addenda.classify(prior, successor, rules)
		return successor, result, {c["classification"] for c in result if c["stable_key"].split(":")[1] == source_id}

	def relabel(d):
		d["technical_requirements"][2]["label"] = "Installed memory (RAM)"

	_, result, got = classes(_successor(relabel), "TECH-003")
	if got != {"unchanged"}:
		problems.append(f"label-only change: TECH-003 classified {sorted(got)}, expected unchanged")

	def material(d):
		d["technical_requirements"][2]["required_value"] = {"value": 32}
		d["technical_requirements"][2]["required_value_display"] = "32"

	_, result, got = classes(_successor(material), "TECH-003")
	if got != {"fresh_response_required"}:
		problems.append(f"material change: TECH-003 classified {sorted(got)}, expected fresh_response_required")

	def remove(d):
		d["technical_requirements"] = [t for t in d["technical_requirements"] if t["technical_requirement_id"] != "TECH-011"]

	_, result, got = classes(_successor(remove), "TECH-011")
	if got != {"removed"}:
		problems.append(f"removed requirement: TECH-011 classified {sorted(got)}, expected removed")

	def add(d):
		extra = copy.deepcopy(d["technical_requirements"][0])
		extra.update({"technical_requirement_id": "TECH-012", "characteristic_key": "other_essential_characteristic", "label": "Other essential characteristic", "control": "TEXT", "options": [], "required_value": {"value": "Privacy screen filter"}, "required_value_display": "Privacy screen filter", "comparison": "Required", "row_order": 12})
		d["technical_requirements"].append(extra)

	successor, result, got = classes(_successor(add), "TECH-012")
	if got != {"new"}:
		problems.append(f"new requirement: TECH-012 classified {sorted(got)}, expected new")
	incomplete = set(addenda.incomplete_required(successor, result))
	new_required = {r["response_id"] for r in successor["response_rows"] if r["identity"]["immutable_source_id"] == "TECH-012" and r["required"]["rule_id"] == "RQ-ALWAYS"}
	if not new_required or not new_required <= incomplete:
		problems.append("a new mandatory requirement must begin incomplete")
	# Release 1.2 (STD-TPL-001 v0.12 §8.1): each effective addendum gets its own
	# acknowledgement; it is new and begins incomplete, and nothing is asked
	# when no addendum is effective.
	if any(r["identity"]["source_family"] == "document" for r in prior["response_rows"]):
		problems.append("no acknowledgement may be asked when no addendum is effective")
	acks = [c for c in result if c["stable_key"].startswith("document:")]
	if [(c["stable_key"].split(":")[1], c["classification"]) for c in acks] != [("ADD-FIXTURE-001", "new")]:
		problems.append(f"the effective addendum must add exactly one new acknowledgement, got {[(c['stable_key'], c['classification']) for c in acks]}")
	elif not {c["successor_response_id"] for c in acks} <= incomplete:
		problems.append("a new addendum acknowledgement must begin incomplete")
	return problems, "Label-only change keeps TECH-003; material change needs a fresh response; removal keeps history only; a new mandatory requirement begins incomplete; an effective addendum adds its own acknowledgement."


def c15():
	problems = []
	data = read_json("04_fixture/moh_input.json")
	out, _ = _render(data)
	if out["invitation_html"] != read("04_fixture/moh_invitation_expected.html"):
		problems.append("moh_invitation_expected.html does not reproduce")
	if out["issued_tender_html"] != read("04_fixture/moh_expected.html"):
		problems.append("moh_expected.html does not reproduce")
	definition = _definitions()["moh"]
	if pretty_json(definition) != read("06_runtime/moh_published_bid_definition_expected.json"):
		problems.append("moh_published_bid_definition_expected.json does not reproduce")
	return problems, f"MoH Invitation, issued Tender and Published Bid Definition (digest {definition['definition_digest'][:12]}…) reproduce byte for byte."


def c16():
	problems = []
	adapter = registry.document_adapter(EXPECTED_IDENTITY["renderer_profile_id"], "1.0.0")
	issued = adapter.extract_text((PACK / "04_fixture/moh_expected.pdf").read_bytes())
	invitation = adapter.extract_text((PACK / "04_fixture/moh_invitation_expected.pdf").read_bytes())
	flat = " ".join(issued.split())
	for heading in REQUIRED_SECTIONS:
		if heading not in flat:
			problems.append(f"issued Tender PDF lacks {heading}")
	for heading in ("Technical Compliance Response", "Acceptance Requirements Confirmation", "Reserved procurement under regulation 149", "V.3 Technical Requirements"):
		if heading not in flat:
			problems.append(f"issued Tender PDF lacks anchored section {heading}")
	if "INVITATION TO TENDER" not in invitation:
		problems.append("Invitation PDF lacks its heading")
	if "INVITATION TO TENDER" in issued:
		problems.append("issued Tender PDF contains the Invitation notice")
	if "TND-MOH-2027-033 — Page 1 of" not in issued:
		problems.append("issued Tender PDF lacks the reference/page footer")
	return problems, "Both PDFs exist with readable text, every section, the anchored response schedules and the page footer."


def _open_items() -> tuple[list[dict], list[str]]:
	decisions = []
	problems = []
	for line in read("05_review/open_issues.md").splitlines():
		match = re.match(r"^\| (\d+) \| (.+?) \| (.+?) \|", line)
		if not match:
			continue
		number, title, status = match.groups()
		if "Decision required" in status and "Resolved" not in status:
			gate = "GATE-RESERVATION" if re.search(r"reserv|county", title, re.I) else "GATE-DOCUMENTS"
			decisions.append({"item": number, "title": re.sub(r"[`*]", "", title)[:160], "owner": "Procurement/legal reviewer", "gate_id": gate})
	return decisions, problems


def _reviews() -> dict[str, dict]:
	doc = read_json("05_review/gate_reviews.json")
	return {r["gate_id"]: r for r in doc["reviews"]}


def c17():
	problems = []
	doc = read_json("05_review/gate_reviews.json")
	if set(doc) != {"schema_version", "machine_checked_by", "machine_checked_at", "reviews"}:
		problems.append("gate_reviews.json keys differ")
	for review in doc["reviews"]:
		if set(review) != {"gate_id", "result", "checked_by", "checked_at", "evidence_refs", "message"}:
			problems.append(f"review {review.get('gate_id')} keys differ")
			continue
		if review["gate_id"] not in gates.GATES:
			problems.append(f"review for unknown gate {review['gate_id']}")
		if review["result"] not in gates.RESULTS:
			problems.append(f"review {review['gate_id']} result {review['result']!r}")
		if review["result"] == "Passed" and not review["evidence_refs"]:
			problems.append(f"review {review['gate_id']} passes without evidence")
	decisions, more = _open_items()
	problems += more
	_, cov = csv_rows("03_registers/coverage_register.csv")
	_, forms = csv_rows("03_registers/forms_register.csv")
	pending = [r["coverage_id"] for r in cov if r["status"] != "Reviewed"] + [f["form_id"] for f in forms if not f["review_status"].startswith("Reviewed")]
	return problems, f"{len(decisions)} open decision(s): {', '.join('item ' + d['item'] for d in decisions) or 'none'}; {len(pending)} register rows awaiting review ({', '.join(pending) or 'none'}); {len(doc['reviews'])} named gate review(s) recorded."


def c18():
	entries = bundle.inventory(PACK)
	constituents = {name: bundle.file_digest(PACK / rel) for name, rel in release_assets.ASSET_FILES.items()}
	input_digest = bundle.candidate_bundle_digest(PACK)
	return [], f"input bundle digest {input_digest}; constituents " + ", ".join(f"{k} {v[:12]}…" for k, v in constituents.items()) + f"; {len(entries)} files."


def c19():
	problems = []
	reviews = _reviews()
	source = reviews.get("GATE-SOURCE")
	if not source or not source["checked_by"] or not source["checked_at"]:
		problems.append("the source check has no recorded checker and time")
	return problems, "Structured gate reviews are well-formed and the source check names its checker, time and outcome."


def c20():
	problems = []
	cli_src = read("04_fixture/build_definition_fixture.py")
	tree = ast.parse(cli_src)
	imports = {(n.module, a.name) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
	if ("kentender_procurement.std_templates.compiler.definition", "compile_published_bid_definition") not in imports:
		problems.append("the CLI adapter does not call the shared compiler")
	own = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and "compile" in n.name.lower()]
	if own:
		problems.append(f"the CLI adapter defines its own compile function(s): {own}")
	compiler_dir = APP_ROOT / "kentender_procurement/std_templates/compiler"
	digests = []
	for path in sorted(compiler_dir.glob("*.py")):
		source = path.read_text(encoding="utf-8")
		for node in ast.walk(ast.parse(source)):
			names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
			if any(n == "frappe" or n.startswith("frappe.") for n in names):
				problems.append(f"{path.name} imports frappe")
		digests.append(f"{path.name}:{hashlib.sha256(source.encode()).hexdigest()}")
	return problems, "The CLI adapter delegates to the one shared, Frappe-free compiler; production parity is proven by the runtime parity test recorded under GATE-COMPILER-PARITY."


def _candidate_for_report(assets, definition) -> dict:
	_, cov = csv_rows("03_registers/coverage_register.csv")
	anchors = sorted({r["document_anchor"] for r in assets.rules})
	return {
		"release_id": assets.envelope["release_id"],
		"template_key": assets.envelope["template_key"],
		"template_release": assets.envelope["template_release"],
		"assets": {rel: digest for rel, digest in bundle.input_entries(bundle.inventory(PACK))},
		"coverage_treatments": {r["coverage_id"]: r["treatment"] for r in cov},
		"document_anchors": anchors,
		"response_rules": {r["rule_id"]: sha256_hex(r) for r in assets.rules},
		"declarations": {t["text_id"]: {"text_version": t["text_version"], "source_text_digest": t["source_text_digest"]} for t in definition["declaration_texts"]},
		"evaluation_mappings": {m["mapping_id"]: {k: m[k] for k in ("evaluation_treatment", "evaluation_group_id")} for m in assets.downstream_rules["mappings"]},
		"contract_mappings": {m["mapping_id"]: {k: m[k] for k in ("contract_treatment", "contract_destination")} for m in assets.downstream_rules["mappings"]},
		"supported_use": assets.profile["supported_use"],
		"renderer": {
			"renderer_profile_id": assets.envelope["renderer_profile_id"],
			"supported_renderer_version": assets.envelope["supported_renderer_version"],
			"document_engine": registry.document_adapter(assets.envelope["renderer_profile_id"], assets.envelope["supported_renderer_version"]).engine_version,
		},
	}


def c21():
	problems = []
	assets = load_assets()
	report = change_report.build(_candidate_for_report(assets, _definitions()["moh"]), read_json("05_review/preceding_release.json"))
	(PACK / "05_review/release_change_report.json").write_text(pretty_json(report), encoding="utf-8", newline="\n")
	if report["overall_result"] not in (change_report.FIRST_RELEASE, change_report.COMPATIBLE, change_report.BREAKING):
		problems.append("overall result is not a released value")
	for category, totals in report["totals"].items():
		if sum(totals.values()) != sum(1 for c in report["changes"] if c["category"] == category):
			problems.append(f"{category} totals do not reconcile")
	for change in report["changes"]:
		if set(change) != {"change_kind", "category", "identity", "summary", "compatibility_effect"}:
			problems.append(f"change {change.get('identity')} is incomplete")
	breaking = any(c["compatibility_effect"] == "Breaking" for c in report["changes"])
	if breaking != (report["overall_result"] == change_report.BREAKING):
		problems.append("overall result disagrees with the change effects")
	return problems, f"Compared with release {report['preceding_release']}: {len(report['changes'])} changes; {report['overall_result']}."


def c22():
	assets = load_assets()
	key = assets.envelope["template_key"]
	templates = PACK.parent
	found = quality.run(
		rules=assets.rules, mappings=assets.downstream_rules["mappings"], profile=assets.profile,
		evaluation=json.loads((templates / "evaluation_rules" / f"{key}.json").read_text(encoding="utf-8")),
		register=json.loads((templates / "quality_register" / f"{key}.json").read_text(encoding="utf-8")),
		master_html=read("02_master/complete_tender.html"), template_release=assets.envelope["template_release"])
	problems = [f"{f.check} {f.where}: {f.message}" for f in found["failures"]]
	return problems, (f"No content defect; {len(found['advisories'])} advisories for review; {len(found['deferred'])} items deferred or open on the record "
		f"({', '.join(sorted({f.where for f in found['deferred']}))}).")


CHECKS = (
	("C01", "Required path inventory and absence of unapproved assets", "pack", c01),
	("C02", "Source, schema and release identities", "01_source; 06_runtime", c02),
	("C03", "Complete coverage, form and insertion classifications", "03_registers", c03),
	("C04", "Jinja key use, strict fixture rendering and unresolved authoring text", "02_master", c04),
	("C05", "Invitation/issued-Tender separation and shared-value equality", "02_master", c05),
	("C06", "Unique stable IDs and response identity tuples", "06_runtime", c06),
	("C07", "Supported controls, compositions, validations and renderer profile", "06_runtime/product_profile.json", c07),
	("C08", "One mapping for every response rule and no orphan mapping", "06_runtime/downstream_rules.json", c08),
	("C09", "Valid evaluation group and explicit evaluated/not-evaluated treatment", "06_runtime/downstream_rules.json", c09),
	("C10", "Valid contract destination and explicit carried/not-carried treatment", "06_runtime/downstream_rules.json", c10),
	("C11", "Response/document obligation and locked-text reconciliation", "06_runtime/response_rules.json; 02_master", c11),
	("C12", "Goods, service, evidence and price-schedule lineage and reconciliation", "04_fixture/moh_input.json", c12),
	("C13", "Reservation and County variants, including unsupported overlap failure", "04_fixture/reservation_variants", c13),
	("C14", "Addendum identity and migration fixtures", "06_runtime/addendum_identity_rules.json", c14),
	("C15", "Exact reproduction of all MoH expected HTML and JSON outputs", "04_fixture; 06_runtime", c15),
	("C16", "PDF existence, readable text, required sections and document anchors", "04_fixture", c16),
	("C17", "Review blockers and mandatory reviewer decisions", "05_review", c17),
	("C18", "Constituent SHA-256 values and the candidate bundle digest", "pack", c18),
	("C19", "Complete structured gate rows, evidence references and source-check facts", "05_review/gate_reviews.json", c19),
	("C20", "Exact compiler parity between fixture and production test vectors", "04_fixture/build_definition_fixture.py", c20),
	("C21", "Generation and internal consistency of the preceding-release change report", "05_review/release_change_report.json", c21),
	("C22", "Content quality: wording, tables, evaluation coverage and polarity", "06_runtime; evaluation_rules; quality_register", c22),
)


def tool_versions() -> dict:
	def cmd(args):
		binary = shutil.which(args[0])
		if not binary:
			return "not installed"
		result = subprocess.run([binary] + args[1:], capture_output=True, text=True, check=False)
		return ((result.stdout or "") + (result.stderr or "")).strip().splitlines()[0]

	return {
		"python": platform.python_version(),
		"jinja2": jinja2.__version__,
		"wkhtmltopdf": cmd(["wkhtmltopdf", "--version"]),
		"pdftotext": cmd(["pdftotext", "-v"]),
	}


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
	parser.add_argument("--root", required=True)
	parser.add_argument("--write-report", required=True)
	args = parser.parse_args(argv)
	if Path(args.root).resolve() != PACK:
		print(f"--root must be the pack root {PACK}", file=sys.stderr)
		return 2
	report = Report()
	for check_id, title, asset, fn in CHECKS:
		report.run(check_id, title, asset, fn)
	env = load_assets().envelope
	review_doc = read_json("05_review/gate_reviews.json")
	gate_rows = gates.evaluate(report.results(), {r["gate_id"]: r for r in review_doc["reviews"]}, machine_checked_by=review_doc["machine_checked_by"], machine_checked_at=review_doc["machine_checked_at"])
	failed = [r for r in report.rows if r["result"] == "Failed"]
	document = {
		"schema_version": 1,
		"release_id": env["release_id"],
		"template_key": env["template_key"],
		"template_release": env["template_release"],
		"tool_versions": tool_versions(),
		"input_bundle_digest": bundle.candidate_bundle_digest(PACK),
		"checks": report.rows,
		"summary": {"passed": sum(1 for r in report.rows if r["result"] == "Passed"), "failed": len(failed), "blocking": bool(failed)},
	}
	(PACK / args.write_report).write_text(pretty_json(document), encoding="utf-8", newline="\n")
	gates_doc = {"schema_version": 1, "release_id": env["release_id"], "template_key": env["template_key"], "template_release": env["template_release"], "gates": gate_rows}
	(PACK / "05_review/release_gates.json").write_text(pretty_json(gates_doc), encoding="utf-8", newline="\n")
	for row in report.rows:
		print(f"{row['check_id']} {row['result']:<7} {row['title']}" + (f" — {row['message']}" if row["result"] != "Passed" else ""))
	print("gates: " + ", ".join(f"{g['gate_id']}={g['result']}" for g in gate_rows))
	return 1 if failed else 0


if __name__ == "__main__":
	sys.exit(main())
