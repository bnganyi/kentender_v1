(() => {
	const wrap = document.querySelector(".kt-profile-wrap");
	const trigger = wrap?.querySelector("#kt-profile-button");
	const menu = wrap?.querySelector("#kt-profile-menu");
	if (!wrap || !trigger || !menu) return;

	function setOpen(open) {
		menu.hidden = !open;
		trigger.setAttribute("aria-expanded", open ? "true" : "false");
	}

	trigger.addEventListener("click", (event) => {
		event.stopPropagation();
		setOpen(menu.hidden);
	});
	document.addEventListener("click", (event) => {
		if (!wrap.contains(event.target)) setOpen(false);
	});
	document.addEventListener("keydown", (event) => {
		if (event.key === "Escape" && !menu.hidden) {
			setOpen(false);
			trigger.focus();
		}
	});
	menu.addEventListener("click", (event) => {
		const logout = event.target.closest("[data-kt-profile-logout]");
		if (!logout) return;
		event.preventDefault();
		setOpen(false);
		if (typeof frappe.logout === "function") {
			frappe.logout();
		} else if (frappe.app && typeof frappe.app.logout === "function") {
			frappe.app.logout();
		} else {
			window.location.href = "/login";
		}
	});
})();
