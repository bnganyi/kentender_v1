"""Writes rule_reconciliation.md from the canonical published definition and bid.

Usage: python3 tools/build_rules.py <evl_source.json>   (from tools/dump_source.py)

Each evaluated response field is given one check kind. The kinds are the draft of
`06_runtime/evaluation_rules.json` (plan D7, OD-C); the comparison values always
come from the published definition, never from this table.
"""
import json
import sys
from decimal import Decimal

src = json.load(open(sys.argv[1]))
definition = src["definition"]["definition"]
package = src["packages"][0]
values = {r["response_id"]: r["value"] for r in package["responses"]}
if package.get("confirmation"):
    values[package["confirmation"]["response_id"]] = package["confirmation"].get("confirmed")
evidence = {e["response_id"]: len(e.get("files") or []) for e in package.get("evidence", [])}
groups = {g["group_key"]: g for s in definition["sections"] for g in s["groups"]}
mappings = {m["mapping_id"]: m for m in definition["evaluation_mappings"]}

YES_NO_REVIEW = {"state_owned_enterprise", "procuring_entity_interest"} | {f"conflict_{i:02d}" for i in range(1, 10)}
RECORDED = {"discounts", "commissions_gratuities_fees", "consultation_details", "business_structure", "ownership_details",
            "trade_licence", "maximum_business_value", "procuring_entity_interest_details", "conflict_details", "comment",
            "contract_value"}
PRESENCE = {"offered_make_model", "certificate_number", "issuer", "guarantee_reference", "client_name", "contract_reference",
            "scope", "signatory_name", "signatory_title"}


def kind_for(rule, field, facts, row):
    """(kind, published basis, evidence assessment required)"""
    if field == "confirmed":
        return "confirmed", "Declared confirmation must be true", False
    if field in RECORDED:
        return "recorded", "Shown to members; not a pass/fail input of the published result rule", False
    if field in YES_NO_REVIEW:
        return "review-if-yes", "\"No\" meets; \"Yes\" discloses a matter the committee must assess (published result rule)", False
    if field == "disclosure":
        return "review-unless", "\"Arrived at the Tender independently\" meets; a consultation needs committee assessment", False
    if field in PRESENCE:
        return "presence", "A value is present (presence never verifies authenticity)", False
    if field == "certificate_category":
        return "choice-in", f"In permitted_categories {facts.get('permitted_categories')}", False
    if field == "certificate_valid_until":
        return "date-not-before", f"Not before submission_deadline_date {facts.get('submission_deadline_date')}", False
    if field == "security_form":
        return "choice-in", f"In permitted_forms {facts.get('permitted_forms')}", False
    if field == "instrument_amount":
        return "money-equals", f"Equals amount {facts.get('amount')} {facts.get('currency')}", False
    if field == "bank_guarantee_valid_until":
        return "date-not-before (when Demand Bank Guarantee)", f"Not before {facts.get('bank_guarantee_expiry_date')}", False
    if field == "insurance_guarantee_valid_until":
        return "date-not-before (when Insurance Guarantee)", f"Not before {facts.get('insurance_guarantee_expiry_date')}", False
    if field == "offered_delivery_date":
        return "date-not-after", f"Not after latest_delivery_date {facts.get('latest_delivery_date')}", False
    if field == "completion_date":
        return "date-in-window", f"Between {facts.get('window_start')} and {facts.get('window_end')}; {facts.get('required_count')} qualifying entries required", False
    if field in ("unit_price", "tax_amount"):
        return "calculation-input", "Input to CALC-LINE-TOTAL / CALC-TENDER-TOTAL (exact decimals, scale 2)", False
    if field == "compliance":
        return "equals", "\"Comply\"", False
    if field == "offered_value":
        comp, ctl, req, unit = facts.get("comparison"), facts.get("control"), facts.get("required_value"), facts.get("unit") or ""
        if ctl == "TEXT":
            return "manual", f"Free text against \"{req.get('value')}\": needs a member finding (EVL v0.4 §4.1)", False
        if comp == "Minimum":
            return "minimum", f"≥ {req.get('value')} {unit}".strip(), False
        if comp == "Maximum":
            return "maximum", f"≤ {req.get('value')} {unit}".strip(), False
        if comp == "One of" or (comp == "Required" and ctl in ("YES_NO", "SELECT")):
            return "equals", f"= {req.get('value')}", False
        if ctl == "MULTI_SELECT":
            return "includes-all", f"Includes {req.get('values')}", False
        if ctl == "PORT_LIST":
            return "ports-minimum", "Each port type at least its minimum_count " + json.dumps(req.get("ports")), False
        return "manual", f"Unsupported comparison {comp}/{ctl}", False
    if field in ("evidence", "certificate_evidence", "security_evidence"):
        required = (row.get("validation") or {}).get("parameters", {}).get("minimum", 0) > 0
        return ("evidence" if required else "evidence-optional"), ("At least one file; its content is assessed by a member" if required else "Optional supporting files; shown, not required"), required
    return "manual", "No automatic meaning defined", False


