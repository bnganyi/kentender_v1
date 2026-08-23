// CFG-CHG-002 — Claude Design -> Vue 3, kentender_core's first production Reference
// Data screen (Procuring Entities / Financial Years / PE-FY Contexts). Partial
// shared-shell participation: kt_cl_shell.enterNative() for the shared native
// sidebar only — never mountContent()/updateChrome() near the Vue root. The Civic
// Ledger chrome host that enterNative() sets up is a different design system
// (Tailwind/Material Symbols) from this page's Industry tokens, so the page rail
// (CFG-PEFY-DES-12) is rendered by Vue's own PageRail.vue instead, scoped inside
// .kt-industry — kt_industry_tokens.css is deliberately scoped to never leak into
// Desk chrome, and the reverse holds too: Desk chrome never leaks into this rail.
frappe.pages["reference-data"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Reference Data"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["reference-data"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		// "procurement" is the one real, populated Workspace Sidebar every KenTender
		// module shares natively (see workspace_sidebar/procurement.json) — every other
		// module (Strategy, Budget, Planning, Departmental Needs) uses this same key.
		// A "configuration-governance" key was tried first but doesn't resolve to any
		// real Workspace Sidebar doc, so it silently fell back to a bad title.
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		// enterNative() only self-populates #kt-cl-chrome-host when given toolbar/chrome
		// opts (which this page deliberately never passes — see file header), but the
		// host div is reused across navigations rather than recreated, so it can still
		// carry another surface's rendered toolbar over from earlier in the session.
		// PageRail.vue is this page's only rail — force the host empty so nothing else
		// can ever render a second one above it.
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		// kt_cl_code_layout.css hides Frappe's native .page-head/.navbar with a
		// `!important` stylesheet rule under body.kt-cl-shell, and that's held up in
		// every reproduction attempt here — but Frappe's own scroll handler
		// (page.js#setup_scroll_handler) still touches .page-head's inline style on
		// every scroll tick, and inline styles set after ours would win a cascade race
		// a plain stylesheet rule can't. Force it below the wire directly so nothing —
		// including a future Frappe upgrade to that handler — can ever re-surface it
		// on scroll.
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_reference_data(wrapper);
};

frappe.pages["reference-data"].on_page_hide = function (wrapper) {
	wrapper.__kt_reference_data_pending = false; // cancel an in-flight mount race (see below)
	unmount_reference_data(wrapper);
};

function mount_reference_data(wrapper) {
	if (wrapper.__kt_reference_data_app) {
		// Already mounted (on_page_show fired again without an intervening hide) — Vue's
		// own reactivity + route watcher handle sub-route changes from here; re-mounting
		// would duplicate the app.
		return;
	}

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	// frappe.require() is async — guard against on_page_hide firing before it resolves
	// (a fast navigate-away-and-back on the very first, uncached load of the bundle),
	// which would otherwise mount an app nothing ever unmounts.
	wrapper.__kt_reference_data_pending = true;
	frappe.require("reference_data.bundle.js").then(() => {
		if (!wrapper.__kt_reference_data_pending) return;
		wrapper.__kt_reference_data_pending = false;
		wrapper.__kt_reference_data_app = frappe.kt_mount_reference_data(el);
	});
}

function unmount_reference_data(wrapper) {
	if (!wrapper.__kt_reference_data_app) return;
	wrapper.__kt_reference_data_app.unmount();
	wrapper.__kt_reference_data_app = null;
}
