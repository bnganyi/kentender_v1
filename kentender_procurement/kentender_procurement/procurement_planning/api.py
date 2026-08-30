# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 — Procurement Planning API surface.

Rebuilt from Phase 2 onward around the §8 command and read contracts. Every
endpoint keeps an explicit signature (no bare **kwargs handed to services —
the framework passes `cmd`/`csrf_token` through `form_dict`), and Playwright
fixture endpoints live in seed/fixture modules, never here (decision D8).
"""

from __future__ import annotations
