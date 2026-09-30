# Run inside `bench --site kentender.midas.com console < tools/dump_source.py` with
# KT_EVL_OUT set in the environment (a scratch directory). Writes the canonical
# Tender's published bid definition and the canonical bid package (evidence bytes
# elided) as JSON. Test-only read of the simulated tender box (stored_package).
import json, os, frappe
from kentender_procurement.bid_submission.test_services import tender_box
from kentender_procurement.tenders.services import bid_definition
out = os.environ.get("KT_EVL_OUT", "/tmp")
h = frappe.get_all("Evaluation Handoff", fields=["name", "tender", "payload_json"], limit=1)[0]
payload = json.loads(h.payload_json)
definition = bid_definition.current(h.tender)
pkgs = []
for env in payload["packages"]:
    att = frappe.db.get_value("Bid Submission Attempt", {"submission_version": env["submission_version"], "status": "Accepted"}, "correlation_id")
    pkg = json.loads(tender_box.stored_package(att))
    for e in pkg.get("evidence", []):
        for f in e.get("files", []):
            f["content_base64"] = "<elided>"
    pkgs.append(pkg)
json.dump({"handoff": payload, "definition": definition, "packages": pkgs}, open(os.path.join(out, "evl_source.json"), "w"), indent=1, default=str)
print("DUMPED", h.name, len(pkgs))
