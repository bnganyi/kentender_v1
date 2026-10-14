# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract formation: from a received Award package to an agreement in force (CM-CHG-001 v0.8 sections 5.2, 5.3, 5.14, 7; plan Phase 4).

Package received -> **Prepare contract** (HOP, or a person whose Contract preparation responsibility covers the managing unit) -> the agreement generated from the issued Form No. 4 and
the verified sources -> **Send for signature** freezes one version and its source package -> the supplier's authorised signatory signs first, the entity's second, each through the shared
trust facade -> the second proof makes the agreement **Active**, and the native order and the funding conversion follow as durable operations that can fail and be restored without asking
for a new signature.

Every command runs once per key under the case's row lock (`records.command`). A **signing attempt** is two steps because the owner is called outside the command's transaction
(`intents.py`): the command records the decision and a `Recorded` intent atomically; the attempt is then carried out, and its outcome (a proof, a refusal, or "unknown") is applied in its own
transaction. An unknown outcome keeps the same attempt for recovery and shows the truthful state; it never signs twice."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, formatdate, getdate

from kentender_contracts.native import adapter
from kentender_contracts.services import authority, clock, events, intents, parties, people, preflight, records, simulation, source_package, signing_flow, work
from kentender_contracts.services.errors import Guards, fail, invalid
from kentender_core.services import contract_funding_contract as funding_seam
from kentender_core.utils.series import allocation_lock

CASE = "Contract Case"
AGREEMENT = "Contract Agreement Version"
SIGNATURE = "Contract Signature"
PACKAGE = "Contract Source Package"
PARTICULARS = ("agreement_date", "entity_signatory", "supplier_signatory", "item_mapping", "native_supplier", "company", "destination", "asset_location")
LABELS = {
	"agreement_date": "Agreement date", "entity_signatory": "Entity signatory", "supplier_signatory": "Supplier signatory", "item_mapping": "Catalogue item for each line",
	"native_supplier": "Supplier in Finance", "company": "Company", "destination": "Delivery destination", "asset_location": "Asset location",
}
REQUIRED_PACKAGE_KEYS = ("award_case", "tender", "decision", "contract_terms", "restrictions")
SIGNING_METHOD = signing_flow.METHOD


# -- intake ---------------------------------------------------------------------------------------------------------------------------
def _next_contract_id() -> str:
	year = clock.now().year
	allocation_lock(CASE)
	taken = frappe.get_all(CASE, filters={"contract_id": ["like", f"CM-{year}-%"]}, pluck="contract_id")
	last = max((int(i.rsplit("-", 1)[1]) for i in taken if i.rsplit("-", 1)[1].isdigit()), default=0)
	return f"CM-{year}-{last + 1:04d}"


def receive_award_package(package: dict[str, Any], *, handoff: list[dict[str, Any]], managing_unit: str, idempotency_key: str, actor: str, contract_id: str = "") -> dict[str, Any]:
	"""`ReceiveAwardPackage` (service-only): a durable case and one **Prepare contract** task for HOP. A retry returns the existing case (section 5.2)."""

	def body() -> dict[str, Any]:
		award_case = cstr(package.get("award_case"))
		if award_case:
			existing = frappe.db.get_value(CASE, {"source_kind": "KenTender award", "source_reference": award_case}, "name")
			if existing:
				return records.summary(frappe.get_doc(CASE, existing), intake="existing")
		missing = [k for k in REQUIRED_PACKAGE_KEYS if not package.get(k) and k != "restrictions" or k not in package]
		if missing or (package.get("decision") or {}).get("outcome") != "Award":
			fail("CM_SOURCE", missing=missing, reason="The award package is incomplete or is not an award.")
		decision = package["decision"]
		doc = records.new(CASE, contract_id=contract_id or _next_contract_id(), source_kind="KenTender award", source_reference=award_case, supplier_organisation=decision.get("organisation"),
			supplier_name=decision.get("supplier"), managing_unit=managing_unit or None, currency=decision.get("currency"), contract_value=decision.get("evaluated_amount"),
			tender_reference=package.get("tender_reference") or package.get("tender"), award_reference=decision.get("id"), legal_profile=package.get("legal_profile") or "", lifecycle="Preparing",
			received_at=clock.now(), record_version=1, title=cstr(package.get("tender_reference") or package.get("tender")),
			source_json=records.dumps({"package": package, "package_digest": records.digest(package), "handoff": handoff}))
		work.assign(doc.name, "RequestContractSignatures", "Review the contract and send it for signature.", "agreement 1", 1, work.holders(work.HOP), role=work.HOP)
		events.record(doc.name, "Award package received", actor, f"Award package {award_case} received.", award_case=award_case, package_digest=records.digest(package))
		return records.summary(doc, intake="created")

	return records.command("ReceiveAwardPackage", case="", idempotency_key=idempotency_key, actor=actor, payload={"package": records.digest(package), "handoff": records.digest(handoff)}, body=body)


