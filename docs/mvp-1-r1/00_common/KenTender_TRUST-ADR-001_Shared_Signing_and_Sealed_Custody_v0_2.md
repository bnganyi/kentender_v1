# TRUST-ADR-001 — Shared Signing and Sealed Custody

**Controlling approval — 3 October 2026.** The Project Owner instructed: “Mark the documents as approved”. This approves this version in the coordinated OVS v0.6 package, including its incorporated amendments. OVS-P01–P05 are approved. The incorporated REQ v1.13, CFG v0.17 and TPR v0.16 changes are accepted within their approved successors; this does not create separate retrospective approvals of those intermediate versions. Earlier proposed/pending wording is drafting history superseded by this record. Static design work and conformance matrices remain open; CM and the separate template walkthrough remain deferred. Approval does not establish implementation, seed execution, testing, legal clearance or production readiness.

**Limited OVS amendment.** OVS v0.6 §4.2 preserves the approved custody/signing boundary: technical page access is not permission to reveal sealed content, release keys, sign or impersonate a member. Administrator/System Manager ordinary technical read is distinct from limited incident-operator access. All §§1–5 production gates and proxy limitations remain unchanged. This amendment adds no production provider, legal clearance or decryption capability.

| Control | Value |
|---|---|
| Document ID | TRUST-ADR-001 |
| Version | 0.2 |
| Status | Approved — 3 October 2026 |
| Scope | Cross-module trust service for signing, attestations and electronic bid custody |
| Consumers | BDS-CHG-001 v0.8; BOP-CHG-001 v0.1; PRC-CHG-001 v0.2; future Evaluation, award and contract units |
| Precedence | Approved BDS production guards remain in force. This ADR neither amends its v0.8 submission rule nor enables production opening. |

## 1. Decisions locked now

1. **Two distinct acts.** An ordinary authenticated workflow decision records the actor, appointment/authority, intent, exact record version, trusted server time and immutable event. Where a law or controlled instrument requires a signature, the production target is a personal advanced electronic signature through a legally acceptable accredited/licensed trust service, verified against the exact frozen target. A workflow click is never renamed or exported as a statutory signature.
2. **One reusable signing capability.** The future shared trust support module owns provider integration, certificate identity and status, personal signing, target digests, verification, long-term proof and revocation handling. The owning business module defines *who*, *what*, *when* and *which statutory targets*. The shared module cannot decide a tender, award or committee appointment.
3. **One reusable evidence and custody capability.** The future support module owns immutable version/digest evidence, encrypted storage, tender-box deposit/receipts, external key custody, independent multi-person release, backup/recovery and audit exports. BDS defines submission eligibility and acceptance; BOP defines the opening ceremony; PRC defines attendance and minutes. An application administrator has no business opening or personal signing authority.
4. **Special opening targets.** Bid Opening names each tender page selected for member signature, each submitted price/change location for initials, every minutes page for initials and the final minutes page for signature/name/designation. A single reviewed batch interaction may request evidence for multiple named targets, but each member's proof must enumerate and bind each exact target. Whether that pattern is legally equivalent to the physical acts remains an explicit legal verification gate.
5. **Independent opening.** The chair cannot open alone. The active appointed roster, at least three including the independent member, participates in the live session. The production custody boundary independently enforces a multi-person authorization before any decrypt/reveal, with key material outside Frappe administrators' control. The detailed threshold, key holders, credential lifetime and recovery are deferred to the support module and operating profile; no historical three-password formula is presumed to be current law.

## 2. Interim development proxies

These proxies are **development/test implementations of the business journey**, not legal equivalents or production electronic-procurement controls. They use synthetic bids and clearly labelled test evidence only.

| Contract | Interim proxy | Non-negotiable limit |
|---|---|---|
| Ordinary decision | Existing authenticated owner command, explicit confirmation of exact version, authority check, immutable event and server timestamp. | No statutory-signature claim. |
| Member signature/initial | Member individually reviews a frozen version and the list of exact page/price/minutes targets, confirms intent, and creates a test attestation bound to their identity and target digest. Stale target requires fresh review. | UI/export labels it **Test attestation — not an electronic signature**. No fake certificate, initials image or “signed” proof. |
| Sealed tender-box deposit | A test adapter accepts a synthetic package, assigns one receipt/envelope identity, encrypts/restricts storage, records digest, version, deadline and replay-safe custody events. | App-managed keys and server-side guards do not establish independent production custody. Never accept real bids through this adapter. |
| Joint opening release | Three named appointed users independently join the test session; at least two distinct committee members, including the independent member, confirm release once; all appointed members remain present before each reveal. The adapter checks the deadline and permits ordered reveals. | This is a **test control**, not the production key threshold or legal opening method. Administrator cannot press for a member; test administrators with infrastructure access are outside its confidentiality guarantee. |
| Exports and handoff | Event register, preview minutes and synthetic handoff retain exact source and proxy status. | Prominent **Test environment — bids are not submitted/opened under the production procedure** on all affected screens, receipts and exports. |

