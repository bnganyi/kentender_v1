# Shared record picker — build plan and reuse guide

| Field | Value |
|---|---|
| Document | Build plan and developer reuse guide for one shared search-as-you-type picker (people first, any record by design) |
| Version | 0.1 |
| Status | **Approved** — not part of KT-STD-001 or AGENTS.md; no register entry; no identifier assigned |
| Approved on | 13 October 2026 |
| Approval record | Project Owner, 13 October 2026, verbatim: “Mark as approved.” |
| Prepared | 13 October 2026 |
| Relies on | AGENTS.md §6 (read in full for this plan); the Table Pagination Amendment Proposal v0.1 (read in full, used as the precedent for shape); KT-STD-001 v1.29 (**not read** — see §11) |
| Owner decisions | Project Owner, 13 October 2026, quoted in §1 |
| Effect if adopted | Adds AGENTS.md §6.12 (text in §7), one component clause to KT-STD-001 (a new version, Proposed until re-approved), and one section to the generated design-system stylesheet |

No application code, AGENTS.md or KT-STD-001 text is changed by this file. §3 is the behaviour the picker must have; §4 is the proposed technical contract; §5 is the build order; §7 is the reuse guide in the form it will take once built.

## 1. Source

The owner's report, with the screenshot of the Bid opening → Add member dialog:

> "This dropdown to select a member from a list of potentially hundreds of users. There is no way to search or sort or even filter. There are many other scenarios that require such a control. Suggest"

The owner's answers to the two questions the suggestion left open:

> "Same department then recent picks"
>
> "General from start"
>
> "Write the plan and include documentation for reusability across the application."

So: the picker's empty state lists the reader's own department first, then their recent picks; and it is built as a general record picker from the first slice, not as a person-only control to be generalised later.

## 2. What exists today (observations, not rules)

Checked on 13 October 2026 by reading the files named; paths are relative to the repository root.

### 2.1 The control

| Item | What exists |
|---|---|
| Add member dialog | `kentender_procurement/.../bid_opening/components/AddMemberDialog.vue`: a native `<select>` over a `candidates` prop; the dialog filters out people already chosen. Its header comment calls the picker "a registered departure" from the board (`tests/ui/fidelity/departures/bid-opening.js`) |
| Server list behind it | `bid_opening/services/appointment.py` `candidates(tender)`: every enabled person holding an active responsibility who passes `people.eligibility` and `security_duty.committee_blocker`, sorted by name. The whole list travels to the browser |
| Evaluation committee | `bid_evaluation/services/reads.py` `candidates(tender_reference, user, purpose)` feeds `public/js/bid_evaluation/screens/committee.js` `personOptions`. Its comment says the list is "every staff account, not only responsibility holders" for the committee, and procurement officers for the secretary. The same function returns `department` per person |
| Only typed search that exists | `kentender_core/api/responsibility_api.py` `search_users(query, limit=20)`: enabled System Users by name or login, first 20, **callable only by an assignment administrator** (`require_assignment_administrator_any`). Used by System setup's `AssignDialog.vue` with a hand-built list (`.kt-matches`). The same dialog's Organisation Unit field is a read-only "combobox" you click open but cannot type in |
| Styling of that list | `.kt-matches` lives in `kentender_core/public/css/kt_admin_configuration.css`, not in the generated `kt_industry_tokens.css` |
| Department of a person | `bid_evaluation/services/member_department.py` `department_of(user)` and core's `staff_home_unit.py` (the staff home organisation unit; its own docstring: "display information, never authority") |

### 2.2 What this means for the design

1. **The rule for "who may be named" differs by screen and belongs to that screen's module.** Opening uses responsibility holders; Evaluation uses every staff account. A single central people list would silently change one of them. The picker therefore owns the *search, ranking, paging and display*; each module keeps its own *eligibility* (§4.1).
2. **`people.py` helpers are copied per module** (`bid_opening`, `bid_evaluation`, `award` each have `full_name`, `holds`, `holders`). This plan does not merge them; it is noted as a related finding (§9).
3. **Command-time checks already exist** (`reads.candidates` says "Eligibility is decided again by the command; this is only the pick list"). The picker keeps that: it is never the authority (§4.4).
4. **Hundreds of rows is the problem today, thousands is the next one** (suppliers, items, tenders), so the control must not assume the whole list fits in the browser.

