# KenTender Statutory and Public-Value Obligations Matrix

**Version:** 1.1  
**Status:** Expanded design baseline for validation  
**Scope:** Strategy, funding, demand, planning, sourcing, purchasing, contract management, receiving, inventory, assets, disposal, complaints and reviews, audit, public disclosure, reporting, risk, integrity monitoring, and supporting platform services  
**Jurisdiction:** Kenya

## 1. Purpose

This matrix establishes how KenTender will convert the governing principles and operative controls of public procurement into system behaviour. It prevents public value, efficiency, sustainability, inclusion and performance from being added as disconnected questionnaires or retrospective analytics.

The matrix distinguishes:

1. **Statutory control (SC):** a mandatory legal or governance control. The system enforces it whenever its legal trigger applies.
2. **Configurable public-value objective (PV):** an approved, measurable objective selected because it is relevant to the organisation, procurement category or specific requirement.
3. **System-derived intelligence (SI):** a measure calculated from workflow, financial, competition, contract or asset data without additional user reporting.

Legal compliance is the operating floor. It is not a competing value objective and must not be traded against cost, speed or convenience.

## 2. Applicability model

| Applicability | Meaning | System treatment |
|---|---|---|
| Universal | Applies to every covered procurement or disposal proceeding | Automatically active; cannot be disabled by the user |
| Triggered statutory | Applies when a legal threshold, method, category, funding, bidder or asset condition is present | Activated by configured rules; override requires authorised legal basis and reasons |
| Organisation-configured | Applies because the procuring entity has approved a strategy, policy or performance target | Available through an approved objective catalogue |
| Procurement-specific | Applies because the approved Value Case makes it relevant and proportionate to the requirement | Selected and approved before tender configuration |
| Derived | Calculated from authoritative system events and transactions | No manual attestation; displayed in operational and analytical views |

## 3. Statutory foundation and constitutional values

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| GOV-01 | Fair, equitable, transparent, competitive and cost-effective procurement | Constitution Art. 227; PPADA s.3 | SC | Universal | All lifecycle modules | Method, access, communication, evaluation and award controls must preserve these principles; material exceptions require reasons and authority | Method justification; publication record; bidder access; responsive bids; evaluation and award history |
| GOV-02 | National values, equality, non-discrimination and protection of marginalised groups | Constitution Arts. 10 and 27; PPADA s.3(a)-(b) | SC | Universal | Strategy, Planning, Tender Configuration, Supplier and Analytics | Prevent unjustified discriminatory requirements; capture applicable inclusion routes; maintain disaggregated reporting where legally required | Requirement justification; participation and award data; complaint and review outcomes |
| GOV-03 | Affirmative action and advancement of youth, minorities and marginalised groups | Constitution Arts. 55 and 56; PPADA s.3(c), ss.155-158 | SC | Triggered statutory | Strategy, Budget, Planning, Tender Configuration, Awards and Analytics | Integrate applicable preferences and reservations into plans and tenders; verify eligibility; apply only the authorised scheme; report performance | Planned allocation; tender scheme; eligibility evidence; award and payment value by beneficiary class |
| GOV-04 | Integrity, professional ethics and conflict control | PPADA s.3(d), ss.62, 65-67; Leadership and Integrity Act | SC | Universal | Identity and Access, Tender Configuration, Bid Submission, Evaluation, Award and Contract Management | Enforce declarations, recusals, confidentiality, separation of duties and protected bid/evaluation access; retain exception history | Conflict declarations; recusals; access logs; confidentiality declarations; prohibited communication events |
| GOV-05 | Prudent and responsible use of public money, openness and fiscal accountability | Constitution Art. 201; PPADA s.3(e) | SC | Universal | Budget, Planning, Demand, Award, Contract and Analytics | Maintain an unbroken link from approved budget to commitment, contract, variations, payment and final cost | Budget line; estimate; award; commitments; variations; payments; final contract value |
| GOV-06 | Efficient, effective and economic use of resources | Constitution Art. 232; PPADA s.3(f) | SC + PV + SI | Universal foundation; targets configurable | Strategy, Demand, Home and Analytics | Require an intended outcome and ownership; calculate process efficiency; allow approved economy and effectiveness targets | Outcome target; cycle times; rework; administrative effort; planned and realised benefits |
| GOV-07 | Professional procurement decision-making | PPADA s.3(g), ss.44-47, 84 | SC | Universal | Governance, Evaluation, Award and Administration | Role and qualification controls, committee appointment, independent evaluation and professional opinion must be recorded | Appointment; membership; qualifications where required; evaluation records; professional opinion |
| GOV-08 | Maximisation of value for money | PPADA s.3(h); National Policy 2020 | SC + PV | Universal principle; measures procurement-specific | Strategy, Demand, Budget, Planning, Evaluation, Contract and Analytics | Define value before sourcing; distinguish price from whole-life value; verify realised value after award | Baseline; market benchmark; total cost; quality/outcome measures; realised benefit |
| GOV-09 | Promotion of local industry and citizen contractors | PPADA s.3(i)-(j), ss.155-158 | SC + PV | Triggered statutory or procurement-specific | Strategy, Planning, Tender Configuration, Evaluation, Contract and Analytics | Apply statutory preferences and any approved, relevant local-value commitments; do not invent unsupported local-content rules | Legal scheme; bidder eligibility; local sourcing or transfer commitment; delivered value |
| GOV-10 | Sustainable development and environmental protection | PPADA s.3(i); National Policy 2020 | SC principle + PV | Procurement-specific except for mandatory disposal controls | Strategy, Demand, Tender Configuration, Contract, Asset and Disposal | Select measurable objectives only where relevant; route each objective to specification, criterion, obligation or reporting; enforce statutory waste controls | Baseline; target; bidder commitment; contract evidence; energy, waste or disposal records |

