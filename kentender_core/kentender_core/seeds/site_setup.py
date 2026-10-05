# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-STD-001 v1.1 §8 — the canonical site fixture world, seeded through the
same public commands as the UI (§8.6: seeds never write a governed DocType
directly; they are deterministic and idempotent, create no legacy authority
row, and never grant a business role to Administrator).

Run:
  bench --site <site> execute kentender_core.seeds.site_setup.run

Idempotency: every step is find-or-skip. Organisation units are addressed by
their §8.2 names (the add command's normalised-sibling rule already collapses
a re-run onto the existing unit); unit *codes* are server-generated
`OU-MOH-{sequence}` values — the §8.2 mnemonic codes (`OU-MOH-DHP`) cannot be
produced through the governed command, which never accepts a user-entered
code (CFG v0.6 §4.3). Recorded as conflict C4 in the tracker.

Conflicting authoritative data fails the seed rather than being repaired
(§8.6): a site configured as a different Procuring Entity raises.
"""

from __future__ import annotations

import frappe

from kentender_core.services import organisation_structure as structure
from kentender_core.services import responsibility_administration as administration
from kentender_core.services import site_configuration as configuration

FIXTURE_TAG = "KT_STD_001_S8"

SITE = {
	"pe_name": "Ministry of Health",
	"pe_code": "PE-MOH",
	"pe_type": "National Government Ministry",
	"ppra_registration": "PPRA/PE/2019/0114",
	"timezone": "Africa/Nairobi",
	# CFG-CHG-002 v0.9 §4.1 / PLN-CHG-001 v1.12 §14.6 — the configured route.
	"statutory_approval_route": "Cabinet Secretary",
	"entity_is_county": False,
}

UNITS = (
	# (unit name, parent unit name or None for the root)
	("Directorate of Digital Health and Policy", None),
	("Digital Health", "Directorate of Digital Health and Policy"),
	("Human Resources Management and Development", None),
)

FISCAL_START_YEARS = (2026, 2027)
INTAKE = {"start_year": 2027, "closes_at": "2026-11-25 23:59:00"}
# PLN-CHG-001 v1.12 §14.1 — departmental-plan intake for FY 2027/28 closes
# 30 Nov 2026, 23:59:59 EAT, stored in site time like every instant (owner
# decision 26 Sep 2026; it was stored as UTC, so the gate, which compares
# against the site clock, closed it at 20:59 EAT).
DPP_INTAKE = {"start_year": 2027, "closes_at": "2026-11-30 23:59:59"}
# CFG-CHG-002 v0.11 §4.3 — the third registered intake. Disposal plans are
# called for the same year as the procurement plan; nothing consumes the
# flag yet, but the Financial years tab lists the activity, so a seed that
# left it closed showed one permanently unfinished row.
DISPOSAL_INTAKE = {"start_year": 2027, "closes_at": "2026-11-30 23:59:59"}

# CFG-CHG-002 v0.9 §3 — the requirement-type and procurement-method
# catalogues Configuration & Governance owns (PLN-CHG-001 v1.12 §14.1: four
# types incl. Works; the eleven Third Schedule methods, Open Tender first).
# PLN-CHG-001 v1.23 §4.4 — the governed requirement-type catalogue carries its
# own procurement category. The Planner selects only the type; the server
# derives the category from this catalogue entry and rejects a client-supplied
# one. Never re-express this mapping as a module constant in a consumer.
REQUIREMENT_TYPES = (
	("Non-consulting services", "Services"),
	("Consulting services", "Services"),
	("Goods", "Goods"),
	("Works", "Works"),
)
PROCUREMENT_METHODS = (
	"Open Tender",
	"Direct Procurement",
	"Restricted Tender",
	"Request for Quotations",
	"Low Value Procurement",
	"Community Participation",
	"Design Competition",
	"Electronic Reverse Auction",
	"Force Account",
	"Competitive Negotiations",
	"Request for Proposals",
)

# CFG-CHG-002 v0.9 §4.4A / PLN-CHG-001 v1.12 §14.1 — the Second Schedule
# matrix in force for FY 2027/28. `max_amount` 0 = no fixed maximum.
_KES = 1.0
THRESHOLD_BANDS = (
	# (method, goods max, works max, services max, basis, reference)
	("Low Value Procurement", 50_000, 100_000, 50_000, "Per item per financial year", "Second Schedule; s.107"),
	("Request for Quotations", 3_000_000, 5_000_000, 3_000_000, "Per request", "Second Schedule; s.105"),
	("Restricted Tender", 30_000_000, 30_000_000, 20_000_000, "Per procurement", "Second Schedule; s.102(1)(b)"),
	("Open Tender", 0, 0, 0, "Funds allocated", "Second Schedule; s.96"),
	("Request for Proposals", 0, 0, 0, "Funds allocated", "Second Schedule; s.116"),
	("Direct Procurement", 0, 0, 0, "Section conditions", "Second Schedule; s.103"),
	("Community Participation", 0, 0, 0, "Funds allocated", "reg 109"),
	("Design Competition", 0, 0, 0, "Funds allocated", "s.92(1)"),
	("Electronic Reverse Auction", 0, 0, 0, "Funds allocated", "s.92(1)"),
	("Force Account", 0, 0, 0, "Funds allocated", "reg 95"),
	("Competitive Negotiations", 0, 0, 0, "Funds allocated", "s.92(1)"),
)
# PLN-CHG-001 v1.12 §4.9 governed reservation values; rank 1 = highest
# advantage (section 156 / regulation 153), 0 = None.
RESERVATION_CATEGORIES = (
	("None", 0, False, ""),
	("Youth", 1, False, "s.157(4); reg 149"),
	("Women", 1, False, "s.157(4); reg 149"),
	("Persons with disabilities", 1, False, "s.157(4); reg 149"),
	("Other disadvantaged group", 2, False, "s.157(4)"),
	("Micro, small and medium enterprise", 3, False, "s.157(4)"),
	("Regional — county", 4, True, "reg 151"),
	("Regional — sub-county", 4, True, "reg 151"),
	("Regional — constituency", 4, True, "reg 151"),
	("National reservation — citizen contractor", 5, False, "s.157(8)(a); reg 163"),
)
REGULATORY_REFERENCE = {
	"gazette_reference": "PPADR 2020 Second Schedule (rev. 2022) — FY 2027/28",
	"effective_from": "2027-07-01",
	"reservation_target_percent": 30,
	"county_resident_target_percent": 20,
	"exclusive_preference_works_amount": 1_000_000_000,
	"exclusive_preference_goods_services_amount": 500_000_000,
}

ACTORS = (
	# (local part, full name)
	("grace.wanjiku", "Grace Wanjiku"),
	("peter.kimani", "Dr Peter Kimani"),
	("julia.njeri", "Julia Njeri"),
	("mercy.kilonzo", "Mercy Kilonzo"),
	("samuel.otieno", "Samuel Otieno"),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04): Departmental Needs' Auditor actor,
	# per KT-STD-001 §8.3's shared register. Extends the register the same way
	# CU-307 extended Mercy's assignments — one canonical fixture world, not a
	# module-owned duplicate.
	("naomi.chebet", "Naomi Chebet"),
	# STR-CHG-001 v1.7 §14.1 / KT-STD-001 §8.3 (2026-09-05) — Strategy's own
	# named actors. Supersede CU-307's Mercy stand-in below, which existed
	# only because these two did not yet exist.
	("esther.muthoni", "Esther Muthoni"),
	("alfred.ochieng", "Dr Alfred Ochieng"),
	# BUD-CHG-001 v1.6 §15.1 / KT-STD-001 §8.3 (2026-09-06) — Budget's own
	# named actors, in the shared register rather than a module-owned copy.
	("josphat.mwangi", "Josphat Mwangi"),
	("beatrice.kamau", "Beatrice Kamau"),
	# REQ-CHG-001 v1.6 §16.1 / KT-STD-001 §8.3 (2026-09-06) — the Head of
	# Procurement Function actor Requisitions authorisation names.
	("charles.mutiso", "Charles Mutiso"),
	# TPR-CHG-001 v0.6 §13.2 / KT-STD-001 §8.3 (2026-09-08) — the Procurement
	# Officer who prepares the Tender; a different person from the Head of
	# Procurement Function who approves it (§10.3).
	("brian.wafula", "Brian Wafula"),
	# PLN-CHG-001 v1.18 §10.1 / KT-STD-001 §8.3 (2026-09-12, plan D19) —
	# Planning's Accounting Officer and statutory approver join the shared
	# register here instead of being created by the Planning seed.
	("amina.hassan", "Amina Hassan"),
	("daniel.rotich", "Daniel Rotich"),
	# KT-STD-001 v1.11 §8.3 (Project Owner, 29 Sep 2026: "Register Daniel
	# Otieno"; seeded at the owner's instruction of 30 Sep 2026) — the
	# technical operator: service health and incidents only, including
	# Opening access support; a technical reader (§3A.6), so he also holds
	# System Manager (TECHNICAL_ACTORS). Not Daniel Rotich.
	("daniel.otieno", "Daniel Otieno"),
	# KT-STD-001 v1.12 §8.3 (approved 30 Sep 2026; seeded at the Project
	# Owner's instruction, "Seed appropriately") — the release
	# operator who holds Bid Submission's production-submission release; no
	# bid content, no supplier business action. Not Beatrice Kamau.
	("nadia.kamau", "Nadia Kamau"),
	# EVL-CHG-001 v0.4 §3, §11.1 (plan D17; KT-STD-001 v1.13 registration owed,
	# FU-EVL-07) — the evaluation committee (Grace Wambui chairs; Peter Mugo and
	# Ruth Achieng are members) and the evaluation's technical support holder.
	# Grace Wambui is not Grace Wanjiku (the Departmental Author).
	("grace.wambui", "Grace Wambui"),
	("peter.mugo", "Peter Mugo"),
	("ruth.achieng", "Ruth Achieng"),
	("esther.njeri", "Esther Njeri"),
)

# KT-STD-001 §3A.6 — register actors who read as technical readers
# (System Manager): never a business turn, fix or action.
TECHNICAL_ACTORS: tuple[str, ...] = ("daniel.otieno",)

# KT-STD-001 v1.11 §8.3 (Project Owner, 29 Sep 2026: "Add Jane Wanjiku") —
# members of the public: a signed-in Website User with no supplier link and
# no bidder rights, on the public portal only.
PUBLIC_ACTORS: tuple[tuple[str, str], ...] = (("jane.wanjiku@observer.example", "Jane Wanjiku"),)

ASSIGNMENTS = (
	# (user local part, business role, unit name or None, kwargs)
	("grace.wanjiku", "Departmental Author", "Digital Health", {}),
	# §8.3 — the Cartesian-product regression fixture: the same user holds a
	# different role in a different unit.
	("grace.wanjiku", "Head of User Department", "Human Resources Management and Development", {}),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04): Grace authors in both departments
	# the module's default Needs live in.
	("grace.wanjiku", "Departmental Author", "Human Resources Management and Development", {}),
	("peter.kimani", "Head of User Department", "Human Resources Management and Development", {}),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04): Peter reviews both departments the
	# module's default Needs live in. Digital Health and HRMD share no
	# covering parent below the site root, so §14.2's fallback applies — two
	# exact leaf assignments rather than one parent grant.
	# PLN-CHG-001 v1.18 §13.1 (2026-09-12, plan D19): Peter takes Digital
	# Health over from Julia's acting period — dated, not open-ended, so the
	# fixture chronology (Julia certifies DHI on 25 Nov 2026, Peter may act
	# from December) is real at command time under the frozen seed clock.
	# Two-year seed world (plan D8, 4 Oct 2026): the SEED-001 chronology is
	# Year 1's planning history, 364 days before its 2026 instants (was
	# 1 Dec 2026), so Peter also decides Year 2's Digital Health Needs.
	("peter.kimani", "Head of User Department", "Digital Health", {"effective_from": "2025-12-02 00:00:00"}),
	(
		"julia.njeri",
		"Head of User Department",
		"Digital Health",
		{
			"appointment_type": "Acting",
			"authority_reference": "MOH/HR/ACT/2025/041",
			# Two-year seed world (plan D8, 4 Oct 2026): the window below is
			# 364 days before its 1 Oct–30 Nov 2026 dates — Year 1's planning
			# history, so her 26 Nov 2025 decisions are authorised for real.
			# PLN-CHG-001 v1.18 §13.1 / SEED-001 §3.1 — 1 Oct through 30 Nov
			# 2026 inclusive. The 5 Sep 2026 stop-gap that widened this window
			# (so a real-clock seed could act as Julia) is retired by plan D19:
			# seeds now run each command under the frozen clock at its fixture
			# instant (kentender_core.seeds.clock), so her 25 Nov 2026
			# decisions are authorised for real. The retired stop-gap row is
			# revoked by `_reconcile_superseded_fixture_assignments`.
			"effective_from": "2025-10-02 00:00:00",
			"effective_to": "2025-12-01 23:59:59",
		},
	),
	("mercy.kilonzo", "Procurement Planner", None, {}),
	# STR-CHG-001 v1.7 §14.1 / KT-STD-001 §8.3 (2026-09-05) — Strategy's own
	# named actors now exist; supersedes CU-307's Mercy stand-in.
	# STR-CHG-001 v1.8 §14.1: the 1 Jul 2023 baseline needs explicit dated
	# authority. Project Owner decision, 26 Sep 2026: backdate it — both
	# assignments start on 1 Jul 2023 (they had no start before).
	("esther.muthoni", "Strategy Author", None, {"effective_from": "2023-07-01 00:00:00"}),
	("alfred.ochieng", "Strategy Approver", None, {"effective_from": "2023-07-01 00:00:00"}),
	# NDS-CHG-001 v1.6 §14.2 (2026-09-04) — Site-wide Auditor, read-only.
	("naomi.chebet", "Auditor", None, {}),
	# BUD-CHG-001 v1.6 §15.1 — Josphat holds Budget Officer and, separately,
	# Finance Confirmation Officer (the no-self-approval fixture); Beatrice
	# is the Budget Approver. All Site-wide (§7).
	("josphat.mwangi", "Budget Officer", None, {}),
	("josphat.mwangi", "Finance Confirmation Officer", None, {}),
	("beatrice.kamau", "Budget Approver", None, {}),
	# REQ-CHG-001 v1.6 §16.1 — Charles authorises Requisitions and, later,
	# approves Tenders (TPR-CHG-001). Site-wide (§8).
	("charles.mutiso", "Head of Procurement Function", None, {}),
	# TPR-CHG-001 v0.6 §5 — Site-wide Procurement Officer (prepares, never
	# approves, the same Version — §10.3).
	("brian.wafula", "Procurement Officer", None, {}),
	# PLN-CHG-001 v1.18 §6 / §10.1 — Site-wide adoption and statutory
	# capacity (the capacity itself resolves from the site's configured
	# route at decision time).
	("amina.hassan", "Accounting Officer", None, {}),
	("daniel.rotich", "Plan Statutory Approver", None, {}),
	# KT-STD-001 v1.11 §8.3 — Site-wide Technical Operator: Bid Submission's
	# signing/tender-box incidents and Bid Opening's Opening access support.
	("daniel.otieno", "Technical Operator", None, {}),
	# KT-STD-001 v1.12 §8.3 — Site-wide Release Operator (Bid Submission's
	# production-submission gate).
	("nadia.kamau", "Release Operator", None, {}),
	# KT-STD-001 v1.13 §8.3 — Grace Wambui, Peter Mugo and Ruth Achieng hold no
	# standing responsibility: their authority is the Evaluation appointment
	# alone ("Appointed tender only"; Project Owner, 1 Oct 2026: "Follow
	# v1.13"). (Until then each held Departmental Author in an existing unit,
	# because committee eligibility required a responsibility.)
	# Esther Njeri holds Evaluation Technical Support: Bid Evaluation's
	# technical issues only, not Daniel Otieno's Technical Operator work
	# (KT-STD-001 v1.13 §8.3; Project Owner, 1 Oct 2026: "Own responsibility").
	("esther.njeri", "Evaluation Technical Support", None, {}),
	(
		"samuel.otieno",
		"Head of User Department",
		"Directorate of Digital Health and Policy",
		{
			# 364 days before 1 Jan–31 Aug 2026 (two-year seed world plan D8).
			"effective_from": "2025-01-02 00:00:00",
			"effective_to": "2025-09-01 23:59:59",
		},
	),
	# Samuel's Directorate term above ends 31 Aug 2026 and is deliberately
	# left expired (KT-STD-001 §8.3 lists him as the expired appointment;
	# Departmental Needs' permission suite uses him as its actor who holds
	# no current authority). Nobody succeeded him, so from 1 Sep 2026 the
	# Directorate had no head — and, because an Organisation Unit grant
	# reaches that unit's descendants (`authorization.descendants_of`, one
	# direction only), neither did Digital Health underneath it. Julia's
	# acting term does not start until 1 Oct and Peter's Digital Health
	# term not until 1 Dec, so a site reseeded in between had no Head of
	# User Department for that whole branch and no reviewer for its Needs.
	#
	# Peter succeeds Samuel at the Directorate, open-ended: he is already
	# the substantive head the Needs, Planning and Requisitions seeds drive
	# as reviewer. This leaves Julia's acting window and Samuel's expired
	# one exactly as the register and the AUTH-DES-03 artboard specify —
	# they still render Scheduled and Expired — and adds no earlier
	# *Digital-Health-scoped* row, so SEED-001's chronology for that unit
	# is untouched.
	(
		"peter.kimani",
		"Head of User Department",
		"Directorate of Digital Health and Policy",
		# 364 days before 1 Sep 2026 (two-year seed world plan D8).
		{"effective_from": "2025-09-02 00:00:00"},
	),
)

# BUD-CHG-001 v1.6 §15.2 — the one governed funding source every Budget
# fixture draws on. Configuration & Governance owns the catalogue (FU-05
# records the pending CFG-CHG-002 v0.8 §4.4 schema reconciliation); the
# Budget seed fails closed if this row is absent, never creates it.
# PLN-CHG-001 v1.18 §10.11 C03 (2026-09-12) — the three governed values the
# Procurement settings artboard lists; Budget draws on the first.
FUNDING_SOURCES = ("Government of Kenya", "Development partner", "Appropriation in Aid")

# TPR-CHG-001 v0.6 §8.5 / plan D6 — the one governed contact office the
# Ministry of Health fixture names for clarifications, notices and the
# contract contact (§13.5). Email on the KT-STD-001 §8.1 fixture domain; no
# telephone is invented.
CONTACT_OFFICES = (
	# (office name, contact email, contact phone, address)
	("Ministry of Health Procurement Office", "procurement@moh.example.test", "", "Afya House, Cathedral Road, Nairobi"),
)


def contact_office_display(office_name: str) -> str:
	"""The rendered contact string for a seeded office (mirrors
	`ContactOffice.display()` without a document load)."""
	for name, email, phone, _address in CONTACT_OFFICES:
		if name == office_name:
			return ", ".join(p for p in (name, email, phone) if p)
	return office_name

# PLN-CHG-001 v1.18 §5.5.1 / §10.1 / §10.11 C04 (2026-09-12) — the method
# eligibility and procedure schedule profiles the Procurement settings tab
# maintains. Every seeded row is `Production verification pending`: the
# figures reproduce the §10.1 display example (21/30/5/2/14; buffers are
# Planning assumptions) and the Second Schedule limits above, none of which
# has been verified against primary law here (v1.18 §15.2 prerequisite;
# plan D16 keeps the fixture-verified set in the Planning seed).
# The window spans every fiscal year this seed creates, derived from
# `FISCAL_START_YEARS` rather than written out, so it moves with them.
#
# It used to start on Planning's own earliest baseline invitation date
# (2027-05-01) — far enough back for the plan it seeds, but in the future
# on any real calendar before then, which left an operator with no rule in
# force on the day they reseeded: 10 of the 11 methods, and every
# Regulatory Reference kind, resolved to nothing until someone widened a
# row by hand. The lower bound is a fixture assumption, not a regulatory
# fact (SEED-OPS-001 v1.2 says so in as many words when it moved the date
# the first time), so it now starts at the first seeded FY. The upper
# bound still ends with the last one. Nothing here is now-relative: these
# are fixed dates that follow the seeded years, so a visual baseline
# captured today still matches tomorrow.
PROFILE_EFFECTIVE = {
	"effective_from": f"{FISCAL_START_YEARS[0]}-07-01",
	"effective_until": f"{FISCAL_START_YEARS[-1] + 1}-06-30",
}
PROFILE_SOURCE = {
	"source_instrument": "Public Procurement and Asset Disposal Act, 2015 and Public Procurement and Asset Disposal Regulations, 2020",
	"provision": "Verification required",
	"applicability_basis": "Planned invitation date",
}
# Every rule version seeded below carries this as its `change_reason` (the
# spec-required "Reason for this version"): it is genuinely the reason a v1
# row exists, not a placeholder. Source-check status is unaffected — the
# reason a version was written and whether its facts have been checked
# against primary law are two separate questions (see `verification_status`).
SEED_CHANGE_REASON = "Canonical seed — initial version for the KT-STD-001 §8 configuration."
# Methods whose admissibility depends on circumstances a Planner declares and
# a separate authorisation may govern (v1.18 §5.5.3.3; LAW §2 conditions).
DECLARATION_METHODS = {
	"Direct Procurement": ("s.103", "Accounting Officer", "Before invitation"),
	"Restricted Tender": ("s.102", "Accounting Officer", "Before invitation"),
	"Competitive Negotiations": ("s.131", "Accounting Officer", "Before invitation"),
	"Force Account": ("reg 95", "Accounting Officer", "Before commencement"),
}
# The categories every admitted method gets a schedule profile for (§10.1
# names the Open Tender goods and services profiles; the rest follow the
# same example periods).
SCHEDULE_PROFILE_CATEGORIES = ("Goods", "Services", "Works")
SCHEDULE_MILESTONES = (
	# (milestone, default days for the period closing at it, basis, statutory ref)
	("invitation", None, "Statutory", "reg 42 — Third Schedule col. 9"),
	("bid_opening", 21, "Statutory", "Verification required"),
	("evaluation_completion", 30, "Statutory", "Third Schedule col. 11 — verification required"),
	("award_approval", 5, "Planning assumption", ""),
	("award_notification", 2, "Planning assumption", ""),
	("contract_signing", 14, "Statutory", "Verification required"),
	("delivery_completion", None, "Source-derived", "Earliest source required-by date"),
)
# Owner decision 2 Oct 2026 (TPR-CHG-001 v0.16): the verified legal minimum preparation period for an Open Tender is 7 days, kept apart from
# the 21-day usual period above. The citation is the Project Owner's research (PPADA s.97(1); PPADR 2020 reg. 86); it has not been checked
# against the primary text by the build, which is why `verification_status` stays at the fixture level.
# The row's basis describes its default (the usual 21 days), which the owner keeps as a planning assumption; the minimum carries its own reference.
LEGAL_PREPARATION_MINIMUMS = {("Open Tender", "bid_opening"): (7, "PPADA s.97(1); PPADR 2020 reg. 86", "Planning assumption")}
REMINDER_THRESHOLD_DAYS = 7

# CFG-CHG-002 v0.16 §13 / BDS-CHG-001 v0.8 §10.1 — the Supplier portal
# fixture values, seeded through UpdatePublicPortalSettings. Controlled test
# values, not production defaults, legal approval or proof the pages are live.
PUBLIC_PORTAL_SETTINGS = {
	"supplier_support_email": "tendersupport@health.go.ke",
	"supplier_support_phone": "+254 20 271 7077",
	"supplier_support_hours": "Monday–Friday, 08:00–17:00 EAT",
	"privacy_notice_url": "https://health.example.test/kentender/privacy",
	"portal_terms_url": "https://health.example.test/kentender/terms",
	"accessibility_statement_url": "https://health.example.test/kentender/accessibility",
}

# Kenya's fixed-date public holidays (Public Holidays Act Cap. 110, First
# Schedule). Good Friday, Easter Monday and the two Eids are deliberately
# absent: they move each year and are gazetted annually, so they are an
# administrator's entry for the year concerned, not a date this seed can
# state as fact.
FIXED_PUBLIC_HOLIDAYS = (
	("01-01", "New Year's Day"),
	("05-01", "Labour Day"),
	("06-01", "Madaraka Day"),
	("10-10", "Huduma Day"),
	("10-20", "Mashujaa Day"),
	("12-12", "Jamhuri Day"),
	("12-25", "Christmas Day"),
	("12-26", "Boxing Day"),
)

# TPR-CHG-001 v0.8 §10.1 "Publication configuration" / plan D6 — the
# publication rule for a national Open Tender, expressed through CFG-CHG-002
# v0.11's own "Publication obligations" rule kind: one reference set per
# required channel (a set carries one channel per version, and overlapping
# versions of one set supersede each other), all citing the same rule id in
# `source_reference`, plus the two cancellation obligations. Every MVP channel
# is Evidence based (§5.5.1): nothing here names an integration contract.
PUBLICATION_RULE = "PUB-RULE-MOH-OT-2027-01"
PUBLICATION_TRIGGER_INVITATION = "TenderInvitation"
PUBLICATION_TRIGGER_CANCELLATION = "TenderCancellation"
PUBLICATION_CHANNELS = (
	# (channel code, display label, public URL expected)
	("STATE_PORTAL", "State Portal", True),
	("MINISTRY_WEBSITE", "Ministry website", True),
	("NOTICE_BOARD", "Notice board", False),
	("NATIONAL_NEWSPAPERS", "Two national newspapers", False),
)
CANCELLATION_OBLIGATIONS = (
	# (code, label, recipient, due rule, days)
	("PPRA_REPORT", "PPRA cancellation report", "Public Procurement Regulatory Authority", "CalendarDaysAfter", 14),
	("CANDIDATE_NOTICE", "Candidate cancellation notice", "Registered candidates", "CalendarDaysAfter", 14),
)

# PLN-CHG-001 v1.18 §13.1 / plan D19 — the two stop-gap assignment rows the
# 5 Sep 2026 seed created and this seed retires (revoked with a reason, never
# deleted): Julia's widened acting window and Peter's undated Digital Health
# authority. Identified exactly; nothing else is touched.
SUPERSEDED_STOPGAP_ASSIGNMENTS = (
	("julia.njeri", "Head of User Department", "Digital Health", "2026-09-01 00:00:00", "2027-06-30 23:59:59"),
	("peter.kimani", "Head of User Department", "Digital Health", None, None),
)
STOPGAP_REVOCATION_REASON = (
	"PLN-CHG-001 v1.18 §13.1 fixture correction (plan D19): replaced by the dated assignment the shared register now specifies."
)

# REQ-CHG-001 v1.6 D2 — the one governed delivery/inspection location
# the Ministry of Health fixture uses (§13.2, §16.1).
DELIVERY_LOCATIONS = (
	("Ministry of Health Headquarters, Afya House, Nairobi", "Afya House, Cathedral Road, Nairobi"),
)

ENABLED_UOMS = (
	"Each",
	"Programme",
	"Set",
	"Lot",
	"Kilogram",
	"Litre",
	"Metre",
	"Square Metre",
	"Cubic Metre",
	"Service Month",
)


def run(*, commit: bool = True) -> dict:
	result = {
		"site": _seed_site(),
		"units": _seed_units(),
		"unit_tree": repair_unit_tree(),
		"company": _seed_company(),
		"fiscal_years": _seed_fiscal_years(),
		"intake": _seed_intake(),
		"dpp_intake": _seed_dpp_intake(),
		"disposal_intake": _seed_disposal_intake(),
		"catalogues": _seed_catalogues(),
		"funding_sources": _seed_funding_sources(),
		"delivery_locations": _seed_delivery_locations(),
		"contact_offices": _seed_contact_offices(),
		"regulatory_reference": _seed_regulatory_reference(effective=PROFILE_EFFECTIVE),
		"method_profiles": _seed_method_profiles(),
		"schedule_profiles": _seed_schedule_profiles(),
		"business_day_calendar": _seed_business_day_calendar(),
		"publication_obligations": _seed_publication_obligations(),
		"exclusive_preference": _seed_exclusive_preference(),
		"preference_margins": _seed_preference_margins(),
		"market_price_index": _seed_market_price_index(),
		"approval_applicability": _seed_approval_applicability(),
		"procurement_settings": _seed_procurement_settings(),
		"public_portal_settings": _seed_public_portal_settings(),
		"uoms": _seed_uoms(),
		"users": _seed_users(),
		"retired_assignments": _reconcile_superseded_fixture_assignments(),
		"assignments": _seed_assignments(),
	}
	if commit:
		frappe.db.commit()
	return result


def stamp_procurement_rules_fixture_verified() -> int:
	"""Every Procurement Rule `run()` just seeded — Method eligibility,
	Schedule profiles, or any Regulatory Reference kind — starts
	`Production verification pending` (plan D16: legally honest, since
	none of it has actually been checked against primary law here). That
	default is correct for a genuinely real site, but every caller of
	`run()` in this codebase today, directly or through
	`kentender_core.seeds.canonical`, seeds the same fixed "Ministry of
	Health" fixture — there is no other kind of site. Left at Pending, that
	fixture stalls at the first governance/submission gate no matter which
	`canonical.seed()` stage the caller stops at; the previous fix upgraded
	it only from the Planning stage onward (`ensure_profiles()`), which is
	why `through="budget"` (or any stage before "planning") still seeded
	unusable rules. This stamp is `canonical.seed()`'s own unconditional
	step, independent of `through` — it never writes `Verified`, and a rule
	outside the seeded window is untouched."""
	from kentender_core.services import procurement_settings as settings

	stamped = 0
	for doctype in (settings.METHOD_PROFILE, settings.SCHEDULE_PROFILE, "Regulatory Reference", settings.CALENDAR):
		for name in frappe.get_all(
			doctype,
			filters={"status": "Active", "verification_status": ("!=", settings.VERIFICATION_FIXTURE)},
			pluck="name",
		):
			frappe.db.set_value(doctype, name, "verification_status", settings.VERIFICATION_FIXTURE, update_modified=False)
			stamped += 1
	return stamped


def refresh_procurement_rules_content(*, fixture_namespace: str = FIXTURE_TAG) -> dict[str, dict]:
	"""Registers a fresh, superseding version of every Procurement Rule
	from this module's own current definitions, even where a version
	already exists for the same window — the seed's own find-or-skip
	guards exist to stop a routine rerun climbing a version every time,
	not to freeze a rule at whatever content an earlier version of this
	module produced. Use this once after `site_setup.py`'s own seed data
	changes, so the canonical world picks up the correction instead of
	needing a full site `wipe`. Never edits in place — every existing
	version is retained, `_supersede_overlapping` simply marks the ones
	this call's fresh version now covers as `Superseded`."""
	return {
		"method_profiles": _seed_method_profiles(fixture_namespace=fixture_namespace, force=True),
		"regulatory_reference": {"reference": _seed_regulatory_reference(fixture_namespace=fixture_namespace, force=True, effective=PROFILE_EFFECTIVE)},
		"publication_obligations": _seed_publication_obligations(fixture_namespace=fixture_namespace, force=True),
		"exclusive_preference": _seed_exclusive_preference(fixture_namespace=fixture_namespace, force=True),
		"preference_margins": _seed_preference_margins(fixture_namespace=fixture_namespace, force=True),
		"market_price_index": _seed_market_price_index(fixture_namespace=fixture_namespace, force=True),
		"approval_applicability": _seed_approval_applicability(fixture_namespace=fixture_namespace, force=True),
	}


