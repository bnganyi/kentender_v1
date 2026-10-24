# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.20 §9.1D — an owner's typed refusal during a cancellation recovery.

Planning and Budget each refuse a recovery that their own records do not support (a draw reversed for another reason, a reservation
that was converted or part released, a fact that changed since it was pinned). That is not a failure to be retried: the recovery is
`Needs attention`, with the owner's own reason, until the owner corrects the cause through its governed route. Anything else an owner
raises (a lock timeout, a database error, an unavailable service) is not a refusal, and the recovery stays `Pending` and is retried."""

from __future__ import annotations

from typing import Any


class OwnerRefusal(Exception):
	"""`owner` is `Planning` or `Budget`; `kind` is `invalid` (the owner's records do not support the recovery) or `conflict` (they changed
	or disagree); `code` is the owner's own error code; `detail` names the exact source and cause."""

	def __init__(self, owner: str, kind: str, code: str, detail: dict[str, Any] | None = None):
		self.owner, self.kind, self.code, self.detail = owner, kind, code, detail or {}
		cause = (detail or {}).get("cause") or ""
		super().__init__(f"{owner}: {cause or code}")

	@property
	def reason(self) -> str:
		cause = self.detail.get("cause") or ""
		return f"{self.owner} — {cause}" if cause else f"{self.owner} refused ({self.code})."
