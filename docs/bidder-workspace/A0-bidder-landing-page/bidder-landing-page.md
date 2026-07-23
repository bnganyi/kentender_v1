# Implement the public-facing KenTender “Available Tenders” landing page for bidders.

Important architecture decision:

This page must be a Frappe Website / Portal page, not an internal Frappe Desk page. Officers use Desk. Bidders and public users use the portal.

Frappe implementation direction:

\- Use a route under the app’s \`www\` folder.

\- Prefer \`/tenders\` as the public route.

\- Use a Python page controller to populate template context.

\- Use Jinja for server-rendered HTML.

\- Add page-specific CSS and JS only where needed.

\- Do not build this as a Desk \`frappe.ui.Page\`.

Target files:

Create or update the equivalent paths in the KenTender app:

\- \`kentender/www/tenders/index.html\`

\- \`kentender/www/tenders/index.py\`

\- \`kentender/www/tenders/index.css\`

\- \`kentender/www/tenders/index.js\`

If the app name or folder structure differs, inspect the project and use the actual app module path.

Page name:

Available Tenders

Route:

\`/tenders\`

Purpose:

Allow bidders and public users to browse published tender opportunities, filter them, view the official tender document, open the Published Tender Overview, and continue existing bids where applicable.

Primary user flow:

Available Tenders

→ Published Tender Overview

→ Start Bid

→ Bidder Workspace / Submission Checklist

For existing bidder drafts:

Available Tenders

→ Continue Bid

→ Bidder Workspace / Submission Checklist

Top public navigation:

\- KenTender

\- Tenders

\- My Bids

\- Clarifications

\- Account

Do not show internal officer modules:

\- Tender Management

\- Procurement Packages

\- Tender Configurations

\- Publications

\- Bid Submissions

\- Evaluation

\- Awards

\- STD Administration

Data source:

Render from published tender/publication records only.

Inspect the project for existing DocTypes before creating new ones. Likely source DocTypes may include:

\- Published Tender

\- Tender Publication

\- Tender

\- Tender Configuration

\- Bid Submission

\- Bid Draft

\- Bidder Workspace

\- Clarification

Use the existing DocTypes if present.

Do not expose internal publication setup states or package review states.

Allowed public tender statuses:

\- Open

\- Closing Soon

\- Clarification Period Closed

\- Closed

\- Cancelled

Map internal system status to public bidder status:

\- Published + current time before submission deadline → Open

\- Published + submission deadline within configured threshold, e.g. 72 hours → Closing Soon

\- Published + clarification deadline passed but submission deadline not passed → Clarification Period Closed

\- Published + submission deadline passed → Closed

\- Cancelled / Suspended / Withdrawn → Cancelled or Unavailable, depending on existing system statuses

Do not display these internal states:

\- Draft

\- Draft Setup

\- Awaiting Setup

\- Ready to Publish

\- Package Review Generated

\- Ready for Package Confirmation

\- Published internally but not bidder-visible

\- Evaluation

\- Awarded, unless specifically exposed later through public award notices

Page layout:

Use a clean public portal layout, not an internal dashboard.

Structure:

1\. Public top navigation

2\. Page header

3\. Search and filters

4\. Tender result list

5\. Right-side “Before you bid” panel

6\. Empty state

7\. Pagination

Header:

Title:

Available Tenders

Subtitle:

Browse open procurement opportunities and start an electronic bid submission.

Search:

Placeholder:

Search by tender title, reference, procuring entity, or category

Filters:

\- Procuring Entity

\- Procurement Category

\- Standard Tender Document

\- Procurement Method

\- Submission Deadline

\- Tender Status

\- Eligibility / Supplier Category, only if the existing system supports it

Buttons:

\- Filter

\- Clear Filters

Tender result card fields:

Each tender card must show:

\- Tender Title

\- Tender Reference

\- Procuring Entity

\- Procurement Method

\- Procurement Category

\- Standard Tender Document

\- Published Date

\- Clarification Deadline

\- Submission Deadline

\- Time Remaining

\- Public Status Badge

\- Brief Scope Summary

\- Primary Action

\- Secondary Actions

Primary action logic:

\- If tender is open and logged-in bidder has no draft: \`View Tender\`

\- If tender is open and logged-in bidder has draft: \`Continue Bid\`

\- If logged-in bidder already submitted: \`View Submitted Bid\`

\- If submission deadline has passed and no submission: \`View Tender\`

\- If tender is cancelled: \`View Notice\`

\- If user is guest: \`View Tender\`

Do not show \`Start Bid\` directly on this landing page.

\`Start Bid\` belongs on the Published Tender Overview screen.

Secondary actions:

\- View Tender Document

\- Download Tender Document

\- View Clarifications

Action routes:

\- \`View Tender\` → published tender overview route

\- \`Continue Bid\` → bidder workspace checklist route

\- \`View Submitted Bid\` → submission receipt or read-only submitted bid route

\- \`View Tender Document\` → official generated tender document viewer

\- \`Download Tender Document\` → official generated PDF download

\- \`View Clarifications\` → tender clarification page or anchor on overview page

Right-side panel:

Title:

Before you bid

Content:

\- Review the official tender document.

\- Check clarification and submission deadlines.

\- Prepare required declarations, evidence, technical responses, and price schedule.

\- Submit electronically before the deadline.

Also show authenticated bidder summary if user is logged in:

\- My Draft Bids count

\- Submitted Bids count

\- Closing Soon count

If user is guest, show:

Sign in to start or continue a bid.

Empty state:

If no tenders match filters, show:

No tenders found.

Try changing your filters or search terms.

Closed tender behavior:

\- Do not show closed tenders in the default list.

\- Closed tenders may appear only when the user filters by Closed or opens from My Bids.

\- Closed tenders must not allow starting a new bid.

Security and permissions:

\- Public tender listing may be visible to guests.

\- Bid-specific state must only be shown to authenticated bidders.

\- Do not expose another bidder’s draft/submission status.

\- Use the current session user to resolve bidder-specific draft/submission state.

\- If user is Guest, do not query private bid drafts or submissions.

\- Do not expose internal package references or internal workflow IDs.

\- The bidder-facing reference should be the official tender reference.

Server-side controller:

In \`index.py\`, implement \`get_context(context)\`.

Responsibilities:

\- Read query params:

\- \`q\`

\- \`procuring_entity\`

\- \`category\`

\- \`std\`

\- \`method\`

\- \`status\`

\- \`deadline\`

\- \`page\`

\- Query only bidder-visible published tenders.

\- Apply filters.

\- Compute public status.

\- Compute time remaining.

\- Compute primary action label and target URL.

\- Compute secondary action URLs.

\- Add counts for the right-side panel.

\- Return a clean context object for the Jinja template.

Expected context shape:

{

"filters": {...},

"tenders": \[

{

"title": "...",

"tender_reference": "...",

"procuring_entity": "...",

"procurement_method": "...",

"procurement_category": "...",

"standard_tender_document": "...",

"published_datetime": "...",

"clarification_deadline": "...",

"submission_deadline": "...",

"time_remaining_label": "...",

"public_status": "Open",

"scope_summary": "...",

"primary_action_label": "View Tender",

"primary_action_url": "/tenders/...",

"view_document_url": "...",

"download_document_url": "...",

"clarifications_url": "..."

}

\],

"counts": {

"draft_bids": 0,

"submitted_bids": 0,

"closing_soon": 0

},

"pagination": {...}

}

Use existing date/time formatting utilities in the project. If none exist, use Frappe utilities consistently and include timezone labels.

Template requirements:

\- Extend the existing KenTender portal base template if present.

\- If no custom base exists, extend Frappe’s standard web template.

\- Keep the UI public-facing and simple.

\- Use cards for tender results on normal public portal layout.

\- Make the results responsive.

\- On desktop, allow a two-column layout: results left, guidance panel right.

\- On mobile, stack search, filters, results, then guidance.

Do not use hardcoded sample tender records in the final implementation.

Temporary mock data is only allowed if no relevant DocTypes exist yet, but must be clearly isolated and easy to replace.

Implementation details:

\- Use server-rendered initial results.

\- Use GET query parameters for search/filter state so URLs are shareable.

\- JS may enhance filtering but must not be required for basic page functionality.

\- Clear Filters should route back to \`/tenders\`.

\- Preserve selected filter values after reload.

\- Ensure document buttons are hidden or disabled if no official document is available.

\- Show a clear “Document not available” state if needed.

Acceptance criteria:

1\. \`/tenders\` loads outside Desk.

2\. The page does not show any internal officer navigation.

3\. Only bidder-visible published tenders are listed.

4\. Default list excludes closed/cancelled tenders unless explicitly filtered.

5\. Search works by title, reference, procuring entity, and category.

6\. Filters preserve state through query params.

7\. Tender cards show key deadlines and public status.

8\. Primary action is state-driven.

9\. Guest users see \`View Tender\`, not private draft/submission actions.

10\. Logged-in bidders see \`Continue Bid\` or \`View Submitted Bid\` only for their own bids.

11\. \`View Tender\` opens the Published Tender Overview screen.

12\. \`Continue Bid\` opens the Bidder Workspace / Submission Checklist.

13\. Official tender document actions are package-driven, not hardcoded.

14\. No internal package review, publication setup, evaluation, or award workflow state is exposed.

15\. Page is responsive and usable on mobile.

Do not implement the Published Tender Overview in this task unless the route target is missing. If missing, add a placeholder route or TODO only.

Deliver:

\- Implement the page.

\- Keep changes minimal and localized.

\- Reuse existing KenTender styles/components where available.

\- Add comments only where the data mapping is non-obvious.