# OVS-CHG-001 v0.6: acceptance map (Phase 0, OVS6-0005)

Criteria are copied by script from `KenTender_OVS-CHG-001_System_Usability_and_Decision_Visibility_v0_6.md` section 15 (18 rows). The phase and proof columns are this plan's, not the spec's. "Proof" names what will be observed; test module names are assigned when each phase starts.

| AC | Criterion (verbatim) | Phase | Proof planned |
|---|---|---|---|
| OVS-AC-001 | For each in-scope module, an authorised user can find active and historical records by business reference/title and return to the same register position | 8, 11 | Register search and return position per module; the meetings register |
| OVS-AC-002 | Submission, completion and hand-off update tasks without removing the authorised record, its decision, reasons or evidence | 2, 11 | Evaluation keeps record after hand-off; per-module task/record rule |
| OVS-AC-003 | Record views distinguish current state, recommendation, opinion, final decision and recorded financial/acceptance events | 3, 7, 11 | Record views label recommendation, opinion, decision and financial events |
| OVS-AC-004 | AO/HOPF without committee appointment see only the defined administrative Evaluation facts before delivery, across all endpoints and downloads | 2 | Leakage test: AO, HOPF (not secretary/recipient) before delivery, every endpoint and download |
| OVS-AC-005 | After delivery they see the report and full defined supporting record, including uncited evaluated documents, without impersonation or appointment | 2, 6 | Delivered-version projection incl. uncited evaluated documents |
| OVS-AC-006 | Return and new correction work neither alter the old delivered projection nor expose unfinished findings/evidence; corrected delivery retains earlier versions | 2, 6 | Returned/correction cases keep the delivered projection |
| OVS-AC-007 | Existing committee, secretary and operational access/actions remain intact; oversight access alone grants no decision power | 2 | Committee, secretary and recipient regression |
| OVS-AC-008 | A department head sees relevant progress, disclosed outcomes and outstanding obligations, including authorised contributor relationships, but no unrelated departmental records | 3, 10 | Department head scope incl. contributors; unrelated department negative |
| OVS-AC-009 | Permission revocation takes effect on subsequent reads/downloads; cached content and search suggestions do not leak across users/scopes | 2, 10 | Revocation on next read and download; cache and suggestion scoping |
| OVS-AC-010 | Stage summaries respect each owner's disclosure rule; omitted stages and failed authorised stages are distinguishable without leaking protected existence | 3 | Omitted stage vs failed authorised stage |
| OVS-AC-011 | Existing personal actions are reachable from the record; observer information creates no duplicate task, approval or notification | 2, 3, 6 | Reads create no task, approval, notification |
| OVS-AC-012 | Meeting counts match §11 for ongoing, aborted, Not held, contributor, date-filter, pagination and partial-failure cases | 4, 8 | Counting test and partial-failure case |
| OVS-AC-013 | A standalone signed contract remains usable without Tender/Award modules or fabricated upstream records | 13 | Deferred (Contract Management) |
| OVS-AC-014 | Contract/payment views display authoritative source states and do not equate invoice approval, credits or liability with confirmed cash settlement | 13 | Deferred (Contract Management) |
| OVS-AC-015 | Supplier users see their own permitted work/history and no competitor or internal committee content | 11 | Supplier surfaces: own history only |
| OVS-AC-016 | Keyboard, focus, zoom, error recovery, duplicate-submit prevention and back/refresh journeys work on the representative surfaces in §14 | 6, 7, 8, 9 | Keyboard, focus, zoom, error recovery, duplicate-submit, back/refresh |
| OVS-AC-017 | Cancellation, suspension, expiry, no bids and no current recommendation produce accurate outcomes and a useful route onward | 2, 6 | Cancellation, suspension, expiry, no bids, no current recommendation |
| OVS-AC-018 | Every applicable module has a recorded usability coverage result; an exclusion has a specific reason and owner, not a silent omission | 11 | Module coverage checklist |

Rows OVS-AC-013 and OVS-AC-014 are deferred with Contract Management on 3 October 2026 and count toward no readiness claim.

The spec's own note applies: "These IDs replace the proposed v0.2 acceptance list; reconciliation must update references to that list rather than retaining conflicting meanings." The retired OVS v0.1 draft (`../retired/`) used OVS-AC-001–024 with different meanings and is not a source for any row here.
