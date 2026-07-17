**IT Tender Wizard Screen Ownership Matrix**

**Global rule**

Each screen owns one primary configuration object.

A screen may display related data only as a source-backed reference.

If the user can edit a field, that screen owns the field.

If another screen owns the field, show it as read-only with:

\- source label

\- owning screen

\- edit link to owning screen

No unexplained system-generated or template values may appear.

**1\. Tender Profile**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Tender profile configuration |
| Primary STD anchor | Tender identity/TDS opening data |
| Owns | Tender display title, scope summary, lot structure, procurement method display, basic participation settings |
| Editable here | Tender title/summary where permitted, lot configuration, participation settings |
| Read-only references | Planning Package Ref, Tender Ref, Procuring Entity, bound STD package |
| Must not own | TDS detailed values, requirements, pricing, evaluation, contract terms |

**2\. Tender Data Sheet**

| **Area** | **Rule** |
| --- | --- |
| Primary object | TDS configuration |
| Primary STD anchor | Tender Data Sheet |
| Owns | Tender-specific TDS values |
| Editable here | deadlines, clarification rules, tender security applicability, submission rules, contact points, currency, language, margin of preference applicability where allowed |
| Read-only references | Tender Ref, Procuring Entity, procurement method |
| Must not own | Technical requirements, price line items, evaluation scoring, SCC obligations |

**Important:** TDS may enable a rule, but downstream screens own the detailed configuration.

Example:

Margin of preference applies: Yes/No

belongs in TDS / Evaluation Setup, not IT Requirements.

**3\. IT Requirements**

| **Area** | **Rule** |
| --- | --- |
| Primary object | IT requirement item |
| Primary STD anchor | Section V / VI — Requirements and Technical Requirements |
| Owns | Requirement title, description, category, treatment, bidder response format, evidence instruction, acceptance criteria |
| Editable here | requirement text, category, mandatory/evaluation-linked/informational treatment, bidder response expectation, evidence instruction, acceptance criteria |
| Read-only references | Linked evaluation criterion, linked forms/evidence item, carry-forward status |
| Must not own | scoring marks, pass marks, evaluation results, price quantities, contract clauses |

**Allowed reference only:**

Linked to Evaluation: Yes

Edit in Evaluation Setup

**Not allowed here:**

Scored 15%

Evidence Set

Acceptance Set

Evaluation score

Bidder compliance

**4\. Implementation Schedule**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Implementation phase / delivery milestone |
| Primary STD anchor | Section VII — Implementation Schedule |
| Owns | delivery approach, phases, milestones, duration, start trigger, deliverables, acceptance checkpoint, evidence required |
| Editable here | phase name, sequence, expected duration, start trigger, deliverables, acceptance criteria, evidence required, carry-forward default |
| Read-only references | related IT requirements, related contract carry-forward state |
| Must not own | live project execution, inspection records, payment certification, actual completion status |

**Template values are prefilled, not locked.**

Correct field behavior:

Expected Duration: 3 months

Source: Standard IT Schedule Template

\[Edit\] \[Reset to Template\]

Not:

Expected Duration: 3 months

read-only with no explanation

**5\. System Inventory**

| **Area** | **Rule** |
| --- | --- |
| Primary object | System inventory / bidder-context item |
| Primary STD anchor | Section VIII — System Inventory Tables; Section IX only for background context |
| Owns | inventory item, category, scope, required action, bidder consideration, site/location reference, technical context |
| Editable here | inventory item details, bidder-facing context, scope, required action, quantity/context where inventory-owned, disclosure classification |
| Read-only references | price schedule link status, related requirement, related implementation phase |
| Must not own | full pricing structure, evaluated price inclusion, scoring, contract obligations |

**System Inventory is not a price schedule.**

It may show:

Price Schedule Link: Required

But pricing details belong in Price Schedule.

For summary blocks, every value must be source-backed:

Primary HQ: 2,500 users

Source: User & Location Scope inventory item

\[Edit\]

If no source exists:

Primary HQ: Not configured

No magical values.

**6\. Price Schedule**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Price schedule item |
| Primary STD anchor | Price Schedule forms; linked to System Inventory Tables |
| Owns | pricing basis, quantity/unit, currency, tax treatment, mandatory/optional price item, evaluated-price inclusion |
| Editable here | price line items, pricing basis, quantity, duration, unit, bidder pricing instruction, evaluated-price inclusion |
| Read-only references | source inventory item, source requirement, source implementation phase |
| Must not own | technical requirement wording, inventory context, evaluation scoring |

Correct relationship:

System Inventory says what exists / what is needed.

Price Schedule says how bidders price it.

