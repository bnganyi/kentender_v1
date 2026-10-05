# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The executed year's portfolio (two-year seed world proposal §5; owner,
4 Oct 2026: "Decisions for the owner: recommendations accepted", D4).

Beside the canonical laptops Tender (T1), FY 2026/27's Active plan carries
eleven more IT-equipment items. Each one is a Requisition and, for ten of
them, a Tender, built through the owning modules' real commands as the named
actors at its own instants, and each stops at its own state at the as-at
instant (18 Jun 2027, 10:00 EAT), so Home and Analytics have many records in
different states at one moment:

=====  =====================================  =========================================================
Ref    Tender                                 State at the as-at instant
=====  =====================================  =========================================================
T2     Supply of printers                     report delivered; professional opinion pending (Charles)
T3     Supply of laboratory desktop computers opinion signed; award decision pending (Amina)
T4     Supply of document scanners            opening taken up; committee review outstanding
T5     Supply of network switches             opening complete; committee not appointed (Amina)
T6     Supply of medical-grade tablets        open for bids; six clarifications; opening arranged
T7     Supply of UPS units                    approved; publication decision pending (Amina)
T8     Supply of wireless access points       returned to Brian for the warranty correction
T9     Supply of field laptops                cancellation recommended; Amina to consider it
T10    Supply of desktop computers            cancelled; compliance evidence pending
T11    Supply of core network routers         cancelled; compliance evidence complete
—      Clinic desktop computers (Req only)    submitted to Procurement; authorisation pending (Charles)
—      Monitors (Req only)                    authorised; not yet taken up by a Tender
=====  =====================================  =========================================================

The only installed Tender format is straightforward off-the-shelf IT
equipment (REQ_PRODUCT_UNSUPPORTED / TND_PRODUCT_UNSUPPORTED otherwise: Tenders
admits Laptop, Desktop computer, Tablet, Monitor, Printer, Scanner, Network
equipment and Power-protection equipment), so the HOME/ANL fixture titles it
cannot carry (office desks, hospital beds, laboratory analysers, clinic
equipment, IT peripherals, servers) have IT substitutes. Afya Digital Supplies Limited and Jirani Office Supplies
Limited bid on T2–T5; all four canonical suppliers register as candidates on
T6. Every stage obeys the executed year's CURRENT cap (plan D5): a record
stops where the cap leaves it."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import frappe

DHI = "Digital Health"
HRMD = "Human Resources Management and Development"
LATEST_DELIVERY = "2027-06-30"  # each item's plan boundary (required by 30 Jun 2027)


def _plus(instant: str, **delta: int) -> str:
	return (datetime.fromisoformat(instant) + timedelta(**delta)).strftime("%Y-%m-%d %H:%M:%S")


def _req_clock(day: str, submitted: str, authorised: str = "") -> dict[str, str]:
	return {
		"draft_opened": f"{day} 09:00:00", "steps_completed": f"{day} 10:30:00", "sent_for_department_approval": f"{day} 10:45:00",
		"submitted_to_procurement": submitted, "authorised": authorised,
	}


def _tender_clock(start: str, submit: str, approve: str = "", published: str = "", deadline: str = "", **extra: str) -> dict[str, str]:
	clock = {"start": start, "submit": submit, "approve": approve, **extra}
	if published:
		day = published[:10]
		clock.update({
			"authorise": f"{day} 07:55:00", "available_at": f"{day} 08:00:00",
			**{f"confirm_{i}": f"{day} 08:0{m}:00" for i, m in ((1, 3), (2, 4), (3, 6), (4, 7))},
		})
	if deadline:
		clock["close"] = deadline
	return clock


def _values(title: str, published: str, deadline: str, security: int, **extra: Any) -> dict[str, Any]:
	day = published[:10]
	return {
		"tender_title": title, "issue_date": day, "clarification_deadline": f"{(datetime.fromisoformat(day) + timedelta(days=10)).date()} 17:00:00",
		"submission_deadline": deadline, "tender_security_amount": float(security), **extra,
	}


