"""ANL8-0703: expected Analytics figures for the two-year seed world, derived from the owner tables with plain SQL and never through a provider.

Run (no writes):
  cd /home/midasuser/frappe-bench && bench --site kentender-test.local execute kentender_core.tests.analytics_seed_world_expected.run
"""
import json, frappe
from decimal import Decimal as D

def expected():
	sql = lambda q, *a: frappe.db.sql(q, a, as_dict=True)
	years = {r.name: r for r in sql("select name, year_start_date from `tabFiscal Year` where name in ('2026-2027','2027-2028')")}
	out = {}
	for fy in years:
		needs = sql("select current_state s, count(*) n from `tabDepartmental Need` where financial_year=%s and current_state not in ('Draft','Withdrawn') group by current_state", fy)
		plans = sql("select active_version v, name from `tabAnnual Plan` where fiscal_year=%s and active_version is not null", fy)
		items = planned = covered = D(0); n_items = 0; states = {"full": 0, "partly": 0, "not": 0}
		for p in plans:
			its = sql("select plan_item_id pid from `tabAnnual Plan Item` where plan_version=%s and item_state='Active'", p.v)
			n_items += len(its)
			for it in its:
				pl = sql("select coalesce(sum(indicative_amount),0) a from `tabPlan Source Allocation` where plan_item_id=%s and plan_version=%s and allocation_state='Active'", it.pid, p.v)[0].a
				cv = sql("select coalesce(sum(amount),0) a from `tabPlan Drawdown Reference` where plan_item_id=%s and drawdown_state='Active'", it.pid)[0].a
				cv = min(D(str(cv)), D(str(pl)))
				planned += D(str(pl)); covered += cv
				states["full" if cv >= D(str(pl)) and pl > 0 else ("partly" if cv > 0 else "not")] += 1
		reqs = sql("select pr.current_state s, count(*) n from `tabProcurement Requisition` pr join `tabAnnual Plan` ap on ap.name = pr.plan_id where ap.fiscal_year=%s and pr.current_state not in ('Draft','Withdrawn') group by pr.current_state", fy)
		tnd = sql("select overall_status s, count(*) n from `tabTender` where fiscal_year=%s group by overall_status", fy)
		out[fy] = {"needs": {r.s: r.n for r in needs}, "plan_items": n_items, "coverage_states": states, "planned": str(planned), "covered": str(covered),
			"requisitions": {r.s: r.n for r in reqs}, "tenders_by_status": {r.s: r.n for r in tnd}}
	return out

def run():
	from kentender_core.services import analytics_workspace as aw
	exp = expected()
	user = "charles.mutiso@moh.example.test"
	frappe.set_user(user)
	for fy in (None, "2026-2027", "2027-2028"):
		o = aw.get_workspace(user, fy=fy or "")
		if o.get("empty"): print(fy, "EMPTY selection"); continue
		cols = {c["key"]: c for c in o["overview"]["strip"]["columns"]}
		seg = lambda k: {s["label"]: s["count"] for s in cols[k].get("segments", [])}
		cov = o["overview"]["coverage"]
		print("==", fy or "All years")
		print(" actual needs", cols["needs"]["figure"], seg("needs"), "| plan items", cols["annual_planning"]["figure"], seg("annual_planning"),
			"| reqs", cols["requisitions"]["figure"], seg("requisitions"), "| tenders", cols["tender_proceedings"]["figure"], seg("tender_proceedings"))
		print(" actual coverage", cov and (cov["planned"], cov["items"], cov["segments"][0]["text"]))
	print("EXPECTED (plain SQL):")
	print(json.dumps(exp, indent=1, default=str))
	frappe.set_user("Administrator")