def _seed_site() -> str:
	if configuration.is_configured():
		stored = frappe.db.get_single_value(configuration.SITE_PE_DOCTYPE, "pe_code")
		if stored != SITE["pe_code"]:
			# §8.6 — never repair, alias or overwrite conflicting authority.
			frappe.throw(
				f"This site is configured as {stored}, not {SITE['pe_code']}. "
				"The canonical seed refuses to overwrite a different site identity."
			)
		# Descriptive fields converge through the same command — only when one
		# differs: the command writes an audit entry on every call, and until
		# 26 Sep 2026 each reseed added one (KT-STD-001 v1.8 §8.6: a second
		# run creates no duplicate audit entry; 745 had piled up).
		payload = {
			field: SITE[field]
			for field in ("pe_name", "pe_type", "ppra_registration", "timezone", "statutory_approval_route", "entity_is_county")
		}
		def _differs(field: str, value) -> bool:
			stored = frappe.db.get_single_value(configuration.SITE_PE_DOCTYPE, field)
			return int(stored or 0) != int(value) if isinstance(value, bool) else (stored or "") != value

		if any(_differs(field, value) for field, value in payload.items()):
			configuration.update_procuring_entity(payload=payload)
		# The PE and its root are meant to exist together (configure_procuring_
		# entity creates both in one transaction) but nothing enforces that
		# invariant once they can drift apart independently - e.g. a
		# `wipe`/`rebuild` cycle interrupted between the two, or the root
		# deleted by some other path. Self-heal here rather than letting
		# _seed_units() fail deep inside with "root organisation unit is
		# missing" for a state this seed itself is meant to fix.
		if not structure._root():
			configuration.repair_organisation_root()
		return "updated"
	configuration.configure_procuring_entity(**SITE)
	return "configured"


