# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Deliveries tab: arrival, inspection, technical certificate and acceptance (boards D04, D05, D19, D06, D07, D07-P; CM-CHG-001 v0.8 section 10)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt, formatdate

from kentender_contracts.boards import chrome, kit, statements
from kentender_contracts.boards.context import Context, money, when
from kentender_contracts.services import bindings, delivery, records, work

COMPARATOR_WORDS = {">=": "At least", "<=": "At most", ">": "More than", "<": "Less than", "=": "", "==": ""}


def units_summary(units: list[str]) -> str:
	if not units:
		return "—"
	return units[0] if len(units) == 1 else f"{units[0]}–{units[-1]}" if len(units) > 3 else ", ".join(units)


def _arrival(ctx: Context, number: int):
	name = frappe.db.get_value("Contract Arrival", {"contract_case": ctx.case, "arrival_no": number}, "name")
	return frappe.get_doc("Contract Arrival", name)


def _arrival_no(subject: str) -> int:
	return cint(subject.split()[-1])


def _item_name(ctx: Context) -> str:
	lines = ctx.terms.get("lines") or [{}]
	return lines[0].get("description") or lines[0].get("item") or "Items"


def d04(ctx: Context) -> dict:
	"""Record delivery (the receiver)."""
	line = (ctx.terms.get("lines") or [{}])[0]
	now = ctx.position["lines"].get(line.get("line_id"), {})
	expected = max(0, cint(now.get("ordered")) - cint(now.get("accepted")) - cint(now.get("pending_decision")) - cint(now.get("deferred")))
	destination = (ctx.terms.get("delivery") or {}).get("destination", "")
	fields = [kit.tx("Supplier delivery reference", "", "supplier_reference"), kit.dt("Received at", "", "received_at", time=True), kit.sel("Destination", destination, [destination] if destination else [""], "destination")]
	replaceable = [u for u in ctx.position["units"].values() if u["status"] in ("Rejected", "Returned") and not any(v["replaces"] == u["unit"] for v in ctx.position["units"].values())]
	if replaceable:  # a replacement names the rejected units it replaces (section 5.4)
		fields.append(kit.ta("Replaces (rejected unit references, one per line)", "", "replaces", rows=3))
	items = kit.t(["Item", "Expected", "Arrived", "Unit references"], [[line.get("description") or line.get("item"), str(expected), f"#{expected}", "—"]], [1, 2], inputs={"0,2": f"quantity.{line.get('line_id')}"}, live={"0,3": f"units.{line.get('line_id')}"})
	b = chrome.base(ctx, "D04", d="D04", name="Receive goods", title="Record delivery", tab="Deliveries", next=chrome.next_block(ctx) or kit.turn("Record the goods that arrived.", ctx.name(ctx.user)), ev=["Delivery schedule 1"],
		regions=[kit.R("Delivery", kit.f(["Delivery due", formatdate((ctx.terms.get("delivery") or {}).get("due"), "d MMMM yyyy")], ["Destination", destination])), kit.R("Arrival details", kit.fl(*fields)),
			kit.R("Items", items, kit.bt("Enter unit references"), kit.xh("Recording delivery does not accept the goods."))], p="Record delivery", s2=["Cancel"])
	b["lineId"] = line.get("line_id")
	b["actions"]["Record delivery"] = kit.command("RecordContractArrival")
	b["actions"]["Cancel"] = kit.tab("Deliveries")
	b["actions"]["Enter unit references"] = kit.dialog("units")
	b["dialogs"]["units"] = kit.dlg("Unit references", [kit.fl(kit.ta("Unit references", "", f"units.{line.get('line_id')}", rows=11))], "Use references", local=True)
	return b


