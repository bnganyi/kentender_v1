# Tender Configurations — CFG-07 Evaluation Setup v6

**Project:** KenTender e-Procurement System  
**Module:** Tender Configurations  
**Configuration family:** Information Technology STD  
**Screen ID:** CFG-07  
**Screen name:** Evaluation Setup  
**Status:** Revised v6 specification  
**Design rule:** Simple, user-facing, STD-grounded, implementation-ready  

---

## 1. Canonical Position

| Item | Value |
|---|---|
| User-facing area | Tender Management → Tender Configurations |
| Parent surface | UI-01 — Tender Configuration Home |
| Configuration step | CFG-07 |
| Comes after | CFG-06 — Price Schedule |
| Comes before | CFG-08 — Forms & Evidence |
| Lifecycle stage | Configuration |
| Primary object | Tender evaluation setup |
| User-facing object | Evaluation Setup |
| STD family | Information Technology |
| Primary STD anchor | Section III — Evaluation and Qualification Criteria; informed by Section II TDS, Section IV forms, IT Requirements, and Price Schedule |
| Workflow gate? | No. This is a configuration step. |

---

## 2. User Goal

Allow the procurement user to define **how bids for this IT tender will be checked, scored, and financially compared**.

---

## 3. Single User Decision

> How will submitted bids be evaluated?

Everything on this screen must support that decision.

---

## 4. Screen Ownership

| Area | Rule |
|---|---|
| This screen owns | Evaluation stages, criteria, pass/fail checks, qualification criteria, technical scoring, pass marks, financial evaluation basis, preference/reservation treatment, and evaluator guidance |
| This screen references | Tender Data Sheet, IT Requirements, Price Schedule, Forms & Evidence, Contract Values where relevant |
| This screen does not own | Requirement wording, price items, bidder submission forms, actual bidder responses, actual evaluation results, award recommendation, contract obligations |
| Editable here | Evaluation criteria, scoring/rules, pass marks, financial evaluation basis, preference/reservation settings, bidder-facing criterion wording, evaluator guidance |
| Read-only here | Source requirement, source TDS value, source price item, source form/evidence item |
| Must not show | Bidder scores, bidder rankings, evaluation committee decisions, award recommendation, contract award approval, hidden criteria, internal rule IDs, hashes, schema names |

---

## 5. STD Grounding

The IT STD requires evaluation and qualification criteria to be stated in the tender document before publication. This screen configures those bidder-facing criteria for the tender.

The screen must support these evaluation areas:

1. **Preliminary Responsiveness** — mandatory checks such as required forms, tender security, eligibility declarations, and administrative completeness.
2. **Qualification Criteria** — bidder capacity, experience, financial capacity, personnel, authorization, and similar qualification requirements where applicable.
3. **Technical Evaluation** — scored or pass/fail assessment of IT requirements, technical approach, implementation approach, support, warranty, security, and compliance.
4. **Financial Evaluation** — how priced submissions are compared, using the configured Price Schedule.
5. **Preferences / Reservations** — margin of preference or reservation treatment where permitted and configured in the TDS.

This screen does not conduct the actual evaluation of submitted bids. It only defines the evaluation framework that bidders will see and evaluators will later apply.

---

## 6. Downstream Impact

This screen feeds:

| Downstream area | How it uses this screen |
|---|---|
| Forms & Evidence | Determines evidence and forms bidders must submit for evaluation |
| Contract Values | May identify commitments that must carry into contract obligations after award |
| Tender Preview | Renders evaluation and qualification criteria in the tender document |
| Readiness Check | Verifies criteria, marks, pass rules, and financial evaluation basis are complete |
| Review & Approval workflow gate | Reviewers check that the evaluation framework is disclosed, lawful, and internally consistent |

This screen must not evaluate bids or create an award recommendation.

---

## 7. Layout

### 7.1 Page Header

Title:

```text
Evaluation Setup
```

Subtitle:

```text
Define how bids will be evaluated.
```

