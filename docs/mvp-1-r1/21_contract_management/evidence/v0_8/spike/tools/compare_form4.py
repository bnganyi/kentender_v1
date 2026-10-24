"""S8b — compare the installed release's Form No. 4 with the official PPRA text (paragraphs 2647-2667 of the retrieved DOCX).

Usage: python3 -I compare_form4.py <ppra.docx> <release_master.html>
Normalisation: lower-case, drop [insert ...] and {{ ... }} fields and underscores, unify spaces and ligatures, split into sentences.
"""
import difflib, html, json, re, sys, zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def norm(text: str) -> str:
	text = html.unescape(text).replace("ﬁ", "fi").replace("ﬂ", "fl").replace("“", '"').replace("”", '"')
	text = re.sub(r"\[[^\]]*\]", " ", text)           # [insert ...] fields
	text = re.sub(r"\{\{[^}]*\}\}", " ", text)         # template fields
	text = re.sub(r"_{3,}", " ", text)
	text = re.sub(r"[^a-z0-9\"]+", " ", text.lower())
	return re.sub(r"\s+", " ", text).strip()


docx, master = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(docx) as z:
	root = ET.fromstring(z.read("word/document.xml"))
paras = ["".join(t.text or "" for t in p.iter(W + "t")) for p in root.iter(W + "p")]
official = [norm(p) for p in paras[2647:2668] if norm(p)]
page = open(master, encoding="utf-8").read()
start = page.index("<h3>Form No. 4 - Contract Agreement</h3>")
end = page.find("{% if contract.performance_security.required %}", start)
release_text = re.sub(r"<[^>]+>", "\n", page[start:end])
release = [norm(p) for p in release_text.split("\n") if norm(p)]
a, b = " ".join(official), " ".join(release)
ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
only_official = [w for w in a.split() if w not in set(b.split())]
only_release = [w for w in b.split() if w not in set(a.split())]
ops = [(tag, a[i1:i2][:90], b[j1:j2][:90]) for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag != "equal" and (i2 - i1 > 12 or j2 - j1 > 12)]
print(json.dumps({"normalised_similarity": round(ratio, 4), "official_chars": len(a), "release_chars": len(b), "words_only_in_official": sorted(set(only_official)), "words_only_in_release": sorted(set(only_release)), "material_differences": ops[:12]}, indent=1))
