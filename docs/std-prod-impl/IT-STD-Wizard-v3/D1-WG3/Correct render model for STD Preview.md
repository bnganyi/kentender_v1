# Correct render model for STD Preview

As a practical note for Cursor implementation, and which ties in to the beginning of the STD config where we pulled out sections from the PDF, how to generate this preview?

Generate the preview from the **structured STD package + tender configuration data**, not by editing the original PDF.

The PDF/DOC was only the **source used to extract and seed the STD Engine**. Once extracted, the preview should be rendered from canonical structured records.

**Correct render model**

Official PPRA IT STD source

→ Extracted STD master structure

→ Locked sections / clauses / forms / render blocks

→ Tender-specific configuration values

→ Generated tender document preview

→ PDF preview artifact

So Cursor should not attempt:

Take the original PDF and inject values into it

That will become fragile and nearly impossible to govern.

It should do:

Render a new tender document from structured STD sections and configuration values

**What the renderer uses**

The preview generator should combine:

| **Source** | **Example** |
| --- | --- |
| Locked STD master text | ITT, GCC, standard form text |
| Configured TDS values | deadlines, addresses, tender security, margin of preference setting |
| IT Requirements | bidder-facing requirements |
| Implementation Schedule | delivery phases/milestones |
| System Inventory & Bidder Background | inventory tables and disclosure-safe background |
| Price Schedule | pricing tables |
| Evaluation Setup | evaluation criteria and scoring rules |
| Forms & Evidence | required bidder forms and evidence |
| Contract Values | SCC values and contract schedules |

**Rendering pipeline**

Use this sequence:

1\. Load approved tender configuration

2\. Load bound active STD version

3\. Load render manifest for that STD family/version

4\. Resolve each document section in order

5\. Inject tender-specific values into approved placeholders

6\. Render structured tables from configuration records

7\. Assemble HTML document

8\. Apply official print stylesheet

9\. Generate PDF preview

10\. Store preview artifact with status GENERATED

11\. Show preview in WG-03

**Important rule**

The renderer must not invent content.

For every document section, the renderer should know whether it is:

| **Section type** | **Behavior** |
| --- | --- |
| Locked STD text | Render from STD Engine, not editable |
| Parameterized STD text | Render locked text with configured values inserted |
| Configured table | Render from wizard configuration records |
| Optional section | Include only if enabled by TDS/config |
| Generated annex | Render from structured configuration |
| Publication-only value | Show placeholder until publication |

Example:

Published Date: \[AUTO-INSERTED ON PUBLISH\]

is correct because publication has not happened yet.

**Data objects Cursor should expect**

Minimum backend objects/services:

STDVersion

STDSection

STDClause

STDRenderBlock

STDFormTemplate

TenderConfiguration

TenderConfigurationStepData

TenderDocumentPreview

TenderDocumentPreviewSection

TenderDocumentPreviewArtifact

But the UI should not expose those names.

**Render manifest**

Each STD version should have a render manifest like:

{

"std_family": "IT",

"std_version": "KE-PPRA-IT-2022-04",

"document_sections": \[

{

"key": "cover_invitation",

"title": "Cover and Invitation",

"source": "template",

"renderer": "cover_invitation_renderer"

},

{

"key": "itt",

"title": "Instructions to Tenderers",

"source": "locked_std_text"

},

{

"key": "tds",

"title": "Tender Data Sheet",

"source": "configured_values",

"renderer": "tds_renderer"

},

{

"key": "evaluation",

"title": "Evaluation and Qualification Criteria",

"source": "configured_values",

"renderer": "evaluation_renderer"

}

\]

}

This prevents Cursor from hardcoding document order inside the preview screen.

**Preview statuses**

Use simple statuses:

Not Generated

Generating

Generated

Generation Failed

Confirmed

Invalidated

If the configuration changes after approval:

Preview Status: Invalidated

and the user must return through readiness/review before confirming a new preview.

**Practical implementation for Frappe**

Backend method examples:

generate_tender_document_preview(configuration_id)

get_tender_document_preview(configuration_id)

confirm_tender_document_preview(configuration_id)

invalidate_tender_document_preview(configuration_id, reason)

download_tender_document_preview_pdf(configuration_id)

PDF generation options:

HTML template + print CSS → wkhtmltopdf / WeasyPrint / Frappe print format PDF

In Frappe, a practical first version can use:

Jinja template

\+ render manifest

\+ configuration payload

\+ Frappe PDF generation