def _findings_rows(ctx: Context, found: dict | None, criteria: list[dict]) -> list[list[str]]:
	rows = []
	units = list((found or {}).get("units", {}))
	for c in criteria:
		required = f"{COMPARATOR_WORDS.get(c['comparator'], c['comparator'])} {c['value']} {c.get('unit', '')}".strip() if c["comparator"] not in ("=", "==") else str(c["value"])
		cells = [found["units"][u]["criteria"][c["id"]] for u in units if c["id"] in found["units"][u]["criteria"]] if found else []
		results = {x["result"] for x in cells}
		result = "Does not meet" if "Does not meet" in results else "Needs review" if (not cells or "Needs review" in results) else "Meets"
		values = [x["observed"] for x in cells if x["observed"]]
		if not cells:
			observed = "Not recorded"
		elif values and len(set(values)) == 1 and len(values) == len(cells):
			observed = f"{values[0]}{(' ' + c.get('unit')) if c.get('unit') and c['comparator'] not in ('=', '==') else ''} on all {len(cells)}"
		else:
			counts: dict[str, int] = {}
			for x in cells:
				counts[x["observed"] or "not recorded"] = counts.get(x["observed"] or "not recorded", 0) + 1
			observed = "; ".join(f"{n} {v}" for v, n in counts.items())
		rows.append([c["name"], required, observed, f"!{result}"])
	return rows


def _criteria_of(ctx: Context, items: list[dict]) -> list[dict]:
	"""The frozen criteria that apply to the lines of an arrival, each once."""
	out: list[dict] = []
	for line_id in dict.fromkeys(i["line_id"] for i in items if i.get("line_id")):
		out += [c for c in delivery.criteria_for(ctx.terms, line_id) if c not in out]
	return out


def is_service(ctx: Context, items: list[dict]) -> bool:
	return bool(items) and all(i.get("line_id") in delivery.service_lines(ctx.terms) for i in items if i.get("line_id")) and any(i.get("line_id") for i in items)


def d05(ctx: Context, number: int) -> dict:
	"""Inspect delivery (an appointed, declared inspector)."""
	arrival = _arrival(ctx, number)
	inspection = delivery.current_inspection(ctx.case, arrival.name)
	found = records.loads(inspection.findings_json) if inspection else None
	items = records.loads(arrival.items_json, [])
	units = [u for i in items for u in i.get("units", [])]
	criteria = _criteria_of(ctx, items)
	names = {}
	obs_rows = []
	given = {(o["unit"], o["criterion_id"]): o.get("value", "") for o in (records.loads(inspection.observations_json, []) if inspection else [])}
	for ri, unit in enumerate(units):
		row = [unit]
		for ci, c in enumerate(criteria):
			value = given.get((unit, c["id"]), "")
			names[f"{ri},{ci + 1}"] = f"obs.{unit}.{c['id']}"
			row.append(f"^{value or 'Not recorded'}|Not recorded,Yes,No" if not isinstance(c["value"], (int, float)) else f"~{value}")
		obs_rows.append(row)
	cols = ["Unit"] + [f"{c['name']}{(' (' + c['unit'] + ')') if c.get('unit') else ''}" for c in criteria]
	b = chrome.base(ctx, "D05", d="D05", name="Inspect delivery", title="Inspect delivery", tab="Deliveries", next=chrome.next_block(ctx), ev=[f"Arrival {number}", "Contract requirements 1"],
		regions=[kit.R("Coverage", kit.f(["Coverage", f"{len(units)} {_item_name(ctx).lower()}; each unit inspected"])), kit.R("Findings", kit.t(["Check", "Required", "Observed", "Result"], _findings_rows(ctx, found, criteria)))],
		p="Record observations", s2=["View all observations"])
	b["arrival"] = arrival.name
	b["actions"]["Record observations"] = kit.dialog("record")
	b["actions"]["View all observations"] = kit.dialog("all")
	b["dialogs"]["record"] = kit.dlg("Record observations", [kit.t(cols, obs_rows, inputs=names)], "Save observations", command="RecordInspectionObservations", args={"arrival": arrival.name})
	b["dialogs"]["all"] = kit.dlg("All observations", [kit.t(cols, [[r[0]] + [c.lstrip("~").split("|")[0].lstrip("^") for c in r[1:]] for r in obs_rows], [1, 2])], "", ["Close"], local=True)
	certified = delivery.certified_units(ctx.case, number)
	if found and any(f["result"] == "Needs review" and u not in certified for u, f in found["units"].items()):  # D05-M: readings are missing or unreadable, so the inspector's only way on is to record them again
		b["id"], b["next"], b["p"], b["s2"] = "D05-M", kit.blk("The inspection evidence needs review.", ctx.name(ctx.user), ["Record observations", "View all observations"]), "", []
	return b


