**KenTender Procurement Home — UX Content Specification**

**1\. Purpose**

Procurement Home is the main landing page for the KenTender procurement system.

It should give users a clear, role-aware overview of the entire procurement lifecycle and guide them to the right next action.

It answers:

What procurement work needs attention?

Where is each procurement journey in the lifecycle?

What approvals, blockers, deadlines, or handoffs require action?

Which module should I open next?

What has recently changed?

Procurement Home should not be a raw dashboard full of technical counts. It should be a calm operational command center.

**2\. Design Principle**

Procurement Home should be organized around **work and lifecycle progress**, not backend modules.

The user should not first think:

Which DocType or module do I open?

The user should think:

What needs my attention today?

Which procurement journey am I working on?

What stage is it in?

What should I do next?

**3\. Recommended Page Structure**

The Procurement Home page should contain these sections:

1\. Welcome and Role Context

2\. My Action Queue

3\. Procurement Lifecycle Overview

4\. Active Procurement Journeys

5\. Key Operational Metrics

6\. Blockers and Exceptions

7\. Recent Handoffs

8\. Module Shortcuts

9\. Evidence and Audit Access

The page should remain compact. Do not show every possible metric by default.

**4\. Section 1 — Welcome and Role Context**

Purpose:

Show the user where they are and what role/context is active.

Example:

Procurement Home

Welcome, Reynolds.

Role: Procurement Planner

Entity: Ministry of Health

Fiscal Year: 2026/2027

Recommended actions:

\[Open My Workbench\]

\[View All Journeys\]

\[Change Entity / Fiscal Year\]

If the user has multiple roles, show the active role clearly.

**5\. Section 2 — My Action Queue**

This should be the most important section on the page.

Purpose:

Show items that require the current user’s action.

Examples:

3 demands awaiting department approval

2 demands awaiting funding review

4 packages awaiting planning action

1 package ready for release

2 tenders awaiting publication setup

1 tender closing today

3 evaluations awaiting decision

1 contract awaiting signature

Recommended UI:

My Action Queue

\[Demand approval required\] 3

\[Funding review required\] 2

\[Packages needing planning\] 4

\[Tenders awaiting publication\] 2

\[Evaluations awaiting decision\] 3

\[Contracts awaiting signature\] 1

Each row should open the relevant workbench or filtered queue.

Do not show actions the user cannot perform.

**6\. Section 3 — Procurement Lifecycle Overview**

Purpose:

Give a simple lifecycle map of procurement work across the system.

Recommended lifecycle stages:

Strategy Alignment

→ Budget & Funding

→ Demand Intake

→ Procurement Planning

→ Tender Document Readiness

→ Tender Management

→ Bid Submission

→ Bid Opening

→ Evaluation & Award

→ Contract Management

Recommended UI:

Procurement Lifecycle

Strategy 12 aligned

Budget 8 funded

Demand 14 active

Planning 6 packages

Tendering 5 tenders

Bid Opening 2 upcoming

Evaluation 3 active

Contracts 4 active

Each stage should be clickable.

The purpose is navigation and awareness, not detailed reporting.

**7\. Section 4 — Active Procurement Journeys**

Purpose:

Show the most important active procurement journeys end-to-end.

A procurement journey is the cross-module thread from strategy and budget through demand, planning, tender, award, and contract.

Example card:

District Hospital Renovation Works

Current stage: Procurement Planning

Next action: Complete package readiness

Estimated value: KES 98,000,000

Method: Open Tender

Owner: Procurement Planning Unit

Status: On track

\[Open Journey\] \[Open Current Work\]

Recommended fields:

| **Field** | **Meaning** |
| --- | --- |
| Journey title | Human-readable procurement activity |
| Current stage | Where it is in the lifecycle |
| Next action | What must happen next |
| Owner | Responsible role/team |
| Value | Estimated or committed value |
| Method | Procurement method where known |
| Status | On track, blocked, delayed, urgent |
| Due date | Next important date |

Show only a small number by default:

Top 5 active journeys

Provide:

\[View All Journeys\]

