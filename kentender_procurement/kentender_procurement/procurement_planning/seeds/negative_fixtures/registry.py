# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NEG-PP2 fixture registry (spec §22.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from kentender_procurement.procurement_planning.seeds.negative_fixtures.constants import (
	ALL_NEGATIVE_FIXTURE_CODES,
	FIXTURE_METADATA,
)
from kentender_procurement.procurement_planning.seeds.negative_fixtures.setups import SETUP_BY_FIXTURE

SetupFn = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class NegativeFixtureSpec:
	fixture_code: str
	setup: str
	attempted_action: str
	expected_result: str
	blocker_code: str
	message: str
	setup_fn: SetupFn


def get_negative_fixture_spec(fixture_code: str) -> NegativeFixtureSpec | None:
	code = (fixture_code or "").strip()
	if code not in SETUP_BY_FIXTURE:
		return None
	meta = FIXTURE_METADATA[code]
	return NegativeFixtureSpec(
		fixture_code=code,
		setup=meta["setup"],
		attempted_action=meta["attempted_action"],
		expected_result=meta["expected_result"],
		blocker_code=meta["blocker_code"],
		message=meta["message"],
		setup_fn=SETUP_BY_FIXTURE[code],
	)


def list_negative_fixture_codes() -> tuple[str, ...]:
	return ALL_NEGATIVE_FIXTURE_CODES
