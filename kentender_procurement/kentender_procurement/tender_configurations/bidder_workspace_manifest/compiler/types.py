# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Pure compiler DTOs (no Frappe / DB)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


COMPILER_VERSION = "1.0.0"

STAGE_IDS: tuple[str, ...] = tuple(f"C{i:02d}" for i in range(1, 23))

SUBMISSION_POLICY_REQUIRED_FIELDS: frozenset[str] = frozenset(
	{
		"deadline_at",
		"timezone",
		"server_time_authoritative",
		"late_submission_behavior",
		"withdrawal_mode",
		"replacement_mode",
		"submission_authority_policy_ref",
		"reauthentication_policy_ref",
		"seal_policy_ref",
		"receipt_policy_ref",
		"concurrent_submission_policy",
		"idempotency_policy",
	}
)

PUBLICATION_MODES: frozenset[str] = frozenset({"publication", "addendum_publication"})
ADDENDUM_MODES: frozenset[str] = frozenset({"addendum_preview", "addendum_publication"})


@dataclass
class Diagnostic:
	diagnostic_id: str
	severity: str  # error | warning | information
	code: str
	message: str
	path: str = ""

	def as_dict(self) -> dict[str, Any]:
		d: dict[str, Any] = {
			"diagnostic_id": self.diagnostic_id,
			"severity": self.severity,
			"code": self.code,
			"message": self.message,
		}
		if self.path:
			d["path"] = self.path
		return d


@dataclass
class StageTrace:
	stage: str
	state: str  # ok | error | skipped
	detail: str = ""

	def as_dict(self) -> dict[str, Any]:
		return {"stage": self.stage, "state": self.state, "detail": self.detail}


@dataclass
class CompileRequestDTO:
	compile_mode: str
	target_manifest_id: str
	target_manifest_version: int
	published_tender_ref: str
	published_tender_version: int
	compiler_version: str = COMPILER_VERSION
	expected_input_digests: dict[str, str] = field(default_factory=dict)
	compiler_run_id: str = "RUN-PURE"
	generated_by: str = "bwmf.compiler"
	generated_at: str = "2026-07-24T00:00:00Z"
	validation_report_ref: str = ""
	# Required for addendum modes — previous published artifact identity + digest
	previous_manifest_ref: str = ""
	previous_manifest_version: int | None = None
	previous_manifest_digest: str = ""
	previous_artifact_id: str = ""


@dataclass
class SourceSet:
	"""Immutable digitized sources bound for one compile."""

	raw: dict[str, Any]
	insertion_order: list[str] = field(default_factory=list)

	@property
	def profile(self) -> str:
		return str(self.raw.get("profile") or "")

	def get(self, key: str, default: Any = None) -> Any:
		return self.raw.get(key, default)


@dataclass
class CompileContext:
	request: CompileRequestDTO
	sources: SourceSet
	normalized: dict[str, Any] = field(default_factory=dict)
	payload: dict[str, Any] = field(default_factory=dict)
	control: dict[str, Any] = field(default_factory=dict)
	envelope: dict[str, Any] = field(default_factory=dict)
	diagnostics: list[Diagnostic] = field(default_factory=list)
	traces: list[StageTrace] = field(default_factory=list)
	logical_resources: list[dict[str, Any]] = field(default_factory=list)
	golden_projection: dict[str, Any] = field(default_factory=dict)
	addendum_impact: dict[str, Any] = field(default_factory=dict)
	payload_digest: str = ""
	projection_digest: str = ""
	diagnostic_digest: str = ""
	digest_label: str = "unmaterialized_preview_payload"
	failed: bool = False
	fail_code: str = ""

	def add_error(self, code: str, message: str, *, diagnostic_id: str = "", path: str = "") -> None:
		self.failed = True
		self.fail_code = code or self.fail_code
		self.diagnostics.append(
			Diagnostic(
				diagnostic_id=diagnostic_id or f"ERR-{code}",
				severity="error",
				code=code,
				message=message,
				path=path,
			)
		)

	def add_diagnostic(self, diagnostic: Diagnostic) -> None:
		self.diagnostics.append(diagnostic)
		if diagnostic.severity == "error":
			self.failed = True
			self.fail_code = diagnostic.code or self.fail_code


@dataclass
class CompileResult:
	ok: bool
	envelope: dict[str, Any]
	payload: dict[str, Any]
	payload_digest: str
	projection_digest: str
	diagnostic_digest: str
	diagnostics: list[dict[str, Any]]
	traces: list[dict[str, Any]]
	logical_resources: list[dict[str, Any]]
	golden_projection: dict[str, Any]
	validation_report: dict[str, Any]
	addendum_impact: dict[str, Any] = field(default_factory=dict)
	digest_label: str = "unmaterialized_preview_payload"
	fail_code: str = ""
