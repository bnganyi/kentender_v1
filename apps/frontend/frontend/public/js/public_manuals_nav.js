(() => {
	const closeDropdowns = () => {
		document
			.querySelectorAll("#mainNav .dropdown, .manuals-nav .dropdown")
			.forEach((dropdown) => {
				const button = dropdown.querySelector(".dropdown-toggle");
				const menu = dropdown.querySelector(".dropdown-menu");
				button?.setAttribute("aria-expanded", "false");
				menu?.classList.remove("show");
			});
	};

	const addManualsLink = (container, before) => {
		if (!container || container.querySelector('a[href="/manuals"]')) return;
		const link = document.createElement("a");
		link.href = "/manuals";
		link.textContent = "Registration Manuals";
		link.className = "text-gray-700 font-medium hover:text-blue-600";
		container.insertBefore(link, before || null);
	};

	const normalizeActiveLink = () => {
		const path = window.location.pathname.replace(/\/$/, "") || "/";
		const navLinks = document.querySelectorAll(
			"#mainNav a, .manuals-nav a, #mobileMenu a, #manuals-mobile-nav a",
		);

		navLinks.forEach((link) => {
			const linkPath =
				new URL(link.href, window.location.origin).pathname.replace(/\/$/, "") || "/";
			const matches = linkPath === path || (path === "/" && linkPath === "/home");
			link.classList.toggle("active", matches);
			if (matches) link.setAttribute("aria-current", "page");
			else link.removeAttribute("aria-current");
			["border-bottom", "padding-bottom", "display", "color", "font-weight"].forEach(
				(property) => {
					link.style.removeProperty(property);
				},
			);
		});

		document
			.querySelectorAll("#mainNav .dropdown, .manuals-nav .dropdown")
			.forEach((dropdown) => {
				const button = dropdown.querySelector(".dropdown-toggle");
				button?.setAttribute("aria-haspopup", "true");
				if (button && !button.hasAttribute("aria-expanded"))
					button.setAttribute("aria-expanded", "false");
				button?.classList.toggle("active", Boolean(dropdown.querySelector("a.active")));
			});
	};

	const updateClock = () => {
		const clock = document.getElementById("live-time");
		if (!clock) return;
		const values = Object.fromEntries(
			new Intl.DateTimeFormat("en-GB", {
				timeZone: "Africa/Nairobi",
				weekday: "short",
				day: "2-digit",
				month: "short",
				year: "numeric",
				hour: "2-digit",
				minute: "2-digit",
				hourCycle: "h23",
			})
				.formatToParts(new Date())
				.map(({ type, value }) => [type, value]),
		);
		clock.textContent = `${values.weekday}, ${values.day} ${values.month} ${values.year}, ${values.hour}:${values.minute}`;
	};

	const installDropdowns = () => {
		document.addEventListener(
			"click",
			(event) => {
				const button = event.target.closest(
					"#mainNav .dropdown-toggle, .manuals-nav .dropdown-toggle",
				);
				if (button) {
					event.preventDefault();
					event.stopImmediatePropagation();
					const dropdown = button.closest(".dropdown");
					const open = button.getAttribute("aria-expanded") !== "true";
					closeDropdowns();
					button.setAttribute("aria-expanded", String(open));
					dropdown.querySelector(".dropdown-menu")?.classList.toggle("show", open);
					return;
				}
				if (!event.target.closest("#mainNav .dropdown, .manuals-nav .dropdown"))
					closeDropdowns();
			},
			true,
		);

		document.addEventListener("keydown", (event) => {
			if (event.key === "Escape") closeDropdowns();
		});
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
		normalizeActiveLink();
		installDropdowns();
		updateClock();
		window.setInterval(updateClock, 30000);
	};

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", install, { once: true });
	} else {
		install();
	}
})();