## 4. Planning, demand and market obligations

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| PLN-01 | Realistic annual procurement plan integrated with the approved budget | PPADA s.53(2), (5), (7)-(10) | SC | Universal | Budget & Funding; Planning | A plan item cannot progress without budget linkage, funding sufficiency, method and required approvals; multi-year items must align to the medium-term framework | Approved budget; funding status; plan approval; annual/multi-year classification |
| PLN-02 | Prevention of excessive or unsupported procurement | PPADA s.53(3) | SC + SI | Universal | Demand Intake; Inventory; Planning | Demand must show quantity basis and consider stock, utilisation, existing assets, repair, reuse, transfer and aggregation before new acquisition | Consumption basis; stock position; asset assessment; demand challenge outcome; avoided demand |
| PLN-03 | Annual asset-disposal planning | PPADA s.53(4); PPADR regs.176-177 | SC | Universal where assets require disposal | Asset Management; Disposal; Planning | Maintain a consolidated approved disposal plan linked to asset records and replacement demands | Asset condition; disposal trigger; departmental and consolidated plan; approval; execution status |
| PLN-04 | Publication of approved procurement plans | PPADA s.53(12)-(13); PPADR reg.50 | SC | Universal subject to publication rules | Planning; Publication | Generate the publishable plan from approved authoritative data and retain publication history | Published version; date; amendments; responsible approver |
| VFM-01 | No artificial splitting of procurement | PPADA s.54(1) | SC + SI | Universal | Demand; Planning; Analytics | Detect related demands by category, unit, time and funding source; require review rather than automatically alleging a breach | Related-demand flags; consolidation decision; reviewer and reasons |
| VFM-02 | Market-informed estimates and prevailing prices | PPADA s.54(2)-(4) | SC | Where market prices or surveys apply | Budget; Planning; Tender Configuration; Award | Record source, date, geography, unit and confidence of market evidence; flag stale or materially divergent estimates and awards | Survey; PPRA index where relevant; estimate-to-market and award-to-market variance |
| VFM-03 | Whole-life cost and benefits case | National Policy 2020 sustainable procurement and value-for-money provisions | PV | Organisation- or procurement-specific | Strategy; Demand; Budget; Evaluation; Contract | Configure cost components by category; do not force lifecycle costing where immaterial; retain assumptions and compare forecast with actual | Acquisition, operating, maintenance, transition and disposal costs; benefit baseline; realised variance |
| MKT-01 | Lawful and justified procurement method | PPADA Part IX, including s.91 and method-specific provisions | SC | Universal | Planning; Tender Configuration | Select method from configured legal rules; record justification, threshold and approval; prevent incompatible tender workflows | Method decision; threshold; justification; approval; changes and reasons |
| MKT-02 | Meaningful competition and market accessibility | Constitution Art.227; PPADA s.3; National Policy 2020 | SC principle + SI | Universal | Planning; Publication; Bid Submission; Analytics | Monitor participation and design risks without treating low participation as proof of misconduct | Invitations/views where available; bids submitted; responsive bids; single-bid rate; repeat failure |
| EFF-01 | Procurement process efficiency | Constitution Art.232; National Policy 2020 | PV + SI | Organisation-configured and derived | All workflow modules; Home; Analytics | Derive stage durations, queue time, returns and duplication from workflow events; optional targets must have owners | End-to-end and stage cycle time; approval returns; overdue work; duplicate submissions |

