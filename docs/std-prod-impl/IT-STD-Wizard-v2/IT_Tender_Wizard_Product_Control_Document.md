# IT Tender Wizard Product Control Document

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Status:** Mandatory control document  
**Design rule:** User-facing simplicity first; legal and technical complexity stays behind the workflow.

---

## 1. Purpose

This document controls all IT Tender Wizard screens, PRDs, Stitch prompts, and Cursor prompts.

No screen specification should be accepted unless it follows this document.

---

## 2. Authoritative User-Facing Lifecycle

Use this lifecycle everywhere:

```text
Approved Procurement Package
→ IT Tender Configuration
→ Configure STD-controlled tender values
→ Validate
→ Review & Approval
→ Final Preview
→ Publication Readiness
→ Tender Management publication workflow
```

### Meaning

| Stage | User-facing meaning |
|---|---|
| Approved Procurement Package | The approved planning/procurement package handed off for tender configuration |
| IT Tender Configuration | The working configuration created from the approved package |
| Configure STD-controlled tender values | The user completes the tender-specific values allowed by the IT Standard Tender Document |
| Validate | The system checks completeness and consistency |
| Review & Approval | Reviewers approve the tender configuration before final rendering |
| Final Preview | The user confirms the generated tender package |
| Publication Readiness | The package is marked ready for Tender Management publication workflow |
| Tender Management publication workflow | Separate downstream publication process |

---

## 3. User-Facing Vocabulary

Use these terms in the default procurement-user UI.

| Use this | Do not use this in default UI |
|---|---|
| Approved Procurement Package | Tender Shell |
| IT Tender Configuration | TenderSTDInstance |
| Standard Tender Document | STD package code |
| Planning Package Ref | Plan item ref, procurement initiation ref |
| Tender Profile | Tender shell metadata |
| Tender Data Sheet | TDS object/schema |
| IT Requirements | Requirement schema rows |
| Implementation Schedule | Schedule model |
| System Inventory | Inventory schema |
| Price Schedule | Commercial price model |
| Evaluation Setup | Evaluation schema |
| Forms & Evidence | Evidence schema/checklist engine |
| Contract Values | SCC parameter object |
| Validation | Rule engine diagnostics |
| Review & Approval | Governance state machine |
| Final Preview | Render output object |
| Publication Readiness | Handoff state |
| Continue / Start / Fix / Review | Ready / Locked |

Forbidden default UI terms:

```text
Tender Shell
TenderSTDInstance
STD binding
STD package code
STD version hash
schema version
rule ID
source anchor
configuration object
render block
clause hash
lifecycle enum
```

These may appear only in admin, audit, or developer diagnostics views.

---

## 4. Screen Sequence

| Step | Screen | User decision |
|---:|---|---|
| 01 | Tender Profile | Is the basic tender identity correct? |
| 02 | Tender Data Sheet | What tender-specific instructions and parameters apply? |
| 03 | IT Requirements | What must bidders supply, deliver, integrate, support, or prove? |
| 04 | Implementation Schedule | How should the solution be delivered? |
| 05 | System Inventory | What bidder-relevant environment or inventory context must be disclosed? |
| 06 | Price Schedule | How should bidders price the tender? |
| 07 | Evaluation Setup | How will bids be evaluated? |
| 08 | Forms & Evidence | What must bidders submit? |
| 09 | Contract Values | What tender-specific contract values and obligations apply? |
| 10 | Validation | Is the configuration complete enough to review? |
| 11 | Review & Approval | Should this configuration be approved for final preview? |
| 12 | Final Preview | Does the generated package match the approved configuration? |
| 13 | Publication Readiness | Is the approved package ready for Tender Management? |

---

## 5. Screen Design Rule

Every screen must answer one user decision only.

A field stays on a screen only if it helps the user make that screen’s decision.

If the answer is “another module might need it later,” remove it from the screen or show it only as a light reference.

---

## 6. Screen Ownership Rule

Each screen owns one primary user task.

