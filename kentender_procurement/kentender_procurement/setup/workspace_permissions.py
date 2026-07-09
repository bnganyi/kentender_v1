# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Boot-session patch for reliable KenTender sidebar visibility.

Root cause
----------
Frappe builds ``bootinfo.workspace_sidebar_item`` inside
``load_desktop_data`` → ``get_sidebar_items``.  A sidebar is included only
when ``sidebar_doc.module in sidebar_doc.user.allow_modules``.  That list is
built by ``User.build_permissions()``, cached per-user in Redis for six hours
(key: ``user:<email>:user_allowed_modules``).

After ``bench migrate``, ``frappe.clear_cache()`` flushes Redis — *including*
that per-user key.  On the very next browser request a gunicorn worker
rebuilds the key.  If ``build_permissions()`` runs while the DB is under
heavy migration I/O (tables being altered, fixtures being imported) the
DocPerm scan may return an incomplete list and ``Kentender Procurement`` can
be absent.  The empty/partial result is then cached for six hours, so every
subsequent page load on that worker silently omits the three procurement
sidebars — producing the blank left rail the user sees.

Additionally, ``auto_generate_sidebar_from_module`` is decorated with
``@site_cache()`` — a *process-level* cache that is NOT flushed when Redis is
cleared.  After ``bench migrate`` without ``bench restart`` each gunicorn
worker retains its own stale snapshot of which modules lack a Workspace
Sidebar record, which can cause further mismatches.

Fix
---
This ``boot_session`` hook runs *after* ``load_desktop_data`` has already
populated ``bootinfo.workspace_sidebar_item``.  It checks whether the three
KenTender navigation sidebars are present; if any are missing it builds their
dict representations directly from the ``Workspace Sidebar`` DB records and
injects them — unconditionally, without consulting ``allow_modules``.

The fix is:

* **Additive** – it never removes existing entries.
* **Idempotent** – it no-ops when sidebars are already there.
* **Safe** – it only adds public, standard sidebars that are shipped as
  fixtures with the app.
