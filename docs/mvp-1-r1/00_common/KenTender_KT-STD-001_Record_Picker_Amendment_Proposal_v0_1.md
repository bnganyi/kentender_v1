# KT-STD-001 amendment proposal — Record picker

| Field | Value |
|---|---|
| Document | Amendment proposal for KT-STD-001 (Document Design and Verification Standards) |
| Version | 0.1 |
| Status | **Proposed** — not part of KT-STD-001; no register entry; no identifier assigned |
| Prepared | 13 October 2026 |
| Relies on | The Shared Record Picker Plan v0.1 (Approved, Project Owner, 13 October 2026, “Mark as approved.”; read in full); AGENTS.md section 6.12 as built; KT-STD-001 v1.29 (**not read in full for this proposal** — see §7) |
| Owner decision | Project Owner, 13 October 2026, quoted in §1 |
| Effect if adopted | Adds one component clause to KT-STD-001 (a new version, Proposed until re-approved) |

KT-STD-001 v1.29 is not edited by this file. The text in §2 is for the owner to place, in a new KT-STD-001 version made under the document-change protocol.

## 1. Source

The owner's report, with the screenshot of the Bid opening Add member dialog:

> "This dropdown to select a member from a list of potentially hundreds of users. There is no way to search or sort or even filter. There are many other scenarios that require such a control. Suggest"

The owner's decisions on the suggestion, and on the plan that followed:

> "Same department then recent picks"
>
> "General from start"
>
> "Mark as approved."
>
> "Implement"

## 2. Proposed clause (text for KT-STD-001)

This is the clause the approved plan states (plan section 3, items 1–13), with the five behaviours the design board and the build added marked **(added)**. The plan's wording is unchanged where it still holds.