Later, if fidelity becomes critical, move to a dedicated document renderer service.

**Cursor instruction**

Use this:

Implement Tender Document Preview generation from structured STD Engine data and tender configuration records.

Do not edit or overlay the original PPRA PDF.

The original PPRA PDF/DOC is only the legal source used to seed the STD Engine. The preview must be generated from the canonical STD version, locked clauses, render blocks, form templates, and tender-specific configuration values.

Create a backend render pipeline:

1\. Load the approved Tender Configuration.

2\. Load the bound Standard Tender Document version.

3\. Load the STD render manifest.

4\. Render locked STD sections from STD Engine.

5\. Render configured sections from CFG-01 to CFG-09 data.

6\. Assemble a complete HTML tender document.

7\. Apply print stylesheet.

8\. Generate PDF preview artifact.

9\. Store preview status and artifact reference.

10\. Return preview metadata and section outline to WG-03.

The WG-03 UI should display the generated preview artifact and document outline only. It must not construct the tender document itself in the browser.

Bottom line: **the preview is a generated legal document assembled from canonical structured STD data and approved configuration data. The browser only displays it; it does not build it.**

Coming back to tender preview, I still need to visualize how the final tender document will look like. Given that this will be an electronic-only process for bid submission, and that the PPRA requires structured and legally defensible tenders, give me a concise and practical sequence from tender preview to bid submission.

The final tender document should be visualized as **one legally controlled electronic tender package**, not just a PDF. The PDF is the human-readable view; the platform also keeps structured submission requirements behind it.

**Practical sequence**

1\. Tender Document Preview

User sees the generated tender document exactly as bidders will see it: cover, invitation, ITT, TDS, evaluation criteria, forms, requirements, schedules, price schedules, SCC, contract forms, appendices.

Purpose: confirm the rendered tender document reflects the approved configuration.

Output:

Preview PDF

Document outline

Preview confirmation record

2\. Confirm Preview

User confirms:

This document reflects the approved tender configuration.

This does **not** publish the tender.

System freezes the preview artifact.

Output:

Confirmed preview package

Immutable preview version

Audit event

3\. Send to Publication Workflow

The confirmed package is handed to Tender Management / Publications.

Package includes:

Generated tender PDF

Structured bidder-response schema

Required forms list

Required evidence list

Price schedule schema

Evaluation setup

Readiness report

Review approval record

Preview confirmation record

STD version reference

This is the key electronic-process point: the publication package is not only a PDF.

4\. Publication Setup

Publication team configures publication-only details:

Publication date/time

Tender closing date/time

Clarification deadline

Site visit / pre-bid meeting details, if any

Publication channels

Bid submission opening window

Bid encryption / locking rules

The tender document itself is not edited here unless returned for correction.

5\. Publish Tender

System publishes:

Human-readable tender document PDF

Electronic bid response forms

Structured price schedule forms

Evidence upload requirements

Bidder declaration forms

Clarification channel

Submission deadline

From the bidder side, the tender appears as:

Tender notice

Tender document

Submission checklist

Online response forms

Upload slots

Price schedule template

Clarification Q&A area

Submit bid button

6\. Bidder Prepares Response

Bidder fills the electronic response, not a loose email-style upload.

They complete:

Eligibility declarations

Technical responses

Compliance responses

Evidence uploads

Price schedule

Required forms

Beneficial ownership disclosure

Bid security details, if required

The system validates completeness before submission.

7\. Bid Submission

Bidder submits electronically.

System does:

Completeness validation

Timestamping

Bid sealing / encryption

Submission receipt

Immutable audit log

No opening before deadline

Bidder receives:

Submission reference

Timestamp

Submitted package summary

Receipt PDF / digital acknowledgement

**The visual model**

Think of the final tender as two synchronized layers:

| **Layer** | **Purpose** |
| --- | --- |
| **Tender Document PDF** | Legal, human-readable tender document |
| **Structured Submission Schema** | Controls what bidders must fill, upload, price, and certify electronically |

The preview screen should therefore show the PDF, but the publication package must also carry the structured bidder-response model.

**Clean lifecycle**

Preview generated

→ Preview confirmed

→ Sent to publication workflow

→ Publication setup completed

→ Tender published

→ Bidder downloads/reads tender

→ Bidder completes structured online submission

→ Bid submitted and sealed

Bottom line: **the preview is the final legal document view; publication turns that confirmed document plus its structured response schema into an electronic bid submission workspace.**