def fmt(v):
    if v is None:
        return "—"
    s = json.dumps(v) if not isinstance(v, str) else v
    return s.replace("|", "\\|")[:90]


def preview(kind, facts, value, field, rid):
    """What the automatic comparison gives on the current canonical seed (informational)."""
    try:
        if kind == "confirmed":
            return "Meets" if value is True else "Does not meet"
        if kind == "equals":
            want = "Comply" if field == "compliance" else (facts.get("required_value") or {}).get("value")
            return "Meets" if value == want else "Does not meet"
        if kind == "minimum":
            return "Meets" if Decimal(str(value)) >= Decimal(str(facts["required_value"]["value"])) else "Does not meet"
        if kind == "maximum":
            return "Meets" if Decimal(str(value)) <= Decimal(str(facts["required_value"]["value"])) else "Does not meet"
        if kind == "includes-all":
            return "Meets" if set(facts["required_value"]["values"]) <= set(value or []) else "Does not meet"
        if kind == "ports-minimum":
            have = {p["port_type"]: p["count"] for p in value or []}
            return "Meets" if all(have.get(p["port_type"], 0) >= p["minimum_count"] for p in facts["required_value"]["ports"]) else "Does not meet"
        if kind == "presence":
            return "Meets" if value not in (None, "") else "Does not meet"
        if kind == "review-if-yes":
            return "Meets" if value == "No" else "Needs review"
        if kind == "review-unless":
            return "Meets" if value == "Arrived at the Tender independently" else "Needs review"
        if kind == "choice-in":
            allowed = facts.get("permitted_categories") or facts.get("permitted_forms") or []
            return "Meets" if value in allowed else "Does not meet"
        if kind == "evidence":
            return "Meets (presence); evidence assessment pending" if evidence.get(rid) else "Does not meet"
        if kind == "manual":
            return "Needs review"
    except Exception:
        return "Needs review"
    return ""


out = [
    "# EVL-CHG-001 v0.4: rule reconciliation",
    "",
    "| Control | Value |",
    "|---|---|",
    "| Version | 0.4-rules.1 |",
    "| Date | 30 September 2026 |",
    f"| Source | The canonical Tender {definition.get('tender_id')} ({src['handoff']['tender_reference']}), published bid definition `{definition['bid_definition_id']}` version {definition['definition_version']}, template release `{definition['template_release_id']}`; the canonical bid package `{package['bid']['bid_reference']}` ({package['bid']['tenderer_name']}). Dumped by `tools/dump_source.py`, written by `tools/build_rules.py`. |",
    "",
    "**Purpose.** Classify every evaluated response of the published definition into one check kind (the draft of `06_runtime/evaluation_rules.json`, plan D7), name its published basis, and state whether a member's evidence assessment is also required (EVL v0.4 §4.2 combined requirement). Comparison values always come from the published definition at run time.",
    "",
    "**Check kinds.** `confirmed` declared true · `equals` / `choice-in` permitted choice · `minimum` / `maximum` numeric with the published unit and inclusive boundary · `date-not-before` / `date-not-after` / `date-in-window` · `includes-all` multi-select · `ports-minimum` · `money-equals` exact decimal · `presence` a value exists · `calculation-input` published calculation · `evidence` required files present, content assessed by a member · `review-if-yes` / `review-unless` a disclosure the committee assesses · `manual` no automatic meaning (free text, \"or equivalent\") · `recorded` shown, not a pass/fail input · `evidence-optional` shown only.",
    "",
]
counts = {}
evaluated = [m for m in definition["evaluation_mappings"] if m["evaluation_treatment"] == "Evaluated"]
not_eval = [m for m in definition["evaluation_mappings"] if m["evaluation_treatment"] != "Evaluated"]
out.append(f"**Counts:** {len(definition['evaluation_mappings'])} mappings: {len(evaluated)} evaluated, {len(not_eval)} not evaluated ({', '.join(m['mapping_id'] for m in not_eval)}). {len(definition['response_rows'])} response rows in the definition.")
out.append("")
out.append("## Mappings")
out.append("")
out.append("| Mapping | Group | Treatment | Responses | Published result rule |")
out.append("|---|---|---|---|---|")
for m in definition["evaluation_mappings"]:
    out.append(f"| {m['mapping_id']} | {m['evaluation_group_id'] or '—'} | {m['evaluation_treatment']} | {len(m['response_ids'])} | {m['evaluation_result_rule'] or m.get('reason','')} |")