### 2.3 Where a person or record is chosen today

Found by a grep for `<select>` lines mentioning person, user, member, officer, holder, assignee, supplier, unit, candidate, successor, approver, reviewer or delegate. **Call sites were located, not each opened**; the Phase 0 audit (§5) builds the complete list with a script, because a `<select>` whose line does not contain those words was not found.

| Call site | File | Proposed disposition |
|---|---|---|
| Add member — Member | `bid_opening/components/AddMemberDialog.vue` | **Picker** (first slice) |
| Replace member — With | `bid_opening/components/ReplacementForm.vue` | **Picker** |
| Replace member — Replace | `bid_opening/components/ReplacementForm.vue` | Stays a select: chosen from the committee, at most a handful |
| Opening — Repeated by, Read aloud by | `bid_opening/screens/OpenBidsScreen.vue` | Stay selects: chosen from the committee |
| Evaluation committee and secretary | `bid_evaluation/screens/committee.js` | **Picker** |
| System setup — assign a responsibility, User | `core/system_setup/components/AssignDialog.vue` | **Picker** (retires the hand-built list) |
| System setup — assign, Organisation Unit | same file | **Picker** (source: units, shows the path) |
| System setup — set home unit | `core/system_setup/components/SetHomeUnitDialog.vue` | **Picker** (units) |
| System setup — filters by unit | `core/system_setup/tabs/UserResponsibilitiesTab.vue` | **Picker** with an "All units" first row |
| Departmental need — unit | `departmental_needs/components/NeedEditorScreen.vue` | **Picker** (units in the reader's scope) |
| Planning purchase entry — unit | `procurement_planning/components/DppEntryEditorScreen.vue` | **Picker** (units in scope) |
| Budget version line — owner unit | `kentender_budget/.../BudgetVersionEditorScreen.vue` | **Picker**, in a table row (see §8, risk 5) |
| Meetings — department filter | `procurement_meetings/ProcurementMeetings.vue` | **Picker** with an "All departments" first row |
| Bid portal — contact person | `bid_portal/screens/CompanyTaskScreen.vue` | Stays a select: the company's own few people |
| Supplier portal — country, structure, type, ownership, evidence type | `kentender_suppliers/.../supplier_account_portal/*` | Stay selects: fixed vocabularies |

## 3. The behaviour (proposed clause for KT-STD-001 and the contract every screen gets)

> **Record picker.** Wherever a reader chooses one person or one record from a list that can grow beyond about a dozen entries, they use the one picker. No screen draws a plain dropdown for such a choice, and no screen sends the whole list to the browser.
>
> 1. **Shape.** A single field that looks like the Industry text field with a search icon. The reader types to search; a list opens beneath it. A chosen record shows as its name inside the field with a "Clear" control, and the list is not drawn while a record is chosen.
> 2. **Search.** Matches the record's name, its one-line detail (for a person: designation and department) and any extra keywords the source supplies (for a person: login). Matching is by word start, ignoring case and accents. Search starts after the reader stops typing for about a quarter of a second. A new character never leaves the old list standing as if it answered the new text; the list marks itself as updating and is replaced when the answer arrives.
> 3. **Results.** At most 20 rows. Each row has the name in strong type, the detail beneath it, and the matched text emphasised. When more matched than are shown, the last line reads "Showing 20 of 143. Keep typing to narrow." Ranking: name starts with the text, then a word of the name starts with it, then the detail or keywords contain it; ties broken by name.
> 4. **Before typing.** Focusing an empty picker opens a list in three parts, in this order: **Your department** (people whose department is the reader's own; records the source marks as near the reader), **Recent** (the last five the reader chose from this source, excluding any already shown), then **Everyone else** in name order. Each part has a small heading and is left out when empty. A reader with no recorded department sees Recent, then Everyone else.
> 5. **Not available is shown, not hidden.** A row that cannot be chosen stays in the list, greyed, with the reason on its second line ("Already on this committee", "Was involved in processing this Tender"). Arrow keys skip it; clicking it does nothing. The reason is the source's own wording.
> 6. **Nothing found.** "No person matches 'xyz'." When the source can say why (for example, only people holding a certain responsibility can be named here), one further line says so.
> 7. **Failure.** If the search cannot be answered, the list says "Could not load people. Try again." with a Try again button. It does not raise Frappe's Message dialog, and it does not clear what the reader has already chosen.
> 8. **Keyboard.** Down and Up move through the choosable rows; Enter chooses; Esc closes the list and **only** the list (inside a dialog, a second Esc closes the dialog); Tab chooses nothing and moves on; typing anywhere in the field searches. Home and End go to the first and last row.
> 9. **Assistive technology.** The field is a combobox in the standard ARIA 1.2 pattern: it announces whether the list is open, which row is active, and, in a polite live region, "12 results" or "No person matches". An unavailable row's reason is part of its accessible description. Clear has a full name ("Clear Amina Hassan").
> 10. **Narrow screens.** The list is as wide as the field and rows are at least 44 px tall. The list never extends past the viewport; it opens upward when there is no room beneath.
> 11. **Required and invalid.** The field accepts the standard `invalid` and required marks. The error text is the screen's inline field error (AGENTS.md §6.10), never a dialog.
> 12. **What it is not.** It is not the authority for who may be chosen. The command that saves the choice checks again and refuses an ineligible one with a field error.
> 13. **Where it does not apply.** Choices from a short fixed vocabulary (a role on a committee, a country, a status) stay plain selects. A choice made from a handful of people already on the screen (who read the minutes aloud) stays a select.

Notes the owner may want to veto: the **Everyone else** part in item 4 (the owner's words were "same department then recent picks"; without it a reader with no department and no recents would see an empty list on focus), and the limit of 20 (the existing `search_users` uses 20).

## 4. Design

### 4.1 Division of work

| Concern | Owner |
|---|---|
| The component, keyboard, display, debounce, stale-response guard, recent-pick memory, styling | `kentender_core` (one component, one stylesheet section) |
| The search endpoint, source registry, clamping, ranking, "near" and recent ordering, the page of results | `kentender_core` |
| **Who may be listed, who may be chosen, the reason a row is unavailable, which rows are near the reader** | The module that owns the choice, as a *source provider* it registers |
| Checking the choice again when it is saved | The module's existing command, using the same function as its provider (§4.4) |

### 4.2 Server contract (proposed)

**Registry.** Each app publishes its sources through a hook, the same pattern as `kt_technical_reference_resolvers`:

```python
# hooks.py of the owning app
kt_record_picker_sources = ["kentender_procurement.bid_opening.services.picker_sources.sources"]
```

```python
# bid_opening/services/picker_sources.py
def sources() -> list[dict]:
	return [{
		"key": "bid_opening.committee_member",   # unique, dotted: <module>.<what is chosen>
		"noun": "person",                        # "No person matches ..."
		"match": "core",                         # see below
		"provider": "kentender_procurement.bid_opening.services.picker_sources.committee_members",
	}]

def committee_members(*, query: str, context: dict, actor: str, limit: int) -> list[dict]:
	"""Rows the actor may see for this choice. Eligibility and scope are decided here."""
```

`match` says who filters by the reader's text: `"core"` (the provider returns every row the actor may see, core matches and ranks; right for a bounded set, up to about 2,000 rows, and lets an existing `candidates()` function become a provider unchanged) or `"provider"` (the provider filters in the database by `query` and returns at most `limit` rows, plus the total that matched; right for suppliers, items, tenders).

**Row.** The only keys core passes on to the browser (anything else a provider returns is dropped):

| Key | Meaning |
|---|---|
| `id` | The value saved (a user id, a unit code, a record name) |
| `label` | Name in strong type |
| `detail` | One line beneath: for a person "Accounting Officer · Ministry of Health"; for a unit its path; the provider composes it |
| `keywords` | Optional extra searchable words that are not displayed |
| `near` | Optional true when the row is near the actor (for a person: same home unit as the actor) |
| `disabled_reason` | Optional wording; present means shown but not choosable |

**Endpoint.** `kentender_core.api.record_picker.search(source, query="", context=None, recent=None, limit=20)` and `resolve(source, ids, context=None)`, both whitelisted. Returns:

```json
{"rows": [{"id": "...", "label": "...", "detail": "...", "disabled_reason": null, "section": "near"}],
 "total": 143, "limit": 20}
```

`section` is `near`, `recent`, `rest` or (when the reader typed) `match`. `resolve` returns the same row for ids the actor may see, so a saved choice that is no longer eligible still shows its name, with its reason.

**Rules core enforces regardless of provider:**

1. The actor is `frappe.session.user`. It is never read from an argument.
2. An unknown source key, or a provider that raises "not found" or "no permission", gives the masked `frappe.DoesNotExistError("Not found")` the Evaluation candidates already use, so the existence of a source is not confirmed to someone who may not use it.
3. `query` is trimmed and cut at 80 characters; `limit` is one of 20 or 50; `context` must be a JSON object under 2 KB; `recent` at most 10 string ids. List and object arguments go through `frappe.parse_json`, because a whitelisted method receives them as strings (a recorded trap on this bench).
4. Rows are filtered to the contract's keys, so a provider cannot leak a field by adding it.
5. `recent` ids are only ever used to *order* rows the provider already returned. An id the provider did not return is dropped silently, so a stale or foreign id reveals nothing.
6. Per-user rate limiting by Frappe's own mechanism is a Phase 1 check (§5), not assumed to exist.

**"Near the reader."** For people, core ships one helper that marks a row `near` when the person's home organisation unit equals the actor's, read through core's own `staff_home_unit` read. The home unit is display information and never authority (its own module says so); the picker uses it only to *order* suggestions, never to decide eligibility. For other record kinds a provider sets `near` by its own rule or not at all.

### 4.3 Client contract (proposed)

Same shape as the pager, for the same reason (AGENTS.md §6.6: a component object cannot cross a bundle boundary):

- Component: `kentender_core/public/js/kt_industry/components/RecordPicker.vue`.
- Mount helper: `kentender_core.industry.mountRecordPicker(el, opts)`, published by `kt_industry_record_picker.bundle.js`, with its own Vue instance; it binds `__` and `frappe` on `globalProperties` (AGENTS.md §6.1) and returns `{ update(next), unmount(), focus() }`.
- Per-app wrapper `public/js/record_picker_shared/RecordPickerHost.vue` (`v-model`, plus `@change` carrying the whole row), copied into `kentender_core`, `kentender_procurement`, `kentender_budget` and `kentender_strategy` like `pager_shared`; a `record_picker_shared.spec.js` fails if the copies differ.
- The search call uses `frappe.call({ silent: true })` so no Message dialog appears (AGENTS.md §6.10); `opts.fetch` replaces it in tests and on the public portal.

```js
kentender_core.industry.mountRecordPicker(el, {
	source: "bid_opening.committee_member",
	context: { tender },               // opaque to the picker; the provider reads it
	value: userId,                     // the caller's OWN selection (AGENTS.md §6.4), never the server echo
	valueLabel: "Amina Hassan",        // shown while chosen; if absent the picker calls resolve()
	inputId: "bop-add-member-person",  // so the screen's <label for> works
	placeholder: "Search by name, role or department",
	noun: "person",
	disabled: false,
	invalid: false,
	onChange(row) {},                  // row, or null when cleared
});
```

Behaviours that must be built in, because each has already cost this repository a defect elsewhere:

- A sequence token on every search (`kentender_core.desk_page.createSequenceGuard()`), so a slow answer for "ami" can never replace the answer for "amina".
- Esc inside a dialog closes the list first and stops the event (`.stop`), because the dialogs here close on `@keydown.esc.stop`; Frappe also has global Escape and link handlers, so this is checked in a browser, not assumed.
- The picker never re-hydrates from a prop change that carries nothing new (AGENTS.md §6.4 "An editor never re-hydrates").
- Recent picks are kept in `localStorage` under `kt.picker.recent.<session user>.<source>`: ids only, newest first, five at most, written when the reader chooses. The **session user is in the key** so two people sharing a browser do not see each other's picks; a blocked store means no recents, and the page still works. The ids are only a hint sent to the server (§4.2 rule 5).
- The list is drawn inside the field's own wrapper and is allowed to be taller than a short dialog: the dialog body must not clip it (risk 3, §8).

### 4.4 Keeping the list and the command in agreement

Today the list function and the saving command are separate code and can drift (a person is offered, then refused; or hidden, though acceptable). The rule for every provider: **the provider calls the same function the command calls** to decide eligibility, and returns `disabled_reason` from that function's own message. Each source ships one **parity test**: build a small world, ask the provider for rows, and assert that every row without a `disabled_reason` is accepted by the command and every row with one is refused with that same reason. This test is what makes the picker safe to add to a screen whose command is the authority.

### 4.5 Styling

A new section ("Part 8, record picker") of the generated `kt_industry_tokens.css`, from a `PICKER` block in `scripts/industry_design_css.py`: change it there and regenerate, never in the CSS file (AGENTS.md §6.6). Class names: `kt-picker`, `kt-picker-input`, `kt-picker-clear`, `kt-picker-list` (`is-updating`), `kt-picker-group`, `kt-picker-option` (`is-active`, `is-disabled`), `kt-picker-name`, `kt-picker-detail`, `kt-picker-reason`, `kt-picker-foot`, `kt-picker-status`. The existing `.kt-matches` is retired when System setup adopts the picker. Precedent: the pager shipped in the generated sheet before the design pack held it; the same hand-off to the design pack is in §10.

### 4.6 Boards and departures

Screens with a board in the design pack have it enforced structurally (AGENTS.md §6.6, `make ui-structure-gate`). Replacing a `<select>` with a combobox is structure the board does not draw, so each adopting screen registers it in `tests/ui/fidelity/departures/<module>.js` as `Component#variant`, with the reason ("a list that can reach hundreds cannot be a native select") and the authority ("Project Owner, 13 October 2026, §1 of this plan"). A reused component counts as new code for the fidelity gate; the picker is registered once per screen, not once globally.

## 5. Build plan

Ordered so that the first browser evidence comes in Phase 3, not at the end. Tests run on `kentender-test.local` (AGENTS.md §8.2), never on the dev site; run focused tests while building and one containing-module run per phase, not the whole suite after each edit. Each phase ends with its evidence reported as run or not run.

| Phase | Work | Evidence to finish |
|---|---|---|
| **0 Ground** | (a) Read KT-STD-001 v1.29 and the baseline register to decide where the clause and any identifier go. (b) Script the full inventory of person/record choices (every `<select>` in every `.vue`/`.js` under `public/js`, with its option source), replacing §2.3's grep. (c) Confirm the three open decisions in §9. (d) Ask Claude Design for the picker board (§10) so the fidelity gate has a target | Inventory table committed with a disposition per row; register and KT-STD-001 read list recorded |
| **1 Server** | Red first: `kentender_core/tests/test_record_picker.py` for the rules in §4.2 (unknown source masked; actor from session; clamping; row keys filtered; recent ids only reorder; near-then-recent-then-rest ordering; ranking; `total` counts after eligibility; `resolve`). Then `services/record_picker.py`, `api/record_picker.py`, the hook, the `staff_home_unit` near helper. Check whether Frappe's `rate_limit` suits this endpoint | `test_record_picker` green; a measured search over 1,000 users on the test site (a figure to be recorded, not promised) |
| **2 Component** | Red first: `RecordPicker.spec.js` — keyboard (all of §3 item 8), stale-response guard, controlled binding, Esc inside a dialog, disabled rows skipped, live region text, recents key includes the user, blocked storage. Then `RecordPicker.vue`, the bundle, `PICKER` in the generator, regenerate, `RecordPickerHost.vue` copies and the equality spec | Component spec green; `make design-css-check` clean; zero console errors on a bare mount |
| **3 First slice** | Add member dialog: source `bid_opening.committee_member` as a provider over `appointment.candidates` logic; the page payload stops carrying the whole list; register the departure; parity test against `AppointOpeningCommittee` | One focused Playwright journey on the test site (open dialog, type, arrow, Enter, save; and an unavailable row); a live browser check at 1440 px and 390 px; the dialog's Esc behaviour; fixtures purged afterwards |
| **4 People** | Replace member "With"; Evaluation committee and secretary (two purposes, one source or two); System setup assign — User (retire the hand-built list; `search_users` stays as an administrator API until nothing calls it) | Each screen's own spec; one parity test per source |
| **5 Units and records** | Organisation Unit as a source with the path as `detail`; Departmental need unit; Planning purchase unit; Budget line owner unit (in a table row); System setup's unit field, home-unit dialog and unit filter; Meetings department filter; retire `.kt-matches` | Each screen's own spec; a live check of the Budget row case (§8 risk 5) |
| **6 Hold the line** | `kentender_core/tests/test_record_picker_guard.py`: fails when a `.vue` `<select>` is fed by a list named like people, users, members, holders, candidates, units or suppliers and is not on an allowlist with a reason per entry (the allowlist starts with §2.3's "stays a select" rows). Write AGENTS.md §6.12 from §7; propose the KT-STD-001 clause under the document-change protocol | Guard green and red-first demonstrated; AGENTS.md §6.12 merged; clause filed as Proposed |

Phases 4 and 5 can run in either order and split by module.

## 6. Acceptance criteria

New figures are proposals and are marked so.

1. **Search.** With 1,000 enabled staff accounts, typing three letters returns a ranked first page; the browser never receives more than 50 rows in one response. *(Proposed: the answer arrives within 300 ms at that size on the test site; to be measured in Phase 1.)*
2. **Empty state.** For a reader with a recorded department and two recent picks, focus shows Your department, then Recent, then Everyone else, no person twice. For a reader without a department, Recent then Everyone else.
3. **Unavailable.** A person already on the committee is visible, greyed, with the reason, and cannot be chosen by mouse or keyboard.
4. **Authority.** A hand-built request naming an ineligible person is refused by the command with a field error (not a dialog), whether or not the picker offered them.
5. **Race.** Typing "ami" then "amina" with the first answer delayed shows only the second answer.
6. **Dialog.** Esc closes the list, a second Esc closes the dialog; the list is not clipped by the dialog at 1440 px or 390 px.
7. **Assistive technology.** Keyboard-only completion of Add member works; the result count is announced. *(Screen-reader testing with a real assistive technology is a separate manual step, recorded as run or not run.)*
8. **Reuse.** A new source needs one provider, one hook entry and one parity test; no change to core. A new screen needs a bundle entry, a host wrapper and a departure entry; no new CSS.
9. **Guard.** Adding a `<select>` over a people list to any screen fails the guard.
10. **Cleanliness.** `make design-css-check` passes; no test data is left on the dev site.

## 7. Reuse guide (draft of AGENTS.md §6.12, to be finalised in Phase 6)

> ### 6.12 Record picker
>
> Any choice of one person or one record from a list that can grow beyond about a dozen entries uses the shared picker. Never build a dropdown, a typed list or a search box for such a choice, and never send the whole list to the browser.

### 7.1 When to use it

| The choice is… | Use |
|---|---|
| A person, unit, supplier, item, tender or other record from a list that can exceed about 12 | **The picker** |
| A role, status, country or other fixed vocabulary | A plain select |
| One of the few people or records already shown on this screen | A plain select |
| A filter over a table with an "All" row, where the field is a unit or person | The picker with an "All" first row (`allLabel`) |

### 7.2 Add a source (the module that owns the choice)

1. **Write the provider** in the owning module's `services/picker_sources.py`: `provider(*, query, context, actor, limit)` returns rows (§4.2). Apply the actor's permission and organisational scope **inside the provider**. Mark unavailable rows with `disabled_reason` instead of dropping them, when the reader benefits from seeing why.
2. **Reuse the command's eligibility function** for `disabled_reason` (§4.4); do not copy its rules.
3. **Register it:** return it from `sources()` and list `sources` under `kt_record_picker_sources` in the app's `hooks.py`. Key it `<module>.<what is chosen>`.
4. **Choose `match`:** `"core"` for a bounded set (up to about 2,000 rows), `"provider"` plus a database `LIKE`/index for anything larger.
5. **Write the parity test:** every row without a reason is accepted by the command, every row with one is refused with that reason.
6. Add the source to the catalogue (§7.5).

### 7.3 Use it on a screen

1. Add `"kt_industry_record_picker.bundle.js"` to the page controller's `bundles` list and import the same bundle in the module's Vitest setup file. Without it `mountRecordPicker` is undefined and the picker silently draws nothing (the same trap as the pager).
2. Copy `record_picker_shared/` into the app if it is not there (`kentender_core`, `kentender_procurement`, `kentender_budget`, `kentender_strategy` already will be).
3. Use the host wrapper where the `<select>` was:
   ```vue
   <label for="bop-add-member-person">Member</label>
   <RecordPickerHost
     v-model="user"
     input-id="bop-add-member-person"
     source="bid_opening.committee_member"
     :context="{ tender }"
     :value-label="chosenLabel"
     :invalid="!!error"
     @change="(row) => (chosenLabel = row ? row.label : '')" />
   ```
4. **Bind to your own selection** (`v-model` on a ref your handler sets), never to a value read back from a server response (AGENTS.md §6.4: the "dropdown changes by itself" defect).
5. Keep the saved `id` and a label together (or pass nothing and let the picker call `resolve`), so a reopened record shows a name, not an id.
6. Show a failed save as an inline field error beneath the picker (AGENTS.md §6.10).
7. Register the departure for a screen that has a board (§4.6).
8. In the screen's spec, stub `mountRecordPicker`'s fetch with `opts.fetch`; do not call the real endpoint in a component test.

### 7.4 Troubleshooting

| Symptom | Likely cause |
|---|---|
| The picker draws nothing, no error | Bundle missing from the controller's `bundles` list or the Vitest setup |
| Esc closes the dialog while the list is open | The dialog handles Esc without `.stop`, or the picker's handler was bypassed |
| The list is cut off at the bottom of the dialog | A `overflow: hidden` ancestor; give the dialog body `overflow: visible` or let the list open upward |
| A chosen name flips to an id after a reload | `value-label` not passed and `resolve` not allowed for this source |
| A person is offered and then refused on save | The provider and the command use different eligibility code (§4.4); the parity test is missing |
| An old answer overwrites a newer one | A hand-built fetch bypassed the sequence guard; use the shared component |
| A recent pick from another user appears | The recents key lacks the session user |
| Search is slow | A `match: "core"` source has grown past about 2,000 rows; move it to `match: "provider"` with an index |

### 7.5 Source catalogue

Rows marked *planned* do not exist yet; the catalogue is kept in this table until Phase 6 moves it into AGENTS.md.

| Key | Owner | Noun | Match | Status |
|---|---|---|---|---|
| `bid_opening.committee_member` | `kentender_procurement` (Bid opening) | person | core | planned — Phase 3 |
| `bid_opening.replacement_member` | `kentender_procurement` (Bid opening) | person | core | planned — Phase 4 |
| `bid_evaluation.committee_member` | `kentender_procurement` (Evaluation) | person | core | planned — Phase 4 |
| `bid_evaluation.secretary` | `kentender_procurement` (Evaluation) | person | core | planned — Phase 4 |
| `core.responsible_user` | `kentender_core` (System setup; administrators only) | person | provider | planned — Phase 4 |
| `core.organisation_unit` | `kentender_core` | unit | core | planned — Phase 5 |
| `nds.need_unit` | `kentender_procurement` (Departmental needs) | unit | core | planned — Phase 5 |
| `planning.purchase_unit` | `kentender_procurement` (Planning) | unit | core | planned — Phase 5 |
| `budget.line_owner_unit` | `kentender_budget` | unit | core | planned — Phase 5 |

## 8. Risks and traps

1. **Providers drifting from commands** (§4.4): the main reason a picker becomes untrustworthy. The parity test is not optional.
2. **A central people list changing eligibility silently** (§2.2 item 1): the reason eligibility stays with the module.
3. **Dialog clipping and Esc**: the dialogs here are modal with their own Esc handling, and Frappe has global Escape and link handlers; verify in a browser.
4. **Recents and shared browsers**: handled by the session user in the key; the ids are a hint only.
5. **A picker inside a table row (Budget owner unit)**: a row may be narrower than the list and rows below may overlap it. The list must be allowed to overlay, and this case is checked live before Phase 5 is called done.
6. **Home unit is display information**: it orders suggestions and nothing else. If anyone later uses `near` to grant or refuse, that breaks the rule in core's own module and needs the owner.
7. **First paint on a cold cache**: the first browser run after a test-site rebuild is slow (AGENTS.md §8); do not read that as a picker defect.
8. **Departures register**: a screen that ships the picker without its entry fails the structure gate; a stale entry also fails.

## 9. Decisions

### 9.1 Already made by the owner (§1)

1. The empty state orders **Your department, then Recent**.
2. The picker is **general from the start**.

### 9.2 Still open — each with a recommendation

1. **Keep "Everyone else" in the empty state?** Recommendation: yes (§3 item 4). Without it a reader with no department and no recents sees nothing on focus.
2. **Where recents are kept.** Recommendation: the browser, keyed by session user (§4.3). The alternative is a server record per user, which needs a DocType, a migration and a retention rule for a convenience.
3. **What happens to `search_users`.** Recommendation: keep it as the administrator-only API until no screen calls it, then remove it with its tests; its callers move to `core.responsible_user`.
4. **Merge the three `people.py` copies?** Recommendation: not in this change. It is a separate cleanup; the picker needs only that each module's provider is correct.

## 10. Required changes elsewhere (named here, not assumed)

| Where | Change |
|---|---|
| `AGENTS.md` | Add AGENTS.md §6.12 from §7, including the source catalogue; mention the picker in `CLAUDE.md`'s non-negotiable rules the way the pager is, once built |
| KT-STD-001 | A new version with the clause in §3, Proposed until re-approved; made under the document-change protocol, from the then-current version |
| Design pack | Ask Claude Design to add the picker to the core Industry design so the stylesheet can be regenerated from it. Brief: one field with a search icon; the open list with the three headed parts, an unavailable row with its reason line, the "Showing 20 of 143" foot, the empty and error states, the chosen state with Clear, and the narrow layout; class names as in §4.5; no change to tokens or existing component rules |
| Per module | `tests/ui/fidelity/departures/<module>.js` entries (§4.6); each adopting screen's spec |
| Baseline register | Whether this work is registered, and under which identifier, is the owner's decision; none is assigned here |

## 11. Not verified

- KT-STD-001 v1.29 and the baseline register (KT-DOC-CTRL-001) were not read. Where the clause belongs, whether an earlier clause already covers part of this, and whether an identifier is needed are unchecked. The reference to a KT-STD-001 rule about "every staff account" in the Evaluation code comment is quoted from that code comment, not read in the standard.
- AUTH-ADR-001 §4.8 (home unit as display information) is cited only through the docstring of `staff_home_unit.py`, which names v1.12. The baseline register lists AUTH-ADR-001 v1.15 as the latest approved set, so the section may have moved; the clause was not read in either version.
- The call sites in §2.3 were found by grep and not each opened; any `<select>` whose line lacks the searched words is not listed. The "stays a select" decisions are proposals pending Phase 0.
- `appointment.candidates`, `reads.candidates` and `search_users` were read; `people.eligibility`, `people.internal`, `security_duty.committee_blocker` and `member_department.department_of` were **not** read, so what they return for a person with no home unit or no designation is not checked.
- Whether Frappe's own rate limiter fits a typed-search endpoint, and whether `frappe.parse_json` is enough for all argument shapes here, are Phase 1 checks.
- No code, test, stylesheet or browser run supports any figure here. The 300 ms and 2,000-row figures are proposals, not measurements.
- Screen-reader behaviour is untested.

## 12. Approval effect

This plan, v0.1, is approved by the Project Owner (13 October 2026). It authorises Phases 0 to 6 of §5 as written and changes no other approved document. The approval did not answer the four open decisions in §9.2, which remain open until the owner answers them. Approval of this plan is not approval of the KT-STD-001 clause in §3, which becomes a separate Proposed version (§10), and it is not evidence that any phase was built, verified or released.