def _opening_clock(deadline: str, bids: int) -> dict[str, Any]:
	"""The ceremony at the deadline, appointed three days before."""
	appoint_day = (datetime.fromisoformat(deadline) - timedelta(days=3)).strftime("%Y-%m-%d")
	opens = [(_plus(deadline, minutes=1 + 2 * i), _plus(deadline, minutes=1 + 2 * i, seconds=30), _plus(deadline, minutes=1 + 2 * i, seconds=45)) for i in range(bids)]
	end = _plus(deadline, minutes=2 * bids + 2)
	return {
		"prepare": f"{appoint_day} 10:10:00", "appoint": f"{appoint_day} 10:15:00", "publish": f"{appoint_day} 10:20:00",
		"join": (_plus(deadline, minutes=-5), _plus(deadline, minutes=-4), _plus(deadline, minutes=-3)),
		"receive": _plus(deadline, seconds=5), "begin": _plus(deadline, seconds=12), "open": opens,
		"end": end, "freeze": _plus(end, minutes=1, seconds=30), "sign": (_plus(end, minutes=2, seconds=30), _plus(end, minutes=3, seconds=30), _plus(end, minutes=5)),
	}


def _evaluation_clock(deadline: str, bids: int, *, review: str = "", meeting: str = "", sent: str = "") -> dict[str, Any]:
	"""Prepared and appointed the day before the opening; the opening taken up
	when its last signature is in; the reviews, the discussion and the report
	at the story's instants (`sent` is the last signature, which delivers it)."""
	day_before = (datetime.fromisoformat(deadline) - timedelta(days=1)).strftime("%Y-%m-%d")
	opening_signed = _opening_clock(deadline, bids)["sign"][-1]
	clock: dict[str, Any] = {
		"prepare": f"{day_before} 08:58:00", "appoint": f"{day_before} 09:00:00", "secretary": f"{day_before} 09:05:00",
		"declare": (f"{day_before} 09:10:00", f"{day_before} 09:12:00", f"{day_before} 09:14:00"), "intake": _plus(opening_signed, seconds=3),
	}
	if sent:
		clock.update({
			"review": review, "start": meeting, "join": (_plus(meeting, minutes=2), _plus(meeting, minutes=3)), "basis": _plus(meeting, minutes=5),
			"end": _plus(meeting, minutes=6), "narrative": _plus(sent, minutes=-12), "freeze": _plus(sent, minutes=-7),
			"sign": (_plus(sent, minutes=-2), _plus(sent, minutes=-1), sent),
		})
	return clock


def _bid_clock(start: str, fill: str, intake: str, complete: str, submit: str) -> dict[str, str]:
	return {"start": start, "fill": fill, "intake": intake, "complete": complete, "submit": submit}


def _two_bids(category_models: tuple[str, str], prices: tuple[str, str], quantity: int, day: str, deadline: str, n: int) -> list[dict[str, Any]]:
	"""Afya and Jirani each start, fill and submit before the deadline (16% tax
	on the quantity at each unit price); every security reference its own."""
	deadline_day = deadline[:10]
	submit_day = (datetime.fromisoformat(deadline_day) - timedelta(days=3)).strftime("%Y-%m-%d")
	out = []
	for index, (key, model, unit_price, delivery) in enumerate((("afya", category_models[0], prices[0], "2027-06-24"), ("jirani", category_models[1], prices[1], "2027-06-28"))):
		tax = int(int(unit_price) * quantity * 16 / 100)
		out.append({
			"bidder": key,
			"clock": _bid_clock(f"{day} {10 + index}:00:00", f"{day} {11 + index}:30:00", f"{submit_day} 0{9 + index}:00:00" if index == 0 else f"{submit_day} 10:30:00",
				f"{submit_day} {11 + index}:00:00", f"{submit_day} {14 + index}:15:00"),
			"goods": {"offered_make_model": model, "offered_delivery_date": delivery},
			"price": {"unit_price": unit_price, "tax_amount": str(tax)},
			"security": {"guarantee_reference": f"{'KCB/TG' if key == 'afya' else 'EQ/BG'}/2027/{n}{index}"},
		})
	return out


CANCELLATION_REASON = (
	"The requirement has been met through a donor-funded supply received this month, so the procurement need has ceased."
)
SERVER_CANCELLATION_REASON = (
	"The routers will be provided under the national government data-centre programme, so the Ministry's procurement need has ceased."
)
WARRANTY_RETURN = "State the warranty period required from suppliers."
T6_QUESTIONS = (
	"Do the tablets need a stylus, or is touch input enough?",
	"May we offer a tablet with a 10.1-inch display instead of 11 inches?",
	"Is a rugged case required for every tablet?",
	"Must the tablets support LTE, or is Wi-Fi only acceptable?",
	"Will delivery be to one site or to each priority facility?",
	"Is device-management software to be priced separately?",
)

