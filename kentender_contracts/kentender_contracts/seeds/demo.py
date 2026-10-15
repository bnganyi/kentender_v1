# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract Management demonstration profiles (CM-CHG-001 v0.8 section 13; plan Phase 11; tracker CM8-1101, CM8-1102; CM-AC-21). Development only; a simulation site only.

A profile puts the site on one stage of one contract: the ten-laptop demonstration of the boards (its own synthetic Award package and identifiers, so it can never overwrite a canonical chain), told through the
**same services as production** with the seed world's own people, and the site's clock set to the moment the stage reaches so the live pages read it as it stood. Trust (signing) and Finance (settlement) evidence is
simulated and carried as such in the records (the source and the signing provider are synthetic); nothing is shown to a user as a test label (DEC-044), and nothing is sent, signed or banked outside the site.

Profiles are isolated: one contract at a time, because the clock is the site's. Running the profile that is already in place changes nothing (the same identities, no new history); running another removes the first and
builds the second. `clean` removes the contract, its native documents and the responsibilities granted for it, and puts the clock back.

    make seed-cm-profile SITE=<site> PROFILE=<name>       # RECEIVED SIGNING ACTIVE ACCEPTED PAID CHANGE WARRANTY TERMINATION CLOSED
    make seed-cm-clean SITE=<site>

Why a profile and not a stage of the canonical seed world: that world is read as at 18 June 2027 10:00, and a contract exists only from 2 July 2027 09:00, when the Award package reaches Contracting (the award seed's
AWD-DEMO-DELIVERED profile); a stage inside the as-at world would carry events after its own as-at instant. The canonical chain from Award's real package is received by Contract Management's real receiver and stays
blocked by the sources nobody supplies yet (FU-CM-70, 71, 72); these profiles do not stand in for it."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import frappe
from frappe.utils.password import update_password

from kentender_contracts.services import records, simulation

NAMESPACE = "CM_DEMO"
PASSWORD = "CmDemo-2027-Aa1!"
#: the seed world's own people (SEED-002); their contract responsibilities are granted for the demonstration and removed by `clean`
CANONICAL = {
	"charles": "charles.mutiso@moh.example.test", "brian": "brian.wafula@moh.example.test", "amina": "amina.hassan@moh.example.test", "julia": "julia.njeri@moh.example.test",
	"peter": "peter.mugo@moh.example.test", "grace": "grace.wanjiku@moh.example.test", "josphat": "josphat.mwangi@moh.example.test", "beatrice": "beatrice.kamau@moh.example.test",
	"daniel": "daniel.otieno@moh.example.test", "naomi": "naomi.chebet@moh.example.test", "mary": "mary.wanjiku@afyadigital.example", "david": "david.ouma@afyadigital.example",
}
EVIDENCE = [{"label": "Notice and delivery proof", "file": "/private/files/demo-notice.pdf"}]


@dataclass(frozen=True)
class Profile:
	name: str
	at: str  # the site's clock when the stage is reached
	summary: str
	build: Callable[[Any], None]
	expects: tuple[tuple[str, str], ...]  # (person, the command of the step that is theirs); empty when the stage leaves nobody a step
	lifecycle: str
	award_suffix: str = ""


def _owner(t) -> None:
	frappe.db.set_value("Contract Case", t.case, "responsible_user", t.p["julia"])


def _received(t) -> None:
	from kentender_contracts.tests import thread_world as tw

	out = tw.receive(t.p, contract_id=t.contract_id, award_case=t.award_case)
	t.case = out["contract"]


def _signing(t) -> None:
	from kentender_contracts.services import formation
	from kentender_contracts.tests import thread_world as tw

	_received(t)
	formation.save_particulars(t.case, expected_version=t.version(), idempotency_key=t.key("particulars"), actor=t.p["brian"], values=tw.package_particulars(t.p, False, t.item))
	formation.request_signatures(t.case, expected_version=t.version(), idempotency_key=t.key("send"), actor=t.p["charles"])
	formation.sign_contract(t.case, party="Supplier", expected_version=t.version(), idempotency_key=t.key("sign-s"), actor=t.p["mary"])


def _active(t) -> None:
	t.active()
	t.appointed()
	_owner(t)


