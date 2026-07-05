**Planning Package Readiness Check UI — Simplified UX Brief**

**1\. Purpose**

The Readiness Check UI helps the planner confirm whether a procurement package is complete enough to move forward for review or release.

It answers:

Is this package ready?

What is missing?

Who needs to fix it?

What is the next action?

The screen should be simple, clear, and action-oriented.

**2\. Where It Appears**

Readiness should appear inside **Package Detail** as a tab or section:

Package Detail

├── Overview

├── Lines & Funding

├── Readiness

├── Review

└── Release

The Readiness tab should not feel like an audit log. It should feel like a checklist.

**3\. Readiness Statuses**

Use simple status labels:

| **Status** | **Meaning** |
| --- | --- |
| Not Checked | Readiness has not been run yet |
| Passed | Package can proceed |
| Failed | One or more blockers must be fixed |
| Passed with Warnings | Package can proceed, but warnings exist |
| Stale | Package changed after the last readiness check |

**4\. Readiness Checks**

Show checks in business language.

Recommended checklist:

| **Check** | **Meaning** |
| --- | --- |
| Demand approved | Source demand has final approval |
| Added to active plan | Demand is included in the active procurement plan |
| Funding confirmed | Budget line and funding are valid |
| Package lines complete | Package has valid lines linked to demand items |
| Category selected | Goods, Works, Services, or Consultancy is selected |
| Method selected | Procurement method is selected or derived |
| Documents attached | Required specifications or documents are available |
| Review complete | Required review/approval is complete before release |

Each check should show:

Pass

Warning

Failed

Not Required

**5\. Recommended UI Layout**

┌ Readiness ───────────────────────────────────────────────┐

│ Status: Failed │

│ 6 of 8 checks passed │

│ │

│ \[Run Readiness Check\] │

│ │

│ Checks │

│ ✓ Demand approved │

│ ✓ Added to active plan │

│ ✓ Funding confirmed │

│ ✓ Package lines complete │

│ ✓ Category selected │

│ ✓ Method selected │

│ ✕ Required documents missing │

│ ✕ Review not complete │

│ │

│ Blockers │

│ 1. Attach the required specification documents. │

│ 2. Submit package for review. │

│ │

│ Next action │

│ Resolve blockers before release. │

│ │

│ \[Go to Documents\] \[Submit for Review\] \[View Evidence\] │

└──────────────────────────────────────────────────────────┘

**6\. Passed State**

When all blocking checks pass:

Status: Passed

This package is ready to proceed.

Next action:

Submit for review or release to Tender Management, depending on approval status.

\[Submit for Review\] \[Go to Release\] \[View Evidence\]

Only show actions that are valid for the package state and user role.

**7\. Failed State**

When checks fail:

Status: Failed

This package is not ready yet.

Blockers:

\- Funding is not confirmed.

\- Package line is missing.

\- Procurement method is not selected.

Next action:

Resolve blockers and run the readiness check again.

\[Resolve Blockers\] \[Run Again\]

The UI must explain the fix. Do not show only technical failure codes.

**8\. Stale State**

If the package changed after readiness was last run:

Status: Stale

Package details changed after the last readiness check.

Run readiness again before release.

\[Run Readiness Check\]

**9\. Role Behavior**

| **Role** | **Allowed Actions** |
| --- | --- |
| Procurement Planner | Run readiness, resolve blockers, submit for review |
| Planning Reviewer | View readiness, request correction, approve/return |
| Procurement Authority | View readiness and release only if checks pass |
| Finance / Budget User | Resolve funding blockers |
| Auditor | View readiness evidence |
| Supplier | No access |

**10\. UX Rules**

The readiness UI should:

show the package readiness status clearly;

show passed and failed checks;

show blockers in plain language;

show the next action;

allow rerun after fixes;

hide technical details by default;

preserve evidence for audit.

The readiness UI should not show:

raw JSON;

internal object IDs;

handoff IDs;

source/target object fields;

technical stack traces;

audit records as primary content.

Technical details belong behind:

View Evidence

→ Technical Details

**11\. Final Product Rule**

The Readiness Check UI succeeds if a planner can immediately understand:

what passed;

what failed;

what must be fixed;

who should fix it;

whether the package can move to review or release.

It fails if users see technical checks but still do not know what action to take.