| Screen | Owns | May reference lightly | Must not own |
|---|---|---|---|
| Tender Profile | Basic tender identity and setup context | Approved Procurement Package, Standard Tender Document | TDS parameters, requirements, pricing, evaluation |
| Tender Data Sheet | Tender-specific instructions and parameters | Tender Profile | Technical requirements, scoring details, price lines |
| IT Requirements | Requirement statements and bidder response expectations | Evaluation link status, evidence link status | Scores, price lines, contract clauses, actual evaluation |
| Implementation Schedule | Delivery approach, milestones, durations, deliverables, acceptance checkpoints | Related requirements | Project execution, payment certification, inspection results |
| System Inventory | Bidder-relevant environment and inventory context | Price Schedule link status | Full pricing, scoring, contract obligations |
| Price Schedule | Pricing structure, quantities, units, pricing instructions | Inventory and requirements as sources | Technical requirement wording, evaluation scoring |
| Evaluation Setup | Evaluation stages, criteria, weights, pass rules, financial evaluation basis | Requirements, evidence, price schedule | Actual bid evaluation results |
| Forms & Evidence | Bidder submission requirements | TDS, requirements, evaluation criteria | Actual bidder uploads or verification |
| Contract Values | SCC values and carry-forward obligations | Requirements, schedule, price items | Contract administration |
| Validation | Findings and readiness summary | Owning screens | Editing configuration fields |
| Review & Approval | Review decisions and return comments | Validation summary | Configuration editing, publication |
| Final Preview | Preview confirmation | Approved configuration | Editing or fixing content |
| Publication Readiness | Handoff readiness | Final preview and package summary | Publishing the tender |

---

## 7. Status Labels

Use only these step-level status labels in user-facing wizard screens:

| Status | Meaning | Typical action |
|---|---|---|
| Not started | No meaningful work has been done | Start |
| In progress | Work has started but required items remain | Continue |
| Needs attention | Blockers, returned corrections, or important warnings require action | Fix |
| Complete | Required local setup is complete | Review |
| Not available yet | A prior required step is incomplete | View required step |

Do not use `Ready` or `Locked` on step cards.

Reserve “locked” only for real governance/legal immutability after approval, publication, or STD legal control.

---

## 8. Action Labels

Allowed main action labels:

```text
Create IT Tender Configuration
Create Configuration
Start
Continue
Fix
Review
Run Validation
Submit for Review
Open Final Preview
Confirm Final Preview
Mark as Publication Ready
Open in Tender Management
```

Do not use:

```text
Finalize Configuration
Start Configuration
Publish Tender
Tender Shell
Bind STD
Create Tender Shell
```

---

## 9. Entry Modal Rule

The dashboard creation modal must start from the planning handoff.

### Modal title

```text
Create IT Tender Configuration
```

### Helper text

```text
Select the approved procurement package that requires an IT tender configuration. The planning reference, procuring entity, procurement method, and applicable standard tender document will be filled from the package.
```

### Fields

| Field | Behavior |
|---|---|
| Approved Procurement Package | User selects this |
| Planning Package Ref | Read-only after package selection |
| Procuring Entity | Read-only after package selection |
| Procurement Method | Read-only after package selection |
| Standard Tender Document | Read-only unless more than one valid IT STD version is available and the user has selection permission |

### Buttons

```text
Cancel
Create Configuration
```

---

## 10. Data Source Rule

Every displayed value must be one of:

| Source type | UI behavior |
|---|---|
| User-entered | Editable on the owning screen |
| Filled from approved package | Read-only with plain source label where helpful |
| Template-assisted | Editable with Reset to template |
| Derived | Read-only with explanation when exposed |
| Owned by another screen | Read-only with link to owning screen |
| STD-controlled | Read-only with plain legal/source reason |
| Not configured | Show “Not configured” |

Do not display hardcoded realistic values unless they are approved seed fixtures.

---

## 11. Validation Rule

Default screens show calm summaries only:

```text
0 Blockers / 2 Warnings
Needs attention
Complete
```

Detailed rule failures belong in Validation.

Do not show in default screens:

```text
RULE_EVAL_003
clause hash mismatch
render block missing
schema invalid
source anchor
```

---

## 12. Stitch and Cursor Prompt Rule

Every prompt must include exact text. Do not write placeholders such as:

```text
short description
appropriate status
sample label
relevant helper text
```

Instead, provide the exact label, exact description, exact button, exact status meaning, and exact forbidden content.

---

## 13. Acceptance Gate for Every Screen

A screen spec fails if any answer is vague.

| Gate | Pass condition |
|---|---|
| User decision | Exactly one decision is stated |
| User-facing object | Uses procurement-user language |
| Lifecycle | Matches the approved lifecycle |
| Ownership | Owns only one primary task |
| STD grounding | States exact STD section or says not an STD content section |
| Labels | Exact labels are provided |
| Descriptions | Exact descriptions are provided |
| Statuses | Only approved statuses are used |
| Actions | Exact actions and enablement rules are given |
| Forbidden content | Internal/debug/legal complexity is explicitly excluded |
| Cursor readiness | API shape and behavior are precise |
| Stitch readiness | Layout and copy are precise |

---

## 14. Final Rule

The legal model must remain complete, but the procurement-user workflow must remain simple.

If a field makes the screen harder to understand and is not required for the current user decision, remove it from the screen.
