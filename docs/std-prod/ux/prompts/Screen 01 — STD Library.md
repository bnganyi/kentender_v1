Screen name:

STD Library

User:

STD Administrator

Purpose:

Allow administrators to view, search, filter, and manage official Standard Tender Document families and their versions.

This screen is for STD Administration, not tender configuration.

Primary user goals:

\- See all STD families and active versions.

\- Identify versions pending review, due for review, or blocked from activation.

\- Open a family or version detail page.

\- Import a new STD package.

\- Create a new version of an existing STD family.

\- View usage, validation, source traceability, and lifecycle status.

Required layout sections:

1\. Page header

2\. Library KPI cards

3\. Library health / compliance summary

4\. Search and filters

5\. Version-aware STD table

6\. Row actions

7\. Pagination

8\. Empty, loading, and error states

Page header:

\- Title: Standard Tender Documents

\- Subtitle: Manage official STD families, active versions, validation status, applicability, source traceability, and lifecycle governance.

\- Primary button: Import STD Package

\- Secondary button: Create STD Family

Recommended KPI cards:

\- STD Families

\- Active STD Versions

\- Versions in Review

\- Review Due Soon / Overdue

\- Activation Blockers

Library health summary:

Show a concise compliance panel with:

\- Unauthorized STD versions in active tender setup

\- Versions pending approval

\- Versions due for review

\- Superseded versions referenced by historical tenders

\- Draft versions blocked from activation

Search and filters:

\- Search by title, family code, version code, category, source authority

\- Category filter

\- Lifecycle state filter

\- Source authority filter

\- Procurement method filter

\- Applicability filter

\- Active only toggle

\- Due for review toggle

\- Has validation blockers toggle

\- Used in tenders toggle

\- Superseded/archived toggle

Required table columns:

\- STD Title

\- Family Code

\- Active Version

\- Category

\- Procurement Method(s)

\- Lifecycle State

\- Applicability

\- Source Authority

\- Last Approved Date

\- Review Due Date

\- Used in Tenders

\- Validation Status

\- Actions

Required row actions:

\- Open

\- View Configuration

\- View Validation Report

\- View Source Traceability

\- View Usage

\- Create New Version

\- Submit for Review

\- Activate

\- Supersede

\- Archive

Action visibility rules:

\- Use in Tender: active versions only.

\- Activate: approved versions only, and only if there are no activation blockers.

\- Supersede: active versions only.

\- Archive: superseded versions only, subject to retention rules.

\- Submit for Review: draft or structuring versions only.

\- View Usage: active, superseded, or archived versions.

\- View Source Traceability: all versions.

\- View Validation Report: all versions.

Lifecycle states:

DRAFT, STRUCTURING, INTERNAL_REVIEW, LEGAL_REVIEW, PROCUREMENT_REVIEW, APPROVED, ACTIVE, SUSPENDED, SUPERSEDED, ARCHIVED

Validation states:

VALID, WARNING, BLOCKED, NOT_TESTED, REVIEW_REQUIRED

Design constraints:

\- Do not include side navigation.

\- This is not a generic document repository.

\- The table must be version-aware.

\- Make lifecycle state and validation status highly visible.

\- Make it clear that this screen manages official STD templates, not individual tenders.

\- Use a formal enterprise/government visual style.

\- Prefer compact, readable density over oversized marketing-style cards.