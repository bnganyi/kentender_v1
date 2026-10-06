# Conflicts and open points (row HOME6-0003, HOME6-0007)

Date: 4 October 2026. Each item names its follow-up and the tracker row it holds up. Nothing here changes an approved document.

## 1. Fixture conflicts inside HOME v0.6

| # | Conflict | Effect | Handling |
|---|---|---|---|
| 1 | **H10 versus H12 on Tender 042.** H10 (§10A.2, retained into §10B.2) has 042 "Supply of network switches" as a Bid opening on 25 June 2027, 11:00 (a Coming up row for Charles, who chairs). H12 (§10B.2) says it "shares the H10 world" yet has 042 "Supply of network switches" as "Appoint the evaluation committee", received 14 May 2027, 10:00. A Tender cannot be both awaiting evaluation-committee appointment since May and about to open on 25 June. HOME §13.1 says 042 exists only in H10. | H10 and H12 cannot be loaded into one world. | Phase 7 builds H12 as its own world with its own 042 binding (FU-HOME-08). Neither scenario is edited. |
| 2 | **"held by" versus "from" (H12).** §10B.2 table: "Waiting for cancellation compliance evidence; held by Brian Wafula". §10B.3 brief: "Waiting for cancellation compliance evidence from Brian Wafula". The board follows the brief. | One string. | Build to the brief (the design input); note in FU-HOME-08. |
| 3 | **Dates.** The spec's read times are 16, 17 and 18 June 2027; the real date is 4 October 2026 and every canonical row is future-dated. | Relative labels would read "in the future" on a live clock. | Home reads `test_clock.current_instant()` (plan D10); each fixture sets its own instant (`seed_scenario_map.md`). |
| 4 | **035 and 036 are skipped** in the H1 references (034, 037, 039, 040) and H8 uses 050–055 as a six-action fixture; the canonical Tender number is generated (`TND-MOH-2027-002` on dev). | References are illustrative. | Fixtures bind generated identities per scenario; text comparisons use the generated reference, not the spec's. |

## 2. Wording that differs between HOME and the owners (FU-HOME-03)

| HOME string | Owner wording | Home's treatment |
|---|---|---|
| Authorise requisition | REQ code: "Decide whether to authorise — {ref}"; REQ-DES-01-ACTION "Decide whether to authorise"; §7.1/§12.1/REQ-DES-08 use "Authorise requisition" | Use the REQ document's own "Authorise requisition" once REQ's feed names it (FU-HOME-02) |
| Appoint the evaluation committee | EVL §7.1 prose matches; §7.3 register: "Appoint evaluation committee for {tender}" | Action text "Appoint the evaluation committee"; tender title carried separately |
| Decide whether this requirement is available to Procurement Planning | NDS §5.5 headline matches; §7.6 register "Review need" | Use the §5.5 headline |
| Authorise publication | TPR §5.11 "Authorise publication of Tender {ref}" | Action text without the reference; title carried separately |
| Prepare professional opinion; Resolve notice delivery; Decide award | AWD §5.9 matches; code appends " for {ref}" | Strip the reference suffix by carrying title and action separately |

## 3. Cross-document conflicts

| # | Conflict | Handling |
|---|---|---|
| 1 | KT-STD v1.22 §4 says register the route in `cl_surface_registry` and `STITCH_DESK_SURFACES`; AGENTS.md §6.5 and the OVS plan (D10) say never add Industry pages. | AGENTS.md governs; Home does not touch the registry. KT-STD wording needs correcting (FU-HOME-11). |
| 2 | HOME §18.0C says design-system tokens and components are "approved in the design system"; no approval record was found and `ds-additions.css` is headed "Not approved". | Phase 1 adopts DS-REV-002 on the owner's gate (OD-3, HOME-G01). Components for Home come from the board, not from `ds-additions.css`. |
| 3 | HOME's Sources list omits PLN, BUD and STR although §17.1 names them. | Low; FU-HOME-12. |
| 4 | HOME §3 lists Contract Management as a later provider; it is deferred (OVS OD-3). | Hook is open to it; no row built (FU-HOME-07). |

## 4. ANL status (row HOME6-0007)

- The repository has no ANL document. The owner's Downloads folder has `KenTender_ANL-CHG-001_Procurement_Analytics_v0_6.md` (4 Oct 16:18, status line still "Proposed … approval of v0.6 required") and `…_v0_8.md` (4 Oct 19:40, "Proposed — 4 October 2026; v0.6 is the approved version"). HOME §18.0C records the owner approving "KT-STD v1.22, HOME v0.6 and ANL v0.8 together", so the Downloads copies carry stale control tables.
- `KenTender home and analytics.zip` (4 Oct 20:44) holds the Home design pack (identical to the repo's: `Home.dc.html` 139,314 bytes, same `_ds`) and an `Analytics/` pack of six boards (Overview, Peter HRMD, Planning and Needs, States, Tenders and Requisitions, index). The Downloads copy of `KenTender_HOME-CHG-001_Home_v0_6.md` (77,805 bytes) is the pre-approval proposal; the repo copy (78,643 bytes) is the approved one and is the controlling file.
- No Analytics page, route, verdict read or tab list exists in code, and the sidebar item is `coming-soon`. HOME §5.1 item 6 and AC-14 make the Analytics link depend on "the actor's Analytics verdict", which does not exist.
- **Decision for the build (plan D7):** the link is absent until ANL ships; HOME-AC-14 is recorded as met by omission, not by a gated link. Which tab the link opens is also unspecified (HOME §11: `/app/analytics/{tab}`; the Overview tab has no suffix). Both are owner questions (FU-HOME-05). No ANL file is filed by this change.

## 5. Questions for the owner (none blocks Phase 1 or 2)

1. Board delta 1: keep the filled module chip (board) or follow the design-system readme (glyph only)? Same question for delta 2 (badge colour source) and delta 8 (rail divider).
2. After Home replaces My Work: where should the Procurement Industry screens' "Home" breadcrumbs point (today the hidden `Procurement Home` workspace) (FU-HOME-21)?
3. Should Administrator and unassigned users also land on Home, or keep Frappe's desktop (today only assigned users land on My Work)?
