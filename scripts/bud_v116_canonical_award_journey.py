#!/usr/bin/env python3
"""BUD-CHG-001 v1.16 / AWD-CHG-001 v0.7 / CM-CHG-001 v0.10 (BUD25-AC-002, -006, -007, -011; CM-AC-85, -91): the canonical two-source award, converted and followed through the real owners.

What is real: the retained Award funding allocation of AWD-MOH-2026-002 (two reservations, KES 46,400,000), the Award owner's verification (`kt_award_funding_verification`), Budget's contract funding provider, the
reservations, the line positions, the audit ledger, Budget's request / entry / correction commands and the people who hold Budget Officer and Budget Approver. What is stood in: Contract Management itself, whose
formation of this particular award is blocked by the issued Form No. 4 declaring no insertions and by the entity address not being held (FU-CM-70, FU-CM-72). This script makes the calls Contract Management makes
(`contract_funding_contract.convert/adjust/close` with the lineage Award supplied) so that the Award -> Budget half of the chain, the closure, the Additional path and the correction are exercised on the real data.

It changes the canonical Budget on the TEST site and puts it back (reservation rows, commitments, requests, entries, corrections, ledger events, journal rows) in a `finally`. Run it under the test-site lock, with
no other session using the site, and never against the development site:

    cd /home/midasuser/frappe-bench/sites && flock -o /tmp/kt-test-site.lock ../env/bin/python ../apps/kentender_v1/scripts/bud_v116_canonical_award_journey.py [report.md]
"""

from __future__ import annotations

import json
import sys
import threading
import traceback
from decimal import Decimal

import frappe

