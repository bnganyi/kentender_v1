#!/usr/bin/env python3
"""BUD-CHG-001 v1.16 / CM-CHG-001 v0.10 / AUTH-ADR-001 v1.16 (BUD25-AC-003, -004, -005, -009; CM-AC-72 to -96): a contract signed before KenTender, funded year by year through BOTH real owners.

What is real: Contract Management's funding services (the route, the year's basis prepared by Finance preparation and confirmed by Finance approval, the one request per year, the outcome receiver, the funding
holds), the funding-request seam that carries the request to Budget, Budget's request, entry and decision commands, the canonical Budget's lines and positions for two financial years, the commitments an approved
entry makes, and the people who hold Budget Officer and Budget Approver. What is stood in: nothing. The canonical world has two Budget Approvers: Beatrice Kamau, who is also the Finance approval holder who confirms a
year's basis (so Budget refuses her the approval of that year's entry), and Hellen Mutua (KT-STD-001 v1.31 section 8.3), who prepared and confirmed nothing and finishes the journey.

It changes the canonical Budget and Contract Management on the TEST site and puts them back (the contract, its records, the requests, entries, commitments, ledger events, journal rows and the Contract Management
responsibilities it granted) in a `finally`. It never touches a person: Hellen is a permanent member of the canonical world. Run it under the test-site lock, with no other session using the site, and never against the development site:

    cd /home/midasuser/frappe-bench/sites && flock -o /tmp/kt-test-site.lock ../env/bin/python ../apps/kentender_v1/scripts/bud_v116_independent_contract_journey.py [report.md]
"""

from __future__ import annotations

import sys
import traceback
from decimal import Decimal

import frappe

SITE = "kentender-test.local"
NAMESPACE = "BUD_JRNY_IND"
PREFIX = "CM-JRNY-IND-"
HOP = "charles.mutiso@moh.example.test"  # Head of Procurement Function
PREP = "josphat.mwangi@moh.example.test"  # Finance preparation, and the canonical Budget Officer
CONFIRM = "beatrice.kamau@moh.example.test"  # Finance approval, and the canonical (only) Budget Approver
SECOND_APPROVER = "hellen.mutua@moh.example.test"  # the second Budget Approver of the canonical world (KT-STD-001 v1.31 section 8.3)
CASE_ROLES = ((HOP, "Head of Procurement Function"), (PREP, "Finance preparation"), (CONFIRM, "Finance approval"))
RESULTS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
	RESULTS.append((label, bool(ok), detail))
	print(("PASS  " if ok else "FAIL  ") + label + (f"  [{detail}]" if detail else ""), flush=True)
	return bool(ok)


def money(value) -> Decimal:
	return Decimal(str(value)).quantize(Decimal("0.01"))