# -- the agreement --------------------------------------------------------------------------------------------------------------------
def current_agreement(case: str, *states: str):
	filters: dict[str, Any] = {"contract_case": case}
	if states:
		filters["state"] = ["in", list(states)]
	name = frappe.db.get_value(AGREEMENT, filters, "name", order_by="version_no desc")
	return frappe.get_doc(AGREEMENT, name) if name else None


def _label_of(user: str, fallback: str = "") -> str:
	return people.full_name(user) if user and frappe.db.exists("User", user) else fallback


def _entity_capacity(user: str) -> str:
	return "Accounting Officer" if people.holds(user, "Accounting Officer") else "Authorised signatory"


def _assemble(doc, particulars: dict[str, Any]) -> dict[str, Any]:
	"""The agreement as it would be generated now: verified sources -> terms, items, rendered Form No. 4, the insertions still empty, the package manifest."""
	source = records.loads(doc.source_json)
	sources = source_package.require(source["handoff"])
	s = {n: v["data"] for n, v in sources.items()}
	entity, supplier_org = s["S10"], s["S11"]
	lines = s["S3"]["lines"]
	entity_user = particulars.get("entity_signatory") or ""
	signatories = [p for p in supplier_org.get("signatories", [])]
	supplier_pick = next((p for p in signatories if p["user"] == particulars.get("supplier_signatory")), signatories[0] if len(signatories) == 1 else None)
	total, currency = s["S3"]["total"], s["S3"]["currency"]
	money = f"{currency} {total:,.0f}" + (", tax included" if s["S3"].get("tax_included") else "")
	values = {
		"agreement_date": formatdate(particulars["agreement_date"], "d MMMM yyyy") if particulars.get("agreement_date") else "", "entity_name": entity["legal_name"], "entity_address": entity.get("address", ""),
		"supplier_name": supplier_org["legal_name"], "goods": ", ".join(f"{cint(l['quantity'])} {l['description']}" for l in lines), "amount": money,
		"documents": ", ".join(label for label, _n, _o in source_package.INCORPORATED),
		"entity_signatory": f"{_label_of(entity_user)}, {_entity_capacity(entity_user)}" if entity_user else "",
		"supplier_signatory": f"{supplier_pick['name']}, {supplier_pick['capacity']}" if supplier_pick else "",
	}
	html, missing = source_package.render(sources["S7"]["data"], values)
	mapping = particulars.get("item_mapping") or {}
	if any(not mapping.get(l["line_id"]) for l in lines):
		missing.append("item_mapping")
	if not _native_supplier(particulars, supplier_org["legal_name"]):
		missing.append("native_supplier")
	if all(mapping.get(l["line_id"]) for l in lines) and any(_creates_assets(mapping[l["line_id"]]) for l in lines) and not particulars.get("asset_location"):
		missing.append("asset_location")
	terms = {
		"title": s["S1"].get("title") or doc.title, "currency": currency, "tax_included": bool(s["S3"].get("tax_included")), "total": total, "lines": lines,
		"delivery": {"due": s["S4"]["delivery_schedule"]["due"], "destination": particulars.get("destination") or s["S4"]["delivery_schedule"].get("destination", "")},
		"warranty": s["S5"]["warranty"], "security": s["S5"]["performance_security"], "advance": s["S5"].get("advance", {}), "payment": s["S5"].get("payment", {}),
		"criteria": s["S6"]["criteria"], "signing_window": s["S8"], "funding": s["S9"], "restrictions": s["S12"].get("restrictions", []),
		"parties": {
			"entity": {"name": entity["legal_name"], "address": entity.get("address", ""), "user": entity_user, "signatory": _label_of(entity_user), "capacity": _entity_capacity(entity_user) if entity_user else ""},
			"supplier": {"name": supplier_org["legal_name"], "organisation": supplier_org.get("organisation"), "user": supplier_pick["user"] if supplier_pick else "",
				"signatory": supplier_pick["name"] if supplier_pick else "", "capacity": supplier_pick["capacity"] if supplier_pick else ""},
		},
		"particulars": particulars,
	}
	return {"sources": sources, "terms": terms, "lines": lines, "html": html, "missing": sorted(set(missing)), "manifest": source_package.manifest(sources)}


