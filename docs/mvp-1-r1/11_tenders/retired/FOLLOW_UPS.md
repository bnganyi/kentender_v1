# Tender Publication — outstanding follow-ups

Found 2026-09-11 while implementing the sitewide technical-read rule
(KT-STD-001 v1.5 §3A.6, AUTH-ADR-001 v1.8 §8). This folder had no tracker or
follow-ups file before this entry.

## Register

| ID | Item | Severity | Owner | Status |
|---|---|---|---|---|
| FU-01 | Technical read is now stated once in KT-STD-001 v1.5 §3A.6. At this module's next version: replace TPUB-CHG-001's own technical-read prose, roles-table row wording, Forbidden panel copy and any masking clause's silence about technical readers with a citation of §3A.6; update AUTH-ADR-001 citations to v1.8. | Low | TPUB-CHG-001 owner | Open |
| FU-02 | The legacy `tender_management/tender_publication` code (`kentender_procurement/kentender_procurement/tender_management/tender_publication/`) grants Administrator and System Manager full write and decide authority through Frappe role sets in `publication_authorization.py` — the exact inverse of AUTH-ADR-001 §8 ("read everything, decide nothing"). `_assert_any_role` and the `actorMay*` predicates bypass every check outright for `actor == "Administrator"`. This is legacy, pre-AUTH-resolver code that TPUB-CHG-001's build replaces; left untouched in this cycle. | Medium — inverted authority, but confined to a module already scheduled for replacement | `kentender_procurement` (tender_management, legacy) | Open |
