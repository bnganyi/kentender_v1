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
	const detailModal = document.getElementById("tender-detail-modal");
	const detailTitle = document.getElementById("tender-detail-title");
	const detailDescription = document.getElementById("tender-detail-description");
	const detailStatus = document.getElementById("tender-detail-status");
	const detailActions = document.getElementById("tender-detail-actions");
	const detailContent = document.getElementById("tender-detail-content");
	let detailRequestVersion = 0;
	let detailTrigger = null;
	const endpoint = "kentender_procurement.bid_submission.api.get_available_tenders";
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
		const detailLink = document.createElement("button");
		detailLink.type = "button";
		detailLink.dataset.tenderDetail = row.reference || "";
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

	function makeSection(title) {
		const section = document.createElement("section");
		section.className = "tender-modal-section";
		const heading = document.createElement("h3");
		heading.textContent = title;
		section.append(heading);
		return section;
	}

	function makeFacts(items) {
		const grid = document.createElement("div");
		grid.className = "tender-modal-facts";
		items.forEach(([label, value]) => {
			if (!value) return;
			const fact = document.createElement("div");
			const factLabel = document.createElement("span");
			factLabel.className = "tender-modal-fact-label";
			factLabel.textContent = label;
			const factValue = document.createElement("span");
			factValue.className = "tender-modal-fact-value";
			factValue.textContent = value;
			fact.append(factLabel, factValue);
			grid.append(fact);
		});
		return grid;
	}

	function addInternalLink(container, href, label, newTab = false) {
		if (!href) return;
		const url = new URL(href, window.location.origin);
		if (
			url.origin !== window.location.origin ||
			(!url.pathname.startsWith("/api/method/") && !url.pathname.startsWith("/tenders/"))
		)
			return;
		const link = document.createElement("a");
		link.href = `${url.pathname}${url.search}${url.hash}`;
		link.textContent = label;
		if (newTab) {
			link.target = "_blank";
			link.rel = "noopener";
		}
		container.append(link);
	}

	function addNotice(title, text, kind) {
		if (!title && !text) return;
		const notice = document.createElement("section");
		notice.className = `tender-modal-section tender-modal-notice ${kind || ""}`;
		if (title) {
			const heading = document.createElement("h3");
			heading.textContent = title;
			notice.append(heading);
		}
		const body = document.createElement("p");
		body.textContent = text || "";
		notice.append(body);
		detailContent.append(notice);
	}

	function renderOverview(data) {
		const tender = data.tender || {};
		const facts = data.facts || {};
		detailTitle.textContent = tender.title || tender.reference || "Tender details";
		detailDescription.textContent = `${tender.reference || ""}${tender.description ? ` · ${tender.description}` : ""}`;
		detailStatus.hidden = !tender.status_label;
		detailStatus.textContent = tender.status_label || "";
		detailActions.replaceChildren();
		const guestActionLabels = {
			sign_in: "Sign in to start bid",
			create_login: "New supplier? Create a login",
		};
		(data.actions || []).forEach((action) => {
			const label = guestActionLabels[action.kind];
			if (!label || !action.href) return;
			const actionUrl = new URL(action.href, window.location.origin);
			if (actionUrl.origin !== window.location.origin || actionUrl.pathname !== "/login")
				return;
			const link = document.createElement("a");
			link.href = `${actionUrl.pathname}${actionUrl.search}${actionUrl.hash}`;
			link.className = action.kind === "sign_in" ? "btn-primary" : "btn-secondary";
			link.textContent = label;
			detailActions.append(link);
		});
		detailActions.hidden = !detailActions.children.length;
		detailContent.replaceChildren();

		if (data.notice) addNotice(data.notice.title, data.notice.text, "is-info");
		if (data.release_notice)
			addNotice("Tender format notice", data.release_notice.text, "is-warning");

		const dates = makeSection("Key dates");
		dates.append(
			makeFacts([
				["Submissions close", tender.deadline],
				[
					tender.clarification_label || "Clarification deadline",
					tender.clarification_deadline,
				],
				["Published", tender.published],
			]),
		);
		(data.related_links || []).forEach((item) => {
			const related = document.createElement("div");
			const relatedLabel = document.createElement("span");
			relatedLabel.className = "tender-modal-fact-label";
			relatedLabel.textContent = item.label || "Related information";
			const relatedLinks = document.createElement("div");
			relatedLinks.className = "tender-modal-links";
			addInternalLink(
				relatedLinks,
				item.href,
				`${item.value || "Details"}${item.text ? ` · ${item.text}` : ""}`,
			);
			related.append(relatedLabel, relatedLinks);
			dates.append(related);
		});
		if (data.cancellation?.cancelled)
			dates.append(makeFacts([["Cancelled", data.cancellation.cancelled]]));
		detailContent.append(dates);

		const noticeAction = (data.actions || []).find((action) => action.kind === "view_notice");
		if (noticeAction) {
			const notice = makeSection("Cancellation notice");
			const links = document.createElement("div");
			links.className = "tender-modal-links";
			addInternalLink(links, noticeAction.href, noticeAction.label || "View notice", true);
			notice.append(links);
			detailContent.append(notice);
		}

		const procurement = makeSection("What is being procured");
		procurement.append(
			makeFacts([
				["Quantity", facts.quantity],
				["Delivery location", facts.delivery_location],
				["Latest delivery", facts.latest_delivery],
				["Currency", facts.currency],
				["Tender security", facts.tender_security],
				["Security method", facts.tender_security_how],
				["Bid validity", facts.bid_validity],
			]),
		);
		detailContent.append(procurement);

		const documents = makeSection("Tender documents");
		const documentList = document.createElement("ul");
		documentList.className = "tender-modal-list";
		(data.documents || []).forEach((documentInfo) => {
			const item = document.createElement("li");
			item.className = "tender-modal-list-item tender-modal-document";
			const name = document.createElement("span");
			name.className = "tender-modal-list-title";
			name.textContent = documentInfo.label || "Tender document";
			const published = document.createElement("span");
			published.className = "tender-modal-list-meta";
			published.textContent = documentInfo.published
				? `Published ${documentInfo.published}`
				: "";
			const links = document.createElement("div");
			links.className = "tender-modal-links";
			addInternalLink(links, documentInfo.view_href, "View", true);
			addInternalLink(links, documentInfo.download_href, "Download");
			item.append(name, published, links);
			documentList.append(item);
		});
		if (!documentList.children.length) {
			const empty = document.createElement("p");
			empty.textContent = "No Tender documents are available.";
			documents.append(empty);
		} else {
			documents.append(documentList);
		}
		detailContent.append(documents);

		const clarifications = makeSection("Addenda and clarification answers");
		const clarificationList = document.createElement("ul");
		clarificationList.className = "tender-modal-list";
		(data.addenda || []).forEach((addendum) => {
			const item = document.createElement("li");
			item.className = "tender-modal-list-item";
			const heading = document.createElement("span");
			heading.className = "tender-modal-list-title";
			heading.textContent = `${addendum.reference || "Addendum"}${addendum.summary ? ` · ${addendum.summary}` : ""}`;
			const meta = document.createElement("span");
			meta.className = "tender-modal-list-meta";
			meta.textContent = `Issued ${addendum.issued || ""}${addendum.current_deadline ? ` · Current deadline ${addendum.current_deadline}` : ""}`;
			const links = document.createElement("div");
			links.className = "tender-modal-links";
			addInternalLink(links, addendum.view_href, "View addendum", true);
			item.append(heading, meta, links);
			clarificationList.append(item);
		});
		(data.answers || []).forEach((answer) => {
			const item = document.createElement("li");
			item.className = "tender-modal-list-item tender-modal-answer";
			const meta = document.createElement("span");
			meta.className = "tender-modal-list-meta";
			meta.textContent = answer.answered
				? `Answered ${answer.answered}`
				: "Published answer";
			const question = document.createElement("strong");
			question.textContent = answer.question || "Clarification";
			const answerText = document.createElement("span");
			answerText.textContent = answer.answer || "";
			item.append(meta, question, answerText);
			clarificationList.append(item);
		});
		if (!clarificationList.children.length) {
			const empty = document.createElement("p");
			empty.textContent = "No addenda or clarification answers have been published.";
			clarifications.append(empty);
		} else {
			clarifications.append(clarificationList);
		}
		if (data.clarification?.closed_text) {
			const closed = document.createElement("p");
			closed.className = "tender-modal-list-meta";
			closed.textContent = data.clarification.closed_text;
			clarifications.append(closed);
		}
		detailContent.append(clarifications);

		if (Array.isArray(data.before_you_start) && data.before_you_start.length) {
			const beforeStart = makeSection("Before you start");
			const list = document.createElement("ul");
			list.className = "tender-modal-list";
			data.before_you_start.forEach((line) => {
				const item = document.createElement("li");
				item.textContent = line;
				list.append(item);
			});
			beforeStart.append(list);
			detailContent.append(beforeStart);
		}
	}

	async function openTenderDetails(reference, trigger) {
		const version = ++detailRequestVersion;
		detailTrigger = trigger;
		detailTitle.textContent = "Tender details";
		detailDescription.textContent = reference;
		detailStatus.hidden = true;
		detailActions.replaceChildren();
		detailActions.hidden = true;
		detailContent.replaceChildren();
		const loading = document.createElement("p");
		loading.textContent = "Loading Tender details…";
		detailContent.append(loading);
		detailModal.showModal();

		try {
			const params = new URLSearchParams({ tender_reference: reference });
			const response = await fetch(
				`/api/method/kentender_procurement.bid_submission.api.get_tender_overview?${params}`,
				{
					method: "GET",
					credentials: "same-origin",
					headers: { Accept: "application/json" },
				},
			);
			const payload = await response.json();
			if (!response.ok || payload.exc || payload.exception || !payload.message) {
				throw new Error("Unable to load Tender details.");
			}
			if (version !== detailRequestVersion) return;
			if (payload.message.outcome === "NOT_FOUND") {
				throw new Error(payload.message.text || "This Tender is unavailable.");
			}
			renderOverview(payload.message);
		} catch (error) {
			if (version !== detailRequestVersion) return;
			const message = document.createElement("p");
			message.setAttribute("role", "alert");
			message.textContent = error.message || "Unable to load Tender details.";
			detailContent.replaceChildren(message);
		}
	}

	function setFiltersExpanded(expanded) {
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
			search: searchInput.value.trim(),
			method: methodSelect.value,
			reservation: reservationSelect.value,
			closing: closingSelect.value,
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
	searchInput.addEventListener("input", () => {
		clearTimeout(searchTimer);
		searchTimer = setTimeout(loadTenders, 300);
	});
	[methodSelect, reservationSelect, closingSelect].forEach((select) =>
		select.addEventListener("change", loadTenders),
	);
	resetButton.addEventListener("click", () => {
		searchInput.value = "";
		methodSelect.value = "";
		reservationSelect.value = "";
		closingSelect.value = "all";
		loadTenders();
	});
	filterToggle.addEventListener("click", () => {
		setFiltersExpanded(filterPanel.classList.contains("collapsed"));
	});
	setFiltersExpanded(localStorage.getItem("allTendersFilterPanelCollapsedV2") === "false");
	retryButton.addEventListener("click", loadTenders);
	results.addEventListener("click", (event) => {
		const trigger = event.target.closest("[data-tender-detail]");
		if (!trigger) return;
		openTenderDetails(trigger.dataset.tenderDetail, trigger);
	});
	document
		.getElementById("tender-modal-close")
		.addEventListener("click", () => detailModal.close());
	detailModal.addEventListener("click", (event) => {
		if (event.target === detailModal) detailModal.close();
	});
	detailModal.addEventListener("close", () => {
		detailRequestVersion += 1;
		detailTrigger?.focus();
	});
	window.addEventListener("pagehide", () => clearTimeout(searchTimer), { once: true });

	loadTenders();
})();
