# 02 — TDS, Tender Profile, and Invitation Extraction

## Tender profile

| Field | Value | Wizard target |
| --- | --- | --- |
| Procuring Entity | National Social Security Fund Staff Pension Scheme (NSSF SPS) | CFG-01 |
| Tender reference | NSSFSPS/ICT/ERP/001/2025-2026 | CFG-01 |
| Contract name | Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an Enterprise Resource Planning (ERP) System | CFG-01 |
| Procurement method | Open National Competitive Tendering | CFG-01 / CFG-02 |
| Procurement category | Information Technology / ERP System | CFG-01 |
| Closing datetime | 2026-06-30T11:00:00+03:00 | CFG-02 |
| Currency | KES | CFG-02 |
| Professional indemnity | KES 500,000 | CFG-02 / CFG-08 |
| Contact email | pension@nssfsps.co.ke | CFG-02 |

## TDS / SCC rows from source table

| Reference | Item | Extracted value | Target |
| --- | --- | --- | --- |
| ITT 1.1 | Name and identification of the Tender | Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an Enterprise Resource Planning (ERP) System Tender No. NSSFSPS/ICT/ERP/001/2025-2026 | CFG-02 |
| ITT 4.1 | Maximum number of JV members | Three (3) | CFG-02 |
| ITT 8.1 | Pre-Tender Meeting | N/A | CFG-02 |
| ITT 9.1 | Address for clarifications | Trust Secretary/Chief Executive Officer NSSF Staff Pension Scheme Nairobi CBD, Mohktar Doddah Street, Hazina Trade Centre, Podium Floor, P.O. Box 30599-00100, Nairobi, Kenya Email: pension@nssfsps.co.ke\|Website: www.nssfsps.co.ke | CFG-02 |
| ITT 9.1 | Deadline for clarifications | No later than seven (7) days before the tender submission deadline | CFG-02 |
| ITT 12.1 | Currency of tender and payment | Kenya Shillings (KES) | CFG-02 |
| ITT 13.1 | Alternative Tenders | Not permitted | CFG-02 |
| ITT 19.9 | Price adjustment | Not permitted. Prices shall be fixed for the duration of the contract. | CFG-02 |
| ITT 21.1 | Period of validity of Tenders | 154 days after the Tender submission deadline | CFG-02 |
| ITT 22.1 | Professional indemnity | Required – KES 500,000.00 | CFG-02 |
| ITT 23.1 | Number of copies of the Tender | One (1) original and two (2) copies | CFG-02 |
| ITT 25.1 | Tender submission deadline | 30th June 2026 AT 11:00 AM EAT | CFG-02 |
| ITT 28.1 | Tender Opening address, date and time | NSSF Staff Pension Scheme Offices, Nairobi CBD, Mohktar Doddah Street, Hazina Trade Centre, Podium Floor, Nairobi, Kenya, 30th June 2026 11:00 a.m. (EAT) | CFG-02 |
| SCC | Performance Security | 10% of the Contract Price (Bank Guarantee or Insurance Bond, valid through contract period + 60 days) | CFG-09 |
| SCC | Payment Milestones (Phase 1) | 20% upon contract signing and commencement; 30% upon completion of Phase 1 implementation and UAT sign-off; 10% upon Phase 1 post-implementation sign-off three (3) months after Phase 1 go-live. | CFG-09 |
| SCC | Payment Milestones (Phase 2) | Phase 2: 15% upon commencement of Phase 2 implementation following Phase 1 Acceptance Certificate; 15% upon Phase 2 go-live and issuance of Phase 2 Acceptance Certificate; 5% upon Phase 2 post-implementation sign-off three (3) months after Phase 2 go-live; 5% retention released upon expiry of the twelve (12) month Phase 2 warranty period." | CFG-09 |
| SCC | Warranty period | 12 months per phase from date of acceptance. | CFG-09 |

## Normalization decisions

| Source value | Normalized handling |
|---|---|
| Professional indemnity of KES 500,000 | Capture as governed security/evidence variant, not generic tender security. |
| One original and two copies | Preserve as source fact, but electronic-only KenTender submission should replace physical copies. |
| Electronic tenders not permitted | Preserve as NSSF fixture fact; do not apply as platform policy. |
| Payment milestones, warranty, performance security inside TDS table | Normalize into CFG-09 Contract Values. |