def d19(ctx: Context, number: int) -> dict:
	"""Confirm technical inspection (the technical certifier)."""
	arrival = _arrival(ctx, number)
	inspection = delivery.current_inspection(ctx.case, arrival.name)
	found = records.loads(inspection.findings_json)
	missing = sum(1 for f in found["units"].values() if f["result"] == "Needs review")
	good = [u for u, f in found["units"].items() if f["result"] == "Meets"]
	bad = [u for u, f in found["units"].items() if f["result"] == "Does not meet"]
	failed_checks = sorted({c["name"] for u in bad for c in [{"name": cid} for cid, v in found["units"][u]["criteria"].items() if v["result"] == "Does not meet"]})
	criteria = _criteria_of(ctx, records.loads(arrival.items_json, []))
	names = {c["id"]: c["name"] for c in criteria}
	tests = ", ".join(f"{c['name']} {c['comparator']} {c['value']}{(' ' + c['unit']) if c.get('unit') else ''}" for c in criteria)
	failed = "; ".join(f"{u}: " + ", ".join(names[cid] for cid, v in found["units"][u]["criteria"].items() if v["result"] == "Does not meet") for u in bad) or "None"
	ao = ctx.name(next(iter(work.holders("Accounting Officer")), ""))
	b = chrome.base(ctx, "D19", d="D19", name="Technical certificate", title="Confirm technical inspection", tab="Deliveries", next=chrome.next_block(ctx), ev=[f"Inspection {inspection.version_no}"],
		regions=[kit.R(f"Technical certificate {number}", kit.r(["Contract", ctx.doc.contract_id], ["Inspected", str(len(found["units"]))], ["Conforms", str(len(good))], ["Fails", str(len(bad))], ["Missing evidence", str(missing)], ["Tests", tests],
			["Conforming units", units_summary(good)], ["Failed units", failed], ["Recipient", f"{ao}, Accounting Officer" if ao else "Accounting Officer"]),
			kit.x(statements.TECHNICAL))],
		p="Sign technical certificate")
	b["arrival"] = arrival.name
	b["actions"]["Sign technical certificate"] = kit.command("SignTechnicalCertificate", arrival=arrival.name)
	return b


def _report_regions(ctx: Context, report, *, signatures: bool, with_failures: bool = True) -> list[dict]:
	lines = records.loads(report.lines_json, [])
	accepted = [u for l in lines for u in l["units"]["accepted"]]
	rejected = [u for l in lines for u in l["units"]["rejected"]]
	deferred = [u for l in lines for u in l["units"]["deferred"]]
	reasons = {u: r for l in lines for u, r in (l.get("reasons") or {}).items()}
	summary = kit.R("Findings", kit.f(["Delivered", str(sum(l["arrived"] for l in lines))], ["Meets", str(len(accepted))], ["Does not meet", str(len(rejected))], ["Needs review", str(len(deferred))]))
	failures = kit.R("Units that do not meet", kit.t(["Unit", "Check", "Required", "Observed", "Result"], [[u, reasons.get(u, "Does not meet the requirement"), "", "", "!Does not meet"] for u in rejected], []))
	reason = "; ".join(sorted(set(reasons.values()))) or "None"
	disposition = kit.R("Quantity disposition", kit.f(["Accepted", str(len(accepted))], ["Rejected", str(len(rejected))], ["Deferred", str(len(deferred))]), kit.r(["Reason", reason]))
	signers = records.loads(report.signers_json, [])
	sigs = kit.R("Signatures", kit.t(["Signer", "Role", "Status", "Signed"], [[s["name"], s["capacity"], "!Signed with dissent" if s["state"] == "Signed" and s.get("dissent") else "!Signed" if s["state"] == "Signed" else "!Awaiting signature", when(s["signed_at"]) if s["signed_at"] else "—"] for s in signers]))
	preview = kit.R("", kit.pv("Report preview", [["Statement", statements.ACCEPTANCE],
		["Findings", f"{len(accepted)} meet; {len(rejected)} do not meet; {len(deferred)} need review"], ["Accepted", str(len(accepted))], ["Rejected", str(len(rejected))], ["Deferred", str(len(deferred))], ["Reason", reason],
		["Signers", ", ".join(s["name"] for s in signers)]]))
	cert = frappe.get_all("Contract Certificate", filters={"name": ["in", (report.technical_certificate or "").split(",")]}, fields=["signer", "signed_at"], limit=1)
	technical = kit.R("Technical evidence", kit.x(f"Technical certificate — signed by {ctx.name(cert[0].signer)}, {when(cert[0].signed_at)}" if cert else "Technical certificate"))
	out = [summary] + ([failures] if with_failures and rejected else []) + [disposition] + ([sigs] if signatures else []) + [preview, technical]
	return out


