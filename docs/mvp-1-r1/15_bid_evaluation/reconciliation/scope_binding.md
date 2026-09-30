# EVL-CHG-001 v0.4: scope binding and dated rules

| Control | Value |
|---|---|
| Version | 0.4-scope.1 |
| Date | 30 September 2026 |
| Source | EVL v0.4 §5.1 (scope gate), §5.7 (timers); the canonical Tender `TDR-225970` (TND-MOH-2027-002) read on kentender.midas.com, 30 Sep 2026; `07_tender_templates/it_equipment_open_v1/06_runtime/product_profile.json` (`supported_use`); `tenders/services/bid_definition.py`; `tenders/services/serializer.py::derived_dates`; `kentender_core/services/procurement_settings.py` |

## 1. Scope predicates (EVL v0.4 §5.1)

EVL v0.4 §5.1: "Read the authoritative published tender definition and require all of: Open Tender; IT Goods with published `product_key` = `IT-EQUIPMENT-OPEN-V1`; one lot; KES; fixed price; lowest-evaluated-responsive method. Never infer these from a title or use defaults."

The published definition (`Tender Bid Definition.definition_json`) carries `template_release_id` and `product_profile_id`. The installed release's `product_profile.json` publishes `supported_use`, which is immutable for that release and digest-checked by `std_templates/services/runtime.py::asset_json`. The Tender record carries `product_key`. Each predicate binds to exactly one of these published values:

| Predicate | Bound published field | Canonical value (TND-MOH-2027-002) | Mismatch treatment |
|---|---|---|---|
| Open Tender | release `product_profile.supported_use.procurement_method` for the definition's `template_release_id` | "Open Tender" | Known unsupported → no case, no tasks |
| IT Goods, product key | `Tender.product_key` and the definition's release `template_key` must both equal `IT-EQUIPMENT-OPEN-V1`; `supported_use.procurement_category` = "Goods" | `IT-EQUIPMENT-OPEN-V1`, `IT-EQUIPMENT-OPEN-V1`, "Goods" | Known unsupported → no case. `product_profile_id` (`GOODS-IT-SIMPLE-V1`) is never used as the key (§5.1 identifier provenance) |
| One lot | `supported_use.lotting_indicator` and `supported_use.award_packages` | "Single lot", 1 | Known unsupported → no case |
| KES | `supported_use.currency` and every `price_rows[].currency` in the definition | "KES", "KES" | Known unsupported → no case |
| Fixed price | `supported_use.price_treatment` | "Fixed price" | Known unsupported → no case |
| Lowest evaluated responsive | `supported_use.financial_evaluation` and the `EVG-FINANCIAL` group `purpose` | "Arithmetic and financial evaluation under the lowest-evaluated-responsive treatment" | Known unsupported → no case |

**Missing or conflicting metadata** (a release asset that cannot be read, a field absent, two sources disagreeing): a named issue for the Tenders owner, with no preparation or assessment tasks, retried on the same publication identity after repair (§5.1).

**Why not the Tender projection.** `bid_definition.projection()` writes `procurement_method: "Open Tender"`, `currency: "KES"` and `lotting_indicator: "Single lot"` as literals. They agree with the release today, but a literal is a default, not a published fact. The seam reads the release values instead, and FU-EVL-02 asks TPR to state the binding.

## 2. Dated rules (EVL v0.4 §5.7)

| Rule | Source found | Canonical value | Treatment |
|---|---|---|---|
| Tender validity end | The published definition's `RR-TENDER-SECURITY` group fact `validity_date`, computed by `serializer.derived_dates` as the submission deadline's date + `tender_validity_days` | 2027-10-10. With the deadline time 11:00 EAT this is the spec's "10 Oct 2027, 11:00 EAT" (§9.11 D07-EXPIRED) | `dated_rules` returns the date, the counting rule ("submission deadline date + validity days"), the source (published definition) and the timezone (site time, EAT). The time of day is the submission deadline's own time; this is stated, not assumed silently. |
| Statutory evaluation deadline | **None authoritative.** `evaluation_period_days` (30) is a Planning schedule profile value (`procurement_settings.PERIOD_BY_MILESTONE`), a planning assumption, not a dated legal rule. No Regulatory Reference kind carries it. | The spec fixture "12 Jul 2027, 11:00 EAT" is 30 days after the 12 Jun 11:00 opening, "supplied by the fixture's dated legal rule" (§9.11 D07-OVERDUE) | **C24.** `dated_rules` returns the evaluation deadline only from an authoritative dated rule. Until Tenders or LAW supplies one, the deadline is shown as not yet available and no overdue condition is raised. A planning assumption is never presented as the statutory deadline (§5.7: "do not guess"). The D07-OVERDUE boards are proven with a simulation-only dated rule (plan D16). FU-EVL-02 and FU-EVL-10. |
| Validity extension | None under TPR v0.13 | — | Simulation-only owner event (plan D8) |

## 3. Canonical reference

The canonical Tender is **TND-MOH-2027-002** ("Clinical training and deployment laptops for digital health rollout"), `TDR-225970`. EVL v0.4 §9.1 names **TND-MOH-2027-033** ("Supply and delivery of business laptops"), and the boards draw 033. As in Bid Opening (its handoff fixture `EV-IN-033-01` is "illustrative"), the canonical stage evaluates 002 with the actual source facts, and the boards' 033 literals are fixture data that the runtime replaces (C21).
