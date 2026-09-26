# STD Configuration retirement — 26 September 2026

Archived by STD-TPL-IMP-001 v1.0 (owner decision OD4, 25 Sep 2026): the
editable STD Configuration module (`std_configuration/`, 27 `STD Cfg *`
DocTypes, 6 `std-cfg-*` Pages), the `Supported Tender Template` registry and
the old `tender_templates/` package, the nine unused STD roles and the stale
Governance & Configuration workspace. The live replacement is the read-only
**STD Templates** module (`kentender_procurement/std_templates`). The patch
`std_tpl_imp_001_retire_std_configuration` removed the database rows and
tables.

`tests/ui/smoke/` also holds browser specs that could no longer run: the
`std-prod-impl/` suite opened the STD Engine pages retired on 5 Sep 2026, and
`procurement/std-module-retired.spec.ts` opened the `std-module-retired`
placeholder page, which no longer exists (follow-up FU-12).