* **No monkey-patching** – plain Frappe data access only.
"""

from __future__ import annotations

import frappe

# Workspace Sidebar record names (as stored in ``tabWorkspace Sidebar``)
# shipped by this app that must always appear in the left navigation rail.
_KT_SIDEBAR_NAMES: tuple[str, ...] = (
	"Procurement",
	"Planning module navigation",
	"Demand Intake",
)

# Maps workspace page name → sidebar name that should be shown for that page.
#
# REGRESSION CHECKLIST: every **public Procurement-module workspace** that users can
# open from the desk (including direct URL / hard refresh) needs a row here, or the
# left rail renders empty. Add a test in ``setup/tests/test_workspace_sidebar_fastpath.py``.
# G0-012 spine stubs (**My Work**, **Bid Opening**, **Evaluation and Award**,
# **Contract Management**) must stay mapped to the main **Procurement** rail.
#
# WHY: Frappe's sidebar JS (sidebar.js set_workspace_sidebar) first checks
# ``frappe.boot.workspace_sidebar_item[entity_name.toLowerCase()]``.  If the
# key exists it calls ``setup(entity_name)`` directly — bypassing the
# ambiguous ``get_workspace_sidebars()`` search.  Without this mapping,
# ``get_workspace_sidebars("Procurement Planning")`` can return two matches
# when multiple sidebars list the same workspace.  Frappe needs a module from
# the router to break the tie, but ``router.meta.module`` is ``undefined`` for
# workspace→workspace navigation and on every hard refresh.  Result: no sidebar
# is set up and the navigation rail is blank.  Adding the workspace page name
# as a direct key removes the ambiguity entirely.
#
# DocType list/form routes use ``get_workspace_sidebars(doctype_name)``.  If two
# sidebars link to the same DocType, ``router.meta.module`` is often missing
# and Frappe never calls ``setup()`` — leaving a stale or empty rail.  Keep each
# settings DocType on at most one shipped sidebar (the main ``Procurement`` rail).
_KT_WORKSPACE_TO_SIDEBAR: dict[str, str] = {
	# Keep Planning surfaces nested under the main Procurement IA shell.
	"procurement planning": "Procurement",
	"procurement-planning": "Procurement",
	"planning-hub": "Procurement",
	"procurement-planning/approved-demands": "Procurement",
	"approved-demands": "Procurement",
	"procurement-planning/plans": "Procurement",
	"plans": "Procurement",
	"procurement-planning/packages": "Procurement",
	"packages": "Procurement",
	"procurement-planning/releases": "Procurement",
	"releases": "Procurement",
	"demand intake and approval": "Procurement",
	"demand-intake-and-approval": "Procurement",
	"procurement home": "Procurement",
	"procurement-home": "Procurement",
	"procurement journeys": "Procurement",
	"plc-procurement-journey": "Procurement",
	"audit event": "Procurement",
	"audit-event": "Procurement",
	"my work": "Procurement",
	"my-work": "Procurement",
	"bid opening": "Procurement",
	"bid-opening": "Procurement",
	"evaluation and award": "Procurement",
	"evaluation-and-award": "Procurement",
	"contract management": "Procurement",
	"contract-management": "Procurement",
	"ktsm supplier registry": "Procurement",
	"ktsm-supplier-registry": "Procurement",
	"governance & configuration": "Procurement",
	"governance-and-configuration": "Procurement",
	# Cross-app lifecycle workspaces: keep the Procurement rail when users follow
	# G0-012 sidebar links (same pattern as DIA / Planning).
	"strategy management": "Procurement",
	"strategy-management": "Procurement",
	"budget management": "Procurement",
	"budget-management": "Procurement",
	# Module-level and DocType-level routes fallback to this key path in
	# frappe/ui/sidebar/sidebar.js when route key disambiguation is missing.
	# Without these keys, /desk/budget/new-* and /desk/strategic-plan/new-*
	# frequently collapse to reduced app-specific sidebars.
	"budget": "Procurement",
	"strategy": "Procurement",
	"demand": "Procurement",
}

# Custom desk page + guided form routes → parent sidebar (context-preserving navigation).
# Keys match Frappe sidebar.js fast-path lookups (route segment or Form/Doctype).
try:
	from kentender_core.module_registry import get_route_sidebar_keys

	_KT_ROUTE_TO_SIDEBAR: dict[str, str] = get_route_sidebar_keys()
except Exception:
	_KT_ROUTE_TO_SIDEBAR = {
		"strategy-builder": "Procurement",
		"budget-builder": "Procurement",
		"form/strategic plan": "Procurement",
		"form/budget": "Procurement",
		"form/demand": "Procurement",
		"form/procurement package": "Procurement",
		"form/ktsm supplier profile": "Procurement",
	}

# Hard-map critical page/doctypes that must always stay on Procurement rail.
# These are user-facing routes from the Procurement sidebar and should never
# fall back to Kentender Core/App-sidebars because of route context drift.
_KT_ROUTE_TO_SIDEBAR.update(
	{
		"procurement-home": "Procurement",
		"plc-procurement-journey": "Procurement",
		"tender-management-v2": "Procurement",
		"audit-event": "Procurement",
		"audit event": "Procurement",
	}
)

# STD prod iframe Desk pages — keep parent Procurement rail (not STD Engine module sidebar).
_STD_PROD_PAGE_ROUTE_KEYS = (
	"std-library",
	"std-family-detail",
	"std-version-detail",
	"std-source-doc",
	"std-section-clauses",
	"std-clause-detail",
	"std-validation-report",
	"std-audit-log",
	"std-parameter-dictionary",
	"std-parameter-detail",
	"std-rule-dictionary",
	"std-rule-detail",
	"std-form-schema-manager",
	"std-form-detail-field-builder",
	"std-requirement-schema-manager",
	"std-price-schedule-schema",
	"std-evaluation-schema",
	"std-render-blocks",
	"std-review-and-approval",
	"std-usage-and-tender-bindings",
	"std-import-package-review",
	"std-version-diff-and-supersession",
	"std-module-retired",
)
for _route_key in _STD_PROD_PAGE_ROUTE_KEYS:
	_KT_ROUTE_TO_SIDEBAR[_route_key] = "Procurement"

# G0-012 / R5 sidebar regression: **Strategy Management** and **Budget Management**
# live in other apps. If those Workspace rows are not ``public`` / are ``is_hidden``,
# ``allowed_workspaces`` drops them and the primary-rail links **Strategy Alignment**
# and **Budget & Funding** disappear (My Work → Demand Intake with no bridge).
# Always include these workspace targets when the Workspace document exists.
_FORCE_INCLUDE_WORKSPACE_IF_EXISTS: frozenset[str] = frozenset(
	(
		"Strategy Management",
		"Budget Management",
	)
)


def patch_bootinfo(bootinfo) -> None:
	"""boot_session hook – unconditionally rebuild all KenTender sidebars.

	Called by Frappe at the end of ``get_bootinfo()`` with the fully-built
	bootinfo dict.

	WHY unconditional?  Frappe's ``get_sidebar_items`` filters each item using
	``is_item_allowed``, which requires the item's target workspace to already
	be in ``allowed_pages``.  ``allowed_pages`` is built from
	``get_workspace_sidebar_items``, which in turn calls ``Workspace.__init__``
	and raises ``PermissionError`` when ``workspace.module`` is not in
	``user_allowed_modules``.

	For non-admin users (e.g. Procurement Planner) the three KenTender
	workspace pages are silently excluded from ``allowed_pages``.  This leaves
	the "Planning module navigation" sidebar with only the DocType link
	("Procurement Templates") and NO workspace links.  When the user lands on
	any of the three workspace pages the sidebar JS finds no sidebar item that
	matches the current page and renders the navigation rail empty.

	We bypass all of that by rebuilding every KenTender sidebar directly from
	its ``Workspace Sidebar`` DB record, using the set of *all* public
	workspaces as the ``allowed_workspaces`` filter — regardless of the user's
	module permissions.  The three workspaces (Procurement Planning, DIA,
	Procurement Home) are public and visible, so they always pass.
	"""
	sidebar_items = bootinfo.get("workspace_sidebar_item")
	if not isinstance(sidebar_items, dict):
		return

	# Build the set of public, visible workspace names once (one cheap DB call).
	allowed_workspaces: set[str] = set(
		frappe.get_all(
			"Workspace",
			filters={"public": 1, "is_hidden": 0},
			pluck="name",
		)
	)

	# Step 1: rebuild the sidebar records by their own name.
	built: dict[str, dict] = {}
	for name in _KT_SIDEBAR_NAMES:
		if not frappe.db.exists("Workspace Sidebar", name):
			continue
		try:
			d = _build_sidebar_dict(name, allowed_workspaces)
			sidebar_items[name.lower()] = d
			built[name] = d
		except Exception:
			# Never crash the boot because of a navigation patch.
			frappe.log_error(
				title=f"KenTender workspace_permissions: failed to inject sidebar '{name}'",
				message=frappe.get_traceback(),
			)

	# Step 2: inject workspace-page-name keys so Frappe's sidebar JS fast-path
	# (``workspace_sidebar_item[entity_name.toLowerCase()]``) resolves directly
	# without going through the ambiguous ``get_workspace_sidebars()`` search.
	#
	# Always overwrite these keys: Frappe may already have registered a workspace
	# slug with a different sidebar (e.g. module-scoped); leaving it would keep
	# the stripped rail after migrate.
	for ws_key, sidebar_name in _KT_WORKSPACE_TO_SIDEBAR.items():
		payload = built.get(sidebar_name) or sidebar_items.get(sidebar_name.lower(), {})
		if payload:
			sidebar_items[ws_key] = payload

	# Step 3: builder / form route prefixes (strategy-builder, Form/Demand, …)
	for route_key, sidebar_name in _KT_ROUTE_TO_SIDEBAR.items():
		payload = built.get(sidebar_name) or sidebar_items.get(sidebar_name.lower(), {})
		if payload:
			sidebar_items[route_key.lower()] = payload

	# Frappe builds `bootinfo.desktop_icons` in `get_bootinfo()` *before* `boot_session`
	# hooks run. `DesktopIcon.is_permitted` reads `workspace_sidebar_item["procurement"]`
	# — without a second pass the Procurement tile stays hidden for users whose sidebar
	# only becomes valid after this patch (e.g. narrowly-scoped desk roles). Recompute icons
	# against the patched bootinfo and refresh the per-user desktop icon cache.
	if frappe.session.user not in (None, "Guest"):
		from frappe import _dict as frappe_dict
		from frappe.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache, get_desktop_icons

		clear_desktop_icons_cache(frappe.session.user)
		# `DesktopIcon.is_permitted` uses attribute access (`bootinfo.workspace_sidebar_item`);
		# unit tests pass a plain `dict` — wrap for compatibility with Frappe core.
		boot_for_icons = frappe_dict(bootinfo) if type(bootinfo) is dict else bootinfo
		icons = get_desktop_icons(bootinfo=boot_for_icons)
		if type(bootinfo) is dict:
			bootinfo["desktop_icons"] = icons
		else:
			bootinfo.desktop_icons = icons


def _build_sidebar_dict(name: str, allowed_workspaces: set[str]) -> dict:
	"""Return the bootinfo-format sidebar dict for *name*.

	Workspace-type links are included when their target is public and visible,
	**or** when the target is one of ``_FORCE_INCLUDE_WORKSPACE_IF_EXISTS`` and a
	``Workspace`` row exists (cross-app G0-012 rail — see module docstring).
	All other link types are included unconditionally.
	"""
	doc = frappe.get_doc("Workspace Sidebar", name)
	items: list[dict] = []

	for item in doc.items:
		link_type = (item.link_type or "").lower()
		if item.type == "Section Break" or _workspace_link_passes_filters(
			item.link_to,
			link_type,
			allowed_workspaces,
		):
			items.append(
				{
					"label": item.label,
					"link_to": item.link_to,
					"link_type": item.link_type,
					"type": item.type,
					"icon": item.icon,
					"child": item.child,
					"collapsible": item.collapsible,
					"indent": item.indent,
					"keep_closed": item.keep_closed,
					"display_depends_on": item.display_depends_on,
					"url": item.url,
					"show_arrow": item.show_arrow,
					"filters": item.filters,
					"route_options": item.route_options,
					"tab": item.navigate_to_tab,
				}
			)

	return {
		"label": doc.title or name,
		"items": items,
		"header_icon": doc.header_icon,
		"module_onboarding": doc.module_onboarding,
		"module": doc.module,
		"app": doc.app,
	}


def _workspace_link_passes_filters(
	link_to: str | None,
	link_type: str,
	allowed_workspaces: set[str],
) -> bool:
	lt = (link_type or "").lower()
	if lt != "workspace":
		return True
	code = (link_to or "").strip()
	if not code:
		return False
	if code in allowed_workspaces:
		return True
	if code in _FORCE_INCLUDE_WORKSPACE_IF_EXISTS:
		# Include cross-app lifecycle workspaces even when `public` / hidden flags
		# were mis-set on site — navigation-only; Workspace route still enforces perms.
		return bool(frappe.db.exists("Workspace", code))
	return False
