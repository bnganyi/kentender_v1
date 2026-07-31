**Implement the functional Procurement Home page**

**1\. Objective**

Procurement Home is the operational landing page for internal procurement users.

It must answer:

1. What requires my action?
2. What deadlines are approaching?
3. Where is procurement work currently concentrated?
4. What should I open next?

It is not an analytics dashboard, reporting warehouse or duplicate workflow engine.

**2\. Scope**

Implement:

- Page context
- Requires Your Action
- Procurement Pipeline
- Upcoming Deadlines
- Portfolio Snapshot
- Permission-scoped and empty states
- Real module queries
- Deep links to owning records
- Tests
- Coherent demonstration fixtures

Do not implement:

- Historical analytics
- Charts
- Recent activity
- News or announcements
- Quick approvals
- Inline state transitions
- Bidder identities
- Bid-submission counts
- Evaluation, award or contract metrics
- New dashboard persistence tables
- A generic dashboard/widget framework

The scope is fixed. Do not reduce it to a partial dashboard or ask for a lean/full implementation choice.

**3\. Inspect before implementation**

Identify and reuse:

- Existing Procurement Home route and page
- Approved Home Stitch designs
- Existing application shell
- Current user, role and organisational-scope services
- Procuring Entity model
- Financial Year model
- Strategy, budget, demand, planning and tender models
- Existing status enums and lifecycle services
- Existing permission checks
- Existing filtered list routes
- Current fixture and test patterns

Use the repository's actual model and status names. Do not create parallel lifecycle enums to match this prompt.

Document the source model and query used for every Home value before implementing it.

**4\. Architecture constraint**

Home must be a read-only projection of existing module data.

Do not persist:

- Home tasks
- Pipeline stages
- Dashboard totals
- Copied deadlines
- Duplicate statuses
- Precalculated demonstration figures

Compute Home data from authoritative module records when the page is requested.

A small Home query/service layer may coordinate existing module queries. Do not introduce an event bus, reporting database, materialised dashboard model or rules engine.

**5\. Route**

Use the canonical route:

/procurement/home

Preserve any current Home route through an alias or redirect if required.

Do not modify the primary navigation or top toolbar in this task.

**6\. Page context**

Header:

- Title: Procurement Home
- Description: Review your procurement work, deadlines and portfolio.
- Procuring Entity
- Financial Year

Behaviour:

- Default to the user's current permitted Procuring Entity and active Financial Year.
- Show an entity selector only when the user can access multiple entities.
- Show a financial-year selector only when the user can access multiple relevant years.
- Validate every selected entity and financial year against the user's access.
- A context change refreshes all Home sections.
- Do not apply one context to only part of the page.
- Do not add arbitrary date-range or module filters.

**7\. Home data contract**

Return one permission-scoped Home response containing:

- Selected entity
- Selected financial year
- Available entity choices
- Available financial-year choices
- Action items
- Pipeline stages
- Upcoming deadlines
- Portfolio snapshot
- Section visibility flags

Use the existing server-rendering or frontend API pattern. Do not introduce a new frontend data architecture solely for Home.

**8\. Requires Your Action**

This is the first and most prominent section.

Fields:

- Work item title and reference
- Procurement stage
- Action required
- Due date
- Urgency
- Action label
- Authorised target URL

Supported action labels:

- Review
- Resolve
- Continue

Do not provide Approve, Reject, Publish or any other state-changing button directly on Home.

**Eligible work**

Include only records where:

- The current user has permission to perform the required action
- The record is within the selected entity and financial year
- The lifecycle state genuinely requires action
- The action has not been completed, cancelled or superseded

Eligible examples include:

- Demand assigned for approval
- Demand returned to its owner for correction
- Procurement plan awaiting the user's review
- Plan returned for correction
- Tender configuration containing unresolved blockers assigned to the user or team
- Tender awaiting an authorised configuration review
- Publication awaiting review or approval
- Record returned from a governance step

Map these examples to actual repository states and assignments. Do not infer assignments from job titles or administrator status.

**Sorting and limits**

Sort in this order:

1. Overdue
2. Due soon
3. Other dated actions
4. Undated actions, oldest first

