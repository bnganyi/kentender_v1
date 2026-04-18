// Scoped UX for Strategy Management workspace only (Desk).
frappe.ready(function () {
	function strategyWorkspaceSlug() {
		const route = frappe.get_route() || [];
		if (route[0] !== "Workspaces") return null;
		return route[1] === "private" ? route[2] : route[1];
	}

	function syncStrategyShellClass() {
		const slug = strategyWorkspaceSlug();
		const match =
			slug === "strategy-management" ||
			slug === frappe.router.slug("Strategy Management");
		document.body.classList.toggle("kt-strategy-shell", !!match);
	}

	syncStrategyShellClass();
	$(document).on("page-change", syncStrategyShellClass);
});
