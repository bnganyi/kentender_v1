# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening demo profiles: the opening's stages, loaded one at a time on the
canonical world so a person can walk them in the browser (BOP-CHG-001 v0.10
§10; the Requisitions demo-profile precedent, REQ-CHG-001 v1.11 §16.4A).

Every profile except the no-bids one is the canonical Tender's own opening
(TND-MOH-2027-002, submissions closed 12 Jun 2027 11:00) told up to one moment
by the real commands, as the canonical people: Amina Hassan (Accounting
Officer), Charles Mutiso (chair and recorder), Brian Wafula (member), Beatrice
Kamau (independent member), Daniel Otieno (Opening access support), David Ouma
(Afya Digital Supplies Limited) and Jane Wanjiku (public observer). The site's
test clock is set to that moment, so every screen is live: the next person
acts from their own page, and the opening moves on through the real
commands. The no-bids profile needs a Tender with an empty box, which the
canonical world does not have; it uses the browser-test Tender (people named
in its report).

`restore_base()` removes whatever profile is loaded, tells the canonical
opening again to completion and clears the test clock. While a profile is
loaded, `seed-canonical-validate` reports the opening as not complete.

Each profile returns a report: what it shows, the site clock, who to sign in
as, where to click, what to do, and observed checks (each named person's next
step as the server answers it)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

LOADED_KEY = "kt_bop_loaded_profile"
DOMAIN = "moh.example.test"
AMINA, CHARLES, BRIAN, BEATRICE, DANIEL = (f"{x}@{DOMAIN}" for x in ("amina.hassan", "charles.mutiso", "brian.wafula", "beatrice.kamau", "daniel.otieno"))
DAVID, JANE = "david.ouma@afyadigital.example", "jane.wanjiku@observer.example"
NAMES = {AMINA: "Amina Hassan", CHARLES: "Charles Mutiso", BRIAN: "Brian Wafula", BEATRICE: "Beatrice Kamau", DANIEL: "Daniel Otieno", DAVID: "David Ouma",
	JANE: "Jane Wanjiku"}
CAST = {"ao": AMINA, "chair": CHARLES, "member": BRIAN, "independent": BEATRICE, "support": DANIEL}
PUBLIC = ((DAVID, -120), (JANE, -60))  # 10:58 and 10:59, as the boards show


def _desk(reference: str) -> str:
	return f"Tenders (under Tender Management) → {reference} → Bid opening"


def _public(reference: str) -> str:
	return f"/tenders/{reference}/opening"


