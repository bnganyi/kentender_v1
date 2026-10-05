"""ANL-CHG-001 v0.8 §10A.12 — golden payloads: what the server sends for each board.

One JSON file per board (or board group), built from dataset A1/A2 by the real
workspace code, so the page and its component tests are ported against exactly
what the endpoint returns. Regenerate after any change to the payload:

  cd /home/midasuser/frappe-bench && bench --site kentender-test.local execute \\
    kentender_core.tests.analytics_goldens.write_all
"""

from __future__ import annotations

import json
from pathlib import Path

from kentender_core.services import analytics_contract as ac
from kentender_core.tests import analytics_a1 as a1
from kentender_core.tests.analytics_a1 import A1, CHARLES, DANIEL, FY, HR, PETER, read

OUT = Path(__file__).resolve().parents[1] / "public" / "js" / "analytics" / "fixtures"


def _broken_tender() -> A1:
	provider = A1()
	base = provider.facts

	def facts(**kw):
		if kw["kind"] != ac.TENDERS:
			return base(**kw)
		records = a1.tenders()
		for rec in records:
			if rec["reference"].endswith("044"):
				rec["bucket"], rec["position"], rec["outstanding"] = ac.UNAVAILABLE, "Status unavailable", None
		return {"records": records}

	provider.facts = facts
	return provider


def _empty() -> A1:
	provider = A1()
	provider.facts = lambda **kw: {"records": []}
	return provider


BOARDS = {
	"ANL-DES-21": lambda: read(CHARLES),
	"ANL-DES-28": lambda: read(CHARLES, fy=FY),
	"ANL-DES-31J": lambda: read(DANIEL),
	"ANL-DES-22": lambda: read(CHARLES, tab="tender-proceedings"),
	"ANL-DES-23": lambda: read(CHARLES, tab="tender-proceedings", state="award"),
	"ANL-DES-24": lambda: read(CHARLES, tab="requisitions"),
	"ANL-DES-25": lambda: read(CHARLES, tab="annual-planning"),
	"ANL-DES-26": lambda: read(CHARLES, tab="needs"),
	"ANL-DES-27": lambda: read(CHARLES, tab="departmental-planning"),
	"ANL-DES-29": lambda: read(PETER, A1("hr", funding_view="department"), dept=HR),
	"ANL-DES-29F": lambda: read(PETER, A1("hr", funding_view="department"), fy=FY, dept=HR),
	"ANL-DES-30": lambda: read(PETER, A1("hr"), tab="tender-proceedings", dept=HR),
	"ANL-DES-30B": lambda: read(PETER, A1("hr"), tab="annual-planning", dept=HR),
	"ANL-DES-31A": lambda: read(CHARLES, tab="tender-proceedings", search="laboratory"),
	"ANL-DES-31B": lambda: read(CHARLES, _empty()),
	"ANL-DES-31C": lambda: read(CHARLES, A1(fail={ac.NEEDS})),
	"ANL-DES-31D": lambda: read(CHARLES, A1(fail={ac.NEEDS, ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS, ac.REQUISITIONS, ac.TENDERS})),
	"ANL-DES-31E": lambda: read(CHARLES, A1(extra={ac.PLAN_ITEMS: {"unavailable_measures": ["coverage"]}})),
	"ANL-DES-31F": lambda: read(CHARLES, _broken_tender(), tab="tender-proceedings"),
	"ANL-DES-31H": lambda: read(CHARLES, A1(kinds=set())),
}


def write_all() -> None:
	OUT.mkdir(parents=True, exist_ok=True)
	for name, build in BOARDS.items():
		(OUT / f"{name}.json").write_text(json.dumps(build(), indent=1, ensure_ascii=False, default=str, sort_keys=False) + "\n", encoding="utf-8")
	print(f"wrote {len(BOARDS)} golden payloads to {OUT}")