**8\. Section 5 — Key Operational Metrics**

Purpose:

Show high-level procurement health.

Recommended cards:

Active Journeys

Approved Demands

Packages in Planning

Published Tenders

Evaluations Active

Contracts Active

Blocked Items

Upcoming Deadlines

Example:

Active Journeys 24

Approved Demands 18

Packages in Planning 7

Published Tenders 5

Evaluations Active 3

Contracts Active 4

Blocked Items 6

Upcoming Deadlines 9

Keep the labels business-readable.

Avoid raw system metrics such as:

handoff objects

workflow records

DocTypes

audit events count

JSON records

Those belong in Evidence & Audit.

**9\. Section 6 — Blockers and Exceptions**

Purpose:

Surface problems early.

Examples:

Budget insufficient for 2 demands

3 packages missing readiness documents

1 tender has no publication date

2 evaluations overdue

1 contract awaiting supplier signature

Recommended UI:

Blockers and Exceptions

High Priority

\- District Hospital Renovation Works: readiness documents missing

\- Medical Equipment Supply: budget confirmation expired

Medium Priority

\- Ambulance Maintenance: package review overdue

Each blocker should show:

what is blocked;

why it is blocked;

who owns the fix;

next action.

Good blocker copy:

Budget confirmation is missing. Finance must confirm funding before the demand can proceed.

Bad blocker copy:

BUDCONF_REF_NULL

**10\. Section 7 — Recent Handoffs**

Purpose:

Show cross-module movement without overwhelming users.

Examples:

Demand approved → ready for Planning

Package released → Tender created

Tender closed → ready for Bid Opening

Evaluation completed → award pending

Award approved → contract created

Recommended UI:

Recent Handoffs

District Hospital Renovation Works

Package released to Tender Management

Tender created: TND-MOH-2026-001

\[Open Tender\] \[View Evidence\]

Theatre Equipment Supply

Demand approved and ready for Planning

\[Open Planning\]

This section should use business labels.

Do not show technical handoff IDs unless the user opens Evidence or Technical Details.

**11\. Section 8 — Module Shortcuts**

Purpose:

Give clear access to major modules.

Recommended shortcuts:

Strategy Alignment

Budget & Funding

Demand Intake & Approval

Procurement Planning

STD / Tender Document Readiness

Tender Management

Supplier & Bid Submission

Bid Opening

Evaluation & Award

Contract Management

Supplier Management

Evidence & Audit

Configuration

Each shortcut should include one short description.

Example:

Procurement Planning

Convert approved demands into tender-ready packages.

\[Open\]

Example descriptions:

| **Module** | **Description** |
| --- | --- |
| Strategy Alignment | Link procurement work to strategic priorities. |
| Budget & Funding | Manage funding, reservations, commitments, and budget controls. |
| Demand Intake & Approval | Capture and approve departmental needs. |
| Procurement Planning | Create packages from approved funded demands. |
| STD / Tender Document Readiness | Prepare or confirm required tender document paths. |
| Tender Management | Prepare, publish, manage, and close tenders. |
| Supplier & Bid Submission | Supplier-facing tender participation and bid submission. |
| Bid Opening | Open submitted bids under controlled rules. |
| Evaluation & Award | Evaluate bids and recommend/approve award. |
| Contract Management | Create and manage awarded contracts. |
| Evidence & Audit | Review lifecycle evidence and audit history. |

**12\. Section 9 — Evidence and Audit Access**

Purpose:

Allow auditors and authorized users to inspect evidence without forcing audit detail into the main page.

Recommended card:

Evidence & Audit

Review procurement journey evidence, approvals, handoffs, and technical records.

\[Open Evidence & Audit\]

Normal users should see only a simple access point.

Auditors may see extra widgets such as:

Pending audit review

Recent evidence records

Exception approvals

Superseded releases

Correction requests

Technical logs should be admin-only.

**13\. Role-Based Personalization**

The home page should adapt to the user’s role.

**Requestor / Department User**

Show:

My demands

Returned demands

Approved demands

Procurement status of my requests