def _creates_assets(item_code: str | None) -> bool:
	"""A fixed-asset item whose receipt creates an asset for each unit: each unit then needs a place."""
	if not item_code or not frappe.db.exists("Item", item_code):
		return False
	flags = frappe.db.get_value("Item", item_code, ["is_fixed_asset", "auto_create_assets"], as_dict=True)
	return bool(flags.is_fixed_asset and flags.auto_create_assets)


def _native_supplier(particulars: dict[str, Any], legal_name: str) -> str:
	named = particulars.get("native_supplier")
	if named and frappe.db.exists("Supplier", named):
		return named
	return legal_name if frappe.db.exists("Supplier", legal_name) else ""


def _check_particulars(values: dict[str, Any]) -> dict[str, Any]:
	clean = {k: v for k, v in (values or {}).items() if k in PARTICULARS and v not in (None, "", {})}
	problems: dict[str, str] = {}
	if "agreement_date" in clean:
		try:
			clean["agreement_date"] = str(getdate(clean["agreement_date"]))
		except Exception:
			problems["agreement_date"] = "Enter the agreement date as a date."
	if "entity_signatory" in clean:
		if not frappe.db.exists("User", clean["entity_signatory"]):
			problems["entity_signatory"] = "Choose a person with an account."
		elif not people.holds(clean["entity_signatory"], "Entity contract signing"):
			problems["entity_signatory"] = "This person does not hold the Entity contract signing responsibility."
	if "asset_location" in clean and not frappe.db.exists("Location", clean["asset_location"]):
		problems["asset_location"] = "Choose an existing location."
	if "item_mapping" in clean:
		bad = [k for k, v in clean["item_mapping"].items() if not frappe.db.exists("Item", v)]
		if bad:
			problems["item_mapping"] = "Choose an existing catalogue item for " + ", ".join(bad) + "."
	invalid(problems)
	return clean


def _draft(doc, particulars: dict[str, Any], actor: str):
	"""Create or refresh the Draft agreement from the verified sources."""
	built = _assemble(doc, particulars)
	draft = current_agreement(doc.name, "Draft")
	fields = {"amount": built["terms"]["total"], "currency": built["terms"]["currency"], "operative_date": particulars.get("agreement_date") or None, "terms_json": records.dumps(built["terms"]),
		"items_json": records.dumps(built["lines"]), "missing_json": records.dumps(built["missing"]), "rendered_html": built["html"], "rendered_digest": records.digest(built["html"])}
	if draft:
		records.update(draft, **fields, record_version=cint(draft.record_version) + 1)
	else:
		draft = records.new(AGREEMENT, contract_case=doc.name, version_no=cint(doc.current_agreement) + 1 if doc.current_agreement else 1, state="Draft", record_version=1, **fields)
	records.bump(doc, title=built["terms"]["title"], current_agreement=draft.version_no)
	return draft, built


