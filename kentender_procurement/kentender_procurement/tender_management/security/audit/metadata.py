# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Common audit event metadata shape — SEC-0500 / pack §14.

Provides a standard schema and validation helpers so existing audit emitters can
map their event metadata into one canonical payload before persistence.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, TypedDict

from frappe.utils import now_datetime

AuditResult = Literal["Success", "Denied", "Failed"]
RiskLevel = Literal["Low", "Medium", "High", "Critical"]


class AuditEventResult(StrEnum):
	SUCCESS = "Success"
	DENIED = "Denied"
	FAILED = "Failed"


class AuditRiskLevel(StrEnum):
	LOW = "Low"
	MEDIUM = "Medium"
	HIGH = "High"
	CRITICAL = "Critical"


_RESULT_VALUES: frozenset[str] = frozenset(r.value for r in AuditEventResult)
_RISK_VALUES: frozenset[str] = frozenset(r.value for r in AuditRiskLevel)


class AuditEventMetadata(TypedDict, total=False):
	# Core identity
	audit_event_code: str
	event_type: str
	actor_user_code: str
	actor_role_codes: list[str]
	object_type: str
	object_code: str
	parent_object_type: str
	parent_object_code: str
	# Domain links
	tender_code: str
	package_code: str
	std_instance_code: str
	template_version_code: str
	output_code: str
	snapshot_code: str
	action_code: str
	# Outcome
	result: AuditResult
	denial_code: str
	message: str
	state_before: str
	state_after: str
	risk_level: RiskLevel
	# Request / integrity
	timestamp: datetime
	request_id: str
	ip_address: str
	input_hash: str
	output_hash: str
	complete_snapshot_hash: str
	evidence_package_hash: str
	# Free-form extension
	details: dict[str, Any]


_STR_FIELDS: frozenset[str] = frozenset(
	{
		"audit_event_code",
		"event_type",
		"actor_user_code",
		"object_type",
		"object_code",
		"parent_object_type",
		"parent_object_code",
		"tender_code",
		"package_code",
		"std_instance_code",
		"template_version_code",
		"output_code",
		"snapshot_code",
		"action_code",
		"denial_code",
		"message",
		"state_before",
		"state_after",
		"request_id",
		"ip_address",
		"input_hash",
		"output_hash",
		"complete_snapshot_hash",
		"evidence_package_hash",
	}
)

_ALLOWED_KEYS: frozenset[str] = frozenset(AuditEventMetadata.__annotations__)

_REQUIRED_KEYS: frozenset[str] = frozenset(
	{
		"audit_event_code",
		"event_type",
		"object_type",
		"object_code",
		"result",
		"risk_level",
		"timestamp",
	}
)


def _norm_text(value: Any) -> str:
	return str(value or "").strip()


def build_audit_metadata(
	*,
	audit_event_code: str,
	event_type: str,
	object_type: str,
	object_code: str,
	result: AuditResult | AuditEventResult,
	risk_level: RiskLevel | AuditRiskLevel,
	timestamp: datetime | None = None,
	**optional: Any,
) -> AuditEventMetadata:
	"""Build a canonical SEC-0500 metadata payload."""
	meta: AuditEventMetadata = {
		"audit_event_code": _norm_text(audit_event_code),
		"event_type": _norm_text(event_type),
		"object_type": _norm_text(object_type),
		"object_code": _norm_text(object_code),
		"result": str(result.value if isinstance(result, AuditEventResult) else result),  # type: ignore[assignment]
		"risk_level": str(risk_level.value if isinstance(risk_level, AuditRiskLevel) else risk_level),  # type: ignore[assignment]
		"timestamp": timestamp or now_datetime(),
	}
	for key, value in optional.items():
		if key not in _ALLOWED_KEYS:
			continue
		if value is None:
			continue
		if key in _STR_FIELDS:
			v = _norm_text(value)
			if v:
				meta[key] = v  # type: ignore[index]
			continue
		if key == "actor_role_codes":
			roles = [_norm_text(x) for x in (value or []) if _norm_text(x)]
			if roles:
				meta["actor_role_codes"] = roles
			continue
		if key == "details":
			if isinstance(value, dict):
				meta["details"] = deepcopy(value)
			continue
		if key == "timestamp" and isinstance(value, datetime):
			meta["timestamp"] = value
	return meta


