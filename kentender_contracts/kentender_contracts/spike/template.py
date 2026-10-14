"""Phase 2 spike S8 (tracker CM8-209): can the installed template release supply Form No. 4 verifiably, and can the package be generated reproducibly?"""

from __future__ import annotations

import hashlib
import re

import frappe

from kentender_contracts.spike import native

RELEASE = "stdr-19da524c-85d1-4fdb-8dee-81860bd68c67"  # IT-EQUIPMENT-OPEN-V1 release 1.5 on the test site
MASTER = "02_master/complete_tender.html"
HEADING = "Form No. 4 - Contract Agreement"


def _master() -> tuple[bytes, dict]:
	row = frappe.db.get_value("Installed STD Release Asset", {"parent": RELEASE, "relative_path": MASTER}, ["relative_path", "asset_role", "mime_type", "byte_size", "sha256_digest", "private_file_id"], as_dict=True)
	content = frappe.get_doc("File", row.private_file_id).get_content()
	return (content if isinstance(content, bytes) else content.encode("utf-8")), row


def form_4(html: str) -> str:
	start = html.index(f"<h3>{HEADING}</h3>")
	end = html.find("{% if contract.performance_security.required %}", start)
	return html[start:end if end > 0 else start + 6000]


def s8_template() -> list[dict]:
	data, row = _master()
	digest = hashlib.sha256(data).hexdigest()
	native.record("S8.master_asset_retrievable_and_verifiable", path=row.relative_path, role=row.asset_role, size=len(data), recorded_size=row.byte_size, recorded_sha256=row.sha256_digest, recomputed_sha256=digest,
		digest_matches=digest == row.sha256_digest)
	html = data.decode("utf-8")
	native.record("S8.stable_anchors_in_the_master", element_ids=len(re.findall(r'\bid="[^"]+"', html)), ids=re.findall(r'\bid="([^"]+)"', html),
		form_4_has_an_id=bool(re.search(r'<h3[^>]*\bid=[^>]*>\s*Form No\. 4', html)), gcc_scc_anchors=[i for i in re.findall(r'\bid="([^"]+)"', html) if "gcc" in i.lower() or "scc" in i.lower() or "conditions" in i.lower()])
	f4 = form_4(html)
	text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", f4))
	blanks = len(re.findall(r"_{5,}", text))
	placeholders = sorted(set(re.findall(r"\{\{\s*([^}]+?)\s*\}\}", f4)))
	native.record("S8.form_no_4_by_its_heading", found=True, bytes=len(f4.encode()), blank_fields=blanks, template_placeholders=placeholders,
		incorporated_documents_listed=len(re.findall(r"\b[a-h]\) ", text)), witness_lines=len(re.findall(r"In the presence of", text)),
		instruction_text_present=("To be completed by the successful Tenderer" in text), starts=text[:140], ends=text[-170:])
	needed = ("<h3>Form No. 4 - Contract Agreement</h3>",)
	native.record("S8.missing_heading_would_fail_visibly", fails_when_absent=_fails(html.replace(needed[0], "<h3>Form 4</h3>")))

	# reproducibility of generation: the same frozen inputs and the same renderer
	context = {"procuring_entity": {"name": "Ministry of Health", "address": "Afya House, Nairobi"}, "tender": {"title": "Supply of ICT equipment", "reference": "TND-MOH-2027-001"}}
	a, b = frappe.render_template(f4, context), frappe.render_template(f4, context)
	native.record("S8.html_generation_is_byte_reproducible", sha_a=hashlib.sha256(a.encode()).hexdigest(), sha_b=hashlib.sha256(b.encode()).hexdigest(), identical=a == b)
	try:
		from frappe.utils.pdf import get_pdf

		pa, pb = get_pdf(a), get_pdf(b)
		native.record("S8.pdf_generation_through_the_existing_path", bytes=len(pa), sha_a=hashlib.sha256(pa).hexdigest(), sha_b=hashlib.sha256(pb).hexdigest(), identical=pa == pb,
			differing_metadata=sorted(set(re.findall(rb"/(CreationDate|ModDate|ID)", pa))) and [m.decode() for m in sorted(set(re.findall(rb"/(CreationDate|ModDate|ID)", pa)))])
	except Exception as exc:  # noqa: BLE001
		native.record("S8.pdf_generation_through_the_existing_path", ok=False, error=f"{type(exc).__name__}: {str(exc)[:200]}")
	return native.save("s8_template")


def _fails(html: str) -> bool:
	try:
		form_4(html)
		return False
	except ValueError:
		return True