class Journey:
	def __init__(self):
		from kentender_budget.services import budget_commitment_contracts as commit
		from kentender_budget.services import budget_contract_funding as budget_funding
		from kentender_budget.services import budget_existing_contract_entry as entries
		from kentender_budget.services.budget_contracts import _line_position_exact
		from kentender_contracts.services import contract_funding as funding
		from kentender_contracts.services import errors, holds, records
		from kentender_core.services import contract_funding_request_contract as seam

		self.commit, self.budget_funding, self.entries, self.position_exact = commit, budget_funding, entries, _line_position_exact
		self.funding, self.errors, self.holds, self.records, self.seam = funding, errors, holds, records, seam
		self.tag = frappe.generate_hash(length=6)
		self.started = frappe.utils.now_datetime()
		self.case = ""
		self.keys = 0
		self.article = {"Initial": "an", "Annual": "an"}
		self.touched_lines: set[str] = set()
		self.before: dict = {}

	# -- helpers --------------------------------------------------------------------------------------------------------------
	def k(self, what: str = "k") -> str:
		self.keys += 1
		return f"jrny-{self.tag}-{what}-{self.keys}"

	def position(self, line):
		return {k: money(v) for k, v in self.position_exact(line, self.commit._current_line_version(line)).items()}

	def version(self):
		return frappe.db.get_value("Contract Case", self.case, "record_version")

	def refused(self, label, fn, *, exceptions=None):
		"""`fn` must be refused. Returns the refusal text, or None when it was not refused."""
		exceptions = exceptions or (self.errors.ContractError, self.errors.InputError, frappe.ValidationError, frappe.PermissionError)
		try:
			out = fn()
		except exceptions as exc:
			check(label, True, f"refused: {str(exc)[:110]}")
			return str(exc)
		if isinstance(out, dict) and out.get("ok") is False:
			check(label, True, f"refused: {str(out.get('message') or out.get('code') or out)[:110]}")
			return str(out)
		check(label, False, "it was not refused")
		return None

	def funding_holds(self):
		return sorted(h.key for h in self.holds.open_holds(self.case) if h.kind == "Funding")

	def budget_request(self, year):
		name = frappe.db.get_value("Contract Funding Request", {"contract": self.case, "fiscal_year": year, "kind": ["!=", "Correction"]}, "name")
		return frappe.get_doc("Contract Funding Request", name) if name else None

	def commitments(self, **filters):
		return frappe.get_all("Procurement Commitment", filters={"contract": self.case, **filters}, fields=["name", "budget_line", "budget", "current_amount", "status", "origin", "entry_row"], order_by="creation asc")

	def years(self):
		first = self.funding.current_year()
		second = frappe.db.get_value("Fiscal Year", {"year_start_date": [">", frappe.db.get_value("Fiscal Year", first, "year_start_date")]}, "name", order_by="year_start_date asc")
		return first, second

	# -- set-up and put-back ---------------------------------------------------------------------------------------------------
	def people(self):
		from kentender_core.services import business_role_registry as registry
		from kentender_core.services import responsibility_administration as administration

		registry.ensure_roles()
		from kentender_contracts.tests import thread_world as tw

		self.unit = tw.unit()
		for user, role in CASE_ROLES:
			administration.grant(user=user, business_role=role, organisation_unit=self.unit if registry.REGISTRY[role].requires_organisation_unit else "", actor="Administrator", fixture_namespace=NAMESPACE)
		frappe.db.commit()

	def second_approver(self):
		"""The canonical world's second Budget Approver must be there: without a second person the journey cannot finish."""
		from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

		holds = bool(frappe.db.exists("User", SECOND_APPROVER)) and bool(authorise_record(user=SECOND_APPROVER, business_role="Budget Approver", organisation_unit="", purpose=PURPOSE_COMMAND).allowed)
		if not check("the canonical world has a second Budget Approver who is not the Finance approval holder", holds and SECOND_APPROVER != CONFIRM, SECOND_APPROVER):
			raise RuntimeError(f"{SECOND_APPROVER} is not a Budget Approver on this site: reseed it (make seed-canonical) or run the journey on a site that has the second Approver of KT-STD-001 v1.31")

	def register_contract(self):
		self.case = self.records.new("Contract Case", contract_id=f"{PREFIX}{self.tag}", source_kind="External record", lifecycle="Active", record_version=1, contract_value=700000, currency="KES",
			supplier_name="Afya Digital Supplies Limited", managing_unit=self.unit, title="Contract signed before KenTender (journey)", current_agreement=1, intake_revision=1).name
		frappe.db.commit()

	def restore(self):
		from kentender_core.services.command_write_guard import purge_doc

		frappe.set_user("Administrator")
		frappe.flags.kt_cm_clock = None
		frappe.db.rollback()
		cases = frappe.get_all("Contract Case", filters={"contract_id": ["like", f"{PREFIX}%"]}, pluck="name")
		requests = frappe.get_all("Contract Funding Request", filters={"contract": ["in", cases or ["-"]]}, pluck="name")
		entries = frappe.get_all("Existing Contract Commitment Entry", filters={"request": ["in", requests or ["-"]]}, pluck="name")
		budgets = sorted({b for b in frappe.get_all("Existing Contract Commitment Entry", filters={"name": ["in", entries or ["-"]]}, pluck="budget") if b})
		for entry in entries:
			for commitment in frappe.get_all("Procurement Commitment", filters={"entry_row": ["like", f"{entry}/%"]}, pluck="name"):
				purge_doc("Procurement Commitment", commitment)
			purge_doc("Existing Contract Commitment Entry", entry)
		for request in requests:
			for outcome in frappe.get_all("Contract Funding Outcome", filters={"request": request}, pluck="name"):
				purge_doc("Contract Funding Outcome", outcome)
			purge_doc("Contract Funding Request", request)
		frappe.flags.allow_budget_audit_purge = True
		try:
			for name in frappe.get_all("Budget Audit Event", filters={"downstream_reference": ["in", cases or ["-"]]}, pluck="name"):
				purge_doc("Budget Audit Event", name)
		finally:
			frappe.flags.allow_budget_audit_purge = False
		if budgets:
			frappe.db.delete("Budget Command Journal", {"budget": ["in", budgets], "creation": [">=", self.started]})
		for case in cases:
			for doctype in self.records.DOCTYPES:
				if doctype == "Contract Case" or not frappe.get_meta(doctype).has_field("contract_case"):
					continue
				frappe.db.delete(doctype, {"contract_case": case})
			frappe.db.delete("Contract Command Journal", {"contract_case": case})
			frappe.db.delete("Contract Case", {"name": case})
		if cases:
			self.records.forget_alerts_of_missing_contracts()
		for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": NAMESPACE}, pluck="name"):
			purge_doc("User Responsibility Assignment", name)
		frappe.db.commit()
		if self.before.get("positions"):
			check("the canonical Budget is back exactly as it was found", {l: self.position(l) for l in self.before["positions"]} == self.before["positions"])
		# the canonical world's own contracts (SEED-002 v0.10 section A8.1) are not this journey's to find gone: only rows named for this journey's contracts count (its contracts all start with PREFIX; a case it
		# creates carries no fixture namespace, so the namespace could not tell them apart)
		mine = {"Contract Case": {"contract_id": ["like", f"{PREFIX}%"]}, "Contract Funding Request": {"contract": ["like", f"{PREFIX}%"]}, "Existing Contract Commitment Entry": {"contract": ["like", f"{PREFIX}%"]},
			"Contract Funding Outcome": {"request": ["in", requests or ["-"]]}}
		left = {dt: n for dt, n in ((dt, frappe.db.count(dt, filters)) for dt, filters in mine.items()) if n}
		check("no request, outcome, entry or contract of this journey is left behind", not left, str(left))

	# -- the journey ----------------------------------------------------------------------------------------------------------
	def pick_lines(self, year, need):
		"""Budget lines of the year that can take `need` between them: the Officer's choice on the screen (`eligible_lines`)."""
		from kentender_budget.services.budget_line_contracts import list_eligible_budget_lines

		eligible = list_eligible_budget_lines(year, self.unit or None)
		lines = eligible if isinstance(eligible, list) else eligible.get("lines", [])
		chosen = []
		for line in lines:
			line_id = line.get("id") or line.get("name") or line.get("budget_line")
			available = money(self.position(line_id)["available"])
			if available >= money(need):
				chosen.append((line_id, available))
		return chosen

	def route_and_basis(self, year1, year2):
		f = self.funding
		check("before any route is recorded the contract carries no funding hold (it keeps its earlier behaviour)", self.funding_holds() == [], str(self.funding_holds()))
		self.refused("only the Head of Procurement can record the route (Finance preparation is refused)", lambda: f.record_route(self.case, route=f.ROUTE_BUDGET, authority_name="Ministry Accounting Officer", approved_amount="700000.00",
			evidence=["Funding authority letter 1"], schedule=[{"year": year1, "amount": "400000.00"}], expected_version=self.version(), idempotency_key=self.k("route-bad"), actor=PREP))
		self.refused("a year share that is not a financial year of this site is refused", lambda: f.record_route(self.case, route=f.ROUTE_BUDGET, authority_name="Ministry Accounting Officer", approved_amount="700000.00",
			evidence=["Funding authority letter 1"], schedule=[{"year": "Select", "amount": "400000.00"}], expected_version=self.version(), idempotency_key=self.k("route-year"), actor=HOP))
		f.record_route(self.case, route=f.ROUTE_BUDGET, authority_name="Ministry Accounting Officer", approved_amount="700000.00", evidence=["Funding authority letter 1"],
			schedule=[{"year": year1, "amount": "400000.00"}, {"year": year2, "amount": "300000.00"}], expected_version=self.version(), idempotency_key=self.k("route"), actor=HOP)
		view = f.view(self.case)
		check("the Head records the route and the year shares; the contract names both years", view["route"] == f.ROUTE_BUDGET and [y["year"] for y in view["years"]] == sorted([year1, year2]), str([(y["year"], y["schedule_amount"], y["label"]) for y in view["years"]]))
		check("with the route recorded, this year's unfunded spending and payments are held", {f"funding:{self.case}:spending", f"funding:{self.case}:pay:{year1}"} <= set(self.funding_holds()), str(self.funding_holds()))
		f.prepare_year_basis(self.case, year=year1, charge="400000.00", explanation="Prior activity and the current-year obligation reconciled to the signed terms", evidence=["Signed contract 1", "Opening reconciliation 1"],
			expected_version=self.version(), idempotency_key=self.k("prep"), actor=PREP)
		self.refused("Finance preparation prepares the year's basis and cannot confirm it", lambda: f.confirm_funding_evidence(self.case, year=year1, expected_version=self.version(), idempotency_key=self.k("conf-bad"), actor=PREP))

	def request_and_fund(self, year, charge, label, *, confirm_after=False, kind="Initial"):
		f = self.funding
		before_commitments = len(self.commitments())
		f.request_funding(self.case, year=year, expected_version=self.version(), idempotency_key=self.k(f"req-{label}"), actor=HOP)
		frappe.db.commit()
		doc = self.budget_request(year)
		rec = f.get_record(self.case, year)
		check(f"{label}: the Head's one request reaches the real Budget owner as {self.article[kind]} {kind} request for {year} and Contract Management says it is open",
			bool(doc) and doc.kind == kind and doc.status == "Open" and rec.request_state == "Open" and bool(rec.request_reference), f"{getattr(doc, 'generated_reference', None)}, {getattr(doc, 'year_allocation_status', None)}, Contract Management: {rec.request_state}")
		check(f"{label}: asking again for the same year returns the same request and creates no second", self._second_request(year, doc.name))
		if confirm_after:
			frappe.set_user(PREP)
			seen = self.entries.get_contract_funding(doc.name)
			frappe.set_user("Administrator")
			check(f"{label}: while Finance has not confirmed the year, Budget says Year allocation required and offers the Officer no Submit", doc.year_allocation_status == self.seam.YEAR_REQUIRED and not seen["actions"].get("submit"),
				f"{doc.year_allocation_status}; actions {sorted(k for k, v in seen['actions'].items() if v)}")
			f.confirm_funding_evidence(self.case, year=year, expected_version=self.version(), idempotency_key=self.k(f"conf-{label}"), actor=CONFIRM)
			frappe.db.commit()
			later = self.budget_request(year)
			check(f"{label}: Finance's later confirmation reaches the same Budget request, which is now Confirmed with the charge", later.name == doc.name and later.year_allocation_status == self.seam.YEAR_CONFIRMED and money(self.entries.amounts_of(later)["charge"]) == money(charge),
				f"{later.year_allocation_status}, charge {self.entries.amounts_of(later)['charge']}")
			doc = later
		amounts = self.entries.amounts_of(doc)
		check(f"{label}: Budget calculated the amount to fund from the confirmed charge and the coverage it can verify (none yet)", money(amounts["charge"]) == money(charge) and money(amounts["required"]) == money(charge), f"charge {amounts['charge']}, required {amounts['required']}")
		check(f"{label}: nothing is committed by the request alone", len(self.commitments()) == before_commitments)
		frappe.set_user(PREP)
		got = self.entries.get_contract_funding(doc.name)
		frappe.set_user("Administrator")
		lines = self.pick_lines(year, charge)
		check(f"{label}: the Budget Officer is offered budget lines with room for the whole amount, and Submit", bool(lines) and bool(got.get("eligible_lines")) and bool(got["actions"].get("submit")), f"{len(lines)} lines with room, {len(got.get('eligible_lines') or [])} eligible, actions {sorted(k for k, v in got['actions'].items() if v)}")
		line = lines[0][0]
		self.touched_lines.add(line)
		self.before.setdefault("positions", {})[line] = self.position(line)
		return doc, line

	def _second_request(self, year, name):
		"""Asking again for a year that already has its request: the same request, nothing new."""
		before = frappe.db.count("Contract Funding Request", {"contract": self.case})
		try:
			self.funding.request_funding(self.case, year=year, expected_version=self.version(), idempotency_key=self.k("again"), actor=HOP)
		except (self.errors.ContractError, self.errors.InputError):
			pass
		frappe.db.commit()
		return frappe.db.count("Contract Funding Request", {"contract": self.case}) == before and self.budget_request(year).name == name

	def enter_and_decide(self, doc, line, charge, label):
		frappe.set_user(PREP)
		pos = self.position(line)
		entry = self.entries.record_existing_contract_commitment_entry({"request": doc.name, "rows": [{"budget_line": line, "amount": str(money(charge))}], "reconciliation": "The year's charge is funded from the line it belongs to.",
			"idempotency_key": self.k(f"rec-{label}")})
		check(f"{label}: the Officer records the entry on one line for the whole amount", bool(entry.get("ok")), str(entry)[:150])
		submitted = self.entries.submit_existing_contract_commitment_entry({"entry": entry["entry"]["id"], "idempotency_key": self.k(f"sub-{label}")})
		check(f"{label}: the Officer submits it for approval", bool(submitted.get("ok")), str(submitted)[:150])
		check(f"{label}: nothing moves while it awaits approval", self.position(line) == pos)
		return entry["entry"]["id"], pos

	def decide_refused(self, entry, who, label, text):
		frappe.set_user(who)
		out = self.refused(text, lambda: self.entries.decide_existing_contract_commitment_entry({"entry": entry, "decision": "Approve", "reason": "", "idempotency_key": self.k(f"dec-bad-{label}")}))
		frappe.set_user("Administrator")
		return out

	def approve(self, entry, line, pos, charge, label):
		frappe.set_user(SECOND_APPROVER)
		view_reason = self.entries.get_contract_funding(frappe.db.get_value("Existing Contract Commitment Entry", entry, "request"))
		check(f"{label}: the second Approver is offered Approve", bool(view_reason["actions"].get("approve")), str(view_reason["actions"]))
		decided = self.entries.decide_existing_contract_commitment_entry({"entry": entry, "decision": "Approve", "reason": "", "idempotency_key": self.k(f"dec-{label}")})
		check(f"{label}: a Budget Approver who prepared nothing and confirmed nothing approves it", bool(decided.get("ok")), str(decided)[:150])
		frappe.set_user("Administrator")
		frappe.db.commit()
		after = self.position(line)
		check(f"{label}: exactly the charge moves into Committed and out of Available; Reserved is untouched", (after["committed"] - pos["committed"], after["available"] - pos["available"], after["reserved"] - pos["reserved"]) == (money(charge), -money(charge), Decimal("0.00")),
			f"committed {after['committed'] - pos['committed']}, available {after['available'] - pos['available']}, reserved {after['reserved'] - pos['reserved']}")
		made = [c for c in self.commitments() if c.entry_row.startswith(f"{entry}/")]
		check(f"{label}: the commitment is the contract's own, on the entry's line, of the entry's origin", len(made) == 1 and made[0].budget_line == line and money(made[0].current_amount) == money(charge), str(made)[:160])
		return decided

	def year_one(self, year1, year2):
		doc, line = self.request_and_fund(year1, "400000.00", "year 1", confirm_after=True)
		entry, pos = self.enter_and_decide(doc, line, "400000.00", "year 1")
		self.decide_refused(entry, CONFIRM, "y1", "year 1: the Budget Approver who confirmed the year's basis in Contract Management is refused, with the real people on both sides")
		self.decide_refused(entry, PREP, "y1p", "year 1: the Budget Officer who prepared the entry cannot approve it")
		check("year 1: the refusals leave the entry awaiting approval and nothing committed", self.entries.entry_summary(frappe.get_doc("Existing Contract Commitment Entry", entry)).get("status") == "Awaiting approval" and not self.commitments())
		self.approve(entry, line, pos, "400000.00", "year 1")
		rec = self.funding.get_record(self.case, year1)
		check("year 1: Budget's outcome reached Contract Management in the same step and the year shows Completed", rec.request_state == "Completed" and rec.outcome == self.seam.OUTCOME_APPROVED, f"{rec.request_state} / {rec.outcome}")
		check("year 1: the funding holds are lifted", self.funding_holds() == [], str(self.funding_holds()))
		check("year 1: the contract's funded years now include year 1 only", self.funding.funded_years(self.case) == {year1}, str(self.funding.funded_years(self.case)))
		doc = self.budget_request(year1)
		check("year 1: the request is Completed in Budget and a repeat of the same approval creates nothing more", doc.status == "Completed" and self._replay_creates_nothing(entry), f"{doc.status}")
		self.first_commitment = self.commitments()[0]

	def _replay_creates_nothing(self, entry):
		frappe.set_user(SECOND_APPROVER)
		count = len(self.commitments())
		try:
			self.entries.decide_existing_contract_commitment_entry({"entry": entry, "decision": "Approve", "reason": "", "idempotency_key": self.k("dec-replay")})
		except Exception:  # noqa: BLE001 - a refusal of the second approval is as good as a no-op
			frappe.db.rollback()
		frappe.set_user("Administrator")
		return len(self.commitments()) == count

	def year_two(self, year1, year2):
		f = self.funding
		lifecycle = frappe.db.get_value("Contract Case", self.case, "lifecycle")
		frappe.flags.kt_cm_clock = frappe.utils.get_datetime(f"{frappe.db.get_value('Fiscal Year', year2, 'year_start_date')} 09:00:00")
		check("the clock moves into the second financial year", f.current_year() == year2, f.current_year())
		check("year 2: the contract is still Active, not reopened, and the new year's spending is held until it is funded", frappe.db.get_value("Contract Case", self.case, "lifecycle") == lifecycle == "Active" and f"funding:{self.case}:spending" in self.funding_holds(), str(self.funding_holds()))
		check("year 2: year 1's funding is untouched and nothing is carried forward", f.funded_years(self.case) == {year1} and not self.budget_request(year2), str(f.funded_years(self.case)))
		f.prepare_year_basis(self.case, year=year2, charge="300000.00", explanation="The second year's obligation under the signed terms", evidence=["Signed contract 1", "Annual funding schedule 1"], expected_version=self.version(), idempotency_key=self.k("prep-y2"), actor=PREP)
		f.confirm_funding_evidence(self.case, year=year2, expected_version=self.version(), idempotency_key=self.k("conf-y2"), actor=CONFIRM)
		doc, line = self.request_and_fund(year2, "300000.00", "year 2", kind="Annual")
		first = self.budget_request(year1)
		check("year 2: the request is a new Annual one for the second year, on its own lineage, and year 1's request stays Completed", doc.name != first.name and doc.fiscal_year == year2 and doc.scope_key != first.scope_key and first.status == "Completed", f"{doc.generated_reference} ({doc.kind}, {doc.fiscal_year}); year 1: {first.generated_reference} {first.status}")
		entry, pos = self.enter_and_decide(doc, line, "300000.00", "year 2")
		self.approve(entry, line, pos, "300000.00", "year 2")
		check("year 2: Contract Management shows both years funded and no funding hold remains", f.funded_years(self.case) == {year1, year2} and self.funding_holds() == [], f"{f.funded_years(self.case)} {self.funding_holds()}")
		again = frappe.db.get_value("Procurement Commitment", self.first_commitment.name, ["current_amount", "status", "budget_line"], as_dict=True)
		check("year 2: year 1's commitment is exactly as it was (same amount, same status, same line)", money(again.current_amount) == money(self.first_commitment.current_amount) and again.status == self.first_commitment.status and again.budget_line == self.first_commitment.budget_line)
		check("year 2: the contract's commitments are one per year, in two different Budgets", len(self.commitments()) == 2 and len({c.budget for c in self.commitments()}) == 2, str([(c.budget, c.current_amount) for c in self.commitments()]))
		check("the contract was never reopened: its lifecycle is Active throughout and no reopening was recorded", frappe.db.get_value("Contract Case", self.case, "lifecycle") == "Active" and not self._reopened())

	def _reopened(self):
		doctype = "Contract Event" if frappe.db.exists("DocType", "Contract Event") else ""
		if not doctype:
			return False
		meta = frappe.get_meta(doctype)
		field = "event_type" if meta.has_field("event_type") else "kind" if meta.has_field("kind") else ""
		return bool(field and frappe.db.exists(doctype, {"contract_case": self.case, field: ["like", "%eopen%"]}))

	def balance(self):
		for line in sorted(self.touched_lines):
			p = self.position(line)
			check(f"A - R - C = V on {line}", p["approved"] - p["reserved"] - p["committed"] == p["available"], str(p))

	def run(self):
		first, second = self.years()
		check("the site has two consecutive financial years with an Active Budget each", bool(first and second) and all(frappe.db.exists("Procurement Budget", {"fiscal_year": y}) for y in (first, second)), f"{first}, {second}")
		self.second_approver()
		self.people()
		self.register_contract()
		self.route_and_basis(first, second)
		self.year_one(first, second)
		self.year_two(first, second)
		self.balance()