## 5. Tendering, evaluation and award obligations

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| TEN-01 | Use and controlled configuration of standard tender documents | PPADA s.70 | SC | Where a prescribed STD applies | STD Administration; Tender Configuration | Preserve locked standard text; record authorised variables, additions, source and version; block publication for unresolved mandatory configuration | STD family/version; configuration changes; validation result; approval |
| TEN-02 | Clear, relevant and non-duplicative bidder requirements | Constitution Art.227; PPADA ss.70, 79-80; National Policy 2020 | SC design control | Universal | Tender Configuration; Forms & Evidence; Bid Submission | Every bidder request must map to a tender requirement and evidence source; reuse verified system data; do not recreate electronic declarations as uploads | Requirement-to-form trace; evidence source; duplication check; applicability |
| EVA-01 | Evaluation only against disclosed tender requirements and criteria | PPADA ss.79-80 | SC | Universal | Tender Configuration; Evaluation | Lock published criteria and rules; evaluation consumes the published snapshot; any lawful clarification or correction is separately recorded | Published criterion; evaluator response; scoring/rule application; audit history |
| EVA-02 | Independent, authorised and recorded evaluation | PPADA ss.46, 80; PPADR regs.28-31 | SC | Universal subject to method rules | Evaluation Governance | Appoint committee, enforce independent access, declarations and signatures, and prevent premature access | Appointment; member access; declarations; individual and consolidated results |
| EVA-03 | Due diligence and post-qualification without changing criteria | PPADA s.83 | SC | When used | Evaluation | Due-diligence scope must derive from published qualification requirements; record source evidence and conclusion | Verification request; evidence; site/reference check; signed conclusion |
| AWD-01 | Professional opinion and accountable award decision | PPADA ss.84-86 | SC | Universal subject to method/threshold | Evaluation; Award | Present evaluation recommendation, procurement professional opinion and accountable award decision as distinct records; divergence requires reasons | Evaluation report; professional opinion; decision; reasons; approvals |
| AWD-02 | Transparent notification and reviewability | PPADA award-notification and Part XV review provisions | SC | Universal | Award; Publication; Review | Generate consistent notifications, reasons permitted by law, standstill/review controls and immutable service records | Successful/unsuccessful notices; service timestamps; review request; suspension and outcome |

## 6. Contract, supplier and benefits obligations

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| CON-01 | Contract must reflect the awarded tender and controlled clarifications | PPADA contract-formation provisions, including s.135 | SC | Universal | Award; Contract Management | Generate or verify the contract against the awarded bid and tender snapshot; prevent unsupported post-award obligations | Tender snapshot; awarded bid; clarifications; signed contract; difference report |
| CON-02 | Controlled contract amendments and variations | PPADA s.139; PPADR contract-management provisions | SC + SI | When variation is requested | Contract Management; Budget; Approval | Require legal basis, technical and financial assessment, funding confirmation, cumulative impact and authorised approval before effect | Variation request; basis; cost/time impact; cumulative percentage; approval; contract revision |
| CON-03 | Implementation governance for complex and specialised contracts | PPADA s.151 | SC | Triggered statutory | Contract Management | Establish the implementation team where required and allocate deliverables, risks, inspections, payments and records | Team appointment; plan; milestones; issues; meeting and decision record |
| CON-04 | Ongoing contract monitoring | PPADA s.152 | SC + SI | Universal | Contract Management; Home; Analytics | Produce monitoring from contract data; surface overdue deliveries, quality issues, payment risks, variations and expiring securities | Monthly progress; milestone status; issues; payments; security/warranty dates |
| CON-05 | Receipt, inspection, acceptance and close-out | PPADA ss.48, 154 and 159 | SC | Universal | Inspection & Acceptance; Contract; Inventory | Separate delivery, inspection, acceptance, inventory receipt and payment eligibility; close only with required certificates and unresolved-issue treatment | Delivery; inspection; acceptance/rejection; inventory entry; completion certificate; final account |
| SUP-01 | Supplier performance and consequence management | PPADA performance, termination, debarment and record provisions; National Policy 2020 | SC + SI | Universal where contracts exist | Supplier Management; Contract; Evaluation | Maintain evidence-based contract performance history; distinguish poor performance, dispute, termination and formal debarment | KPI results; defects; notices; remedies; termination; debarment status |
| VAL-01 | Benefits realisation after award | PPADA s.3(h), contract-management provisions; National Policy 2020 | PV + SI | Where the Value Case contains measurable benefits | Contract; Strategy; Analytics | Carry approved targets into the contract plan and compare them with verified results; do not close benefits based solely on self-declaration | Baseline; target; actual; evidence; verifier; variance and corrective action |

