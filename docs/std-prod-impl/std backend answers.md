1.  **Module location:** create a new module:

kentender_procurement/std_engine/

Do **not** extend tender_management. Tender Management should consume STD outputs later.

1.  **Source PDF:** register the PDF on import.

data/DOC 10...pdf → std_source_document

Store filename, source hash, page/anchor refs, and package link. Zip metadata alone is not enough.

1.  **Version diff:** stub single-version UI for Milestone 1.

Do **not** create a fake second STD version yet. Add a later fixture package for Screen 21.

1.  **Usage bindings:** seed minimal read-only bindings from smoke-test expectations.

Mark them clearly as:

fixture_source = "SMOKE_TEST_EXPECTATION"

1.  **Import UX:** start with bench/CLI import, but scaffold HTTP endpoints now.

Required:

POST /std-engine/import/dry-run

POST /std-engine/import/commit

GET /std-engine/import-runs/:id

commit should only import as DRAFT.

1.  **Commit tracker:** yes, add tracker now.

Create/commit:

docs/std-engine/BE_IMPLEMENTATION_TRACKER.md

docs/std-engine/IMPORT_WIRING_PLAN.md

docs/std-engine/MILESTONE_1_VERTICAL_SLICE.md

Final instruction to Cursor:

Start BE-00 with a separate std_engine module, register the source PDF during import, implement CLI import plus dry-run/commit HTTP scaffolding, keep version diff single-version until a real second package exists, seed minimal smoke-test usage bindings, and commit the tracker/docs immediately.

Top of Form

Bottom of Form