import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class TenantRegistration(Document):
    def before_insert(self):
        if not self.registered_at:
            self.registered_at = now_datetime()

    def validate(self):
        if self.status not in ("Pending", "Provisioning", "Active", "Failed"):
            frappe.throw("Invalid tenant registration status.")