Primary actions:

```text
Add Criterion
Import Suggested Criteria
Run Check
```

Footer actions:

```text
Save Evaluation Setup
Continue to Forms & Evidence
```

`Continue to Forms & Evidence` is disabled while blocker issues remain.

---

### 7.2 Context Strip

Show only:

| Field | Example |
|---|---|
| Procurement Package Ref | PP-ICT-2024-009 |
| Tender Title | Data Center Hardware Refresh |
| Procuring Entity | National Treasury |
| Procurement Method | Open National Tender |
| STD Family | Information Technology |
| Standard Tender Document | IT Standard Tender Document — April 2022 |
| Wizard State | In Progress |
| Issues | 1 Blocker / 3 Warnings |

Do not show internal IDs, hashes, schema versions, binding IDs, rule IDs, or source anchors.

---

### 7.3 Section Tabs

Use these tabs:

```text
All Criteria
Preliminary Checks
Qualification
Technical Evaluation
Financial Evaluation
Preferences & Reservations
Needs Attention
```

Tab meanings:

| Tab | Meaning |
|---|---|
| All Criteria | Every configured evaluation criterion |
| Preliminary Checks | Mandatory administrative and responsiveness checks |
| Qualification | Bidder capacity, experience, authorization, personnel, and financial capability checks |
| Technical Evaluation | Technical pass/fail or scored criteria linked to requirements and implementation approach |
| Financial Evaluation | Financial comparison method and evaluated price basis |
| Preferences & Reservations | Margin of preference, reserved procurement, or applicable preference treatment |
| Needs Attention | Criteria missing required rule, marks, pass rule, source, bidder-facing wording, or evidence link |

---

## 8. Main Table

Use this exact table structure:

| Column | Purpose |
|---|---|
| Criterion ID | Short generated identifier, e.g. `EVAL-001` |
| Criterion | User-facing criterion name |
| Stage | Preliminary / Qualification / Technical / Financial / Preference |
| Evaluation Basis | Pass/Fail / Scored / Lowest evaluated price / Preference rule / Post-qualification |
| Source / Link | TDS / IT Requirement / Price Schedule / Forms & Evidence / User added / Standard IT STD |
| Marks / Rule | Marks, pass rule, or comparison rule |
| Bidder Evidence | Required / Not required / To be configured in Forms & Evidence |
| Status | Complete / Needs attention |
| Action | Edit / Fix / Review |

### Sample rows

| Criterion ID | Criterion | Stage | Evaluation Basis | Source / Link | Marks / Rule | Bidder Evidence | Status | Action |
|---|---|---|---|---|---|---|---|---|
| EVAL-001 | Tender security submitted | Preliminary | Pass/Fail | TDS | Must be submitted in required form and amount | Required | Complete | Review |
| EVAL-002 | Manufacturer authorization for supplied servers | Qualification | Pass/Fail | Forms & Evidence | Required where bidder is not the manufacturer | Required | Complete | Edit |
| EVAL-003 | Compute node technical compliance | Technical | Scored | IT Requirement | 20 marks | Required | Complete | Edit |
| EVAL-004 | Implementation approach and delivery plan | Technical | Scored | Implementation Schedule | 15 marks | Required | Complete | Edit |
| EVAL-005 | Support and warranty capability | Technical | Scored | IT Requirement | 10 marks | Required | Complete | Edit |
| EVAL-006 | Financial comparison | Financial | Lowest evaluated price | Price Schedule | Compare evaluated price including required recurrent costs | Not required | Complete | Review |
| EVAL-007 | Margin of preference | Preference | Preference rule | TDS | Not applicable unless TDS states it applies | To be configured in Forms & Evidence if applicable | Complete | Review |
| EVAL-008 | Data migration experience | Qualification | Pass/Fail | User added | Minimum two similar assignments required | Required | Needs attention | Fix |

---

## 9. Required Status Labels

Use only:

| Status | Meaning |
|---|---|
| Complete | Required evaluation setup for this criterion is sufficiently defined |
| Needs attention | One or more required evaluation details are missing or inconsistent |

Do not use:

```text
Valid
Invalid
Ready
Locked
Passed
Failed
```

---

## 10. Evaluation Stage Definitions

| Stage | Exact description |
|---|---|
| Preliminary | Mandatory responsiveness checks applied before detailed evaluation. |
| Qualification | Checks that the bidder has required eligibility, capacity, experience, authorization, personnel, or financial capability. |
| Technical | Assessment of the proposed IT solution, technical requirements, implementation approach, support, security, or compliance. |
| Financial | Evaluation of the bidder's price submission using the configured Price Schedule. |
| Preference | Preference, reservation, or margin-of-preference treatment where permitted and configured. |

---

## 11. Evaluation Basis Options

Use only these labels unless a family-specific rule adds more:

```text
Pass/Fail
Scored
Lowest evaluated price
Preference rule
Post-qualification
```

---

## 12. Criterion Drawer

Open when the user selects `Add Criterion`, `Edit`, or `Fix`.

### Drawer title

For new criterion:

```text
Add Evaluation Criterion
```

For existing criterion:

```text
Edit Evaluation Criterion
```

### Drawer sections and exact fields

#### A. Criterion

| Field | Control | Required | Notes |
|---|---|---:|---|
| Criterion Name | Text input | Yes | Example: `Compute node technical compliance` |
| Stage | Select | Yes | Preliminary / Qualification / Technical / Financial / Preference |
| Evaluation Basis | Select | Yes | Pass/Fail / Scored / Lowest evaluated price / Preference rule / Post-qualification |
| Source / Link | Select or read-only link | Yes | TDS / IT Requirement / Price Schedule / Forms & Evidence / User added / Standard IT STD |
| Bidder-facing Wording | Text area | Yes | Exact wording that will appear in the tender document |

#### B. Rule or Score

| Field | Control | Required | Notes |
|---|---|---:|---|
| Pass/Fail Rule | Text area | Conditional | Required for pass/fail criteria |
| Marks | Number | Conditional | Required for scored criteria |
| Technical Pass Mark | Number | Conditional | Required if the tender uses scored technical evaluation |
| Financial Evaluation Rule | Text area | Conditional | Required for financial criteria |
| Preference Rule | Text area | Conditional | Required where a preference/reservation applies |

#### C. Evidence

| Field | Control | Required | Notes |
|---|---|---:|---|
| Bidder Evidence Requirement | Select | Yes | Required / Not required / To be configured in Forms & Evidence |
| Evidence Instruction | Text area | Conditional | Required when evidence is Required |
| Related Form or Evidence Item | Read-only or link | Optional | Configured in CFG-08 Forms & Evidence |

#### D. Evaluator Guidance

| Field | Control | Required | Notes |
|---|---|---:|---|
| Evaluator Guidance | Text area | Optional | May explain how to apply disclosed criteria only |
| Disclosure Check | Read-only | Yes | Shows whether the bidder-facing wording is complete |

Evaluator guidance must not introduce hidden criteria that are not disclosed to bidders.

#### E. References

Display only as references:

| Reference | Display rule |
|---|---|
| Related TDS Value | Show label and `View TDS` link |
| Related Requirement | Show title and `View requirement` link |
| Related Price Item | Show title and `View price schedule` link |
| Related Form / Evidence Item | Show title and `View forms & evidence` link |

Do not allow editing of TDS, requirements, price items, or forms inside this drawer.

---

## 13. Scoring Summary

If the tender uses scored technical evaluation, show a compact scoring summary above the table:

| Field | Example |
|---|---|
| Technical marks total | 100 |
| Technical pass mark | 75 |
| Configured scored marks | 85 / 100 |
| Status | Needs attention |

If the tender uses only pass/fail technical evaluation, hide the marks summary and show:

```text
Technical evaluation is configured as pass/fail.
```