def _accepted(t, count: int = 10) -> list[str]:
	from kentender_contracts.tests import thread_world as tw

	_active(t)
	frappe.flags.kt_cm_clock = "2027-07-12 10:00:00"
	units = tw.fresh_serials(count)
	arrival = t.arrive(units, received_at="2027-07-12 10:00:00")["arrival"]
	t.inspect(arrival, units)
	frappe.flags.kt_cm_clock = "2027-07-20 10:00:00"
	t.accept(arrival)
	return units


def _claimed(t) -> str:
	frappe.flags.kt_cm_clock = "2027-07-21 08:05:00"
	return t.claim("DEMO-INV-1", 10)["invoice"]


def _accepted_and_claimed(t) -> None:
	_accepted(t)
	_claimed(t)


def _paid(t) -> None:
	_accepted(t)
	invoice = _claimed(t)
	frappe.flags.kt_cm_clock = "2027-07-22 09:00:00"
	t.certify_invoice(invoice)
	frappe.flags.kt_cm_clock = "2027-07-25 09:00:00"
	t.pay(invoice, "DEMO-BANK-1")


def _change(t) -> None:
	from kentender_contracts.services import change

	_active(t)
	frappe.flags.kt_cm_clock = "2027-07-14 09:00:00"
	change.request_change(t.case, kind="Extension", request={"proposed_date": "2027-07-27"}, reason="Supplier reports a seven-day shipment delay.", evidence=EVIDENCE, expected_version=t.version(),
		idempotency_key=t.key("ask"), actor=t.p["david"])
	roster = dict(zip(change.REVIEW_KINDS["Extension"], (t.p["peter"], t.p["julia"], t.p["brian"]), strict=True))
	change.appoint_reviewers(t.case, change=1, reference="AO/VAR/2027/001", reviewers=roster, expected_version=t.version(), idempotency_key=t.key("appoint"), actor=t.p["charles"])


def _warranty(t) -> None:
	from kentender_contracts.services import warranty

	units = _accepted(t)
	frappe.flags.kt_cm_clock = "2028-07-10 09:00:00"
	warranty.record_claim(t.case, unit=units[3], fault="Battery does not charge", notice_date="2028-07-10", remedy="Like-for-like replacement", expected_version=t.version(), idempotency_key=t.key("claim"), actor=t.p["julia"])


def _termination(t) -> None:
	from kentender_contracts.services import termination

	_accepted(t, 8)
	frappe.flags.kt_cm_clock = "2027-07-30 09:00:00"
	termination.request(t.case, grounds="Material non-delivery", clause="Contract clause 8", recommendation="Terminate the unperformed balance", evidence=EVIDENCE, expected_version=t.version(), idempotency_key=t.key("term"),
		actor=t.p["charles"])


def _closed(t) -> None:
	from kentender_contracts.services import closeout, final_acceptance

	_paid(t)
	frappe.flags.kt_cm_clock = "2028-07-28 08:30:00"
	final_acceptance.sign(t.case, expected_version=t.version(), idempotency_key=t.key("final"), actor=t.p["amina"])
	frappe.flags.kt_cm_clock = "2028-07-28 09:00:00"
	closeout.issue_completion_certificate(t.case, expected_version=t.version(), idempotency_key=t.key("completion"), actor=t.p["charles"])
	t.confirm_delivery()
	frappe.flags.kt_cm_clock = "2028-07-28 10:00:00"
	review = frappe.db.get_value("Contract Closeout", {"contract_case": t.case, "state": "Awaiting signature"}, "name")
	closeout.sign_closeout(t.case, closeout=review, expected_version=t.version(), idempotency_key=t.key("close"), actor=t.p["amina"])


