# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic array ordering helpers."""

from __future__ import annotations

from typing import Any, Callable, Sequence


def sort_by_keys(items: Sequence[dict[str, Any]], keys: Sequence[str]) -> list[dict[str, Any]]:
	def key_fn(row: dict[str, Any]) -> tuple:
		return tuple(_sortable(row.get(k)) for k in keys)

	return sorted(items, key=key_fn)


def _sortable(value: Any) -> Any:
	if value is None:
		return ""
	if isinstance(value, bool):
		return int(value)
	return value


def sort_strings(values: Sequence[str]) -> list[str]:
	return sorted(values)


def deep_sort_arrays(
	node: Any,
	*,
	array_key_rules: dict[str, Sequence[str]] | None = None,
	path: str = "$",
) -> Any:
	"""Sort arrays at known paths; leave unknown arrays as-is (caller should sort explicitly)."""
	rules = array_key_rules or {}
	if isinstance(node, dict):
		return {k: deep_sort_arrays(v, array_key_rules=rules, path=f"{path}.{k}") for k, v in node.items()}
	if isinstance(node, list):
		rule = rules.get(path)
		if rule and node and isinstance(node[0], dict):
			sorted_items = sort_by_keys(node, rule)
			return [deep_sort_arrays(x, array_key_rules=rules, path=f"{path}[]") for x in sorted_items]
		return [deep_sort_arrays(x, array_key_rules=rules, path=f"{path}[]") for x in node]
	return node