## 7. Inventory, asset stewardship and disposal obligations

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| AST-01 | Receipt and recording of accepted goods, works and services | PPADA s.159 | SC | Universal | Inspection & Acceptance; Inventory | Create inventory or asset records only from accepted receipts; preserve links to contract, item, location and custodian | Acceptance; receipt; asset/inventory identifier; custodian; location |
| AST-02 | Prevention of wastage, loss, deterioration and unnecessary stockholding | PPADA ss.160-162 | SC + SI | Universal where inventory/assets exist | Inventory; Asset Management; Demand; Analytics | Track stock, condition, utilisation, inspection and ageing; expose excess, dormant, deteriorating and unaccounted assets | Stock level; consumption; utilisation; condition; inspection; losses; ageing |
| AST-03 | Continuing use, reuse and transfer before replacement or disposal | PPADA ss.160-165; lifecycle-value principle | SC foundation + PV | Asset- and procurement-specific | Demand; Asset Management; Disposal | A replacement demand should identify displaced assets and record repair, reuse, transfer, trade-in or disposal decision | Asset link; condition assessment; option analysis; authorised disposition |
| DSP-01 | Verified, valued and approved disposal decision | PPADA ss.163-164; PPADR disposal provisions | SC | When an asset is proposed for disposal | Disposal | Enforce committee verification, technical report where appropriate, reserve price, method recommendation and accounting-officer decision | Committee; survey; valuation; reserve price; recommendation; approval/rejection and reasons |
| DSP-02 | Lawful disposal method and completion | PPADA s.165 | SC | Universal for disposal | Disposal; Publication; Finance | Limit methods to authorised options; run the required disposal workflow; capture transfer, buyer, proceeds, costs and completion | Method; notice; bids/auction; recipient; payment/proceeds; handover; closure |
| DSP-03 | Licensed handling of radioactive and electronic waste | PPADA s.165(2); Environmental Management and Co-ordination Act | SC | Triggered by waste type | Disposal; Supplier Verification | Block transfer unless handler licensing and validity are verified; retain disposal and environmental evidence | Waste classification; licence; validity; quantities; handover and disposal certificate |
| DSP-04 | Disposal value and environmental outcome | PPADA s.3(i), ss.160-165; National Policy 2020 | PV + SI | Procurement- or asset-category-specific | Strategy; Asset; Disposal; Analytics | Measure reuse, transfer, trade-in, proceeds, disposal cost and compliant waste handling against approved targets | Reuse rate; recovery value; disposal cost; time to dispose; compliant waste rate |

## 8. Transparency, data and system intelligence obligations

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| DAT-01 | Complete procurement and disposal record | PPADA s.68 and related record provisions | SC | Universal | Records Management across all modules | Build the official record from authoritative transactions; preserve versions, actors, timestamps, approvals and reasons | Complete lifecycle dossier; retention status; missing-record exceptions |
| DAT-02 | Appropriate confidentiality and controlled disclosure | PPADA s.67; data-protection and access-to-information law as applicable | SC | Universal | Identity and Access; Publication; Records | Classify data; prevent premature or unauthorised disclosure; publish only authorised fields and versions | Classification; access history; publication rule; disclosure approval |
| DAT-03 | Electronic procurement and digital evidence | PPADA s.64; PPADR e-procurement provisions | SC enablement | Universal where KenTender is used | Platform; all modules | Use durable electronic communications, timestamps, submissions, signatures where applicable and audit evidence; avoid recreating paper artefacts | Submission receipt; timestamp; version/hash; identity; communication record |
| DAT-04 | Operational performance intelligence | Constitution Art.232; National Policy 2020 | SI | Derived | Home; Analytics | Calculate workload, cycle time, overdue action, rework, competition, contract and value indicators from primary records | KPI definitions; source records; calculation version; filters; refresh date |
| DAT-05 | Public and regulatory reporting | PPADA planning, award, preference, contract and disposal reporting provisions; PPADR | SC + SI | Triggered by report type | Publication; Reporting; Analytics | Generate prescribed reports from authoritative data; require review only for exceptions, narrative and lawful redaction | Report dataset; reporting period; approval; submission/publication receipt |

## 9. Complaints, reviews, disputes and audit-support obligations