def save_particulars(case: str, *, expected_version: int, idempotency_key: str, actor: str, values: dict[str, Any] | None = None) -> dict[str, Any]:
	"""`SaveContractParticulars`: the released missing fields, then the agreement regenerated from the verified sources. Reads and saved preparation are never refused by a rule."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Preparing")
		prior = current_agreement(case, "Draft")
		particulars = {**(records.loads(prior.terms_json).get("particulars", {}) if prior else {}), **_check_particulars(values or {})}
		draft, built = _draft(doc, particulars, actor)
		events.record(case, "Particulars saved", actor, "Contract particulars saved.", agreement=draft.name, missing=built["missing"])
		return records.summary(doc, agreement=draft.name, agreement_version=draft.version_no, missing=built["missing"])

	return records.command("SaveContractParticulars", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "values": values or {}}, body=body, authorise=authorise)


# -- send for signature ---------------------------------------------------------------------------------------------------------------
def request_signatures(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RequestContractSignatures`: after the source, authority, rule, restriction and signing-window checks, freeze one complete version and its source package (section 5.3)."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Preparing")
		draft = current_agreement(case, "Draft")
		if not draft:
			fail("CM_CHANGED", reason="No agreement has been prepared.")
		particulars = records.loads(draft.terms_json).get("particulars", {})
		built = _assemble(doc, particulars)
		invalid({k: f"Enter the {LABELS.get(k, k).lower()}." for k in built["missing"]})
		if records.digest(built["html"]) != draft.rendered_digest:
			fail("CM_SOURCE", reason="The source material changed since the agreement was last prepared. Review it again.")
		branches = set() if simulation.enabled() else {preflight.PRODUCTION_BRANCH}
		guards = preflight.rules(doc, "RequestContractSignatures", branches)
		preflight.holds(guards, case, "new_signing_attempt")
		window = built["terms"]["signing_window"]["signing_window"]
		if window.get("ends_on") and getdate(window["ends_on"]) < getdate(clock.now()):
			guards.add("CM_SOURCE", reason="The signing window for this award has ended.", ended_on=window["ends_on"])
		if built["terms"]["restrictions"]:
			guards.add("CM_HOLD", hold="award restriction", kind="Restriction", reason="An award restriction requires review.", holder="Head of procurement function", clears_with="The restriction is resolved by its owner", consequence="new_signing_attempt")
		guards.raise_if_any()
		package = records.new(PACKAGE, contract_case=case, agreement_version=draft.version_no, state="Frozen", manifest_json=records.dumps(built["manifest"]), package_digest=built["manifest"]["package_digest"], frozen_at=clock.now())
		version_digest = records.digest({"text": built["html"], "package": built["manifest"]["package_digest"], "amount": built["terms"]["total"], "currency": built["terms"]["currency"]})
		records.update(draft, state="Awaiting signatures", source_package=package.name, rendered_digest=version_digest, frozen_at=clock.now(), record_version=cint(draft.record_version) + 1)
		parties_ = built["terms"]["parties"]
		subject = f"agreement {draft.version_no}"
		for sequence, (party, who) in enumerate((("Supplier", parties_["supplier"]), ("Entity", parties_["entity"])), start=1):
			records.new(SIGNATURE, contract_case=case, agreement_version=draft.version_no, party=party, sequence=sequence, signer=who["user"], capacity=who["capacity"],
				state="Requested" if sequence == 1 else "Waiting", record_version=1)
		records.bump(doc, lifecycle="Awaiting signatures")
		work.finish(case, command="RequestContractSignatures", subject=subject, actor=actor)
		work.assign(case, "SignContractVersion", "Review the agreement before signing.", subject, draft.version_no, [parties_["supplier"]["user"]], role="Authorised signatory")
		work.assign(case, work.waiting_command("SignContractVersion", "supplier"), "Waiting for the supplier's signature.", subject, draft.version_no, work.holders(work.HOP), role=work.HOP, state="Waiting")
		events.record(case, "Sent for signature", actor, f"Agreement {draft.version_no} sent for signature.", agreement=draft.name, package=package.name, package_digest=package.package_digest)
		return records.summary(doc, agreement=draft.name, agreement_version=draft.version_no, package=package.name)

	return records.command("RequestContractSignatures", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version}, body=body, authorise=authorise)


# -- signing --------------------------------------------------------------------------------------------------------------------------
def _slot(case: str, party: str, *, states: tuple[str, ...] = ()):
	agreement = current_agreement(case, "Awaiting signatures", "Effective")
	if not agreement:
		fail("CM_CHANGED", reason="No agreement is out for signature.")
	filters: dict[str, Any] = {"contract_case": case, "agreement_version": agreement.version_no, "party": party}
	if states:
		filters["state"] = ["in", list(states)]
	name = frappe.db.get_value(SIGNATURE, filters, "name")
	return agreement, (frappe.get_doc(SIGNATURE, name) if name else None)


def _authorise_signing(case: str, party: str, actor: str) -> None:
	from kentender_contracts.services import segregation

	if party not in ("Supplier", "Entity"):
		invalid({"party": "Choose Supplier or Entity."})
	if party == "Supplier":
		organisation = frappe.db.get_value(CASE, case, "supplier_organisation")
		segregation.supplier_signs_only_as_signatory(actor, signatories=parties.signatories(organisation, clock.now()), action="sign")
	else:
		authority.require_capacity(case, actor, "entity signatory")


def _record_attempt(case: str, party: str, expected_version: int, actor: str, key: str) -> dict[str, Any]:
	doc = records.lock(case)
	records.check_version(doc, expected_version)
	preflight.lifecycle(doc, "Awaiting signatures")
	agreement, slot = _slot(case, party)
	if slot is None or slot.state == "Signed":
		return records.summary(doc, agreement=agreement.name, signature=slot.name if slot else "", already=True)
	if slot.signer.lower() != actor.lower():
		fail("CM_AUTHORITY", missing="mandate", reason="This signature is for another person.", capacity=party)
	if party == "Entity":
		supplier = frappe.db.get_value(SIGNATURE, {"contract_case": case, "agreement_version": agreement.version_no, "party": "Supplier"}, "state")
		if supplier != "Signed":
			fail("CM_CHANGED", reason="The supplier signs first.", waiting_for="supplier signature")
	subject = f"signature {party.lower()} agreement {agreement.version_no}"
	existing = signing_flow.existing(case, subject, agreement.version_no, f"sign-{party.lower()}")
	guards = preflight.rules(doc, "SignContractVersion")
	preflight.holds(guards, case, "new_signing_attempt", except_keys=[f"operation:{existing}"] if existing else [])
	terms = records.loads(agreement.terms_json)
	window = terms["signing_window"]["signing_window"]
	if window.get("ends_on") and getdate(window["ends_on"]) < getdate(clock.now()):
		guards.add("CM_SOURCE", reason="The signing window for this award has ended.", ended_on=window["ends_on"])
	if terms.get("restrictions"):
		guards.add("CM_HOLD", hold="award restriction", kind="Restriction", reason="An award restriction requires review.", holder="Head of procurement function", clears_with="The restriction is resolved by its owner", consequence="new_signing_attempt")
	guards.raise_if_any()
	intent = signing_flow.record(case, subject, agreement.version_no, f"sign-{party.lower()}")
	return records.summary(doc, agreement=agreement.name, signature=slot.name, intent=intent.name, party=party)


def sign_contract(case: str, *, party: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignContractVersion`: record the attempt (atomically with its decision), carry it out through the trust facade, then apply the outcome. A proof makes the signature; a
	refusal or an unavailable service keeps the work and the same attempt; an unknown outcome stays pending and is recovered, never repeated with a new signature."""
	preflight.exists(case)
	recorded = records.command("SignContractVersion", case=case, idempotency_key=idempotency_key, actor=actor, payload={"party": party, "expected": expected_version},
		authorise=lambda: _authorise_signing(case, party, actor), body=lambda: _record_attempt(case, party, expected_version, actor, idempotency_key))
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	return _complete_signature(case, recorded, actor)


