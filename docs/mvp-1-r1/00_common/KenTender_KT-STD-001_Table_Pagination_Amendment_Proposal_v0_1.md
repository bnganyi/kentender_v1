# KT-STD-001 amendment proposal — Table pagination

| Field | Value |
|---|---|
| Document | Amendment proposal for KT-STD-001 (Document Design and Verification Standards) |
| Version | 0.1 |
| Status | **Proposed** — not part of KT-STD-001; no register entry; no identifier assigned |
| Prepared | 6 October 2026 |
| Relies on | KT-STD-001 v1.22 (approved; **not read in full for this proposal** — see §7) |
| Owner decision | Project Owner, 6 October 2026, quoted in §1 |
| Effect if adopted | Adds one component clause to KT-STD-001 (a new version, Proposed until re-approved) |

KT-STD-001 v1.22 is not edited by this file. The text in §2 is for the owner to place, in a new KT-STD-001 version made under the document-change protocol.

## 1. Source

The owner's accepted standard, in their words:

> "Tables need pagination. Recommend a standard:, e.g., 1 far left: total number of rows. 2. right: dropdown to choose number of rows per page. 3. far right: page counter with current highlighted [1, 2, 3, ..., 8, 9]. 4. Default 10 rows"

The owner then accepted the recommended standard (below) with: "All accepted. Implement and document."

## 2. Proposed clause (text for KT-STD-001)

> **Table pagination.** A table whose row count can grow is paged. Every such table uses the one pager component; no module draws its own pager or its own row-count line.
>
> 1. **Layout.** One row beneath the table, above a hairline rule. At the far left, the total: "47 needs"; when the rows span more than one page, "Showing 11–20 of 47 needs". To the right, "Rows per page" with a choice of 10, 25, 50 and 100, defaulting to 10. At the far right, Prev, the numbered pages and Next.
> 2. **Page numbers.** At most seven slots. The first page, the last page, the current page and its neighbours are always shown; skipped pages are a single ellipsis. Nine pages read `1 2 3 4 5 … 9` on page 1, `1 … 4 5 6 … 9` on page 5 and `1 … 5 6 7 8 9` on page 9. The current page is filled with the product accent and is marked as the current page for assistive technology. Prev is unavailable on the first page and Next on the last.
> 3. **Short lists.** With 10 rows or fewer, only the total is shown. The page-size choice appears once there are more than 10 rows, and the numbered pages once there is more than one page. A list with no rows shows no pager; the screen's own empty state speaks.
> 4. **Behaviour.** Choosing a new page size, search, filter, year or department returns to page 1. A page past the end is shown as the last page. The reader's page size is remembered for that screen in their browser. The page is kept when the reader opens a record and comes back.
> 5. **Narrow screens.** The total takes its own line; the page-size choice and the pager sit below it; the numbered pages give way to "Page n of m" with Prev and Next.
> 6. **Where it applies.** Registers and lists. Not small tables on a detail page (line items, amounts, history), which show every row.
> 7. **Accessibility.** The pager is a labelled navigation region. Each page button has a full name ("Go to page 3"). The total is announced when it changes.
> 8. **Control shape.** The pager's buttons and page-size field use the Industry control shape (rectangular, outlined; 6 October 2026 owner decision, built in the shared stylesheet), so the filled current page is the only filled square in the row.

## 3. As built (observations, not rules)

