# Tender Initiation - STD Binding Layer

Yes. The bridge should be a **Tender Initiation / STD Binding layer** between Planning and Tender Management.

Planning Module

→ Procurement Plan Item

→ Tender Initiation

→ STD Selection & Binding

→ IT STD Configuration

→ Tender Package Generation

→ Tender Management Workflow

**1\. Planning hands over the procurement intent**

The Planning module should not create the tender document. It should provide the approved procurement need.

Planning sends:

procurement_plan_item_id

procuring_entity

procurement_category

procurement_method

estimated_budget

funding source

procurement title

description / scope summary

planned dates

lot/package structure

approval status

Hard rule:

Only approved plan items can initiate a tender.

**2\. Tender Initiation creates the tender shell**

Tender Management creates a draft tender record from the plan item.

Tender

\- tender_id

\- plan_item_id

\- title

\- procurement_category

\- procurement_method

\- procuring_entity

\- estimated_value

\- lifecycle_state = DRAFT

At this point, the tender exists, but no STD is bound yet.

**3\. STD Engine recommends/selects the STD**

Tender Management asks STD Engine:

Which active STD versions are valid for this plan item?

Selection logic:

procurement_category = Information Technology

procurement_method = Open Tender / RFP / etc.

estimated_value

entity type

legal regime

funding source

For IT:

Selected STD family: KE-PPRA-IT

Selected STD version: KE-PPRA-IT-2022-04

But bind only when the STD version is ACTIVE. During current development, use DRAFT only for simulation/testing.

**4\. Create Tender STD Instance**

This is the actual bridge object.

TenderSTDInstance

\- tender_id

\- plan_item_id

\- std_family_code

\- std_version_id

\- package_id

\- lifecycle_state = IN_CONFIGURATION

\- binding_status = DRAFT_BINDING

\- source = PLANNING_INITIATED

This object stores the tender-specific configuration separately from the master STD.

Hard rule:

Tender Management must never copy or edit STD master data.

It only stores configuration values against an STD instance.

**5\. IT STD Configuration fills the tender-specific data**

Now launch the IT Tender Configuration Wizard.

It consumes schemas from the bound IT STD:

TDS parameters

SCC parameters

requirements schema

technical requirements

implementation schedule

system inventory

price schedule schema

evaluation schema

tendering forms

contract output schema

render blocks

validation rules

Planning can prefill some values:

| **Planning field** | **Tender/STD target** |
| --- | --- |
| Procurement title | Tender title / Invitation |
| Procurement method | TDS method field |
| Estimated budget | Budget/control field |
| Planned dates | Procurement timeline |
| Category | STD family selection |
| Scope summary | Initial requirements draft |
| Lots/packages | Lot structure / price schedules |

**6\. Validation before tender workflow advances**

Tender Management asks STD Engine to validate the tender STD instance.

Validation gates:

mandatory TDS complete

mandatory SCC complete

requirements present

price schedules valid

evaluation criteria valid

forms active

render blocks complete

no blocker rules

Only then:

IN_CONFIGURATION

→ READY_FOR_REVIEW

**7\. Generate tender package**

STD Engine renders the tender package.

Output:

tender document bundle

bidder response schema

evaluation schema

contract output schema

publication manifest

bundle hash

Tender Management stores references, not reconstructed content.

TenderGeneratedBundle

\- tender_id

\- std_instance_id

\- bundle_hash

\- render_manifest

\- generated_at

**8\. Tender Management takes over workflow**

Once generated and validated:

Tender Management handles:

\- internal review

\- approvals

\- publication

\- addenda

\- clarifications

\- deadlines

\- opening

But it continues consuming STD Engine outputs.

**Core bridge objects**

Create these before building full tender workflow:

ProcurementPlanItem

Tender

TenderSTDInstance

TenderSTDConfigurationValue

TenderGeneratedBundle

TenderValidationFinding

TenderPublicationReadiness

**Minimal implementation sequence**

1\. Planning → Tender initiation API

2\. Tender shell creation from approved plan item

3\. STD recommendation/selection API

4\. TenderSTDInstance binding

5\. IT STD configuration values

6\. STD validation for tender instance

7\. Render preview

8\. Generate tender bundle

9\. Submit tender for review

**The rule to keep clean**

Planning defines the need.

STD Engine defines the legal/document/schema structure.

Tender Management manages the procurement event lifecycle.

That is the bridge.