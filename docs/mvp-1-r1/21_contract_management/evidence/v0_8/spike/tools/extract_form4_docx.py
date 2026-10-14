import hashlib, json, sys, zipfile
import xml.etree.ElementTree as ET
path = sys.argv[1]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
raw = open(path, "rb").read()
out = {"sha256": hashlib.sha256(raw).hexdigest(), "expected": "ee081f608999d4b17fa7b83e005f0ac56a9befd811644c464a2f771224f05e81"}
out["hash_matches_spec"] = out["sha256"] == out["expected"]
with zipfile.ZipFile(path) as z:
    info = z.getinfo("word/document.xml")
    out["document_xml_bytes"] = info.file_size
    if info.file_size > 200_000_000:
        raise SystemExit("document.xml too large to parse safely")
    root = ET.fromstring(z.read("word/document.xml"))
paras = ["".join(t.text or "" for t in p.iter(W + "t")) for p in root.iter(W + "p")]
out["paragraph_count"] = len(paras)
out["form4_window"] = {i: paras[i] for i in range(2645, 2671) if i < len(paras)}
heads = [i for i, t in enumerate(paras) if "contract agreement" in t.lower() and len(t) < 90]
out["paragraphs_naming_contract_agreement_short"] = {i: paras[i] for i in heads[:12]}
print(json.dumps(out, indent=1, ensure_ascii=False))
