(() => {
	const form = document.getElementById("tender-filters");
	if (!form) return;

	const searchInput = document.getElementById("tender-search");
	const methodSelect = document.getElementById("tender-method");
	const reservationSelect = document.getElementById("tender-reservation");
	const closingSelect = document.getElementById("tender-closing");
	const results = document.getElementById("tender-results");
	const count = document.getElementById("tender-count");
	const state = document.getElementById("tender-results-state");
	const errorNotice = document.getElementById("tender-load-error");
	const resetButton = document.getElementById("tender-filter-reset");
	const retryButton = document.getElementById("tender-retry");
	const filterPanel = document.getElementById("filterPanel");
	const filterToggle = document.getElementById("filterToggle");
	const endpoint = "frontend.api.tender_import.get_available_tenders";
	let requestVersion = 0;
	let searchTimer = null;

	function addFact(container, label, value) {
		if (!value) return;
		const fact = document.createElement("div");
		const factLabel = document.createElement("div");
		factLabel.className = "tender-card-fact-label mb-1";
		factLabel.textContent = label;
		const factValue = document.createElement("div");
		factValue.className = "tender-card-fact-value";
		factValue.textContent = value;
		fact.append(factLabel, factValue);
		container.append(fact);
	}

	function renderTender(row) {
		const card = document.createElement("article");
		card.className = "rounded-2xl shadow-lg card-hover overflow-hidden bg-black/5 tender-card";
		const reservation =
			!row.reservation || row.reservation.trim().toLowerCase() === "none"
				? "No reservation"
				: row.reservation;

		const content = document.createElement("div");
		content.className = "p-6";
		const top = document.createElement("div");
		top.className = "flex justify-between items-start mb-4 flex-wrap gap-2 tender-card-top";
		const badges = document.createElement("div");
		badges.className = "flex gap-2";
		const category = document.createElement("span");
		category.className = "badge badge-category text-xs";
		category.textContent = reservation;
		const published = document.createElement("span");
		published.className = "badge badge-active";
		published.textContent = "Published";
		badges.append(category, published);

		const deadlineWrap = document.createElement("div");
		deadlineWrap.className = "flex items-center text-gray-600 gap-2 tender-deadline-wrap";
		const deadlineLabel = document.createElement("div");
		deadlineLabel.className = "text-xs text-gray-900 font-bold uppercase tracking-wide";
		deadlineLabel.textContent = "Submission Deadline:";
		const deadline = document.createElement("span");
		deadline.className = "font-bold text-sm text-green-600 mono";
		deadline.textContent = row.submission_deadline_label || "Not stated";
		deadlineWrap.append(deadlineLabel, deadline);
		top.append(badges, deadlineWrap);

		const title = document.createElement("h3");
		title.className = "text-xl font-bold mb-4 leading-tight tender-card-title";
		title.textContent = row.title || "Untitled Tender";

		const meta = document.createElement("div");
		meta.className = "flex flex-col lg:flex-row justify-between gap-4 tender-card-meta";
		const facts = document.createElement("div");
		facts.className = "flex flex-wrap gap-8 tender-card-facts";
		addFact(facts, "Procuring entity", row.procuring_entity);
		addFact(facts, "Method", row.method);
		addFact(facts, "Reservation", reservation);
		addFact(facts, "Reference", row.reference);

		const actions = document.createElement("div");
		actions.className = "tender-card-actions";
		const detailLink = document.createElement("a");
		const tenantRedirect =
			typeof row.redirect_url === "string" && row.redirect_url.trim()
				? row.redirect_url.trim()
				: typeof row.tenant_url === "string" && row.tenant_url.trim() && row.href
					? `${row.tenant_url.replace(/\/$/, "")}${row.href}`
					: row.reference
						? `/tenders/${encodeURIComponent(row.reference)}`
						: "/all-tenders";
		detailLink.href = tenantRedirect;
		detailLink.className = "btn-primary text-sm whitespace-nowrap";
		detailLink.append(document.createTextNode("View Details "));
		const arrow = document.createElement("i");
		arrow.className = "fas fa-arrow-right ml-2";
		arrow.setAttribute("aria-hidden", "true");
		detailLink.append(arrow);
		actions.append(detailLink);
		meta.append(facts, actions);
		content.append(top, title, meta);
		card.append(content);
		return card;
	}

	function setFiltersExpanded(expanded) {
		if (!filterPanel || !filterToggle) return;
		filterPanel.classList.toggle("expanded", expanded);
		filterPanel.classList.toggle("collapsed", !expanded);
		filterToggle.setAttribute("aria-expanded", expanded ? "true" : "false");
		filterToggle.querySelector(".toggle-text").textContent = expanded
			? "Hide Filters"
			: "Show Filters";
		filterToggle.querySelector("i").classList.toggle("fa-chevron-up", !expanded);
		filterToggle.querySelector("i").classList.toggle("fa-chevron-down", expanded);
		localStorage.setItem("allTendersFilterPanelCollapsedV2", expanded ? "false" : "true");
	}

	function updateOptions(select, options, fallback) {
		const selected = select.value;
		select.replaceChildren();
		(options || fallback).forEach((option) => {
			const element = document.createElement("option");
			element.value = option.value;
			element.textContent =
				select.id === "tender-reservation" && option.value.trim().toLowerCase() === "none"
					? "No reservation"
					: option.label;
			select.append(element);
		});
		select.value = [...select.options].some((option) => option.value === selected)
			? selected
			: "";
	}

	async function loadTenders() {
		const version = ++requestVersion;
		const params = new URLSearchParams({
			search: searchInput ? searchInput.value.trim() : "",
			method: methodSelect ? methodSelect.value : "",
			reservation: reservationSelect ? reservationSelect.value : "",
			closing: closingSelect ? closingSelect.value : "all",
		});

		errorNotice.hidden = true;
		state.hidden = false;
		state.textContent = "Loading tenders…";
		results.replaceChildren();

		try {
			const response = await fetch(`/api/method/${endpoint}?${params}`, {
				method: "GET",
				credentials: "same-origin",
				headers: { Accept: "application/json" },
			});
			const payload = await response.json();
			if (!response.ok || payload.exc || payload.exception || !payload.message) {
				throw new Error("Tender list request failed");
			}
			if (version !== requestVersion) return;

			const data = payload.message;
			const rows = Array.isArray(data.rows) ? data.rows : [];
			updateOptions(methodSelect, data.options?.method, [
				{ value: "", label: "All methods" },
			]);
			updateOptions(reservationSelect, data.options?.reservation, [
				{ value: "", label: "All categories" },
			]);
			count.textContent =
				data.count_text || (rows.length ? `${rows.length} tenders` : "No tenders found");
			if (!rows.length) {
				state.textContent = data.empty_text || "No tenders match these filters.";
				return;
			}

			state.hidden = true;
			const fragment = document.createDocumentFragment();
			rows.forEach((row) => fragment.append(renderTender(row)));
			results.append(fragment);
		} catch (_) {
			if (version !== requestVersion) return;
			state.hidden = true;
			errorNotice.hidden = false;
			count.textContent = "Tenders unavailable";
		}
	}

	form.addEventListener("submit", (event) => {
		event.preventDefault();
		clearTimeout(searchTimer);
		loadTenders();
	});
	if (searchInput)
		searchInput.addEventListener("input", () => {
			clearTimeout(searchTimer);
			searchTimer = setTimeout(loadTenders, 300);
		});
	[methodSelect, reservationSelect, closingSelect].forEach((select) => {
		if (select) select.addEventListener("change", loadTenders);
	});
	if (resetButton)
		resetButton.addEventListener("click", () => {
			searchInput.value = "";
			if (methodSelect) methodSelect.value = "";
			if (reservationSelect) reservationSelect.value = "";
			if (closingSelect) closingSelect.value = "all";
			loadTenders();
		});
	if (filterToggle)
		filterToggle.addEventListener("click", () => {
			setFiltersExpanded(filterPanel.classList.contains("collapsed"));
		});
	setFiltersExpanded(localStorage.getItem("allTendersFilterPanelCollapsedV2") === "false");
	if (retryButton) retryButton.addEventListener("click", loadTenders);
	window.addEventListener("pagehide", () => clearTimeout(searchTimer), { once: true });

	loadTenders();
})();