def unit_tree_intact() -> bool:
	"""Every unit sits inside its parent's nested-set range."""
	rows = {row.name: row for row in frappe.get_all("Organisation Unit", fields=["name", "parent_organisation_unit", "lft", "rgt"])}
	return all(
		rows[row.parent_organisation_unit].lft < row.lft and row.rgt < rows[row.parent_organisation_unit].rgt
		for row in rows.values()
		if row.parent_organisation_unit in rows
	)


def repair_unit_tree() -> str:
	"""Found 26 Sep 2026: the root's range (1–2) no longer enclosed its
	children (14–19), so `authorization.descendants_of(root)` returned
	nothing (AUTH-ADR-001 v1.9 §4.3: a grant covers the unit and all its
	descendants). Rebuilds the tree only when it is broken."""
	if unit_tree_intact():
		return "intact"
	from frappe.utils.nestedset import rebuild_tree

	rebuild_tree("Organisation Unit")
	return "rebuilt"


def _seed_units() -> dict[str, str]:
	root = structure._root()
	created: dict[str, str] = {}
	by_name = {"__root__": root}
	for name, parent_name in UNITS:
		parent = by_name["__root__"] if parent_name is None else by_name[parent_name]
		outcome = structure.add_organisation_unit(parent_id=parent, name=name)
		by_name[name] = outcome["unit"]
		created[name] = outcome["unit"]
	return created


