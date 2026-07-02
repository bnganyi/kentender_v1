# Planning Hub wiring — deferred follow-ups

Tracked gaps intentionally left out of PP4 hub wiring v1:

| Gap | Doc reference | Status |
|---|---|---|
| Request Revision workflow | Operational Flow §6.5 | No PP2 `Revised` state or API; header action hidden (`show_request_revision: false`) until workflow ticket lands |
| Global toolbar search | hub toolbar + search-and-filter pack | Input disabled; server-side cross-module search deferred |
| Ledger Filter drawer | search-and-filter pack | Button disabled; client filter on plan title/code/entity only |
| Server pagination | hub ledger footer | First page (20 rows) from shell API; full pager UI deferred |
| Tier 1 National tag | hub mock | Omitted unless domain field exists on Procurement Plan |

When implementing follow-ups, extend `planning_hub_view_model.py` and `planning_hub_page.js` — do not add parallel hub loaders.
