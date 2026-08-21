"""AUTH-UI-05 Planning-owned support projection contract."""

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_procurement.procurement_planning.services.get_support_plan import get_support_plan


class TestSupportPlanGate04(IntegrationTestCase):
	def test_support_projection_has_no_operational_actions(self):
		plan = frappe.get_all("Procurement Plan", filters=[["current_approved_version","is","set"]], fields=["name","procuring_entity"], limit=1)
		if not plan:
			self.skipTest("No approved Procurement Plan fixture is installed")
		suffix = uuid4().hex[:8]
		user = f"auth.g04.plan.{suffix}@test.local"
		frappe.get_doc({"doctype":"User","email":user,"first_name":"Support","enabled":1,"send_welcome_email":0}).insert(ignore_permissions=True)
		profile = frappe.get_doc({"doctype":"Capability Profile","profile_id":f"CAP-G04-PLAN-{suffix}","profile_name":"Plan Support","capabilities":json.dumps(["support.record.view"]),"allows_entity_wide":1,"status":"Active","effective_from":add_days(now_datetime(),-1),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)
		assignment = frappe.get_doc({"doctype":"Operational Scope Assignment","assignment_id":f"OSA-G04-PLAN-{suffix}","user_id":user,"capability_profile_id":profile.name,"procuring_entity_id":plan[0].procuring_entity,"effective_from":add_days(now_datetime(),-1),"status":"Active","assigned_by":"Administrator","assigned_at":now_datetime(),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)
		try:
			projection = get_support_plan(plan=plan[0].name, purpose="Test", user=user)
			self.assertEqual(set(projection["actions"]), {"back"})
			for forbidden in ("items", "finance_evidence", "review", "approve", "return"):
				self.assertNotIn(forbidden, projection)
			self.assertTrue(frappe.db.exists("Audit Event", {"event_type":"authorization.support_record_view","performed_by":user}))
		finally:
			frappe.db.delete("Audit Event", {"performed_by":user})
			frappe.delete_doc("Operational Scope Assignment", assignment.name, force=True, ignore_permissions=True)
			frappe.delete_doc("Capability Profile", profile.name, force=True, ignore_permissions=True)
			frappe.delete_doc("User", user, force=True, ignore_permissions=True)
			frappe.db.commit()