def normalize_audit_metadata(raw: dict[str, Any]) -> AuditEventMetadata:
	"""Normalize external metadata into canonical SEC-0500 keys.

	This lets existing emitters map legacy aliases (``event_code``, ``actor``,
	``instance_code``) without changing all callsites immediately.
	"""
	src = dict(raw or {})
	alias_map = {
		"event_code": "audit_event_code",
		"instance_code": "std_instance_code",
		"configuration_snapshot_code": "snapshot_code",
		"publication_snapshot_code": "snapshot_code",
		"std_publication_snapshot_code": "snapshot_code",
		"actor": "actor_user_code",
	}
	for old, new in alias_map.items():
		if old in src and new not in src:
			src[new] = src.get(old)

	# Fill minimal missing canonical values from aliases.
	if not src.get("audit_event_code") and src.get("event_type"):
		src["audit_event_code"] = src.get("event_type")

	return build_audit_metadata(
		audit_event_code=_norm_text(src.get("audit_event_code")),
		event_type=_norm_text(src.get("event_type")),
		object_type=_norm_text(src.get("object_type")),
		object_code=_norm_text(src.get("object_code")),
		result=(_norm_text(src.get("result")) or AuditEventResult.SUCCESS.value),
		risk_level=(_norm_text(src.get("risk_level")) or AuditRiskLevel.MEDIUM.value),
		timestamp=src.get("timestamp") if isinstance(src.get("timestamp"), datetime) else None,
		actor_user_code=src.get("actor_user_code"),
		actor_role_codes=src.get("actor_role_codes"),
		parent_object_type=src.get("parent_object_type"),
		parent_object_code=src.get("parent_object_code"),
		tender_code=src.get("tender_code"),
		package_code=src.get("package_code"),
		std_instance_code=src.get("std_instance_code"),
		template_version_code=src.get("template_version_code"),
		output_code=src.get("output_code"),
		snapshot_code=src.get("snapshot_code"),
		action_code=src.get("action_code"),
		denial_code=src.get("denial_code"),
		message=src.get("message"),
		state_before=src.get("state_before"),
		state_after=src.get("state_after"),
		request_id=src.get("request_id"),
		ip_address=src.get("ip_address"),
		input_hash=src.get("input_hash"),
		output_hash=src.get("output_hash"),
		complete_snapshot_hash=src.get("complete_snapshot_hash"),
		evidence_package_hash=src.get("evidence_package_hash"),
		details=src.get("details"),
	)


def validate_audit_metadata(meta: dict[str, Any], *, strict_high_critical: bool = True) -> AuditEventMetadata:
	"""Validate metadata against SEC-0500 schema; raise ``ValueError`` if invalid."""
	m = normalize_audit_metadata(meta)
	for key in _REQUIRED_KEYS:
		if key not in m:
			raise ValueError(f"Missing required audit metadata field: {key}")
		if key != "timestamp" and not _norm_text(m.get(key)):
			raise ValueError(f"Required audit metadata field is blank: {key}")

	if str(m.get("result")) not in _RESULT_VALUES:
		raise ValueError("result must be one of Success/Denied/Failed")
	if str(m.get("risk_level")) not in _RISK_VALUES:
		raise ValueError("risk_level must be one of Low/Medium/High/Critical")
	if not isinstance(m.get("timestamp"), datetime):
		raise ValueError("timestamp must be a datetime")
	if "actor_role_codes" in m and not isinstance(m.get("actor_role_codes"), list):
		raise ValueError("actor_role_codes must be a list")
	if "details" in m and not isinstance(m.get("details"), dict):
		raise ValueError("details must be a dict")

	# Pack acceptance: high/critical legal events must include actor and object refs.
	if strict_high_critical and str(m.get("risk_level")) in {
		AuditRiskLevel.HIGH.value,
		AuditRiskLevel.CRITICAL.value,
	}:
		if not _norm_text(m.get("actor_user_code")):
			raise ValueError("actor_user_code is required for High/Critical events")
		if not _norm_text(m.get("object_type")) or not _norm_text(m.get("object_code")):
			raise ValueError("object_type/object_code are required for High/Critical events")

	return m
