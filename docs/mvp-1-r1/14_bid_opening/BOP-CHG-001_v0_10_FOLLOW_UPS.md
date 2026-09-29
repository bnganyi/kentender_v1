# BOP-CHG-001 v0.10: outstanding follow-ups

| Control | Value |
|---|---|
| Version | 0.10-follow-ups.2 |
| Date | 29 September 2026 |
| Status | Open register |

This register holds items found while planning BOP-CHG-001 v0.10 and its shared Proceedings service (PRC-CHG-001 v0.9). They include corrections owed to other documents, gaps in sibling contracts, capabilities with no provider on this bench, and production-gate items. Nothing here blocks this module's own build unless a row says so. **Status:** opened 29 September 2026 at Phase 0.

**Predecessor:** none. This is the first Bid Opening follow-up register.

## 1. New in v0.10

| ID | Item | Severity | Owner | Status |
|---|---|---|---|---|
| FU-BOP-01 | BOP-CHG-001 v0.10 is Proposed (line 7) and the boards are drawn against it. It was authored from the pre-approval v0.9 draft, so it reverts approved v0.9 text in these rows:<br>• Governing standard: "KT-STD-001 v1.9" against v0.9 "KT-STD-001 v1.10".<br>• Shared service: "v0.9 proposed coordinated contract" against "v0.9 approved coordinated contract".<br>• BOP v0.10 §5: the timed kind is "proposed for KT-STD-001 v1.10 §2.9.1" against "approved KT-STD-001 v1.10 §2.9.1".<br>• BOP v0.10 §17: the same reversions for PRC and KT-STD-001.<br>• BOP v0.10 §18: v0.9's approval effect is retained as "Approval of this proposed v0.9".<br>• BOP v0.10 §19 and BOP v0.10 §20: the v0.8 and focused-review accounts.<br>v0.10 needs a successor built from approved v0.9 plus the four v0.10 changes, then owner approval. Evidence: `reconciliation/v0_9_to_v0_10_diff.md`. | High — spec | Project Owner | Closed 29 Sep 2026: v0.10 approved by the Project Owner with approval references reconciled (tracker BOP10-005). (0.10-follow-ups.1 read: Open. It does not block Phases 1–7 (OD-A). Phase 8 boards c2c, c2d, h4, h5 and n2 are built to v0.10 on OD-A.) |
| FU-BOP-02 | TRUST-ADR-001 v0.1 is cited as approved (BOP v0.10 line 7 and BOP v0.10 §17; PRC v0.9 lines 7 and 24), but no file exists in the repository. Plan D4, D5 and D6 build only to the semantics quoted in BOP and PRC. | High — spec | Project Owner | Closed 29 Sep 2026: TRUST-ADR-001 v0.1 supplied in `00_common/`; plan D15–D17 record its effect. (0.10-follow-ups.1 read: Open) |
| FU-BOP-03 | The baseline register (`as_of` 2026-09-26) has:<br>• no entries for BOP-CHG-001, PRC-CHG-001 or TRUST-ADR-001;<br>• KT-STD-001 at v1.9 and TPR-CHG-001 at v0.12;<br>• FW-001 still "Planned";<br>• IF-011 "Not started".<br>The file `KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_10_proposed.md` says "Approved" in its control table but keeps `_proposed` in its name. The register's BDS-CHG-001 implementation status ("Planned") also disagrees with the BDS v0.8 tracker (G00–G13 passed). | Medium — register | Documentation owner | Closed 29 Sep 2026: register refreshed (`as_of` 2026-09-28) with BOP, PRC, TRUST and KT-STD-001 v1.10 entries. Residual: the register does not yet list the proposed KT-STD-001 v1.11 (see FU-BOP-08). (0.10-follow-ups.1 read: Open) |
| FU-BOP-04 | No page renderer exists. BOP v0.10 needs a derived page count, price and change locations, and minutes pages (BOP v0.10 §7 OpenNextTender, SelectOpeningTargets). Plan D5 builds a default wkhtmltopdf renderer. Whether it is the "approved rendering" (BOP v0.10 §7 OpenNextTender) is an operating-profile question. | Medium — production gate | Project Owner | Open |
| FU-BOP-05 | BDS offers no published read or acknowledge service for `Bid Opening Handoff`, and no reveal or multi-person custody operation on the tender box. Plan D4 adds `bid_submission/services/opening_gateway.py` as an additive BDS seam. It needs a BDS tracker addendum row and a note in the next BDS-CHG-001 revision. | Medium — cross-module | BDS owner | Open |
| FU-BOP-06 | `cancel_tender` emits `TenderCancelled` with no downstream consumer, and TPR-CHG-001 v0.13 offers no post-close cancellation (BOP v0.10 §10.7). The cancelled-after-start branch (BOP-N18, PRC-N09, board c12) can only be exercised through a simulation-only owner event until TPR-CHG-001 v0.14 is approved and built. Plan D8 adds a `bid-opening` outbox consumer to Tenders cancellation. | Medium — cross-module | Tenders owner; Project Owner (TPR v0.14) | Open |
| FU-BOP-07 | The pre-opening physical-security visibility exception depends on BDS-CHG-001 v0.9, which is proposed and not in the repository (BOP v0.10 §3). Until it is approved, no pre-opening physical-security fact is shown to PE opening users. | Low — spec | Project Owner | Open |
| FU-BOP-08 | Jane Wanjiku (public observer, BOP v0.10 §10) is not in KT-STD-001 §8.3. Request that she be added there, with her email domain, before the Phase 10 seed creates her. Also confirm the Opening access support holder: plan D11 uses Daniel Otieno from BDS plan D13, who is not in KT-STD-001 §8.3 either. KT-STD-001 v1.10 §8.3 registers a different Daniel, Daniel Rotich, `daniel.rotich@moh.example.test`, with role "Statutory approver, in the entity's configured route" (line 586), so BDS's Daniel Otieno reuses a registered first name with a different surname. Decide whether to register him, rename him, or name another holder; plan D11 keeps BDS's existing persona until then. | Low — standard | KT-STD owner | In progress 29 Sep 2026: owner instructed "Register Daniel Otieno" and "Add Jane Wanjiku"; drafted as KT-STD-001 v1.11 (Proposed). Needs Project Owner approval and a register entry before Phase 10 seeds them. (0.10-follow-ups.1 read: Open) |
| FU-BOP-09 | Departure: BOP v0.10 §13 and BOP-A16 require stand-in verification in an isolated deployment. OD-C runs it on the dev site behind `kt_bds_simulation_environment`. Record this in the next BOP revision, or reverse it before any production claim. | Medium — spec | Project Owner | Open (accepted departure, OD-C) |
| FU-BOP-10 | Presence needs a live session (BOP v0.10 §5), but socket.io is not served on this bench. Plan D7 uses a polling heartbeat, and its lapse timeout is an operating-profile input with a 60-second simulation default. Production needs the approved mechanism and timeout. | Medium — production gate | Project Owner | Open |
| FU-BOP-11 | BOP-A17 requires the future Evaluation appointment guard to call `is_excluded_from_evaluation(tender, user)`. The Evaluation change unit must name this read. | Low — cross-module | Evaluation owner (future) | Open |
| FU-BOP-12 | `Evaluation Handoff` is emitted `Pending` with consumer `evaluation`, and nothing consumes it (BOP-A10: "its uptake remains future Evaluation scope"). A new register interface row is needed alongside IF-011. | Low — register | Documentation owner | Open |
| FU-BOP-13 | The committed drafts `13_proceedings/KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_1.md` and `…_v0_2.md` are deleted in the working tree, but PRC-CHG-001 v0.9 line 10 says "v0.1 accepted scope remains historical evidence". The Bid Opening Phase 0 commit leaves those deletions unstaged. | Low — document control | Project Owner | Open |
| FU-BOP-14 | TRUST-ADR-001 v0.1 line 9 lists consumers "BOP-CHG-001 v0.1; PRC-CHG-001 v0.2"; the current consumers are BOP-CHG-001 v0.10 and PRC-CHG-001 v0.9. The register entry already notes "update by a later controlled revision". | Low — spec | TRUST owner | Open |