The test custody adapter may use standard authenticated encryption and independent digest checks; its exact library, keys and deployment are implementation details. The proxy's guards must still test negative paths: early attempt, one-member/absent-member attempt, stale member, invalid package, duplicate receipt, interrupted session, stale target, administrator attempt and recovery without rewriting history. The test two-person release is a product exercise, not a choice of the future production threshold.

## 3. Production boundary and truthful alternative

The approved BDS-CHG-001 v0.8 `production_bid_submission_enabled` flag stays **false** until its entire production operating profile, licensed signature, authoritative tender box, trusted time, recovery, security and statutory acceptance evidence pass. A proxy cannot satisfy that guard, issue a live bidder receipt or make the supplier portal say **Submitted**. Production Bid Opening and legally effective member signatures likewise remain disabled until the support module and legal profile are approved and integrated. Internal work such as tender preparation and draft bid practice may proceed under its own lawful scope.

If an entity must conduct a real procurement before these services exist, the lawful external channel and opening procedure must be approved and used *in that channel*. KenTender may later import factual evidence through a separately specified, authorized interface; it must not present an internally generated proxy receipt, readout or minutes as that channel's official record. No automatic external-system equivalence is implied.

## 4. Deferred support-module contract

Implement a separately controlled **Trust, Signing and Custody** support module. Its production design must specify:

- licensed/accredited provider selection, personal certificate enrolment and authority, signing-device or remote-signing control, certificate-chain/status-at-time verification, trusted time, proof retention and independently verifiable export;
- canonical package/rendered-page identities, exact signature/initial targets, accessible review and batch authorization, version change and supplementary correction handling;
- sealed per-submission encryption, authoritative accepted receipt, immutable inventory/lineage, separated key management (managed HSM or equivalent), independent multi-person release, backup/restore, breach and failed/uncertain-result reconciliation;
- deadline and effective addendum binding, tenant separation, least privilege, supplier/committee/admin adversarial tests, disaster recovery, operational monitoring and evidence of approved government-channel integration where applicable.

The interface must return distinct `Unavailable`, `Rejected`, `Indeterminate` and `Accepted/Verified` outcomes with one correlation identity and safe retries. Owner modules never fabricate a successful receipt or proof on timeout. Adoption requires contract tests plus real provider/tender-box integration tests and an explicit release gate. A simulated pass cannot close production requirements.

## 5. Legal decisions and closure

**Locked questions; answers deferred.** (L1) Verify that the chosen per-target advanced electronic signing procedure satisfies PPADA section 78 page signatures, price/change initials and minutes signatures/initials. (L2) Verify the operative procurement instruments and directions, including the status/effect of the 4 December 2025 judgment on the 2020 Regulations and any appeal, stay or replacement, before selecting the production electronic custody/credential procedure. Record the actual sources, applicable date, responsible reviewer, interpretation and tests in the operating profile. Neither legal question is closed by this architecture approval.

This ADR approves the cross-module **contract, ownership and interim test boundary**. It defers the actual production provider, electronic signing method, key threshold/custody implementation and legal compliance finding. No module may override this boundary through a local flag, generic checkbox, administrator privilege or document-approval inference.

## Sources checked

- PPADA section 78 as reproduced in [PPRA review record](https://ppra.go.ke/?mdocs-file=10256).
- Communications Authority [national PKI](https://www.ca.go.ke/national-public-key-infrastrure) and [accredited electronic certification providers](https://www.ca.go.ke/market-structure).
- [Kenya Information and Communications Act](https://new.kenyalaw.org/akn/ke/act/1998/2/eng@2022-12-31), electronic signature provisions; live consolidated text and prescribing instruments require the L1 review.
- [High Court judgment of 4 December 2025](https://new.kenyalaw.org/akn/ke/judgment/kehc/2025/19224/eng@2025-12-04), subject to L2 current-status verification.
