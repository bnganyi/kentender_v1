# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The board vocabulary (CM-CHG-001 v0.8 section 10; plan Phase 4): the design tool's own helpers, in Python.

`design/cm-data-*.js` writes each board with `S({...})`, regions of blocks (`f`, `r`, `t`, `fl`, `x`, `xs`, `xh`, `lk`, `bt`, `pv`) and a next step (`turn`, `wait`, `done`, `blk`). The server builds
the live screens from the **same shapes** with live data, and one Vue component (`CmBoard.vue`) draws them class for class as the design's template does, so a screen cannot drift from its board
without the structural fidelity gate seeing it.

Beyond the design's own vocabulary a board carries what the design cannot draw because it is static: `actions` (a button's label -> what it does: run a command, open a dialog, go to a route),
`dialogs` (the design's dialog boards, with named fields), `case` and `version` (the expected revision a command is sent with) and field `name`s. Table cells keep the design's prefix syntax:
`@` link, `!` status pill, `#` or `~` input, `^` select. An input's name is given in the table block's `inputs` (`"row,col"` -> name)."""

from __future__ import annotations

from typing import Any


def f(*items) -> dict:
	return {"k": "facts", "items": [list(i) for i in items]}


def r(*items) -> dict:
	return {"k": "rows", "items": [list(i) for i in items]}


def t(cols, rows, num=(), inputs: dict[str, str] | None = None, live: dict[str, str] | None = None) -> dict:
	"""`inputs` names an input cell (`"row,col"` -> field name); `live` draws a cell from another field as the reader types (unit references, summarised as a range)."""
	return {"k": "table", "cols": list(cols), "rows": [list(x) for x in rows], "num": list(num), "inputs": inputs or {}, "live": live or {}}


def fl(*items) -> dict:
	return {"k": "fields", "items": list(items)}


def x(v: str) -> dict:
	return {"k": "text", "v": v}


def xs(v: str) -> dict:
	return {"k": "strong", "v": v}


def xh(v: str) -> dict:
	return {"k": "help", "v": v}


def lk(*items) -> dict:
	return {"k": "links", "items": list(items)}


def bt(*items) -> dict:
	return {"k": "btns", "items": list(items)}


def pv(title: str, items, open_: bool = True) -> dict:
	return {"k": "preview", "t": title, "items": [list(i) for i in items], "open": open_}


def R(title: str, *blocks) -> dict:
	return {"t": title, "b": list(blocks)}


def _field(kind: str):
	def make(label: str, value: Any = "", name: str = "", **o) -> dict:
		return {"t": kind, "l": label, "v": "" if value is None else value, "name": name, "o": o}

	return make


tx, dt, ta, file, ro = _field("tx"), _field("dt"), _field("ta"), _field("file"), _field("ro")


def sel(label: str, value: Any, opts, name: str = "", **o) -> dict:
	return {"t": "sel", "l": label, "v": value, "opts": list(opts) if opts else [value], "name": name, "o": o}


def pick(label: str, value: Any, source: str, name: str, context: dict | None = None, value_label: str = "", noun: str = "", **o) -> dict:
	"""One person or one record chosen with the shared record picker (AGENTS.md section 6.12); `value` is the chosen id, `value_label` its saved name."""
	return {"t": "pick", "l": label, "v": value or "", "source": source, "context": context or {}, "valueLabel": value_label, "noun": noun, "name": name, "o": o}


def rad(label: str, opts, si: int = -1, name: str = "") -> dict:
	return {"t": "rad", "l": label, "opts": list(opts), "si": si, "name": name, "o": {}}


def wide(field: dict) -> dict:
	return {**field, "wide": True}


def turn(headline: str, holder: str = "") -> dict:
	return {"k": "turn", "h": headline, "s": f"Responsible: {holder}" if holder else ""}


def wait(headline: str, sentence: str = "") -> dict:
	return {"k": "wait", "h": headline, "s": sentence}


def done(headline: str, sentence: str = "") -> dict:
	return {"k": "done", "h": headline, "s": sentence}


def blk(headline: str, holder: str = "", fixes=(), sentence: str = "") -> dict:
	return {"k": "blk", "h": headline, "s": f"Responsible for the fix: {holder}" if holder else "", "fixes": list(fixes), "s2": sentence}


def dlg(title: str, blocks, primary: str = "", secondary=("Cancel",), **extra) -> dict:
	return {"t": title, "b": list(blocks), "p": primary, "s2": list(secondary), **extra}


def board(**o) -> dict:
	"""A board with the design's defaults (`S`)."""
	base = {"ref": "", "sub": "", "back": "Back to contracts", "page": "record", "s2": [], "ev": [], "regions": [], "actions": {}, "dialogs": {}}
	return {**base, **o}


# -- what a button does ------------------------------------------------------------------------------------------------------------------
def command(name: str, **args) -> dict:
	"""Run a Contract Management command with these fixed arguments plus the form's values."""
	return {"do": "command", "command": name, "args": args}


def dialog(key: str) -> dict:
	return {"do": "dialog", "dialog": key}


def route(*segments: str) -> dict:
	return {"do": "route", "route": list(segments)}


def download(url: str) -> dict:
	"""Open an audience-checked evidence file."""
	return {"do": "download", "url": url}


def tab(name: str) -> dict:
	return {"do": "tab", "tab": name}


def disabled(label: str) -> str:
	"""A secondary action drawn but not available (the design's leading `-`)."""
	return f"-{label}"