def _seed_company() -> str:
	existing = frappe.get_all("Company", pluck="name", limit_page_length=2)
	if existing:
		# One Company corresponds to the site PE (§7 of the ADR). A site that
		# already runs accounting keeps its Company; the seed never creates a
		# competing legal entity beside it.
		return f"existing: {existing[0]}"
	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": SITE["pe_name"],
			"abbr": "MOH",
			"default_currency": "KES",
			"country": "Kenya",
		}
	).insert(ignore_permissions=True)
	return SITE["pe_name"]


def _seed_fiscal_years() -> list[str]:
	out = []
	for year in FISCAL_START_YEARS:
		name = configuration._fy_name(year)
		if frappe.db.exists("Fiscal Year", name):
			out.append(f"existing: {name}")
			continue
		configuration.add_fiscal_year(start_year=year)
		out.append(name)
	return out


def _intake_closes_at(configured: str) -> str:
	"""The documented close instant, while it is still ahead of the clock.

	`open_*_submission` refuses an instant already in the past
	(`CFG_INTAKE_CLOSE_INSTANT_INVALID`), so a seed that hardcodes one stops
	working on the day it passes — the whole site would fail to seed rather
	than merely show a stale deadline. Past that day the intake is opened
	with no close instant, which is what the register's own "open" state
	means anyway: open until an administrator closes it. The fixed instant
	is still used whenever it is real, so nothing becomes now-relative until
	the documented date has genuinely gone by.
	"""
	from frappe.utils import get_datetime, now_datetime

	return configured if configured and get_datetime(configured) > now_datetime() else ""


def _converge_intake(module_key: str, target: str, flag_closes_at: str, closes_at: str, reason: str) -> None:
	"""Bring an already-open year's close instant to the seeded one.

	The seeders used to return early on "already open" without ever writing
	`closes_at`, so a year opened by anything else (a test, an earlier seed)
	kept whatever instant it had — usually none, which is why every activity
	read "No closing date" after a reseed. Only writes when it differs, so a
	rerun adds no audit entry.
	"""
	current = frappe.db.get_value("Fiscal Year", target, flag_closes_at) or ""
	if str(current)[:16] == str(closes_at)[:16]:
		return
	configuration.update_intake_close_instant(
		module_key=module_key, fiscal_year=target, closes_at=closes_at, reason=reason
	)


def _seed_intake() -> str:
	target = configuration._fy_name(INTAKE["start_year"])
	closes_at = _intake_closes_at(INTAKE["closes_at"])
	reason = "Annual needs call issued under circular MOH/PROC/2026/07."
	if frappe.db.get_value("Fiscal Year", target, configuration.FLAG_OPEN):
		_converge_intake("needs", target, configuration.FLAG_CLOSES_AT, closes_at, reason)
		return f"already open: {target}"
	configuration.open_needs_submission(fiscal_year=target, closes_at=closes_at, reason=reason)
	return f"opened: {target}"


def _seed_dpp_intake() -> str:
	target = configuration._fy_name(DPP_INTAKE["start_year"])
	closes_at = _intake_closes_at(DPP_INTAKE["closes_at"])
	reason = "Departmental procurement plans called for FY 2027/28 under regulation 40(3)."
	if frappe.db.get_value("Fiscal Year", target, configuration.DPP_FLAG_OPEN):
		_converge_intake("dpp", target, configuration.DPP_FLAG_CLOSES_AT, closes_at, reason)
		return f"already open: {target}"
	configuration.open_dpp_submission(fiscal_year=target, closes_at=closes_at, reason=reason)
	return f"opened: {target}"


def _seed_disposal_intake() -> str:
	"""The third registered intake (CFG-CHG-002 v0.11 §4.3). The Financial
	years tab lists it beside needs and departmental plans, so leaving it
	the only one closed read as an unfinished setup on every reseed even
	though no disposal workflow consumes it yet."""
	target = configuration._fy_name(DISPOSAL_INTAKE["start_year"])
	closes_at = _intake_closes_at(DISPOSAL_INTAKE["closes_at"])
	reason = "Disposal plans called for FY 2027/28 alongside the annual procurement plan."
	if frappe.db.get_value("Fiscal Year", target, configuration.DISPOSAL_FLAG_OPEN):
		_converge_intake("disposal_plan", target, configuration.DISPOSAL_FLAG_CLOSES_AT, closes_at, reason)
		return f"already open: {target}"
	configuration.open_disposal_plan_submission(fiscal_year=target, closes_at=closes_at, reason=reason)
	return f"opened: {target}"


def _seed_catalogues() -> dict[str, int]:
	created = 0
	for title, category in REQUIREMENT_TYPES:
		if frappe.db.exists("Requirement Type", title):
			updates = {}
			if frappe.db.get_value("Requirement Type", title, "status") != "Active":
				updates["status"] = "Active"
			if frappe.db.get_value("Requirement Type", title, "procurement_category") != category:
				updates["procurement_category"] = category
			if updates:
				frappe.db.set_value("Requirement Type", title, updates, update_modified=False)
			continue
		frappe.get_doc(
			{"doctype": "Requirement Type", "title": title, "procurement_category": category, "status": "Active"}
		).insert(ignore_permissions=True)
		created += 1
	for title in PROCUREMENT_METHODS:
		if frappe.db.exists("Procurement Method", title):
			if frappe.db.get_value("Procurement Method", title, "status") != "Active":
				frappe.db.set_value("Procurement Method", title, "status", "Active", update_modified=False)
			continue
		frappe.get_doc({"doctype": "Procurement Method", "title": title, "status": "Active"}).insert(ignore_permissions=True)
		created += 1
	return {"created": created, "requirement_types": len(REQUIREMENT_TYPES), "procurement_methods": len(PROCUREMENT_METHODS)}


def _seed_funding_sources() -> dict[str, int]:
	"""Through the Procurement settings commands, which audit each change
	(KT-STD-001 v1.8 §8.6; until 26 Sep 2026 the seed inserted and enabled
	the rows directly)."""
	from kentender_core.services import procurement_settings

	created = 0
	for label in FUNDING_SOURCES:
		if frappe.db.exists("Funding Source", label):
			if frappe.db.get_value("Funding Source", label, "record_status") != "Available":
				procurement_settings.update_funding_source(name=label, enabled=True)
			continue
		procurement_settings.add_funding_source(label=label, idempotency_key=f"site-setup:funding-source:{label}")
		created += 1
	return {"created": created, "total": len(FUNDING_SOURCES)}


