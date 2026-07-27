# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reject float money; prefer decimal strings."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	JcsError,
	assert_no_float,
)


def guard_money_graph(payload: dict[str, Any]) -> None:
	assert_no_float(payload)
	# Explicit money-ish keys must be str when present
	for path, value in _walk(payload):
		leaf = path.rsplit(".", 1)[-1]
		if leaf in {"amount", "unit_price", "total", "grand_total", "vat_amount", "net_amount"}:
			if isinstance(value, float):
				raise JcsError(f"{path}: money must not be float")
			if isinstance(value, int) and not isinstance(value, bool):
				raise JcsError(f"{path}: money must be decimal string, not int")


def _walk(node: Any, path: str = "$"):
	if isinstance(node, dict):
		for k, v in node.items():
			yield from _walk(v, f"{path}.{k}")
	elif isinstance(node, list):
		for i, v in enumerate(node):
			yield from _walk(v, f"{path}[{i}]")
	else:
		yield path, node
