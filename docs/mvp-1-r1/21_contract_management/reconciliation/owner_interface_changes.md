# CM-CHG-001 v0.8: owner-interface changes (CM8-515 to CM8-518, CM8-521)

| Control | Value |
|---|---|
| Version | 0.8-owner-interface.1 |
| Date | 15 October 2026 |
| Status | Record of what Phase 5 built in each owning module and what each owner still has to do. **No owner document has been changed, approved or marked verified by writing this.** The successors under the document-change protocol (AWD, TPR, STD-TPL, EVL, BUD, CFG) are not written (FU-CM-82); this file is what they will be written from. |

Every change is **additive and read-only** unless it says otherwise: no rule, record, screen or command of the owner changed. Each is read back through the core seam (`kentender_core.services.contract_source_contract` for sources, `contract_funding_contract` for funding) so Contract Management imports none of them.

| Owner | Built (additive) | Where | Still needed from the owner |
|---|---|---|---|
| Core | `handoff(award_case)` and an optional `references(award_case)` on a source provider; a provider may say why it cannot supply a source (`unavailable`) | `contract_source_contract.py` | none |
| Core / CFG | `Site Procuring Entity.pe_address` (Small Text), read once for the entity's principal address | `site_procuring_entity.json` | record the address; expose it in System setup (FU-CM-72) |
| Award (AWD) | A provider of `S<n>-<award case>` for twelve sources; the package carries `managing_unit` and `handoff`; the notification's identity and digest, the earliest signing instant from Award's own minimum-wait clock, the window's end from the tender's validity | `award/services/contract_sources.py`, `eligibility._content` | send a "restriction lifted" update (FU-CM-73); decide the reading of the signing window's end (FU-CM-83); the allocation of an award over several reservations (FU-CM-71); Award's tracker addendum |
| Tenders (TPR) | `contract_seam.py`: the issued instance and its addenda (S1), the schedules with the addendum applied (S4), the commercial values the officer decisions state (S5), typed technical criteria and untyped acceptance checks (S6), the issued Form No. 4 byte for byte (S7); `tender_facts` carries the requesting unit | `tenders/services/contract_seam.py`, `award_seam.py` | type the advance, remedies, termination and change terms or declare them text (FU-CM-75); type the acceptance checks (FU-CM-76) |
| Template release (STD-TPL) | none | | **Declare the insertions of Form No. 4** (which blank is the agreement date, the supplier, the goods, the signatories) and ship the renderer conformance evidence (FU-CM-70, CM-TPL-01) |
| Bid Evaluation (EVL) | `contract_seam.py`: the accepted offer's identity and clarifications (S2), the priced lines from the frozen report (S3) | `bid_evaluation/services/contract_seam.py` | none |
| Bid Submission (BDS) | none | | decide whether the accepted offer's bytes may be released after award (FU-CM-80) |
| Budget (BUD) | `contract_funding_provider.py`: converts a formed agreement's allocations with `convert_reservation`; the one gateway that mints the Contract Management principal (the mint-scan test names it) | `kentender_budget/services/contract_funding_provider.py` | real reservations in the seed world; allocation of an award over several reservations (FU-CM-71); `revalidate_reservations` before signing (FU-CM-81) |
| Supplier Accounts | none (the existing seam `find_active_account`, `organisation`, `organisation_signatories` is used as it is) | | a search source if a verified-supplier picker is wanted (FU-CM-77) |

**Version numbers.** None is assigned here: each successor takes its number from the baseline register at the time it is written (document-change protocol, Step 0).