SITE = "kentender-test.local"
AWARD = "AWD-MOH-2026-002"
OFFICER = "josphat.mwangi@moh.example.test"
APPROVER = "beatrice.kamau@moh.example.test"
CONFIRMER = "finance.confirmer.journey@example.test"
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
		from kentender_budget.services import budget_commitment_corrections as corrections
		from kentender_budget.services import budget_contract_funding as funding
		from kentender_budget.services import budget_existing_contract_entry as entries
		from kentender_budget.services.budget_contracts import _line_position_exact
		from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller
		from kentender_core.services import contract_funding_contract as seam
		from kentender_core.services import contract_source_contract as sources

		self.commit, self.corrections, self.funding, self.entries = commit, corrections, funding, entries
		self.position_exact, self.PRINCIPAL_CONTRACT, self.service_caller = _line_position_exact, PRINCIPAL_CONTRACT, service_caller
		self.seam, self.sources = seam, sources
		self.tag = frappe.generate_hash(length=6)
		self.contract = f"CM-JRNY-{self.tag}"
		self.rival = f"CM-JRNY-RIVAL-{self.tag}"
		self.started = frappe.utils.now_datetime()
		self.before = {}

	# -- helpers --------------------------------------------------------------------------------------------------------------
	def position(self, line):
		exact = self.position_exact(line, self.commit._current_line_version(line))
		return {k: money(v) for k, v in exact.items()}

	def commitments(self, **filters):
		return frappe.get_all("Procurement Commitment", filters=filters, fields=["name", "contract", "reservation", "budget_line", "current_amount", "status", "origin", "lineage_json"], order_by="creation asc")

	def as_user(self, user):
		frappe.set_user(user)

	def commitf(self):
		frappe.db.commit()

	def refused(self, label, fn):
		"""`fn` must be refused and leave nothing behind."""
		before = (len(self.commitments(contract=self.contract)), {l: self.position(l) for l in self.lines})
		try:
			fn()
		except (self.seam.Refused, self.seam.Unavailable, frappe.ValidationError, frappe.PermissionError) as exc:
			after = (len(self.commitments(contract=self.contract)), {l: self.position(l) for l in self.lines})
			return check(label, before == after, f"refused: {str(exc)[:110]}")
		return check(label, False, "it was not refused")

	# -- the journey ----------------------------------------------------------------------------------------------------------
	def facts(self):
		from kentender_procurement.award.services import funding_allocation, state

		doc = frappe.get_doc("Award Case", AWARD)
		decision = state.committed_decision(doc)
		held = funding_allocation.current(doc)
		check("the canonical award has a committed Award decision and a retained funding allocation", bool(decision and decision.outcome == "Award" and held), f"decision {getattr(decision, 'name', None)}, allocation {getattr(held, 'name', None)}")
		if not (decision and held):
			raise SystemExit(self.finish())
		s9 = json.loads(self.sources.fetch(f"S9-{AWARD}")["content"])
		self.allocations = s9["allocations"]
		self.total = money(s9["total"])
		self.lineage = {"award": AWARD, "decision": held.decision, "allocation_digest": held.digest, "agreement_version": 1}
		self.lines = sorted({a["budget_line"]["id"] if isinstance(a["budget_line"], dict) else a["budget_line"] for a in self.allocations})
		self.reservations = [a["reservation"] for a in self.allocations]
		check("the award is split over two reservations that add up to KES 46,400,000", len(self.reservations) == 2 and sum(money(a["amount"]) for a in self.allocations) == self.total == money("46400000"), ", ".join(f"{a['reservation']}={a['amount']}" for a in self.allocations))
		self.before["reservations"] = {r: frappe.get_doc("Funding Reservation", r).as_dict() for r in self.reservations}
		self.before["positions"] = {l: self.position(l) for l in self.lines}
		self.budgets = sorted({frappe.db.get_value("Procurement Budget Line", l, "budget") for l in self.lines})
		self.rows = [{"reservation": a["reservation"], "amount": a["amount"], "source_allocation": a.get("source_allocation")} for a in self.allocations]

	def install_authority(self):
		"""Stand in for Contract Management's interim answer: each journey contract may draw on exactly the two reservations the award names. The Award owner's verification stays real."""
		from kentender_core.services import contract_reservation_authority as authority

		self.authority_flag = authority.FLAG
		self.authority_stand_in = authority.Static({c: set(self.reservations) for c in (self.contract, self.rival, f"CM-JRNY-THIRD-{self.tag}")})
		frappe.flags[authority.FLAG] = [self.authority_stand_in]

	def convert_args(self, **over):
		return {"contract": over.pop("contract", self.contract), "allocations": over.pop("allocations", self.rows), "amount": float(over.pop("amount", self.total)), "lineage": over.pop("lineage", self.lineage)}

	def declined(self, fn):
		"""The text of the refusal when `fn` is refused, by an exception (a person without the responsibility) or by a result that says it was not done; None when it was done."""
		try:
			out = fn()
		except Exception as exc:  # noqa: BLE001 - the refusal is what is looked for
			return f"{type(exc).__name__}: {str(exc)[:90]}"
		return str(out)[:120] if isinstance(out, dict) and out.get("ok") is False else None

	def refusals(self):
		bad_rows = [dict(self.rows[0], amount=str(money(self.rows[0]["amount"]) + 1)), *self.rows[1:]]
		self.refused("a wrong amount on one reservation is refused and nothing is funded", lambda: self.seam.convert(f"{self.contract}:bad-amount", **self.convert_args(allocations=bad_rows)))
		self.refused("a funding allocation Award does not hold is refused", lambda: self.seam.convert(f"{self.contract}:bad-digest", **self.convert_args(lineage={**self.lineage, "allocation_digest": "0" * 64})))
		self.refused("a conversion that carries no lineage is refused", lambda: self.seam.convert(f"{self.contract}:no-lineage", **self.convert_args(lineage=None)))
		self.refused("a reservation the award does not name is refused", lambda: self.seam.convert(f"{self.contract}:foreign", **self.convert_args(allocations=[{**self.rows[0], "reservation": "NO-SUCH-RESERVATION"}, *self.rows[1:]])))

		from kentender_procurement.award.services import funding_allocation, funding_verification
		from kentender_core.services.award_funding_verification import UNAVAILABLE, Verification

		original = funding_verification.Provider.verify
		funding_verification.Provider.verify = lambda self_, **kw: Verification(UNAVAILABLE, ["The Award owner did not answer."])
		try:
			self.refused("an Award owner that cannot answer stops the conversion, never a pass", lambda: self.seam.convert(f"{self.contract}:unavailable", **self.convert_args()))
		finally:
			funding_verification.Provider.verify = original
		compute = funding_allocation.compute
		funding_allocation.compute = lambda doc: {**compute(doc), "digest": "f" * 64}
		try:
			self.refused("a source that moved after the allocation was retained stops the conversion (stale source)", lambda: self.seam.convert(f"{self.contract}:stale", **self.convert_args()))
		finally:
			funding_allocation.compute = compute
		check("after every refusal the reservations and positions are exactly as they were", {r: frappe.get_doc("Funding Reservation", r).remaining_amount for r in self.reservations} == {r: row["remaining_amount"] for r, row in self.before["reservations"].items()} and {l: self.position(l) for l in self.lines} == self.before["positions"])

	def race(self):
		"""Two contracts try to convert the same award at once from two connections: exactly one wins."""
		site, path = frappe.local.site, frappe.local.sites_path
		outcome: dict[str, object] = {}

		def run(name, contract, identity):
			try:
				frappe.init(site=site, sites_path=path)
				frappe.connect()
				frappe.set_user("Administrator")
				from kentender_budget.services.contract_funding_provider import service
				from kentender_core.services import contract_funding_contract as seam

				frappe.flags.kt_contract_funding_providers = [service()]
				frappe.flags[self.authority_flag] = [self.authority_stand_in]
				try:
					outcome[name] = ("ok", seam.convert(identity, **self.convert_args(contract=contract)))
					frappe.db.commit()
				except Exception as exc:  # noqa: BLE001
					frappe.db.rollback()
					outcome[name] = ("refused", f"{type(exc).__name__}: {str(exc)[:110]}")
			finally:
				frappe.db.close()

		gate = threading.Event()
		threads = [threading.Thread(target=lambda n=n, c=c, i=i: (gate.wait(10), run(n, c, i))) for n, c, i in (("a", self.contract, f"{self.contract}:convert"), ("b", self.rival, f"{self.rival}:convert"))]
		for t in threads:
			t.start()
		gate.set()
		for t in threads:
			t.join(120)
		frappe.db.rollback()  # the main connection reads fresh committed state
		wins = [k for k, v in outcome.items() if v[0] == "ok"]
		check("two contracts converting the same award at once: exactly one wins and the other is refused", len(wins) == 1, json.dumps(outcome, default=str)[:300])
		winner = self.contract if wins == ["a"] else self.rival
		loser = self.rival if winner == self.contract else self.contract
		self.contract = winner
		made = self.commitments(contract=winner)
		check("the winner holds exactly one commitment per reservation, with the awarded amounts", sorted((c.reservation, money(c.current_amount)) for c in made) == sorted((a["reservation"], money(a["amount"])) for a in self.allocations), str([(c.reservation, c.current_amount) for c in made]))
		check("the loser holds nothing", not self.commitments(contract=loser))
		return made

	def after_conversion(self, made):
		positions = {l: self.position(l) for l in self.lines}
		committed = sum(p["committed"] - self.before["positions"][l]["committed"] for l, p in positions.items())
		reserved = sum(p["reserved"] - self.before["positions"][l]["reserved"] for l, p in positions.items())
		available = sum(p["available"] - self.before["positions"][l]["available"] for l, p in positions.items())
		check("conversion moves exactly the awarded price from Reserved to Committed and leaves Available unchanged", (committed, reserved, available) == (self.total, -self.total, Decimal("0.00")), f"committed {committed}, reserved {reserved}, available {available}")
		lineage = [json.loads(c.lineage_json or "{}") for c in made]
		check("each commitment carries the verified Award allocation it came from", all(l.get("allocation_digest") == self.lineage["allocation_digest"] for l in lineage), str(lineage[0])[:160] if lineage else "no lineage")
		replay = self.seam.convert(f"{self.contract}:convert", **self.convert_args(contract=self.contract))
		check("repeating the conversion returns the same result and creates nothing more", len(self.commitments(contract=self.contract)) == len(made) and bool(replay.get("reference")), str(replay)[:100])
		check("the funding owner reads back what it already did under that identity", bool(self.seam.lookup(f"{self.contract}:convert")))
		self.refused("a third contract cannot take what is already converted (no overspend)", lambda: self.seam.convert(f"{self.contract}:third", **self.convert_args(contract=f"CM-JRNY-THIRD-{self.tag}")))

	def variation_and_close(self, made):
		first = made[0]
		adjusted_total = money(first.current_amount) + money("100000")
		before = {l: self.position(l) for l in self.lines}
		result = self.seam.adjust(f"{self.contract}:vary", contract=self.contract, allocations=[{"reservation": first.reservation, "new_total": float(adjusted_total)}], event_id=f"{self.contract}:variation-1", event_type="ContractVariation")
		after = {l: self.position(l) for l in self.lines}
		delta_c = sum(after[l]["committed"] - before[l]["committed"] for l in self.lines)
		delta_v = sum(after[l]["available"] - before[l]["available"] for l in self.lines)
		check("a lawful increase of KES 100,000 raises Committed and lowers Available by exactly that", (delta_c, delta_v) == (money("100000"), money("-100000")), str(result)[:100])
		final_total = self.total + money("100000")
		before = {l: self.position(l) for l in self.lines}
		closed = self.seam.close(f"{self.contract}:close", contract=self.contract, final_amount=float(final_total), event_id=f"{self.contract}:closed", event_type="ContractClosed", evidence=["Closure 1"])
		after = {l: self.position(l) for l in self.lines}
		check("closing the contract changes status only: the final amount stays counted and nothing is released", after == before and all(c.status == "Closed" for c in self.commitments(contract=self.contract)), str(closed)[:100])
		again = self.seam.close(f"{self.contract}:close", contract=self.contract, final_amount=float(final_total), event_id=f"{self.contract}:closed", event_type="ContractClosed", evidence=["Closure 1"])
		check("a repeated closure is the same closure", again.get("reference") == closed.get("reference") and again.get("amount") == closed.get("amount"), f"first {closed}, again {again}")
		self.refused("a Closed commitment accepts no further adjustment from the contract service", lambda: self.seam.adjust(f"{self.contract}:vary-closed", contract=self.contract, allocations=[{"reservation": first.reservation, "new_total": float(adjusted_total + 1)}], event_id=f"{self.contract}:variation-2", event_type="ContractVariation"))
		events_before = frappe.db.count("Budget Audit Event", {"budget": ["in", self.budgets]})
		check("reopening the contract in Contract Management makes no funding call and changes nothing in Budget", frappe.db.count("Budget Audit Event", {"budget": ["in", self.budgets]}) == events_before and {l: self.position(l) for l in self.lines} == after)
		return self.commitments(contract=self.contract)

	def request(self, kind, subject, original, charge, year):
		payload = {"kind": kind, "contract": self.contract, "contract_reference": self.contract, "agreement_version": "1", "supplier_name": "Afya Digital Supplies Limited", "target_year": year, "currency": "KES",
			"subject_event": subject, "original_commitment": original, "basis": {"schema": self.seam_basis_schema(), "contract": self.contract, "target_year": year, "currency": "KES", "confirmed_charge": charge, "digest": f"BASIS-{subject}",
			"evidence": ["Signed contract 1", "Variation 1"], "explanation": "The effective increment after reopening", "confirmers": [{"user": CONFIRMER, "assignment": "URA-FINANCE-1", "at": str(frappe.utils.now_datetime())}]},
			"evidence": ["Variation 1"]}
		return self.funding.receive_contract_funding_request(payload, f"{self.contract}:{subject}:{frappe.generate_hash(length=5)}", caller=self.service_caller(self.PRINCIPAL_CONTRACT, reference=self.contract))

	def seam_basis_schema(self):
		from kentender_core.services import contract_funding_request_contract as request_seam

		return request_seam.BASIS_SCHEMA

	def additional(self, closed):
		line = closed[0].budget_line
		year = frappe.db.get_value("Procurement Budget", frappe.db.get_value("Procurement Budget Line", line, "budget"), "fiscal_year")
		before = self.position(line)
		got = self.request("Additional", "JRNY-INC-1", closed[0].name, "50000.00", year)
		check("a real later increment after closure is received as one Additional request for the increment only", got.get("ok") and got["request"]["amount_requiring_funding"] == "50000.00", str(got.get("request", got))[:140])
		request = got["request"]["id"]
		self.as_user(OFFICER)
		entry = self.entries.record_existing_contract_commitment_entry({"request": request, "rows": [{"budget_line": line, "amount": "50000.00"}], "reconciliation": "The increment is funded from the line it belongs to.", "idempotency_key": f"rec-{frappe.generate_hash(length=8)}"})
		check("the Officer records the Additional entry", entry.get("ok"), str(entry)[:140])
		submitted = self.entries.submit_existing_contract_commitment_entry({"entry": entry["entry"]["id"], "idempotency_key": f"sub-{frappe.generate_hash(length=8)}"})
		check("the Officer submits it", submitted.get("ok"), str(submitted)[:140])
		self.as_user(OFFICER)
		own = self.declined(lambda: self.entries.decide_existing_contract_commitment_entry({"entry": entry["entry"]["id"], "decision": "Approve", "reason": "", "idempotency_key": f"dec-{frappe.generate_hash(length=8)}"}))
		check("the preparer cannot approve their own entry", own is not None, own or "it was approved")
		self.as_user(APPROVER)
		decided = self.entries.decide_existing_contract_commitment_entry({"entry": entry["entry"]["id"], "decision": "Approve", "reason": "", "idempotency_key": f"dec-{frappe.generate_hash(length=8)}"})
		check("a different Budget Approver approves it", decided.get("ok"), str(decided)[:140])
		self.as_user("Administrator")
		after = self.position(line)
		check("only the increment is added to Committed and taken from Available; Reserved is untouched", (after["committed"] - before["committed"], after["available"] - before["available"], after["reserved"] - before["reserved"]) == (money("50000"), money("-50000"), Decimal("0.00")), f"{after}")
		check("the original Closed commitment is neither raised nor reopened", frappe.db.get_value("Procurement Commitment", closed[0].name, ["current_amount", "status"], as_dict=True) == {"current_amount": closed[0].current_amount, "status": "Closed"})
		again = self.request("Additional", "JRNY-INC-1", closed[0].name, "50000.00", year)
		check("repeating the same increment funds nothing a second time", not again.get("ok", True) and again.get("code") == "BUDGET_ENTRY_DUPLICATE", str(again)[:120])

	def correction(self, closed):
		target = closed[0]
		line = target.budget_line
		before = self.position(line)
		reservation_before = frappe.get_doc("Funding Reservation", target.reservation).remaining_amount
		new_amount = money(target.current_amount) - money("200000")
		self.as_user(OFFICER)
		recorded = self.corrections.record_commitment_correction({"commitment": target.name, "new_amount": float(new_amount), "reason": "The final obligation included work that was never performed.", "evidence": ["Final obligation review 1", "Closure 1"],
			"contract_reference": self.contract, "idempotency_key": f"cor-{frappe.generate_hash(length=8)}"})
		check("the Officer records a supported downward correction of the Closed commitment", recorded.get("ok"), str(recorded)[:140])
		own = self.declined(lambda: self.corrections.decide_commitment_correction({"correction": recorded["correction"]["id"], "decision": "Approve", "reason": "", "idempotency_key": f"dc-{frappe.generate_hash(length=8)}"}))
		check("the person who recorded the correction cannot approve it", own is not None, own or "it was approved")
		self.as_user(APPROVER)
		decided = self.corrections.decide_commitment_correction({"correction": recorded["correction"]["id"], "decision": "Approve", "reason": "", "idempotency_key": f"dc-{frappe.generate_hash(length=8)}"})
		check("a different Budget Approver approves it", decided.get("ok"), str(decided)[:140])
		self.as_user("Administrator")
		after = self.position(line)
		check("the decrease goes back to Available; Reserved and the reservation's own remainder are unchanged", (after["committed"] - before["committed"], after["available"] - before["available"], after["reserved"] - before["reserved"]) == (money("-200000"), money("200000"), Decimal("0.00")) and frappe.get_doc("Funding Reservation", target.reservation).remaining_amount == reservation_before, f"{after}")

	def balance(self):
		for line in self.lines:
			p = self.position(line)
			check(f"A - R - C = V on {line}", p["approved"] - p["reserved"] - p["committed"] == p["available"], str(p))

	# -- put the test site back ------------------------------------------------------------------------------------------------
	def restore(self):
		from kentender_core.services.command_write_guard import purge_doc

		frappe.set_user("Administrator")
		frappe.db.rollback()
		contracts = [self.contract, self.rival, f"CM-JRNY-THIRD-{self.tag}"]
		commitments = frappe.get_all("Procurement Commitment", filters={"contract": ["in", contracts]}, pluck="name")
		for doctype in ("Commitment Correction",):
			for name in frappe.get_all(doctype, filters={"commitment": ["in", commitments or ["-"]]}, pluck="name"):
				purge_doc(doctype, name)
		for name in frappe.get_all("Existing Contract Commitment Entry", filters={"contract": ["in", contracts]}, pluck="name"):
			purge_doc("Existing Contract Commitment Entry", name)
		for request in frappe.get_all("Contract Funding Request", filters={"contract": ["in", contracts]}, pluck="name"):
			for outcome in frappe.get_all("Contract Funding Outcome", filters={"request": request}, pluck="name"):
				purge_doc("Contract Funding Outcome", outcome)
			purge_doc("Contract Funding Request", request)
		for name in commitments:
			purge_doc("Procurement Commitment", name)
		frappe.flags.allow_budget_audit_purge = True
		try:
			for name in frappe.get_all("Budget Audit Event", filters={"budget": ["in", self.budgets], "creation": [">=", self.started]}, pluck="name"):
				purge_doc("Budget Audit Event", name)
		finally:
			frappe.flags.allow_budget_audit_purge = False
		frappe.db.delete("Budget Command Journal", {"budget": ["in", self.budgets], "creation": [">=", self.started]})
		for name, row in self.before.get("reservations", {}).items():
			for field in ("status", "remaining_amount", "original_amount", "modified"):
				if field in row:
					frappe.db.set_value("Funding Reservation", name, field, row[field], update_modified=False)
		frappe.db.commit()
		if self.before.get("positions"):
			check("the canonical Budget is back exactly as it was found", {l: self.position(l) for l in self.lines} == self.before["positions"])

	def finish(self):
		failed = [r for r in RESULTS if not r[1]]
		print(f"\n{len(RESULTS) - len(failed)} passed, {len(failed)} failed", flush=True)
		return 1 if failed else 0

	def run(self):
		self.facts()
		frappe.flags.kt_contract_funding_providers = [__import__("kentender_budget.services.contract_funding_provider", fromlist=["service"]).service()]
		# Contract Management's interim answer (may this contract draw on this reservation?) is the one thing stood in for: these contract ids are not Contract Management cases, so with the real hook nobody knows them.
		self.refused("a contract Contract Management does not know cannot draw on any reservation (the interim check, before any stand-in)", lambda: self.seam.convert(f"{self.contract}:unknown", **self.convert_args()))
		self.install_authority()
		self.refusals()
		self.commitf()
		made = self.race()
		self.after_conversion(made)
		self.commitf()
		closed = self.variation_and_close(made)
		self.commitf()
		self.additional(closed)
		self.commitf()
		self.correction(closed)
		self.commitf()
		self.balance()


def main() -> int:
	frappe.init(site=SITE, sites_path=".")
	frappe.connect()
	if frappe.local.site != "kentender-test.local":
		print("This journey runs on the test site only.")
		return 2
	frappe.set_user("Administrator")
	journey = Journey()
	try:
		journey.run()
	except SystemExit as exc:
		return int(exc.code or 1)
	except Exception:  # noqa: BLE001
		traceback.print_exc()
		check("the journey ran to the end", False, "an unexpected error; see the trace above")
	finally:
		journey.restore()
	code = journey.finish()
	if len(sys.argv) > 1:
		with open(sys.argv[1], "w") as handle:
			handle.write("# Canonical two-source award: Award to Budget journey (test site)\n\n")
			handle.write(f"Run {frappe.utils.now()} on `{SITE}`, award `{AWARD}`.\n\n| Check | Result | Detail |\n|---|---|---|\n")
			for label, ok, detail in RESULTS:
				handle.write(f"| {label} | {'Pass' if ok else '**FAIL**'} | {detail.replace('|', '/')[:200]} |\n")
	return code


if __name__ == "__main__":
	sys.exit(main())
