(() => {
	const addManualsLink = (container, before) => {
		if (!container || container.querySelector('a[href="/manuals"]')) return;
		const link = document.createElement("a");
		link.href = "/manuals";
		link.textContent = "Registration Manuals";
		link.className = "text-gray-700 font-medium hover:text-blue-600";
		container.insertBefore(link, before || null);
	};

	const install = () => {
		const desktopNav = document.querySelector("#mainNav");
		addManualsLink(desktopNav);

		const mobileMenu =
			document.querySelector("#mobileMenu-inner") ||
			document.querySelector("#mobileMenu .container") ||
			document.querySelector("#mobileMenu");
		const dashboardLink = mobileMenu?.querySelector('a[href="/app/home"]');
		addManualsLink(mobileMenu, dashboardLink);
	};

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", install, { once: true });
	} else {
		install();
	}
})();
