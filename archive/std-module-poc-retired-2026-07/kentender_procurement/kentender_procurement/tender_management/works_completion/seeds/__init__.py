# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic seed fixtures for Works completion (WORKS-COMP-1100+).

**WORKS-COMP-1100 — MOH representative fixture**

- Primary callable: ``run`` in module
  ``kentender_procurement.tender_management.works_completion.seeds.works_completion_moh_fixture``.
- Alias: ``seed_works_completion_moh_fixture`` (same module).

``bench execute`` (default tender reference ``TND-MOH-2026-001``)::

	bench --site kentender.midas.com execute \\
	  kentender_procurement.tender_management.works_completion.seeds.works_completion_moh_fixture.run

Python import::

	from kentender_procurement.tender_management.works_completion.seeds.works_completion_moh_fixture import run
"""

from __future__ import annotations
