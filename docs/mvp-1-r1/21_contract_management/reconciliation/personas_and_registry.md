# CM-CHG-001 v0.8: personas, registry and independence checks

| Control | Value |
|---|---|
| Version | 0.8-personas.1 |
| Date | 14 October 2026 |
| Source | Read-only queries on `kentender-test.local` (`User`, `User Responsibility Assignment`, `Organisation Unit`, `Installed STD Release`), `kentender_core/services/business_role_registry.py`, import scans of `kentender_core` and `kentender_suppliers` (tracker CM8-010) |

All queries read only; nothing was created, changed or run through a test. The test site is a copy of dev refreshed earlier; counts will differ after a rebuild.

## Personas (CM v0.8 §13) on the test site

| Person | User (enabled) | Responsibilities today (status Enabled) | CM needs (CM v0.8 §6.2, §13) | Gap |
|---|---|---|---|---|
| Charles Mutiso | `charles.mutiso@moh.example.test` | Head of Procurement Function | HOP: prepare, certify, completion certificate | None for HOP; no CM registry entries yet |
| Amina Hassan | `amina.hassan@moh.example.test` | Accounting Officer | AO; entity signatory under current authority check | Entity-signatory authority record not modelled yet |
| Brian Wafula | `brian.wafula@moh.example.test` | Procurement Officer | Contract preparation where authorised; procurement inspection member by separate appointment | Contract preparation and appointment absent |
| Julia Njeri | `julia.njeri@moh.example.test` | Head of User Department, scope `OU-MOH-02501` (Digital Health) | Contract owner; inspection chair by appointment (needs Contract inspection); the D40-HOD branch is oversight-only | Contract coordination and Contract inspection absent |
| Peter Mugo | `peter.mugo@moh.example.test` | **None found** | Technical member and technical certifier (needs Technical certification and Contract inspection) | **No responsibility at all** |
| Grace Wanjiku | `grace.wanjiku@moh.example.test` | Departmental Author at `OU-MOH-02502` and `OU-MOH-02501`; Head of User Department at `OU-MOH-02502` | Receiver (Receiving at the managing OU); D40-D has no Receiving | Receiving absent |
| Josphat Mwangi | `josphat.mwangi@moh.example.test` | Finance Confirmation Officer; Budget Officer | Finance maker (Finance preparation, Site-wide, plus native permission) | Finance preparation absent; **Finance Confirmation Officer is Budget's funding-confirmation role**, not a CM Finance role |
| Beatrice Kamau | `beatrice.kamau@moh.example.test` | Budget Approver | Finance approver (Finance approval, Site-wide, plus native permission) | Finance approval absent |
| Mary Wanjiku | `mary.wanjiku@afyadigital.example` | none found (supplier authority is through the supplier-account provider) | Supplier signatory | Authority through `kt_supplier_account_provider` (read-time); not an AUTH assignment |
| David Ouma | `david.ouma@afyadigital.example` | same | Supplier representative | same |
| Daniel Otieno | `daniel.otieno@moh.example.test` | Technical Operator | Technical read, recovery scope, no business commands | Recovery scope definition |
| Naomi Chebet | `naomi.chebet@moh.example.test` | Auditor | Read-only audit scope | None |
| Grace Wambui | `grace.wambui@moh.example.test` (user exists) | not queried | Distinct change reviewer (D27-R) | Appointment only |
| Ruth Achieng | `ruth.achieng@moh.example.test` (user exists) | not queried | Legal reviewer in D27-R | Appointment only |

All named personas exist as enabled users; **none of CM's eight new responsibilities exist** in the registry. Existing people receive CM capacities only by explicit assignment or appointment in the isolated CM fixtures (CM v0.8 §13); creating or reusing a person grants nothing.

## Registry (`business_role_registry.py`, 18 entries)

Organisation Unit: Departmental Author, Head of User Department. Site-wide: Procurement Planner, Auditor, Budget Officer, Accounting Officer, Plan Statutory Approver, Budget Approver, Finance Confirmation Officer, Head of Procurement Function, Procurement Officer, Strategy Author, Strategy Approver, Supplier Account Support Officer, Technical Operator, Release Operator, Evaluation Technical Support. Tender: Tender Security Intake Officer. The module docstring records the third scope type **Tender** as added on 10 October 2026 for the tender-security duty alone. **CM adds Site-wide and Organisation Unit entries only** (Contract preparation, Contract coordination, Receiving; Contract inspection, Technical certification, Entity contract signing, Finance preparation, Finance approval). Whether to reuse "Finance Confirmation Officer" for Finance approval was not settled by CM v0.8 ("Do not introduce … a global Payments Officer"); the plan registers the CM names the document uses.

## Organisation unit labels

CM boards and KT-STD v1.29 use `OU-MOH-DHI` (Digital Health, under `OU-MOH-DHP`). The test site's generated names are `OU-MOH-02501` (Digital Health) and `OU-MOH-02500` (Directorate of Digital Health and Policy). **The KT-STD codes are labels**; seeds use the generated names, as earlier modules do. Playwright-prefixed units also exist on the test site.

## Independence (static scan, CM-AC-25 / CM-AC-32)

| Check | Result (14 Oct 2026) |
|---|---|
| `kentender_suppliers` imports of `kentender_procurement`, `kentender_budget` or `kentender_strategy` outside tests | **0** |
| `kentender_core` imports of those apps outside tests and outside `seeds/` | **0** (89 import lines exist, all under `seeds/`: the canonical seed orchestrator and stage seeders) |
| `kentender_core` hooks naming those apps | 0 string references in `hooks.py` |
| `required_apps` | core: none declared; suppliers: `["erpnext", "kentender_core"]`; strategy: core; budget: core, strategy; procurement: core, strategy, budget |

This is a **static scan only**. It does not prove that core and suppliers install and migrate on a site without the tendering apps; Phase 1's `kentender-cm-only.local` (CM8-107) and the spike's S9 do. A real install may expose import-time or patch dependencies the scan cannot see.

## Installed STD template releases (read-only query)

| Site | Releases installed |
|---|---|
| `kentender-test.local` | 1.1, 1.2, 1.3, 1.4, **1.5** (installed 11 Oct 2026) |
| `kentender.midas.com` | 1.1, 1.2, 1.3, 1.4 |

The Phase 4 L2 run needs the release the canonical tender used; which one that is was not established in Phase 0.