Hide:

technical audit

release controls

evaluation controls

configuration

**Finance / Budget User**

Show:

funding review queue

budget exceptions

reservations

commitments

demands awaiting funding

**Procurement Planner**

Show:

approved demands ready for planning

packages in creation

planning blockers

packages ready for review or release

**Tender Manager**

Show:

packages released to Tender Management

tenders awaiting publication

published tenders

closing deadlines

clarifications/addenda

**Evaluation User**

Show:

closed tenders awaiting evaluation

evaluation panels

pending scoring

award recommendations

**Contract Manager**

Show:

awards awaiting contract creation

contracts awaiting signature

active contracts

delivery/payment milestones

**Auditor / Oversight User**

Show:

evidence exceptions

approval trails

handoff history

audit queue

technical details access

**14\. Recommended First-Screen Layout**

┌ Procurement Home ──────────────────────────────────────────────────────────┐

│ Welcome, Reynolds │

│ Ministry of Health · FY 2026/2027 · Procurement Planner │

│ \[Open My Workbench\] \[View All Journeys\] \[Change Context\] │

└─────────────────────────────────────────────────────────────────────────────┘

┌ My Action Queue ────────────────────────┬ Blockers and Exceptions ─────────┐

│ Packages needing planning 4 │ 2 budget issues │

│ Packages awaiting review 2 │ 3 readiness blockers │

│ Tenders awaiting publication 1 │ 1 overdue evaluation │

│ Contracts awaiting signature 1 │ \[View blockers\] │

└─────────────────────────────────────────┴──────────────────────────────────┘

┌ Procurement Lifecycle ─────────────────────────────────────────────────────┐

│ Strategy → Budget → Demand → Planning → Tender → Opening → Evaluation │

│ 12 8 14 6 5 2 3 │

└─────────────────────────────────────────────────────────────────────────────┘

┌ Active Procurement Journeys ───────────────────────────────────────────────┐

│ District Hospital Renovation Works │

│ Current stage: Procurement Planning · Next: Complete readiness │

│ \[Open Journey\] \[Open Current Work\] │

│ │

│ Theatre Equipment Supply │

│ Current stage: Tender Management · Next: Publish tender │

│ \[Open Journey\] \[Open Current Work\] │

└─────────────────────────────────────────────────────────────────────────────┘

┌ Module Shortcuts ──────────────────────────────────────────────────────────┐

│ Demand Intake | Procurement Planning | Tender Management | Evaluation │

│ Contract Management | Evidence & Audit | Configuration │

└─────────────────────────────────────────────────────────────────────────────┘

**15\. Content Priority**

The most important content should appear in this order:

1\. My Action Queue

2\. Blockers and Exceptions

3\. Active Procurement Journeys

4\. Lifecycle Overview

5\. Module Shortcuts

6\. Evidence and Audit

7\. Reports / Analytics

Do not put static reports above user actions.

**16\. UX Rules**

Procurement Home should:

show what needs attention;

show lifecycle context;

show active journeys;

guide users to the correct module;

hide technical records by default;

adapt to role;

use business-readable language;

show blockers clearly;

provide evidence access without overwhelming the page.

Procurement Home should not:

be a blank dashboard;

be a grid of raw modules only;

show every metric at once;

expose DocTypes;

show handoff IDs as primary content;

force users to understand backend records;

duplicate every module’s full dashboard;

become an audit log.

**17\. Recommended Labels**

Use:

My Action Queue

Active Procurement Journeys

Current Stage

Next Action

Blocked Items

Upcoming Deadlines

Recent Handoffs

Open Current Work

View Evidence

Avoid:

DocType

workflow instance

source object

target object

technical reference

handoff payload

JSON

internal log

**18\. Final Product Rule**

Procurement Home succeeds if a user can open KenTender and immediately understand:

what needs their attention;

which procurement journeys are active;

where each journey is in the lifecycle;

what is blocked;

what changed recently;

which module or workbench to open next.

It fails if the user only sees static modules, technical records, or empty dashboard cards and still has to guess where to work.