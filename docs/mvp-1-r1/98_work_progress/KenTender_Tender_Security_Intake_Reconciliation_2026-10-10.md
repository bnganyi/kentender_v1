# Reconciliation — tender-security intake and sealed-bid confidentiality (10 October 2026)

Project Owner brief and decisions are quoted in the register (DEC-045 to DEC-048, item TSI-001) and in each document's control table. Nothing below is approved or committed; the six documents are Proposed.

## 1. Original contradictions

| # | Contradiction | Where |
|---|---|---|
| 1 | BDS required a separately authorised receipt owner and said an opening appointment grants no receipt permission; AUTH defined no such role; the implementation bundled the intake into the Head of Procurement Function office, who is also the evaluation secretary by office and, in the demonstration, the opening chair | BDS §5.9, §6; AUTH §4.4; `business_role_registry.py` |
| 2 | BDS §12.3 allowed “the same person may hold both capacities”; AUTH §5.8 allows holding two roles; no document prohibited or required separation | BDS, AUTH |
| 3 | No document stated the limited security-intake exception to sealed-bid confidentiality; AUTH §8 and the code gave Administrator and System Manager a technical read of bid existence and counts | BDS §5.9, AUTH §8, `technical_read.py` |
| 4 | `physical_original_required` was meant to follow the published Tender but was hard-coded true; electronic security was an upload with no submission, verification or distinction from the original | BDS §4.8, `tender_security.py` |
| 5 | Charles Mutiso recorded the demonstration intake; his actual permission was the Head's office role (authorised by the implemented rule, not unauthorised) | seeds, dev data |

## 2. Agreed rules (Project Owner, 10 October 2026)

Explicit Tender-scoped duty assigned by the Head of Procurement Function to an existing officer (assigner, scope, period recorded); office, appointments and technical status grant nothing; the Head sees assignments, never intake. Separation of intake from opening and evaluation enforced in both directions as an approved product policy (not a statutory prohibition); exposure persists after the duty ends; an unused assignment may be revoked; existing conflicts flagged for the Accounting Officer. The limited security-intake exception; intake independent of bid submission; matching only after the opening boundary. Administrator and System Manager get no pre-opening access to sealed records, on any surface; application restrictions, not infrastructure claims. Issuer verification mocked, its source “Test Issuer Service (simulation)” shown with the result and response time, no banners.

## 3. Document changes (all Proposed, predecessors unchanged)

BDS-CHG-001 v0.14 (supersedes the v0.13 proposal), AUTH-ADR-001 v1.13, TRUST-ADR-001 v0.4, BOP-CHG-001 v0.13, EVL-CHG-001 v0.9, SEED-002 v0.5; the register (4 decisions, 3 interfaces, delivery item TSI-001, proposals recorded); the Bid Submission runbook (new §3A). Preservation checks pass for all six; no new consistency error; the only new warnings are the expected forward-version citations. Boards owed: BDS-DES-15 redraw, a new duty page, the Company task status facts.

## 4. Implementation changes

Tender scope type and the Tender Security Intake Officer in the registry and the existing assignment mechanism; HOPF bundle tag removed; grant guard and participants hooks; exposure and conflict records and a migration that flags existing conflicts; opening and evaluation appointment checks (members, replacements, secretary by office and delegate); intake kinds (physical, issuer confirmation) with the issuer's time kept apart; intake never reads a bid; matching only after the opening starts (BOP publishes the boundary); sealed hand-off carries no intake; sealed families closed to technical accounts (no DocPerm, deny hooks, the record itself refuses, no technical-search resolvers, no per-bid technical read, bid evidence files not served by URL, audited service status); HOPF duty page; intake page limited to assigned Tenders; electronic security journey with the mock issuer and four separate facts; seeds and browser fixtures use Mercy Kilonzo.

## 5. Test evidence (kentender-test.local unless stated)

- Python new or changed: duty 14, intake and matching 20, verification 9, sealed surfaces 6, technical read 2, sealed desk read 5, BOP duty 5, EVL duty 6, core registry 19 and administration 39 — all pass.
- Regression sweep of 40 modules: all pass except five environment or earlier-work failures, none touching these changes (see §6).
- Vitest: bid portal 390, duty page 6, receipts page 12 — pass.
- Browser (Playwright): intake 6, duty 5, sealed access over real HTTP as Administrator 4, company task 6, review and release evidence 6 — all pass.
- Canonical seed rebuilt on the test site; every intake, assignment, conflict and boundary check passes. One unrelated check fails (requisitions hand-off version 1.5).
- Dev: migrated; 5 existing conflicts (Charles on opening committees) flagged for the Accounting Officer; dev data otherwise untouched.

## 6. Not closed, and why

1. The dev canonical world is still the old flow (Charles recorded the intakes). Reseeding dev is blocked by stray older Afya supplier organisations (Mary holds assignments in two); on the test site I removed them. Needs your decision to reseed or clean dev.
2. Pre-opening the supplier's bid reads **Not yet matched** (a consequence of matching after the boundary); confirm that wording.
3. Whether the original is required should come from the published Tender; the template publishes no such flag, so it is shown whenever security is required (TPR and STD-TPL change owed).
4. Bid Opening's own incident records still show an envelope identifier to System Manager on the Desk; not locked in this pass.
5. Exceptional (break-glass) access to a sealed record is not provided; TRUST requires the production support module to define it.
6. Failing for reasons outside this work: guidance (Daniel Otieno lacks System Manager on the test copy), overdue-close test (a leftover real Tender), acceptance-gaps (stepper labels from uncommitted UI work), technical-read conformance and module registry (other modules); the Documentation Control workbook is still stale.
