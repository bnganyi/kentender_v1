# OVS-CHG-001 v0.6: stage-summary contract (Phase 0, OVS6-0003)

**Status: draft for owner review. Nothing here is approved.** OVS v0.6 §13 says a new summary structure "must be incorporated into the canonical owner/interface definitions during reconciliation, rather than added as contradictory prose beside an old response schema", and none of the filed owner documents carries one (FU-OVS-07). This file is the Phase 0 proposal that those documents would adopt. Sources used: OVS v0.6 §§4, 4.1, 8, 13, 18.2; the review board `design/OVS First Slice Review.dc.html` (views OVS-TPR-01 to 06); the existing hook in the code (`kt_tender_record_links`, `hooks.py:146`). Anything not found in those sources is marked **(proposed)**.

## 1. What the section must do

From OVS v0.6 §8: the Tender record has **Decisions and progress** for the Opening, Evaluation and Award records the reader is authorised to know exist. Each stage shows "status, latest disclosed outcome, actor/date, recorded reason, outstanding matter and authoritative links". One primary **View record** link, plus **View report** or **View supporting records** where applicable. It is "a working section, not a second journey tracker or parallel approval process". Denied stages are omitted; an authorised stage that fails shows **We could not load this stage** and **Try again** while other sections stay usable.

## 2. Provider contract

The hook (proposed name `kt_tender_stage_summaries`, like `kt_tender_record_links`) lists dotted paths. Each is called as `fn(tender=<Tender name>, user=<actor>)` and returns a list of zero or one summaries for its stage. `get_tender` concatenates them in the fixed order Bid opening, Bid evaluation, Award.

| Rule | Detail |
|---|---|
| Permission first | The provider first decides whether the reader may know the stage exists. If not, it returns `[]` and nothing else; denial is never an error. |
| No record yet | A stage with no case returns `[]`. |
| Authorised but failing | After the permission check passes, the provider catches its own failure and returns one entry with `state: "unavailable"` and `error_key: "OVS_STAGE_UNAVAILABLE"`. |
| Escaping exception | An exception that escapes before the permission check finished is logged and the stage is omitted. The caller never infers that a stage exists from an exception (OVS v0.6 §8). |
| Owner decides disclosure | The provider, not Tenders, sets `disclosure` and fills `facts` (OVS v0.6 §13: "Owner-defined disclosure per stage"). Tenders formats nothing and recomputes no outcome (OVS v0.6 §3). |
| Reads only | A provider creates no record, task, event or notification. |

## 3. Summary fields

| Field | Type | Meaning | Source |
|---|---|---|---|
| `key` | text | `bid-opening`, `bid-evaluation` or `award` (the same keys the existing record links use) | existing hook |
| `label` | text | **Bid opening**, **Bid evaluation**, **Award** | board |
| `state` | text | `ok` or `unavailable` | OVS v0.6 §8 |
| `error_key` | text | `OVS_STAGE_UNAVAILABLE` when `state` is `unavailable` | OVS v0.6 §18.2 |
| `status` | text | The owner's own plain status label (board examples: Finalized, Report sent, Reviewing, Returned for correction) | board; owner wording |
| `disclosure` | text | `status_only` or `full` | **(proposed)** |
| `outcome` | label and value, optional | The latest disclosed outcome: Recommendation, No responsive bids, Award, No award and so on; never implies a winner when none is recorded (OVS v0.6 §7) | OVS v0.6 §8 |
| `actor` | text, optional | Who decided, delivered or holds the stage | OVS v0.6 §8 |
| `recorded_at` | instant, optional | The recorded instant, shown in site time with the zone for significant instants (OVS v0.6 §12) | OVS v0.6 §8 |
| `reason` | text, optional | The recorded reason; **Not recorded** when an expected reason is missing (OVS v0.6 §6) | OVS v0.6 §6 and OVS v0.6 §8 |
| `outstanding` | text and holder, optional | The outstanding matter, naming the person only when the owner supplies the assignment (OVS v0.6 §8: prefer "Charles Mutiso is preparing the professional opinion" to "The report is now with Award") | OVS v0.6 §8 |
| `facts` | ordered list of `{label, value}` | Each distinct fact is its own labelled pair; nothing is joined with a separator | board; project discipline |
| `version` | text, optional | The report or record version the facts come from | OVS v0.6 §13 ("version reference where applicable") |
| `notice` | text, optional | One plain line explaining a limit, for example the status-only line | board |
| `links` | list of `{key, label, route}` | Order: primary **View record**, then **View report** or **View supporting records** when applicable. A link is present only if the reader can open its target | OVS v0.6 §8 |