def _seed_delivery_locations() -> dict[str, int]:
	created = 0
	for location_name, address in DELIVERY_LOCATIONS:
		if frappe.db.exists("Delivery Location", location_name):
			frappe.db.set_value("Delivery Location", location_name, {"address": address, "status": "Active"}, update_modified=False)
			continue
		frappe.get_doc(
			{
				"doctype": "Delivery Location",
				"location_name": location_name,
				"address": address,
				"status": "Active",
				"fixture_namespace": FIXTURE_TAG,
			}
		).insert(ignore_permissions=True)
		created += 1
	return {"created": created, "total": len(DELIVERY_LOCATIONS)}


def _seed_contact_offices() -> dict[str, int]:
	created = 0
	for office_name, contact_email, contact_phone, address in CONTACT_OFFICES:
		if frappe.db.exists("Contact Office", office_name):
			frappe.db.set_value(
				"Contact Office", office_name,
				{"contact_email": contact_email, "contact_phone": contact_phone, "address": address, "status": "Active"},
				update_modified=False,
			)
			continue
		frappe.get_doc(
			{
				"doctype": "Contact Office",
				"office_name": office_name,
				"contact_email": contact_email,
				"contact_phone": contact_phone,
				"address": address,
				"status": "Active",
				"fixture_namespace": FIXTURE_TAG,
			}
		).insert(ignore_permissions=True)
		created += 1
	return {"created": created, "total": len(CONTACT_OFFICES)}


# --------------------------------------------------------------------------
# D16 (24 Sep 2026) — an overlapping save must name what it replaces. The
# seed owns every record it writes, so when a re-run replaces its own earlier
# version it declares that replacement explicitly instead of relying on the
# silent supersession the services no longer perform.
# --------------------------------------------------------------------------


def _seed_replaces(doctype: str, filters: dict, effective_from, effective_until) -> list[str]:
	from kentender_core.services.procurement_settings import _overlaps

	return [
		row["name"]
		for row in frappe.get_all(doctype, filters={**filters, "status": "Active"}, fields=["name", "effective_from", "effective_until"])
		if _overlaps(row["effective_from"], row["effective_until"], effective_from, effective_until or None)
	]


def _seed_save_reference_version(**kwargs):
	from kentender_core.services import regulatory_reference as register

	kwargs.setdefault(
		"supersedes_version_ids",
		_seed_replaces(register.DOCTYPE, {"reference_set": kwargs["reference_set"]}, kwargs["effective_from"], kwargs.get("effective_until")),
	)
	return register.save_regulatory_reference_version(**kwargs)


def _seed_register_method_profile_version(**kwargs):
	from kentender_core.services import procurement_settings as settings

	kwargs.setdefault(
		"replaces",
		",".join(_seed_replaces(settings.METHOD_PROFILE, {"procurement_method": kwargs["procurement_method"]}, kwargs["effective_from"], kwargs.get("effective_until"))),
	)
	return settings.register_method_profile_version(**kwargs)


def _seed_register_schedule_profile_version(**kwargs):
	from kentender_core.services import procurement_settings as settings

	kwargs.setdefault(
		"supersedes_version_ids",
		_seed_replaces(
			settings.SCHEDULE_PROFILE,
			{"procurement_method": kwargs["procurement_method"], "procurement_category": kwargs["procurement_category"]},
			kwargs["effective_from"],
			kwargs.get("effective_until"),
		),
	)
	return settings.register_schedule_profile_version(**kwargs)


def _seed_register_business_day_calendar_version(**kwargs):
	from kentender_core.services import procurement_settings as settings

	kwargs.setdefault(
		"supersedes_version_ids",
		_seed_replaces(settings.CALENDAR, {"calendar_name": kwargs["calendar_name"]}, kwargs["effective_from"], kwargs.get("effective_until")),
	)
	return settings.register_business_day_calendar_version(**kwargs)


def _reservation_has_measure(version_name: str) -> bool:
	import json

	from kentender_core.services import regulatory_reference as register

	payload = json.loads(frappe.db.get_value(register.DOCTYPE, version_name, "payload_json") or "{}")
	return bool(payload.get("measure_stage"))


def _seed_regulatory_reference(fiscal_year: str = "", fixture_namespace: str = FIXTURE_TAG, *, verification_status: str = "Production verification pending", reservation_target_percent=None, county_target_percent=None, force: bool = False, effective: dict | None = None) -> str:
	"""CFG-CHG-002 v0.11 Phase 2b — seeds the "Reservation rules" kind's
	Regulatory Reference Set/Version for `fiscal_year`. `threshold_matrix`
	is no longer seeded here at all: it is now derived at read time from
	`Procurement Method Profile` (D10), which `_seed_method_profiles` already
	seeds with the same Second Schedule figures — closes the former
	duplicate-write (FU-08).

	`effective` overrides the window. Without it the version spans exactly
	`fiscal_year`, which is what the isolation-year fixture worlds need; the
	canonical seed passes `PROFILE_EFFECTIVE` so this rule is in force over
	the same span as every other seeded rule rather than only inside the
	planning year (a reseed before 1 July 2027 otherwise left the site with
	no reservation rule in force at all)."""
	from kentender_core.services import regulatory_reference as register

	fiscal_year = fiscal_year or configuration._fy_name(DPP_INTAKE["start_year"])
	fy_row = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	if not fy_row:
		frappe.throw(f"Unknown fiscal year: {fiscal_year}.")
	window = effective or {"effective_from": fy_row["year_start_date"], "effective_until": fy_row["year_end_date"]}

	reference_key = "RESERVATION-RULES"
	reference_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": reference_key}, "name")
	if not reference_set:
		reference_set = register.create_regulatory_reference(
			reference_key=reference_key,
			reference_kind="Reservation rules",
			display_name="Reservation rules",
			fixture_namespace=fixture_namespace,
		)["reference_set"]

	target = REGULATORY_REFERENCE["reservation_target_percent"] if reservation_target_percent is None else reservation_target_percent
	county_target = REGULATORY_REFERENCE["county_resident_target_percent"] if county_target_percent is None else county_target_percent

	# Find-or-create, like every sibling profile seed (`_profile_exists`).
	# Without this the seed saved a brand-new version on every run — each one
	# superseding the last — so the canonical set climbed a version per
	# `site_setup.run()`, per gate and per test run (found live at v21).
	existing = frappe.db.get_value(
		register.DOCTYPE,
		{
			"reference_set": reference_set,
			"status": "Active",
			"effective_from": window["effective_from"],
		},
		"name",
	)
	# A version saved before the v0.13 measure correction has no measure
	# stage, so Planning's read cannot use it; converge by saving a corrected
	# successor rather than keeping the old shape forever.
	if existing and not force and _reservation_has_measure(existing):
		return existing

	outcome = _seed_save_reference_version(
		reference_set=reference_set,
		payload={
			"obligation_code": "ANNUAL-RESERVATION-TARGET",
			# CFG-CHG-002 v0.13 §4.7 — the planning measure; its denominator
			# (the eligible value of the current Annual Plan) follows from it.
			"measure_stage": "PlanningAllocation",
			"target_percent": target,
			"county_target_percent": county_target,
			"overlap_policy": "Independent",
			"categories": [
				{"category": name, "advantage_rank": rank, "is_regional": regional, "statutory_reference": ref}
				for name, rank, regional, ref in RESERVATION_CATEGORIES
			],
		},
		effective_from=window["effective_from"],
		effective_until=window.get("effective_until", ""),
		applicability_basis="FiscalYearStart",
		verification_status=verification_status,
		source_instrument=PROFILE_SOURCE["source_instrument"],
		provision="s.157(4); s.157(8)(a); reg 149; reg 151; reg 163",
		interpretation=(
			f"At least {target}% of the value the entity plans to procure must be set aside through "
			f"reservation for youth, women, persons with disabilities, other disadvantaged groups, MSMEs "
			f"and regional candidates; an additional {county_target}% county-resident preference applies "
			f"for a county entity. The approved annual budget is the ceiling the plan must fit inside, "
			f"not the measure of this obligation: it authorises spending without obliging it."
		),
		change_reason=SEED_CHANGE_REASON,
		fixture_namespace=fixture_namespace,
	)
	return outcome["reference"]


def _seed_publication_obligations(*, effective: dict | None = None, fixture_namespace: str = FIXTURE_TAG, verification_status: str = "Production verification pending", force: bool = False) -> dict[str, int]:
	"""TPR-CHG-001 v0.8 §10.1 / plan D6 — six "Publication obligations"
	reference sets (four invitation channels, two cancellation obligations),
	find-or-create like every sibling seed. `effective` defaults to the
	profile window (Planning invites before the FY it plans for opens)."""
	from kentender_core.services import regulatory_reference as register

	effective = effective or PROFILE_EFFECTIVE
	created = 0
	rows = [
		(
			f"{PUBLICATION_RULE}/{code}", f"{label} — {PUBLICATION_RULE}",
			{
				"obligation_id": "LAW-OB-PUB-INVITATION", "accountable_actor_role": "Head of Procurement Function",
				"recipient": "Public", "channel": code, "trigger_event": PUBLICATION_TRIGGER_INVITATION,
				"due_rule": "Immediate", "source_reference": "s.96(2)",
			},
		)
		for code, label, _public_url in PUBLICATION_CHANNELS
	] + [
		(
			f"{PUBLICATION_RULE}/{code}", f"{label} — {PUBLICATION_RULE}",
			{
				"obligation_id": f"LAW-OB-CANCEL-{code}", "accountable_actor_role": "Accounting Officer",
				"recipient": recipient, "channel": code, "trigger_event": PUBLICATION_TRIGGER_CANCELLATION,
				"due_rule": due_rule, "days": days, "source_reference": "s.138",
			},
		)
		for code, label, recipient, due_rule, days in CANCELLATION_OBLIGATIONS
	]
	for reference_key, display_name, payload in rows:
		reference_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": reference_key}, "name")
		if not reference_set:
			reference_set = register.create_regulatory_reference(
				reference_key=reference_key, reference_kind="Publication obligations", display_name=display_name, fixture_namespace=fixture_namespace,
			)["reference_set"]
		if not force and frappe.db.get_value(register.DOCTYPE, {"reference_set": reference_set, "status": "Active", "effective_from": effective["effective_from"]}, "name"):
			continue
		is_invitation = payload["trigger_event"] == PUBLICATION_TRIGGER_INVITATION
		_seed_save_reference_version(
			# A publication/cancellation obligation applies to any tender
			# regardless of category — no `applicability_categories`
			# restriction (an empty list means "all categories", the same
			# convention `resolve_reference` uses for entity types).
			reference_set=reference_set, payload=payload, effective_from=effective["effective_from"], effective_until=effective.get("effective_until", ""),
			applicability_basis="InvitationDate",
			verification_status=verification_status, source_instrument=PROFILE_SOURCE["source_instrument"],
			provision="s.96(2)" if is_invitation else "s.138",
			interpretation=(
				f"Every tender invitation is published to {display_name.split(' — ')[0].lower()} at the point of invitation."
				if is_invitation
				else f"A cancelled procurement is notified to {payload['recipient'].lower()} via {display_name.split(' — ')[0].lower()} within {payload['days']} days of cancellation."
			),
			change_reason=SEED_CHANGE_REASON,
			fixture_namespace=fixture_namespace,
		)
		created += 1
	return {"created": created, "total": len(rows)}