def _complete_signature(case: str, recorded: dict[str, Any], actor: str) -> dict[str, Any]:
	agreement = frappe.get_doc(AGREEMENT, recorded["agreement"])
	slot = frappe.get_doc(SIGNATURE, recorded["signature"])
	party = recorded["party"]
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=agreement.name, target_digest=agreement.rendered_digest, version=agreement.version_no,
		action=f"Sign the contract agreement as the {party.lower()}")
	if signing_flow.settled(result):
		return _apply_signature(case, slot.name, result["reference"], actor, result["method"])
	pending = result["state"] in ("Attempting", "Uncertain", "Recorded")
	with records.atomic():
		doc = records.lock(case)
		slot = frappe.get_doc(SIGNATURE, slot.name)
		records.update(slot, state="Pending" if pending else "Failed", correlation_id=frappe.db.get_value(intents.INTENT, recorded["intent"], "operation_identity"))
		records.bump(doc)
		work.incident(case, "RestoreContractOperation", "Restore signing", f"signature {party.lower()} agreement {agreement.version_no}", agreement.version_no)
		events.record(case, "Signing not completed", actor, f"The {party.lower()} signature was not completed ({result['state'].lower()}).", intent=recorded["intent"], outcome=result["outcome"] or result["state"])
	frappe.db.commit()
	signing_flow.unfinished(result, party=party)


