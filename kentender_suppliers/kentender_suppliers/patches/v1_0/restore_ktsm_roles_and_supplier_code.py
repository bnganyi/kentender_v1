# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""Restore the KTSM Frappe Roles and the Supplier business-code field (AUD-XC-004).

`ensure_kentender_sm_h1_roles_and_perms` and
`ensure_kentender_supplier_code_on_supplier` are logged as run, but a site can
lose their effect afterwards (dev and test sites were found without the
KenTender supplier roles and without `Supplier.kentender_supplier_code`). The
registry's named capabilities now live on those roles, so a site without them
has nobody who can act. Both underlying patches are idempotent; this one runs
them again on every site that has not recorded it.
"""

from kentender_suppliers.patches.v1_0 import (
	ensure_kentender_sm_h1_roles_and_perms,
	ensure_kentender_supplier_code_on_supplier,
)


def execute():
	ensure_kentender_sm_h1_roles_and_perms.execute()
	ensure_kentender_supplier_code_on_supplier.execute()