**(proposed)** Fields not named in OVS v0.6: `state`, `error_key` (the key is OVS's, the field is not), `disclosure`, `notice`. The board draws status-only blocks with a line of this kind but names no field.

## 4. Facts per owner

The facts below are what the review board draws. Values shown as `[ … ]` on the board are not supplied by any approved owner document (FU-OVS-04) and stay open until the owner design sections exist.

### 4.1 Bid opening

| Disclosure | Facts | Source |
|---|---|---|
| Full (after the reveal) | Opening completed (instant); Bids opened (number); Minutes (state, wording from BOP) | board view OVS-TPR-02 |
| Status only (before the reveal) | Status; scheduled opening instant **(proposed)** | BOP v0.11 sealed-box rule |
| Link | **View record** | `["tenders", <reference>, "opening"]` |

### 4.2 Bid evaluation

| Disclosure | Facts | Source |
|---|---|---|
| Full, report delivered | Recommendation (bidder); Evaluated total; Report sent (instant); Sent to (name); Recorded reason | board view OVS-TPR-01 |
| Status only | Committee appointed (date); Evaluation deadline (date); Chair (name); the line **Bid details are shared with you when the committee's report is sent.** | board view OVS-TPR-03 |
| Returned | Report 1 recommendation; Evaluated total; **Returned for correction**; the return reason; the line **A corrected report is being prepared.** | board view OVS-TPR-04; OVS §7 |
| Links | **View record** and, when delivered and permitted, **View report** | `["tenders", <reference>, "evaluation"]` |

### 4.3 Award

| Disclosure | Facts | Source |
|---|---|---|
| Full, decision recorded | Stage, Outcome, Decision recorded (instant) and a decision-reason summary, in Award's own words | OVS-P03; board view OVS-TPR-05 (values `[ … ]`) |
| Before a decision | Stage only; the outstanding matter and, when Award supplies it, the person preparing the opinion | OVS v0.6 §8 |
| Link | **View record** | `["award", <award name>]` |

## 5. Head of User Department

OVS-P01 to P03 give the department head: administrative Tender progress and the revealed Opening summary; Evaluation administrative progress before delivery and a scoped summary of the delivered outcome and reasons after, "with correction/expiry status", but "no full bid, committee notes or full report access"; and the final Award decision, outcome, date and a reason summary, but not the draft opinion, unissued notices or correspondence. The provider decides this from the Tender's lead or contributing departments through the existing `department` reader mode (`tenders/services/tender_authorization.py:153`).

## 6. Where the contract differs from today

| Today | Contract |
|---|---|
| `record_links` returns `{key, label, route}` only | Summary adds status, disclosure, facts, outcome, actor, time, reason, outstanding matter and links |
| Provider returns `[]` for any denial | Same, plus an explicit `unavailable` entry for an authorised failure |
| Header buttons on `PublishedScreen.vue` (12–18) | Replaced by the section once each equivalent link works; `kt_tender_record_links` stays for other consumers until the TPR version retires it |

## 7. Open points (owner or Phase 1)

| # | Point | Why it is open |
|---|---|---|
| OP-1 | **Decided 4 Oct 2026: a department-level view** (owner: "FU-OVS-40: a department-level view"). **Where a department head's View record goes.** The Evaluation route today returns Not found to a department head (`bid_evaluation/services/reads.py` `require`). OVS-P02 gives the department head a scoped summary but "no full report". Either the Evaluation and Award routes render a department-level view, or the department head's block carries no link. | No owner document says which. |
| OP-2 | **Placement.** TPR v0.17 §10.10 gives none. The board puts the section after the current facts, as the retired OVS v0.1 proposed. | TPR design section (FU-OVS-02) |
| OP-3 | **The Evaluation line after Award takes over.** The board still shows "The Head of Procurement will review the report." in a delivered block; OVS v0.6 §8 prefers naming the person preparing the opinion once Award supplies it. | Board predates the v0.6 wording; Award must supply the assignment (plan D9) |
| OP-4 | **One-bid fixture.** The board shows "Bids opened 1"; the canonical Tender has four bids. | FU-OVS-19 |
| OP-5 | **Disclosure word.** `status_only` and `full` are this file's names. | Naming belongs to the owners |