def _apply_signature(case: str, slot_name: str, proof: str, actor: str, method: str) -> dict[str, Any]:
	with records.atomic():
		doc = records.lock(case)
		slot = frappe.get_doc(SIGNATURE, slot_name)
		if slot.state == "Signed":  # a replay of an applied outcome changes nothing
			return records.summary(doc, signature=slot.name, state="Signed", party=slot.party, **({"effective": True} if doc.lifecycle == "Active" else {}))
		records.update(slot, state="Signed", proof_reference=proof, method=method or SIGNING_METHOD, signed_at=clock.now(), record_version=cint(slot.record_version) + 1)
		agreement = frappe.get_doc(AGREEMENT, frappe.db.get_value(AGREEMENT, {"contract_case": case, "version_no": slot.agreement_version}, "name"))
		subject = f"agreement {agreement.version_no}"
		work.finish(case, command="RestoreContractOperation", subject=f"signature {slot.party.lower()} agreement {agreement.version_no}", actor=actor)
		events.record(case, "Signed", actor, f"Agreement {agreement.version_no} signed for the {slot.party.lower()}.", signature=slot.name, proof=proof)
		if slot.party == "Supplier":
			work.finish(case, command="SignContractVersion", subject=subject, actor=actor)
			entity = frappe.get_doc(SIGNATURE, frappe.db.get_value(SIGNATURE, {"contract_case": case, "agreement_version": agreement.version_no, "party": "Entity"}, "name"))
			records.update(entity, state="Requested")
			work.assign(case, "SignContractVersion", "Review the agreement before signing.", subject, agreement.version_no, [entity.signer], role="Entity contract signing")
			work.assign(case, work.waiting_command("SignContractVersion", "entity"), "Waiting for the entity's signature.", subject, agreement.version_no, work.holders(work.HOP), role=work.HOP, state="Waiting")
			records.bump(doc)
			outcome = records.summary(doc, signature=slot.name, state="Signed", party="Supplier")
		else:
			_activate(doc, agreement, actor)
			outcome = None
	frappe.db.commit()
	if outcome:
		return outcome
	carry_out_effects(case, actor)
	return records.summary(frappe.get_doc(CASE, case), signature=slot_name, state="Signed", party="Entity", effective=True)


def _activate(doc, agreement, actor: str) -> None:
	"""Both proofs are in: the agreement is in force (the same transaction as the second proof) and the native order and the funding conversion are recorded as durable operations."""
	preflight_guards = preflight.holds(Guards(), doc.name, "activate_contract")
	preflight_guards.raise_if_any()
	subject = f"agreement {agreement.version_no}"
	work.finish(doc.name, command="SignContractVersion", subject=subject, actor=actor)
	records.update(agreement, state="Effective", effective_at=clock.now(), record_version=cint(agreement.record_version) + 1)
	records.bump(doc, lifecycle="Active", operative_date=agreement.operative_date)
	intents.record(doc.name, subject, agreement.version_no, "Purchase order", "effective", recovery_owner="Technical operator; Budget owner")
	intents.record(doc.name, subject, agreement.version_no, "Funding conversion", "effective", recovery_owner="Technical operator; Budget owner")
	work.assign(doc.name, "RecommendContractInspectors", "Recommend the inspectors for this contract.", subject, agreement.version_no, work.holders(work.HOP), role=work.HOP)
	events.record(doc.name, "Agreement effective", actor, f"Agreement {agreement.version_no} is in force.", agreement=agreement.name)


