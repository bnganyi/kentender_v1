# Change request — KT-STD-001: journey position figure and blocked next step

**Target:** KT-STD-001 Document, Design and Verification Standards, **v1.22 (Proposed, 4 Oct 2026; v1.21 is the approved standard)**
**Proposed version:** v1.23, Proposed (one concern: workflow-guidance presentation). The owner may instead fold this into v1.22 before approving it. See decision K1.
**Source:** design approval of 6 October 2026, quoted verbatim: “2e it is. Approved”. Design detail: *Handoff — DS-REV-004 Journey position figure and blocked step*.
**Method:** apply the anchored edits below with `scripts/apply_edits.py` to a new file, then run `preservation_check.py`, `consistency_check.py` and `register_check.py`. This change request is not the revision. No KT-STD file has been edited.

---

## 1. Read list

- **Read in full:** KT-STD-001 v1.22 lines 1–460: front matter, control table, §§1–2.9.3, §3, §3A.1–§3A.4. This includes all of §2.6.7, §2.6.11 and §2.9.
- **Not read:** KT-STD-001 v1.22 lines 461–913 (§3A.5 onward, §3B next-step contract, §§4–12). §3B and §12 may need consequential edits; that has not been checked.
- **Not read:** the baseline register KT-DOC-CTRL-001 (`KenTender_Baseline_Register.yaml`). It wasn't supplied, so the current version and status come from the document's own control table only.
- **Not compared:** a second upload, `…v1_22-511d621c.md`. Confirm which v1.22 file is current before editing.

## 2. Why a standard change is needed

§2.6.11 gives Claude Design control of visual treatment, so the new bars and the shape of the blocked block need no rule change. Three rules do touch the approved design:

1. §2.9.2: “Each stage has its label and one marker: done, current, blocked or not started. Only the current stage names its holder.” The position figure is a new element of the tracker that no rule mentions.
2. §2.6.7: “Status colour is supplementary. Every state has explicit text and meets contrast requirements.” The compact track keeps per-stage state text for assistive technology only.
3. §2.9.3 rule 6: “The tracker uses text and neutral markers. The product accent marks only the current stage.” The figure uses the key-figure colour, accent-800.

## 3. Change manifest

| # | Section | Operation | What changes | Source basis | New content? |
|---|---|---|---|---|---|
| E1 | §2.9.2 | Add paragraph | Allow one position figure; state its content and the exception for state text | Approval of 6 Oct 2026 | Yes: rule wording |
| E2 | §2.9.3 rule 3 | Append note | The figure is permitted alongside stage labels and markers | E1 | Yes |
| E3 | §2.9.3 rule 6 | Append note | Colour of the figure; amber when blocked | §2.6.11 items 5–6 | Yes |
| E4 | §2.9.1, blocked row | Append note | Shape of the blocked container; its warning rule is not an accent rule | Approval of 6 Oct 2026 | Yes |
| E5 | Front matter, control table | Version, status, change-type row, successor paragraph | v1.23 Proposed | Protocol | Yes |

## 4. Anchored edits

Each anchor is quoted from v1.22 and must match exactly once.

**E1 — §2.9.2.** Anchor:
> Stages are formal steps a person performs. A computed condition, such as budget fit, is never a stage: it appears as the current stage's blocked marker and in the next-step block.

Append after it:
> (v1.23) **Position figure.** The tracker may lead with one position figure: the number of the current or blocked stage and the number of stages, in the form “{n} of {N}”, with “Current · {holder}” or “Blocked · {holder}” beneath. The figure is derived from the supplied stages and holder and adds no fact. It is not drawn when no stage is current or blocked, unless the change unit states otherwise. Where the figure is shown, the per-stage state line may be omitted from view, provided that each done stage keeps a check marker and each stage's state remains available as text to assistive technology and in print. This is a stated exception to §2.6.7 “Every state has explicit text” for the tracker only.

**E2 — §2.9.3 rule 3.** Anchor:
> 3. **The tracker is one row.** Stage labels and markers only.

Replace with:
> 3. **The tracker is one row.** Stage labels and markers only. (v1.23: and the position figure in §2.9.2.)

**E3 — §2.9.3 rule 6.** Anchor:
> The tracker uses text and neutral markers. The product accent marks only the current stage.

Replace with:
> The tracker uses text and neutral markers. The product accent marks only the current stage. (v1.23: the §2.9.2 position figure uses the key-figure colour under §2.6.11 item 5 and refers only to the current stage; when that stage is blocked, it uses the warning status colour, with text.)

**E4 — §2.9.1 table, Your turn, blocked.** Anchor:
> The only kind that uses a state-tinted container, in the guidance region.

Replace with:
> The only kind that uses a state-tinted container, in the guidance region. (v1.23: the container has the same shape as the other kinds — a 3 px left rule in the warning status colour over the warning tint, with no icon. That rule is a status mark, not an accent rule, and does not count toward the §2.6.7 limit.)

**E5 — control and front matter.** Add a successor paragraph above “**Proposed successor v1.22 …**”. Set Version to 1.23. Set Status to “Proposed — {date}; v1.21 is the approved standard; v1.22 was Proposed and not approved”. Retain the v1.22 status as “(retained)”. Add a “v1.23 change type” row: “Presentation addition: §2.9.2 position figure and its state-text exception; §2.9.1 blocked-container shape; notes in §2.9.3 rules 3 and 6. No content, permission, workflow, fixture or verification rule changes.” Extend Supersedes. Exact wording depends on K1.

## 5. Decisions for the Project Owner

- **K1 — Version.** Make this v1.23, or fold it into v1.22 before approval? Recommendation: v1.23, which keeps one concern per version and leaves the v1.22 surface change reviewable on its own.
- **K2 — State-text exception (E1).** Accept that done and not-started states are shown by marker and position, with no visible word? Recommendation: accept. If declined, drop the exception sentence from E1. The design then puts back the 12px state line and keeps everything else.
- **K3 — All done.** E1 leaves the figure out when no stage is current or blocked. The design handoff recommends “N of N · Done” for a completed record. Choose one, or leave it to each change unit.
- **K4 — Blocked label.** §2.9.1 doesn't fix the label for the blocked kind. The approved design handoff of 26 Sep 2026 uses “Your turn, blocked”. Recommendation: add that label to the §2.9.1 row in the same edit.

## 6. Corrections needed elsewhere

- **Design system:** DS-REV-004 (companion handoff). It must not ship the figure as default until this change is approved.
- **Change units carrying a journey tracker** (for example the Tender publication screens): the §2.6.8 item 12 briefs need no new content, because the figure is derived. Re-check the first-view budget (§2.9.3 rule 5) on each artboard.
- **KT-STD-001 §2.4:** the outlined-control amendment raised in DS-REV-003 is still open. It is a separate concern and is not included here.

## 7. Not verified

- §3B, §§4–12 and §12 approval scope (not read).
- Agreement with KT-DOC-CTRL-001 (not supplied).
- The two v1.22 copies (not compared).
- The preservation, consistency and register checks have not been run; they run when the edits are applied.
- The contrast figure in the design handoff is worked out by hand.