## Verifying a fix

- **FU-BOP-01** closes when a successor BOP version, built from approved v0.9 and containing the four v0.10 changes, is approved; the tracker authority line then points at it.
- **FU-BOP-02** closes when TRUST-ADR-001 is committed, and plan D4, D5 and D6 have been checked against it.
- **FU-BOP-03** closes when the register has BOP, PRC, TRUST and KT-STD-001 v1.10 entries and `register_check.py` passes.
- **FU-BOP-04** closes when the operating profile names the renderer, or approves D5's.
- **FU-BOP-05** closes when the BDS tracker addendum row is Done and the BDS document records the seam.
- **FU-BOP-06** closes when TPR-CHG-001 v0.14 is approved and the c12 branch passes through a real Tenders cancellation.
- **FU-BOP-07** closes when BDS-CHG-001 v0.9 is approved, or its exception is withdrawn.
- **FU-BOP-08** closes when KT-STD-001 §8.3 lists Jane Wanjiku and the support holder.
- **FU-BOP-09** closes when the owner records the departure in a BOP revision, or the stand-in runs move to an isolated site.
- **FU-BOP-10** closes when the operating profile sets the presence mechanism and timeout.
- **FU-BOP-11** and **FU-BOP-12** close when the Evaluation change unit consumes both.
- **FU-BOP-13** closes when the owner either restores the two PRC drafts or records their removal.
- **FU-BOP-14** closes when a TRUST-ADR-001 revision names the current consumers.