Do not show bidder scores or evaluation outcomes.

---

## 14. Preferences & Reservations

The screen must support preference and reservation settings without turning them into IT Requirements.

Use this simple display:

| Field | Example |
|---|---|
| Margin of preference | Not applicable |
| Reserved procurement | Not applicable |
| Source | TDS |
| Evidence required | No |
| Status | Complete |

If preference applies, show the required evidence as a link to Forms & Evidence. Do not calculate bidder-specific preference adjustments here.

---

## 15. Empty State

If no criteria exist, show:

```text
No evaluation criteria have been configured yet.

Add the checks, qualification criteria, technical criteria, and financial evaluation basis that bidders will be evaluated against.
```

Primary button:

```text
Add Criterion
```

Secondary button:

```text
Import Suggested Criteria
```

---

## 16. Import Behavior

`Import Suggested Criteria` may import suggestions from:

| Source | Behavior |
|---|---|
| Tender Data Sheet | Suggest tender security, margin of preference, reservation, and method-specific checks |
| IT Requirements | Suggest technical pass/fail or scored criteria linked to requirements |
| Implementation Schedule | Suggest delivery approach or implementation methodology criteria |
| Price Schedule | Suggest financial evaluation basis and evaluated price components |
| Standard IT STD template | Suggest standard preliminary, qualification, technical, and financial criteria |

Imported criteria are draft suggestions. The user must confirm stage, evaluation basis, rule/marks, bidder-facing wording, and evidence requirement before the criterion is complete.

---

## 17. Validation Rules

### Blockers

| Rule | Message |
|---|---|
| Missing criterion name | Add a criterion name. |
| Missing stage | Select the evaluation stage. |
| Missing evaluation basis | Select how this criterion will be evaluated. |
| Missing source/link | Select the source or mark the criterion as user added. |
| Missing bidder-facing wording | Add the wording bidders will see. |
| Pass/fail criterion without rule | Add the pass/fail rule. |
| Scored criterion without marks | Enter the marks for this scored criterion. |
| Technical scoring total incomplete | Complete the technical scoring allocation. |
| Technical scoring pass mark missing | Enter the technical pass mark. |
| Financial evaluation method missing | Define how evaluated prices will be compared. |
| Preference applies without rule | Add the preference or reservation rule. |
| Evidence required without instruction | Add the evidence instruction or link it to Forms & Evidence. |

### Warnings

| Rule | Message |
|---|---|
| User-added criterion has no source explanation | Confirm why this criterion is needed. |
| Requirement has no evaluation treatment | Review whether this requirement needs evaluation linkage. |
| Price item excluded from financial evaluation | Confirm this exclusion is intentional. |
| Evaluator guidance may exceed bidder-facing wording | Confirm evaluator guidance does not introduce hidden criteria. |
| Margin of preference not applicable | Confirm this matches the TDS setting. |

---

## 18. Completion Rule

The screen is complete when:

1. Each criterion has a name, stage, evaluation basis, source/link, and bidder-facing wording.
2. Pass/fail criteria have clear pass/fail rules.
3. Scored criteria have marks.
4. Technical scoring total and pass mark are complete where scored technical evaluation applies.
5. Financial evaluation basis is complete.
6. Preference/reservation treatment matches the TDS.
7. Required evidence is linked or clearly instructed.
8. There are no blocker findings.

Warnings may remain, but must be visible.

---

## 19. Forbidden Content

Do not show:

```text
Actual bidder scores
Bidder rankings
Evaluation committee decisions
Award recommendation
Contract award approval
Actual submitted bid data
Hidden criteria
Post-award performance data
Rule IDs
Schema names
Hash values
Internal binding IDs
```

---

## 20. Stitch Prompt