| Item | What exists on 6 October 2026 |
|---|---|
| Component | `kentender_core/public/js/kt_industry/components/TablePager.vue`, published as `kentender_core.industry.mountPager` (`kt_industry_pager.bundle.js`) |
| Styling | Part 7 of the generated `kt_industry_tokens.css`, from `PAGER` in `scripts/industry_design_css.py`. It is **not** in the design pack yet |
| Server arithmetic | `kentender_core/services/paging.py` (`page_of`; default 10; offer 10, 25, 50, 100; clamps a page past the end; ignores a size outside the offer) |
| Adopted by | Departmental Needs; Procurement Requisitions (server-paged); Tenders; Evaluation; Award tasks; Procurement Planning (departmental plans, an annual plan's purchases and ready requirements, a departmental plan's requirements); Procurement meetings (server-paged, replacing "Show more"); the bid portal's Available tenders, My bids and Receipt history; Tender security receipts; Budget version lines and funding activity; Strategy plans and own work; System setup user responsibilities |
| Not paged, on purpose | Detail-page tables (a bid opening's register, criteria, evidence, history), Budget's five-line preview, Technical search, small bounded catalogues (Fiscal years, Procuring entities, Contexts, STD template releases) |
| Developer rule | `AGENTS.md` §6.11 |

### 3.1 Where the build departs from what the owner accepted

1. **The page number is not in the URL.** It was recommended. These screens keep their filters in memory, not in the URL, so a page number in the URL alone would restore page 3 of a list whose filter was lost. The page is instead held by the screen's root and kept across opening a record and coming back; a browser refresh returns to page 1. Putting page and filters in the URL together is a separate change.
2. **Most adopters page in the browser, not on the server.** Only Procurement Requisitions and Procurement meetings are paged by the server. The others already receive their whole list, and Departmental Needs also needs every row for the decision queue and "continue" rows above the table. The pager and its contract are the same; only where the slice is cut differs. Lists that can pass about 100 rows (Tenders, the bid-portal lists, Planning purchases, Budget activity) are candidates to move to the server.
3. **No gate yet** fails when a new table has no pager.
4. **Two screens' copy changed.** The bid portal's count lines ("1 available Tender", "2 records"), Strategy's "Showing 1 of 1 plan", Planning's "n departmental plans" and System setup's "n responsibilities" are now the pager's total, worded with the same nouns.
5. **Not reached live.** Budget's detail tables, Tender security receipts and Planning's annual and departmental plan screens could not be driven with a user that has data on the dev site; they are covered by the existing specs and the shared paging spec only.

## 4. Instruction for Claude Design (to amend the core design)

> Add a table pager to the core Industry design system, matching the behaviour in this proposal's §2, so the design pack owns it and the stylesheet can be regenerated from it.
>
> Draw one pager row beneath a register: total at the far left; "Rows per page" select (10, 25, 50, 100) then Prev, numbered pages and Next at the right. Current page filled with the accent and white text, 2px corners; other pages and Prev/Next as ghost buttons; skipped pages as an ellipsis; a hairline rule above the row. Show these states on one board: first page of nine (`1 2 3 4 5 … 9`), a middle page (`1 … 4 5 6 … 9`), the last page, a list of 10 or fewer (total only), a list that fits one page at 100 rows per page (total and size choice, no numbers), and the narrow layout ("Page 2 of 9" with Prev and Next). Keep class names `kt-pager`, `kt-pager-count`, `kt-pager-size`, `kt-pager-nav`, `kt-pager-page` (modifier `is-current`), `kt-pager-step`, `kt-pager-gap`, `kt-pager-status`, so the existing component keeps working. Do not change tokens, colours or existing component rules.
>
> Deliver the updated pack and a short list of the rules that changed.

## 5. Acceptance criteria for this proposal

Taken from the build's tests, not newly invented: the page window never exceeds seven slots (`table_pager.spec.js`); the register returns one page, the total that matched and a clamped page (`test_paging`, `test_read`); the pager draws only the total for 10 rows or fewer; the page survives opening a record and returning (checked in a browser, 6 October 2026, with a real need and inflated list data).

## 6. Decisions for the owner

1. Fold §2 into the next KT-STD-001 version? Recommendation: yes.
2. Put the page number (and the filters) in the URL for registers? Recommendation: yes, as its own change covering page and filters together.
3. Add a gate that fails when a register has no pager? Recommendation: yes, once most registers have adopted it.

## 7. Not verified

- KT-STD-001 v1.22 was not read in full for this proposal, so the clause's placement, numbering and any overlap with existing component rules are unchecked.
- The baseline register (KT-DOC-CTRL-001) was not consulted; this file is not registered.
- The pager was measured live at 1440px and 560px only, on Departmental Needs and Procurement Requisitions. Screen-reader behaviour was not tested with an assistive technology.
- No Playwright suite was run for the pager.
