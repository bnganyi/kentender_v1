# CTX-CHG-001 — Working Context

**Controlling approval — 3 October 2026.** The Project Owner instructed: “Mark the documents as approved”. This approves this version in the coordinated OVS v0.6 package, including its incorporated amendments. OVS-P01–P05 are approved. The incorporated REQ v1.13, CFG v0.17 and TPR v0.16 changes are accepted within their approved successors; this does not create separate retrospective approvals of those intermediate versions. Earlier proposed/pending wording is drafting history superseded by this record. Static design work and conformance matrices remain open; CM and the separate template walkthrough remain deferred. Approval does not establish implementation, seed execution, testing, legal clearance or production readiness.

| Control | Value |
|---|---|
| Version | 1.1 |
| Status | Approved — 3 October 2026 |
| Date | 3 October 2026 |
| Supersedes | v1.0 only on approval; its implementation claim is historical and not evidence for this successor |
| Sources | Uploaded CTX v1.0, AUTH v1.10, KT-STD v1.14, CFG v0.17 proposed over v0.16, NDS v1.15; OVS v0.6 |

## 1. Durable rule

Permissions determine what a user may access. Working context only filters the current list. It is visible, reversible, module-appropriate and never grants access. An authorised direct record link resolves from the record, even when it differs from the current list filters.

## 2. One site, one entity

The site Procuring Entity is supplied by Configuration. Remove CTX v1.0's multi-entity chooser, global PE preference and cross-PE picker from the MVP contract. Display the site identity where useful; do not ask a user to choose the only entity. Do not add PE copies to records to support context: each owner defines its data and the site supplies entity identity.

## 3. Authority

Use AUTH's current User Responsibility Assignment and registered list/direct-record predicates. Do not use Frappe User Permission, User Scope Assignment or browser preference as business authority. Apply active dates and the exact valid responsibility/scope pair; filters never widen it. Technical reads follow KT-STD and the proposed OVS §4.2 exception for sealed contents/credentials. Configuration maintenance remains separately authorised.

## 4. Module-owned filters

Financial Year and department filters are local to the module, optional where that module supports an unfiltered authorised list, and always changeable. A module decides which values are meaningful. Creation eligibility and intake windows come from that module and CFG; choosing an old/closed year must not hide permitted historical records or corrections.

A filter belongs in the register, not as a mandatory context dialogue before a deep link. Provide Clear filters and preserve return-list context. Do not add a global FY, PE Fiscal Year Context gate or a new context-approval process. Fiscal Year identifiers follow CFG/native owner contracts; labels and integer years are display values, not substitute identities.

## 5. Persistence and service boundary

Reuse valid server-side per-user module preferences where already implemented, with snake_case keys. Store only an optional selection, not eligibility or authority. Revalidate preferences on each read against current access. An obsolete preference is cleared with a plain explanation and the permitted list; it must not trap the user behind a denied old context.

Core may supply preference get/set plumbing; owners resolve offered values and record context. Existing get_module_fy/select_module_fy and get_module_ou/select_module_ou can be retained only where their implementations satisfy this contract. No installed implementation was inspected here. Obsolete select_working_pe/pe_options flows are retired for MVP consumers; remove their call sites and stop reading the old PE preference. Preserve unrelated defaults. Do not delete historic business records or treat migration of a preference as a change of record ownership.

A register request returns current permitted filters, applied filter values, results and typed page state. A direct record read resolves permissions and the record's actual owner context without first persisting a different working preference. A mutation rechecks the owner's authority, source, state and eligibility regardless of the selected filter. No second permission cache is introduced.

## 6. Owner adoption

Apply these rules to Needs, Budget, Planning, Strategy, Requisitions, Tender records, downstream stages and independent Contract Management where their register supports filters. Home continues to compose KT-STD next_step and hand-off items; it does not introduce a global FY prerequisite. Shared usability and recovery are owned by OVS v0.6, not repeated here.

## 7. Acceptance

1. An authorised direct link opens despite a different saved FY/department filter and returns to the original list context.
2. Switching/clearing a filter changes only visible permitted results, never responsibility or command authority.
3. An expired responsibility or invalid saved preference grants nothing and does not prevent access through another valid responsibility.
4. No MVP route requires PE selection, PE Fiscal Year Context or a Frappe User Permission to establish business authority.
5. Closed intake prevents only the owner-defined new work; authorised history and corrections remain accessible.
6. Refresh and back preserve useful filter state; old v1.0 preference consumers cannot restore retired gates.

## 8. Predecessor disposition

Retain v1.0 in the source archive. Its context-is-not-authority principle is preserved. Its multi-PE selection, obsolete permission sources, context registry, mandatory picker/band and per-record-PE prescription are replaced. CTX-FU-01 is superseded by AUTH's assignment-time enforcement requirement, not fixed by reinstating the old scope store. CTX-FU-02 is resolved at requirement level by owner Fiscal Year identities; actual code conversion must be verified. CTX-FU-03 legacy Planning tests remain an implementation follow-up if still present; no repository correction is claimed.