```text
Design CFG-07 — Evaluation Setup for the KenTender Tender Configurations module.

Screen purpose:
Define how bids will be evaluated.

Single user decision:
How will submitted bids be evaluated?

Use this exact title:
Evaluation Setup

Use this exact subtitle:
Define how bids will be evaluated.

The screen is part of one tender configuration. It is not an actual bid evaluation screen, evaluation committee workspace, award recommendation screen, or contract award approval screen.

Top context strip must show only:
- Procurement Package Ref
- Tender Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Wizard State
- Issues

Primary actions:
- Add Criterion
- Import Suggested Criteria
- Run Check

Main tabs:
- All Criteria
- Preliminary Checks
- Qualification
- Technical Evaluation
- Financial Evaluation
- Preferences & Reservations
- Needs Attention

Main table columns:
- Criterion ID
- Criterion
- Stage
- Evaluation Basis
- Source / Link
- Marks / Rule
- Bidder Evidence
- Status
- Action

Use these sample rows:
1. EVAL-001 | Tender security submitted | Preliminary | Pass/Fail | TDS | Must be submitted in required form and amount | Required | Complete | Review
2. EVAL-002 | Manufacturer authorization for supplied servers | Qualification | Pass/Fail | Forms & Evidence | Required where bidder is not the manufacturer | Required | Complete | Edit
3. EVAL-003 | Compute node technical compliance | Technical | Scored | IT Requirement | 20 marks | Required | Complete | Edit
4. EVAL-004 | Implementation approach and delivery plan | Technical | Scored | Implementation Schedule | 15 marks | Required | Complete | Edit
5. EVAL-005 | Support and warranty capability | Technical | Scored | IT Requirement | 10 marks | Required | Complete | Edit
6. EVAL-006 | Financial comparison | Financial | Lowest evaluated price | Price Schedule | Compare evaluated price including required recurrent costs | Not required | Complete | Review
7. EVAL-007 | Margin of preference | Preference | Preference rule | TDS | Not applicable unless TDS states it applies | To be configured in Forms & Evidence if applicable | Complete | Review
8. EVAL-008 | Data migration experience | Qualification | Pass/Fail | User added | Minimum two similar assignments required | Required | Needs attention | Fix

Status labels:
- Complete
- Needs attention

Do not use:
- Valid
- Invalid
- Ready
- Locked
- Passed
- Failed

Drawer:
Use a right-side drawer for Add/Edit/Fix.

Drawer sections:
1. Criterion
   - Criterion Name
   - Stage
   - Evaluation Basis
   - Source / Link
   - Bidder-facing Wording
2. Rule or Score
   - Pass/Fail Rule
   - Marks
   - Technical Pass Mark
   - Financial Evaluation Rule
   - Preference Rule
3. Evidence
   - Bidder Evidence Requirement
   - Evidence Instruction
   - Related Form or Evidence Item
4. Evaluator Guidance
   - Evaluator Guidance
   - Disclosure Check
5. References
   - Related TDS Value
   - Related Requirement
   - Related Price Item
   - Related Form / Evidence Item

Evaluator guidance must not introduce hidden criteria.
The drawer must not allow editing of TDS, IT Requirements, Price Schedule, or Forms & Evidence.

Footer actions:
- Save Evaluation Setup
- Continue to Forms & Evidence

Disable Continue to Forms & Evidence if blocker issues remain.

Do not show actual bidder scores, bidder rankings, evaluation committee decisions, award recommendations, contract award approval, actual submitted bid data, hidden criteria, post-award performance data, rule IDs, hashes, schemas, or internal binding IDs.
```

---

## 21. Cursor Prompt

