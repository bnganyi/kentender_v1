The root correction is to establish one canonical Workspace identity:

- Database name: Budget Management
- User-facing label: Budget & Funding
- Route: /app/budget-management
- Procurement sidebar target: Budget Management

Currently both install.py and the teardown patch check for Budget Management but allow Frappe to derive the database name from the label, producing Budget & Funding.

**1\. Create one shared workspace helper**

Add a helper such as:

kentender_budget/kentender_budget/setup/budget_workspace.py

Its responsibility should be:

import frappe

CANONICAL_NAME = "Budget Management"

LEGACY_NAME = "Budget & Funding"

def ensure_budget_workspace() -> str:

if not frappe.db.exists("Workspace", CANONICAL_NAME):

if frappe.db.exists("Workspace", LEGACY_NAME):

frappe.rename_doc(

"Workspace",

LEGACY_NAME,

CANONICAL_NAME,

force=True,

)

else:

doc = frappe.get_doc(

{

"doctype": "Workspace",

"label": "Budget & Funding",

"title": CANONICAL_NAME,

"module": "Kentender Budget",

"app": "kentender_budget",

"type": "Workspace",

"content": "\[\]",

"icon": "money-bill-wave",

"public": 1,

"is_hidden": 0,

}

)

doc.insert(

ignore_permissions=True,

set_name=CANONICAL_NAME,

)

frappe.db.set_value(

"Workspace",

CANONICAL_NAME,

{

"label": "Budget & Funding",

"title": CANONICAL_NAME,

"module": "Kentender Budget",

"app": "kentender_budget",

"public": 1,

"is_hidden": 0,

},

update_modified=False,

)

return CANONICAL_NAME

Using insert(set_name=...) is the important correction; Frappe explicitly supports setting the document name during insertion. [Frappe Document API source](https://github.com/frappe/frappe/blob/develop/frappe/model/document.py?utm_source=chatgpt.com)

**2\. Remove the duplicated faulty creation code**

Both of these should call ensure_budget_workspace():

- kentender_budget/install.py
- kentender_budget/patches/mvp1_teardown_drop_legacy_budget_doctypes.py

There should be no second implementation of Workspace creation.

**3\. Add a corrective migration patch**

Create:

kentender_budget/patches/normalize_budget_management_workspace.py

The patch should simply call the helper:

from kentender_budget.setup.budget_workspace import ensure_budget_workspace

def execute():

ensure_budget_workspace()

Add it to patches.txt after the existing teardown patch:

kentender_budget.patches.mvp1_teardown_drop_legacy_budget_doctypes

kentender_budget.patches.normalize_budget_management_workspace

This repairs existing installations and creates the canonical record on fresh ones before after_migrate navigation runs.

**4\. Keep the Procurement link unchanged**

This is already correct:

{

"label": "Budget & Funding",

"link_to": "Budget Management",

"link_type": "Workspace"

}

Do not change link_to to the display label.

**5\. Add focused tests**

Test only these cases:

- neither Workspace exists → canonical Workspace is created;
- only legacy Budget & Funding exists → it is renamed;
- canonical Workspace exists → repeated calls make no duplicate;
- Procurement sidebar inserts after the helper runs;
- the final Workspace has name Budget Management and label Budget & Funding.

Then verify with:

bench --site cardinal-demo.xyz migrate

bench --site cardinal-demo.xyz execute frappe.db.exists \\

\--args '\["Workspace", "Budget Management"\]'

This fixes both the current site and every subsequent installation without weakening link validation or adding a second Workspace.