# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared STD template compiler (STD-TPL-IMP-001 v1.0 §7).

Pure Python — no module in this package may import `frappe`
(`test_compiler_purity` enforces it). The curation CLI adapter
(`04_fixture/build_definition_fixture.py`) and the production Tenders service
call the same `compile_published_bid_definition`.
"""

from kentender_procurement.std_templates.compiler.definition import (  # noqa: F401
	DEFINITION_FIELDS,
	compile_published_bid_definition,
	verify_definition_digest,
)
from kentender_procurement.std_templates.compiler.errors import STDTemplateError  # noqa: F401