# CFG-CHG-002 Phase 2c (tracker CFG11-202/304, FU-13) — the four Regulatory
# Reference kinds whose payload validators and "Add rule" UI already existed
# but had no seeded row anywhere: Exclusive preference, Preference margins,
# Market price index, Approval applicability. Same find-or-create shape as
# the siblings above; every row here starts `Production verification
# pending` from `run()`, same as every sibling profile (D16).
EXCLUSIVE_PREFERENCE_THRESHOLDS = (
	# (reference_key suffix, display label, categories, restriction_code)
	("WORKS", "Exclusive preference — Works", ("Works",), "WORKS-LOCAL-CONTENT", REGULATORY_REFERENCE["exclusive_preference_works_amount"]),
	(
		"GOODS-SERVICES",
		"Exclusive preference — Goods and services",
		("Goods", "Services"),
		"GOODS-SERVICES-LOCAL-CONTENT",
		REGULATORY_REFERENCE["exclusive_preference_goods_services_amount"],
	),
)


def _seed_exclusive_preference(*, effective: dict | None = None, fixture_namespace: str = FIXTURE_TAG, verification_status: str = "Production verification pending", force: bool = False) -> dict[str, int]:
	"""The KES ceilings below which a procurement is reserved exclusively
	for citizen contractors (s.157(8)(a); reg 163) — one set per category
	group since the works and goods/services ceilings differ (reg 163(2))."""
	from kentender_core.services import regulatory_reference as register

	effective = effective or PROFILE_EFFECTIVE
	created = 0
	for suffix, display_name, categories, restriction_code, amount in EXCLUSIVE_PREFERENCE_THRESHOLDS:
		reference_key = f"EXCLUSIVE-PREFERENCE/{suffix}"
		reference_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": reference_key}, "name")
		if not reference_set:
			reference_set = register.create_regulatory_reference(
				reference_key=reference_key, reference_kind="Exclusive preference", display_name=display_name, fixture_namespace=fixture_namespace,
			)["reference_set"]
		if not force and frappe.db.get_value(register.DOCTYPE, {"reference_set": reference_set, "status": "Active", "effective_from": effective["effective_from"]}, "name"):
			continue
		_seed_save_reference_version(
			reference_set=reference_set,
			payload={
				"restriction_code": restriction_code,
				# A single category when the set covers exactly one (Works);
				# blank when it spans more than one (Goods and Services) -
				# the payload field takes one value, `applicability_categories`
				# below carries the real (possibly multi-category) scope.
				"category": categories[0] if len(categories) == 1 else "",
				# Applies regardless of procurement method (reg 163 gates on
				# value and category, not on how the procurement is run).
				"method": "",
				"currency": "KES",
				"comparator": "LessThanOrEqual",
				"amount": amount,
				"funding_origin_condition": "GoK-funded",
				"local_origin_condition": "Kenyan-registered",
				"eligible_party_classification": "Citizen contractor",
				"source_reference": "s.157(8)(a); reg 163",
			},
			effective_from=effective["effective_from"],
			effective_until=effective.get("effective_until", ""),
			applicability_basis="InvitationDate",
			applicability_categories=list(categories),
			verification_status=verification_status,
			source_instrument=PROFILE_SOURCE["source_instrument"],
			provision="s.157(8)(a); reg 163",
			interpretation=(
				f"A procurement for {' or '.join(c.lower() for c in categories)} estimated at or below "
				f"KES {amount:,.0f} is reserved exclusively for citizen contractors."
			),
			change_reason=SEED_CHANGE_REASON,
			fixture_namespace=fixture_namespace,
		)
		created += 1
	return {"created": created, "total": len(EXCLUSIVE_PREFERENCE_THRESHOLDS)}


def _seed_preference_margins(*, effective: dict | None = None, fixture_namespace: str = FIXTURE_TAG, verification_status: str = "Production verification pending", force: bool = False) -> dict[str, int]:
	"""The MSME evaluation margin under s.155: a tenderer at least 51%
	Kenyan-owned through a micro, small or medium enterprise receives a 15%
	margin at financial evaluation under Open Tender."""
	from kentender_core.services import regulatory_reference as register

	effective = effective or PROFILE_EFFECTIVE
	reference_key = "PREFERENCE-MARGINS/MSME"
	reference_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": reference_key}, "name")
	if not reference_set:
		reference_set = register.create_regulatory_reference(
			reference_key=reference_key, reference_kind="Preference margins", display_name="Preference margins — MSME", fixture_namespace=fixture_namespace,
		)["reference_set"]
	if not force and frappe.db.get_value(register.DOCTYPE, {"reference_set": reference_set, "status": "Active", "effective_from": effective["effective_from"]}, "name"):
		return {"created": 0, "total": 1}
	_seed_save_reference_version(
		reference_set=reference_set,
		payload={
			"scheme_code": "MSME-MARGIN",
			"procedure": "Open Tender",
			"margin_percent": 15,
			"origin_condition": "Kenyan-registered",
			"shareholding_from": 51,
			"shareholding_to": 100,
			"shareholding_from_included": True,
			"shareholding_to_included": True,
			"evaluation_basis": "Financial evaluation",
			"source_reference": "s.155",
		},
		effective_from=effective["effective_from"],
		effective_until=effective.get("effective_until", ""),
		applicability_basis="InvitationDate",
		verification_status=verification_status,
		source_instrument=PROFILE_SOURCE["source_instrument"],
		provision="s.155",
		interpretation=(
			"A tenderer at least 51% owned by Kenyan citizens through a micro, small or medium "
			"enterprise receives a 15% margin at financial evaluation under Open Tender."
		),
		change_reason=SEED_CHANGE_REASON,
		fixture_namespace=fixture_namespace,
	)
	return {"created": 1, "total": 1}


MARKET_PRICE_INDEX_ROWS = (
	# (item, category, unit, indicative KES price)
	("Laptop computer, standard office specification", "Goods", "Each", 85_000),
	("Office desk, standard", "Goods", "Each", 25_000),
	("Site clearance", "Works", "Hectare", 150_000),
)


def _seed_market_price_index(*, effective: dict | None = None, fixture_namespace: str = FIXTURE_TAG, verification_status: str = "Production verification pending", force: bool = False) -> dict[str, int]:
	"""An indicative published price list for a few commonly procured items,
	so Planning's market-price-index panel has real rows instead of always
	reporting nothing published."""
	from frappe.utils import add_days
	from kentender_core.services import regulatory_reference as register

	effective = effective or PROFILE_EFFECTIVE
	reference_key = "MARKET-PRICE-INDEX"
	reference_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": reference_key}, "name")
	if not reference_set:
		reference_set = register.create_regulatory_reference(
			reference_key=reference_key, reference_kind="Market price index", display_name="Market price index", fixture_namespace=fixture_namespace,
		)["reference_set"]
	if not force and frappe.db.get_value(register.DOCTYPE, {"reference_set": reference_set, "status": "Active", "effective_from": effective["effective_from"]}, "name"):
		return {"created": 0, "total": 1}
	# A price is observed, then published, then the rule takes effect - in
	# that order. Both dates fall before `effective_from`, never on it, so
	# a rule that claims to already be published is not dated as if the
	# publication happened the same day it starts applying.
	observation_date = add_days(effective["effective_from"], -60)
	publication_date = add_days(effective["effective_from"], -30)
	_seed_save_reference_version(
		reference_set=reference_set,
		payload={
			"rows": [
				{
					"item": item, "category": category, "unit": unit, "currency": "KES", "price": price,
					"observation_date": str(observation_date), "publication_date": str(publication_date),
					"publication_reference": "Indicative price index",
				}
				for item, category, unit, price in MARKET_PRICE_INDEX_ROWS
			]
		},
		effective_from=effective["effective_from"],
		effective_until=effective.get("effective_until", ""),
		applicability_basis="FiscalYearStart",
		verification_status=verification_status,
		source_instrument=PROFILE_SOURCE["source_instrument"],
		provision="Indicative price index published by the Authority",
		interpretation="Indicative unit prices for commonly procured items, published for cost estimation; not a statutory ceiling.",
		change_reason=SEED_CHANGE_REASON,
		fixture_namespace=fixture_namespace,
	)
	return {"created": 1, "total": 1}


def _seed_approval_applicability(*, effective: dict | None = None, fixture_namespace: str = FIXTURE_TAG, verification_status: str = "Production verification pending", force: bool = False) -> dict[str, int]:
	"""Closes FU-13: a proper seeded "Approval applicability" rule for the
	site's own entity type, naming the Cabinet Secretary as plan-approval
	authority (reg 40(4)) — the same route `SITE["statutory_approval_route"]`
	already configures for this Ministry, so the rule and the configured
	route agree rather than one being silently unset."""
	from kentender_core.services import regulatory_reference as register

	effective = effective or PROFILE_EFFECTIVE
	reference_key = "APPROVAL-APPLICABILITY/NATIONAL-MINISTRY"
	reference_set = frappe.db.get_value(register.SET_DOCTYPE, {"reference_key": reference_key}, "name")
	if not reference_set:
		reference_set = register.create_regulatory_reference(
			reference_key=reference_key,
			reference_kind="Approval applicability",
			display_name="Approval applicability — National Government Ministry",
			fixture_namespace=fixture_namespace,
		)["reference_set"]
	if not force and frappe.db.get_value(register.DOCTYPE, {"reference_set": reference_set, "status": "Active", "effective_from": effective["effective_from"]}, "name"):
		return {"created": 0, "total": 1}
	_seed_save_reference_version(
		reference_set=reference_set,
		payload={
			"entity_types": [SITE["pe_type"]],
			"county_applicability": "NonCounty",
			"required_entity_evidence": "Procuring entity registration",
			"approval_route": SITE["statutory_approval_route"],
			# Free text, not a governed enum (`required_capacity_code` has
			# no validator lookup) — describes what the approval route
			# actually requires of the approver, not an internal code.
			"required_capacity_code": "Delegated authority to approve the annual procurement plan for this entity type",
			"source_reference": "reg 40(4)",
		},
		effective_from=effective["effective_from"],
		effective_until=effective.get("effective_until", ""),
		applicability_basis="PlanApprovalDate",
		applicability_entity_types=[SITE["pe_type"]],
		applicability_county="NonCounty",
		verification_status=verification_status,
		source_instrument=PROFILE_SOURCE["source_instrument"],
		provision="reg 40(4)",
		interpretation=f"A {SITE['pe_type'].lower()}'s annual procurement plan is approved by the {SITE['statutory_approval_route']}.",
		change_reason=SEED_CHANGE_REASON,
		fixture_namespace=fixture_namespace,
	)
	return {"created": 1, "total": 1}


