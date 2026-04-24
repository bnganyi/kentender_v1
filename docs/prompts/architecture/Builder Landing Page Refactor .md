Builder Landing Page Refactor

# Review

**What is causing the problem**

The content is pushed down by the combination of:

-   large header block
-   subtitle
-   four KPI cards with generous vertical padding
-   tabs + queue chips + helper text + filters + search
-   then only after that the master-detail work area starts

So the page is correct structurally, but the **working list/detail pane starts too low**.

**Best low-risk refactor**

**1\. Compress the header band**

Keep:

-   title
-   subtitle
-   New Demand button

But reduce vertical padding above and below them.

The title block can be about **30–40% shorter** without losing clarity.

**2\. Tighten KPI cards**

Do not remove them. Just make them shallower.

Change from:

-   large cards with big empty interior

To:

-   compact cards with:
    -   smaller top/bottom padding
    -   slightly smaller value text
    -   tighter card height

That alone will pull the work area upward significantly.

**3\. Merge tabs and queues more tightly**

Right now you have:

-   top tabs
-   second row queue chips
-   helper text
-   filters
-   search

That is too much stacked control surface.

**Better:**

Keep:

-   top tabs
-   queue chips
-   search

But:

-   move helper text into muted inline text beside tabs/queues, or remove it
-   collapse filters by default
-   reduce vertical gaps between tab row and queue row

**4\. Make search sit on the same control line if possible**

Instead of:

-   tabs row
-   queue row
-   helper text
-   filters row
-   search row

Refactor to:

-   Row 1: tabs + New Demand already in page header
-   Row 2: queue chips + search aligned right
-   Row 3: collapsed filters only

This is the biggest non-drastic win.

**5\. Reduce outer container padding above the master-detail pane**

The gap between the controls block and the “All Demands” / detail split is too generous.

Trim that spacing so the split pane begins sooner.

**6\. Keep filters collapsed by default**

This is already partly right. Keep it collapsed and visually smaller.

Do not let filters consume height unless the user explicitly opens them.

**Specific layout target**

The page should visually become:

Title + button

Compact KPI strip

Tabs / queues / search / collapsed filters

Master-detail work area

instead of:

Large title block

Large KPI strip

Large nav/control block

Then work area much lower

**One more strong improvement**

**Make the master-detail pane slightly taller on first paint**

Without changing the concept, increase the visible height of:

-   left list panel
-   right detail panel

So even if some header remains, the user still feels they’re in the working area immediately.

**What not to do**

Do not:

-   remove KPI cards entirely
-   remove tabs entirely
-   move actions into hidden menus
-   collapse the detail panel by default

That would be overcorrecting.

**My recommended minimal refactor list**

1.  Reduce top header padding
2.  Reduce KPI card height
3.  Put queue chips and search on one row
4.  Remove or inline helper text
5.  Keep filters collapsed and compact
6.  Reduce spacing before the master-detail pane
7.  Increase visible split-pane height slightly

# Cursor Prompts

Apply a non-drastic compression refactor to the Demand Intake & Approval landing/workbench page.

Goal:  
Keep the current concept, KPI cards, queues, master-detail layout, and action model.  
Improve vertical efficiency so the real work area starts higher on the page.  
Also fix KPI card number truncation by removing unnecessary repeated currency text.

Do NOT redesign the page.  
Do NOT change DIA workflow logic, permissions, or queue semantics.  
Do NOT remove the master-detail pattern.

**1\. HEADER COMPRESSION**

Refactor the top page header to use less vertical space.

Keep:

-   page title
-   subtitle
-   New Demand button

Change:

-   reduce top and bottom padding
-   tighten spacing between title and subtitle
-   tighten spacing between header and KPI strip

The header should still feel professional, but clearly more compact.

**2\. KPI STRIP COMPRESSION**

Keep the KPI cards, but make them shallower and more space-efficient.

**Required changes:**

-   reduce card vertical padding
-   reduce internal empty space
-   slightly reduce value font size only if needed for fit
-   keep labels readable and prominent
-   ensure all cards align to same height

**Critical number-display rule:**

Do NOT repeat currency in every KPI card when all cards are using the same page currency context.

Instead:

-   assert currency once in the page context or subtitle if needed
-   show card values as pure numbers where appropriate
-   use compact formatting that preserves full readability

Examples:

-   Instead of KES 3,025,0...  
    render full value cleanly, e.g. 3,025,000
-   If currency must be present, use it once in page context, not repeated everywhere

**Labels should remain explicit**

Examples:

-   Approved
-   Planning Ready
-   Emergency Approved
-   Total Value Ready for Planning

No truncation of important numeric values is acceptable.

**3\. CONTROL BAND COMPRESSION**

The area between the KPI strip and the master-detail work area is too tall.  
Compress it without changing the core concept.

**Keep:**

-   top tabs (My Work / All / Approved / Rejected)
-   queue chips
-   filters
-   search

**Refactor:**

