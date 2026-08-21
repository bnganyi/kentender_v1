import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.services.my_work import NO_ACTIVE_OPERATIONAL_ASSIGNMENT, claim_my_work_task, get_my_work, patch_bootinfo_home


class TestAuthorizationGate03(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.user = self._user("actor")
		self.other = self._user("other")
		self.outsider = self._user("outsider")
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.profile = frappe.get_doc({"doctype":"Capability Profile","profile_id":f"CAP-G03-{self.suffix}","profile_name":"Gate 03","capabilities":json.dumps(["budget.review"]),"allows_entity_wide":1,"status":"Active","effective_from":add_days(now_datetime(),-1),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		for dt in ("Workflow Task","Workflow Routing Rule","Workflow Queue Membership","Workflow Queue","Operational Scope Assignment","Capability Profile"):
			for name in frappe.get_all(dt, filters=[["name","like",f"%{self.suffix}%"]], pluck="name"):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
		for user in (self.user,self.other,self.outsider):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)

	def _user(self, label):
		email=f"auth.g03.{label}.{self.suffix}@test.local"
		frappe.get_doc({"doctype":"User","email":email,"first_name":label.title(),"enabled":1,"send_welcome_email":0}).insert(ignore_permissions=True)
		return email

	def _assignment(self, user=None, status="Active"):
		return frappe.get_doc({"doctype":"Operational Scope Assignment","assignment_id":f"OSA-G03-{uuid4().hex[:6]}-{self.suffix}","user_id":user or self.user,"capability_profile_id":self.profile.name,"procuring_entity_id":self.pe,"effective_from":add_days(now_datetime(),-1),"status":status,"assigned_by":"Administrator","assigned_at":now_datetime(),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)

	def _queue(self):
		return frappe.get_doc({"doctype":"Workflow Queue","queue_id":f"QUE-G03-{self.suffix}","queue_name":"Gate 03 Budget Queue","module_name":"Budget & Funding","required_capability":"budget.review","procuring_entity_id":self.pe,"status":"Active","effective_from":add_days(now_datetime(),-1),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)

	def _membership(self, queue, status="Active"):
		return frappe.get_doc({"doctype":"Workflow Queue Membership","membership_id":f"QMB-G03-{uuid4().hex[:6]}-{self.suffix}","queue_id":queue.name,"user_id":self.user,"effective_from":add_days(now_datetime(),-1),"status":status,"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)

	def _rule(self, user="", queue=None):
		rid=f"RTR-G03-{uuid4().hex[:6]}-{self.suffix}"
		return frappe.get_doc({"doctype":"Workflow Routing Rule","routing_version_id":f"RTV-{rid}","routing_rule_id":rid,"version":1,"module_name":"Budget & Funding","task_type":"budget.review","procuring_entity_id":self.pe,"required_capability":"budget.review","assignee_strategy":"Named claimable queue" if queue else "Named user","assignee_user_id":user,"queue_id":queue.name if queue else "","priority":100,"effective_from":add_days(now_datetime(),-1),"status":"Active","approved_by":"Administrator","approved_at":now_datetime()}).insert(ignore_permissions=True)

	def _task(self, rule, user="", queue="", creator="Administrator", state="Open"):
		tid=f"TSK-G03-{uuid4().hex[:6]}-{self.suffix}"
		return frappe.get_doc({"doctype":"Workflow Task","task_id":tid,"task_iteration":1,"module_name":"Budget & Funding","task_type":"budget.review","subject_type":"Procuring Entity","subject_id":self.pe,"procuring_entity_id":self.pe,"financial_year_id":"2027/28","routing_rule_id":rule.routing_rule_id,"routing_rule_version":rule.version,"assignee_type":"Queue" if queue else "User","assigned_user_id":user,"queue_id":queue,"state":state,"created_by_actor":creator,"created_at":now_datetime(),"concurrency_token":uuid4().hex,"idempotency_key":f"IDEM-{tid}"}).insert(ignore_permissions=True)

	def test_no_assignment_is_explicit(self):
		frappe.set_user(self.user)
		result=get_my_work()
		self.assertEqual(result["reason_code"],NO_ACTIVE_OPERATIONAL_ASSIGNMENT)
		self.assertEqual(result["counts"],{"assigned":0,"claimable":0,"waiting":0})

	def test_assigned_route_carries_subject_and_task_context(self):
		self._assignment(); rule=self._rule(self.user); task=self._task(rule,user=self.user)
		frappe.set_user(self.user); result=get_my_work(); row=result["buckets"]["assigned"][0]
		self.assertEqual(result["counts"],{"assigned":1,"claimable":0,"waiting":0})
		self.assertEqual(row["route"],["budget-review",self.pe])
		self.assertEqual(row["route_options"]["task_id"],task.name)
		self.assertEqual((row["procuring_entity"],row["financial_year"]),(self.pe,"2027/28"))

	def test_active_queue_member_can_claim_and_open(self):
		self._assignment(); queue=self._queue(); self._membership(queue); rule=self._rule(queue=queue); task=self._task(rule,queue=queue.name)
		frappe.set_user(self.user); before=get_my_work()
		self.assertEqual([r["task_id"] for r in before["buckets"]["claimable"]],[task.name])
		claimed=claim_my_work_task(task.name,task.concurrency_token)
		self.assertEqual(claimed["claimed_task"]["task_id"],task.name)
		self.assertEqual((claimed["counts"]["assigned"],claimed["counts"]["claimable"]),(1,0))

	def test_inactive_queue_membership_cannot_claim(self):
		self._assignment(); queue=self._queue(); self._membership(queue,status="Suspended"); rule=self._rule(queue=queue); self._task(rule,queue=queue.name)
		frappe.set_user(self.user)
		self.assertEqual(get_my_work()["counts"]["claimable"],0)

	def test_waiting_is_relationship_only_and_has_no_action(self):
		self._assignment(); rule=self._rule(self.other)
		waiting=self._task(rule,user=self.other,creator=self.user)
		self._task(rule,user=self.other,creator=self.outsider)
		self._task(rule,user=self.other,creator=self.user,state="Completed")
		frappe.set_user(self.user); result=get_my_work(); row=result["buckets"]["waiting"][0]
		self.assertEqual(result["counts"]["waiting"],1)
		self.assertEqual((row["task_id"],row["route"],row["action_label"]),(waiting.name,[],""))

	def test_operational_user_lands_on_my_work(self):
		self._assignment(); frappe.set_user(self.user); boot=frappe._dict(home_page="desktop"); patch_bootinfo_home(boot)
		self.assertEqual(boot.home_page,"my-work")

	def test_administrator_home_is_unchanged(self):
		frappe.set_user("Administrator"); boot=frappe._dict(home_page="desktop"); patch_bootinfo_home(boot)
		self.assertEqual(boot.home_page,"desktop")
