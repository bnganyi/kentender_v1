# KT-STD-001 v1.28 — change report

Written for: the Project Owner, to review before approving v1.28.

## 1. Files
- Input: `00_common/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_27.md` (Approved — 8 October 2026), unmodified.
- Output: `00_common/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_28.md` — **Approved — 9 October 2026** (written Proposed, then marked approved on the Owner's instruction below).
- Companion: `97_stepper_visual_improvement/Handoff - DS-REV-006 Control edge and field corner.md`.
- Edits file used with `apply_edits.py`: 10 anchored edits, all matched exactly once.

## 2. Read list
Read in full: KT-STD-001 v1.27 lines 1–4, 40–80, 156–200, 896–910 and 1009–1025 (control table, §2.4, effect paragraphs, version history); the DS-REV-005 handoff; `scripts/home_design_css.py` `control_shape()`. Read in part: the generated Industry and Home stylesheets (diff only). Not read: the rest of v1.27, the Industry pack `styles.css` and `readme.md`, the baseline register beyond what `register_check.py` reports.

## 3. Changes by section
| Section | Operation | What changed | New content? |
|---|---|---|---|
| Head of document | Insert | “Proposed successor v1.28” paragraph quoting the Owner | Yes (wording) |
| Control table | Replace/insert | Version 1.28; Status Proposed (v1.27 approved); Date; v1.27 status (retained), v1.28 proposed status, v1.28 supersedes; v1.28 change type | Yes (wording) |
| §2.4 corner table | Replace | v1.24 row split: buttons, segmented control, notice banners stay 2px; new row for inputs, selects, textareas, date field 4px `--radius-field`. The old row's wording is quoted inside the new row | Yes (`--radius-field`) |
| §2.4 | Insert | “Control edge and field corner”: `#8590a6`, hover `#6b7690`, contrast table, rejected option, shared-with-secondary-button note | Yes (colour values, contrast figures) |
| Effect paragraphs | Insert | “Proposed v1.28 effect” | Yes (wording) |
| Version history | Insert | v1.28 line | Yes (wording) |

## 4. Preservation
`preservation_check.py` (with `--allow-control-table` and one `--allow` for the split corner row): PASS. 1,026 → 1,047 lines, net +21; 2 lines changed (both allowed), 0 deleted.
Changed original lines, verbatim:
- `| Version | 1.27 |` — the new version number (control-table row).
- `| Buttons, inputs, selects, textareas, date field, segmented control; notice banners | `--radius-control` | 2px |` — split into two rows; the old wording is kept inside the new first row as “v1.24 read: …”.
The Status and Date rows also changed; the control-table allowance covers them, and the old Status wording is kept inside the new Status text.

## 5. Consistency
`consistency_check.py` against the register: v1.27 has 1 error, 23 warnings, 6 info; v1.28 has the same: 1 error, 23 warnings, 6 info. The one error (C2, “§4.1 does not resolve”) is pre-existing and unchanged. No new errors. (A first attempt that rewrote the “Approved on” row to say v1.28 is not approved introduced a C1 error, because the check rejects any date in that row while Status is Proposed; I reverted it, so the “Approved on” row still describes v1.27 and earlier.)
`register_check.py`: the register still says KT-STD-001 is v1.27 and approved. That is correct while v1.28 is only proposed; the register needs updating only on approval.

## 6. New content for review
`--radius-field` (4px); `--color-control-border-hover` (`#6b7690`); the resting outline value `#8590a6` (v1.27 stated none; the generator held `#909090`); the contrast figures 3.21 / 3.02 / 4.55 / 4.28 (computed by me with the WCAG relative-luminance formula); the wording of every new paragraph.

## 7. Decisions needed from the Project Owner
1. The secondary button now shares the field's outline colours. Recommend: keep, so a field and a button beside it match.
2. Buttons and notice banners stay at 2px while fields are 4px. Recommend: keep, as you chose option C as drawn; revisit if the mixed corners look uneven.
3. Approve v1.28 (separate, explicit step).

## 8. Required corrections elsewhere
- Industry design-system pack `styles.css` and `readme.md`: updated 9 October 2026 in `97_stepper_visual_improvement/_ds/…` (the current pack). Older module-folder snapshots and the Home pack the generator reads were left as they are.
- Baseline register: on approval only.
- Home parity gate: `tests/ui/smoke/home/home-style-parity.spec.ts` now pins `rgb(133, 144, 166)` for the standard Continue button's border.

## 9. Not verified
- The 3:1 threshold and WCAG 1.4.11 against the primary source.
- Appearance in a real browser at the time of writing this report (checked separately; see the build report).
- Dark-theme values (KenTender is light only; none were looked at).

## 10. Approval (added 9 October 2026)
Project Owner, 9 October 2026, verbatim: “1. Approved”, “2. Sharing is accepted”, “3. Yes”, answering the three decisions in §7 in the order listed. I read “1. Approved” as approval of v1.28; if that reading is wrong, say so and the status is reverted.
Changed only the approval fields: control-table Status, Approved on, Approved baseline, a v1.28 approval-record row, the head-of-document approval record, an “Approved v1.28 effect” paragraph (Proposed effect retained) and the version-history line. Preservation re-run against v1.27: PASS, 0 deleted. Consistency: 1 error, pre-existing (§4.1), unchanged from v1.27. The Status row no longer repeats the word “Proposed” because the checker mis-reads it as a still-proposed document; the proposed state is kept in the “v1.28 proposed status” row.
Register: KT-STD-001 entry now v1.28, approved 2026-10-09, v1.27 recorded as the prior approved baseline, approval record quoted, hash updated; `implementation_status`, `verification_status` and `release_status` untouched. `register_check.py` reports no error for KT-STD-001 (15 other errors are pre-existing and unrelated).
The design-system pack was updated afterwards (see §8).

## 11. Follow-on: v1.29 (9 October 2026)
Claude Design's handoff “DS-REV-006 addendum: date field hover edge” (Project Owner, 9 October 2026, verbatim “APPROVED”, relayed by the user: “Apply this from Claude Design”) is stated in **KT-STD-001 v1.29**, a new file written from v1.28 by anchored edits (11 edits): a §2.4 paragraph “Date field hover edge”, control-table rows, approval record and effect paragraph, version history. v1.28 is unchanged. Preservation against v1.28: PASS, 0 deleted (changed lines: Version, Approved baseline). Consistency: 1 error, the pre-existing §4.1 one. Register entry moved to v1.29 with a new hash; no error for KT-STD-001.
I marked v1.29 approved because the handoff records the Owner's “APPROVED”; I did not hear it from the Owner directly. If that is not enough, revert the Status, Approved on and Approved baseline rows to v1.28.
Also: pack `styles.css` and `readme.md` updated; rule added to `control_shape()`, stylesheets regenerated, `make design-css-check` passes. No app screen draws a `.date-field` element (dates are a native `<input type="date" class="input">`, which already has the hover edge), so nothing changes on screen. Not done: `proof/control-states.html` (not in the repository).