> **Record picker.** Wherever a reader chooses one person or one record from a list that can grow beyond about a dozen entries, they use the one picker. No screen draws a plain dropdown for such a choice, and no screen sends the whole list to the browser.
>
> 1. **Shape.** A single field that looks like the Industry text field with a search icon. The reader types to search; a list opens beneath it. A chosen record shows as its name inside the field with a "Clear" control, and the list is not drawn while a record is chosen. **(added)** Typing over a chosen record clears the choice and searches for what was typed; the screen is told the choice is gone.
> 2. **Search.** Matches the record's name, its one-line detail and any extra keywords the source supplies (for a person: login). Matching is by word start, ignoring case and accents. Search starts after the reader stops typing for about a quarter of a second. A new character never leaves the old list standing as if it answered the new text; the list marks itself as updating and is replaced when the answer arrives. **(added)** A whole login typed exactly finds that person first, ahead of anyone whose words merely share its parts.
> 3. **Results.** At most 20 rows. Each row has the name in strong type, the detail beneath it, and the matched text emphasised. When more matched than are shown, the last line reads "Showing 20 of 143. Keep typing to narrow." Before typing it reads "Showing 20 of 216. Type to search." **(added)** Ranking: a whole login, then a name that starts with the text, then a word of the name, then the detail or keywords; ties broken by name.
> 4. **Before typing.** Focusing an empty picker opens a list in up to three parts, in this order: **Your department** (people whose home unit is the reader's; records the source marks as near the reader), **Recent** (the last five the reader chose from this source, excluding any already shown), then **Everyone else** in name order. Each part has a small heading and is left out when empty. **(added)** A list that is only "Everyone else" has no heading. **(added)** A source may name the parts itself (units read "Your directorate" and "Other units"). A reader with no recorded home unit sees Recent, then Everyone else. A first opening says "Loading people…" until the first answer.
> 5. **Not available is shown, not hidden.** A row that cannot be chosen stays in the list, greyed, with the reason on its second line. Arrow keys skip it; clicking it does nothing. The reason is the command's own wording.
> 6. **Nothing found.** "No person matches 'xyz'." When the source can say why, one further line says so.
> 7. **Failure.** "Could not load people. Try again." with a Try again button. It does not raise Frappe's Message dialog, and it does not clear what the reader has already chosen.
> 8. **Keyboard.** Down and Up move through the choosable rows; Enter chooses; Esc closes the list and **only** the list (inside a dialog, a second Esc closes the dialog); Tab chooses nothing and moves on; Home and End go to the first and last row.
> 9. **Assistive technology.** The field is a combobox in the standard ARIA 1.2 pattern. A polite live region says "12 results", **(added)** "20 of 143 results" when more matched than are shown, "No person matches xyz" or "Could not load people." An unavailable row's reason is part of its accessible description. Clear has a full name ("Clear Amina Hassan").
> 10. **Placement.** **(added)** The list floats over the page, placed from the field and sized to the room there is (never shorter than a few rows, never taller than 340 px), so no dialog, table row or scroll area around the field can clip it. It opens upward when there is no room beneath and follows the field if the page scrolls or resizes. On a narrow screen it is as wide as the field and rows are at least 44 px tall.
> 11. **Required and invalid.** The field accepts the standard `invalid` and required marks. The error text is the screen's inline field error, never a dialog.
> 12. **What it is not.** It is not the authority for who may be chosen. The command that saves the choice checks again and refuses an ineligible one with a field error. **(added)** A choice that a later change on the screen makes ineligible (a different role) is re-checked and shown with its reason beneath the field.
> 13. **Where it does not apply.** Choices from a short fixed vocabulary (a role on a committee, a country, a status, a unit of measure) and a choice from a handful of people already on the screen stay plain selects. **(added)** A filter over a person or record list offers the picker with an "All …" first row, which is a choice, distinct from nothing chosen.
>
> 14. **Adding several.** **(added, approved 14 October 2026)** Where a reader names many people in one go (a committee), one dialog holds the picker and the list being built. The picker's list stays open in the page beside the field; choosing a row adds the person to **To appoint** and leaves the list, the search text and the reader's place where they were; an added person stays in the list greyed "Added to this list". Each person's role is set in the list, and one action carries them all. Enter adds the active row and moves to the next choosable one, with the search text selected so typing starts a new search; Esc clears the search, and a second Esc reaches the dialog. A live region says "Added Amina Hassan. 3 to appoint." The command that carries them checks each person again and the refused person's row says why.

## 3. As built (observations, not rules)

| Item | What exists on 13 October 2026 |
|---|---|
| Server | `kentender_core/services/record_picker.py` (registry through the `kt_record_picker_sources` hook, clamping, matching, ranking, near/recent/rest, `search`, `resolve`, `matches`, `people_near`, `person_row`), `api/record_picker.py`, and core's own sources in `services/picker_sources.py` |
| Component | `kt_industry/components/RecordPicker.vue`, published as `kentender_core.industry.mountRecordPicker` (`kt_industry_record_picker.bundle.js`); per-app wrapper `record_picker_shared/RecordPickerHost.vue` in `kentender_core`, `kentender_procurement`, `kentender_budget`, `kentender_strategy` (equality spec) |
| Styling | Part 12 of the generated `kt_industry_tokens.css`, from `PICKER` in `scripts/industry_design_css.py`. It is **not** in the design pack yet |
| Sources | `bid_opening.committee_member`, `bid_evaluation.committee_member`, `bid_evaluation.secretary`, `core.responsible_user`, `core.organisation_unit`, `core.home_unit`, `core.reference_unit` |
| Adopted by | Bid opening (Add members, which adds several and appoints them in one action; Replace member); Bid evaluation (committee rows, replacement, secretary delegation); System setup (assign responsibility: user and unit; set home unit; the register's unit filter); Budget (a line's "Available to", in a table row) |
| Stays a plain select, with its reason | `ALLOWED` in `kentender_core/tests/test_record_picker_guard.py` (7 entries) |
| Retired | `search_users` (System setup's administrator-only user search) and the `.kt-matches` list styles; the Bid opening and Evaluation "candidates" payloads and `get_candidates` |
| Developer rule | AGENTS.md section 6.12 |
| Gate | `test_record_picker_guard` fails on a new `<select>` over a people or unit list, and on a stale allowance |

### 3.1 Where the build departs from the approved plan

1. **One source for Add member and Replace member**, not two. Both ask "who may take this role on this committee"; the replacement passes the absent member's role.
2. **A row carries `extra`** (up to eight short text facts handed back to the screen when chosen). The plan listed five row keys. A screen needing a person's department or designation read it from `extra` instead of parsing the text beneath the name.
3. **A search returns the source's wording** (`labels`: noun, plural, the two part headings, a hint), so a screen passes none of it.
4. **The list floats (fixed position)** instead of sitting inside the field's wrapper. The plan named dialog clipping as risk 3; it happened on the first real browser run (the System setup home-unit dialog cut the list off and the backdrop swallowed the click). Fixed, with specs.
5. **An exact login ranks first.** Found when a login typed in a browser test chose a different person who shared its words.
6. **The stylesheet part is Part 12, not Part 8** (the plan's number was taken).
7. **A person barred by the tender-security duty was briefly left out of the list** in Bid opening and Bid evaluation (the plan says list every unavailable person). The Project Owner saw a person "not appearing" with the empty message "No person matches", reverted on 14 October 2026: they are listed unavailable with the command's own reason, as the plan says. Tests: the opening and evaluation intake-duty tests assert the listed reason equals the command's refusal.
8. **Some inventory rows changed.** The Departmental need and Planning purchase "Unit" fields are units of measure (a catalogue the reader can extend), not organisation units, so they stay selects. The Meetings department filter lists only departments in meetings the reader already sees, and two "my departments" selects (Needs editor, Requisitions filter) are scope-limited; all are on the guard's allowance with a reason.
9. **`search_users` was removed**, not kept: nothing called it once System setup moved to `core.responsible_user`.
10. **A dependent field is set first.** In Replace member the absent member's role changes who may be listed (an independent member cannot be someone who processed the Tender), so the screen re-checks a saved choice when the role changes, and the browser journeys set the role before choosing the person. In Add members each person has their own role, so no one role can decide the list: every row says in `extra` whether that person could not be the independent member, and the dialog shows it beside them.
11. **The Add members dialog appoints in one action, as the board draws it.** The page's committee table (boards a1 and a2) is now filled only by a refused appointment or by a refresh that brings a draft back; it is no longer where people are added one at a time. The board's "Appoint N members" is the same command as the page's "Appoint committee", with the same guard when refused. If the Project Owner would rather the dialog only add people to the table, with Appoint committee on the page, that is a small change (§6, item 5).

## 4. Instruction for Claude Design (to add the picker to the core design)

> The board "Record Picker States" draws the people picker. Please extend it, and add the picker to the core Industry design system so the stylesheet can be regenerated from it.
>
> Draw: the **units** variant (a path from the root as the name, the unit code beneath, "Your directorate" and "Other units" parts, the "All …" first row for a filter, and the chosen "All departments" state); the picker **inside a table row** (a Budget line's "Available to") with the list floating over the rows beneath; the list **floating over a dialog** without being clipped by the dialog's edge, opening upward at the bottom of the screen; the **first opening** ("Loading people…" with no rows); a **list with no heading** (only "Everyone else"); and the "20 of 143 results" announcement in the accessibility table. Keep the class names `kt-picker`, `kt-picker-anchor`, `kt-picker-field`, `kt-picker-input`, `kt-picker-clear`, `kt-picker-list` (`is-up`, `is-updating`), `kt-picker-group`, `kt-picker-option` (`is-active`, `is-disabled`), `kt-picker-name`, `kt-picker-detail`, `kt-picker-reason`, `kt-picker-mark`, `kt-picker-foot`, `kt-picker-status`, `kt-picker-note`, so the existing component keeps working. Do not change tokens, colours or existing component rules. State is carried by modifier classes, not inline style.

## 5. Acceptance criteria and the evidence for each

From the approved plan, section 6. "Observed" means the check ran on 13 October 2026.

| # | Criterion | Evidence |
|---|---|---|
| 1 | Search over 1,000 accounts returns a ranked first page; never more than 50 rows; ≤300 ms *(proposed)* | **Not measured at 1,000**: the test site has 51 people. Measured 0.36 s for 35 people on `bid_opening.committee_member` (about 10 ms a person), which is comfortable to a few hundred and slow past a thousand (AGENTS.md section 6.12, known limits). The 50-row cap is a server test |
| 2 | Empty state: department, then recent, then everyone else; nobody twice | Server test (order, cap, no duplicates); component spec; seen live as "Your department / Recent / Everyone else" only on the design board — **not observed on the running site** (no home unit recorded for the test accounts) |
| 3 | An unavailable person is visible, greyed, with the reason, and cannot be chosen | Component spec; Bid opening and Bid evaluation parity tests against the commands; Playwright (the replacement journey, a current member listed and unchoosable) — observed |
| 4 | A hand-built request naming an ineligible person is refused by the command | The commands' own existing tests are unchanged; the parity tests prove list and command agree. Not re-run as a separate hand-built-request test |
| 5 | A slow older answer never replaces a newer one | Component spec — observed |
| 6 | Esc closes the list then the dialog; the list is not clipped at 1440 px or 390 px | Esc: component and dialog specs. Clipping: **found and fixed at 1440 px** (home-unit dialog) and observed fixed in two System setup dialogs; **390 px not checked live** |
| 7 | Keyboard-only completion of Add member; the result count is announced | Keyboard behaviour: component specs. The browser journeys choose by clicking the row. Live-region text: component spec. **No screen-reader testing** |
| 8 | A new source is one provider, one hook entry, one parity test; a new screen needs a bundle entry, a host wrapper and a departure entry | Seven sources were added this way. Core itself gained `extra`, `matches`/`words` and the exact-login rule as the early consumers needed them; the later sources needed nothing in core beyond a hook entry |
| 9 | Adding a `<select>` over a people list fails the guard | Red demonstrated with a probe template, then removed; green on the repository |
| 10 | `make design-css-check` passes; no test data left on the dev site | `make design-css-check` passes; browser runs were on the test site only (see §7) |

## 6. Decisions for the owner

1. **Should the opening committee being drafted on Prepare opening be saved on the server?** Today the Add members dialog appoints in one action, so the people sit in the page's table only after a refused appointment. That table survives a refresh and coming back in the same tab (session storage) and says "Not appointed yet", but it is not saved for another browser or person. A server draft would be a new state in the appointment record. Recommendation: not now; it is a domain change for BOP-CHG-001.
2. **Fold §2 into the next KT-STD-001 version?** Recommendation: yes, with §3.1 items 1–11 either accepted into the clause or rejected.
3. **Open decisions from the plan (section 9.2).** The build followed the recommendations without an answer: "Everyone else" kept in the empty state (the board draws it); recents kept in the browser keyed by the signed-in person; `search_users` removed; the three `people.py` copies left alone. Confirm or reverse.
4. **Should the Add members dialog appoint directly (as built; the approved board's "Appoint N members") or only add people to the page's table, for the page's Appoint committee?** Recommendation: directly, as the board draws it; the table then serves a refused appointment and a refresh.
5. **Give a source the means to scale?** Recommendation: when a deployment has more than about a thousand responsibility holders, move `bid_opening.committee_member` to a database-filtered source. Not built; there is no such deployment today.

## 7. Not verified

- KT-STD-001 v1.29 and the baseline register were not read; where the clause belongs, any overlap with an existing clause, and whether an identifier is needed are unchecked.
- The picker has not been run against 1,000 accounts, and "near" and "recent" have not been seen on the running site (§5, items 1 and 2).
- 390 px layout and any assistive technology were not tested.
- The Playwright journeys that drive the changed screens: Bid opening Prepare (the main journey passes; the next test in the file, the Tender record's link to its opening, fails because the Tender page's header link now gives way to the Opening stage block's own "View record" link, which this work did not touch, and the third test did not run because the file is serial), Bid evaluation committee (4 of 4), System setup responsibilities and home units (all), Budget officer (the picker step passes; a later test in the file fails while seeding its own fixture, `BUDGET_INVALID_STATE`, not in anything the picker touches, **not proven to fail without this work**). The Bid opening demo walk and the Evaluation journeys beyond the committee were not run.
- The test site was used for every browser and Python run; it has not been rebuilt afterwards, so it may hold leftovers from the Budget and other fixtures.
- The "stays a plain select" allowances for the Requisitions department filter and the Meetings filter assume the lists are small; their sizes were not measured.