```text
Implement CFG-07 — Evaluation Setup for the KenTender Tender Configurations module.

Use the mounted UI bundle / Frappe Desk page architecture. Do not use a raw Stitch iframe. Do not load Tailwind from CDN.

Screen goal:
Define how bids will be evaluated.

Primary object:
TenderConfigurationEvaluationSetup

API shape:
{
  configuration_id,
  procurement_package_ref,
  tender_title,
  procuring_entity_name,
  procurement_method_label,
  std_family_label,
  standard_tender_document_label,
  wizard_state_label,
  blocker_count,
  warning_count,
  active_tab,
  evaluation_mode,
  scoring_summary: {
    show_scoring_summary,
    technical_marks_total,
    technical_pass_mark,
    configured_scored_marks,
    status_label
  },
  criteria: [
    {
      criterion_id,
      criterion_name,
      stage,
      stage_label,
      evaluation_basis,
      evaluation_basis_label,
      source_type,
      source_label,
      marks_or_rule_display,
      bidder_evidence_label,
      status,
      status_label,
      action_label,
      route_or_drawer_action
    }
  ],
  summary: {
    total_criteria,
    preliminary_count,
    qualification_count,
    technical_count,
    financial_count,
    preference_count,
    needs_attention_count
  }
}

Allowed tabs:
- all_criteria
- preliminary_checks
- qualification
- technical_evaluation
- financial_evaluation
- preferences_reservations
- needs_attention

Allowed status labels:
- Complete
- Needs attention

Allowed stages:
- Preliminary
- Qualification
- Technical
- Financial
- Preference

Allowed evaluation basis labels:
- Pass/Fail
- Scored
- Lowest evaluated price
- Preference rule
- Post-qualification

Render:
1. Page title: Evaluation Setup.
2. Subtitle: Define how bids will be evaluated.
3. Context strip with only the specified fields.
4. Primary actions: Add Criterion, Import Suggested Criteria, Run Check.
5. Tabs listed above.
6. Main table with exact columns:
   Criterion ID, Criterion, Stage, Evaluation Basis, Source / Link, Marks / Rule, Bidder Evidence, Status, Action.
7. Right drawer for Add/Edit/Fix with sections:
   Criterion, Rule or Score, Evidence, Evaluator Guidance, References.
8. Footer actions:
   Save Evaluation Setup, Continue to Forms & Evidence.
9. Disable Continue to Forms & Evidence if blocker_count > 0.

Rules:
- Do not render actual bidder scores.
- Do not render bidder rankings.
- Do not render evaluation committee decisions.
- Do not render award recommendation.
- Do not render contract award approval.
- Do not render actual submitted bid data.
- Do not introduce hidden criteria through evaluator guidance.
- Do not edit TDS, IT Requirements, Price Schedule, or Forms & Evidence inside this screen.
- References to TDS, requirements, price items, and forms must be read-only links.
- No hardcoded realistic values outside approved seed/demo fixtures.
- Use procurement-facing language only.
- Do not show internal IDs, hashes, schema versions, rule IDs, or binding IDs.

Acceptance criteria:
- User can understand how bids will be evaluated without seeing actual evaluation results.
- User can add/edit/fix evaluation criteria from a drawer.
- Every criterion has a clear stage, evaluation basis, source/link, rule or marks, evidence treatment, and bidder-facing wording.
- Technical marks and pass mark are visible only as configuration summary, never as bidder scores.
- Continue to Forms & Evidence is blocked only by blocker findings.
- Screen remains focused on evaluation framework setup.
```

---

## 22. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User can tell the screen defines how bids will be evaluated. |
| STD grounding | Screen covers preliminary, qualification, technical, financial, and preference/reservation evaluation areas. |
| Ownership | Screen owns evaluation framework only. |
| No actual evaluation leakage | Screen does not show bidder scores, rankings, committee decisions, or awards. |
| No hidden criteria | Evaluator guidance cannot introduce undisclosed criteria. |
| Table clarity | Table includes Stage, Evaluation Basis, Source / Link, Marks / Rule, Bidder Evidence, Status, and Action. |
| Drawer clarity | Drawer edits criteria only and shows references as read-only links. |
| Status simplicity | Only Complete and Needs attention are used. |
| Continuation rule | Continue to Forms & Evidence is disabled while blocker issues remain. |
| Implementation readiness | Stitch and Cursor prompts contain exact labels, rows, statuses, and forbidden content. |

---

## 23. Final Rule

If a field does not help the user define how bids will be evaluated, remove it from CFG-07.