def _profile_exists(doctype: str, filters: dict) -> str:
	return frappe.db.get_value(
		doctype, {"status": "Active", "effective_from": PROFILE_EFFECTIVE["effective_from"], **filters}, "name"
	) or ""


def _seed_method_profiles(*, effective: dict | None = None, verification_status: str | None = None, fixture_namespace: str = FIXTURE_TAG, force: bool = False) -> dict[str, int]:
	"""One `Production verification pending` eligibility profile per admitted
	method, built from the Second Schedule bands above plus a declaration
	condition where circumstances govern admissibility. Find-or-skip on
	(method, effective_from); a rerun creates no second Version. `force`
	skips that check and always registers — a superseding correction (never
	an edit-in-place) for when this function's own definition of a rule
	changes and the canonical world must pick up the correction without a
	full site wipe."""
	from kentender_core.services import procurement_settings as settings

	effective = effective or PROFILE_EFFECTIVE
	created = 0
	for method, goods, works, services, basis, reference in THRESHOLD_BANDS:
		if not force and _profile_exists(settings.METHOD_PROFILE, {"procurement_method": method, "effective_from": effective["effective_from"]}):
			continue
		conditions = []
		for category, amount in (("Goods", goods), ("Works", works), ("Services", services)):
			conditions.append(
				{
					"condition_id": f"{category[:1]}-VALUE",
					"kind": "Known fact",
					"description": (
						f"Estimated value within the Second Schedule limit for {category.lower()} (KES {amount:,.0f}, {basis.lower()})."
						if amount
						else f"No fixed maximum for {category.lower()}: determined by the funds allocated or the section's conditions."
					),
					"procurement_category": category,
					"maximum_amount": amount,
					"cumulative_basis": basis,
					"mandatory": True,
					# A "Known fact" is evaluated by the system from the
					# Planner's own estimate, never by a named approver
					# (`profiles.py`'s Known-fact/Declaration split) —
					# `authorisation_actor`/`authorisation_stage` are
					# correctly blank here, not a gap. What the fact is
					# checked against is real, though, and belongs on the
					# condition: the same market-survey basis Planning's
					# own `estimate_basis` field already requires.
					"required_evidence": "Estimated value basis (market survey and incidental costs)",
					"statutory_reference": reference,
				}
			)
		if method in DECLARATION_METHODS:
			ref, actor, stage = DECLARATION_METHODS[method]
			conditions.append(
				{
					"condition_id": "CIRCUMSTANCES",
					"kind": "Declaration",
					"description": "Circumstances supporting the selected method.",
					"procurement_category": "",
					"mandatory": True,
					"required_evidence": "Method eligibility record",
					"authorisation_actor": actor,
					"authorisation_stage": stage,
					"statutory_reference": ref,
				}
			)
		_seed_register_method_profile_version(
			procurement_method=method,
			conditions=conditions,
			verification_status=verification_status or settings.VERIFICATION_PENDING,
			fixture_namespace=fixture_namespace,
			source_instrument=PROFILE_SOURCE["source_instrument"],
			applicability_basis=PROFILE_SOURCE["applicability_basis"],
			provision=reference,
			change_reason=SEED_CHANGE_REASON,
			**effective,
		)
		created += 1
	return {"created": created, "total": len(THRESHOLD_BANDS)}


def _seed_schedule_profiles(*, effective: dict | None = None, verification_status: str | None = None, fixture_namespace: str = FIXTURE_TAG, limits: dict | None = None, estimated_delivery_default_days: int | None = None, methods: tuple[str, ...] | None = None) -> dict[str, int]:
	"""A schedule profile per admitted method and category, at
	`Production verification pending` (statutory minimum/maximum cells blank
	= verification required; buffers labelled Planning assumption).

	This used to seed Open Tender alone, on the reasoning that catalogue
	membership is not operational support (v1.18 §5.5.3.3). The catalogue
	does not behave that way in practice: `profiles.admissible_methods`
	gates the Planner's dropdown on the *method* profile, which all eleven
	have, so all eleven are offered — and choosing any of the other ten
	then blocks readiness with `PLN_REFERENCE_UNAVAILABLE`, whose own
	missing-setting panel sends the administrator to a System setup screen
	that has no control capable of creating a schedule profile. The dead
	end was unreachable by the remedy it named. Every method the catalogue
	offers now carries the same Planning-example schedule the three
	original rows always did — no new claim about any method's statutory
	timings, which stay blank pending verification exactly as before.

	`methods` narrows the set; the Planning and Requisitions fixture worlds
	pass a single method so that a method with no schedule stays reachable
	for the tests that assert that blocker.
	"""
	from kentender_core.services import procurement_settings as settings

	effective = effective or PROFILE_EFFECTIVE
	limits = limits or {}  # milestone → (minimum_days, maximum_days) for a fixture-verified set
	methods = methods or PROCUREMENT_METHODS
	created = 0
	total = 0
	for method in methods:
		for category in SCHEDULE_PROFILE_CATEGORIES:
			total += 1
			if _profile_exists(settings.SCHEDULE_PROFILE, {"procurement_method": method, "procurement_category": category, "effective_from": effective["effective_from"]}):
				continue
			_seed_register_schedule_profile_version(
				procurement_method=method,
				procurement_category=category,
				profile_name=f"{method} — {category.lower()}",
				procedure="Planning example",
				milestones=[
					{
						"milestone": key,
						"label": settings.MILESTONE_LABELS[key],
						"sequence": index + 1,
						"applies": True,
						"counting_rule": "Calendar days",
						"minimum_days": limits.get(key, (None, None))[0] or (LEGAL_PREPARATION_MINIMUMS.get((method, key)) or (None,))[0],
						"maximum_days": limits.get(key, (None, None))[1],
						"default_days": default,
						"basis": (LEGAL_PREPARATION_MINIMUMS.get((method, key)) or (None, None, basis))[2],
						"statutory_reference": (LEGAL_PREPARATION_MINIMUMS.get((method, key)) or (None, ref))[1],
					}
					for index, (key, default, basis, ref) in enumerate(SCHEDULE_MILESTONES)
				],
				counting_rule="Calendar days",
				estimated_delivery_period_default_days=estimated_delivery_default_days,
				verification_status=verification_status or settings.VERIFICATION_PENDING,
				fixture_namespace=fixture_namespace,
				**effective,
				**PROFILE_SOURCE,
			)
			created += 1
	return {"created": created, "total": total}


def _seed_business_day_calendar(*, effective: dict | None = None, fixture_namespace: str = FIXTURE_TAG, verification_status: str | None = None) -> dict[str, int]:
	"""The working-day calendar a schedule counting in working days needs.

	Nothing seeded one before, so a freshly seeded site showed "No
	working-day calendars yet" and no schedule could be switched off
	calendar days. Only the fixed-date statutory holidays are listed:
	Easter and the two Eids move every year and are gazetted annually, so
	they are an administrator's to add for the year in question rather than
	dates this seed can state.
	"""
	from frappe.utils import getdate

	from kentender_core.services import procurement_settings as settings

	effective = effective or PROFILE_EFFECTIVE
	name = "Kenya public holidays"
	start, until = getdate(effective["effective_from"]), getdate(effective["effective_until"])
	if frappe.db.get_value(settings.CALENDAR, {"calendar_name": name, "status": "Active", "effective_from": start}, "name"):
		return {"created": 0, "holidays": 0}
	holidays = [
		{"holiday_date": f"{year}-{month_day}", "holiday_name": label, "source_reference": "Public Holidays Act (Cap. 110)"}
		for year in range(start.year, until.year + 1)
		for month_day, label in FIXED_PUBLIC_HOLIDAYS
		if start <= getdate(f"{year}-{month_day}") <= until
	]
	_seed_register_business_day_calendar_version(
		calendar_name=name,
		effective_from=effective["effective_from"],
		effective_until=effective.get("effective_until", ""),
		weekend_days=["Saturday", "Sunday"],
		holidays=holidays,
		verification_status=verification_status or settings.VERIFICATION_PENDING,
		source_instrument="Public Holidays Act (Cap. 110)",
		provision="First Schedule",
		fixture_namespace=fixture_namespace,
	)
	return {"created": 1, "holidays": len(holidays)}


def _seed_procurement_settings() -> dict[str, int]:
	from kentender_core.services import procurement_settings as settings

	current = frappe.db.get_single_value(settings.SETTINGS, "approaching_milestone_threshold_days")
	if int(current or 0) == REMINDER_THRESHOLD_DAYS:
		return {"approaching_milestone_threshold_days": REMINDER_THRESHOLD_DAYS, "changed": 0}
	settings.set_reminder_threshold_days(days=REMINDER_THRESHOLD_DAYS)
	return {"approaching_milestone_threshold_days": REMINDER_THRESHOLD_DAYS, "changed": 1}


def _seed_public_portal_settings() -> dict:
	from kentender_core.services import public_portal

	current = public_portal.get_public_portal_settings()
	if current["values"] == PUBLIC_PORTAL_SETTINGS:
		return {"record_version": current["record_version"], "changed": 0}
	result = public_portal.update_public_portal_settings(
		**PUBLIC_PORTAL_SETTINGS,
		expected_version=current["record_version"],
		idempotency_key=f"site-setup:public-portal:{current['record_version']}",
	)
	if not result.get("ok"):
		frappe.throw(f"Supplier portal fixture values were refused: {result.get('errors')}")
	return {"record_version": result["record_version"], "changed": 1}