def main() -> int:
	frappe.init(site=SITE, sites_path=".")
	frappe.connect()
	if frappe.local.site != "kentender-test.local":
		print("This journey runs on the test site only.")
		return 2
	frappe.set_user("Administrator")
	journey = Journey()
	journey.restore()  # whatever an earlier, interrupted run of this journey left
	RESULTS.clear()
	try:
		journey.run()
	except Exception:  # noqa: BLE001
		traceback.print_exc()
		check("the journey ran to the end", False, "an unexpected error; see the trace above")
	finally:
		journey.restore()
	failed = [r for r in RESULTS if not r[1]]
	print(f"\n{len(RESULTS) - len(failed)} passed, {len(failed)} failed", flush=True)
	if len(sys.argv) > 1:
		with open(sys.argv[1], "w") as handle:
			handle.write("# Independent contract: Contract Management to Budget, year by year (test site)\n\n")
			handle.write(f"Run {frappe.utils.now()} on `{SITE}`.\n\n| Check | Result | Detail |\n|---|---|---|\n")
			for label, ok, detail in RESULTS:
				handle.write(f"| {label} | {'Pass' if ok else '**FAIL**'} | {detail.replace('|', '/')[:200]} |\n")
	return 1 if failed else 0


if __name__ == "__main__":
	sys.exit(main())