PROFILES: dict[str, Profile] = {p.name: p for p in (
	Profile("RECEIVED", "2027-07-02 09:00:00", "The Award package has reached Contracting; the head of procurement prepares the contract.", _received, (("charles", "RequestContractSignatures"),), "Preparing"),
	Profile("SIGNING", "2027-07-03 10:00:00", "The agreement is out for signature and the supplier has signed; the Accounting Officer signs for the entity.", _signing, (("amina", "SignContractVersion"),), "Awaiting signatures"),
	Profile("ACTIVE", "2027-07-05 09:00:00", "The agreement is in force with its order; the inspectors are appointed and ready for the first delivery.", _active, (), "Active"),
	Profile("ACCEPTED", "2027-07-21 09:00:00", "Ten laptops were delivered, inspected and accepted, and the supplier has claimed for them.", _accepted_and_claimed, (("charles", "SignContractCertification"),), "Active"),
	Profile("PAID", "2027-07-25 14:00:00", "The claim was certified, posted and paid in full.", _paid, (), "Active"),
	Profile("CHANGE", "2027-07-14 10:00:00", "A delivery extension is requested and its reviewers are named.", _change, (("peter", "RecordContractChangeReview"),), "Active"),
	Profile("WARRANTY", "2028-07-10 10:00:00", "A warranty claim is recorded on an accepted unit and its defect notice is next.", _warranty, (("julia", "SendContractCorrespondence"),), "Active"),
	Profile("TERMINATION", "2027-07-30 10:00:00", "Termination of the unperformed balance is requested; the Accounting Officer decides.", _termination, (("amina", "DecideContractTermination"),), "Active"),
	Profile("CLOSED", "2028-07-28 11:00:00", "The final acceptance, the completion certificate and its delivery are recorded and the contract is closed.", _closed, (), "Closed", award_suffix="-FIN"),
)}


def state_file() -> Path:
	"""Where a browser walk reads the world from, and where the clock that was in place is kept so `clean` puts it back."""
	return Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "artifacts/cm-demo-world.json"


def _previous_instant() -> Any:
	file = state_file()
	return (json.loads(file.read_text()).get("previous_instant") or None) if file.exists() else None


def _guard() -> None:
	if not simulation.enabled():
		frappe.throw("The Contract Management demonstration profiles use simulated Trust and Finance evidence and run on a simulation site only.")
	if "kentender_contracts" not in frappe.get_installed_apps():
		frappe.throw("Contract Management is not installed on this site.")


def _contract(profile: Profile) -> str:
	return f"CM-DEMO-{profile.name}"


def _case_of(profile: Profile) -> str:
	return frappe.db.get_value("Contract Case", {"contract_id": _contract(profile), "fixture_namespace": NAMESPACE}, "name") or ""


def present() -> str:
	"""The profile now in place, or empty."""
	for profile in PROFILES.values():
		if _case_of(profile):
			return profile.name
	return ""


def problems(profile: Profile) -> list[str]:
	"""Everything that keeps the profile's contract from being the stage it claims to be (empty means it is)."""
	from kentender_contracts.services import work

	case = _case_of(profile)
	if not case:
		return [f"{_contract(profile)} does not exist"]
	found = []
	lifecycle = frappe.db.get_value("Contract Case", case, "lifecycle")
	if lifecycle != profile.lifecycle:
		found.append(f"the lifecycle is {lifecycle}, not {profile.lifecycle}")
	live = {(t["holder"].lower(), t["command"].split(":")[0]) for t in work.live(case) if t["state"] in ("actionable", "blocked")}
	for person, command in profile.expects:
		if (CANONICAL[person].lower(), command) not in live:
			found.append(f"{person} has no {command} step")
	return found


def _steps(profile: Profile, case: str) -> list[dict[str, str]]:
	"""Who has a step on the contract and what it says, for a walk to look for."""
	from kentender_contracts.services import work

	live = [t for t in work.live(case) if t["state"] in ("actionable", "blocked")]
	found = []
	for person, command in profile.expects:
		task = next((t for t in live if t["holder"].lower() == CANONICAL[person].lower() and t["command"].split(":")[0] == command), None)
		found.append({"persona": person, "email": CANONICAL[person], "command": command, "headline": task["title"] if task else ""})
	return found


def validate(profile: str = "") -> dict[str, Any]:
	chosen = PROFILES[profile or present()]
	found = problems(chosen)
	return {"profile": chosen.name, "problems": found, "ok": not found}