def d06(ctx: Context, number: int) -> dict:
	"""Acceptance review: the chair prepares one report from the findings."""
	arrival = _arrival(ctx, number)
	prior = delivery.position.decided_units(ctx.case)
	found = records.loads(delivery.current_inspection(ctx.case, arrival.name).findings_json)
	certified = delivery.certified_units(ctx.case, number)
	lines = []
	units = {"accepted": [], "rejected": [], "deferred": []}
	reasons = {}
	for u, f in found["units"].items():
		if u in prior:
			continue
		key = "accepted" if f["result"] == "Meets" and u in certified else "rejected" if f["result"] == "Does not meet" and u in certified else "deferred"
		units[key].append(u)
		if key == "rejected":
			reasons[u] = "; ".join(c["reason"] for c in f["criteria"].values() if c["reason"])
	draft = frappe._dict(lines_json=records.dumps([{"arrived": sum(len(v) for v in units.values()), "units": units, "reasons": reasons}]), signers_json=records.dumps([m for m in ctx.appointment["members"]]), technical_certificate="")
	draft.signers_json = records.dumps([{"name": m["name"], "capacity": m["capacity"], "state": "Awaiting", "signed_at": ""} for m in ctx.appointment["members"]])
	cert = delivery._certificate_for(ctx.case, number)
	draft.technical_certificate = cert.name if cert else ""
	regions = _report_regions(ctx, draft, signatures=False)
	sent_back = _correction_asked(ctx)
	if sent_back:
		regions.insert(0, sent_back)
	b = chrome.base(ctx, "D06", d="D06", name="Acceptance review", title="Review inspection", tab="Deliveries", next=chrome.next_block(ctx), ev=[f"Inspection {delivery.current_inspection(ctx.case, arrival.name).version_no}"],
		regions=regions, p="Prepare report for signing")
	b["actions"]["Prepare report for signing"] = kit.command("PrepareAcceptanceReport", arrivals=[arrival.name])
	return b


def d07(ctx: Context, version: int, *, pending: bool = False) -> dict:
	"""Acceptance signature: a required member signs the exact frozen report. D07-P: signed, the stock update is pending."""
	report = frappe.get_doc("Contract Acceptance", frappe.db.get_value("Contract Acceptance", {"contract_case": ctx.case, "version_no": version}, "name"))
	regions = _report_regions(ctx, report, signatures=True)
	if pending:
		regions = [r for r in regions if r["t"] not in ("Units that do not meet", "Technical evidence")]
	b = chrome.base(ctx, "D07-P" if pending else "D07", d="D07", name="Acceptance signature", title="Sign acceptance report", tab="Deliveries", next=chrome.next_block(ctx), ev=["Inspection 1", "Technical certificate 1"],
		regions=regions, p="" if pending else "Sign report", s2=[] if pending else ["Request correction", "Sign with dissent"])
	if not pending:
		b["actions"]["Sign report"] = kit.command("SignAcceptanceReport", acceptance=report.name)
		_correction_dialog(b, report)
		_dissent_dialog(b, report)
	return b


def _dissent_dialog(board: dict, report) -> None:
	"""A member's dissent from named units of the frozen report: signed, but not decided."""
	board["actions"]["Sign with dissent"] = kit.dialog("dissent")
	board["dialogs"]["dissent"] = kit.dlg("Sign with dissent", [kit.xh("Your signature stays on this exact report. The units you name are not decided: they are read again before they can be accepted or rejected."),
		kit.fl(kit.ta("Units you dissent from", "", "dissent_units", rows=4), kit.ta("Reason for your dissent", "", "dissent_reason"))], "Sign with dissent", command="SignAcceptanceReport", args={"acceptance": report.name})


def _correction_dialog(board: dict, report) -> None:
	"""D07's secondary action: the reason is required, and the request goes to the chair."""
	board["actions"]["Request correction"] = kit.dialog("correction")
	board["dialogs"]["correction"] = kit.dlg("Request correction", [kit.fl(kit.ta("Reason", "", "reason"))], "Send request", command="RequestAcceptanceCorrection", args={"acceptance": report.name})