These case types have different legal effects, deadlines, confidentiality and decision authorities. They shall not be implemented as one generic complaint record.

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| CSE-01 | Administrative complaint and service-feedback handling | National Policy 2020 stakeholder-engagement and dispute-resolution provisions | PV + SI | Organisation-configured | Complaints; Service Management | Receive, classify, acknowledge, assign, respond and close complaints that do not constitute statutory review proceedings; allow reclassification by an authorised officer | Complainant; subject; acknowledgement; assignment; response; closure reason; time to resolve |
| REV-01 | Statutory procurement administrative review | PPADA Part XV, ss.167-175; PPADR review provisions | SC | Triggered by a valid review request | Administrative Review | Record filing, service, affected proceeding, statutory suspension, parties, submissions, hearing events, orders, decision and implementation; calculate legal deadlines from the applicable rule version | Review request; fee/status where applicable; notices; suspension; record transmitted; decision; compliance action |
| REV-02 | Controlled continuation, suspension and implementation of review outcomes | PPADA ss.168, 171 and 173 | SC | Where review proceedings or orders apply | Review; Tender; Evaluation; Award | Freeze only the affected actions; display the legal basis; prevent prohibited progression; route the final order to responsible owners and verify implementation | Suspension scope; affected records; order; assigned actions; implementation verification |
| DSPT-01 | Contract claim management | Contract and applicable dispute-resolution provisions; National Policy 2020 | SC + PV | When a claim arises | Contract Management; Legal | Register notices and claims for payment, time, variation, loss or other relief; preserve contractual notice periods, assessment, recommendation, decision and financial exposure | Claim notice; clause; dates; amount/time claimed; assessment; decision; provision/payment |
| DSPT-02 | Contract dispute and legal proceeding support | Contract terms; applicable dispute-resolution law; National Policy 2020 | SC | When a dispute escalates | Legal; Contract Management | Distinguish negotiation, adjudication, mediation, arbitration and litigation; maintain privileged access, authorities, orders, settlement and enforcement | Dispute stage; counsel/representatives; pleadings/submissions; orders; settlement; financial outcome |
| INT-01 | Integrity allegation and protected referral | PPADA ss.62, 65-66; anti-corruption and whistleblower requirements as applicable | SC | When an allegation or system flag requires referral | Integrity Case Management | Separate allegation from finding; restrict access; preserve evidence; record referral and outcome without exposing protected information in normal procurement views | Allegation source; affected proceeding; evidence manifest; referral; status; authorised outcome |
| AUD-01 | Audit, inspection and investigation support | PPADA oversight, inspection and record provisions, including s.68; National Policy 2020 | SC | When authorised review occurs | Audit Support; Records | Define scope and authority; provide a read-only evidence workspace; preserve source versions; record requests, responses, findings and closure | Authority; scope; evidence index; access log; requests; report; management response |
| AUD-02 | Findings and corrective-action management | PPADA compliance and enforcement framework; National Policy 2020 | SC + SI | When a finding is issued | Compliance; Responsible Business Module | Record finding, severity, source, management response, action owner, due date, evidence and independent verification; prevent self-closure where segregation is required | Finding; response; action plan; overdue status; completion evidence; verifier |
| AUD-03 | Legal hold and extended record preservation | PPADA s.68; archives, audit, investigation and litigation requirements as applicable | SC | Triggered | Records Management | Suspend ordinary disposition for records affected by review, audit, investigation or litigation; preserve integrity and access history until authorised release | Hold authority; scope; custodians; start/release dates; preserved versions; access log |

## 10. Public disclosure and open-contracting obligations

The public portal is a controlled projection of authoritative KenTender records. It is not a separately maintained content system.

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| PUB-01 | Publication of legally required notices and information | PPADA and PPADR publication provisions | SC | Triggered by proceeding and publication type | Publication; Public Portal | Generate publication from approved source records; enforce timing, content, language and channel rules; retain every published and withdrawn version | Source record; approval; publication type; version; timestamp; channel receipt |
| PUB-02 | Open-contracting lifecycle disclosure | National Policy 2020 open-contracting strategy | PV + SI | Organisation-configured, subject to legal publication limits | Public Portal; Open Data | Publish structured planning, tender, award, contract and implementation releases using stable identifiers and documented mappings to authoritative records | OCDS release/package; source links; publication date; version; data-quality result |
| PUB-03 | Confidentiality, privacy and lawful redaction | PPADA s.67; access-to-information and data-protection law as applicable | SC | Universal | Publication; Records; Data Governance | Apply field-level publication classifications; record redaction basis and approver; prevent protected bid, evaluation, personal or commercially sensitive information from leaking | Classification; redaction; legal basis; approver; disclosure/access history |
| PUB-04 | Public search, access and reuse | Constitution Arts.201 and 227; National Policy 2020 | PV | Organisation-configured within publication duties | Public Portal | Provide accessible search, filters, downloads and stable public identifiers; clearly distinguish planned, tendered, awarded, contracted, paid and delivered values | Availability; accessibility; search/download usage; update latency; user feedback |
| PUB-05 | Correction, supersession and withdrawal transparency | Transparency and record-integrity principles | SC design control | Whenever published data changes | Publication; Public Portal | Never silently overwrite a release; publish correction or supersession metadata and retain the public history unless lawful removal is required | Prior/new version; reason; authority; timestamps; withdrawal basis |