Define Due soon as due within the next three calendar days unless an existing shared deadline rule already defines it.

Show a maximum of eight items.

Provide View all work, linked to the appropriate existing work-queue destination. If no unified work queue exists, link to a filtered page that can display all permitted action items; do not build a second workflow engine.

**Empty state**

When no actions exist, show:

- No actions require your attention
- New approvals, returned work and other assigned actions will appear here.

**9\. Procurement Pipeline**

Show these six mutually exclusive stages:

1. Demands under review
2. Approved demands awaiting planning
3. Plan items awaiting tender initiation
4. Tenders in preparation
5. Published and open tenders
6. Closed tenders awaiting the next stage

Each stage contains:

- Label
- Count
- Filtered destination URL

**Stage rules**

Use explicit relationships and lifecycle states.

- **Demands under review:** submitted demands currently in review or approval and not approved, rejected, cancelled or returned to draft.
- **Approved demands awaiting planning:** approved demands not yet represented by an approved procurement-plan item.
- **Plan items awaiting tender initiation:** approved plan items that do not yet have a tender record.
- **Tenders in preparation:** tenders created but not published, cancelled or abandoned.
- **Published and open tenders:** published tenders whose submission deadline has not passed.
- **Closed tenders awaiting the next stage:** tenders whose submission period is closed and which have not yet entered an implemented downstream stage.

Use existing explicit links between demands, plan items and tenders. Do not match records by title, reference text or similar heuristic.

A procurement record must not be counted in two pipeline stages.

Do not add Evaluation, Award or Contract counts in this MVP.

Add a link:

View procurement lifecycle

Target it to the existing or planned Procurement Lifecycle page.

**10\. Upcoming Deadlines**

Show no more than five significant unresolved events.

Supported sources:

- Explicit demand review or approval deadline
- Explicit procurement-plan approval deadline
- Planned tender initiation date
- Scheduled publication date
- Clarification deadline
- Bid submission deadline

Fields:

- Event
- Procurement record title and reference
- Date and time
- Time remaining
- Action
- Target URL

Rules:

- Use only dates explicitly stored by the owning module.
- Do not manufacture deadlines from creation or update timestamps.
- Include future deadlines in ascending order.
- Include overdue deadlines only when the associated action remains unresolved.
- After overdue unresolved events, show the nearest future deadlines.
- Use the application's configured timezone and existing date-formatting conventions.
- Each action opens the owning record.
- Do not disclose bidder identities, submission contents or the number of bids received.

If there are no deadlines, show:

No upcoming procurement deadlines.

**11\. Portfolio Snapshot**

Show these six figures when the user has the relevant permissions:

1. Approved procurement budget
2. Funding allocated to approved procurement plans
3. Available funding balance
4. Unfunded approved demand
5. Active tenders
6. Open tenders

**Financial definitions**

- **Approved procurement budget:** total approved procurement funding for the selected entity and financial year.
- **Allocated to procurement plans:** funding allocated to approved procurement-plan items for the same context.
- **Available funding balance:** approved procurement budget minus approved plan allocations.
- **Unfunded approved demand:** the funding shortfall on approved demands that do not have sufficient confirmed funding.

Use the existing Budget & Funding service where it already defines these values. Do not reproduce competing financial calculations.

Do not aggregate different currencies.

If the budget module maintains an entity base currency, use that authoritative base-currency view. If it legitimately returns multiple currencies, render separate currency values rather than converting or combining them.

**Tender definitions**

- **Active tenders:** non-cancelled tenders in preparation, publication, open or closed-awaiting-next-stage states.
- **Open tenders:** published tenders whose submission deadline has not passed.

Do not include archived, cancelled or abandoned tenders.

**Interaction**

Every figure links to the corresponding permission-scoped supporting records.

Do not show:

- Percentage change
- Trend arrows
- Performance scores
- Savings
- Bid counts
- Unverified estimates

**12\. Permission behaviour**

Use existing permissions and organisational scope.

Minimum behaviour:

