# NSSF PoC Audit

Verdict: **useful PoC, not legally acceptable yet.** It proves the pipeline can generate a large NSSF-based preview, but it also proves the architecture problem Cursor flagged: the preview is still mixing **legal tender document**, **internal PoC notes**, and **electronic bidder workspace instructions** into one PDF.

**What is good**

The PoC now has real value:

| **Area** | **Review** |
| --- | --- |
| NSSF scale | It generated a 41-page preview, not a toy sample. |
| TDS | Most values are now bidder-facing and formatted. |
| Evaluation | Preliminary, technical pass/fail, scored technical criteria, and financial evaluation are represented. |
| Forms | Bidder forms and required fields are surfaced. |
| Price schedule | 22 NSSF-style price lines are present. |
| Requirements | The large ERP requirements matrix is now represented. |

So yes: **this is progress**. It proves the configuration-to-preview pipeline can carry a complex ERP tender.

**Critical blockers**

| **Blocker** | **Example from output** | **Required fix** |
| --- | --- | --- |
| Locked STD text still missing | ITT is still a short generated paragraph, not full official ITT text | Render ITT/GCC from STD Engine, not generated summary. |
| Internal notes leak into PDF | “Source NSSF fact… PoC submission deadline advanced…” appears inside TDS | Move to audit/readiness notes only. Never bidder-facing. |
| Date contradiction | Submission deadline says **30 June 2027**, while source/opening note says **30 June 2026** | Separate source_deadline from demo_submission_deadline; never mix them in tender PDF. |
| Security contradiction | TDS says tender security not required, but professional indemnity KES 500,000 appears in notes/evaluation | Model professional indemnity as a required evidence/security instrument cleanly. |
| Requirement text corruption | Several requirements are visibly truncated: “Hazina Trade Centre, Podium Flo”, “deployed as a fu” | Import/extraction quality gate must block preview if row text is truncated. |
| PDF overuses bidder workspace language | Every requirement repeats “Confirm Yes/No…” and evidence boilerplate | Move response controls to bidder workspace; PDF should state requirements, not render 190 form controls. |
| Price schedule units are wrong | Many rows show Users even for lump sum, monthly cloud, annual fees | Normalize price units and quantities. |
| Forms are summarized | Page 7 lists form fields, but not full legal declaration text | E-forms must preserve declaration wording, not just field names. |

**Main architectural correction**

The PDF should be:

Legal tender document view

The bidder workspace should be:

Electronic completion surface

Right now the PDF is trying to be both. That is why it becomes noisy and legally risky.

**Required split**

| **Output** | **Should contain** |
| --- | --- |
| Tender Preview PDF | Locked ITT/GCC, TDS, evaluation criteria, requirements, schedules, forms, SCC, contract forms |
| Bidder Workspace | Yes/No controls, compliance statements, evidence uploads, price entry, declarations, submit/seal/receipt |
| Audit / Readiness Report | Source overrides, demo deadline changes, extraction warnings, policy conflicts |

**Decision**

**Do not approve this as final.**  
**Do approve it as proof that the next build must separate PDF rendering from bidder workspace rendering.**

Next instruction to Cursor should be:

Stop putting electronic response controls, PoC source notes, demo overrides, and extraction diagnostics inside the tender preview PDF.

Render the tender preview as the legal document only.

Generate the bidder completion controls separately from the same schema in the bidder workspace.

The PoC has added value. It has exposed the exact boundary we needed: **legal document ≠ bidder response UI ≠ audit diagnostics.**

My observations: 1. The locked text issue keeps recurring, and I also flagged it earlier. Instead of just being descriptive, it it prescribe exactly what is required where. 2. I think most of the sections will be more readable in a tabular manner, similar to the NSSF document itself. As an example, the IT requirements are tedious in the preview PDF

You are right on both points.

The current PoC proves the pipeline, but it is still **too loose**. The locked-text issue should no longer be discussed as a “concern”; it needs to become a hard rendering contract. The requirements section also became unreadable because the PDF renders each requirement as a repeated paragraph block instead of a matrix/table, while the NSSF-style source is naturally tabular.

**1\. Locked text: exact prescription**

Cursor must implement these render block types:

| **Render block type** | **Source** | **Editable?** | **Used for** |
| --- | --- | --- | --- |
| LOCKED_STD_TEXT | STD Engine clause library | No  | ITT, GCC, standard legal instructions, standard form text |
| PARAMETERIZED_STD_TEXT | STD Engine text + approved placeholders | Only placeholder values | Invitation, TDS-driven clauses, SCC-driven clauses |
| CONFIGURED_TABLE | Wizard configuration | Yes, before approval | TDS table, evaluation criteria, requirements, price schedules, implementation schedule |
| ELECTRONIC_SCHEMA_REFERENCE | Bidder workspace schema | No PDF controls | Notes that bidders complete responses electronically |
| AUDIT_ONLY | System/readiness metadata | Never bidder-facing | Demo overrides, source notes, extraction warnings |

Hard rule:

The renderer must not generate, summarize, paraphrase, or replace locked ITT/GCC/form legal text.

For locked sections, the renderer may only read approved STD Engine text blocks and insert approved configured values into declared placeholders.

For the current preview, this means:

| **Section** | **Required rendering** |
| --- | --- |
| Instructions to Tenderers | Full locked ITT text from PPRA IT STD |
| General Conditions of Contract | Full locked GCC text from PPRA IT STD |
| Standard forms | Locked form wording from STD Engine, with electronic fields mapped separately |
| TDS | Configured values inserted into allowed TDS structure |
| SCC | Configured contract values inserted into allowed SCC structure |

No more generated ITT paragraph like:

The tenderer shall prepare the tender in accordance with...

That is a placeholder, not legally sufficient.

**2\. Requirements: use tables, not repeated blocks**

The IT requirements should render like the NSSF matrix.

Do **not** repeat this 190 times:

Confirm Yes/No, cite reference pages, and include a compliance statement.

Treatment: Mandatory

Bidder response: Yes/No confirmation

Evidence: ...

Use grouped tables:

| **ID** | **Requirement** | **Treatment** | **Bidder response** | **Evidence / reference** |
| --- | --- | --- | --- | --- |
| GEN-001 | Implementation will be done at NSSF SPS Offices, Hazina Trade Centre... | Mandatory | Yes/No + compliance statement | Reference pages / upload |
| GEN-002 | ERP system shall be built on Microsoft Dynamics 365 Business Central... | Mandatory | Yes/No + compliance statement | Reference pages / upload |

For large sections, render by group:

A. General Requirements

B. Pension Management Requirements

C. General Ledger Requirements

D. Procurement Module

...

Each group gets a compact table. The bidder workspace handles the actual Yes/No controls, text boxes, uploads, and validation.

**3\. Exact instruction to Cursor**

Send this:

Revise the NSSF PoC renderer with the following non-negotiable rules.

1\. Implement render block types:

\- LOCKED_STD_TEXT

\- PARAMETERIZED_STD_TEXT

\- CONFIGURED_TABLE

\- ELECTRONIC_SCHEMA_REFERENCE

\- AUDIT_ONLY

2\. ITT, GCC, and standard legal form text must render only from STD Engine locked text blocks.

Do not generate, summarize, paraphrase, or replace locked legal text.

3\. TDS, SCC, evaluation criteria, requirements, implementation schedule, price schedule, and system inventory must use section-specific table renderers.

4\. Do not render bidder input controls inside the PDF.

The PDF may state that bidders must complete responses in the electronic submission workspace, but Yes/No controls, textareas, evidence uploads, price inputs, validation, submit, seal, and receipt belong only in the bidder workspace.

5\. Render IT requirements as grouped compliance matrices:

columns:

\- Requirement ID

\- Requirement

\- Treatment

\- Bidder response required

\- Evidence / reference required

6\. Render price schedule as a proper table:

columns:

\- Item

\- Description

\- Unit

\- Quantity

\- Currency

\- Bidder completion method

7\. Render evaluation criteria as tables:

columns:

\- Stage

\- Criterion

\- Basis

\- Maximum marks / pass-fail rule

\- Evidence required

8\. Never render audit notes, source exceptions, demo overrides, extraction warnings, or internal field names inside the bidder-facing tender PDF.

9\. If a locked STD section is unavailable, preview generation must fail with a readiness blocker:

"Locked STD text unavailable for \[section\]. Load approved STD Engine text before generating preview."

10\. The bidder workspace must be generated separately from the electronic submission schema and must contain the interactive controls.

**Bottom line**

The next fix is not more content extraction. It is **renderer discipline**:

Locked legal text stays locked.

Configured values render in controlled tables/placeholders.

Bidder controls move to the bidder workspace.

Audit notes stay out of the PDF.

That is the line that makes this legally defensible and readable.

Top of Form

Bottom of Form

Top of Form

Bottom of Form