## 11. Reporting, analytics, risk and integrity-monitoring obligations

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| RPT-01 | Operational workload and exception reporting | Constitution Art.232; National Policy 2020 | SI | Derived | Home; Work Management | Generate queues for overdue approvals, deadlines, expiring securities, inspections, payments and corrective actions from authoritative dates and states | Source state; due date; owner; age; escalation; resolution |
| RPT-02 | Statutory and regulatory reporting | PPADA and PPADR reporting provisions | SC + SI | Triggered by report type | Regulatory Reporting | Maintain versioned report definitions; generate from transactions; validate completeness; record approval, submission and receipt | Dataset; rule version; exceptions; approver; submission receipt |
| ANA-01 | Management and public-value analytics | PPADA s.3; Constitution Arts.201 and 232; National Policy 2020 | SI | Derived | Analytics | Measure spend, cycle time, competition, inclusion, price, contract performance, inventory, asset, disposal and realised-value outcomes; retain definition and calculation lineage | Metric definition; source; filters; period; calculation version; refresh date |
| RSK-01 | Enterprise procurement and disposal risk framework | National Policy 2020 section on risk management | SC policy control + PV | Universal framework; individual risks conditional | Risk Management; all lifecycle modules | Maintain risk taxonomy, assessment, controls, owners, treatment, residual rating and review; link risks to strategy, procurement, contract, inventory and disposal records | Risk; cause/event/impact; controls; owner; rating; treatment; review history |
| RSK-02 | Transaction and portfolio risk indicators | National Policy 2020 risk and integrity provisions | SI | Derived | Risk Analytics | Detect configured indicators such as potential splitting, repeated direct procurement, low competition, price variance, supplier concentration, unusual timing, excessive variation or asset anomalies | Rule/model version; source transactions; indicator; score/severity; explanation |
| INT-02 | Human review of risk and fraud indicators | Fairness, due process, integrity and accountability principles | SC design control | Whenever an indicator may lead to action | Integrity Monitoring | Treat scores as leads, not findings; require assigned review, supporting evidence, explanation, conflict checks, disposition and referral where warranted | Reviewer; evidence; decision; false-positive reason; referral; review time |
| INT-03 | No automated adverse determination | Constitution Art.227 fairness; PPADA eligibility, evaluation, sanction and debarment procedures | SC design control | Universal | Risk; Evaluation; Supplier; Contract | A score or flag shall not automatically disqualify a bidder, terminate a contract, debar a supplier or establish fraud; action must use the legally authorised process | Flag; human decision; legal route; notice; response opportunity; final determination |
| INT-04 | Integrity-monitoring data safeguards | PPADA s.67 and data-protection requirements | SC | Universal | Data Governance; Integrity Monitoring | Restrict sensitive signals, relationships and allegations; apply retention, purpose limitation, access logging and correction mechanisms | Purpose; data source; access; retention; correction; model/rule governance |
| DQ-01 | Analytical data quality and lineage | Accountability and auditability principles; National Policy 2020 | SC design control + SI | Universal | Data Governance; Analytics | Publish metrics only with defined source, owner, calculation and refresh date; expose missing or stale data rather than inventing values | Completeness; validity; duplication; lineage; last refresh; quality exception |

## 12. Purchasing, ordering and procurement-to-payment obligations

| ID | Obligation or value | Primary anchor | Class | Applicability | System ownership | Required system treatment | Core evidence and measures |
|---|---|---|---|---|---|---|---|
| PUR-01 | Framework agreements, standing arrangements and call-offs | PPADA and PPADR method and framework provisions | SC | Where the configured arrangement is used | Sourcing; Framework Management | Record framework scope, suppliers, ceilings, term, call-off method and ordering controls; prevent orders outside scope or validity | Framework; lots/suppliers; ceiling; call-off rule; utilisation; expiry |
| PUR-02 | Electronic catalogues and authorised requisition-to-order conversion | E-procurement enablement under PPADA s.64 and PPADR | SC design control + SI | Where catalogue purchasing is authorised | Catalogue; Requisition; Purchase Orders | Use approved items, prices, suppliers, budgets and delegations; retain catalogue and price version used for each order | Catalogue item/version; requisition; approval; order; price variance |
| PUR-03 | Purchase order, delivery schedule and amendment control | Contract and financial-control principles | SC | Where an order instrument is used | Purchase Orders; Contract | Generate orders from an approved source arrangement; control quantity, price, delivery and amendment authority; prevent orders beyond funds or contractual ceiling | Source contract/framework; funding; order; amendment; balance; delivery status |
| PAY-01 | Invoice validation and payment certification | Contract, inspection, acceptance and public-finance controls | SC | When payment is claimed | Contract; Receiving; Finance Integration | Match invoice to contract/order, accepted receipt, milestone and applicable deductions; route exceptions for authorised resolution; do not fabricate accounting status | Invoice; order/contract; receipt/acceptance; certification; exception; payment status |
| PAY-02 | Interoperability with public financial-management systems | National Policy 2020 technology and efficiency provisions | SC design control | Where external financial systems remain authoritative | Integration; Finance | Exchange budget, commitment, invoice, payment and reconciliation status using stable identifiers; identify the system of record for each datum | Interface message; source system; acknowledgement; reconciliation; failed transaction |

## 13. Receiving, inventory, asset and disposal boundaries

### 13.1 Required transaction sequence

`Contract/order delivery → physical receipt → inspection → acceptance or rejection → inventory/asset recording → payment certification → custody/use → transfer, replacement or disposal`

The system shall not treat physical receipt as contractual acceptance. Only accepted goods enter available stock or the asset register. Rejected, damaged, short-delivered or quarantined items remain contract exceptions.

### 13.2 Domain ownership