- Requestors see their own permitted demands and returned work.
- Approvers see actions explicitly assigned or available to them under the existing approval rules.
- Procurement Officers see permitted planning and tender work.
- Heads of Procurement see permitted entity-wide work and portfolio information.
- Administrators see only operational data allowed by their assigned organisational scope.

Administrator status does not automatically grant access to sealed bids or all entity data.

If the user lacks permission for a Home section:

- Omit that section
- Do not return its totals from the server
- Reflow the remaining layout
- Do not show locked cards or permission warnings

If Portfolio Snapshot is omitted, Upcoming Deadlines expands across the available width.

Home links must never expose records that the user cannot open.

**13\. Bid confidentiality**

Home must not expose before authorised opening:

- Bidder names
- Bid contents
- Tender prices
- Submission documents
- Number of bids received
- Submission activity patterns

General tender visibility or Administrator status must not bypass bid-sealing rules.

**14\. UI requirements**

Implement the approved Stitch design.

Page order:

1. Page context
2. Requires Your Action
3. Procurement Pipeline
4. Upcoming Deadlines and Portfolio Snapshot

Desktop layout:

- Requires Your Action: full width
- Procurement Pipeline: full width
- Upcoming Deadlines: left column
- Portfolio Snapshot: right column

Use the existing KenTender visual system.

Do not add:

- Hero banners
- Greetings
- Illustrations
- Additional cards
- Charts
- Tooltips containing technical definitions
- Internal IDs, hashes or schema information

Zero is valid data. Show 0; do not treat it as absent.

Do not use the illustrative Stitch values as production constants.

**15\. Failure handling**

Do not silently replace failed queries with zero.

If a permitted section cannot be loaded:

- Show a restrained section-level unavailable message
- Keep successfully loaded sections visible
- Log the underlying failure using the existing application logging pattern

Do not expose exception details or technical messages to the user.

**16\. Fixtures**

Create a coherent demonstration fixture using real module records.

The fixture must demonstrate:

- At least one assigned approval
- One returned item
- One tender configuration blocker
- One publication action
- All six populated pipeline stages where supported
- At least three upcoming deadlines
- Approved budget and plan allocations
- An unfunded approved demand
- Active and open tenders
- A user with no assigned actions
- A user without financial visibility

The figures shown by Home must be calculated from these records. Do not seed Home-specific totals.

Development data may be torn down and reseeded.

**17\. Tests**

Add tests for:

**Context**

- Correct default entity and financial year
- Multi-entity selector visibility
- Unauthorized entity or financial-year selection rejected
- Context applied consistently to all sections

**Requires Your Action**

- Only authorised actionable records included
- Completed and cancelled actions excluded
- Correct overdue and due-soon ordering
- Eight-item limit
- Correct deep links
- No state-changing Home actions
- Empty state

**Pipeline**

- Correct stage definitions
- Mutual exclusivity
- Correct handling of returned, cancelled and published records
- Correct filtered links
- No Evaluation, Award or Contract counts

**Deadlines**

- Explicit deadlines only
- Correct overdue and upcoming ordering
- Five-item limit
- Resolved deadlines excluded
- Correct timezone formatting

**Portfolio**

- Financial definitions match Budget & Funding
- Available balance calculated correctly
- Unfunded demand calculated correctly
- Currency values never combined
- Active and open tender definitions
- Correct supporting-record links

**Permissions and confidentiality**

- Section omission when permission is absent
- Data limited to organisational scope
- Home counts do not reveal forbidden records
- Bidder identities and bid counts never returned
- Administrator cannot bypass sealed-bid restrictions

**UI**

- Approved content order
- Permission-based layout reflow
- Genuine zero values displayed
- No internal identifiers or hard-coded demonstration metrics

Run the existing relevant regression suite in addition to the new Home tests.

**18\. Delivery report**

Provide a concise implementation report containing:

- Files changed
- Stitch design used
- Source query for each Home section
- Pipeline state mapping
- Financial metric definitions
- Permission rules applied
- Routes and deep links used
- Fixtures created
- Tests executed and results
- Genuine remaining gaps

Do not expand this task into Analytics, Evaluation, Awards, Contracts, Supplier Management or primary-menu restructuring.