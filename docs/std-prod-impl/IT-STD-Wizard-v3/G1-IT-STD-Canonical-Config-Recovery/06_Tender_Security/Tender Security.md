Tender Security

The [PPRA IT STD](https://ppra.go.ke/standard-tender-documents/?utm_source=chatgpt.com) allows the TDS to require either a **Tender Security** or a **Tender-Securing Declaration**. These are fundamentally different bidder tasks.

**First distinction**

| **Item**                    | **Meaning**                                                                                                        |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Tender Security             | A financial instrument supporting the bid, normally issued by a bank, insurer or approved financial institution    |
| Tender-Securing Declaration | The bidder accepts specified consequences if it withdraws the tender or fails to sign/furnish performance security |
| Performance Security        | Furnished by the successful bidder after award                                                                     |
| Professional Indemnity      | Insurance evidence; not tender security                                                                            |

The NSSF fixture requires professional indemnity and post-award performance security, but does not appear to require tender security. Therefore, Tender Security should not be mandatory for NSSF merely because it exists in the canonical IT STD.

**TDS-controlled modes**

The published tender must configure one mode:

- **External Tender Security**
- **Tender-Securing Declaration**
- **Not required**

If not required, omit the section from the bidder checklist entirely.

**Mode 1 - External Tender Security**

**Configured by the tender**

- Required amount
- Currency
- Accepted instrument types
- Minimum expiry date or validity rule
- Acceptable issuer categories
- Foreign-institution and correspondent-bank rules
- Any other TDS conditions

**Bidder-provided information**

- Instrument type
- Guarantee/instrument number
- Issuing institution's legal name
- Issuer address and country
- Issue date
- Expiry date
- Guaranteed amount
- Currency
- Electronic guarantee or issuer verification reference
- Correspondent institution, where required

The beneficiary, Tenderer, tender reference and required amount are derived-not re-entered.

For a JV, the system must display the required applicant name derived from the CBQ/JV information.

The screen should perform structural checks:

- Accepted instrument type
- Amount not below the requirement
- Correct currency
- Sufficient validity
- Required issuer and correspondent details
- Tenderer/JV naming requirement

Passing these checks means **Ready**, not "Verified" or "Approved". The Procuring Entity evaluates legal responsiveness after opening.

**Mode 2 - Tender-Securing Declaration**

This requires almost no data entry.

Derived from the tender and CBQ:

- Tenderer
- Tender reference
- Procuring Entity
- Suspension/consequence terms
- Authorized signatory
- Certification date/time

The bidder should:

- Read the exact configured declaration.
- Certify it once electronically.

No upload, stamp, typed signature or duplicate signatory fields are needed.

**Mode 3 - Not required**

Do not show an empty Tender Security section or ask the bidder to acknowledge that it is not required.

**Recommended UI scope**

Only two conditional screen designs are needed:

- **Provide Tender Security** - requirements summary, instrument details and electronic instrument submission.
- **Certify Tender-Securing Declaration** - exact legal terms, signatory summary and one certification action.

**Legal-template decisions before implementation**

- **Electronic original:** A scanned paper guarantee should not automatically be treated as the required original. The template must approve digitally signed issuer documents, direct issuer submission or another authenticated electronic method.
- **Expiry rule:** The STD contains a 30-day rule in ITT 22.4, while the insurance form mentions 28 days. The manually prepared IT STD template must resolve this rather than letting runtime code guess.
- **Issuer verification:** The bidder UI must not claim that an issuer is verified unless an actual verification source or process exists.
- **Confidentiality:** Tender-security contents must not become visible to the Procuring Entity before the lawful opening stage.