out.append("")
out.append("## Evaluated responses")
out.append("")
out.append("\"Current seed\" is what the automatic comparison gives on today's canonical bid (see C22); \"Ordinary story\" is EVL v0.4 §9.12.")
out.append("")
out.append("| Group key | Requirement | Field | Check kind | Published basis | Evidence assessment | Canonical bid value | Current seed | Ordinary story (§9.12) |")
out.append("|---|---|---|---|---|---|---|---|---|")
for r in definition["response_rows"]:
    m = mappings.get(r["evaluation_mapping_id"])
    if not m or m["evaluation_treatment"] != "Evaluated":
        continue
    g = groups.get(r["group_key"], {})
    facts = g.get("published_facts", {})
    field = r["field"]["field_key"]
    kind, basis, assess = kind_for(r["identity"]["rule_id"], field, facts, r)
    counts[kind] = counts.get(kind, 0) + 1
    label = facts.get("label") or facts.get("description") or facts.get("evidence_kind") or r["group_key"].split("/")[-1]
    val = values.get(r["response_id"])
    if kind in ("evidence", "evidence-optional"):
        val = f"{evidence.get(r['response_id'], 0)} file(s)"
    story = "Meets" if kind not in ("recorded", "evidence-optional", "calculation-input") else ""
    out.append(f"| {r['group_key']} | {fmt(label)} | {field} | {kind} | {fmt(basis)} | {'Yes' if assess or kind == 'manual' else ''} | {fmt(val)} | {preview(kind, facts, values.get(r['response_id']), field, r['response_id'])} | {story} |")
out.append("")
out.append("**Kinds used:** " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ".")
out.append("")
out.append("## Financial")
out.append("")
out.append("| Price row | Calculation | Inputs | Submitted in package |")
out.append("|---|---|---|---|")
for p in definition["price_rows"]:
    out.append(f"| {p['description']} | {p['calculation']['calculation_id']} | {fmt(p['calculation']['inputs'])} | {fmt(package['price'].get('total') if p['calculation']['calculation_id']=='CALC-TENDER-TOTAL' else package['price']['lines'][0].get('line_total'))} |")
out.append("")
out.append("No published arithmetic-correction rule, adjustment, preference margin or tie-break is present in the definition. A recomputed total that differs from the submitted total is therefore Needs review with the discrepancy shown, never a corrected amount (EVL v0.4 §4.4). Evaluation adjustments read **None**.")
out.append("")
out.append("## Findings")
out.append("")
out.append("1. **The canonical bid is placeholder data (C22).** Many answers read \"Seeded answer for the canonical bid.\", numeric answers are 0 (memory, storage, display, battery), connectivity is [\"Ethernet\"], ports are one USB-A, experience contract values are 0.01, every conflict question is \"Yes\", and the evidence files are 453-byte stand-ins. On this bid the automatic checks give **Not responsive**, which contradicts the ordinary story. The Bid Submission canonical seed must submit the EVL v0.4 §9.1/§9.12 facts before the Evaluation canonical stage can tell that story (Phase 13, BDS tracker addendum).")
out.append("2. **The hand-off omits the definition identity (C23).** `packages[].bid_definition_id` and `definition_digest` are empty and `definition_version` is 0 in `EV-IN-MOH-2027-002-01`. The package itself carries `tender.bid_definition_id/definition_version/definition_digest`; Evaluation reads those and cross-checks them with `bid_definition.definition_for`.")
out.append("3. **Free text needs a member.** TECH-008 (processor, \"or equivalent benchmark\"), TECH-009 (operating system) and WS-SERVICE-LOCATION / WS-SUPPORT-CONTACTS are text; they are `manual` or `presence` with a member finding (C13).")
out.append("4. **Evidence assessments.** Every required evidence field (reservation certificate, tender security, technical evidence, experience, manufacturer authorisation, datasheet, after-sales, eligibility documents) is a combined requirement: presence is automatic, and a member's evidence finding completes it (EVL v0.4 §4.2).")
out.append("5. **Debarment.** SD1 \"not debarred\" has no authoritative external source (EVL v0.4 §2.2); it is `confirmed` plus a member evidence finding.")
open("rule_reconciliation.md", "w").write("\n".join(out) + "\n")
print(counts)