-   reduce vertical spacing between tab row and queue row
-   reduce vertical spacing between queue row and filters/search
-   remove or inline explanatory helper text if it pushes content down
-   keep Filters collapsed by default and visually compact
-   make search field less tall if needed

**4\. COMBINE QUEUES + SEARCH MORE EFFICIENTLY**

If feasible without major redesign:

-   place queue chips and search in a tighter shared control region
-   avoid giving each its own large vertical band

At minimum:

-   reduce the number of stacked rows before the master-detail pane begins

Do NOT remove queues or search.  
Do NOT hide important controls behind menus.

**5\. REDUCE GAP BEFORE MASTER-DETAIL AREA**

The gap between the top control container and the actual demand list/detail split is too generous.

Required:

-   trim top margin/padding before the split pane
-   make the working area begin noticeably sooner

The page should feel like users arrive at work immediately, not after a long preamble.

**6\. INCREASE FIRST-PAINT WORK AREA EMPHASIS**

Without changing the concept:

-   slightly increase the visible initial height of the list/detail work region
-   ensure the user can see meaningful demand content higher on first load

This can be done by reclaiming space from the header/KPI/control band rather than changing the master-detail concept.

**7\. NUMBER FORMATTING / CARD SPACE RULES**

Apply system-wide card value formatting rules on this page:

1.  No truncated KPI values
2.  Prefer compact numeric display over repeated currency prefixes
3.  Currency should be asserted once where possible, not repeated redundantly
4.  Use full thousands separators
5.  If abbreviations are ever used, they must be deliberate and readable (not accidental CSS truncation)

For this page, full numbers are preferred over clipped values.

**8\. DO NOT CHANGE**

Do NOT change:

-   queue meanings
-   approval actions
-   detail panel concept
-   list/detail concept
-   underlying DIA logic
-   role behavior
-   filters semantics

This is a layout compression and information-density improvement only.

**9\. ACCEPTANCE CRITERIA**

The refactor is correct only if:

-   the page header is visibly shorter
-   KPI cards are more compact
-   KPI numbers no longer truncate
-   repeated currency text is reduced or removed where unnecessary
-   the tabs/queues/filters/search block is tighter
-   the master-detail work area begins higher on the page
-   the page still feels like the same DIA workbench, not a redesign
-   no important controls are hidden or removed

At the end report:

1.  spacing/padding reductions made
2.  KPI card changes made
3.  how number truncation was fixed
4.  whether currency repetition was removed/reduced
5.  any remaining layout constraints that still prevent further compression without a deeper redesign

---

## 10. Implementation record (2026-04-23)

**Shipped in code** (`kentender_procurement` desk assets):

1. **Header** — `kt-dia-workspace-header--compact`: smaller title (`h5` / ~1.2rem), tighter intro, reduced shell padding and margins below header.
2. **KPI** — shallower cards (reduced padding, slightly smaller value type), **no** `KES` on every currency cell; values are **plain integers with locale grouping**; one line under the strip: *“All monetary figures in {currency}”* (`#kt-dia-kpi-currency-note`, `data-testid="dia-kpi-currency-context"`). **Removed** ellipsis/clip on `.kt-dia-kpi-value` so amounts do not truncate.
3. **Control band** — `kt-dia-control-surface` on the tab/queue/filters block; **queue pills + search** on one row (`kt-dia-queue-search-line` / `kt-dia-search-compact`); search label `sr-only`; filters stay `<details>` collapsed; chip row unchanged; removed the old separate full-width search row.
4. **Scope hint** — same content, tighter typography/margins (`kt-dia-scope-hint`).
5. **Master–detail** — `kt-dia-master-detail--tight`, smaller gap before split; **queue list** `max-height` increased to `min(78vh, 40rem)`.

**Cross-workbench:** **Procurement Planning** landing received the same **compact header, KPI strip, currency legend, tighter tabs/queues, split-pane lift** (no search in PP — search row is DIA-only). See **[Builder-Landing-Standard.md](./Builder-Landing-Standard.md)** for the shared look-and-feel rules for all future builders.

6. **Procurement Home** — `procurement_home_workspace.js` + `procurement_home_workspace.css`: compact header (`kt-ph-workspace-header--compact`), number-only currency KPIs with `#kt-ph-kpi-currency-note` (`ph-kpi-currency-context`), shallower KPI cards, no ellipsis on values.
7. **Strategy Management** — `strategy_workspace.js` + `strategy_workspace.css`: compact header, tighter KPI rows and master–detail (`kt-strategy-master-detail--tight`), no ellipsis on KPI values, plan list `max-height` to `min(78vh, 40rem)`.
8. **Budget Management** — `budget_workspace.js` + `budget_workspace.css`: same as Strategy for header/KPIs/split; `#kt-budget-kpi-currency-note` (`budget-kpi-currency-context`) with `resolveLandingDisplayCurrency()`; budget row list `max-height` to `min(78vh, 40rem)`.