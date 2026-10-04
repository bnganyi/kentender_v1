# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`PreviewSTDReleaseDocument` and `DownloadSTDReleaseReviewPack`
(STD-TPL-IMP-001 v1.0 §6, §11, §13).

Previews stream the release's own immutable, digest-checked rendering of
each output (the MoH fixture PDFs); the review pack is the exact installed
pack plus its manifest, review record and owner decision. Raw JSON is only
ever delivered inside the review pack. Both reads are audited.
"""

from __future__ import annotations

import io
import zipfile
from typing import Any

import frappe

from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.release import bundle
from kentender_procurement.std_templates.services import access, runtime

PREVIEWS = {
	"invitation": ("04_fixture/moh_invitation_expected.pdf", "invitation-to-tender-preview.pdf"),
	"issued_tender": ("04_fixture/moh_expected.pdf", "complete-issued-tender-preview.pdf"),
}


def _audit(release_id: str, action: str, metadata: dict[str, Any]) -> None:
	from kentender_core.services.audit_event_service import log_audit_event

	log_audit_event(event_type="STD Release", entity="STD Templates", document_type="Installed STD Release", document_name=release_id, action=action, metadata=metadata)


def preview(release_id: str, output_id: str, *, user: str | None = None) -> tuple[str, bytes]:
	access.require_reader(user)
	if output_id not in PREVIEWS:
		fail("STD_RELEASE_NOT_FOUND", identity=output_id)
	release = runtime.release_doc(release_id)
	rel, name = PREVIEWS[output_id]
	content = runtime.asset_bytes(release, rel)
	_audit(release.name, "Previewed", {"output_id": output_id, "asset": rel})
	return f"{release.template_key}-{release.template_release}-{name}", content


def review_pack(release_id: str, *, user: str | None = None) -> tuple[str, bytes]:
	access.require_reader(user)
	release = runtime.release_doc(release_id)
	buffer = io.BytesIO()
	root = f"{release.template_key}-{release.template_release}"
	with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for row in sorted(release.assets, key=lambda a: a.relative_path.encode("utf-8")):
			archive.writestr(f"{root}/{row.relative_path}", runtime.asset_bytes(release, row.relative_path))
		for field, rel in (("manifest_file", bundle.MANIFEST_PATH), ("review_record_file", bundle.REVIEW_RECORD_PATH), ("owner_decision_file", bundle.OWNER_DECISION_PATH)):
			if release.get(field):
				archive.writestr(f"{root}/{rel}", runtime._file_bytes(release.get(field)))
	_audit(release.name, "Review pack downloaded", {"assets": len(release.assets)})
	return f"{root}-review-pack.zip", buffer.getvalue()
