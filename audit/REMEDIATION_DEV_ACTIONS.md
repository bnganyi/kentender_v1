# Dev-site actions the owner must run (code is live on dev at once; schema/patches/seeds are not)

Merged 07 Oct 2026 from audit/progress/*.md.

## INT-A

None. No schema, patch or seed change was committed; the only code change is the canonical seed script (takes effect the next time `seed-canonical` runs on a rebuild or lower stage; it makes that path work again).

## INT-B

None (no migrate, patch or schema change by this worker).

## REGRESS

None from this file. RG-02, RG-13 and RG-20 will each need `bench migrate` on dev when they land.

## WP1.1

- None (no schema, DocPerm, patch or seed change). A normal restart/clear-cache is enough for the Python change.

## WP1.2

No migrate or patch (no schema change). `make seed-canonical` / Budget Playwright fixture resets on dev will use the updated seed callers; old rows are unaffected. The `/api/method/kentender_budget.api.budget_api.{check_funding,reserve_funding,release_reservation,convert_reservation,adjust_commitment,revalidate_reservations}` and `kentender_budget.api.dia_budget_control.release_reservation` routes disappear on the next dev restart/reload.

## WP1.3

- `bench --site kentender.midas.com migrate` (runs `drop_retired_tm2_surface`, syncs the two DocPerm changes and the removed Procurement Journey field `tm2_tender_ref`, which only drops from metadata; the column stays harmlessly). Until then dev keeps the 23 empty TM2 tables and 5 companion doctype records, the `tender-management-v2` Page record and `All` DocPerm on the two publication doctypes; the code for them is gone, so the page route fails to load but nothing else depends on it.
- After migrate: `bench --site kentender.midas.com clear-cache`, restart workers, then hard refresh Desk.
- Not run on dev by me (only read-only SELECT counts).

## WP1.4-1.6

- `bench --site kentender.midas.com migrate` will run the new patch `kentender_suppliers.patches.v1_0.restore_ktsm_roles_and_supplier_code` (re-creates KTSM roles + Supplier.kentender_supplier_code; idempotent; double run tested on the test site).

## WP2.1

- `bench --site kentender.midas.com migrate` (Audit Event DocPerm becomes read-only for System Manager and Administrator; track_changes 0). The controller guard is live on dev as soon as the code is, before migrate; dev seed or Playwright clean-up helpers that called `frappe.delete_doc("Audit Event")` now use `purge_audit_events` (works on dev because `developer_mode` is on, refused over HTTP).
- Test site: migrated already (DocPerm check: 0 write/create/delete rows for Audit Event).

## WP2.2-4.5

- `bench --site kentender.midas.com migrate` (DocPerm: write/create/delete removed from System Manager and Strategy Author for the five Strategy doctypes; doctype JSON `modified` was bumped to 2026-10-07 02:20 so the sync applies). The guard code is live on dev as soon as the code is, before the migrate; any dev seed or script that writes Strategy records directly must use `maintenance_write("Strategy", ...)` (in-process only, dev/test sites).
- Test site: migrated (0 write/create/delete DocPerm rows on the five doctypes at the time of the run).

## WP2.3-3.5-3.6-budget

- `bench --site kentender.midas.com migrate`: doctype sync for the 10 Budget doctypes (DocPerm write/create/delete/share removed; `Procurement Commitment.contract` no longer unique) and the existing patch `bud_chg_001_v1_12_commitment_contract_unique_per_reservation` (drops the table-wide unique index and adds `uq_commitment_contract_reservation`). After migrate check `show index from \`tabProcurement Commitment\``: only the composite unique key plus `contract_index`.
- Budget JS bundle was rebuilt in the shared bench (`sites/assets/kentender_budget/dist/js/budget_funding.bundle.Q2SRQYSM.js`; `public/dist` is git-ignored). Dev needs `bench --site kentender.midas.com clear-cache` and a hard refresh; per the deploy notes restart workers, then clear-cache.
- Seeds were edited (`stamped` stamps in the Budget seeds; `fixture_insert`/`purge_doc` for direct Budget writes and deletes). Run `make seed-canonical-validate SITE=...` after migrating dev; not run by me (see Commands run).

## WP2.6-2.8

- `bench --site kentender.midas.com migrate`: DocPerm (read only) for 25 Requisition/Tender doctypes, User Responsibility Assignment and 8 legacy doctypes; new hooks (`has_permission` / `permission_query_conditions` for 5 Requisition doctypes and Tender Command Journal). No patch. Code (controller guards, removed endpoints) is live on dev as soon as it is deployed, before migrate.
- Dev seed and Playwright clean-up helpers now delete through `purge_doc` / `maintenance_write` (allowed there because `developer_mode` is on, refused over HTTP). The canonical seed run on dev must be run from a shell, not a request.
- Dev may hold Operational Scope Assignment / Workflow Task rows; none were touched. Run `kentender_core.scripts.auth_migration_inventory` before any clean-up (AUTH §11.3).

## WP3.1-3.3

- `bench --site kentender.midas.com migrate` (new doctype Budget Submission Attempt; patch `bud_chg_001_v1_12_commitment_contract_unique_per_reservation` drops the table-wide unique index on Procurement Commitment.contract and adds unique (contract, reservation)). Applied to the test site (before its rebuild from dev, and again by the rebuild); verified table and indexes on the test site.
- After migrating dev, re-run the canonical seed validation (`make seed-canonical-validate SITE=...`): the budget seeds now pass the line's owner as the source unit; not run by me.

## WP3.2-4.3

- `bench --site kentender.midas.com migrate` (owner to run): adds `sent_for_approval_by` and `sent_for_approval_at` to Requisition Version. No data patch needed: existing Versions have no sender recorded, so for those only the preparer rule applies.
- No seed or patch needed in principle: the Requisitions seed profiles and Playwright fixtures prepare with an Author, certify with a Head and authorise with a different HOPF, and test_requisitions_seed / test_requisitions_profiles passed on the test site (13 profile tests are skipped there by their own guard, so the lead's seed-canonical validation on the test site should confirm the full two-year world still builds).

## WP3.4-4.1-award

- `bench --site kentender.midas.com migrate`: adds the `signed_by` Link field to Award Professional Opinion (a doctype schema change, applied on the test site by migrate). Existing signed opinions keep `signed_by` empty; the segregation rule also checks `author`, so they are covered. No patch is needed.
- No seed or patch is required. Check that canonical Award tenders still have funding reservations that Budget can read (they do on the test site copy).

## WP3.5-2.4-2.5

- `bench --site kentender.midas.com migrate` (DocPerm JSON of 14 doctypes: write/create/delete/share removed) then restart workers and clear-cache (hooks.py registers the new scope hooks; the guard and hooks are live as soon as the code is, before migrate).
- Declare Each whole-number on dev: `upsert_departmental_needs()` does it (runs with `make seed-canonical`), or set UOM `Each` `must_be_whole_number = 1`. No patch was added (the UOM catalogue is CFG-owned).
- Any dev-only script or Playwright fixture that saves, inserts or deletes the 14 doctypes through the document API now needs `maintenance_write(<family>, reason=...)` (families `Procurement Planning` and `Departmental Needs`); raw `frappe.db.*` is unaffected. I found and changed: Planning seed clear, canonical clear, Planning/Needs test fixtures. Test site: migrated (DocPerm verified by the tests).

## WP3.6-needs-planning

* `bench --site kentender.midas.com migrate` (owner, later): **Planning Command Journal gains `standing`**. Until it runs, every Planning command on dev fails on the journal insert (unknown column), because the code is already live there. No patch, no data change. Needs has no schema change.

## WP3.6-req-tenders

* `bench --site kentender.midas.com migrate` (owner, later): Tender Command Journal gains a unique index on `idempotency_key`. Before it, on dev: `select idempotency_key, count(*) from \`tabTender Command Journal\` group by idempotency_key having count(*) > 1;` must return nothing (delete the later duplicate rows if it does; they only record replays). No patch, no seed.

## WP3.6-residual

* `bench --site kentender.midas.com migrate` (owner, later): Strategy Command Journal gains `actor` and `payload_hash`; Evaluation Command Journal gains `standing`. No patch, no data change.

## WP4.2-eval

None (no doctype, patch or permission change). Code takes effect on restart.

## WP4.4-tenders

None. No doctype JSON, DocPerm, patch or seed changed; code only.

## WP4.6-planning-needs

- None for code. The DocPerm JSON was already migrated on the test site by WP3.5; dev still needs the WP3.5 `bench --site kentender.midas.com migrate` listed in its progress file, then restart workers and clear-cache. No new migrate, patch or seed from this work.
