# Verification B (EVL, AWD, HND, NDS, PLN Critical/High)

| ID | Verdict | Note |
|---|---|---|
| AUD-EVL-001 | CONFIRMED | `declaration.py:51-63` + `roster.py:69,78`: a later "No conflict" supersedes the conflict and restores eligibility; no guard. |
| AUD-EVL-002 | CONFIRMED | Qualified conclusion leaves requirement Needs review -> provisional -> `signing.py:70-71` blocks; QUALIFIED outcome unreachable. |
| AUD-EVL-003 | CONFIRMED | Member "Meets" finding resolves a discrepant price requirement (`aggregate.py:99`), bid ranked at submitted total (`comparison.py:63-64`). |
| AUD-AWD-001 | CONFIRMED | Only role-holding gates (`guards.py`, `people.py`); no SoD in Award/Evaluation; SPEC GAP stands (no doc names incompatible actions). |
| AUD-AWD-002 | CONFIRMED | Award reads funding only from the frozen report snapshot; unknown validity does not block `positive_guards`; no Budget re-read. |
| AUD-HND-001 | CONFIRMED | `release` hard-fails, REQ routes refuse consumed handoff, tests un-consume by DB write; owner-tracked as REQ FU-30. |
| AUD-HND-002 | CONFIRMED | Withdrawal check consults one pinned revision's projection; older Active-plan revision ignored. Duplicate of AUD-NDS-002. |
| AUD-NDS-001 | CONFIRMED | Successor acceptance publishes only the superseded event; `current_accepted_events` skips it; Draft entry deleted by `refresh_draft_entries`. |
| AUD-NDS-002 | CONFIRMED | Same root cause as AUD-HND-002; absent projection row reads "Not included". |
| AUD-PLN-001 | CORRECTED | Severity High -> Medium: code claim true, but REQ `authorise.py:112` calls Budget `check_funding` which independently refuses insufficient funds. |
| AUD-PLN-002 | CONFIRMED | Existing hold of another kind is reused; withdrawal requires kind "Withdrawal request"; no other hold release path. |
| AUD-PLN-003 | CONFIRMED | Classification correction never flags a Draft item; the classification-aware check is test-only. |
| AUD-PLN-004 | CONFIRMED | No/ambiguous reservation rule -> `mandatory: False` -> no blocker and "Required allocation met". |

Counts: CONFIRMED 12, CORRECTED 1, REFUTED 0.