# (profile, title, walker stage, seconds from the deadline to set the clock to
# (None: the stage's own moment), controls, what to do: [(person, action)],
# expected next steps: {person: headline start})
PROFILES: dict[str, dict[str, Any]] = {
	"BOP-DEMO-APPOINT": {
		"title": "The committee is not yet appointed", "stage": "prepared", "boards": "a1, a2",
		"steps": [(AMINA, "Add Charles Mutiso (chair and recorder), Brian Wafula (member) and Beatrice Kamau (independent member); try appointing with two first to see the refusal; then Appoint committee.")],
		"expect": {AMINA: "Appoint opening committee"},
	},
	"BOP-DEMO-PUBLISH": {
		"title": "Committee appointed; how to attend not yet published", "stage": "appointed", "boards": "a3, a4",
		"steps": [(AMINA, "Publish how to attend."), (BEATRICE, "Open the notification \"You are on the opening committee …\" (bell) to reach the opening.")],
		"expect": {AMINA: "Publish how to attend"},
	},
	"BOP-DEMO-BEFORE-JOIN": {
		"title": "Published; members cannot join yet", "stage": "published", "at": -1200, "boards": "a5, c1 (timed), p1a",
		"steps": [(CHARLES, "See \"You can join from 12 Jun 2027, 10:55 EAT.\""), (JANE, f"Public page {_public('{ref}')}: how to attend, join not open yet.")],
		"expect": {CHARLES: "You can join from"},
	},
	"BOP-DEMO-JOIN": {
		"title": "Join window open (10:56)", "stage": "published", "at": -240, "boards": "c1, p1",
		"steps": [(CHARLES, "Join opening."), (BRIAN, "Join opening."), (BEATRICE, "Join opening (from the bell notification)."),
			(JANE, f"Sign in and Join public opening at {_public('{ref}')}.")],
		"expect": {CHARLES: "Join opening for", BRIAN: "Join opening for"},
	},
	"BOP-DEMO-MISSING-MEMBER": {
		"title": "Submissions closed; Beatrice has not joined", "stage": "missing", "boards": "c2",
		"steps": [(CHARLES, "See who is missing; Notify Beatrice Kamau."), (BEATRICE, "Join opening."), (CHARLES, "Start opening.")],
		"expect": {CHARLES: "Opening cannot start because Beatrice Kamau has not joined."},
	},
	"BOP-DEMO-READY": {
		"title": "Everyone present; ready to start (walk the whole opening from here)", "stage": "ready", "boards": "c3 → c4 … c9 → r1 … r6",
		"steps": [(CHARLES, "Start opening; Open next bid."), (BRIAN, "Read the details aloud."), (CHARLES, "Record what was read aloud; End opening; Prepare and finish the opening record; sign."),
			(BRIAN, "Review and sign."), (BEATRICE, "Review and sign — the last signature completes the opening.")],
		"expect": {CHARLES: "Ready to start"},
	},
	"BOP-DEMO-READ-ALOUD": {
		"title": "A bid is open; waiting for it to be read aloud and recorded", "stage": "opened", "boards": "c5, c6",
		"steps": [(BRIAN, "Read these details aloud."), (CHARLES, "Record what was read aloud.")],
		"expect": {BRIAN: "Read these details aloud", CHARLES: "Record what was read aloud"},
	},
	"BOP-DEMO-REQUESTS": {
		"title": "Bid read out; a request answered; ready to end", "stage": "answered", "boards": "c7, c8, c13, c9",
		"steps": [(CHARLES, "Record a request or a comment for Evaluation; End opening."), (BEATRICE, "Record my differing account."),
			(JANE, f"Public page {_public('{ref}')}: the bid appears as read aloud.")],
		"expect": {CHARLES: "End the opening"},
	},
	"BOP-DEMO-MEMBER-LEFT": {
		"title": "Paused: Beatrice left during the opening", "stage": "member-left", "boards": "c10",
		"steps": [(CHARLES, "See the pause; Notify Beatrice Kamau."), (BEATRICE, "Rejoin opening — the opening continues."),
			(AMINA, "(Only if Beatrice cannot return) Appoint a replacement, with a reason.")],
		"expect": {CHARLES: "Waiting for Beatrice Kamau to rejoin"},
	},
	"BOP-DEMO-CANNOT-OPEN": {
		"title": "Paused: the bid could not be opened; support is checking", "stage": "unreadable", "boards": "c11",
		"steps": [(CHARLES, "See why; Retry is not available until support resolves it."), (DANIEL, "See the problem notification; technical status only.")],
		"expect": {CHARLES: "This bid could not be opened"},
	},
	"BOP-DEMO-RETRY": {
		"title": "Support resolved the problem; retry opening", "stage": "resolved", "boards": "c11b",
		"steps": [(CHARLES, "Retry opening — the same bid opens.")],
		"expect": {CHARLES: "Retry opening"},
	},
	"BOP-DEMO-AO-DECISION": {
		"title": "Support could not fix it; the Accounting Officer decides", "stage": "unresolved", "boards": "c11c, c11e",
		"steps": [(AMINA, "Decide how to proceed with the paused opening (no Tender route exists yet in this version)."), (CHARLES, "Waiting for Amina Hassan.")],
		"expect": {AMINA: "Decide how to proceed with the paused opening"},
	},
	"BOP-DEMO-SIGN": {
		"title": "Opening record finished; Brian has signed", "stage": "member-signed", "boards": "r3, r4",
		"steps": [(BEATRICE, "Review and sign."), (CHARLES, "Review and sign — the last signature completes the opening.")],
		"expect": {BEATRICE: "Review and sign opening record", BRIAN: "Waiting for"},
	},
	"BOP-DEMO-NOT-HELD": {
		"title": "The opening never started (public attendance service down)", "stage": "not-held-due", "boards": "n1 → n2",
		"steps": [(AMINA, "Record that the opening did not take place, with the reason.")],
		"expect": {AMINA: "The opening has not started; record what happened"},
	},
	"BOP-DEMO-NO-BIDS": {
		"title": "No bids were submitted (browser-test Tender)", "stage": "empty-started", "boards": "z1 → h2", "world": "browser",
		"steps": [], "expect": {},
	},
}


def list_profiles() -> list[dict[str, str]]:
	return [{"profile": k, "title": v["title"], "boards": v["boards"]} for k, v in PROFILES.items()]


def loaded_profile() -> str:
	return cstr(frappe.db.get_default(LOADED_KEY))


def _canonical() -> tuple[str, str]:
	from kentender_procurement.bid_opening.seeds import kentender_mvp_v1 as base

	tender = base.canonical_tender()
	if not tender or not frappe.db.exists("Bid Submission Close", {"tender": tender}):
		frappe.throw("Seed the canonical world through bid_opening first: make seed-canonical THROUGH=bid_opening.")
	return tender, cstr(frappe.db.get_value("Tender", tender, "tender_reference"))


