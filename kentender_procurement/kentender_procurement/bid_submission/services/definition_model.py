# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The exact Published Bid Definition a Draft is bound to, read for the bid
runtime (BDS-CHG-001 v0.8 §4.4.2 and §4.4.5; plan D11).

Tasks come from the published sections in order, groups from their published
compositions, and fields from the published response rows; nothing is
inferred from labels or positions. A composition repeated per arrangement
member (template release 1.2) becomes one group instance per member of the
bid's arrangement, each field keyed by its published response identity plus
the member's organisation (STD-TPL-001 §13.6). The portal sees a field only
by its handle: an opaque token derived from the definition digest and the
field key, so no published identity leaves the server."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field as dataclass_field
from typing import Any

from kentender_procurement.bid_submission.services.controls import KINDS

PER_MEMBER = "per_arrangement_member"


def task_key(section_id: str) -> str:
	return section_id.removeprefix("TASK-").lower()


@dataclass
class Task:
	key: str
	label: str
	purpose: str
	order: int


@dataclass
class Group:
	key: str  # instance key: the published group key, plus the member for a repeated group
	group_key: str
	rule_id: str
	composition_id: str
	task_key: str
	published_facts: dict[str, Any]
	member: str | None
	fields: list["Field"] = dataclass_field(default_factory=list)


@dataclass
class Field:
	key: str  # response identity, plus the member for a repeated group
	response_id: str
	group: Group
	field_key: str
	label: str
	help_text: str
	control_id: str
	required_rule: dict[str, Any]
	visibility_rule: dict[str, Any]
	validation_id: str
	validation_parameters: dict[str, Any]
	evidence_rule: dict[str, Any] | None
	supplied: dict[str, Any] | None
	label_parameters: list[str]
	member: str | None
	handle: str
	sequence: int

	@property
	def kind(self) -> str:
		return KINDS[self.control_id]

	@property
	def editable(self) -> bool:
		return self.supplied is None

	@property
	def task_key(self) -> str:
		return self.group.task_key


def _handle(digest: str, key: str) -> str:
	return "f" + hashlib.sha256(f"{digest}\x00{key}".encode("utf-8")).hexdigest()[:20]


class DefinitionModel:
	def __init__(self, definition: dict[str, Any], *, members: list[str] | tuple[str, ...] = ()):
		self.definition = definition
		self.digest = definition["definition_digest"]
		rows = {r["response_id"]: r for r in definition.get("response_rows") or []}
		self.tasks: list[Task] = []
		self._groups: dict[str, list[Group]] = {}
		self._fields: dict[str, list[Field]] = {}
		self._by_key: dict[str, Field] = {}
		self._by_handle: dict[str, Field] = {}
		for section in sorted(definition.get("sections") or [], key=lambda s: int(s.get("order") or 0)):
			key = task_key(section["section_id"])
			self.tasks.append(Task(key=key, label=section.get("label", ""), purpose=section.get("purpose", ""), order=int(section.get("order") or 0)))
			self._groups[key], self._fields[key] = [], []
			for published in section.get("groups") or []:
				instances = list(members) if published.get("repetition") == PER_MEMBER else [None]
				for member in instances:
					group = Group(
						key=f"{published['group_key']}#{member}" if member else published["group_key"], group_key=published["group_key"], rule_id=published.get("rule_id", ""),
						composition_id=published.get("composition_id", ""), task_key=key, published_facts=published.get("published_facts") or {}, member=member,
					)
					for response_id in published.get("response_ids") or []:
						row = rows[response_id]
						spec = row.get("field") or {}
						validation = row.get("validation") or {}
						field_key = f"{response_id}#{member}" if member else response_id
						item = Field(
							key=field_key, response_id=response_id, group=group, field_key=spec.get("field_key", ""), label=spec.get("label", ""), help_text=spec.get("help_text", ""),
							control_id=spec.get("control_id", ""), required_rule=row.get("required") or {"rule_id": "RQ-NEVER"}, visibility_rule=row.get("visibility") or {"rule_id": "VS-ALWAYS"},
							validation_id=validation.get("validation_id", "VAL-NONE"), validation_parameters=validation.get("parameters") or {}, evidence_rule=row.get("evidence"),
							supplied=spec.get("supplied_value"), label_parameters=list(spec.get("label_parameters") or []), member=member, handle=_handle(self.digest, field_key),
							sequence=int(row.get("sequence") or 0),
						)
						group.fields.append(item)
						self._fields[key].append(item)
						self._by_key[field_key] = item
						self._by_handle[item.handle] = item
					self._groups[key].append(group)

	@property
	def price_rows(self) -> list[dict[str, Any]]:
		return list(self.definition.get("price_rows") or [])

	def task(self, key: str) -> Task | None:
		return next((t for t in self.tasks if t.key == key), None)

	def groups_of(self, task: str) -> list[Group]:
		return list(self._groups.get(task, []))

	def fields_of(self, task: str) -> list[Field]:
		return list(self._fields.get(task, []))

	def all_fields(self) -> list[Field]:
		return [f for t in self.tasks for f in self._fields[t.key]]

	def by_handle(self, handle: str) -> Field | None:
		return self._by_handle.get(handle)

	def by_key(self, key: str) -> Field | None:
		return self._by_key.get(key)
