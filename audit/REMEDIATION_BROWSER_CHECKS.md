# Screens that need a real-browser check (agents did not run Playwright)

Merged 07 Oct 2026 from audit/progress/*.md.

## INT-A

None from this gate (Python only).

## INT-B

None.

## REGRESS

None added by this reconciliation (BUD-007 Vue editor half is already recorded).

## WP1.1

- Needs workspace register, a Need's detail page, Save draft (first save and later save), Submit, Accept/Return/Decline from the review screen, withdrawal request/decision, and the "Planning status" panel: the Vue code sends no `user` and only service fields, but a live run after deploy is the only proof the stricter field check does not refuse a field the screen sends. As Planner / AO / HOPF open an Accepted Need that has an author's Draft update: the page should show the accepted requirement, not the draft title.

## WP1.2

None required: no screen calls these functions. Funding Activity ledger labels change for newly created release/convert/adjust events (see follow-up 5) — worth one look at Budget > Funding Activity after the next seed.

## WP1.3

- Desk loads without console 404s after the asset-hook removals (assets for the 5 removed JS/CSS files are no longer referenced; clear cache + hard refresh).
- Procurement Home page (`/desk/kt-procurement-home`): 2-stage pipeline, empty deadlines state, portfolio shows budget figures only.
- Procurement Journeys page (`/desk/plc-procurement-journey`): list cards no longer show "Open Tender".
- IT Tender Configuration dashboard fallback breadcrumb now links to `tenders`.
- Publications / Publication Setup pages (Tender Configurations) as an officer: confirm status actions still work with the new DocPerms and status guard (service paths set the flags; not exercised in a browser).

## WP1.4-1.6

- Supplier workbench (/app/ktsm-supplier-registry or its page): a System Manager/Administrator can still open it (reads) but Approve / Suspend now need the KTSM roles.
- Module landing / working-context pickers (Budget, Needs, Planning) for a seeded user who only has a User Permission row.

## WP2.1

None: no screen writes Audit Event; Home/analytics/evidence timeline only read it.

## WP2.2-4.5

- Strategy plan workspace: save plan details on a first Draft, on a successor Draft (dates only), and with a blank "Use until"; structure editor add/edit/reorder/delete and an Approve on an Active-expired version (the approval page should show the new "applicability ended ... Return it" message through the blockers list).
- Strategy Desk list/form for the five doctypes should now be read-only for Strategy Author and System Manager (after migrate).
- Seed worlds (canonical / Playwright) that build or tear down Strategy data through the changed seed code (works master hierarchy, canonical reset, Playwright fixtures).
- I could not probe over HTTP: the Strategy login in .env.ui was refused on the test server (Invalid login credentials) while the test site was being rebuilt, so the REST bypass is proven in-process with `frappe.client.set_value` and `doc.save` as the Author (tests above), not over the wire.

## WP2.3-3.5-3.6-budget

- Budget version editor (Approval details and Budget lines tabs): click Save changes and try to type while it runs - the controls are disabled until the response; afterwards the typed field keeps the saved value and the Version header shows the new stamp; add a line, save, then save again (second save must succeed with the returned stamp, no duplicate line).
- Editor: a refused line save (empty title, `1e3`, `100.005`) shows the field message and leaves every row as it was on the server.
- Editor: two browser windows on the same Draft - the second save shows the "This budget has changed" notice (the first window's line save now moves the stamp).
- Approval task and Closure screens still send the stamp (unchanged code); a quick approve and close pass on the seeded world.

## WP2.6-2.8

- System setup > Assign responsibility dialog: choosing yourself or Administrator/a System Manager account should show the refusal under the User field and keep the save button disabled (the server preview now returns it as a `user` problem; I did not look at the Vue dialog).
- Desk legacy pages `/app/user-operational-acc/<user>` and `/app/workflow-routing-rul/<name>`: the "Add operational assignment" and "Create revised rule" buttons are removed; the pages still load read-only.

## WP3.1-3.3

- Approval screen: a version resubmitted by a dual-role user shows no Approve action for that user; Approve refused on a Closed Budget now returns code BUDGET_CLOSED (check the screen shows a sensible message, it uses the generic errors.status text).
- Version History tab: the API now returns `attempts`; the Vue tab does not render them yet (no UI change was made).

## WP3.2-4.3

- Requisitions editor, Draft prepared by an Author who has since been made Head of the lead department: "Submit to Procurement" must not be offered to that person; another lead Head still sees it.
- Department approval task: the person who sent or prepared the Version gets no approve action (read-only); the Home My work list omits it.
- Procurement authorisation task: a user who prepared the Version sees no Authorise button.
- Department approval task: if the balance or product eligibility changed after Send, pressing Submit to Procurement should show the blocking-findings message (REQ_BLOCKING_FINDINGS), not a generic error.
- Requirements workbench, Add requirement dialog: the characteristic list should be limited to the item category (server now refuses others with "<characteristic> does not apply to <category> equipment.").
- Tenders: Start tender and Start corrected version still work from the UI (consumption is inside the command; no web endpoint).

## WP3.4-4.1-award

- Award record as HOP and as AO: the Decide award / Decide correction buttons are hidden for an AO who prepared or signed the opinion, and Save/Sign opinion are hidden for a person who recorded a decision.
- Decision refused for unreadable or short funding: confirm the screen shows the funding reason, not the generic status text (follow-up 10).
- A funding-restriction issue: the HOP "Owner correction confirmed" action is refused with a hold message while Budget still shows a shortfall, and clears once Budget confirms.
- Order from a Tenders suspension: "Restriction ended" is refused until the Tenders release event arrives, then works without typed evidence.

## WP3.5-2.4-2.5

- Needs workspace and list as Departmental Author (own Needs only), as Head of User Department (unit subtree) and as Procurement Planner (accepted Needs only; the Planning plan-item evidence link to a Need revision still opens for the Planner).
- Save a Draft Need with quantity 1.5 on Each (refused with the new message) and 1.5 on Programme (accepted); submit.
- Desk forms for Annual Plan, Annual Plan Version, Plan Item and Departmental Plan Entry open read-only for the Planner/Author/HoD (no Save/Delete); the Plan workbench and Departmental plan editor still save.
- Publish a plan end to end (snapshot currency now from the Budget).

## WP3.6-needs-planning

* Needs screens that send commands (save draft, submit, return/accept/decline, withdraw, create update, request and decide withdrawal): the Vue pages already send an idempotency key and the expected version, so no front-end change; a double-clicked Submit and a retry after a dropped response are worth one manual pass on the test site (the second request should return the first result, not an error).
* Planning: the departmental plan and plan-version screens (start plan, save requirement, submit, accept/return, funding confirmation, adoption, approval): same double-click and retry check; a user whose responsibility was revoked mid-session should see "not found" on a retry, not the old result.

## WP3.6-req-tenders

* Requisitions editor: a double-clicked Save or Send for approval (two requests, one key) should show one result and no error; a Save after another tab saved should show the stale-version message (`REQ_STALE_VERSION`), not a generic "document has been modified" error.
* Tenders: a double-clicked Start tender (same key) should open the one Tender; a Save of the draft after another tab saved should show the stale-version message (`TND_STALE_VERSION`).
* Retry after a refused Tender draft save (validation errors returned as data): the corrected Save with the same key must go through.

## WP3.6-residual

* Strategy screens that call the commands (plan details save, structure save, submit, discard, successor, return, approve): the Vue pages already send an idempotency key and the expected version on every call (`strategyApi.js`, `runAttempt`), so no front-end change was needed, but a retry after an unknown outcome and a double-clicked Approve are worth one manual pass on the test site.

## WP4.2-eval

- Report summary and Financial comparison screens when funding is `Unavailable`: "Available funding" and "Shortfall" amounts render blank (the `money` helper returns "" for null) beside the qualification text "Funding could not be confirmed: ...". JS was not changed; consider showing "Not confirmed".
- A bid whose only unresolved requirements are qualified: comparison table still shows "Needs review"/"Not ranked" for that bid with the report outcome "Qualified report" (Send for signing now enabled).
- Price requirement with a discrepancy: the member "Record finding" form now returns a field error on `result`; confirm the message renders under the result control.
- Bid Opening committee form: an Evaluation member chosen as Independent member shows "Appointed to evaluate this Tender." beside the person.

## WP4.4-tenders

- Addendum screen (Tenders): choosing the "Invitation - clarification deadline" row (revised value typed as a date; invalid or later-than-submission text should show the field error), and the "Submission - submission deadline" row (the revised-deadline field must appear once the row is chosen and saved; the revised value then shows as a date label).
- Addendum awaiting channel confirmation on a Tender whose deadline has passed: the Confirm control should be absent and a late confirm via the API shows the "submission period has ended" refusal.
- Conflicting channel confirmation in the browser: the refusal inline state still shows, and the History tab now lists "ConfirmationConflictRejected" after a reload.
- StartTender double-click / second tab on one handoff: the second session lands on the first Tender, not an error.

## WP4.6-planning-needs

- As the Head of User Department, accept a Submitted Need whose unit was disabled after submission: the Review screen should show the unit-unavailable message and leave the task open; return still works.
- Planner opening a departmental plan Draft: Need-origin entries show their quantity as before (the quantity now travels as a string internally).
