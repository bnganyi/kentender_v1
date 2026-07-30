**Implement the bidder-facing Price Schedule module**

**1\. Objective**

Create a simple, fully electronic pricing workflow driven by the published tender configuration.

The bidder must price the configured goods and services directly in the system. Do not recreate a paper price schedule, require spreadsheet uploads, or ask bidders to re-enter totals elsewhere.

The Price Schedule is the authoritative source of tender prices. Its calculated totals must flow into the Form of Tender and final submission review as read-only values.

**2\. Implementation principles**

- The published tender configuration defines what must be priced.
- The canonical IT STD provides the available schedule structures.
- Not every tender requires every schedule.
- NSSF data is a test fixture, not the canonical structure.
- Use manually prepared tender/template configuration. Do not build another compiler, rules engine or automatic PDF extractor.
- Reuse existing bidder-workspace patterns, models, permissions and section-status services.
- Do not display internal IDs, hashes, schema names or technical metadata.
- Do not show evaluation scores, Passed, Failed, Qualified or Compliant.

**3\. Configuration**

Add or extend a simple tender-level Price Schedule configuration.

It must support:

- Single-lot or multi-lot tender
- Main offer
- Alternative offers only when expressly permitted
- Supply and Installation schedule
- Recurrent Costs schedule only when required
- Configured currencies
- Configured pricing columns
- Country-of-origin requirement by line
- Tax fields only when separately required
- Recurrent-cost periods
- Required and optional lines
- Whether zero is an accepted entered price

Each configured price line must contain at least:

- Stable internal line identifier
- Display reference
- Description
- Schedule type
- Lot, when applicable
- Quantity
- Unit
- Required or optional
- Country-of-origin requirement
- Permitted currency or currencies
- Display order

Descriptions, quantities and units are published tender data and must be read-only for bidders.

Do not expose internal identifiers in the UI.

If the existing tender model already represents inventory or implementation-schedule lines, reference those records rather than creating duplicate item descriptions.

**4\. Bidder response data**

Persist bidder-entered pricing separately from the published line configuration.

Each response must be scoped to:

- Tender
- Bidder submission
- Main or permitted alternative offer
- Lot, when applicable
- Schedule
- Configured price line
- Currency or configured currency component

Store monetary values using decimal types. Do not use binary floating-point calculations.

Distinguish between:

- Blank: the bidder has not answered
- Zero: the bidder deliberately entered zero

Do not treat blank and zero as equivalent.

**5\. Screens**

**5.1 Price Schedule overview**

Implement the approved Price Schedule overview.

Show:

- Title: Price Schedule
- Description: Enter your prices for the goods and services specified in this tender.
- Overall progress
- Configured schedules
- Progress for each schedule
- Status
- Action

Show only applicable configured schedules.

Examples:

- Supply and Installation
- Recurrent Costs

Omit Recurrent Costs completely when it is not configured.

For multiple lots, provide a lot selector. Do not show it for a single-lot tender.

For permitted alternatives, provide separate configured offer tabs. Do not show alternative controls when alternatives are prohibited.

Allowed statuses:

- Not started
- In progress
- Complete
- Needs attention

**5.2 Supply and Installation**

Render an inline editable pricing table.

Base columns:

- Item
- Description
- Quantity
- Unit
- Country of origin, when required
- Currency
- Unit price
- Total

Rules:

- Item, description, quantity and unit are read-only.
- Country of origin uses a country-name selector, not an origin-code field.
- Currency is either fixed by configuration or restricted to the permitted currencies.
- Show only the pricing columns configured for the tender.
- If local and foreign components are required, render those configured columns in the same schedule.
- Calculate line totals automatically.
- Calculate schedule subtotals automatically.
- Bidder cannot add, delete or reorder published lines.
- Bidder cannot directly edit calculated totals.

Actions:

- Back to Price Schedule
- Save draft
- Continue

**5.3 Recurrent Costs**

Render this screen only when recurrent costs are configured.

Show:

- Item
- Description
- Quantity
- Unit
- Currency
- Configured periods
- Total

Configured periods may be Year 1, Year 2, Year 3 or another tender-defined period set.

Rules:

- Item definitions and periods are read-only.
- Bidder enters the price for each required period.
- Calculate row totals, period subtotals and the recurrent-cost total.
- Do not assume a fixed number of years.
- Do not create recurrent-cost rows that are absent from the tender configuration.

Actions:

- Back to Price Schedule
- Save draft
- Continue

**5.4 Review Price Schedule**

Implement a review screen showing:

- Lot, when applicable
- Schedule
- Currency
- Subtotal
- Status
- Action

Include:

- Supply and Installation subtotal
- Recurrent Costs subtotal when applicable
- Separately configured taxes when applicable
- Total for each currency

Never convert or combine different currencies into a single total.

Display blocking issues above the summary. Each issue must link to the affected schedule or line.

Examples:

- 2 required items have no unit price.
- Country of origin is missing for item 1.4.
- One recurrent-cost period is incomplete.

Actions:

- Back
- Save draft
- Complete Price Schedule

Disable Complete Price Schedule while blocking issues remain.

Completing this section is not certification or bid submission. Do not add a declaration, signature field, confirmation checkbox or certification dialog.

**6\. Calculations**

Calculate values on the server. Client-side calculations may provide immediate display feedback but are not authoritative.

For each currency component:

- Line total = configured quantity × entered unit price
- Schedule subtotal = sum of valid line totals
- Period subtotal = sum of recurrent-cost values for that period
- Schedule total = sum of schedule subtotals
- Lot total = sum of applicable schedule totals for that lot

Apply configured tax calculations only when the tender requires separate tax pricing.

Do not perform currency conversion.

Use the configured currency precision consistently. Apply rounding at the line-total level and use the rounded line totals for subtotals.

Do not implement unspecified discount calculations. If an existing Form of Tender workflow captures permitted discounts, keep that responsibility there and consume the Price Schedule totals as its base amounts.

**7\. Validation**

A required price line is complete only when:

- Every required price field has an explicit value
- Currency is permitted
- Country of origin is present when required
- Every required recurrent-cost period is priced
- Values use valid decimal precision
- Negative prices are rejected
- Zero is accepted only where the configuration permits it

An optional line may remain blank.

Validation must run:

- When saving
- When opening the review screen
- When completing the section
- During final submission readiness checks

Return field-level errors and a section-level issue list.

**8\. Status derivation**

Derive status rather than allowing it to be manually selected.

- Not started: no bidder price responses exist
- In progress: some responses exist, but required entries remain incomplete
- Complete: the bidder completed the section and no blocking issues remain
- Needs attention: a previously completed section has become invalid or contains blocking issues

Changing any price after completion must reopen the Price Schedule and set it to In progress or Needs attention until reviewed and completed again.

The bidder-workspace checklist must use the derived Price Schedule status and blocking-issue count.

**9\. Form of Tender integration**

The Form of Tender must consume Price Schedule totals through a read-only calculation/query service.

Do not:

- Copy totals into editable Form of Tender fields
- Ask bidders to type the tender price again
- Maintain independent competing totals

If the Price Schedule changes after the Form of Tender has been completed or certified, mark the Form of Tender as requiring review.

Final submission must be blocked when:

- The Price Schedule is required but incomplete
- Blocking Price Schedule issues exist
- The Form of Tender no longer reflects the current Price Schedule totals

**10\. Security and lifecycle**

Use the existing bidder-workspace authorization rules.

Ensure:

- A bidder can access only its own submission
- Published price-line definitions cannot be modified through bidder endpoints
- Calculated totals cannot be overridden by client requests
- Completed sections remain editable before final submission, but editing reopens the section
- Final submission locking follows the existing submission lifecycle

Do not create a separate approval workflow inside the Price Schedule. Bidder completion is not procurement evaluation or approval.

**11\. Fixtures**

Create lean fixtures proving configuration-driven behaviour:

- Single-lot tender with Supply and Installation only
- Multi-lot tender with Supply and Installation and Recurrent Costs
- Tender using more than one permitted currency

Do not make the fixtures NSSF-specific. NSSF may be retained as an additional calibration fixture only.

**12\. Tests**

Add tests for:

- Applicable schedules are generated from tender configuration
- Recurrent Costs are omitted when not configured
- Single-lot and multi-lot behaviour
- Main and permitted alternative offers remain separate
- Read-only published descriptions, quantities and units
- Required price validation
- Blank and zero remain distinct
- Country-of-origin validation
- Currency restrictions
- Decimal calculations and rounding
- Recurrent-cost period totals
- Totals remain separate by currency
- Server totals cannot be overridden
- Completion is blocked by unresolved issues
- Editing a completed schedule reopens it
- Checklist status and issue roll-up
- Form of Tender receives read-only current totals
- Price changes invalidate Form of Tender review
- Cross-bidder access is rejected
- No internal IDs, hashes or technical metadata appear in rendered bidder screens

**13\. Delivery**

Before implementation, inspect the repository and identify:

- Existing tender configuration model
- Existing bidder-response persistence pattern
- Existing section-status and readiness services
- Existing Form of Tender total fields
- Approved Price Schedule Stitch designs
- Existing money, currency and decimal utilities

Reuse these components. Do not introduce parallel infrastructure.

Implement the module, migrations if required, fixtures, tests and checklist integration.

Finish with a concise implementation report containing:

- Files changed
- Configuration added
- Calculation rules implemented
- Validation rules implemented
- Form of Tender integration
- Tests executed and results
- Any genuine remaining gaps

Do not expand the task into evaluator pricing analysis, bid comparison, currency conversion, arithmetic-error correction after submission, spreadsheet import or PDF generation.