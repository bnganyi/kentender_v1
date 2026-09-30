# EVL-CHG-001 v0.4: rule reconciliation

| Control | Value |
|---|---|
| Version | 0.4-rules.1 |
| Date | 30 September 2026 |
| Source | The canonical Tender TDR-225970 (TND-MOH-2027-002), published bid definition `PBD-58834afb37a79fee4e2f9946` version 2, template release `stdr-09bbfebd-0297-48c0-8ec2-7aa0c2e64495`; the canonical bid package `BID-MOH-2027-002-001` (Afya Digital Supplies Limited). Dumped by `tools/dump_source.py`, written by `tools/build_rules.py`. |

**Purpose.** Classify every evaluated response of the published definition into one check kind (the draft of `06_runtime/evaluation_rules.json`, plan D7), name its published basis, and state whether a member's evidence assessment is also required (EVL v0.4 §4.2 combined requirement). Comparison values always come from the published definition at run time.

**Check kinds.** `confirmed` declared true · `equals` / `choice-in` permitted choice · `minimum` / `maximum` numeric with the published unit and inclusive boundary · `date-not-before` / `date-not-after` / `date-in-window` · `includes-all` multi-select · `ports-minimum` · `money-equals` exact decimal · `presence` a value exists · `calculation-input` published calculation · `evidence` required files present, content assessed by a member · `review-if-yes` / `review-unless` a disclosure the committee assesses · `manual` no automatic meaning (free text, "or equivalent") · `recorded` shown, not a pass/fail input · `evidence-optional` shown only.

**Counts:** 22 mappings: 19 evaluated, 3 not evaluated (DM-DOC-ACK, DM-SUPPLIER-DETAILS, DM-JV-MEMBER). 154 response rows in the definition.

## Mappings

| Mapping | Group | Treatment | Responses | Published result rule |
|---|---|---|---|---|
| DM-DOC-ACK | — | Not evaluated | 1 | Document acknowledgement is administrative; the Tender documents are incorporated by the Contract Agreement, not by this response. |
| DM-SUPPLIER-DETAILS | — | Not evaluated | 9 | Identity and contact facts are administrative; eligibility is assessed through the declarations and eligibility documents, and the Contract names the awarded Tenderer from its verified identity. |
| DM-JV-MEMBER | — | Not evaluated | 8 | Joint-venture member identity and contact facts are administrative; eligibility is assessed through the declarations and eligibility documents, and the Contract names the awarded Tenderer from its verified identity. |
| DM-DECL-FORM-OF-TENDER | EVG-ELIGIBILITY | Evaluated | 4 | Pass when the Form of Tender is confirmed and item (k) meets ITT 3.8; otherwise fail with the item named. |
| DM-DECL-CITD | EVG-ELIGIBILITY | Evaluated | 3 | Pass when the certificate is confirmed and any disclosed consultation is assessed as not collusive; otherwise fail with the reason. |
| DM-DECL-SD1 | EVG-ELIGIBILITY | Evaluated | 1 | Pass when SD1 is confirmed and the Tenderer is not debarred; otherwise fail. |
| DM-DECL-SD2 | EVG-ELIGIBILITY | Evaluated | 1 | Pass when SD2 is confirmed; otherwise fail. |
| DM-DECL-CODE-OF-ETHICS | EVG-ELIGIBILITY | Evaluated | 1 | Pass when the commitment is confirmed; otherwise fail. |
| DM-DECL-CBQ | EVG-ELIGIBILITY | Evaluated | 17 | Pass when the questionnaire is certified and no unresolved conflict of interest is disclosed; otherwise fail with the item named. |
| DM-RESERVATION | EVG-ELIGIBILITY | Evaluated | 5 | Pass when a valid registration certificate in the published category, valid at the submission deadline, is evidenced; otherwise fail with the reason. Never assessed against the Planning designation alone. |
| DM-TENDER-SECURITY | EVG-ELIGIBILITY | Evaluated | 7 | Pass when a permitted instrument for the published amount and currency, valid to the published expiry date, is evidenced; otherwise fail. |
| DM-GOODS-OFFER | EVG-TECHNICAL-COMPLIANCE | Evaluated | 3 | Pass when a make and model is stated and the offered delivery date is not later than the latest delivery date; otherwise fail with the reason. |
| DM-TECHNICAL | EVG-TECHNICAL-COMPLIANCE | Evaluated | 44 | Each requirement is an individual pass/fail check: pass when compliance is Comply and the offered value meets the published comparison; the group fails if any mandatory check fails, keeping every failed check and its reason. No weight or score. |
| DM-WARRANTY-SUPPORT | EVG-TECHNICAL-COMPLIANCE | Evaluated | 24 | Pass when the confirmation is Yes and the offered warranty is not less than the published minimum; otherwise fail with the reason. |
| DM-EXPERIENCE | EVG-ELIGIBILITY | Evaluated | 12 | Post-qualification GO/NO GO: pass when the published number of comparable contracts, completed within the published period, are evidenced; otherwise fail. |
| DM-ACCEPTANCE | EVG-TECHNICAL-COMPLIANCE | Evaluated | 5 | Pass when the acceptance requirement is confirmed; otherwise fail. |
| DM-EVIDENCE-MANUFACTURER-AUTHORISATION | EVG-ELIGIBILITY | Evaluated | 1 | Post-qualification GO/NO GO: pass when manufacturer authorisation for the offered goods is evidenced; otherwise fail. |
| DM-EVIDENCE-DATASHEET | EVG-TECHNICAL-COMPLIANCE | Evaluated | 1 | Pass when datasheets or brochures supporting the offered goods are evidenced; otherwise fail. |
| DM-EVIDENCE-AFTER-SALES | EVG-ELIGIBILITY | Evaluated | 1 | Post-qualification GO/NO GO: pass when the published after-sales support evidence is provided; otherwise fail. |
| DM-EVIDENCE-ELIGIBILITY-DOCUMENTS | EVG-ELIGIBILITY | Evaluated | 1 | Pass when the documents listed in item 7 of the Tenderer Information Form are evidenced; otherwise fail. |
| DM-PRICE-GOODS | EVG-FINANCIAL | Evaluated | 2 | Arithmetic check and correction under the published rules, then comparison on the lowest evaluated responsive Tender Price. |
| DM-SUBMISSION | EVG-ELIGIBILITY | Evaluated | 3 | Pass when the Tender is signed by a named authorised person; otherwise fail. |