def d07a(ctx: Context, version: int) -> dict:
	"""The Accounting Officer's decision on a committee's recommendation (authored, FU-CM-84): the report as every member signed it, with any dissent applied, and the choice to accept or send it back."""
	report = frappe.get_doc("Contract Acceptance", frappe.db.get_value("Contract Acceptance", {"contract_case": ctx.case, "version_no": version}, "name"))
	shown = frappe._dict(lines_json=records.dumps(delivery.decision_of(ctx.case, report)["lines"]), signers_json=report.signers_json, technical_certificate=report.technical_certificate)
	b = chrome.base(ctx, "D07-A", d="D07", name="Acceptance decision", title="Decide on acceptance", tab="Deliveries", next=chrome.next_block(ctx), ev=["Inspection 1", "Technical certificate 1"],
		regions=_report_regions(ctx, shown, signatures=True), p="Accept as recommended", s2=["Request correction"])
	b["actions"]["Accept as recommended"] = kit.command("DecideContractAcceptance", acceptance=report.name)
	_correction_dialog(b, report)
	return b


def _plural(item: str, quantity: int) -> str:
	return f"{quantity} {item.lower()}{'' if quantity == 1 else 's'}"


def d31(ctx: Context, number: int) -> dict:
	"""Required services: the technical certifier records the evidence of a performed related service (D31). A service has no stock or asset behind it, only a requirement, a deadline and evidence."""
	arrival = _arrival(ctx, number)
	items = records.loads(arrival.items_json, [])
	item = next(i for i in items if i.get("line_id"))
	lines = ctx.terms.get("lines", [])
	line = next(l for l in lines if l["line_id"] == item["line_id"])
	service = next((x for x in ctx.terms.get("services", []) if x.get("line_id") == line["line_id"]), {})
	unit = item["units"][0]
	inspection = delivery.current_inspection(ctx.case, arrival.name)
	found = records.loads(inspection.findings_json) if inspection else None
	given = {(o["unit"], o["criterion_id"]): o.get("value", "") for o in (records.loads(inspection.observations_json, []) if inspection else [])}
	criteria = delivery.criteria_for(ctx.terms, line["line_id"])
	goods = [l for l in lines if l.get("kind") != "service"]
	agreement = kit.R("Agreement", kit.f(*([["Goods", " · ".join(f"{_plural(l['item'], cint(l['quantity']))} · {money(l['amount'], ctx.terms.get('currency', 'KES'))}" for l in goods)]] if goods else []),
		["Service", f"{cint(line['quantity'])} {line['item'].lower()} {cstr_(line.get('uom')).lower()} · {money(line['amount'], ctx.terms.get('currency', 'KES'))}".replace("  ", " ")], ["Total", money(ctx.terms.get("total"), ctx.terms.get("currency", "KES"))]))
	required = kit.R("Required service", kit.r(["Requirement", service.get("requirement", "")], ["Deadline", formatdate(service["deadline"], "d MMM yyyy") if service.get("deadline") else ""],
		["Evidence required", service.get("evidence_required", "")]))
	names = {}
	fields = []
	for ci, c in enumerate(criteria):
		names[c["id"]] = f"obs.{unit}.{c['id']}"
		fields.append(kit.tx(c.get("label") or c["name"], str(given.get((unit, c["id"]), "")), names[c["id"]]))
	fields.append(kit.tx("Reference", unit, "service_reference"))
	result = found["units"][unit]["result"] if found and unit in found["units"] else "Needs review"
	observations = kit.R("Observations", kit.fl(*fields), kit.t(["Requirement", "Result"], [[line["item"], f"!{result}"]]))
	b = chrome.base(ctx, "D31", d="D31", name="Required services", title=f"Review {line['item'].lower()} completion", tab="Deliveries", next=chrome.next_block(ctx), regions=[agreement, required, observations],
		p="Save observations", s2=["View service requirement"], ev=["Agreement 1", unit])
	b["arrival"] = arrival.name
	b["actions"]["Save observations"] = kit.command("RecordInspectionObservations", arrival=arrival.name)
	b["actions"]["View service requirement"] = kit.dialog("requirement")
	b["dialogs"]["requirement"] = kit.dlg("Service requirement", [kit.r(["Requirement", service.get("requirement", "")], ["Deadline", formatdate(service["deadline"], "d MMM yyyy") if service.get("deadline") else ""],
		["Evidence required", service.get("evidence_required", "")], *[[c.get("label") or c["name"], f"{COMPARATOR_WORDS.get(c['comparator'], c['comparator'])} {c['value']} {c.get('unit', '')}".strip()] for c in criteria])], "", ["Close"], local=True)
	return b