| Domain | Owns | Does not own |
|---|---|---|
| Receiving | Delivery event, quantities presented, delivery documents, temporary custody and discrepancies | Final technical acceptance or asset lifecycle |
| Inspection and Acceptance | Specification, quality and quantity verification; acceptance, rejection, quarantine and corrective action | Stock issue, depreciation or disposal approval |
| Inventory and Stores | Stock locations, balances, batches/serials where applicable, issues, returns, transfers, reservations, adjustments and stocktaking | Capital-asset lifecycle or contract award |
| Asset Management | Identifiable asset register, custody, location, condition, utilisation, maintenance, warranty, transfer, impairment and replacement | Procurement evaluation or disposal committee decision |
| Disposal | Boarding, committee verification, valuation, method, approval, sale/transfer/waste handling, proceeds and closure | Rewriting the source asset history |
| Finance Integration | Commitment, invoice, payment and reconciliation status from the authoritative financial system | Procurement evaluation or physical acceptance |

## 14. Target capability architecture

The following is the comprehensive target capability set. A capability may be a page, workflow, service or integration; it does not automatically require a top-level menu item.

| Domain | Target capabilities |
|---|---|
| Strategy and initiation | Government/entity strategy alignment; public-value objective catalogue; procurement Value Case; budget and funding; demand intake; requisitions; demand challenge; procurement planning; category/spend management; market and price intelligence; strategy and method selection |
| Tender design and sourcing | Tender shell; STD library/version/binding; specifications; requirements and schedules; qualification/evaluation setup; forms and evidence; readiness checks; approvals; publication; clarification/addenda; pre-bid meetings/site visits |
| Supplier and bidder participation | Supplier registration/profile; beneficial ownership and eligibility data; preference/reservation evidence; supplier discovery; opportunity alerts; electronic bid workspace; bid submission/receipt; secure opening; clarifications; bidder communication |
| Evaluation and award | Committee appointment; conflicts/confidentiality; independent evaluation; due diligence/post-qualification; professional opinion; award decision; notification; standstill; contract formation |
| Purchasing and ordering | Framework agreements; standing arrangements; call-offs; catalogues; RFQs; requisition-to-order; purchase orders; delivery schedules; order amendments/cancellation |
| Contract and payment lifecycle | Contract repository; implementation plans; milestones/deliverables/KPIs; securities/insurance/warranties/retention; variations/extensions; claims; disputes; supplier performance; receipt/inspection/acceptance; invoice validation; payment certification/integration; termination; close-out; benefits realisation |
| Inventory and stores | Warehouse/store structure; goods receipt; inspection interface; batches/serials/expiry; stock balances; issues/returns; transfers; reservations; adjustments; reorder controls; stocktaking; reconciliation; excess/obsolete/expired stock; consumption forecasting |
| Asset lifecycle | Asset creation from accepted procurement; classification/identifier; funding/ownership; custodian/location; warranty/maintenance; condition/utilisation; transfer/reassignment; loss/damage/impairment; replacement planning; physical verification; boarding linkage |
| Disposal | Departmental/consolidated plan; asset identification; technical report; committee; valuation/reserve price; approval; tender/auction/transfer/trade-in/waste method; bidder/buyer process; licensed waste handler; proceeds/costs; handover; closure |
| Complaints, review and legal | Administrative complaint; statutory administrative review; suspension/order implementation; contract claim; contract dispute; mediation/arbitration/litigation support; integrity allegation; protected referral; legal hold |
| Assurance and oversight | Internal/external audit; PPRA or authorised inspection; evidence workspace; finding; management response; corrective action; compliance monitoring; sanction/debarment linkage; regulatory reporting |
| Public transparency | Public plans; tender/addenda; cancellation; award; contract/amendment; implementation/completion; disposal notices/results; public statistics; OCDS releases; redaction; correction/supersession; search/download/accessibility |
| Reporting and intelligence | Operational work queues; statutory reports; management reports; spend/category analytics; process efficiency; competition; inclusion/local industry; whole-life cost/value; contract performance; inventory/asset/disposal outcomes; data-quality reporting |
| Risk and integrity | Enterprise risk register; procurement risk assessment; transaction/portfolio indicators; conflict/relationship indicators; duplicate/anomaly detection; risk review; integrity case referral; rule/model governance; false-positive handling |
| Platform governance | Organisations; users/roles/delegations; segregation of duties; committees/professional roles; digital signatures/seals where applicable; rules/thresholds/workflows; master data; records/retention/legal hold; documents/evidence; notifications/escalations |
| Platform operations | APIs/integrations; identity federation; privacy/confidentiality; cybersecurity; encryption/key management; observability; support; business continuity/disaster recovery; accessibility; multilingual support where required; training/guidance; system administration |

## 15. Value-objective enforcement routes

Every procurement-specific public-value objective must be assigned exactly one primary enforcement route and may have supporting reporting routes.

