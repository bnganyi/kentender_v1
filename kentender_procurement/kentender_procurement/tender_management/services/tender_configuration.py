# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Parse ``configuration_json`` on tender documents (TM2)."""

from __future__ import annotations

import json
from typing import Any

from frappe.model.document import Document


def parse_configuration_json(doc: Document) -> dict[str, Any]:
	raw = getattr(doc, "configuration_json", None) or ""
	if not raw:
		return {}
	try:
		parsed = json.loads(raw)
		return parsed if isinstance(parsed, dict) else {}
	except json.JSONDecodeError:
		return {}
