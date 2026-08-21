"""AUTH-G04 administration, diagnostic and support authorization evidence."""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.services.authorization_administration import activate_revised_routing_rule, change_assignment_state, create_draft_assignment, create_queue_membership, create_revised_routing_rule
from kentender_core.services.authorization_diagnostics import authorize_support_record_view, diagnose_access
from kentender_core.services.authorization_policy import ResourceContext


class TestAuthorizationGate04(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:8]
		self.user = self._user("operator")
		self.support = self._user("support")
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.profile = self._profile("Operational", ["plan.finance.confirm"])
		self.support_profile = self._profile("Support", ["support.record.view", "authorization.diagnostic.view"])
		self.support_assignment = self._assignment(self.support, self.support_profile)
		self.resource = ResourceContext("Procuring Entity", self.pe, self.pe, "2027/28")

	def tearDown(self):
		frappe.db.delete("Audit Event", {"performed_by": ["in", [self.user, self.support]]})
		for doctype in ("Audit Event", "Workflow Routing Rule", "Workflow Queue Membership", "Workflow Queue", "Separation of Duties Rule", "Operational Scope Assignment", "Capability Profile"):
			field = "document_name" if doctype == "Audit Event" else "name"
			for name in frappe.get_all(doctype, filters=[[field, "like", f"%{self.suffix}%"]], pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		for user in (self.user, self.support):
			if frappe.db.exists("User", user):
				frappe.delete_doc("User", user, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _user(self, label):
		email = f"auth.g04.{label}.{self.suffix}@test.local"
		frappe.get_doc({"doctype":"User","email":email,"first_name":label,"enabled":1,"send_welcome_email":0}).insert(ignore_permissions=True)
		return email

	def _profile(self, label, capabilities):
		return frappe.get_doc({"doctype":"Capability Profile","profile_id":f"CAP-G04-{label}-{self.suffix}","profile_name":label,"capabilities":json.dumps(capabilities),"allows_entity_wide":1,"status":"Active","effective_from":add_days(now_datetime(),-1),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)

	def _assignment(self, user, profile):
		return frappe.get_doc({"doctype":"Operational Scope Assignment","assignment_id":f"OSA-G04-{uuid4().hex[:5]}-{self.suffix}","user_id":user,"capability_profile_id":profile.name,"procuring_entity_id":self.pe,"effective_from":add_days(now_datetime(),-1),"status":"Active","assigned_by":"Administrator","assigned_at":now_datetime(),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)

	def _rule(self):
		return frappe.get_doc({"doctype":"Workflow Routing Rule","routing_version_id":f"RTV-G04-{self.suffix}","routing_rule_id":f"RTR-G04-{self.suffix}","version":1,"module_name":"Procurement Planning","task_type":"plan.finance.confirm","procuring_entity_id":self.pe,"required_capability":"plan.finance.confirm","assignee_strategy":"Named user","assignee_user_id":self.user,"priority":100,"effective_from":add_days(now_datetime(),-1),"status":"Active","approved_by":"Administrator","approved_at":now_datetime()}).insert(ignore_permissions=True)

	def test_assignment_lifecycle_is_concurrency_protected_and_audited(self):
		draft = create_draft_assignment({"assignment_id":f"OSA-G04-LIFE-{self.suffix}","user_id":self.user,"capability_profile_id":self.profile.name,"procuring_entity_id":self.pe,"effective_from":now_datetime()}, user="Administrator")
		active = change_assignment_state(draft.name, draft.concurrency_token, "Active", user="Administrator")
		with self.assertRaises(frappe.ValidationError):
			change_assignment_state(draft.name, draft.concurrency_token, "Suspended", user="Administrator")
		ended = change_assignment_state(active.name, active.concurrency_token, "Ended", reason="Contract ended", user="Administrator")
		self.assertEqual(ended.status, "Ended")
		self.assertTrue(frappe.db.exists("Audit Event", {"document_name":draft.name,"action":"ended"}))

	def test_categorical_assignment_sod_is_blocked(self):
		self._assignment(self.user, self.profile)
		other_profile = self._profile("Authority", ["plan.approve"])
		frappe.get_doc({"doctype":"Separation of Duties Rule","rule_id":f"SOD-G04-{self.suffix}","rule_name":"Finance versus approval","first_capability":"plan.finance.confirm","second_capability":"plan.approve","enforcement_level":"Assignment","status":"Active","effective_from":add_days(now_datetime(),-1)}).insert(ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			create_draft_assignment({"user_id":self.user,"capability_profile_id":other_profile.name,"procuring_entity_id":self.pe,"effective_from":now_datetime()}, user="Administrator")

	def test_routing_revision_supersedes_without_editing_active_version(self):
		self._assignment(self.user, self.profile)
		current = self._rule()
		revised = create_revised_routing_rule(current.name, user="Administrator")
		activated = activate_revised_routing_rule(revised.name, user="Administrator")
		self.assertEqual(activated.status, "Active")
		self.assertEqual(frappe.db.get_value("Workflow Routing Rule", current.name, "status"), "Superseded")
		self.assertEqual(frappe.db.get_value("Workflow Routing Rule", current.name, "version"), 1)

	def test_queue_membership_requires_governed_capability_scope(self):
		queue = frappe.get_doc({"doctype":"Workflow Queue","queue_id":f"QUE-G04-{self.suffix}","queue_name":"Gate 04","module_name":"Procurement Planning","required_capability":"plan.finance.confirm","procuring_entity_id":self.pe,"status":"Active","effective_from":add_days(now_datetime(),-1),"concurrency_token":uuid4().hex}).insert(ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			create_queue_membership({"queue_id":queue.name,"user_id":self.user,"effective_from":now_datetime()}, user="Administrator")
		self._assignment(self.user, self.profile)
		membership = create_queue_membership({"membership_id":f"QMB-G04-{self.suffix}","queue_id":queue.name,"user_id":self.user,"effective_from":now_datetime()}, user="Administrator")
		self.assertEqual(membership.user_id, self.user)

	def test_diagnostic_is_read_only_and_support_projection_is_explicit_and_audited(self):
		diagnostic = diagnose_access(tested_user=self.user, capability="plan.finance.confirm", resource=self.resource, actor="Administrator")
		self.assertFalse(diagnostic["allowed"])
		self.assertNotIn("actions", diagnostic)
		with self.assertRaises(frappe.PermissionError):
			authorize_support_record_view(user="Administrator", resource=self.resource, purpose="Support")
		authorize_support_record_view(user=self.support, resource=self.resource, purpose=f"Support {self.suffix}")
		self.assertTrue(frappe.db.exists("Audit Event", {"event_type":"authorization.support_record_view","performed_by":self.support}))

	def test_generated_pages_are_bound_to_protected_live_services(self):
		for page in ("user-operational-acc", "workflow-routing-rul", "access-diagnostic", "support-plan-view"):
			self.assertTrue(frappe.db.exists("Page", page))