def _clear_loaded() -> None:
	"""Undo any loaded profile's world: the browser-test world, the test
	controls and the clock."""
	from kentender_core.services import test_clock

	from kentender_procurement.bid_opening.services import simulation
	from kentender_procurement.bid_submission.services import simulation as bds_simulation

	if PROFILES.get(loaded_profile(), {}).get("world") == "browser":
		from kentender_procurement.bid_opening.seeds import playwright_ui_fixtures as world

		world.restore_site(commit=False)
	simulation.reset_controls()
	bds_simulation.set_controls(custody_service_down=0, reveal_outcome="Deliver")
	test_clock.set_instant(None)
	frappe.db.set_default(LOADED_KEY, "")


def _checks(tender: str, expect: dict[str, str]) -> list[dict[str, Any]]:
	from kentender_procurement.bid_opening.services import reads

	out = []
	for user, start in expect.items():
		frappe.set_user(user)
		try:
			answer = reads.get_opening(tender=tender, user=user)["next_step"]
		finally:
			frappe.set_user("Administrator")
		out.append({"person": NAMES.get(user, user), "expected": start, "observed": answer.get("headline"), "ok": cstr(answer.get("headline")).startswith(start)})
	return out


def load_profile(*, profile: str, commit: bool = True) -> dict[str, Any]:
	from kentender_core.services import test_clock

	from kentender_procurement.bid_opening.seeds import clear
	from kentender_procurement.bid_opening.seeds import kentender_mvp_v1 as base
	from kentender_procurement.bid_opening.seeds import playwright_ui_fixtures as world

	if profile not in PROFILES:
		frappe.throw(f"Unknown Bid Opening profile {profile!r}. One of: {', '.join(PROFILES)}")
	spec = PROFILES[profile]
	frappe.set_user("Administrator")
	_clear_loaded()
	if spec.get("world") == "browser":
		built = world.reset_opening_fixture(stage=spec["stage"], commit=False)
		frappe.db.set_default(LOADED_KEY, profile)
		report = {
			"profile": profile, "title": spec["title"], "boards": spec["boards"], "tender": built["tender_reference"], "site_clock": built["instant"],
			"where": _desk(built["tender_reference"]), "password": "the shared fixture password (.env.ui)",
			"do": [{"person": "Charles Mutiso (pw.req.hopf@example.test)", "action": "End opening with no bids; then prepare, finish and sign the record."},
				{"person": "Playwright Tenders Officer (pw.tnd.officer@example.test) and Playwright Independent (pw.bop.independent@example.test)",
					"action": "Review and sign."}],
			"checks": [], "note": "The canonical Tender has a bid, so this profile uses the browser-test Tender, whose box is empty; restore removes it.",
		}
		if commit:
			frappe.db.commit()
		return report
	tender, reference = _canonical()
	clear.wipe(tenders=[tender], namespace=base.NAMESPACE)
	walker = world.OpeningWorld(tender, reference, cast=CAST, box_closed=True, public=PUBLIC)
	saved = {flag: frappe.flags.get(flag) for flag in ("kt_bop_fixture_namespace", "kt_prc_fixture_namespace", "kt_bop_clock", "kt_prc_clock", "kt_bds_clock", "kt_tenders_clock")}
	frappe.flags.kt_bop_fixture_namespace = frappe.flags.kt_prc_fixture_namespace = base.NAMESPACE  # canonical rows: the canonical clear keeps them
	try:
		walker.run(spec["stage"])
		if spec.get("at") is not None:
			walker.at(spec["at"])
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value
	from kentender_procurement.bid_submission.services import simulation as bds_simulation

	bds_simulation.set_controls(reveal_outcome="Deliver")
	test_clock.set_instant(walker.instant)
	frappe.db.set_default(LOADED_KEY, profile)
	report = {
		"profile": profile, "title": spec["title"], "boards": spec["boards"], "tender": reference, "site_clock": walker.instant, "where": _desk(reference),
		"public_page": _public(reference), "password": "the shared fixture password (.env.ui)",
		"do": [{"person": f"{NAMES[user]} ({user})", "action": action.replace("{ref}", reference)} for user, action in spec["steps"]],
		"checks": _checks(tender, spec["expect"]),
	}
	if commit:
		frappe.db.commit()
	return report


def restore_base(*, commit: bool = True) -> dict[str, Any]:
	"""Remove the loaded profile, tell the canonical opening again to
	completion, and clear the test clock."""
	from kentender_procurement.bid_opening.seeds import clear
	from kentender_procurement.bid_opening.seeds import kentender_mvp_v1 as base

	frappe.set_user("Administrator")
	was = loaded_profile()
	_clear_loaded()
	tender, reference = _canonical()
	clear.wipe(tenders=[tender], namespace=base.NAMESPACE)
	built = base.upsert_bid_opening_base(commit=False)
	failures = [r["check"] for r in base.validate_bid_opening_seed() if not r["ok"]]
	if commit:
		frappe.db.commit()
	return {"restored": True, "was": was or None, "tender": reference, "opening": built.get("opening"), "failures": failures}
