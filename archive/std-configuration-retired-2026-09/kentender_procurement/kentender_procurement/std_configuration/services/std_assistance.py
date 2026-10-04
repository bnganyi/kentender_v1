# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 §16.2 draft assistance engine.

§19: "AI assistance is an optional authoring adapter behind the proposal
contract; the core runtime works without it." This module owns the *proposal
contract* only — validate a caller-supplied set of proposed items, store them
as an immutable-until-decided `STD Cfg Assistance Batch`, and let the
Configurator accept/reject each one individually. It does not call an AI
service and does not read `std_engine`'s live DocTypes at runtime (§2.3, §19)
— *producing* the candidate proposals (an AI call, or Phase 10's real
reuse-bundle transformation) is a separate adapter's job, upstream of
`prepare_proposal`. `prepare_proposal` itself is shared by both §13.2 commands
(`PreparePriorConfigurationProposal`/`PrepareAIAssistedDraftProposal`) — they
differ only in `assistance_type` and, for the real Phase 10 adapter,
*where the caller sourced `proposed_items` from* — never in how this module
validates, stores, or later accepts/rejects them.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_configuration.services.std_authorization import (
	CAP_CONFIGURE,
	require_draft_capability,
)
from kentender_procurement.std_configuration.services.std_errors import (
	STD_ASSISTANCE_STALE,
	std_throw,
)
from kentender_procurement.std_configuration.services.std_lifecycle import (
	REFERENCE_SCOPED_CONTENT_DOCTYPES,
)

# §16.2 — a proposal may only target a real, already-modeled domain doctype;
# never an arbitrary/unknown one.
ALLOWED_TARGET_ENTITIES = set(REFERENCE_SCOPED_CONTENT_DOCTYPES)


def _validate_proposed_items(proposed_items: list[dict]) -> None:
	if not proposed_items:
		frappe.throw(_("At least one proposed item is required"))
	for item in proposed_items:
		missing = [k for k in ("proposed_item_label", "owning_area", "target_entity", "proposed_payload") if not item.get(k)]
		if missing:
			frappe.throw(_("Proposed item is missing required field(s): {0}").format(", ".join(missing)))
		if item["target_entity"] not in ALLOWED_TARGET_ENTITIES:
			frappe.throw(_("{0} is not a governed proposal target").format(item["target_entity"]))
		if not isinstance(item["proposed_payload"], dict):
			frappe.throw(_("proposed_payload must be an object"))


def prepare_proposal(
	draft_name: str,
	assistance_type: str,
	input_reference: str,
	proposed_items: list[dict],
	actor: str | None = None,
) -> "frappe.model.document.Document":
	"""§13.2 `PreparePriorConfigurationProposal`/`PrepareAIAssistedDraftProposal`.
	§16.2 — "Assistance failure or cancellation creates no package change": if
	`_validate_proposed_items` throws, nothing has been written yet."""
	draft = frappe.get_doc("STD Cfg Draft", draft_name)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_CONFIGURE, draft)
	_validate_proposed_items(proposed_items)

	batch = frappe.get_doc(
		{
			"doctype": "STD Cfg Assistance Batch",
			"draft_id": draft.name,
			"assistance_type": assistance_type,
			"input_reference": input_reference,
			"actor": actor,
			"proposals": [
				{
					"proposed_item_label": item["proposed_item_label"],
					"owning_area": item["owning_area"],
					"target_entity": item["target_entity"],
					"current_draft_state": item.get("current_draft_state") or "Not configured",
					"status": "Proposed",
					"proposed_payload": frappe.as_json(item["proposed_payload"]),
				}
				for item in proposed_items
			],
		}
	)
	batch.insert(ignore_permissions=True)
	return batch


def _load_batch_and_assert_fresh(batch_id: str):
	batch = frappe.get_doc("STD Cfg Assistance Batch", batch_id)
	draft = frappe.get_doc("STD Cfg Draft", batch.draft_id)
	if int(draft.record_version or 0) != int(batch.draft_record_version_snapshot or 0):
		std_throw(STD_ASSISTANCE_STALE)
	return batch, draft


def _proposal_rows(batch, item_names: list[str]):
	by_name = {row.name: row for row in batch.proposals}
	rows = []
	for item_name in item_names:
		row = by_name.get(item_name)
		if not row:
			frappe.throw(_("Proposal item {0} not found in this batch").format(item_name))
		if row.status != "Proposed":
			frappe.throw(_("Proposal item {0} is already {1}").format(item_name, row.status.lower()))
		rows.append(row)
	return rows


def accept_items(batch_id: str, item_names: list[str], actor: str | None = None) -> dict:
	"""§13.2 `AcceptAssistanceItems` / §16.2 — "The Configurator reviews each
	proposed item... and accepts or rejects it deliberately. There is no
	Accept all." — enforced simply by requiring an explicit, non-empty
	`item_names` list; nothing is ever accepted implicitly.

	§17.7 — "Accepted content loses its 'legacy'/'AI' operational character":
	the created record passes through the SAME `insert()` path (and therefore
	the same Phase 1/2 validators) as any directly-authored row."""
	if not item_names:
		frappe.throw(_("At least one proposal item must be named — there is no Accept all"))
	batch, draft = _load_batch_and_assert_fresh(batch_id)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_CONFIGURE, draft)

	accepted = []
	for row in _proposal_rows(batch, item_names):
		payload = frappe.parse_json(row.proposed_payload)
		doc = frappe.get_doc(
			{
				"doctype": row.target_entity,
				"reference_doctype": "STD Cfg Draft",
				"reference_name": draft.name,
				**payload,
			}
		)
		doc.insert(ignore_permissions=True)
		row.status = "Accepted"
		row.accepted_entity_name = doc.name
		accepted.append({"proposal_item": row.name, "target_entity": row.target_entity, "created": doc.name})

	batch.save(ignore_permissions=True)
	draft.db_set("record_version", (draft.record_version or 0) + 1, update_modified=False)
	return {"batch_id": batch.name, "accepted": accepted}


def reject_items(batch_id: str, item_names: list[str], actor: str | None = None) -> dict:
	"""§13.2 `RejectAssistanceItems` — no content is ever created for a
	rejected item."""
	if not item_names:
		frappe.throw(_("At least one proposal item must be named"))
	batch, draft = _load_batch_and_assert_fresh(batch_id)
	actor = actor or frappe.session.user
	require_draft_capability(actor, CAP_CONFIGURE, draft)

	rejected = []
	for row in _proposal_rows(batch, item_names):
		row.status = "Rejected"
		rejected.append(row.name)

	batch.save(ignore_permissions=True)
	return {"batch_id": batch.name, "rejected": rejected}
