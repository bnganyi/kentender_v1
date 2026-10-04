---
name: kentender-document-change
description: Mandatory protocol for creating, revising, enhancing, correcting, reconciling, reviewing or marking approved any KenTender requirements document — KT-STD, AUTH, STR, BUD, NDS, PLN, REQ, TPR, TPUB, BDS, CFG, STD-TPL, STD-ST, STD-STD, LAW, SEED, DSP change units, ADRs, amendments, trackers and the document registry. Use it for every such task, however small ("fix one line", "mark approved", "weave this in", "reconcile these", "add a section", "review this document"), and whenever a KenTender file is uploaded for change. It prevents lost content, invented facts, broken cross-references and unverified claims.
---

# KenTender document change protocol

KenTender's requirement documents are approved legal-and-product contracts for a public e-procurement system. One silent omission or invented fact can reach production and public procurement. This protocol exists because past edits dropped approved content, invented identifiers, treated build behaviour as rules and reported documents from memory. See `references/lessons.md`.

The protocol makes errors **visible and small**. It cannot make them impossible. Follow every step for every change; the steps are cheap compared with a defect found in code.

## Non-negotiable rules

1. **Patch, never regenerate.** Change a document only through anchored edits (`scripts/apply_edits.py` or equivalent exact-once replacements). Never write out a whole document from your understanding of it.
2. **Prove preservation.** Every revision passes `scripts/preservation_check.py` against the exact previous file, and every changed or deleted original line is listed verbatim in the change report.
3. **Read before writing.** Read the target document and every document the change relies on, in full. If a governing document is needed and not supplied, stop and ask for it. Never draft against a document you have not read.
4. **Quote, don't summarise, when stating what a document says.** Cite section and line, and quote short wording. A statement about another document that you haven't just read is marked unverified.
5. **Keep sources, observations and proposals apart.** An approved document states a rule. A build, screenshot or draft shows an observation or a proposal. Never let an observation become a rule without the owner's decision.
6. **Label everything new.** Any identifier, fixture value, wording or figure that doesn't come from a source is listed as new content for the owner to review.
7. **Law and regulation.** State a legal or regulatory proposition only from the primary text read in full. Otherwise write "not verified against the primary source".
8. **The owner decides.** Domain decisions, legal interpretations and approvals belong to the Project Owner. Record them only when the owner states them, and quote the instruction in the approval record.

## Workflow

Work continuously through these steps. Stop only for the reasons in "When to stop", not to report progress between steps.

### Step 0 — Establish the ground

- Read the baseline register, **KT-DOC-CTRL-001** (`KenTender_Baseline_Register.yaml`). It is the canonical record of every controlled document's version and status, and of interfaces, decisions, delivery items and audit findings. Use it, not memory or earlier turns, for current versions. If a document's own control table disagrees with the register, report the disagreement; don't pick one silently.
- Confirm that you have the **current** version of every file you will change or rely on. Use uploaded files, not earlier turns or memory. If a later version may exist, ask.
- Start large changes in a fresh session with the registry and the exact files uploaded. Long sessions degrade recall.

### Step 1 — Read

- Read the target document in full, then every authority the change touches: sibling documents, KT-STD-001, the fixture register, and legal sources when relevant.
- Keep a read list in the form "read in full: …; read in part: … (sections); not read: …". It goes into the report.
- Note every conflict you find between documents, with section and line. Don't resolve a conflict silently.

### Step 2 — Plan the change

Write a change manifest before editing:

| Section | Operation | What changes | Source basis | New content? |
|---|---|---|---|---|

Then decide:

- **Version impact.** A domain change bumps the version and sets Status to Proposed ("Proposed — vX was Approved; re-approval required"). Marking approved is a separate, explicit step on the owner's instruction.
- **Scope.** Prefer one concern per version. Split a request that bundles a domain decision, new commands, fixtures and reconciliation, unless the owner asks for it together.
- **Other documents.** Each change needed in another document is named as a required correction in this one, and is never assumed.
- **Owner decisions.** List questions only the owner can answer. Give your recommendation, and don't encode a recommendation as decided.