def _reconcile_superseded_fixture_assignments() -> list[str]:
	"""Revoke, with a reason, exactly the two stop-gap rows the 5 Sep 2026
	seed granted (§13.1 / plan D19). Matched on user, role, unit and the
	exact period they carried; any other row is left alone."""
	units = {
		row["unit_name"]: row["name"]
		for row in frappe.get_all("Organisation Unit", fields=["name", "unit_name"], limit_page_length=0)
	}
	revoked: list[str] = []
	for local, role, unit_name, effective_from, effective_to in SUPERSEDED_STOPGAP_ASSIGNMENTS:
		unit = units.get(unit_name)
		if not unit:
			continue
		rows = frappe.get_all(
			"User Responsibility Assignment",
			filters={"user": f"{local}@moh.example.test", "business_role": role, "organisation_unit": unit, "status": "Enabled"},
			fields=["name", "effective_from", "effective_to"],
		)
		for row in rows:
			row_from = str(row["effective_from"] or "") or None
			row_to = str(row["effective_to"] or "") or None
			if row_from == effective_from and row_to == effective_to:
				administration.revoke(row["name"], reason=STOPGAP_REVOCATION_REASON, actor="Administrator")
				revoked.append(row["name"])
	return revoked


def _seed_uoms() -> dict[str, int]:
	enabled = 0
	for uom in ENABLED_UOMS:
		if frappe.db.exists("UOM", uom):
			frappe.db.set_value("UOM", uom, "enabled", 1, update_modified=False)
		else:
			frappe.get_doc({"doctype": "UOM", "uom_name": uom, "enabled": 1}).insert(
				ignore_permissions=True
			)
		enabled += 1
	disabled = frappe.db.sql(
		"""update `tabUOM` set enabled = 0 where name not in %(keep)s and enabled = 1""",
		{"keep": ENABLED_UOMS},
	)
	remaining = frappe.db.count("UOM", {"enabled": 1})
	return {"enabled": enabled, "enabled_total": remaining}


def _seed_users() -> list[str]:
	out = []
	for local, full_name in ACTORS:
		email = f"{local}@moh.example.test"
		if not frappe.db.exists("User", email):
			first, _, last = full_name.partition(" ")
			doc = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"user_type": "System User",
					"enabled": 1,
				}
			)
			doc.insert(ignore_permissions=True)
			doc.add_roles("Desk User")
		if frappe.conf.get("developer_mode") or frappe.flags.get("kt_fixture_passwords"):
			# The register's actors log in with the shared fixture password so
			# they can be used at all: on a development site, or whenever the
			# canonical seed was allowed to run (developer_mode,
			# allow_canonical_seed or force — `canonical.run` sets the flag).
			# Until 26 Sep 2026 only developer_mode counted, so a new site
			# seeded with force had actors nobody could log in as.
			from frappe.utils.password import update_password

			from kentender_core.seeds.constants import TEST_PASSWORD

			update_password(email, TEST_PASSWORD)
		if local in TECHNICAL_ACTORS and "System Manager" not in frappe.get_roles(email):
			frappe.get_doc("User", email).add_roles("System Manager")
		out.append(email)
	for email, full_name in PUBLIC_ACTORS:
		if not frappe.db.exists("User", email):
			first, _, last = full_name.partition(" ")
			frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "send_welcome_email": 0,
				"user_type": "Website User", "enabled": 1}).insert(ignore_permissions=True)
		if frappe.conf.get("developer_mode") or frappe.flags.get("kt_fixture_passwords"):
			from frappe.utils.password import update_password

			from kentender_core.seeds.constants import TEST_PASSWORD

			update_password(email, TEST_PASSWORD)
		out.append(email)
	return out


def reset_site_setup(*, commit: bool = False) -> dict[str, int]:
	"""Tear down everything `run()` creates or converges, for a caller that has
	already torn down every module stage on top of it (site is the foundation
	every other stage's Fiscal Years, Organisation Units and actors reference,
	so this must run last, never on its own — `canonical.run(wipe=True)` is
	the sanctioned entry point).

	Three things `run()` touches are deliberately left alone, matching
	SEED-OPS-001 §3.2: the ERPNext Company (`_seed_company` never creates one
	if any exists, and never will here either), the Requirement Type /
	Procurement Method catalogues, and UOM enablement — none of the three
	carries a fixture_namespace, because they are Configuration & Governance's
	shared reference data, not this seed's own rows, whatever this seed does
	to activate them.

	Resets the Site Procuring Entity Single doctype directly rather than
	through a command: CFG-BR-001 has no "unconfigure" command to call — a
	real Procuring Entity is never meant to un-onboard itself — so a caller
	that genuinely wants a blank site accepts the same direct-delete
	authority this whole teardown path already exercises everywhere else.
	"""
	from kentender_core.services import organisation_structure as structure
	from kentender_core.services import regulatory_reference as register
	from kentender_core.services import site_configuration as configuration

	deleted: dict[str, int] = {}
	# Procurement Method Profile, Procedure Schedule Profile, Regulatory
	# Reference and its Set are audit-immutable by design (their own
	# on_trash refuses deletion) with exactly one sanctioned override: the
	# same kt_fixture_purge flag the document's own fixture-purge callers
	# already set — canonical.py's clear_non_canonical() uses it on
	# Regulatory Reference for exactly this reason.
	_PURGE_FLAGGED = {"Procurement Method Profile", "Procedure Schedule Profile", "Regulatory Reference", "Regulatory Reference Set"}

	def delete(doctype: str, names: list[str]) -> None:
		for name in names:
			if not frappe.db.exists(doctype, name):
				continue
			if doctype in _PURGE_FLAGGED:
				doc = frappe.get_doc(doctype, name)
				doc.flags.kt_fixture_purge = True
				doc.delete(ignore_permissions=True, force=True)
			else:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, delete_permanently=True)
		if names:
			deleted[doctype] = deleted.get(doctype, 0) + len(names)

	# Assignments and users first: everything below is what they were granted
	# on or authored through, and Frappe's own ownership/modified-by columns
	# would otherwise point at a user this function is about to delete.
	assignment_names = frappe.get_all(
		"User Responsibility Assignment",
		filters={"fixture_namespace": FIXTURE_TAG},
		pluck="name",
	)
	delete("User Responsibility Assignment", assignment_names)

	actor_emails = [f"{local}@moh.example.test" for local, _ in ACTORS]
	for email in actor_emails:
		if not frappe.db.exists("User", email):
			continue
		for doctype, field in (
			("User Responsibility Assignment", "user"),
			("User Scope Assignment", "user"),
			("User Permission", "user"),
			("Notification Log", "for_user"),
			("Contact", "user"),
		):
			if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, field):
				continue
			delete(doctype, frappe.get_all(doctype, filters={field: email}, pluck="name"))
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		deleted["User"] = deleted.get("User", 0) + 1

	# Profiles and the regulatory reference: every row, not just this seed's
	# own FIXTURE_TAG namespace. These four doctypes are audit-immutable
	# (on_trash refuses deletion outside the kt_fixture_purge flag `delete()`
	# already sets above), so nothing but a deliberate purge like this one
	# ever removes them — nothing outside a full wipe should call this
	# function (it has exactly one caller, `canonical.run(wipe=True)`), and
	# other test suites' own namespaces (e.g. Planning's, Regulatory
	# Reference's own test suite) were found accumulating hundreds of rows
	# here with no other path that ever cleans them up.
	from kentender_core.services import procurement_settings as settings

	for doctype in (settings.METHOD_PROFILE, settings.SCHEDULE_PROFILE):
		delete(doctype, frappe.get_all(doctype, pluck="name"))
	delete(register.DOCTYPE, frappe.get_all(register.DOCTYPE, pluck="name"))
	delete(register.SET_DOCTYPE, frappe.get_all(register.SET_DOCTYPE, pluck="name"))

	# Delivery Location / Contact Office: every row, not just this seed's own
	# named ones — neither carries a fixture_namespace column (an existing
	# row is updated in place on a rerun without ever being stamped if it
	# predates this seed), and other modules' own test suites were found
	# leaving obviously-disposable rows behind here (e.g. "Test Delivery
	# Location — Requisitions") with no other path that ever removes them.
	delete("Delivery Location", frappe.get_all("Delivery Location", pluck="name"))
	delete("Contact Office", frappe.get_all("Contact Office", pluck="name"))

	# Fiscal Years, then Organisation Units, then the site identity itself —
	# the two things every stage above ultimately hangs off, so last.
	fy_names = [configuration._fy_name(year) for year in FISCAL_START_YEARS]
	delete("Fiscal Year", [name for name in fy_names if frappe.db.exists("Fiscal Year", name)])

	unit_names = [name for name, _parent in UNITS]
	root = structure._root()
	if root:
		unit_names.append(root)
	pending = [u for u in unit_names if frappe.db.exists("Organisation Unit", u)]
	for _ in range(8):
		if not pending:
			break
		remaining = []
		for unit in pending:
			if frappe.db.count("Organisation Unit", {"parent_organisation_unit": unit}):
				remaining.append(unit)
				continue
			frappe.delete_doc("Organisation Unit", unit, force=True, ignore_permissions=True)
			deleted["Organisation Unit"] = deleted.get("Organisation Unit", 0) + 1
		pending = remaining

	if configuration.is_configured():
		for field in ("pe_name", "pe_code", "pe_type", "ppra_registration", "statutory_approval_route"):
			frappe.db.set_single_value(configuration.SITE_PE_DOCTYPE, field, "")
		frappe.db.set_single_value(configuration.SITE_PE_DOCTYPE, "entity_is_county", 0)
		frappe.db.set_single_value(configuration.SITE_PE_DOCTYPE, "timezone", "Africa/Nairobi")
		deleted["Site Procuring Entity"] = 1

	if commit:
		frappe.db.commit()
	return deleted


def _seed_assignments() -> list[str]:
	units = {
		row["unit_name"]: row["name"]
		for row in frappe.get_all(
			"Organisation Unit", fields=["name", "unit_name"], limit_page_length=0
		)
	}
	out = []
	for local, role, unit_name, kwargs in ASSIGNMENTS:
		outcome = administration.grant(
			user=f"{local}@moh.example.test",
			business_role=role,
			organisation_unit=units[unit_name] if unit_name else "",
			fixture_namespace=FIXTURE_TAG,
			actor="Administrator",
			**kwargs,
		)
		out.append(f"{outcome['assignment']}{'' if outcome['created'] else ' (existing)'}")
	return out
