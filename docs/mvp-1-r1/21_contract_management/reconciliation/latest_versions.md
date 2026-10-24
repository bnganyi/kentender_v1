# CM-CHG-001 v0.8: latest-version check

| Control | Value |
|---|---|
| Version | 0.8-versions.1 |
| Date | 14 October 2026 |
| Source | `docs/mvp-1-r1/98_work_progress/KenTender_Baseline_Register.yaml` (KT-DOC-CTRL-001, `as_of` 2026-10-12), the document folders, and CM v0.8 §§1, 17.6 (tracker CM8-009; follow-up FU-CM-36) |

CM v0.8 cites the owner documents it was reconciled against. The register is the canonical record of current versions and status; folder files can run ahead of it (a proposed successor) or behind it. **Register versions below are as read from the register on 14 October 2026. Whether each difference changes a CM clause was checked only where stated; the rest is "not checked", not "no effect".** Rule applied (memory: check the latest document version first): the build binds to the register's approved version, and reads the folder's proposed successor only for what it states.

| Document | CM v0.8 cites | Register (approved, `as_of` 12 Oct 2026) | Latest file in folder | Checked effect on CM |
|---|---|---|---|---|
| KT-STD-001 | v1.25 | **1.29** (approved 9 Oct) | v1.29 | v1.26–v1.29 not read in full. v1.28/v1.29 changed field outline `#8590a6`, hover `#6b7690` and the 4px field corner (§2.4); the CM design pack may predate this. **Not verified**; Phase 4 compares computed styles with the live shared stylesheet, not with the board |
| AUTH-ADR-001 | v1.11 | **1.15** (approved 11 Oct) | v1.15 | v1.13 adds a third scope type, **Tender**, for the Tender Security Intake Officer only (header, read). CM uses Site-wide and Organisation Unit only (CM §6.2) and adds no scope type, so CM's rule stands. v1.12 home-unit and v1.15 incident-read audit not otherwise read |
| CFG-CHG-002 | v0.18 | **0.19** (approved 8 Oct) | v0.19 | Not read beyond the register line |
| AWD-CHG-001 | v0.5 | **0.5** (approved 3 Oct) | v0.6 (proposed, 10 Oct) | CM's citation is the current approved version. v0.6 withdraws the test-environment notice and visible labelling of synthetic adapters (header, read); no change to the package contract was read |
| BUD-CHG-001 | v1.12 | **1.12** (approved 3 Oct) | v1.12 | Same. BUD names Contract Management as the contract, variation and cancellation owner (line 104) |
| TPR-CHG-001 | v0.17 | **0.20** (approved 11 Oct) | v0.20 | Not read; v0.20 does not name Contract Management (search) |
| STD-TPL-001 | v0.15 | **0.17** (approved 11 Oct) | v0.17 | Release 1.5 `downstream_rules.json` read (see `package_gap.md`); document body not read |
| BDS-CHG-001 | v0.11 | **0.16** (approved 11 Oct) | v0.16 | Not read |
| PRC-CHG-001 | v0.11 | **0.12** (approved 8 Oct) | v0.12 | Not read |
| EVL-CHG-001 | v0.5 | **0.8** (approved 8 Oct) | v0.8 | Not read; Evaluation is upstream of Award only |
| BOP-CHG-001 | v0.11 | **0.15** (approved 11 Oct) | v0.15 | Not read |
| REQ-CHG-001 | v1.14 | **1.18** (approved 9 Oct) | v1.18 | Not read. REQ source allocations feed CM's funding lineage (CM §5.14); allocation identities per REQ v1.18 to be read in Phase 5 |
| PLN-CHG-001 | v1.29 | **1.31** (approved 9 Oct) | v1.31 | Not read |
| NDS-CHG-001 | v1.16 | **1.17** (approved 9 Oct) | v1.17 | Not read |
| STR-CHG-001 | v1.9 | **1.10** (approved 12 Oct) | v1.10 | Not read |
| TRUST-ADR-001 | v0.1 (read in full by CM) | **0.6** (approved 11 Oct) | v0.6 | §§1–4 read. v0.6 keeps one reusable signing capability owned by a future support module; the interface returns `Unavailable`, `Rejected`, `Indeterminate` and `Accepted/Verified` with one correlation identity and safe retries; "A simulated pass cannot close production requirements" (§4, read); no test notices (§2, read). **Consistent with plan D8.** Item 2 of §1: the owning business module defines who, what, when and which targets; the shared module cannot decide business outcomes |
| TRUST-OPS-001 | not cited | 0.1 (approved 11 Oct) | v0.1 | New since CM v0.7's sources; sealed-bid incident recovery; not CM-related |
| SEED-OPS-001 | v1.19 (CM read targeted sections of an older copy) | **1.24** (register status "Historical provenance"; implementation Implemented) | **v1.25** (folder and two copies; latest commit "SEED-OPS-001 seed runbook v1.25") | The register lags the folder by one version. Seed stage rules for `contracts` are read in Phase 11 |
| LAW-REG-001 | v1.2 | **1.2** | v1.2 | Same |
| OVS-CHG-001 | v0.6 | **0.6** | v0.6 | Same |
| Baseline register | 1 October version | `as_of` 2026-10-12 (36 documents) | — | **CM-CHG-001 has no document entry** (FU-CM-13). Searching the register's interfaces, decisions, delivery items and future work for `Contract Management`, `Contracting` and `CM-CHG` found: **FW-008** (capability Contract Management, "Planned", trigger "Approve contract lifecycle and integration contracts", boundary "Current contract mappings prepare data only"), **IF-019** (Award → Contracting, "Proposed interface", implementation Not started), **DEC-016** (Contract Management among capabilities "explicitly planned future work"; "Do not expose placeholder journeys as current capability"), AWD-001 and OVS-005. FW-008 and IF-019 are the rows the register update must change |

## Conclusions

1. **No owner document applies any §17.10 amendment** (see `seam_register.md`). Every amendment is open and is written against the **current** versions in the table, never against the versions CM cites.
2. **Two things to confirm with the owner when they next revise CM:** the stale citations (FU-CM-36) and the CM register entry (FU-CM-13).
3. **The register's SEED-OPS entry lags the folder (v1.24 vs v1.25).** Not a CM matter; recorded because Phase 11 adds a stage to the runbook.
4. **Not read in Phase 0:** KT-STD v1.26–v1.29 bodies, AUTH v1.12–v1.15 bodies, CFG v0.19, TPR v0.20, STD-TPL v0.17, BDS v0.16, PRC v0.12, REQ v1.18 and SEED-OPS v1.25 beyond their headers and the targeted searches stated above. Each is read in the phase that depends on it (AUTH/CFG in Phase 3, TPR/STD-TPL/AWD in Phases 4–5, SEED-OPS in Phase 11).