#: The portfolio, by Plan Item (two-year seed world proposal §5.1–§5.2). Plan
#: Item titles and departments come from Planning's own seed
#: (`procurement_planning.seeds.kentender_mvp_v1.PORTFOLIO`).
PORTFOLIO: tuple[dict[str, Any], ...] = (
	{
		"key": "printers", "ref": "T2", "item": "Printers", "category": "Printer", "item_name": "Network laser printers",
		"uses": {DHI: "Printing for Digital Health offices"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-03-01", "2027-03-02 09:00:00", "2027-03-12 11:00:00")},
		"tender": {
			"stop": "closed", "clock": _tender_clock("2027-03-16 10:00:00", "2027-03-16 15:00:00", "2027-03-25 10:00:00", "2027-04-09", "2027-05-10 12:00:00"),
			"values": _values("Supply of printers", "2027-04-09", "2027-05-10 12:00:00", 100_000),
		},
		"bids": _two_bids(("OfficeJet Pro 9130", "LaserWorks 4200"), ("100000", "105000"), 40, "2027-04-20", "2027-05-10 12:00:00", 21),
		"evaluation": {"stop": "report_sent", "reference": "011", "clock": _evaluation_clock(
			"2027-05-10 12:00:00", 2, review="2027-05-24 09:00:00", meeting="2027-06-16 09:00:00", sent="2027-06-16 11:30:00")},
		"award": {"through": "received", "clock": {}},
	},
	{
		"key": "lab_desktops", "ref": "T3", "item": "Laboratory desktop computers", "category": "Desktop computer", "item_name": "Laboratory desktop computers",
		"uses": {DHI: "Running hospital laboratory systems"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-03-02", "2027-03-04 09:00:00", "2027-03-11 11:00:00")},
		"tender": {
			"stop": "closed", "clock": _tender_clock("2027-03-17 10:00:00", "2027-03-17 15:00:00", "2027-03-24 10:00:00", "2027-04-06", "2027-05-07 12:00:00"),
			"values": _values("Supply of laboratory desktop computers", "2027-04-06", "2027-05-07 12:00:00", 180_000),
		},
		"bids": _two_bids(("ProDesk 600 G9", "Vertex Tower 5"), ("125000", "128000"), 60, "2027-04-15", "2027-05-07 12:00:00", 31),
		"evaluation": {"stop": "report_sent", "reference": "012", "clock": _evaluation_clock(
			"2027-05-07 12:00:00", 2, review="2027-05-20 09:00:00", meeting="2027-06-04 09:00:00", sent="2027-06-04 15:00:00")},
		"award": {"through": "signed", "clock": {"opinion": "2027-06-17 15:30:00", "sign": "2027-06-17 16:00:00"}},
	},
	{
		"key": "scanners", "ref": "T4", "item": "Document scanners", "category": "Scanner", "item_name": "Document scanners",
		"uses": {HRMD: "Digitising staff records in Human Resources"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-03-03", "2027-03-03 15:00:00", "2027-03-15 12:00:00")},
		"tender": {
			"stop": "closed", "clock": _tender_clock("2027-03-18 10:00:00", "2027-03-18 15:00:00", "2027-04-01 10:00:00", "2027-04-16", "2027-06-03 10:00:00"),
			"values": _values("Supply of document scanners", "2027-04-16", "2027-06-03 10:00:00", 70_000),
		},
		"bids": _two_bids(("ScanPro 3000", "DocuFeed 750"), ("115000", "118000"), 25, "2027-05-17", "2027-06-03 10:00:00", 41),
		"evaluation": {"stop": "intake", "reference": "013", "clock": _evaluation_clock("2027-06-03 10:00:00", 2)},
	},
	{
		"key": "switches", "ref": "T5", "item": "Network switches", "category": "Network equipment", "item_name": "Managed network switches",
		"uses": {HRMD: "Networking the staff training centres"},
		# a partial draw: 25 of the item's 30 switches
		"amounts": {HRMD: ("25", "7500000.00")},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-03-03", "2027-03-08 10:00:00", "2027-03-15 11:30:00")},
		"tender": {
			"stop": "closed", "clock": _tender_clock("2027-03-19 09:00:00", "2027-03-19 15:00:00", "2027-04-02 10:00:00", "2027-05-14", "2027-06-14 11:00:00"),
			"values": _values("Supply of network switches", "2027-05-14", "2027-06-14 11:00:00", 150_000),
		},
		"bids": _two_bids(("NetCore 2930F", "SwitchLine 48G"), ("250000", "255000"), 25, "2027-05-25", "2027-06-14 11:00:00", 51),
		"evaluation": {"stop": "prepared", "reference": "014", "clock": _evaluation_clock("2027-06-14 11:00:00", 2)},
	},
	{
		"key": "tablets", "ref": "T6", "item": "Medical-grade tablets", "category": "Tablet", "item_name": "Medical-grade tablets",
		"uses": {DHI: "Clinical teams at priority facilities"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-04-14", "2027-04-16 09:00:00", "2027-04-20 11:00:00")},
		"tender": {
			"stop": "published", "clock": _tender_clock("2027-04-22 10:00:00", "2027-04-22 15:00:00", "2027-05-06 10:00:00", "2027-05-24", "2027-06-25 11:00:00"),
			"values": _values("Supply of medical-grade tablets", "2027-05-24", "2027-06-25 11:00:00", 120_000, clarification_deadline="2027-06-18 17:00:00"),
		},
		# the four canonical suppliers start bids (Drafts), so they are candidates
		"candidates": (
			("afya", "2027-05-26 10:00:00"), ("jirani", "2027-05-27 10:00:00"), ("pwani", "2027-05-31 09:00:00"), ("mlima", "2027-06-01 11:00:00"),
		),
		"clarifications": tuple(zip(
			("afya", "jirani", "pwani", "mlima", "afya", "jirani"), T6_QUESTIONS,
			("2027-06-02 10:00:00", "2027-06-04 14:00:00", "2027-06-08 09:30:00", "2027-06-10 11:00:00", "2027-06-15 15:00:00", "2027-06-17 09:00:00"),
		)),
		# the opening committee appointed; the chair's Start opening is upcoming
		"opening": {"arranged_only": True, "clock": {"prepare": "2027-06-15 09:55:00", "appoint": "2027-06-15 10:00:00", "publish": "2027-06-15 10:05:00"}},
	},
	{
		"key": "ups", "ref": "T7", "item": "UPS units", "category": "Power-protection equipment", "item_name": "Line-interactive UPS units",
		"uses": {HRMD: "Power protection in the training centres"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-05-03", "2027-05-05 09:00:00", "2027-05-10 11:00:00")},
		"tender": {
			"stop": "approved", "clock": _tender_clock("2027-05-12 10:00:00", "2027-06-08 10:00:00", "2027-06-16 15:30:00"),
			"values": _values("Supply of UPS units", "2027-06-21", "2027-07-12 11:00:00", 80_000),
		},
	},
	{
		"key": "access_points", "ref": "T8", "item": "Wireless access points", "category": "Network equipment", "item_name": "Indoor wireless access points",
		"uses": {DHI: "Wireless coverage in Digital Health offices", HRMD: "Wireless coverage in Human Resources offices"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-03-08", "2027-03-09 10:00:00", "2027-03-15 11:00:00")},
		"tender": {
			"stop": "returned", "clock": _tender_clock("2027-03-16 09:00:00", "2027-06-14 10:00:00", **{"return": "2027-06-16 09:00:00"}),
			"values": _values("Supply of wireless access points", "2027-06-28", "2027-07-19 11:00:00", 130_000),
			"return_reason": WARRANTY_RETURN,
		},
	},
	{
		"key": "field_laptops", "ref": "T9", "item": "Field laptops", "category": "Laptop", "item_name": "Rugged field laptops",
		"uses": {DHI: "County digital health officers in the field"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-04-05", "2027-04-07 09:00:00", "2027-04-12 11:00:00")},
		"tender": {
			"stop": "cancellation_recommended",
			"clock": _tender_clock("2027-04-13 10:00:00", "2027-04-13 15:00:00", "2027-04-27 10:00:00", "2027-05-10", "2027-06-21 11:00:00", recommend_cancellation="2027-06-16 14:00:00"),
			"values": _values("Supply of field laptops", "2027-05-10", "2027-06-21 11:00:00", 140_000),
			"cancellation_reason": CANCELLATION_REASON,
		},
	},
	{
		"key": "desktops", "ref": "T10", "item": "Desktop computers", "category": "Desktop computer", "item_name": "Office desktop computers",
		"uses": {HRMD: "Human Resources offices"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-03-15", "2027-03-17 09:00:00", "2027-03-22 11:00:00")},
		"tender": {
			"stop": "cancelled",
			"clock": _tender_clock("2027-03-24 10:00:00", "2027-03-24 15:00:00", "2027-04-07 10:00:00", "2027-04-26", "2027-06-28 11:00:00",
				recommend_cancellation="2027-06-14 10:00:00", cancel="2027-06-15 12:00:00"),
			"values": _values("Supply of desktop computers", "2027-04-26", "2027-06-28 11:00:00", 240_000),
			"cancellation_reason": CANCELLATION_REASON,
		},
	},
	{
		"key": "routers", "ref": "T11", "item": "Core network routers", "category": "Network equipment", "item_name": "Core network routers",
		"uses": {DHI: "The national digital health data centre"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-03-01", "2027-03-01 15:00:00", "2027-03-15 14:00:00")},
		"tender": {
			"stop": "cancelled",
			"clock": _tender_clock("2027-03-17 09:00:00", "2027-03-17 15:00:00", "2027-03-31 10:00:00", "2027-04-12", "2027-06-30 11:00:00",
				recommend_cancellation="2027-06-14 09:00:00", cancel="2027-06-16 12:00:00"),
			"values": _values("Supply of core network routers", "2027-04-12", "2027-06-30 11:00:00", 500_000),
			"cancellation_reason": SERVER_CANCELLATION_REASON,
			# every obligation evidenced the same afternoon
			"evidence": {
				"NOTICE-STATE_PORTAL": ("2027-06-16 14:00:00", "PPIP-CANCEL-ROUTERS", "pdf"),
				"NOTICE-MINISTRY_WEBSITE": ("2027-06-16 14:05:00", "WEB-CANCEL-ROUTERS", "pdf"),
				"NOTICE-NOTICE_BOARD": ("2027-06-16 14:10:00", "NB-CANCEL-ROUTERS", "jpg"),
				"NOTICE-NATIONAL_NEWSPAPERS": ("2027-06-16 14:15:00", "NP-CANCEL-ROUTERS", "pdf"),
				"PPRA_REPORT": ("2027-06-16 15:00:00", "PPRA-CANCEL-ROUTERS", "pdf"),
				"CANDIDATE_NOTICE": ("2027-06-16 15:30:00", "CAND-CANCEL-ROUTERS", "pdf"),
			},
		},
	},
	{
		"key": "clinic_desktops", "ref": "R-clinic", "item": "Clinic desktop computers", "category": "Desktop computer", "item_name": "Clinic desktop computers",
		"uses": {DHI: "Outpatient clinic registration desks"},
		"requisition": {"stop": "procurement", "clock": _req_clock("2027-06-14", "2027-06-16 11:00:00")},
	},
	{
		"key": "monitors", "ref": "R-monitors", "item": "Monitors", "category": "Monitor", "item_name": "24-inch office monitors",
		"uses": {HRMD: "Human Resources offices"},
		"requisition": {"stop": "authorised", "clock": _req_clock("2027-06-01", "2027-06-03 09:00:00", "2027-06-10 11:00:00")},
	},
)


def _reaches(stage: str, current: str) -> bool:
	from kentender_core.seeds.canonical import CURRENT_STAGES

	return CURRENT_STAGES.index(current) >= CURRENT_STAGES.index(stage)


def _requisition(spec: dict[str, Any]) -> str:
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import _plan_item_id

	plan_item = _plan_item_id(spec["item"])
	return frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item, "current_state": ("not in", ("Withdrawn", "Revoked", "Superseded"))}, "name") if plan_item else ""


def _tender_stop(spec: dict[str, Any], current: str) -> str:
	"""The Tender's stop under the cap: the bid stages after `tenders` close a
	Tender whose story closes; at `tenders` it still closes, with no bids."""
	return spec["tender"]["stop"]


def seed_portfolio(*, current: str) -> dict[str, Any]:
	"""Every portfolio item as far as `current` lets it go. Idempotent."""
	from kentender_procurement.award.seeds.kentender_mvp_v1 import award_portfolio_tender
	from kentender_procurement.bid_evaluation.seeds.kentender_mvp_v1 import evaluate_portfolio_tender
	from kentender_procurement.bid_opening.seeds.kentender_mvp_v1 import open_portfolio_tender
	from kentender_procurement.bid_submission.seeds import kentender_mvp_v1 as bids
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import DELIVERY_LOCATION, build_requisition
	from kentender_procurement.tenders.seeds import kentender_mvp_v1 as tenders

	out: dict[str, Any] = {}
	if not _reaches("requisitions", current):
		return out
	for spec in PORTFOLIO:
		key = spec["key"]
		row: dict[str, Any] = out.setdefault(key, {})
		row["requisition"] = build_requisition(
			key=f"portfolio-{key}", plan_item_title=spec["item"], requirement_title=spec["item"],
			shared={"equipment_category": spec["category"], "item_name": spec["item_name"], "delivery_location": DELIVERY_LOCATION, "latest_delivery_date": LATEST_DELIVERY},
			uses=spec["uses"], clock_map=spec["requisition"]["clock"], stop=spec["requisition"]["stop"], amounts=spec.get("amounts"),
		)
		if not spec.get("tender") or not _reaches("tenders", current):
			continue
		story = {**spec["tender"], "key": key, "requisition": row["requisition"]["requisition"], "stop": _tender_stop(spec, current)}

		def interleave(step: str, *, tender: str, tender_reference: str, spec=spec) -> Any:
			if not _reaches("bid_submission", current):
				return None
			if step == "published" and spec.get("candidates"):
				candidates = {}
				for bidder, at in spec["candidates"]:
					started = bids.portfolio_bid(
						tender=tender, tender_reference=tender_reference, bidder_key=bidder, clock_map={"start": at, "fill": _plus(at, minutes=30)},
						goods={"offered_make_model": "MedTab 11 Pro", "offered_delivery_date": "2027-06-30"}, price={}, submit=False,
					)
					candidates[bidder] = started.get("candidate") or _candidate_of(tender, bidder)
				tenders.receive_portfolio_clarifications(tender, [(candidates[b], q, at) for b, q, at in spec["clarifications"]], key=spec["key"])
				return candidates
			if step == "before_close" and spec.get("bids"):
				return [
					bids.portfolio_bid(tender=tender, tender_reference=tender_reference, bidder_key=b["bidder"], clock_map=b["clock"], goods=b["goods"], price=b["price"], security=b["security"])
					for b in spec["bids"]
				]
			if step == "closed" and spec.get("bids"):
				return bids.close_portfolio_box(tender, spec["tender"]["clock"]["close"])
			return None

		row["tender"] = tenders.build_tender(story, interleave=interleave)
		tender = row["tender"]["tender"]
		if row["tender"].get("idempotent") and _reaches("bid_submission", current) and _missing_bid_story(spec, tender):
			# A Tender told without its bids (a run at CURRENT=tenders) cannot be
			# given them afterwards — its Requisition's hand-off is consumed once.
			frappe.throw(
				f"The portfolio Tender {tender} ({spec['ref']}) was seeded without its bid lifecycle.", exc=tenders.CanonicalTenderNeedsRebuild,
			)
		if spec.get("opening") and _reaches("bid_opening", current) and spec["opening"].get("arranged_only"):
			row["opening"] = open_portfolio_tender(tender, spec["opening"]["clock"], 0)
		if spec.get("evaluation") and _reaches("bid_opening", current):
			row["opening"] = open_portfolio_tender(tender, _opening_clock(spec["tender"]["clock"]["close"], len(spec["bids"])), len(spec["bids"]))
		if spec.get("evaluation") and _reaches("bid_evaluation", current):
			row["evaluation"] = evaluate_portfolio_tender(
				tender, spec["evaluation"]["clock"], stop=spec["evaluation"]["stop"], reference=spec["evaluation"]["reference"], summary=_summary(spec),
			)
		if spec.get("award") and _reaches("award", current):
			row["award"] = award_portfolio_tender(tender, through=spec["award"]["through"], clock_map=spec["award"]["clock"])
	return out


def _missing_bid_story(spec: dict[str, Any], tender: str) -> bool:
	if spec.get("bids"):
		return frappe.db.count("Bid Workspace", {"tender": tender, "status": "Submitted"}) < len(spec["bids"])
	if spec.get("candidates"):
		return frappe.db.count("Tender Clarification", {"tender": tender}) < len(spec["clarifications"])
	return False


def _candidate_of(tender: str, bidder: str) -> str:
	from kentender_procurement.bid_submission.seeds import kentender_mvp_v1 as bids

	bid = bids.canonical_bid(tender) if bidder == "afya" else bids.bidder_bid(tender, bids.portfolio_bidder(bidder))
	return frappe.db.get_value("Bid Workspace", bid, "bidder_arrangement") or ""


def _summary(spec: dict[str, Any]) -> str:
	return (
		f"Two bids were received for the {spec['item'].lower()}. Both are responsive. Afya Digital Supplies Limited's is the lowest evaluated responsive bid; "
		"Jirani Office Supplies Limited's is ranked second."
	)


#: What each portfolio item shows at the as-at instant, by the stage that
#: last moved it: (requisition state, Tender status, submitted bids, opening
#: state, evaluation state, award stage).
def expected_state(spec: dict[str, Any], current: str) -> dict[str, Any]:
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import REQUISITION_STOPS
	from kentender_procurement.tenders.seeds.kentender_mvp_v1 import TENDER_STOPS

	out: dict[str, Any] = {"requisition": REQUISITION_STOPS[spec["requisition"]["stop"]] if _reaches("requisitions", current) else None}
	if spec.get("tender") and _reaches("tenders", current):
		out["tender"] = TENDER_STOPS[spec["tender"]["stop"]]
		if spec.get("bids"):
			out["bids"] = len(spec["bids"]) if _reaches("bid_submission", current) else 0
			out["opening"] = "Opening complete" if _reaches("bid_opening", current) else None
		if spec.get("candidates"):
			out["candidates"] = len(spec["candidates"]) if _reaches("bid_submission", current) else 0
			out["clarifications"] = len(spec["clarifications"]) if _reaches("bid_submission", current) else 0
		if spec.get("evaluation"):
			stop = spec["evaluation"]["stop"]
			out["evaluation"] = (stop if _reaches("bid_evaluation", current) else None)
		if spec.get("award"):
			out["award"] = {"received": "Opinion", "signed": "Decision"}[spec["award"]["through"]] if _reaches("award", current) else None
	return out


def validate_portfolio(*, current: str) -> list[dict[str, Any]]:
	"""One row per portfolio fact at the as-at instant. Never mutates."""
	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": f"portfolio: {label}"})

	if not _reaches("requisitions", current):
		check(not any(_requisition(spec) for spec in PORTFOLIO), f"no portfolio Requisitions at CURRENT={current}")
		return rows
	for spec in PORTFOLIO:
		want = expected_state(spec, current)
		name = _requisition(spec)
		state = frappe.db.get_value("Procurement Requisition", name, "current_state") if name else None
		check(state == want["requisition"], f"{spec['ref']} {spec['item']}: Requisition {want['requisition']} (got {state})")
		if "tender" not in want:
			continue
		tender = frappe.db.get_value("Tender", {"requisition": name}, ["name", "overall_status"], as_dict=True) if name else None
		check(bool(tender) and tender.overall_status == want["tender"], f"{spec['ref']} Tender {want['tender']} (got {tender and tender.overall_status})")
		if not tender:
			continue
		if "bids" in want:
			submitted = frappe.db.count("Bid Workspace", {"tender": tender.name, "status": "Submitted"})
			check(submitted == want["bids"], f"{spec['ref']} {want['bids']} submitted bids (got {submitted})")
			opening = frappe.db.get_value("Bid Opening Case", {"tender": tender.name}, "state")
			if want["opening"]:
				check(opening == want["opening"], f"{spec['ref']} opening {want['opening']} (got {opening})")
		if "candidates" in want:
			drafts = frappe.db.count("Bid Workspace", {"tender": tender.name})
			check(drafts == want["candidates"], f"{spec['ref']} {want['candidates']} candidate bids (got {drafts})")
			clarifications = frappe.get_all("Tender Clarification", filters={"tender": tender.name}, pluck="status")
			check(len(clarifications) == want["clarifications"], f"{spec['ref']} {want['clarifications']} clarifications (got {len(clarifications)}: {clarifications})")
		if want.get("evaluation"):
			case = frappe.db.get_value("Evaluation Case", {"tender": tender.name}, ["name", "state", "source_intake"], as_dict=True)
			if want["evaluation"] == "report_sent":
				check(bool(case) and case.state == "Report sent", f"{spec['ref']} evaluation report sent (got {case and case.state})")
			elif want["evaluation"] == "intake":
				check(bool(case) and bool(case.source_intake) and case.state != "Report sent", f"{spec['ref']} opening taken up, committee review outstanding (got {case and case.state})")
			else:
				check(bool(case) and not case.source_intake, f"{spec['ref']} evaluation prepared, committee not appointed (got {case and case.state})")
		if want.get("award"):
			stage = frappe.db.get_value("Award Case", {"tender": tender.name}, "stage")
			check(stage == want["award"], f"{spec['ref']} award at {want['award']} (got {stage})")
	return rows


#: Which Home and Analytics fixture each executed-year record serves (plan
#: SW-0502). The HOME/ANL datasets are illustrative (HOME-CHG-001 v0.6 §13,
#: ANL-CHG-001 v0.8 §13): the seed supplies their states, and its generated
#: references replace the fixtures' numbers.
SERVES = {
	"laptops": "ANL Award bucket and award amount; HOME H12 recently completed (Amina's award decision); AWD-DEMO-* profiles",
	"printers": "HOME H2/H10 Prepare professional opinion (Charles); ANL 044 shape",
	"lab_desktops": "HOME H12 Decide award (Amina)",
	"scanners": "HOME H10–H12 committee review outstanding and evaluation deadline; ANL 043 shape",
	"switches": "HOME H12 Appoint the evaluation committee (Amina)",
	"tablets": "Anonymous /tenders list; HOME H1 clarification, H3 addendum guard, H8 paging; H10 Start opening (Coming up); ANL Open bucket",
	"ups": "HOME H1 completed submission, H10 waiting on Amina, H12 Authorise publication",
	"access_points": "ANL preparation bucket and warranty outstanding matter (041 shape); combined Digital Health + HRMD item",
	"field_laptops": "HOME H1 waiting on Amina, H12 Consider cancellation",
	"desktops": "HOME H1/H12 cancellation compliance evidence pending (034 shape)",
	"routers": "ANL Closed bucket, cancellation complete (046 shape); Women reservation",
	"clinic_desktops": "HOME H10 Authorise requisition (Charles); ANL R-A",
	"monitors": "ANL requisition authorised but not taken up (T2 transition open)",
}


def binding_rows() -> list[dict[str, Any]]:
	"""The generated references and states of the executed year's records at
	the as-at instant, for the binding table (plan SW-0502). Read-only."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import COMBINED_ITEM_TITLE, _plan_item_id

	items = [{"key": "laptops", "ref": "T1", "item": COMBINED_ITEM_TITLE}] + [{"key": s["key"], "ref": s["ref"], "item": s["item"]} for s in PORTFOLIO]
	rows = []
	for spec in items:
		plan_item = _plan_item_id(spec["item"])
		requisition = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item}, ["name", "requisition_reference", "current_state"], as_dict=True) if plan_item else None
		tender = frappe.db.get_value("Tender", {"requisition": requisition.name}, ["name", "tender_reference", "overall_status", "requirement_title"], as_dict=True) if requisition else None
		row = {
			"ref": spec["ref"], "plan_item": plan_item, "item": spec["item"],
			"requisition": requisition.requisition_reference if requisition else "", "requisition_state": requisition.current_state if requisition else "",
			"tender": tender.tender_reference if tender else "", "tender_status": tender.overall_status if tender else "",
			"opening": "", "evaluation": "", "award": "", "serves": SERVES.get(spec["key"], ""),
		}
		if tender:
			row["opening"] = frappe.db.get_value("Bid Opening Case", {"tender": tender.name}, "state") or ""
			row["evaluation"] = frappe.db.get_value("Evaluation Case", {"tender": tender.name}, "state") or ""
			row["award"] = frappe.db.get_value("Award Case", {"tender": tender.name}, "stage") or ""
		rows.append(row)
	return rows
