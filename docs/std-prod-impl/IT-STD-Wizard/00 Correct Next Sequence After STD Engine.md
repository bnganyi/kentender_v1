# Correct Next Sequence After STD Engine

Before moving fully into generic Tender Management, do these two bridge steps:

1\. IT Tender Wizard

2\. NSSF ERP sample tender configuration

3\. Then Tender Management integration

**Step 1 — Finish STD Engine as usable source**

The STD Engine must expose the IT STD as:

Active/usable template candidate

schemas

rules

forms

requirements structure

evaluation structure

price schedule structure

render blocks

validation APIs

This gives Tender Management something real to consume.

**Step 2 — Build the IT Tender Wizard**

The IT Tender Wizard is the **configuration layer** for one tender using the IT STD.

It should create:

TenderSTDInstance

TenderSTDConfigurationValue

IT requirements

implementation schedule

system inventory

price schedules

evaluation setup

TDS values

SCC values

forms/evidence activation

render preview

validation findings

This is the missing bridge between “STD template exists” and “actual tender exists.”

Do this before broad Tender Management because it proves how a tender document is actually assembled from the STD.

**Step 3 — Configure the NSSF ERP tender as the sample**

Use NSSF ERP as a **calibration tender**, not as the master STD.

Purpose:

Prove that a real complex IT tender can be represented using the IT STD wizard.

It should test:

ERP module requirements

technical compliance matrix

implementation phases

payment milestones

professional indemnity

warranty/support

evaluation scoring

price schedules

contract carry-forward

Output should be:

NSSF ERP TenderSTDInstance

validated configuration

rendered tender preview

bidder response schema

evaluation schema

contract output carry-forward map

This becomes your gold sample.

**Step 4 — Then build Tender Management bridge**

Once the IT Wizard and NSSF sample work, build the broader flow:

Planning item

→ Tender shell

→ STD selection

→ IT Tender Wizard configuration

→ validation

→ tender package generation

→ tender approval/publication workflow

**Why this order is better**

If you build Tender Management first, it will be too abstract and will start inventing fields already owned by STD Engine.

If you build the IT Wizard first, you force the right boundary:

STD Engine owns structure.

IT Wizard owns tender-specific configuration.

Tender Management owns procurement event workflow.

Planning owns procurement intent.

**Practical next artifacts**

Create these next:

IT_Tender_Wizard_Final_PRD

IT_Tender_Wizard_Domain_Model

NSSF_ERP_Tender_Instance_Mapping

NSSF_ERP_Sample_Data_Package

Tender_Management_Bridge_PRD

Planning_to_Tender_STD_Binding_Contract

**Final recommendation**

Do **not** jump straight from STD Engine to full Tender Management.

The right path is:

STD Engine

→ IT Tender Wizard

→ NSSF ERP sample tender

→ Planning-to-Tender bridge

→ Tender Management workflow

→ Supplier response

→ Evaluation

→ Contract formation

That gives you a real, testable procurement chain instead of a generic workflow shell.