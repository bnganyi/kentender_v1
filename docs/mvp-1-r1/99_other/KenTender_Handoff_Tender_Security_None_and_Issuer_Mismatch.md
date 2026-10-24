# Handoff: "No security required" and issuer mismatches

**18 October 2026.** These decisions change four documents (STD-TPL-001, TPR-CHG-001, BDS-CHG-001 and EVL-CHG-001), the code that implements them and the module guides.

| | |
|---|---|
| For | Whoever revises STD-TPL-001, TPR-CHG-001, BDS-CHG-001 and EVL-CHG-001, and Claude Code, which implements the result |
| Baseline | TPR-CHG-001 v0.20, approved by the Project Owner (owner's statement, 18 October 2026: "v0.16 is now approved, as is TPR v0.20"). BDS-CHG-001 v0.16, approved under the same statement. STD-TPL-001 v0.17 and EVL-CHG-001 (current version): **not read for this handoff** |
| Read for this handoff | **TPR v0.20:** §§1, 2, 3, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 6, 13, 24. **BDS v0.16:** §§1, 2, 3, 4.3, 4.8, 4.9, 4.10, 4.11, 5.1–5.11, 5.15, 6, 12.3. Everything else in those documents was not read for this handoff |
| Protocol | `kentender-document-change`. Every approved rule is kept unless a change below replaces it. Replaced wording is kept beside its correction |

## Project Owner decisions

| ID | Decision | Owner's words | Status |
|---|---|---|---|
| S1 | Whether a tender requires tender security is decided tender by tender. "No security required" becomes a fourth choice alongside the three existing methods. The template must change so the issued documents match that choice. | "Security should be a configuration item and is decided tender to tender." and "The template needs to change to match a no tender decision. Add 'No security required'" (18 October 2026) | Decided |
| S2 | Manual entry of tender-security details is temporary. KenTender will connect directly to issuers' systems (the banks and insurers that issue guarantees), and suppliers will no longer type the details. Until then, Evaluation decides what an issuer mismatch means for a bid. | "Going forward, there will be no manual entries of tender security details and this will become a moot point. KenTender will interface directly with issuer systems. In the meantime, Evaluation is the correct place to handle this" (18 October 2026) | Decided |
| S3 | Whether adding or removing a security requirement on a published tender, by addendum, is allowed and on what terms. | — | **Open.** Recommendation in B4 |

**What S1 replaces.** TPR v0.20 §24.1 and BDS v0.16 §4.8 both record the fourth row as a "Conflict recorded, for the Owner", leaving it "supported by release 1.5, not offered". The reason given (TPR §24.1, verbatim): "this product's issued documents state a Tender Security is required (ITT 18.2: 'a Tender Security is required in accordance with ITT 18.1'; the template's insertion-point register (`tender.tender_security.type`) fixes the treatment to 'Tender Security' and excludes the Tender-Securing Declaration path), so a Tender that stated no security would publish documents that contradict it. Offering the fourth method needs an Owner-approved document variant (a source-coverage decision under STD-TPL-001 §13)". S1 is that owner approval.

**Not verified against the primary source.** Whether the Public Procurement and Asset Disposal Act and its Regulations allow an open tender with no tender security, or require a Tender-Securing Declaration in its place. The owner has decided S1. Whoever revises STD-TPL-001 should read the governing provisions in full and record the basis, or record that it was not verified.

---

## Part A: STD-TPL-001 — the template (the main change)

STD-TPL-001 v0.17 was not read for this handoff. Section numbers below are those cited by TPR v0.20 and BDS v0.16. Confirm them against the document before editing.

| ID | Change |
|---|---|
| A1 | **Conditional ITT 18 wording.** The ITT 18 clauses, the matching Tender Data Sheet entry and the Tender Security form become conditional on the Tender's security choice. When the method is one of the three existing ones, the issued documents read as today. When it is **No security required**, ITT 18.2 states that no tender security is required for this tender, the Tender Security form is not issued, and no other clause, form or checklist refers to a security. Replacement wording is new content for owner review. |
| A2 | **Insertion-point register.** `tender.tender_security.type` stops being fixed to 'Tender Security'. It takes either 'Tender Security' or 'None', driven by the Tender's security choice. The Tender-Securing Declaration path stays excluded; S1 does not add it. |
| A3 | **Source coverage (§13).** Record the owner's approval (S1, quoted) as the source-coverage decision for the variant, so the "None" document is a covered variant and not a deviation. |
| A4 | **Response rules (§18.9).** Keep release 1.5's existing behaviour: when the Tender states no security, neither security response group (`RR-TENDER-SECURITY`, `RR-TENDER-SECURITY-ISSUER`) is generated. No change to the rule; only the document text changes. |
| A5 | **Release.** Issue the change as a new template release (1.6), not a change to 1.5. It reaches new tenders and unpublished drafts only through the explicit update TPR v0.20 §24.2 already defines (`UpdateDraftTemplateRelease`). Published tenders keep their release. |
| A6 | **Acceptance.** Add tests that render both variants: (a) a three-method Tender issues ITT 18 and the security form as today; (b) a "None" Tender issues no security clause, form or checklist line, and no text anywhere in the issued package says a security is required. |

---

## Part B: TPR-CHG-001 v0.21

| ID | Change | Replaces or changes (v0.20) |
|---|---|---|
| B1 | **Fourth choice.** `tender_security_method` gains **No security required**. It stays required, with no default. | §5.2 "v0.20 amendment to the two rows above"; §24.1 list; §24.1 "Conflict recorded" paragraph (keep it, labelled superseded by v0.21) |
| B2 | **Dependent fields.** When **No security required** is chosen: the tender-security amount is hidden and must be empty; `tender_security_original` is hidden and stored as **Not required**; the review raises a Must fix if an amount is present. When any other method is chosen, today's rules apply unchanged. | §5.2 Tender security amount row; §5.4 |
| B3 | **Release check.** **No security required** is offered only when the Tender's bound template release supports the "None" document variant (release 1.6 or later). A draft on release 1.5 shows the option as unavailable, with **Update to the current release** as the fix (TPR v0.20 §24.2). | §24.2 |
| B4 | **Addenda (S3, open).** Recommendation: allow an addendum to move between **No security required** and a method, as a non-material change on the existing addendum rows (TPR v0.20 §24.3). Adding a requirement after publication must apply the existing late-amendment and deadline-extension rules, so suppliers have time to obtain a guarantee. Removing a requirement needs no extension. Until the owner decides, the addendum catalogue does not offer a change to or from **No security required**. | §24.3 |
| B5 | **Officer help.** The Tender details task's help line for the new choice reads: "No tender security will be asked of suppliers. The tender documents will say so." New wording for owner review. | §24.1 help line |
| B6 | **Security statement correction.** `CorrectSecurityStatement` (§24.4) gains **No security required** as a value, so a Tender published before §23 that said in its documents that no security was required can be recorded correctly. Refuse it for a Tender whose published documents state a security is required. | §24.4 |
| B7 | **Fixtures.** Add one isolated fixture: a Draft whose officer chose **No security required**, on release 1.6, complete and submittable. Canonical tenders keep **Bidder uploads an electronic instrument** with the original **Required** (SEED-002 v0.7). | §13.4 |
| B8 | **Acceptance.** Replace TPR20-AC-001's "**No security required** is not offered" with: "the Tender details task offers the four choices with no default; **No security required** hides and empties the amount and the original-delivery field; it is unavailable on a release before 1.6". | §24.5 |

---

## Part C: BDS-CHG-001 v0.17

| ID | Change | Replaces or changes (v0.16) |
|---|---|---|
| C1 | **The fourth row is offered.** The "No security required" row in the §4.8 v0.16 table changes from "**Supported by release 1.5, not offered**" to offered, from release 1.6. Keep the "Conflict recorded, for the Owner" paragraph, labelled resolved by S1. | §4.8 v0.16 table and conflict paragraph |
| C2 | **What the supplier sees.** On a no-security Tender, the Company, declarations and tender security task shows no security inputs, upload, status or advisory, and says once: "This tender does not require tender security." New wording for owner review. The supplier-facing status set gains no new value; the security status line is absent. | §4.8; §10.9 (BDS-DES-08) |
| C3 | **Intake.** No intake duty can be assigned for a no-security Tender, and `SubmitTenderSecurity` is refused with the existing unknown-response code. | §6 Tender Security Intake Officer row; §7.3 |
| C4 | **Direction for issuer interfaces (S2).** Add to §5.10 or a new production-readiness item: KenTender will obtain guarantee details directly from issuers' systems, and supplier typing of security details ends when that interface is approved. Until then, manual entry, issuer verification and the v0.16 rule that **Pending**, **Mismatch** and **Unavailable** block nothing all stay as they are. Record S2 verbatim. | §5.10; §4.8 v0.16 "a pending issuer response blocks nothing" (unchanged, cross-referenced) |
| C5 | **Mismatch ownership.** In the §4.8 v0.16 paragraph "what Evaluation does with the outcome after the opening is for EVL-CHG-001, not decided here", add: "Decided by the Project Owner, 18 October 2026 (S2): Evaluation owns the treatment; see EVL-CHG-001." | §4.8 |
| C6 | **Acceptance.** Add: a no-security Tender's bid shows no security inputs or status and submits without them; intake assignment and `SubmitTenderSecurity` are refused for it. | §14.3 |

---

## Part D: EVL-CHG-001 (not read for this handoff)

| ID | Change |
|---|---|
| D1 | **Issuer mismatch at evaluation (S2).** State how evaluators treat a bid whose tender security still reads **Mismatch**, **Pending** or **Unavailable** from the issuer when the bids are opened. Bid Submission passes the issuer status, its source and its time; it decides nothing. The rule is for the owner to approve. Recommendation: evaluators see the status in the tender-security check, may seek clarification from the supplier or confirm directly with the issuer through the evaluation clarification route, and record the finding against the published tender-security requirement. A mismatch is not by itself a failure. |
| D2 | **No-security tenders.** The tender-security check is absent for a Tender that required no security. It is not shown as passed or as not applicable in a way that suggests a check was made. |
| D3 | **Later.** When the issuer interface (S2) replaces manual entry, revisit D1: a confirmed guarantee from the issuer's own system leaves only the compliance comparison. |

---

## Part E: Code

1. **Template:** implement release 1.6 with the conditional ITT 18 wording, the form and the insertion point (A1–A6). Render tests for both variants.
2. **Tenders:** add the fourth option to the security method control, the dependent-field rules, the release check and the review rules (B1–B3, B6). Keep the addendum catalogue unchanged until S3 is decided.
3. **Supplier portal:** hide the security group on a no-security Tender, refuse intake and `SubmitTenderSecurity` for it (C2, C3).
4. **Evaluation:** skip the tender-security check for a no-security Tender (D2). D1 waits for the EVL revision.
5. **Seeds:** add the isolated fixture in B7. No canonical fact changes.
6. **Guides:** after approval, update the Tenders guide ("Tender details" row and the Addenda paragraph) and the Supplier Portal and Bids guide (the tender-security paragraph) to show the fourth choice.

## New content for owner review

- The "None" wording of ITT 18.2 and the omission of the security form (A1).
- The value 'None' for `tender.tender_security.type` (A2).
- Release number 1.6 (A5).
- The officer help line (B5) and the supplier message (C2).
- The isolated fixture (B7).
- The EVL recommendation (D1).

## Decisions still needed

1. **S3:** may an addendum add or remove a security requirement after publication? Recommendation in B4.
2. **D1:** how evaluators treat an unresolved issuer mismatch. Recommendation in Part D.
3. **Legal basis:** confirm against the Act and Regulations that an open tender may go out with no security and no Tender-Securing Declaration, or record that it was not verified.

## Records to update

- Baseline register (KT-DOC-CTRL-001): TPR-CHG-001 v0.20 and BDS-CHG-001 v0.16 to Approved on the owner's 18 October 2026 statement; then the v0.21 and v0.17 proposals; STD-TPL-001 and EVL-CHG-001 proposals.
- TPR v0.20 and BDS v0.16 control tables: mark Approved, quoting the owner's statement, before the successors are drafted.