**7\. Evaluation Setup**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Evaluation criterion |
| Primary STD anchor | Section III — Evaluation and Qualification Criteria |
| Owns | evaluation stages, mandatory checks, scored criteria, weights, pass marks, financial evaluation basis |
| Editable here | criterion name, type, score/weight, pass rule, linked requirement, evidence needed for evaluation |
| Read-only references | IT Requirements, Price Schedule items, Forms & Evidence items |
| Must not own | requirement text, bidder submissions, actual evaluation results, award recommendation |

Only this screen owns:

15 marks

85/100

Technical pass mark

Financial evaluation method

**8\. Forms & Evidence**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Bidder submission requirement |
| Primary STD anchor | Section IV — Tendering Forms; references to TDS, requirements, evaluation |
| Owns | required forms, certificates, declarations, evidence submission instructions |
| Editable here | submission item, mandatory/conditional/optional rule, bidder instruction, accepted format, linked requirement/criterion |
| Read-only references | IT Requirement, Evaluation Criterion, TDS source |
| Must not own | actual bidder uploads, document verification, evaluation scores |

**9\. SCC / Contract Carry-Forward**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Contract carry-forward item / SCC parameter |
| Primary STD anchor | SCC and contract schedules |
| Owns | SCC values, carry-forward decisions, contract obligation text, contract location, acceptance/verification method |
| Editable here | SCC parameter values, carry-forward yes/no/conditional, obligation wording, contract location, acceptance method |
| Read-only references | source requirement, source implementation phase, source price item |
| Must not own | contract signing, post-award administration, payment certification, inspection results |

This screen converts approved tender configuration into contract-facing obligations.

**10\. Validation Report**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Validation finding |
| Primary STD anchor | Cross-screen rules |
| Owns | validation findings only |
| Editable here | nothing except running validation or accepting warnings where policy allows |
| Read-only references | all owning screens |
| Must not own | fixing configuration fields |

Validation should deep-link to the owning screen.

**11\. Review & Approval**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Review workflow decision |
| Primary STD anchor | Governance workflow, not an STD content section |
| Owns | review stages, reviewer decisions, comments, return requests |
| Editable here | reviewer decision, comment, return reason, clarification request |
| Read-only references | validation status, configuration summary |
| Must not own | configuration editing, publication, award, contract signing |

Review approves the **Tender STD Configuration**, not the tender publication.

**12\. Final Tender Preview**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Rendered tender package preview |
| Primary STD anchor | Generated output from approved configuration |
| Owns | preview confirmation only |
| Editable here | confirmation checklist only |
| Read-only references | rendered tender document, approved configuration summary |
| Must not own | fixing render blockers, editing content, publication |

If serious issue appears here:

Return for Correction

not “fix here.”

**13\. Publication Readiness**

| **Area** | **Rule** |
| --- | --- |
| Primary object | Publication-readiness handoff |
| Primary STD anchor | Wizard-to-Tender-Management handoff |
| Owns | readiness confirmation and handoff package |
| Editable here | readiness confirmation only, possibly publication metadata if explicitly owned by Tender Management |
| Read-only references | validation, review approval, final preview, package contents |
| Must not own | actual publication, bidder notification, opening bid submission |

Final action:

Mark as Publication Ready

Not:

Publish Tender

**Refactor rule for all screens**

Every visible field must be classified as one of these:

| **Field type** | **UI behavior** |
| --- | --- |
| User-entered | Editable |
| Template-prefilled | Editable with “Reset to template” |
| Derived | Read-only with formula/source explanation |
| Owned elsewhere | Read-only with “Edit in \[owning screen\]” |
| STD-locked | Read-only with legal/source explanation |
| Not configured | Show “Not configured”, not fake values |

**Immediate fixes for confusing screens**

**IT Requirements**

Remove:

Scored (15%)

Evidence Set

Acceptance Set

Replace with:

Treatment: Mandatory / Evaluation-linked / Informational

Bidder Evidence: Required / Optional / Not Required / Missing Instruction

Acceptance Criteria: Defined / Missing / Not Applicable

Linked to Evaluation: Yes / No

Scoring stays in **Evaluation Setup**.

**Implementation Schedule**

Template values must be editable.

Use:

Expected Duration

3 months

Source: Standard IT Schedule Template

\[Edit\] \[Reset to Template\]

Single Turnkey Delivery must replace the phase table with one delivery milestone.

**System Inventory**

Remove magical summary blocks unless source-backed.

Every summary value must show:

Value

Source

Edit / View Source

Disclosure status

Example:

42 locations

Source: User & Location Scope inventory record

\[Edit\]

If no record exists:

Not configured

**Cursor prompt to enforce this refactor**

Refactor the IT Tender Configuration Wizard to enforce strict screen ownership.

Problem:

The current wizard is becoming confusing because screens show values from many places without clear ownership. Some values appear magical, read-only, hardcoded, or configured in the wrong screen.

Implement a screen ownership contract across the wizard.

Global rules:

1\. Each screen owns one primary configuration object.

2\. A screen may display related data only as a source-backed reference.

3\. If a field is editable, the current screen owns it.

4\. If another screen owns the field, show it as read-only with:

\- source label

\- owning screen

\- edit link to owning screen

5\. Template-prefilled values must be editable unless explicitly locked by STD rule.

6\. Do not show hardcoded or magical values.

7\. If a value has no configured source, show “Not configured”.

8\. Do not expose technical metadata in main user screens.

Field source types:

\- User-entered

\- Template-prefilled

\- Derived

\- Owned elsewhere

\- STD-locked

\- Not configured

Required behavior:

For every displayed field, show or internally model:

\- field value

\- source type

\- source object

\- owner screen

\- editability

\- reason if read-only

Screen ownership:

Tender Profile owns tender profile basics.

Tender Data Sheet owns TDS values.

IT Requirements owns requirement definitions, bidder response expectations, bidder evidence instructions, and acceptance criteria.

Implementation Schedule owns phases, milestones, duration, start trigger, deliverables, acceptance checkpoints, and evidence required.

System Inventory owns inventory items, bidder context, scope, required action, and disclosure-safe technical context.

Price Schedule owns commercial pricing structure, pricing basis, quantities, units, tax treatment, and evaluated-price inclusion.

Evaluation Setup owns criteria, scoring, pass marks, and financial evaluation basis.

Forms & Evidence owns bidder submission requirements.

SCC / Contract Carry-Forward owns SCC values and contract obligation carry-forward.

Validation Report owns validation findings only.

Review & Approval owns review workflow decisions only.

Final Tender Preview owns preview confirmation only.

Publication Readiness owns publication-readiness handoff only.

Specific refactors:

IT Requirements:

\- Remove “Scored (15%)” from requirement type.

\- Replace with Treatment: Mandatory, Evaluation-linked, Informational.

\- Remove “Evidence Set”; replace with Bidder Evidence: Required, Optional, Not Required, Missing Instruction.

\- Remove “Acceptance Set”; replace with Acceptance Criteria: Defined, Missing, Not Applicable.

\- Evaluation scores and marks must only appear in Evaluation Setup.

\- Use a row-triggered drawer, not an always-open middle editor.

Implementation Schedule:

\- Expected Duration, Start Trigger, Deliverables, Acceptance Criteria, Evidence Required must be editable unless explicitly locked.

\- Template values should show Source: Standard IT Schedule Template with Edit and Reset to Template.

\- Selecting Single Turnkey Delivery must hide phase table and show one delivery milestone configuration.

\- Switching from phased to single delivery must show confirmation and preserve previous phase data as draft history.

System Inventory:

\- Remove hardcoded bidder-context and security summary values.

\- Every summary value must be derived from a configured inventory/context record or show Not configured.

\- System Inventory may show Price Schedule Link as a light reference only.

\- Do not move full pricing fields into System Inventory.

\- Add source and edit links for user/location/security context values.

\- Sensitive context must show disclosure warning.

Price Schedule:

\- Own price class, pricing basis, quantity/unit, mandatory/optional, tax treatment, currency, evaluated-price inclusion.

\- Reference inventory and requirements only as sources.

Evaluation Setup:

\- Own all score percentages, marks, pass marks, and financial evaluation rules.

\- Do not let other screens edit scoring.

SCC / Contract Carry-Forward:

\- Own contract obligation text, SCC values, carry-forward decisions, contract location, acceptance/verification method.

\- Use references to requirements, schedule, inventory, and price items.

Final Tender Preview:

\- Do not show blockers as normal work items.

\- It is read-only and confirms the approved rendered package.

\- Serious issues require Return for Correction.

Publication Readiness:

\- Do not publish tender.

\- Mark as Publication Ready hands package to Tender Management.

Expected result:

The wizard should feel controlled and predictable.

Users should always understand:

\- what they are configuring

\- where a value came from

\- whether they can edit it

\- why it is read-only

\- which screen owns the field

This ownership matrix is the correction layer the PRD was missing. It should now govern all remaining UI and backend implementation.

**Implementation tracking:** [`98 IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md`](98%20IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md) and [`Screen_Ownership_Implementation_Tracker.md`](Screen_Ownership_Implementation_Tracker.md).