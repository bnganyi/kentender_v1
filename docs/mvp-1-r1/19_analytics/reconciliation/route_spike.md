# ANL-CHG-001 v0.8: route spike and slug check (rows ANL8-0002, ANL8-0003)

Run 5 October 2026 on the test site (`kentender-test.local`, http://127.0.0.1:8001), as Administrator, in headless Chromium (Playwright). Frappe 16.12.0. Nothing was written to the site.

## Question

ANL §9.1 puts `fy`, `dept` and `state` in the URL query, and requires refresh, Back, Forward and a shared link to reproduce the same view. Frappe's `set_route` was read (FU-ANL-14) as dropping the query string. Does it, and what works instead?

## Observed

| Step | Observed (literal) |
|---|---|
| Frappe's own base path | `/desk/home`. Pages open at `/desk/...`; `/app/...` is not the prefix this version writes. |
| `frappe.route_options = {fy:'FY-X', dept:'OU-Y'}` then `frappe.set_route('home','needs')` | URL became `/desk/home/needs`. **The query string is dropped.** `frappe.route_options` kept both keys in memory. |
| `history.pushState(null,null,'/desk/home/needs?fy=FY-X&dept=OU-Y&state=award')` then `frappe.router.route()` | Route parsed as `["home","needs"]`; URL kept the full query. |
| Same push using the prefix `/app/` | Route parsed as `["app","home","needs"]`: wrong. The prefix must be copied from the current URL, not hard-coded. |
| Second push `?fy=FY-Z`, then browser Back | URL and route returned to `?fy=FY-X&dept=OU-Y&state=award`. Forward returned to `?fy=FY-Z`. |
| Reload on `/desk/home/needs?fy=FY-Z` | Same URL and route after reload. |
| `frappe.route_options` after Back and Forward | **Stale keys survive.** After Forward to `?fy=FY-Z` the options read `{fy:'FY-Z', dept:'OU-Y', state:'award'}`: `dept` and `state` came from an earlier entry. |

## Decision (plan D7, FU-ANL-14)

- The Analytics page writes its own history entries: it takes the prefix from `location.pathname` (the first segment, `desk` or `app`), pushes `<prefix>/analytics[/<tab>]?fy=&dept=&state=` with `history.pushState`, then calls `frappe.router.route()`. Parameters that are absent are not written (absent `fy` means All years).
- The page reads the applied filters **only from `location.search`** (`URLSearchParams`), never from `frappe.route_options`, which keeps stale keys across Back and Forward (AGENTS.md §6.4 already says not to rely on it). It reads again on every route change.
- Search text and the paging cursor stay in component state and never enter the URL (ANL §9.1).
- The browser's Back and Forward reproduce the previous view by re-reading `location.search`; a fresh server verdict is read each time.

## Slug check (row ANL8-0003)

Read-only queries on the test site (a copy of the dev site), `lower(name) like '%analytics%'`:

| Table | Result |
|---|---|
| Page | none |
| Workspace | none |
| Desktop Icon | none |
| Workspace Sidebar | none |
| DocType | none |
| Module Def | none |

No Page, Workspace, Desktop Icon, Workspace Sidebar, DocType or Module Def is named for `analytics` on the test site. `Analytics` exists only as an ERPNext stock role (`test_procurement_home_page_roles.py:46`). The dev site itself was not queried; the test site is its copy as of the last rebuild.

## Not done

Console errors during the spike (11, then 2) were Frappe's known dev noise and were not itemised.
