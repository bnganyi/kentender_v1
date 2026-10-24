"""Writes recovery_matrix.md from CM v0.8 §5.17/§5.18 (verbatim) and kentender_contracts/services/recovery.py (the code model).

Usage, from reconciliation/:
  PYTHONPATH=../../../../kentender_contracts python3 tools/build_recovery_matrix.py > recovery_matrix.md

The specification's four columns are copied verbatim with the source line. The right-hand columns are the code model, which is
authored (a reading of the prose into guarded consequences) and is marked for owner review. `test_cm_recovery_matrix` fails
if the specification's rows and the model's rows differ, or if this file is stale."""
import sys
from pathlib import Path

from kentender_contracts.services import recovery
from kentender_contracts.services.capabilities import CAPABILITIES

HERE = Path(__file__).resolve().parent
SPEC = HERE.parents[1] / "KenTender_CM-CHG-001_Contract_Management_v0_8.md"
DATE = "14 October 2026"


def spec_rows(section: str, next_section: str, width: int) -> list[tuple[int, list[str]]]:
	lines = SPEC.read_text().splitlines()
	start = next(i for i, line in enumerate(lines) if line.startswith(section))
	end = next(i for i, line in enumerate(lines) if i > start and line.startswith(next_section))
	rows = []
	for i in range(start, end):
		line = lines[i]
		if line.startswith("| ") and not line.startswith("|---"):
			cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
			if len(cells) == width:
				rows.append((i + 1, cells))
	return rows[1:]  # the header row


def operations() -> list[tuple[int, list[str]]]:
	return spec_rows("### 5.17", "### 5.18", 4)


def corrections() -> list[tuple[int, list[str]]]:
	return spec_rows("### 5.18", "### 5.19", 3)


def esc(text: str) -> str:
	return text.replace("|", "\\|")


def render() -> str:
	ops, cors = operations(), corrections()
	out = ["# CM-CHG-001 v0.8: recovery and correction matrix", "", "| Control | Value |", "|---|---|", "| Version | 0.8-recovery.1 |", f"| Date | {DATE} |",
		"| Source | CM v0.8 §5.17 and §5.18, copied verbatim by `tools/build_recovery_matrix.py` (tracker CM8-304); code model in `kentender_contracts/services/recovery.py` and `capabilities.py` |",
		"| Status | The specification columns are approved text. The **Code model** columns are an authored reading of the prose into guarded consequences and are **for owner review** |", "",
		f"**Counts:** {len(ops)} operation rows (§5.17) and {len(cors)} correction rows (§5.18).", "",
		"**Rule** (CM v0.8 §5.17, verbatim): \"Evaluate every open hold independently. The permitted action set is the intersection of all applicable guards; the most prominent task never masks another restriction.\"", "",
		"## Guarded consequences", "", "| Key | Consequence a hold can block |", "|---|---|"]
	out += [f"| `{key}` | {label} |" for key, label in CAPABILITIES.items()]
	out += ["", "Recording a fact, an issue, a supplier claim or a lawfully required liability is never blocked by a hold; it stays within the actor's authority (§5.17).", "",
		"## §5.17 Operation failure and permitted-work matrix", "",
		"| ID | Pending / failed operation | Truthful state and permitted work | Blocked consequences | Recovery / resumption | Spec line | Code model: raised by | Blocks | Recovery owner |", "|---|---|---|---|---|---|---|---|---|"]
	for row, (line, cells) in zip(recovery.OPERATIONS, ops):
		assert cells[0] == row.name, (cells[0], row.name)
		raised = ", ".join(row.kinds) + (f" (subject `{row.subject}…`)" if row.subject else "") + (f"; states {', '.join(row.states)}" if row.states else "") if row.kinds else f"state: `{row.condition}`"
		out.append(f"| {row.id} | {esc(cells[0])} | {esc(cells[1])} | {esc(cells[2])} | {esc(cells[3])} | {line} | {esc(raised)} | {', '.join('`%s`' % b for b in row.blocks)} | {row.owner} |")
	out += ["", "## §5.18 Corrections and downstream consequences", "",
		"| ID | Changed fact | Required treatment | History and resumption | Spec line | Code model: holds | Invalidates | Owner |", "|---|---|---|---|---|---|---|---|"]
	for row, (line, cells) in zip(recovery.CORRECTIONS, cors):
		assert cells[0] == row.name, (cells[0], row.name)
		out.append(f"| {row.id} | {esc(cells[0])} | {esc(cells[1])} | {esc(cells[2])} | {line} | {', '.join('`%s`' % b for b in row.blocks) or '—'} | {row.invalidates or '—'} | {row.owner} |")
	out += ["", "## Reversal order of native documents", "",
		"Proved by spike S7: a later document blocks the cancellation of an earlier one, so a reversal runs in this order and never the reverse.", "",
		"| Reverse first | Then | Source |", "|---|---|---|"]
	out += [f"| {first} | {then} | Spike evidence `evidence/v0_8/spike/` (S7), tracker B-findings |" for first, then in recovery.REVERSAL_ORDER]
	out += ["", "## Boundaries this model keeps", "",
		"- **A pending operation changes no lifecycle state and no signature.** The case stays Active, Closed or Terminated as it was; a retry never asks for a repeat signature (§5.17: \"no repeat report signatures\", \"no fresh AO close-out signature for technical retry\", \"No fictional rollback of signatures\").",
		"- **Recovery reads the owner first.** `services/intents.py` looks up the owner's document by operation identity and links what exists before any retry.",
		"- **Termination and closure share the funding-finalisation row (R17-08).** A failed owner finalisation holds only `mark_financially_finalised` and `release_funds`; `close_contract` stays permitted and surviving payment and warranty duties stay assigned.",
		"- **Dispatches have no row.** A failed or uncertain Report dispatch or Notice dispatch is retried by its own recovery and holds nothing; §5.17 lists no blocked consequence for it.",
		"- **A correction request holds only the affected scope.** `Hold.scope` names the subjects; unaffected separable lines stay eligible (§5.18). R18-07 places no hold; it invalidates the pending approval.", ""]
	return "\n".join(out)


if __name__ == "__main__":
	sys.stdout.write(render())
