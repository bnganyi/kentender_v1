# KenTender

# Confidential Business Questionnaire — Simple Stitch Screen Prompts

Use one prompt at a time.

## Rules for every screen

- Reuse the existing KenTender Bidder Workspace shell.
- Use a full page, not a drawer.
- The bidder enters all bidder information directly in this questionnaire.
- Leave bidder fields blank. Do not invent or prefill bidder names, addresses, people or registration details.
- Prefill only the tender information published by the Procuring Entity.
- Use normal user language. Show no hashes, IDs, schemas, source references or system metadata.
- Do not add PDFs, document-form replicas or implementation architecture.
- Save draft does not certify the questionnaire.

Use this tender information as the design example:

- Procuring Entity: National Social Security Fund Staff Pension Scheme (NSSF SPS)
- Tender Reference: NSSFSPS/ICT/ERP/001/2025-2026
- Tender Opening: 30 June 2026, 11:00 a.m. EAT

---

## Screen 1 — Bidder Details

```text
Design the first screen of the KenTender Confidential Business Questionnaire.

Title: Confidential Business Questionnaire
Description: Tell us who is submitting this tender. For a joint venture, complete one questionnaire for each member.

Show a simple five-step progress bar:
1. Bidder Details
2. Business Details
3. Ownership
4. Conflicts
5. Certify

Show the Procuring Entity, Tender Reference and Tender Opening as read-only tender information.

Ask:
- Are you bidding as a single entity or a joint venture?

If joint venture is selected, show:
- Current entity: Lead bidder
- Add joint venture member
- One questionnaire is required for each member

Provide blank fields:
- Legal name of bidder
- Country
- City
- Location
- Building
- Floor
- Postal address
- Contact person
- Contact email

Actions:
- Save draft
- Continue
- Back to checklist

Do not use an organisation profile or “verified information” panel.
```

---

## Screen 2 — Business Details

```text
Design the Business Details screen of the KenTender Confidential Business Questionnaire.

Keep the same page header and five-step progress bar.

Provide blank fields:

Trade licence:
- Current trade licence registration number
- Expiry date

Registering body or agency:
- Name
- Country
- Physical address
- Postal address
- Email
- Telephone

Business:
- Nature of business
- Maximum value of business handled
- Currency

Ask:
- Is the bidder listed on a stock exchange? Yes / No

If Yes, reveal:
- Stock exchange name
- Country
- Physical address
- Postal address
- Email
- Telephone

Actions:
- Back
- Save draft
- Continue

Do not add uploads or qualification questions.
```

---

## Screen 3 — Ownership and Management

```text
Design the Ownership and Management screen of the KenTender Confidential Business Questionnaire.

Keep the same page header and five-step progress bar.

Ask:
- What type of entity is the bidder?
  - Sole proprietor
  - Partnership
  - Registered company

Show only the fields for the selected type.

For a sole proprietor:
- Full name
- Age
- Nationality
- Country of origin
- Citizenship

For a partnership, show an empty partners table:
- Full name
- Nationality
- Citizenship
- Percentage of shares owned
- Add partner

For a registered company:
- Private or public company
- Nominal capital in Kenya shillings or equivalent
- Issued capital in Kenya shillings or equivalent
- Empty directors table:
  - Full name
  - Nationality
  - Citizenship
  - Percentage of shares owned
  - Add director

Actions:
- Back
- Save draft
- Continue

Do not show all three entity forms together.
```

---

## Screen 4 — Interests and Conflicts

```text
Design the Interests and Conflicts screen of the KenTender Confidential Business Questionnaire.

Keep the same page header and five-step progress bar.

First ask:
“Is there any person in National Social Security Fund Staff Pension Scheme who has an interest or relationship in this bidder?”

Use Yes / No.

If Yes, reveal an empty table:
- Person’s full name
- Designation in the Procuring Entity
- Interest or relationship with the bidder
- Add person

Below it, show the nine required conflict questions as numbered rows:
1. Common ownership or control with another tenderer
2. Subsidy received from another tenderer
3. Same legal representative as another tenderer
4. Relationship capable of influencing another tenderer or the Procuring Entity
5. Affiliate involved in preparing the design or technical specifications
6. Conflicting role in supplying goods or services during contract implementation
7. Business or family relationship with staff involved in tender preparation or evaluation
8. Business or family relationship with staff involved in contract implementation or supervision
9. Whether any conflict under questions 7 or 8 has been resolved

Each question requires Yes or No.
When an answer indicates a conflict or unresolved issue, reveal a Details field directly below that question.

Show progress: 0 of 9 answered.

Actions:
- Back
- Save draft
- Review questionnaire

Do not replace the nine questions with one general checkbox.
```

---

## Screen 5 — Review and Certify

```text
Design the Review and Certify screen of the KenTender Confidential Business Questionnaire.

Keep the same page header and five-step progress bar.

Show four review rows:
- Bidder Details
- Business Details
- Ownership and Management
- Interests and Conflicts

Each row shows Complete or Needs attention and has an Edit action.

If anything is incomplete:
- Show exactly what must be completed
- Disable certification

When complete, show this certification:
“On behalf of the Tenderer, I certify that the information given above is complete, current and accurate as at the date of submission.”

Provide blank fields:
- Full name of person certifying
- Title or designation

Add:
- I confirm that I am authorised to certify this questionnaire for the bidder

Primary action:
- Certify questionnaire

Secondary actions:
- Back
- Save draft

After certification, show:
- Questionnaire complete
- Name of certifying person
- Title or designation
- Certification date and time

For a joint venture, show which entities are complete and a simple action to continue with the next member.

If questionnaire answers are later changed, show “Certification required again”.

Do not show hashes, technical signature information or audit metadata.
```
