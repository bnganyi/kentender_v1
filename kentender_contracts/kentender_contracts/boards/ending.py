# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Recording that a contract did not proceed (CM-CHG-001 v0.8 section 5.14; FU-CM-42; plan Phase 5).

The specification names the outcome but no screen for it, so this is the thin authored form: a link on the agreement summary for the preparer, and a dialog with the reason. When the signing window has ended the
head of procurement's follow-up task opens the agreement summary with this as its primary action. It is registered as a departure from the boards (no artboard draws it)."""

from __future__ import annotations

from kentender_contracts.boards import kit
from kentender_contracts.services.formation_end import KINDS

LABEL = "Record that the contract did not proceed"
KEY = "notproceeding"


def attach(board: dict, *, primary: bool = False) -> None:
	board["dialogs"][KEY] = kit.dlg(LABEL, [kit.fl(kit.sel("Why the contract did not proceed", KINDS[0], KINDS, "kind"), kit.ta("Details", "", "reason"))], "Record", command="RecordContractNotProceeding", args={})
	board["actions"][LABEL] = kit.dialog(KEY)
	if primary:
		board["p"], board["s2"] = LABEL, []
		return
	for region in board.get("regions", []):
		for block in region.get("b", []):
			if block.get("k") == "links":
				block["items"].append(LABEL)
				return


def restriction(board: dict, issue: str) -> None:
	"""The head of procurement's step on an Award restriction: record the owner's resolution. The restriction itself is Award's; this only records that its owner resolved it, with the reference."""
	board["dialogs"]["resolution"] = kit.dlg("Record the resolution", [kit.fl(kit.tx("Resolution reference", "", "reference"), kit.ta("How it was resolved", "", "reason"))], "Record",
		command="RecordRestrictionResolution", args={"issue": issue})
	board["actions"]["Record the resolution"] = kit.dialog("resolution")
	board["p"], board["s2"] = "Record the resolution", []