def clean() -> dict[str, Any]:
	"""Remove the demonstration contract, its native documents and the responsibilities granted for it; put the clock back."""
	from kentender_contracts.tests import native_world as world
	from kentender_contracts.tests import thread_world as tw
	from kentender_core.services import test_clock

	_guard()
	frappe.set_user("Administrator")
	cases = frappe.get_all("Contract Case", filters={"fixture_namespace": NAMESPACE}, pluck="name")
	for case in cases:
		for doctype in records.DOCTYPES:
			if doctype in ("Contract Case", "Contract Simulated Signature", "Contract Simulated Funding") or not frappe.get_meta(doctype).has_field("contract_case"):
				continue
			frappe.db.delete(doctype, {"contract_case": case})
		frappe.db.delete("Contract Simulated Funding", {"contract": case})
		frappe.db.delete("Notification Log", {"document_type": "Contract Case", "document_name": case})
		frappe.db.delete("Contract Case", {"name": case})
	frappe.db.delete("Contract Command Journal", {"fixture_namespace": NAMESPACE})
	frappe.db.delete("Contract Simulated Signature", {"signer": ["in", list(CANONICAL.values())], "fixture_namespace": NAMESPACE})
	for name in frappe.get_all("File", filters={"file_name": ["like", "cm-test-%"]}, pluck="name"):
		frappe.delete_doc("File", name, force=True, ignore_permissions=True)
	frappe.db.commit()
	failed = world.teardown() if cases else {}
	tw.teardown(NAMESPACE)
	test_clock.set_instant(_previous_instant())
	if state_file().exists():
		state_file().unlink()
	frappe.db.commit()
	return {"removed": cases, "native_not_removed": failed}


def run(profile: str = "ACTIVE", rebuild: bool = False, passwords: bool = False) -> dict[str, Any]:
	"""Put the site on one profile. The profile already in place is left exactly as it is (`rebuild` builds it again). `passwords` sets a known password for the seed world's people on this copy (a browser walk signs in with it)."""
	from kentender_contracts.tests import native_world as world
	from kentender_contracts.tests import thread_world as tw
	from kentender_core.services import test_clock

	_guard()
	chosen = PROFILES.get(profile)
	if chosen is None:
		frappe.throw(f"Unknown profile {profile!r}; expected one of {', '.join(PROFILES)}")
	if present() == chosen.name and not rebuild and not problems(chosen):
		test_clock.set_instant(chosen.at)
		return {"profile": chosen.name, "contract": _case_of(chosen), "built": False, "problems": []}
	previous = _previous_instant() if state_file().exists() else test_clock.current_instant()  # the clock before any profile was put on the site, kept across profiles
	clean()
	frappe.set_user("Administrator")
	frappe.flags.kt_cm_fixture_namespace = NAMESPACE
	frappe.conf.kt_cm_simulation_environment = 1
	tw.ADDRESSES.update(CANONICAL)
	test_clock.set_instant("2027-07-02 09:00:00")
	world.build()
	world.ensure_workflow()
	people = tw.build(NAMESPACE)
	people.update({k: v for k, v in CANONICAL.items() if k in ("mary", "david", "naomi")})
	if passwords:
		for address in set(people.values()):
			if frappe.db.exists("User", address):
				update_password(address, PASSWORD)
	frappe.db.commit()
	frappe.flags.kt_contract_source_providers = None
	t = tw.Thread(people, tag=f"DEMO{chosen.name[:6]}", contract_id=_contract(chosen), award_case=f"CM-DEMO-AWD-{chosen.name}{chosen.award_suffix}", item=world.ITEM_PLAIN)
	frappe.flags.kt_cm_clock = "2027-07-02 09:00:00"
	try:
		chosen.build(t)
		frappe.db.commit()
	finally:
		frappe.flags.kt_cm_clock = None
		frappe.flags.kt_contract_source_providers = None
	test_clock.set_instant(chosen.at)  # the live pages read the stage as it stood
	frappe.db.commit()
	found = problems(chosen)
	case = _case_of(chosen)
	out = {"profile": chosen.name, "contract": case, "built": True, "at": chosen.at, "problems": found}
	state_file().parent.mkdir(parents=True, exist_ok=True)
	state_file().write_text(json.dumps({**out, "previous_instant": str(previous or ""), "password": PASSWORD, "summary": chosen.summary, "people": CANONICAL, "steps": _steps(chosen, case)}, indent=1))
	return out