def cstr_(value) -> str:
	return "" if value is None else str(value)


def report_is_service(ctx: Context, report) -> bool:
	"""A report whose every line is a service is signed on the service board."""
	lines = records.loads(report.lines_json, [])
	return bool(lines) and all(l["line_id"] in delivery.service_lines(ctx.terms) for l in lines)


def d31a(ctx: Context, version: int) -> dict:
	"""The frozen service acceptance report a required member signs (D31-A): each service line separately, with the invoice entitlement it creates and the absence of any stock or asset unit."""
	report = frappe.get_doc("Contract Acceptance", frappe.db.get_value("Contract Acceptance", {"contract_case": ctx.case, "version_no": version}, "name"))
	lines = records.loads(report.lines_json, [])
	by_line = {l["line_id"]: l for l in ctx.terms.get("lines", [])}
	name = {lid: (by_line[lid].get("item") or "") for lid in by_line}
	rows = [[name[l["line_id"]] or l["item"], f"{l['arrived']} {cstr_(by_line[l['line_id']].get('uom')).lower()}".strip(), str(l["accepted"]), str(l["deferred"])] for l in lines]
	entitled = sum(cint(l["accepted"]) * flt(by_line[l["line_id"]]["rate"]) for l in lines)
	cert = frappe.get_all("Contract Certificate", filters={"name": ["in", (report.technical_certificate or "").split(",")]}, fields=["signer", "signed_at"], limit=1)
	signers = records.loads(report.signers_json, [])
	roles = {m["user"].lower(): ("Chair" if m["capacity"] == "Chair" else f"{m.get('role_label') or ''} member".strip().capitalize() if m.get("role_label") else "Member") for m in ctx.appointment["members"]}
	regions = [kit.R("Report lines", kit.t(["Line", "Quantity", "Accepted", "Deferred"], rows, [2, 3])),
		kit.R("Technical evidence", kit.x(f"Technical certificate signed by {ctx.name(cert[0].signer)}, {when(cert[0].signed_at)}" if cert else "Technical certificate")),
		kit.R("Signatures", kit.t(["Signer", "Role", "Status"], [[s["name"], roles.get(s["user"].lower(), s["capacity"]), "!Signed with dissent" if s["state"] == "Signed" and s.get("dissent") else "!Signed" if s["state"] == "Signed" else "!Awaiting signature"] for s in signers])),
		kit.R("", kit.xh(f"Invoice entitlement for the service is {money(entitled)}, once. No stock or asset unit is created for a {(name[lines[0]['line_id']] or lines[0]['item']).lower()} service." if lines else ""))]
	b = chrome.base(ctx, "D31-A", d="D31", name="Required services", title="Sign acceptance report", tab="Deliveries", next=chrome.next_block(ctx), regions=regions, p="Sign report", s2=["Request correction", "Sign with dissent"], ev=["Agreement 1"])
	b["actions"]["Sign report"] = kit.command("SignAcceptanceReport", acceptance=report.name)
	_correction_dialog(b, report)
	_dissent_dialog(b, report)
	return b


def _correction_asked(ctx: Context) -> dict | None:
	"""For the chair preparing again: the latest report was sent back, and why."""
	latest = frappe.get_all("Contract Acceptance", filters={"contract_case": ctx.case}, fields=["state", "correction_reason", "version_no"], order_by="version_no desc", limit=1)
	if not latest or latest[0].state != "Superseded" or not latest[0].correction_reason:
		return None
	return kit.R("Correction requested", kit.r([f"Report {latest[0].version_no}", latest[0].correction_reason]))


