# IT Tender Wizard Screen Decision and Ownership Matrix

## 1. Purpose

This matrix prevents screen sprawl. Each screen gets one user decision, one owned object, and strict limits on what it may reference.

This matrix applies to **all IT Tender Wizard screens**.

## 2. Global Rule

```text
If a field is editable on a screen, that screen owns it.
If another screen owns it, show a read-only reference with source and edit link.
If no source exists, show Not configured.
```

## 3. Matrix

| Screen | Single User Decision | Owns | Editable Here | May Reference Lightly | Must Not Show/Own |
|---|---|---|---|---|---|
| Dashboard | Which tender configuration do I open or create? | Configuration list state | Filters, create/open action | Tender Ref, status, validation summary | detailed STD data, configuration forms |
| Configuration Overview | Where am I in this configuration? | Wizard progress summary | navigation only | step status, blockers summary | detailed editing, legal/audit metadata |
| Tender Profile | What tender am I configuring? | Tender profile | title/summary where allowed, lot setup, basic participation settings | Planning Package Ref, Tender Ref, PE, STD package | TDS details, requirements, pricing, evaluation, SCC |
| Tender Data Sheet | What tender-specific instructions apply? | TDS values | deadlines, submission rules, currency, language, security applicability, preference applicability | tender profile, procurement method, STD constraints | technical requirements, price lines, scoring, SCC obligations |
| IT Requirements | What must bidders supply or satisfy? | IT requirement items | requirement text, category, treatment, bidder response, evidence instruction, acceptance criteria | evaluation link status, forms link status, carry-forward status | marks, percentages, bidder scores, price quantities, contract clauses |
| Implementation Schedule | How will delivery happen? | phases or single delivery milestone | approach, duration, trigger, deliverables, acceptance, evidence | related requirements, carry-forward status | live project execution, payment certification, inspection records |
| System Inventory | What environment or inventory must bidders account for? | inventory/context items | item, scope, action, bidder consideration, location/site context, disclosure status | requirement link, phase link, price link status | full pricing, evaluated-price inclusion, scoring, contract obligations |
| Price Schedule | How should bidders price the tender? | price schedule items | pricing basis, quantity/unit, duration, currency, tax, mandatory/optional, evaluated-price inclusion | source requirement, source inventory item, source phase | requirement wording, inventory editing, scoring |
| Evaluation Setup | How will bids be evaluated? | criteria and scoring framework | stages, mandatory checks, weights, marks, pass rules, financial method | linked requirements, price items, evidence items | requirement authoring, bidder submissions, actual evaluation results |
| Forms & Evidence | What must bidders submit? | submission requirements | form/evidence item, mandatory/conditional/optional rule, instruction, accepted format | TDS, requirement, evaluation source links | bidder uploads, verification decisions, scores |
| SCC / Carry-Forward | What becomes contract-facing? | SCC values and carry-forward items | SCC values, carry-forward decision, obligation wording, contract location, acceptance method | source requirement, phase, price item, form | contract administration, payments, inspections, signing |
| Validation Report | Is the configuration complete and consistent? | validation findings | run validation; accept warning where allowed | deep links to owning screens | editing configuration fields |
| Review & Approval | Has the configuration been approved for rendering? | review decisions | approve, return, comment, request correction | validation and configuration summary | editing, publication, award, contract signing |
| Final Tender Preview | Does the approved rendered package look correct? | preview confirmation | confirmation checklist | approved configuration, rendered output | fixing blockers, editing content, publication |
| Publication Readiness | Is the package ready for Tender Management? | readiness handoff | readiness confirmation, handoff action | validation, review, preview, package contents | actual publication, bidder notification, bid opening |

## 4. Immediate Refactor Priority

All screens will be refactored, but the first pass starts with the screens already showing complexity risk:

1. IT Requirements
2. Implementation Schedule
3. System Inventory
4. Price Schedule
5. Evaluation Setup
6. SCC / Contract Carry-Forward

Then complete the remaining screens in sequence.

## 5. Screen Test

A screen fails if it:

- shows unexplained values;
- locks editable tender-specific values;
- embeds another screen's workspace;
- exposes scoring outside Evaluation Setup;
- exposes pricing outside Price Schedule;
- exposes contract administration inside SCC configuration;
- shows audit/legal-engine metadata in the default view;
- needs explanation before a normal procurement user knows what to do.

## 6. Simplification Bias

When uncertain, remove the field from the main screen.

If still useful, move it to a drawer.

If mainly legal/audit/technical, move it to audit/details.

