# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Deliveries tab: arrival, inspection, technical certificate and acceptance (boards D04, D05, D19, D06, D07, D07-P; CM-CHG-001 v0.8 section 10)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, formatdate

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
		cells = [(found["units"][u]["criteria"][c["id"]]) for u in units] if found else []
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


def d05(ctx: Context, number: int) -> dict:
	"""Inspect delivery (an appointed, declared inspector)."""
	arrival = _arrival(ctx, number)
	inspection = delivery.current_inspection(ctx.case, arrival.name)
	found = records.loads(inspection.findings_json) if inspection else None
	items = records.loads(arrival.items_json, [])
	units = [u for i in items for u in i.get("units", [])]
	criteria = ctx.terms.get("criteria") or []
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
	return b


def d19(ctx: Context, number: int) -> dict:
	"""Confirm technical inspection (the technical certifier)."""
	arrival = _arrival(ctx, number)
	inspection = delivery.current_inspection(ctx.case, arrival.name)
	found = records.loads(inspection.findings_json)
	good = [u for u, f in found["units"].items() if f["result"] == "Meets"]
	bad = [u for u, f in found["units"].items() if f["result"] == "Does not meet"]
	failed_checks = sorted({c["name"] for u in bad for c in [{"name": cid} for cid, v in found["units"][u]["criteria"].items() if v["result"] == "Does not meet"]})
	names = {c["id"]: c["name"] for c in ctx.terms.get("criteria", [])}
	tests = ", ".join(f"{c['name']} {c['comparator']} {c['value']}{(' ' + c['unit']) if c.get('unit') else ''}" for c in ctx.terms.get("criteria", []))
	failed = "; ".join(f"{u}: " + ", ".join(names[cid] for cid, v in found["units"][u]["criteria"].items() if v["result"] == "Does not meet") for u in bad) or "None"
	ao = ctx.name(next(iter(work.holders("Accounting Officer")), ""))
	b = chrome.base(ctx, "D19", d="D19", name="Technical certificate", title="Confirm technical inspection", tab="Deliveries", next=chrome.next_block(ctx), ev=[f"Inspection {inspection.version_no}"],
		regions=[kit.R(f"Technical certificate {number}", kit.r(["Contract", ctx.doc.contract_id], ["Inspected", str(len(found["units"]))], ["Conforms", str(len(good))], ["Fails", str(len(bad))], ["Missing evidence", "0"], ["Tests", tests],
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
	sigs = kit.R("Signatures", kit.t(["Signer", "Role", "Status", "Signed"], [[s["name"], s["capacity"], "!Signed" if s["state"] == "Signed" else "!Awaiting signature", when(s["signed_at"]) if s["signed_at"] else "—"] for s in signers]))
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
	lines = []
	units = {"accepted": [], "rejected": [], "deferred": []}
	reasons = {}
	for u, f in found["units"].items():
		if u in prior:
			continue
		key = "accepted" if f["result"] == "Meets" else "rejected" if f["result"] == "Does not meet" else "deferred"
		units[key].append(u)
		if key == "rejected":
			reasons[u] = "; ".join(c["reason"] for c in f["criteria"].values() if c["reason"])
	draft = frappe._dict(lines_json=records.dumps([{"arrived": sum(len(v) for v in units.values()), "units": units, "reasons": reasons}]), signers_json=records.dumps([m for m in ctx.appointment["members"]]), technical_certificate="")
	draft.signers_json = records.dumps([{"name": m["name"], "capacity": m["capacity"], "state": "Awaiting", "signed_at": ""} for m in ctx.appointment["members"]])
	cert = delivery._certificate_for(ctx.case, number)
	draft.technical_certificate = cert.name if cert else ""
	b = chrome.base(ctx, "D06", d="D06", name="Acceptance review", title="Review inspection", tab="Deliveries", next=chrome.next_block(ctx), ev=[f"Inspection {delivery.current_inspection(ctx.case, arrival.name).version_no}"],
		regions=_report_regions(ctx, draft, signatures=False), p="Prepare report for signing")
	b["actions"]["Prepare report for signing"] = kit.command("PrepareAcceptanceReport", arrivals=[arrival.name])
	return b


def d07(ctx: Context, version: int, *, pending: bool = False) -> dict:
	"""Acceptance signature: a required member signs the exact frozen report. D07-P: signed, the stock update is pending."""
	report = frappe.get_doc("Contract Acceptance", frappe.db.get_value("Contract Acceptance", {"contract_case": ctx.case, "version_no": version}, "name"))
	regions = _report_regions(ctx, report, signatures=True)
	if pending:
		regions = [r for r in regions if r["t"] not in ("Units that do not meet", "Technical evidence")]
	b = chrome.base(ctx, "D07-P" if pending else "D07", d="D07", name="Acceptance signature", title="Sign acceptance report", tab="Deliveries", next=chrome.next_block(ctx), ev=["Inspection 1", "Technical certificate 1"],
		regions=regions, p="" if pending else "Sign report")
	if not pending:
		b["actions"]["Sign report"] = kit.command("SignAcceptanceReport", acceptance=report.name)
	return b


def deliveries_summary(ctx: Context) -> dict:
	"""The Deliveries tab when the viewer has no delivery step to take: what arrived and where each unit stands."""
	lines = ctx.position["lines"].values()
	arrivals = [[a["delivery_reference"], when(a["received_at"]), str(sum(i["quantity"] for i in a["items"])), a["destination"] or ""] for a in ctx.arrivals]
	regions = [kit.R("Delivery position", kit.t(["Item", "Ordered", "Arrived", "Accepted", "Rejected", "Awaiting decision", "Remaining"],
		[[l["item"], str(l["ordered"]), str(l["arrived"]), str(l["accepted"]), str(l["rejected"] + l["returned"]), str(l["pending_decision"] + l["deferred"]), str(l["remaining"])] for l in lines], [1, 2, 3, 4, 5, 6]))]
	regions.append(kit.R("Arrivals", kit.t(["Delivery", "Received", "Units", "Destination"], arrivals, [2])) if arrivals else kit.R("Arrivals", kit.xh("No goods have arrived yet.")))
	b = chrome.base(ctx, "D04-S", d="D04", name="Deliveries", title="Deliveries", tab="Deliveries", next=chrome.next_block(ctx), regions=regions, ev=[])
	if ctx.doc.lifecycle == "Active" and "receiver" in ctx.audiences:
		b["p"] = "Record delivery"
		b["actions"]["Record delivery"] = kit.route(ctx.case, "deliveries", "record-delivery")
		waiting = [u["unit"] for u in ctx.position["units"].values() if u["status"] == "Rejected"]
		if waiting:  # rejected units still in custody: the receiver records the supplier's collection (section 5.4)
			b["s2"] = ["Record collection of rejected units"]
			b["actions"]["Record collection of rejected units"] = kit.dialog("collect")
			b["dialogs"]["collect"] = kit.dlg("Record collection", [kit.xh("Rejected units are collected by the supplier, with the supplier's collection evidence."), kit.fl(kit.ta("Units collected", "\n".join(waiting), "units", rows=6),
				kit.tx("Collection evidence", "", "evidence"))], "Record collection", command="RecordCustodyReturn", args={})
	return b
