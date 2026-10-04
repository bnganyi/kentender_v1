# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §5.10/D14 — supporting-material file checks.

The implementation now lives once in `kentender_core.services.file_integrity`
(TPR-CHG-001 v0.8 plan D10 lifted it so Requisition supporting materials and
Tender publication evidence share one truthful scanner vocabulary); this
module keeps Requisitions' own allow-list, size limit and error code.
"""

from __future__ import annotations

from kentender_core.services import file_integrity

MAX_FILE_SIZE_BYTES = file_integrity.MAX_FILE_SIZE_BYTES  # 20 MB, per §5.10
ALLOWED_EXTENSIONS: tuple[str, ...] = file_integrity.DEFAULT_ALLOWED_EXTENSIONS


def check_file(file_doc_name: str) -> dict[str, str]:
	"""Reads the private Frappe File, checks type/size/readability, computes
	a SHA-256 digest and records the scan result. Raises
	`ProcurementRequisitionsError("REQ_FILE_INVALID", ...)` on any failed
	check; returns `{digest, check_result}` on success."""
	from kentender_procurement.procurement_requisitions.services.errors import fail

	result = file_integrity.check_file(
		file_doc_name, allowed_extensions=ALLOWED_EXTENSIONS, fail=lambda message: fail("REQ_FILE_INVALID", message)
	)
	return {"digest": result["digest"], "check_result": result["check_result"]}