def deliveries_summary(ctx: Context) -> dict:
	"""The Deliveries tab when the viewer has no delivery step to take: what arrived and where each unit stands."""
	lines = ctx.position["lines"].values()
	arrivals = [[a["delivery_reference"], when(a["received_at"]), str(sum(i["quantity"] for i in a["items"])), a["destination"] or ""] for a in ctx.arrivals]
	regions = [kit.R("Delivery position", kit.t(["Item", "Ordered", "Arrived", "Accepted", "Rejected", "Awaiting decision", "Remaining"],
		[[l["item"], str(l["ordered"]), str(l["arrived"]), str(l["accepted"]), str(l["rejected"] + l["returned"]), str(l["pending_decision"] + l["deferred"]), str(l["remaining"])] for l in lines], [1, 2, 3, 4, 5, 6]))]
	regions.append(kit.R("Arrivals", kit.t(["Delivery", "Received", "Units", "Destination"], arrivals, [2])) if arrivals else kit.R("Arrivals", kit.xh("No goods have arrived yet.")))
	exceptions = _exceptions_rows(ctx)
	if exceptions:
		regions.append(kit.R("Delivery exceptions", kit.t(["Delivery", "Exception", "Detail", "Status"], exceptions)))
	b = chrome.base(ctx, "D04-S", d="D04", name="Deliveries", title="Deliveries", tab="Deliveries", next=chrome.next_block(ctx), regions=regions, ev=[])
	if ctx.doc.lifecycle == "Active" and "receiver" in ctx.audiences:
		b["p"] = "Record delivery"
		b["actions"]["Record delivery"] = kit.route(ctx.case, "deliveries", "record-delivery")
		waiting = [u["unit"] for u in ctx.position["units"].values() if u["status"] in ("Rejected", "Excess")]
		b["s2"] = ["Record unexpected goods"]
		b["actions"]["Record unexpected goods"] = kit.dialog("unexpected")
		b["dialogs"]["unexpected"] = kit.dlg("Record unexpected goods", [kit.xh("Goods no line of the contract names are recorded and held apart. They are not inspected or accepted."),
			kit.fl(kit.tx("Supplier delivery reference", "", "supplier_reference"), kit.dt("Received at", "", "received_at", time=True), kit.tx("Destination", (ctx.terms.get("delivery") or {}).get("destination", ""), "destination"),
				kit.tx("Description", "", "unexpected_description"), kit.tx("Quantity", "", "unexpected_quantity"), kit.ta("Unit references", "", "unexpected_units", rows=4))], "Record goods", command="RecordContractArrival", args={})
		if waiting:  # rejected or surplus units still in custody: the receiver records the supplier's collection (section 5.4)
			b["s2"] = ["Record collection of rejected units", "Record unexpected goods"]
			b["actions"]["Record collection of rejected units"] = kit.dialog("collect")
			b["dialogs"]["collect"] = kit.dlg("Record collection", [kit.xh("Rejected and surplus units are collected by the supplier, with the supplier's collection evidence."), kit.fl(kit.ta("Units collected", "\n".join(waiting), "units", rows=6),
				kit.tx("Collection evidence", "", "evidence"))], "Record collection", command="RecordCustodyReturn", args={})
	return b


def _exceptions_rows(ctx: Context) -> list[list[str]]:
	rows = []
	resolved = {}
	for event in frappe.get_all("Contract Event", filters={"contract_case": ctx.case, "event_type": "Delivery exception resolved"}, fields=["detail_json"]):
		detail = records.loads(event.detail_json)
		resolved[detail.get("arrival")] = detail.get("disposition", "Resolved")
	for a in ctx.arrivals:
		found = records.loads(frappe.db.get_value("Contract Arrival", a["name"], "exceptions_json") or "[]", [])
		for e in found:
			detail = {"Excess": f"{e.get('quantity')} beyond the contract: {len(e.get('units') or [])} named", "Unexpected": f"{e.get('quantity')} {e.get('item')}", "Premature": e.get("reason", ""),
				"Ambiguous": f"Reference {e.get('reference')} was used for {e.get('earlier')}"}.get(e["kind"], "")
			rows.append([a["delivery_reference"], e["kind"], detail, f"!{resolved.get(a['name'], 'Open')}"])
	return rows


def resolve_dialog(board: dict, arrival: str) -> None:
	"""HOP's step on a delivery with exceptions: record what became of them."""
	board["dialogs"]["resolve"] = kit.dlg("Record what became of it", [kit.fl(kit.sel("What became of it", "Separate delivery", ["Separate delivery", "Duplicate delivery note", "To be collected by the supplier",
		"Awaiting the supplier's instruction"], "disposition"), kit.ta("Reason", "", "reason"))], "Record", command="ResolveDeliveryException", args={"arrival": arrival})
	board["actions"]["Record what became of it"] = kit.dialog("resolve")
	board["p"] = "Record what became of it"