For large or domain-affecting changes, show the manifest and wait for agreement. For editorial or narrowly specified changes, continue.

### Step 3 — Edit

- Use `scripts/apply_edits.py` with a JSON list of edits. Each anchor must match exactly once, and the output goes to a new versioned file. The original is never modified.
- **Correct by addition.** Keep superseded wording beside the correction, for example "(v1.26 read: BUD v1.9)", or keep the old row labelled "superseded … retained as history". Never compress existing content into a summary or a pointer back to an earlier version.
- Update the control table, change scope, change register, traceability and approval-effect sections for the new version. Keep the previous version's approval effect as "(retained)".
- When one `§` refers to another document, name that document immediately before it ("KT-STD-001 §8.3"), even if the sentence already named it.
- Reuse existing identifiers, error codes, labels and actors. Search the document before adding any code, ID or name.
- Apply `references/project-disciplines.md` to all new text.

### Step 4 — Verify

Run both scripts and resolve every result:

```bash
python scripts/preservation_check.py PREVIOUS.md REVISED.md --allow-control-table
python scripts/consistency_check.py REVISED.md --actors KT-STD-001.md --registry KenTender_Baseline_Register.yaml
python scripts/register_check.py KenTender_Baseline_Register.yaml --docs REVISED.md [other current documents]
```

- **preservation_check** must PASS. Any other allowed change needs its own `--allow` and a stated reason in the report.
- **consistency_check** must show no ERROR introduced by this change. Report pre-existing errors as findings; don't fix them silently.
- **register_check** must show that the register and the revised document agree on version, status and approval date, or the report must say that the register needs updating.
- **Manual checks:**
  - Recompute every number stated in new text: totals, sums, percentages, counts of criteria and rows.
  - Confirm every new fixture fact is consistent with the fixture register and with other fixtures.
  - Confirm no new text joins unrelated facts on one line with a delimiter (the delimiter-cramming rule).
  - Confirm every statement about another document or the law is quoted from a source read this session.
- If a check fails, fix it with another anchored edit and rerun both scripts.

### Step 5 — Report

End every change with this report. No confident summary replaces it.

1. **Files:** input file, output file, version and status.
2. **Read list:** read in full / in part / not read.
3. **Changes by section:** from the manifest, as made.
4. **Preservation result:** counts, plus every changed or deleted original line, verbatim, with its reason.
5. **Consistency result:** errors and warnings, marked as introduced or pre-existing.
6. **New content for review:** every identifier, fixture value, wording or figure not taken from a source.
7. **Decisions needed:** owner questions, each with a recommendation.
8. **Required corrections elsewhere:** other documents that must change.
9. **Not verified:** everything you did not or could not check.

## When to stop and ask

- A governing document the change depends on is missing or may be out of date.
- The change needs a domain, legal or policy decision that no approved document states.
- Documents conflict and the resolution would change a rule.
- A preservation or consistency failure can't be fixed without removing approved content.

Otherwise, keep working until the report is complete.

## Marking a document approved

Only on the owner's explicit instruction. Change:

- the control-table Status, Approved on and Approval record (quote the instruction);
- the current version's approval-effect sentence, from proposed to declarative ("vX is approved by the Project Owner …").

Nothing else changes in the document. Run both scripts afterwards.

Then update the register entry, following its own governance rule. Set `requirement_status`, `approval_date`, `version`, `filename` and `supersedes`, and update any interfaces, decisions, delivery items or audit findings the approval changes. Never change `implementation_status`, `verification_status` or `release_status` because a document was approved: the register's `status_rule` forbids using approval as evidence. Run `register_check.py` on the updated register.

## Reviews without edits

When asked to review, apply Steps 0, 1, 4 and 5. Run `consistency_check.py` on every supplied document. Separate findings you verified in the text from judgements, and say which parts of which documents you did not read.

## Using this protocol in Claude Code

Run the scripts from the repository. Commit the manifest, the new version file and the report together. Never edit an approved file in place: every revision is a new versioned file, whose predecessor stays unchanged as evidence. CI may run `consistency_check.py` on all documents, `preservation_check.py` on every changed document against its predecessor, and `register_check.py` on the register with the current documents.