# -- the native order and the funding conversion --------------------------------------------------------------------------------------
def native_order(case: str) -> str:
	return cstr(frappe.db.get_value(intents.INTENT, {"contract_case": case, "operation_kind": "Purchase order", "state": ["in", list(intents.SETTLED)]}, "result_reference"))


def _items(terms: dict[str, Any]) -> list[dict[str, Any]]:
	mapping = terms["particulars"]["item_mapping"]
	out = []
	for line in terms["lines"]:
		code = mapping[line["line_id"]]
		stock = frappe.db.get_value("Item", code, "is_stock_item")
		out.append({"item_code": code, "qty": line["quantity"], "rate": line["rate"], "warehouse": _warehouse(code) if stock else None})
	return out


def _warehouse(item_code: str) -> str | None:
	return frappe.db.get_value("Item Default", {"parent": item_code}, "default_warehouse") or frappe.db.get_value("Warehouse", {"is_group": 0, "disabled": 0}, "name")


def _company(terms: dict[str, Any]) -> str:
	return terms["particulars"].get("company") or frappe.defaults.get_global_default("company")


def carry_out_effects(case: str, actor: str = "") -> dict[str, Any]:
	"""Carry the pending purchase order and funding conversion through their owners, each in its own transaction. Safe to repeat: the owner is read first by identity."""
	agreement = current_agreement(case, "Effective")
	if not agreement:
		return {"ok": True, "operations": []}
	terms = records.loads(agreement.terms_json)
	out = []
	for kind in ("Purchase order", "Funding conversion"):
		name = frappe.db.get_value(intents.INTENT, {"contract_case": case, "operation_kind": kind, "subject": f"agreement {agreement.version_no}"}, "name")
		if not name:
			continue
		if kind == "Purchase order":
			supplier = _native_supplier(terms["particulars"], terms["parties"]["supplier"]["name"])

			def executor(identity, supplier=supplier):
				try:
					return adapter.create_purchase_order(identity, company=_company(terms), supplier=supplier, items=_items(terms), currency=terms["currency"], schedule_date=terms["delivery"]["due"]), "Purchase Order"
				except frappe.ValidationError as exc:
					raise intents.OwnerRefused(str(exc)) from exc

			result = intents.execute(name, executor, lambda identity: adapter.find_by_identity("Purchase Order", identity), native_doctype="Purchase Order")
		else:
			def executor(identity):
				try:
					return funding_seam.convert(identity, contract=case, allocations=terms["funding"]["allocations"], amount=terms["total"])["reference"], "Procurement Commitment"
				except funding_seam.Refused as exc:
					raise intents.OwnerRefused(str(exc)) from exc

			def lookup(identity):
				found = funding_seam.lookup(identity)
				return found["reference"] if found else None

			result = intents.execute(name, executor, lookup, native_doctype="Procurement Commitment")
		out.append({"kind": kind, **result})
		if result["state"] not in intents.SETTLED:
			with records.atomic():
				work.incident(case, "RestoreContractOperation", "Restore contract operation", f"agreement {agreement.version_no}", agreement.version_no)
				events.record(case, "Operation pending", actor, f"{kind} did not complete ({result['state'].lower()}).", intent=name)
			frappe.db.commit()
		else:
			with records.atomic():
				work.finish(case, command="RestoreContractOperation", subject=f"agreement {agreement.version_no}", actor=actor)
				events.record(case, f"{kind} linked", actor, f"{kind} {result['reference']} linked.", intent=name, reference=result["reference"])
			frappe.db.commit()
	return {"ok": True, "operations": out}


def restore_operations(case: str, *, actor: str) -> dict[str, Any]:
	"""`RestoreContractOperation` (technical recovery): read each owner first, link what exists, create only what is missing. Never asks for a new signature."""
	if not (people.technical(actor) or people.holds(actor, work.TECHNICAL)):
		fail("CM_AUTHORITY", missing="responsibility", responsibility=work.TECHNICAL, provisioned_by="System setup, by a System Manager")
	return carry_out_effects(case, actor)
