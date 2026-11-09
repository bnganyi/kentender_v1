(() => {
	const METHOD = "frontend.api.user_profile.get_my_profile";
	let dialog;
	let profileData = null;
	let activeTab = "basic";

	const escapeHtml = (value) =>
		String(value ?? "").replace(/[&<>"']/g, (character) => ({
			"&": "&amp;",
			"<": "&lt;",
			">": "&gt;",
			'"': "&quot;",
			"'": "&#39;",
		})[character]);

	function formatDate(value) {
		if (!value) return __("Not available");
		const date = new Date(String(value).replace(" ", "T"));
		if (Number.isNaN(date.getTime())) return escapeHtml(value);
		return escapeHtml(new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date));
	}

	function field(label, value) {
		return `<div class="kt-profile-field"><dt>${__(label)}</dt><dd>${value ? escapeHtml(value) : `<span class="is-empty">${__("Not provided")}</span>`}</dd></div>`;
	}

	function activityMarkup(rows) {
		if (!rows.length) return `<p class="kt-profile-empty">${__("No activity recorded.")}</p>`;
		return `<ol class="kt-profile-events">${rows.map((row) => `
			<li>
				<span class="kt-profile-event-marker" aria-hidden="true"></span>
				<div class="kt-profile-event-copy"><strong>${escapeHtml(row.subject || row.operation || __("Activity"))}</strong><span>${escapeHtml(row.status || "")}${row.operation ? ` · ${escapeHtml(row.operation)}` : ""}</span></div>
				<time>${formatDate(row.communication_date)}</time>
			</li>`).join("")}</ol>`;
	}

	function sessionMarkup(data) {
		const sessions = data.sessions || [];
		const history = data.session_history || [];
		const active = sessions.length
			? `<div class="kt-profile-subsection"><h3>${__("Active sessions")}</h3><div class="kt-profile-table-wrap"><table><thead><tr><th>${__("Device")}</th><th>${__("IP address")}</th><th>${__("Started")}</th><th>${__("Last active")}</th><th>${__("State")}</th></tr></thead><tbody>${sessions.map((session) => `<tr><td>${escapeHtml(session.user_agent || __("Unknown device"))}<div class="kt-profile-secondary">${escapeHtml(session.id || "")}</div></td><td>${escapeHtml(session.ip_address || __("Not available"))}</td><td>${formatDate(session.session_created)}</td><td>${formatDate(session.last_updated)}</td><td>${session.is_current ? __("Current") : __("Active")}</td></tr>`).join("")}</tbody></table></div></div>`
			: `<div class="kt-profile-subsection"><h3>${__("Active sessions")}</h3><p class="kt-profile-empty">${__("No active sessions found.")}</p></div>`;
		const events = history.length
			? `<ol class="kt-profile-events">${history.map((row) => `<li><span class="kt-profile-event-marker" aria-hidden="true"></span><div class="kt-profile-event-copy"><strong>${escapeHtml(row.operation || row.subject || __("Session event"))}</strong><span>${escapeHtml(row.status || row.subject || "")}${row.ip_address ? ` · ${escapeHtml(row.ip_address)}` : ""}</span></div><time>${formatDate(row.communication_date)}</time></li>`).join("")}</ol>`
			: `<p class="kt-profile-empty">${__("No session history recorded.")}</p>`;
		return `${active}<div class="kt-profile-subsection"><h3>${__("Sign-in history")}</h3>${events}</div>`;
	}

	function render() {
		const root = dialog.fields_dict.profile.$wrapper[0];
		if (!profileData) {
			root.innerHTML = `<div class="kt-profile-loading" role="status">${__("Loading profile…")}</div>`;
			return;
		}
		const { profile, activity, session_history: sessionHistory, sessions } = profileData;
		const displayName = profile.full_name || profile.email || __("User");
		const initials = displayName.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
		const image = profile.user_image && (profile.user_image.startsWith("/") || profile.user_image.startsWith("https://"))
			? `<img src="${escapeHtml(profile.user_image)}" alt="">`
			: `<span aria-hidden="true">${escapeHtml(initials)}</span>`;
		const tabs = [
			["basic", __("Basic info")],
			["activity", __("Activity log")],
			["sessions", __("User Session History")],
		];
		let content = "";
		if (activeTab === "basic") {
			content = `<div class="kt-profile-layout">
				<section class="kt-profile-card"><h3>${__("Personal information")}</h3><dl class="kt-profile-fields">${field("Full name", profile.full_name)}${field("Email", profile.email)}${field("Username", profile.username)}${field("Phone", profile.phone)}${field("Mobile", profile.mobile_no)}${field("Location", profile.location)}</dl></section>
				<section class="kt-profile-card"><h3>${__("Account details")}</h3><dl class="kt-profile-fields">${field("First name", profile.first_name)}${field("Middle name", profile.middle_name)}${field("Last name", profile.last_name)}${field("Language", profile.language)}${field("Time zone", profile.time_zone)}${field("Last login", formatDate(profile.last_login))}${field("Last active", formatDate(profile.last_active))}</dl></section>
			</div>`;
		} else if (activeTab === "activity") {
			const lastActivity = activity?.[0]?.communication_date;
			content = `<div class="kt-profile-layout">
				<aside class="kt-profile-card kt-profile-overview"><h3>${__("Activity overview")}</h3><dl class="kt-profile-fields">${field("Events shown", (activity || []).length)}${field("Most recent activity", lastActivity ? formatDate(lastActivity) : "")}</dl></aside>
				<section class="kt-profile-card"><h3>${__("Activity log")}</h3>${activityMarkup(activity || [])}</section>
			</div>`;
		} else {
			content = `<div class="kt-profile-layout">
				<aside class="kt-profile-card kt-profile-overview"><h3>${__("Session overview")}</h3><dl class="kt-profile-fields">${field("Active sessions", (sessions || []).length)}${field("Sign-in events", (sessionHistory || []).length)}</dl></aside>
				<section class="kt-profile-card">${sessionMarkup({ sessions: sessions || [], session_history: sessionHistory || [] })}</section>
			</div>`;
		}
		root.innerHTML = `<div class="kt-user-profile">
			<div class="kt-profile-cover" aria-hidden="true"></div>
			<header class="kt-profile-summary"><div class="kt-profile-avatar">${image}</div><div class="kt-profile-identity"><h2>${escapeHtml(displayName)}</h2><p>${escapeHtml(profile.email || "")}</p></div><div class="kt-profile-summary-stats"><div><strong>${(sessions || []).length}</strong><span>${__("Active sessions")}</span></div><div><strong>${(activity || []).length}</strong><span>${__("Activity events")}</span></div></div></header>
			<div class="kt-profile-tabs" role="tablist" aria-label="${__("User Profile sections")}">${tabs.map(([key, label]) => `<button type="button" role="tab" data-profile-tab="${key}" aria-selected="${activeTab === key}">${label}</button>`).join("")}</div>
			<section class="kt-profile-content" role="tabpanel">${content}</section>
		</div>`;
	}

	function ensureDialog() {
		if (dialog) return;
		dialog = new frappe.ui.Dialog({
			title: __("User Profile"),
			size: "large",
			fields: [{ fieldname: "profile", fieldtype: "HTML" }],
			primary_action_label: __("Close"),
			primary_action: () => dialog.hide(),
		});
		dialog.$wrapper.addClass("kt-user-profile-modal");
		dialog.$wrapper.on("click", "[data-profile-tab]", (event) => {
			activeTab = event.currentTarget.dataset.profileTab;
			render();
		});
	}

	async function openProfile() {
		ensureDialog();
		activeTab = "basic";
		profileData = null;
		render();
		dialog.show();
		try {
			const response = await frappe.call({ method: METHOD });
			profileData = response.message;
		} catch (_) {
			profileData = { error: true };
		}
		if (profileData?.error) {
			dialog.fields_dict.profile.$wrapper.html(`<p class="kt-profile-error" role="alert">${__("We could not load your profile. Please try again.")}</p>`);
		} else {
			render();
		}
	}
	document.addEventListener("kt-user-profile-open", openProfile);

	document.addEventListener("click", (event) => {
		const target = event.target instanceof Element ? event.target : event.target?.parentElement;
		const trigger = target?.closest(".sidebar-user-button");
		if (!trigger) return;
		event.preventDefault();
		event.stopImmediatePropagation();
		openProfile();
	}, true);
})();
