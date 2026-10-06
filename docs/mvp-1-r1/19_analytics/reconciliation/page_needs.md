# ANL-CHG-001 v0.8 Phase 5: what the page needed that the payload or the charts do not give

Written 5 October 2026 while building the Analytics page. Each row names the workaround the page used at first.

**Update, 5 October 2026 (later): rows 1, 2, 3, 5, 6 and 8 are closed.** The server now sends `register.title`, strip column `has_matters`, month `axis_lines`, cell `quiet`, `charts.by_item.legend` and a `register.state_options` that always includes the applied state, and the page draws them; its heuristics (digit-start test, month label splitting, the "No " mute, legend inference, unit as title) are removed and `Analytics.spec.js` asserts each field. Rows 4 and 7 stay open (below). The rows are kept as the record of what was asked.

| # | Need | Where | Workaround in the page | Ask |
|---|---|---|---|---|
| 1 | A title for the record register ("Tenders", "Requisitions", "Plan items", "Needs", "Departmental plans" on the boards) | `register` | The page draws `register.title` when present, otherwise the area's `unit` with its first letter capitalised. That reads "Tender" for a single Tender and "Plan items in the Active Plan" on Annual planning. | Add `register.title` (plural unit, as the boards draw it). |
| 2 | Whether a strip column's outstanding line has matters (board: hourglass and heading weight) or none (plain quiet text) | `overview.strip.columns[].outstanding` | The page tests whether the sentence starts with a digit. | Add a boolean such as `outstanding_matters`. |
| 3 | Month axis lines ("Jul 2026" two lines, "Jun 2027 (to date)" as "Jun" and "(to date)") | `charts.monthly.months[]` | `axisLinesOf()` splits the server's label and shows the year on the first month and when the year changes. | Add `axis_lines` per month. |
| 4 | A label note beside a Plan item in "Coverage by Plan item" (board: "IT peripherals" then muted "HRMD share") | chart `SegmentedBarRows` rows take a plain `label` string | The page joins `label` and `share_note` with a space, so the note is not muted. | Optional `labelNote` on the chart rows (chart owner). |
| 5 | A muted first line in the Recorded AO outcome cell ("No AO award decision recorded") | `register.rows[].cells` | The page mutes a first line that starts with "No " in that column only. | Add a `quiet` flag per cell. |
| 6 | The legend of "Coverage by Plan item" (Covered / Not yet covered, both shown on the boards even when only one occurs) | `charts.by_item` | The page lists each supplied segment once, in order first met, so a payload with no Not-yet-covered segment shows no such legend entry. | Add `legend` to `by_item`. |
| 7 | The tick labels of the step axis | `steps.axis.ticks` is numbers | The page writes each number as a string. | None unless a unit is wanted. |
| 8 | The selected state offered as an option | `register.state_options` | None. `?state=award` on a site with no Award Tender is accepted by the server (it filters to nothing) but the State select has no Award option, so it shows blank. | State select options should always include the applied state (as `fy_options` and `dept_options` do). |

## Colours the charts do not know

The chart files are final and draw an unknown tone as neutral grey (neutral-400). Mapped in the page's own wrapper (`components/presentation.js`, `boardTone`), from what the boards draw:

| Tone from the payload | Board | Page draws |
|---|---|---|
| `pair-mid` (Partly covered, ANL-DES-21) | `--data-family-2` | family-2 |
| `muted`, Closed (ANL-DES-21, 22) | `--data-cat-5` | cat-5 |
| `muted`, Status unavailable (ANL-DES-31F) | `--color-neutral-400` | the charts' own neutral-400 fallback (no mapping needed) |

The payload and the boards also differ on categorical tones, which is a decision for the server or the design, not the page:

- Tender buckets: boards draw Preparation, Open, Evaluation, Award, Closed with cat-1 to cat-5. The payload sends cat-1, cat-2, cat-4, cat-5 and `muted`. Drawn as sent, Award and a Closed on cat-5 would share a swatch, so the page applies the board's five tones to those five bucket keys (Opening and Sent to Contract Management keep the server's tone; a cat-3 clash is possible if either ever appears).
- Requisitions: boards draw Submitted with cat-3 and Authorised with cat-1; the payload sends cat-1 and cat-2. Drawn as sent.
- Tender monthly series: boards draw Published cat-1, Cancelled cat-5, AO award decisions cat-4; the payload sends cat-1, cat-2, cat-3. Drawn as sent.

## Chart behaviour to note

- `FromZeroBars` takes `halfRange`. The page passes the payload's `timing.span` (the largest number of days in the data), so the longest bar reaches the edge of the track. The board scales to 30 days.
- `RangeStrip` cannot draw a step with no completed events (it needs a median). The page leaves such a step out of the strip; the server's `empty_text` states the all-empty case.

## Observations on the payload

- Resolved: ANL-DES-31F's golden payload now has the fourth outstanding row for 044, "Supply of printers" with "We could not load the current position." and no waiting time. **Deviation from the board and §10A.11**, which say "We could not load the current Award position.": the server's wording is generic because owners do not say which stage failed (decision of the lead, 5 Oct 2026). Registered as a departure in `tests/ui/fidelity/departures/analytics.js`.