| Route | Intended use | Example | Lock point |
|---|---|---|---|
| Strategic outcome | Organisation or programme result | Reduce service downtime | Approval of Strategy Alignment objective |
| Demand gate | Condition to justify proceeding | Replacement requires asset condition assessment | Demand approval |
| Planning decision | Choice of approach | Aggregate common requirements | Procurement-plan approval |
| Mandatory specification | Minimum delivered characteristic | Energy-performance threshold | Tender publication |
| Preliminary criterion | Mandatory bidder or offer condition authorised by law and the tender | Applicable eligibility evidence | Tender publication |
| Evaluated criterion | Disclosed scored or pass/fail measure | Whole-life cost formula | Tender publication |
| Contract obligation or KPI | Delivery commitment measured after award | Availability, local training or waste take-back | Contract signature |
| Asset or disposal control | Custody, reuse, valuation or lawful transfer requirement | Licensed e-waste recipient | Disposal approval and completion |
| Reporting only | Important observation that should not affect eligibility or award | Process-cycle target | Approved Value Case |

An objective must not silently move from reporting to eligibility, evaluation or contract enforcement after publication.

## 16. Governance and state model

### 10.1 Value-objective states

`Draft → Reviewed → Approved → Available for selection → Selected in Value Case → Translated into procurement treatment → Published and locked → Contracted → Measured → Verified → Closed`

Additional terminal or exception states:

- **Retired:** no longer available for new procurements; historical use remains intact.
- **Not applicable:** considered but excluded with a recorded reason where consideration is required.
- **Superseded:** replaced by an approved version; published procurements retain their original version.
- **Needs corrective action:** measured result is outside tolerance and remains open.

### 10.2 Approval responsibilities

| Decision | Responsible owner | Required reviewers/approvers |
|---|---|---|
| Create or amend organisation objective | Strategy or policy owner | Legal/policy owner; procurement; affected technical owner; authorised approver |
| Select objective for a procurement | Demand owner | Procurement professional; finance where cost-related; technical owner; demand approver |
| Convert objective into tender treatment | Procurement professional | Technical owner; legal/STD owner where required; tender approval authority |
| Publish evaluation or contractual treatment | Tender approval authority | Completion of configuration and readiness validation |
| Change before publication | Assigned configuration owner | Same approval appropriate to materiality; full version history |
| Change after publication | Only through the legally permitted amendment route | Authorised approver; bidder notification and time controls where applicable |
| Verify delivered result | Contract manager or designated verifier | Technical/user acceptance; finance where financial benefit; procurement oversight |
| Verify disposal result | Disposal committee and designated asset officers | Accounting officer approval and environmental/licensing verification where triggered |

## 17. Mandatory system traceability

KenTender shall maintain this chain without manual re-entry:

`Legal/policy source → approved organisational objective → procurement Value Case → demand and budget → procurement plan → tender requirement/criterion → bidder response → award commitment → contract KPI → acceptance/performance result → asset record → disposal result → portfolio reporting`

Each link must retain its source identifier and version. Where no downstream treatment is required, the system records that decision and its reason instead of creating an empty form.

## 18. Initial implementation priorities

### Priority 1 — Foundation

- Establish the obligation and objective catalogues.
- Implement applicability types, source references, versioning and approval states.
- Add the procurement Value Case to Strategy Alignment and Demand Intake.
- Add trace identifiers rather than copying objective text between modules.

### Priority 2 — Upstream value controls

- Budget and whole-life cost baseline.
- Demand challenge, inventory and displaced-asset checks.
- Procurement-plan treatment and method justification.
- Preference, reservation and local-industry applicability.

### Priority 3 — Tender enforceability

- Objective-to-requirement translation.
- Evaluation and evidence mapping.
- Publication lock and immutable evaluation snapshot.
- Duplication prevention across forms and evidence.

### Priority 4 — Delivery and asset outcomes

- Contract KPI and benefit measurement.
- Supplier performance.
- Receiving, inspection, inventory and asset lifecycle operations.
- Disposal planning, valuation, method and environmental controls.
- Purchasing, ordering, invoice validation and financial-system integration.

### Priority 5 — Analytics

- Process efficiency and competition indicators.
- Planned versus awarded versus realised cost and value.
- Inclusion, local industry and sustainability outcomes.
- Contract and disposal performance.
- Complaints, review, audit and corrective-action reporting.
- Explainable risk and integrity indicators with human disposition.
- Public disclosure and open-contracting releases.

Analytics must follow the underlying controls and transactions. It must not be used to compensate for missing lifecycle data.

## 19. Legal and policy sources used

1. Constitution of Kenya, 2010, especially Articles 10, 27, 55, 56, 201, 227 and 232.
2. Public Procurement and Asset Disposal Act, 2015, revised through 2022.
3. Public Procurement and Asset Disposal Regulations, 2020.
4. National Public Procurement and Asset Disposal Policy, 2020.
5. Leadership and Integrity Act.
6. Environmental Management and Co-ordination Act, for licensed handling of applicable waste.
7. Access to Information Act and Data Protection Act, for publication, confidentiality and personal-data controls where applicable.
8. Applicable contract, arbitration, court, archives, audit and public-finance rules for claims, disputes, legal holds, records and financial integration.

This matrix is a product and implementation baseline, not a substitute for legal review. Section references and configured thresholds must be validated against the authoritative versions in force when a rule is released.