## Evaluated responses

"Current seed" is what the automatic comparison gives on today's canonical bid (see C22); "Ordinary story" is EVL v0.4 §9.12.

| Group key | Requirement | Field | Check kind | Published basis | Evidence assessment | Canonical bid value | Current seed | Ordinary story (§9.12) |
|---|---|---|---|---|---|---|---|---|
| RR-DECL-FORM-OF-TENDER/FORM-TENDER | FORM-TENDER | discounts | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-DECL-FORM-OF-TENDER/FORM-TENDER | FORM-TENDER | state_owned_enterprise | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-FORM-OF-TENDER/FORM-TENDER | FORM-TENDER | commissions_gratuities_fees | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-DECL-FORM-OF-TENDER/FORM-TENDER | FORM-TENDER | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-DECL-CITD/FORM-CITD | FORM-CITD | disclosure | review-unless | "Arrived at the Tender independently" meets; a consultation needs committee assessment |  | Arrived at the Tender independently | Meets | Meets |
| RR-DECL-CITD/FORM-CITD | FORM-CITD | consultation_details | recorded | Shown to members; not a pass/fail input of the published result rule |  | — |  |  |
| RR-DECL-CITD/FORM-CITD | FORM-CITD | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-DECL-SD1/FORM-SD1 | FORM-SD1 | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-DECL-SD2/FORM-SD2 | FORM-SD2 | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-DECL-CODE-OF-ETHICS/FORM-COE | FORM-COE | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | business_structure | recorded | Shown to members; not a pass/fail input of the published result rule |  | Sole proprietor |  |  |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | ownership_details | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | trade_licence | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | maximum_business_value | recorded | Shown to members; not a pass/fail input of the published result rule |  | 0.00 |  |  |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | procuring_entity_interest | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | procuring_entity_interest_details | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_01 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_02 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_03 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_04 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_05 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_06 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_07 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_08 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_09 | review-if-yes | "No" meets; "Yes" discloses a matter the committee must assess (published result rule) |  | Yes | Needs review | Meets |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | conflict_details | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-DECL-CBQ/FORM-CBQ | FORM-CBQ | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-RESERVATION/RESERVATION | RESERVATION | certificate_category | choice-in | In permitted_categories ['Youth'] |  | Youth | Meets | Meets |
| RR-RESERVATION/RESERVATION | RESERVATION | certificate_number | presence | A value is present (presence never verifies authenticity) |  | Seeded answer for the canonical bid. | Meets | Meets |
| RR-RESERVATION/RESERVATION | RESERVATION | certificate_valid_until | date-not-before | Not before submission_deadline_date 2027-06-12 |  | 2027-06-12 |  | Meets |
| RR-RESERVATION/RESERVATION | RESERVATION | certificate_evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-RESERVATION/RESERVATION | RESERVATION | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-TENDER-SECURITY/TENDER-SECURITY | TENDER-SECURITY | security_form | choice-in | In permitted_forms ['Demand Bank Guarantee', 'Insurance Guarantee'] |  | Demand Bank Guarantee | Meets | Meets |
| RR-TENDER-SECURITY/TENDER-SECURITY | TENDER-SECURITY | issuer | presence | A value is present (presence never verifies authenticity) |  | KCB Bank Kenya | Meets | Meets |
| RR-TENDER-SECURITY/TENDER-SECURITY | TENDER-SECURITY | guarantee_reference | presence | A value is present (presence never verifies authenticity) |  | KCB/TG/2027/8841 | Meets | Meets |
| RR-TENDER-SECURITY/TENDER-SECURITY | TENDER-SECURITY | instrument_amount | money-equals | Equals amount 500000 KES |  | 500000.00 |  | Meets |
| RR-TENDER-SECURITY/TENDER-SECURITY | TENDER-SECURITY | bank_guarantee_valid_until | date-not-before (when Demand Bank Guarantee) | Not before 2027-11-09 |  | 2027-11-09 |  | Meets |
| RR-TENDER-SECURITY/TENDER-SECURITY | TENDER-SECURITY | insurance_guarantee_valid_until | date-not-before (when Insurance Guarantee) | Not before 2027-11-07 |  | — |  | Meets |
| RR-TENDER-SECURITY/TENDER-SECURITY | TENDER-SECURITY | security_evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-GOODS-OFFER/GDS-0bccf3841dce92eb483dee3f | Business laptops | offered_make_model | presence | A value is present (presence never verifies authenticity) |  | ApexBook Pro 14 | Meets | Meets |
| RR-GOODS-OFFER/GDS-0bccf3841dce92eb483dee3f | Business laptops | offered_delivery_date | date-not-after | Not after latest_delivery_date 2027-09-30 |  | 2027-09-15 |  | Meets |
| RR-GOODS-OFFER/GDS-0bccf3841dce92eb483dee3f | Business laptops | evidence | evidence-optional | Optional supporting files; shown, not required |  | 0 file(s) |  |  |
| RR-TECHNICAL/TECH-001 | Electrical compatibility | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-001 | Electrical compatibility | offered_value | equals | = Yes |  | Yes | Meets | Meets |
| RR-TECHNICAL/TECH-001 | Electrical compatibility | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-001 | Electrical compatibility | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-002 | New and unused equipment | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-002 | New and unused equipment | offered_value | equals | = Yes |  | Yes | Meets | Meets |
| RR-TECHNICAL/TECH-002 | New and unused equipment | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-002 | New and unused equipment | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-003 | Memory | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-003 | Memory | offered_value | minimum | ≥ 16 GB |  | 0 | Does not meet | Meets |
| RR-TECHNICAL/TECH-003 | Memory | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-003 | Memory | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-004 | Storage capacity | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-004 | Storage capacity | offered_value | minimum | ≥ 512 GB |  | 0 | Does not meet | Meets |
| RR-TECHNICAL/TECH-004 | Storage capacity | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-004 | Storage capacity | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-005 | Storage type | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-005 | Storage type | offered_value | equals | = NVMe SSD |  | NVMe SSD | Meets | Meets |
| RR-TECHNICAL/TECH-005 | Storage type | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-005 | Storage type | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-006 | Display size | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-006 | Display size | offered_value | minimum | ≥ 14.0 inches |  | 0.00 | Does not meet | Meets |
| RR-TECHNICAL/TECH-006 | Display size | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-006 | Display size | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-007 | Battery runtime | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-007 | Battery runtime | offered_value | minimum | ≥ 8 hours |  | 0.00 | Does not meet | Meets |
| RR-TECHNICAL/TECH-007 | Battery runtime | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-007 | Battery runtime | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-008 | Processor requirement | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-008 | Processor requirement | offered_value | manual | Free text against "64-bit business-class processor, minimum 10 cores or equivalent benchma | Yes | Seeded answer for the canonical bid. | Needs review | Meets |
| RR-TECHNICAL/TECH-008 | Processor requirement | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-008 | Processor requirement | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-009 | Operating-system compatibility | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-009 | Operating-system compatibility | offered_value | manual | Free text against "Approved organisational Windows environment": needs a member finding (E | Yes | Seeded answer for the canonical bid. | Needs review | Meets |
| RR-TECHNICAL/TECH-009 | Operating-system compatibility | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-009 | Operating-system compatibility | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-010 | Network connectivity | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-010 | Network connectivity | offered_value | includes-all | Includes ['Wi-Fi 6', 'Bluetooth 5 or later'] |  | ["Ethernet"] | Does not meet | Meets |
| RR-TECHNICAL/TECH-010 | Network connectivity | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-010 | Network connectivity | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-TECHNICAL/TECH-011 | Required ports | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-TECHNICAL/TECH-011 | Required ports | offered_value | ports-minimum | Each port type at least its minimum_count [{"minimum_count": 2, "port_type": "USB-C"}, {"m |  | [{"count": 1, "port_type": "USB-A"}] | Does not meet | Meets |
| RR-TECHNICAL/TECH-011 | Required ports | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-TECHNICAL/TECH-011 | Required ports | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-WARRANTY-SUPPORT/WS-MINIMUM-WARRANTY | Minimum warranty period | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-MINIMUM-WARRANTY | Minimum warranty period | offered_value | minimum | ≥ 36 months |  | 36 | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-MINIMUM-WARRANTY | Minimum warranty period | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-WARRANTY-SUPPORT/WS-MINIMUM-WARRANTY | Minimum warranty period | evidence | evidence-optional | Optional supporting files; shown, not required |  | 0 file(s) |  |  |
| RR-WARRANTY-SUPPORT/WS-ONSITE-SUPPORT | On-site support | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-ONSITE-SUPPORT | On-site support | offered_value | equals | = Yes |  | Yes | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-ONSITE-SUPPORT | On-site support | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-WARRANTY-SUPPORT/WS-ONSITE-SUPPORT | On-site support | evidence | evidence-optional | Optional supporting files; shown, not required |  | 0 file(s) |  |  |
| RR-WARRANTY-SUPPORT/WS-RESPONSE-TIME | Maximum support response time | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-RESPONSE-TIME | Maximum support response time | offered_value | maximum | ≤ 8 hours |  | 4 | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-RESPONSE-TIME | Maximum support response time | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-WARRANTY-SUPPORT/WS-RESPONSE-TIME | Maximum support response time | evidence | evidence-optional | Optional supporting files; shown, not required |  | 0 file(s) |  |  |
| RR-WARRANTY-SUPPORT/WS-MANUFACTURER-SUPPORT | Manufacturer support | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-MANUFACTURER-SUPPORT | Manufacturer support | offered_value | equals | = Yes |  | Yes | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-MANUFACTURER-SUPPORT | Manufacturer support | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-WARRANTY-SUPPORT/WS-MANUFACTURER-SUPPORT | Manufacturer support | evidence | evidence-optional | Optional supporting files; shown, not required |  | 0 file(s) |  |  |
| RR-WARRANTY-SUPPORT/WS-SERVICE-LOCATION | Service location | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-SERVICE-LOCATION | Service location | offered_value | manual | Free text against "Within Kenya": needs a member finding (EVL v0.4 §4.1) | Yes | Seeded answer for the canonical bid. | Needs review | Meets |
| RR-WARRANTY-SUPPORT/WS-SERVICE-LOCATION | Service location | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-WARRANTY-SUPPORT/WS-SERVICE-LOCATION | Service location | evidence | evidence-optional | Optional supporting files; shown, not required |  | 0 file(s) |  |  |
| RR-WARRANTY-SUPPORT/WS-SUPPORT-CONTACTS | Warranty contact, escalation and service-centre details | compliance | equals | "Comply" |  | Comply | Meets | Meets |
| RR-WARRANTY-SUPPORT/WS-SUPPORT-CONTACTS | Warranty contact, escalation and service-centre details | offered_value | manual | Free text against "Supplier to provide escalation and warranty-contact details.": needs a  | Yes | Seeded answer for the canonical bid. | Needs review | Meets |
| RR-WARRANTY-SUPPORT/WS-SUPPORT-CONTACTS | Warranty contact, escalation and service-centre details | comment | recorded | Shown to members; not a pass/fail input of the published result rule |  | Seeded answer for the canonical bid. |  |  |
| RR-WARRANTY-SUPPORT/WS-SUPPORT-CONTACTS | Warranty contact, escalation and service-centre details | evidence | evidence-optional | Optional supporting files; shown, not required |  | 0 file(s) |  |  |
| RR-EXPERIENCE/EXPERIENCE-01 | EXPERIENCE-01 | client_name | presence | A value is present (presence never verifies authenticity) |  | Seeded answer for the canonical bid. | Meets | Meets |
| RR-EXPERIENCE/EXPERIENCE-01 | EXPERIENCE-01 | contract_reference | presence | A value is present (presence never verifies authenticity) |  | Seeded answer for the canonical bid. | Meets | Meets |
| RR-EXPERIENCE/EXPERIENCE-01 | EXPERIENCE-01 | contract_value | recorded | Shown to members; not a pass/fail input of the published result rule |  | 0.01 |  |  |
| RR-EXPERIENCE/EXPERIENCE-01 | EXPERIENCE-01 | completion_date | date-in-window | Between 2022-06-12 and 2027-06-12; 2 qualifying entries required |  | 2022-06-12 |  | Meets |
| RR-EXPERIENCE/EXPERIENCE-01 | EXPERIENCE-01 | scope | presence | A value is present (presence never verifies authenticity) |  | Seeded answer for the canonical bid. | Meets | Meets |
| RR-EXPERIENCE/EXPERIENCE-01 | EXPERIENCE-01 | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-EXPERIENCE/EXPERIENCE-02 | EXPERIENCE-02 | client_name | presence | A value is present (presence never verifies authenticity) |  | Seeded answer for the canonical bid. | Meets | Meets |
| RR-EXPERIENCE/EXPERIENCE-02 | EXPERIENCE-02 | contract_reference | presence | A value is present (presence never verifies authenticity) |  | Seeded answer for the canonical bid. | Meets | Meets |
| RR-EXPERIENCE/EXPERIENCE-02 | EXPERIENCE-02 | contract_value | recorded | Shown to members; not a pass/fail input of the published result rule |  | 0.01 |  |  |
| RR-EXPERIENCE/EXPERIENCE-02 | EXPERIENCE-02 | completion_date | date-in-window | Between 2022-06-12 and 2027-06-12; 2 qualifying entries required |  | 2022-06-12 |  | Meets |
| RR-EXPERIENCE/EXPERIENCE-02 | EXPERIENCE-02 | scope | presence | A value is present (presence never verifies authenticity) |  | Seeded answer for the canonical bid. | Meets | Meets |
| RR-EXPERIENCE/EXPERIENCE-02 | EXPERIENCE-02 | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-ACCEPTANCE/ACC-001 | ACC-001 | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-ACCEPTANCE/ACC-002 | ACC-002 | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-ACCEPTANCE/ACC-003 | ACC-003 | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-ACCEPTANCE/ACC-004 | ACC-004 | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-ACCEPTANCE/ACC-005 | ACC-005 | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |
| RR-EVIDENCE-MANUFACTURER-AUTHORISATION/EVIDENCE-MANUFACTURER-AUTHORISATION | Manufacturer's authorisation | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-EVIDENCE-DATASHEET/EVIDENCE-DATASHEET | Technical datasheets or brochures | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-EVIDENCE-AFTER-SALES/EVIDENCE-AFTER-SALES | After-sales support evidence | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-EVIDENCE-ELIGIBILITY-DOCUMENTS/EVIDENCE-ELIGIBILITY-DOCUMENTS | Eligibility and registration documents | evidence | evidence | At least one file; its content is assessed by a member | Yes | 1 file(s) | Meets (presence); evidence assessment pending | Meets |
| RR-PRICE-GOODS/GDS-0bccf3841dce92eb483dee3f | Business laptops | unit_price | calculation-input | Input to CALC-LINE-TOTAL / CALC-TENDER-TOTAL (exact decimals, scale 2) |  | 160000.00 |  |  |
| RR-PRICE-GOODS/GDS-0bccf3841dce92eb483dee3f | Business laptops | tax_amount | calculation-input | Input to CALC-LINE-TOTAL / CALC-TENDER-TOTAL (exact decimals, scale 2) |  | 6400000.00 |  |  |
| RR-SUBMISSION/SUBMISSION | SUBMISSION | signatory_name | presence | A value is present (presence never verifies authenticity) |  | Mary Wanjiku | Meets | Meets |
| RR-SUBMISSION/SUBMISSION | SUBMISSION | signatory_title | presence | A value is present (presence never verifies authenticity) |  | Managing Director | Meets | Meets |
| RR-SUBMISSION/SUBMISSION | SUBMISSION | confirmed | confirmed | Declared confirmation must be true |  | true | Meets | Meets |

**Kinds used:** calculation-input 2, choice-in 2, confirmed 13, date-in-window 2, date-not-after 1, date-not-before 1, date-not-before (when Demand Bank Guarantee) 1, date-not-before (when Insurance Guarantee) 1, equals 22, evidence 19, evidence-optional 7, includes-all 1, manual 4, maximum 1, minimum 5, money-equals 1, ports-minimum 1, presence 12, recorded 28, review-if-yes 11, review-unless 1.

## Financial

| Price row | Calculation | Inputs | Submitted in package |
|---|---|---|---|
| Business laptops | CALC-LINE-TOTAL | {"quantity": "250", "tax_amount": "RSP-ad948695e30bfda006fba1a0", "unit_price": "RSP-ea299 | 46400000.00 |
| Total Tender Price | CALC-TENDER-TOTAL | {"line_price_row_ids": ["PRC-28c050f621aae797597662e8"]} | 46400000.00 |

No published arithmetic-correction rule, adjustment, preference margin or tie-break is present in the definition. A recomputed total that differs from the submitted total is therefore Needs review with the discrepancy shown, never a corrected amount (EVL v0.4 §4.4). Evaluation adjustments read **None**.

## Findings

1. **The canonical bid is placeholder data (C22).** Many answers read "Seeded answer for the canonical bid.", numeric answers are 0 (memory, storage, display, battery), connectivity is ["Ethernet"], ports are one USB-A, experience contract values are 0.01, every conflict question is "Yes", and the evidence files are 453-byte stand-ins. On this bid the automatic checks give **Not responsive**, which contradicts the ordinary story. The Bid Submission canonical seed must submit the EVL v0.4 §9.1/§9.12 facts before the Evaluation canonical stage can tell that story (Phase 13, BDS tracker addendum).
2. **The hand-off omits the definition identity (C23).** `packages[].bid_definition_id` and `definition_digest` are empty and `definition_version` is 0 in `EV-IN-MOH-2027-002-01`. The package itself carries `tender.bid_definition_id/definition_version/definition_digest`; Evaluation reads those and cross-checks them with `bid_definition.definition_for`.
3. **Free text needs a member.** TECH-008 (processor, "or equivalent benchmark"), TECH-009 (operating system) and WS-SERVICE-LOCATION / WS-SUPPORT-CONTACTS are text; they are `manual` or `presence` with a member finding (C13).
4. **Evidence assessments.** Every required evidence field (reservation certificate, tender security, technical evidence, experience, manufacturer authorisation, datasheet, after-sales, eligibility documents) is a combined requirement: presence is automatic, and a member's evidence finding completes it (EVL v0.4 §4.2).
5. **Debarment.** SD1 "not debarred" has no authoritative external source (EVL v0.4 §2.2); it is `confirmed` plus a member evidence finding.
