<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";

// CFG-PEFY-DES-12 — shared top page rail, rendered inside the Vue root (.kt-industry
// scope) rather than reusing kentender_core.cl_shell's Civic Ledger toolbar, which is
// a different design system (Tailwind/Material Symbols) — kt_industry_tokens.css is
// explicitly scoped to never leak into Desk chrome, and the inverse holds too: this
// rail never leaks into Desk chrome either, it only exists inside the Vue mount root.

const props = defineProps({
	trail: { type: Array, required: true }, // [{label, route?}] — last item has no route (current)
	epoch: { type: Number, default: 0 }, // bump to re-fetch (handle.refreshContext)
});

// CTX-CHG-001 v1.1 §2: there is no Procuring Entity switcher. A site is one Procuring Entity, shown where useful
// and never chosen; the global working-entity preference and its picker are retired.

// Mirrors kt_cl_components.js's sessionUserLabel/sessionUserRole — same source data,
// kept local so this Industry-scoped component has no dependency on Civic Ledger.
function sessionUserLabel() {
	try {
		return (frappe.session && frappe.session.user_fullname) || frappe.session.user || "User";
	} catch (e) {
		return "User";
	}
}

function sessionUserRole() {
	try {
		const roles = (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
		const skip = { Administrator: 1, Guest: 1, All: 1, "System Manager": 1, "Desk User": 1 };
		for (const role of roles) {
			if (!skip[role]) return role;
		}
		return roles[0] || "";
	} catch (e) {
		return "";
	}
}

const userName = sessionUserLabel();
const userRole = sessionUserRole();
const menuOpen = ref(false);
const allNotificationsOpen = ref(false);
const allNotificationsFilter = ref("all");
const allNotifications = ref([]);
const allNotificationsLoading = ref(false);
const allNotificationsLoadingMore = ref(false);
const allNotificationsError = ref("");
const allNotificationsHasMore = ref(false);
const markingAllNotificationsRead = ref(false);
const unreadNotificationCount = ref(0);
const userMenu = ref(null);
const searchTrigger = ref(null);
const notificationWrapper = ref(null);
const searchEnabled = computed(() => !!frappe.boot?.desk_settings?.search_bar);
const notificationsEnabled = computed(
	() => !!frappe.boot?.desk_settings?.notifications && frappe.session?.user !== "Guest",
);

function closeMenu() {
	menuOpen.value = false;
}

function openSearch() {
	const deskSearchTrigger = document.querySelector("#navbar-modal-search");
	if (deskSearchTrigger) {
		deskSearchTrigger.click();
		return;
	}
	searchTrigger.value?.click();
}

function toggleNotifications() {
	if (allNotificationsOpen.value) {
		closeAllNotifications();
		return;
	}
	openAllNotifications();
}

async function refreshUnreadNotificationCount() {
	if (!notificationsEnabled.value) {
		unreadNotificationCount.value = 0;
		return;
	}
	try {
		const response = await frappe.call({
			method: "frappe.client.get_count",
			args: {
				doctype: "Notification Log",
				filters: {
					for_user: frappe.session.user,
					read: 0,
				},
			},
		});
		unreadNotificationCount.value = Number(response.message) || 0;
	} catch (error) {
		unreadNotificationCount.value = 0;
	}
}

function onNewNotification() {
	refreshUnreadNotificationCount();
	if (allNotificationsOpen.value) loadAllNotifications(true);
}

function onNotificationIndicatorHide() {
	refreshUnreadNotificationCount();
}

const NOTIFICATION_PAGE_SIZE = 25;

async function loadAllNotifications(reset = false) {
	if (allNotificationsLoading.value) return;
	allNotificationsLoading.value = true;
	if (reset) {
		allNotifications.value = [];
		allNotificationsError.value = "";
	}
	try {
		const response = await frappe.call({
			method: "frappe.desk.doctype.notification_log.notification_log.get_notification_logs",
			args: {
				limit: NOTIFICATION_PAGE_SIZE + 1,
				start: reset ? 0 : allNotifications.value.length,
				unread: allNotificationsFilter.value === "unread",
			},
		});
		const rows = response.message?.notification_logs || [];
		allNotificationsHasMore.value = rows.length > NOTIFICATION_PAGE_SIZE;
		const page = rows.slice(0, NOTIFICATION_PAGE_SIZE);
		allNotifications.value = reset ? page : allNotifications.value.concat(page);
	} catch (_) {
		allNotificationsError.value = __("Notifications could not be loaded.");
	} finally {
		allNotificationsLoading.value = false;
		allNotificationsLoadingMore.value = false;
	}
}

function openAllNotifications() {
	menuOpen.value = false;
	allNotificationsFilter.value = "all";
	allNotificationsOpen.value = true;
	refreshUnreadNotificationCount();
	loadAllNotifications(true);
}

async function openNotificationSettings() {
	closeAllNotifications();
	menuOpen.value = false;
	try {
		const response = await frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Notification Settings",
				name: frappe.session.user,
			},
		});
		const settings = response.message;
		await frappe.model.with_doctype("Notification Subscribed Document");
		const dialog = new frappe.ui.Dialog({
			title: __("Notification Settings"),
			size: "large",
			fields: [
				{
					fieldtype: "Check",
					fieldname: "enabled",
					label: __("Enable System Notification"),
				},
				{
					fieldtype: "Table MultiSelect",
					fieldname: "subscribed_documents",
					label: __("Open Documents"),
					options: "Notification Subscribed Document",
				},
				{ fieldtype: "Section Break", label: __("Email Settings") },
				{
					fieldtype: "Check",
					fieldname: "enable_email_notifications",
					label: __("Enable Email Notifications"),
				},
				{
					fieldtype: "Check",
					fieldname: "enable_email_mention",
					label: __("Mentions"),
					depends_on: "eval:doc.enable_email_notifications",
				},
				{
					fieldtype: "Check",
					fieldname: "enable_email_assignment",
					label: __("Assignments"),
					depends_on: "eval:doc.enable_email_notifications",
				},
				{
					fieldtype: "Check",
					fieldname: "enable_email_share",
					label: __("Document Share"),
					depends_on: "eval:doc.enable_email_notifications",
				},
				{
					fieldtype: "Check",
					fieldname: "enable_email_event_reminders",
					label: __("Event Reminders"),
					depends_on: "eval:doc.enable_email_notifications",
				},
				{
					fieldtype: "Check",
					fieldname: "enable_email_threads_on_assigned_document",
					label: __("Email Threads on Assigned Document"),
					description: __(
						"Get notified when an email is received on any of the documents assigned to you.",
					),
					depends_on: "eval:doc.enable_email_notifications",
				},
			],
			primary_action_label: __("Save"),
			primary_action: async (values) => {
				const existingRows = new Map(
					(settings.subscribed_documents || []).map((row) => [row.document, row]),
				);
				const updatedSettings = {
					...settings,
					...values,
					subscribed_documents: (values.subscribed_documents || []).map((row) => {
						const document = typeof row === "string" ? row : row.document;
						return existingRows.get(document) || { document };
					}),
				};
				try {
					await frappe.call({
						method: "frappe.client.save",
						args: { doc: updatedSettings },
						freeze: true,
					});
					frappe.boot.notification_settings = updatedSettings;
					dialog.hide();
					frappe.show_alert({
						message: __("Notification settings saved"),
						indicator: "green",
					});
				} catch (error) {
					frappe.msgprint(error.message || __("Could not save notification settings."));
				}
			},
		});
		dialog.set_values(settings);
		dialog.show();
	} catch (error) {
		frappe.msgprint(error.message || __("Could not load notification settings."));
	}
}

function closeAllNotifications() {
	allNotificationsOpen.value = false;
}

function filterAllNotifications(filter) {
	if (allNotificationsFilter.value === filter) return;
	allNotificationsFilter.value = filter;
	loadAllNotifications(true);
}

function loadMoreNotifications() {
	if (!allNotificationsLoading.value && allNotificationsHasMore.value) {
		allNotificationsLoadingMore.value = true;
		loadAllNotifications();
	}
}

async function markAllNotificationsRead() {
	if (markingAllNotificationsRead.value) return;
	markingAllNotificationsRead.value = true;
	try {
		await frappe.call(
			"frappe.desk.doctype.notification_log.notification_log.mark_all_as_read",
		);
		allNotifications.value =
			allNotificationsFilter.value === "unread"
				? []
				: allNotifications.value.map((item) => ({ ...item, read: 1 }));
		await refreshUnreadNotificationCount();
	} catch (_) {
		allNotificationsError.value = __("Notifications could not be updated.");
	} finally {
		markingAllNotificationsRead.value = false;
	}
}

function notificationSubject(notification) {
	const subject = notification.subject || __("Notification");
	return frappe.utils?.strip_html
		? frappe.utils.strip_html(subject)
		: String(subject).replace(/<[^>]*>/g, "");
}

function notificationTime(value) {
	return value ? frappe.datetime.comment_when(value) : "";
}

function notificationHref(notification) {
	if (notification.link) return notification.link;
	const doctype = notification.document_type || "Notification Log";
	const name = notification.document_name || notification.name;
	return frappe.utils.get_form_link(doctype, name);
}

async function openNotification(notification) {
	closeAllNotifications();
	if (!notification.read) {
		frappe.call("frappe.desk.doctype.notification_log.notification_log.mark_as_read", {
			docname: notification.name,
		});
	}
	const href = notificationHref(notification);
	if (href) window.location.href = href;
}

function handleClickOutside(event) {
	if (userMenu.value && !userMenu.value.contains(event.target)) {
		closeMenu();
	}
}

onMounted(() => {
	document.addEventListener("click", handleClickOutside);
	if (searchEnabled.value && frappe.search?.AwesomeBar && searchTrigger.value) {
		const deskSearchTrigger = document.querySelector("#navbar-modal-search");
		if (deskSearchTrigger) {
			deskSearchTrigger.classList.add("hidden");
		} else {
			new frappe.search.AwesomeBar().setup(searchTrigger.value);
		}
	}
	if (notificationsEnabled.value && notificationWrapper.value) {
		document.querySelector(".body-sidebar .sidebar-notification")?.classList.add("hidden");
		refreshUnreadNotificationCount();
		frappe.realtime?.on("notification", onNewNotification);
		frappe.realtime?.on("indicator_hide", onNotificationIndicatorHide);
	}
	$(document).on("page-change.ktIndustryRail", closeAllNotifications);
});

onBeforeUnmount(() => {
	document.removeEventListener("click", handleClickOutside);
	$(document).off("page-change.ktIndustryRail", closeAllNotifications);
	frappe.realtime?.off?.("notification", onNewNotification);
	frappe.realtime?.off?.("indicator_hide", onNotificationIndicatorHide);
});

function toggleMenu() {
	menuOpen.value = !menuOpen.value;
	if (menuOpen.value) closeAllNotifications();
}

function goRoute(route) {
	if (!route) return;
	// The contract is a segments array, applied as set_route arguments. A
	// string path must not fall into apply(), which would spread it into
	// single characters and navigate nowhere (the Needs breadcrumb defect).
	if (typeof route === "string") {
		frappe.set_route(route);
		return;
	}
	frappe.set_route.apply(frappe, route);
}

function openProfile() {
	closeMenu();
	document.dispatchEvent(new Event("kt-user-profile-open"));
}

function logout() {
	closeMenu();
	if (typeof frappe.logout === "function") {
		frappe.logout();
		return;
	}
	if (frappe.app && typeof frappe.app.logout === "function") {
		frappe.app.logout();
		return;
	}
	window.location.href = "/login";
}
</script>

<template>
	<header class="kt-rail">
		<nav class="kt-rail-crumbs" aria-label="Breadcrumb">
			<template v-for="(item, i) in trail" :key="i">
				<a
					v-if="item.route"
					href="#"
					class="kt-rail-crumb-link"
					@click.prevent="goRoute(item.route)"
					>{{ item.label }}</a
				>
				<span v-else class="kt-rail-crumb-current" aria-current="page">{{
					item.label
				}}</span>
				<span v-if="i < trail.length - 1" class="kt-rail-sep">/</span>
			</template>
		</nav>
		<div class="kt-rail-actions">
			<button
				v-if="searchEnabled"
				ref="searchTrigger"
				type="button"
				id="kt-rail-awesomebar-search"
				class="kt-rail-btn kt-rail-search navbar-search-bar"
				:aria-label="__('Search')"
				title="Search (Ctrl+K)"
				@click="openSearch"
			>
				<svg
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.8"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<circle cx="11" cy="11" r="6"></circle>
					<path d="m16 16 5 5"></path>
				</svg>
			</button>
			<div
				v-if="notificationsEnabled"
				ref="notificationWrapper"
				class="standard-items-sections kt-rail-notification-host"
			>
				<button
					type="button"
					class="kt-rail-btn kt-rail-notifications sidebar-notification"
					:aria-label="__('Notifications')"
					:aria-expanded="allNotificationsOpen"
					@click.stop="toggleNotifications"
				>
					<span class="notifications-icon">
						<svg
							class="notifications-seen"
							width="20"
							height="20"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M10.268 21a2 2 0 0 0 3.464 0"></path>
							<path
								d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"
							></path>
						</svg>
						<svg
							class="notifications-unseen"
							width="20"
							height="20"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M10.268 21a2 2 0 0 0 3.464 0"></path>
							<path
								d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"
							></path>
						</svg>
					</span>
					<span
						v-if="unreadNotificationCount > 0"
						class="kt-rail-notification-count"
						:aria-label="`${unreadNotificationCount} unread notifications`"
						:title="`${unreadNotificationCount} unread notifications`"
					>
						{{ unreadNotificationCount > 99 ? "99+" : unreadNotificationCount }}
					</span>
				</button>
			</div>
		</div>
		<div class="kt-rail-div"></div>
		<div ref="userMenu" class="kt-rail-user-wrap">
			<button
				type="button"
				class="kt-rail-user"
				:aria-expanded="menuOpen"
				@click.stop="toggleMenu"
			>
				<span class="kt-rail-user-text">
					<span class="kt-rail-user-name">{{ userName }}</span>
					<span v-if="userRole" class="kt-rail-user-role">{{ userRole }}</span>
				</span>
				<svg
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="kt-rail-chevron"
				>
					<path d="m6 9 6 6 6-6"></path>
				</svg>
			</button>

			<div v-if="menuOpen" class="kt-rail-user-menu" role="menu" aria-label="User menu">
				<button
					type="button"
					class="kt-rail-user-menu-item"
					role="menuitem"
					@click="openProfile"
				>
					<svg viewBox="0 0 24 24" aria-hidden="true" class="kt-rail-user-menu-icon">
						<path d="M20 21a8 8 0 0 0-16 0"></path>
						<circle cx="12" cy="7" r="4"></circle>
					</svg>
					<span>{{ __("Profile") }}</span>
				</button>
				<button
					type="button"
					class="kt-rail-user-menu-item danger"
					role="menuitem"
					@click="logout"
				>
					<svg viewBox="0 0 24 24" aria-hidden="true" class="kt-rail-user-menu-icon">
						<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
						<path d="M16 17l5-5-5-5"></path>
						<path d="M21 12H9"></path>
					</svg>
					<span>{{ __("Logout") }}</span>
				</button>
			</div>
		</div>
	</header>
	<Teleport to="body">
		<div
			v-if="allNotificationsOpen"
			class="kt-all-notifications-backdrop"
			@click.self="closeAllNotifications"
			@keydown.esc="closeAllNotifications"
		>
			<section
				class="kt-all-notifications-modal"
				role="dialog"
				aria-modal="true"
				aria-labelledby="kt-all-notifications-title"
			>
				<header class="kt-all-notifications-header">
					<h2 id="kt-all-notifications-title">{{ __("Notifications") }}</h2>
					<div class="kt-all-notifications-header-actions">
						<button
							type="button"
							class="kt-all-notifications-settings"
							@click="openNotificationSettings"
						>
							{{ __("Settings") }}
						</button>
						<button
							type="button"
							class="kt-all-notifications-mark-read"
							:disabled="
								markingAllNotificationsRead || unreadNotificationCount === 0
							"
							@click="markAllNotificationsRead"
						>
							<span aria-hidden="true">✓</span>
							{{
								markingAllNotificationsRead
									? __("Marking…")
									: __("Mark all as read")
							}}
						</button>
					</div>
				</header>
				<div class="kt-all-notifications-toolbar">
					<div
						class="kt-all-notifications-filters"
						role="group"
						:aria-label="__('Filter notifications')"
					>
						<button
							type="button"
							:class="{ 'is-active': allNotificationsFilter === 'all' }"
							:aria-pressed="allNotificationsFilter === 'all'"
							@click="filterAllNotifications('all')"
						>
							{{ __("All") }}
						</button>
						<button
							type="button"
							:class="{ 'is-active': allNotificationsFilter === 'unread' }"
							:aria-pressed="allNotificationsFilter === 'unread'"
							@click="filterAllNotifications('unread')"
						>
							{{ __("Unread") }}
							<span
								v-if="unreadNotificationCount > 0"
								class="kt-all-notifications-pill"
								:title="`${unreadNotificationCount} unread notifications`"
							>
								{{
									unreadNotificationCount > 99 ? "99+" : unreadNotificationCount
								}}
							</span>
						</button>
					</div>
				</div>
				<div class="kt-all-notifications-list" aria-live="polite">
					<p
						v-if="allNotificationsLoading && !allNotifications.length"
						class="kt-all-notifications-state"
						role="status"
					>
						{{ __("Loading notifications…") }}
					</p>
					<p
						v-else-if="allNotificationsError"
						class="kt-all-notifications-state"
						role="alert"
					>
						{{ allNotificationsError }}
					</p>
					<p v-else-if="!allNotifications.length" class="kt-all-notifications-state">
						{{
							allNotificationsFilter === "unread"
								? __("You are all caught up.")
								: __("No notifications yet.")
						}}
					</p>
					<a
						v-for="notification in allNotifications"
						:key="notification.name"
						class="kt-all-notification-row"
						:class="{ 'is-unread': !notification.read }"
						:href="notificationHref(notification)"
						@click.prevent="openNotification(notification)"
					>
						<span class="kt-all-notification-avatar" aria-hidden="true">{{
							(notification.from_user || "K").charAt(0).toUpperCase()
						}}</span>
						<span class="kt-all-notification-content">
							<strong>{{ notification.from_user || __("KenTender") }}</strong>
							<span>{{ notificationSubject(notification) }}</span>
							<time>{{ notificationTime(notification.creation) }}</time>
						</span>
						<span class="kt-all-notification-side">
							<span class="kt-all-notification-marker" aria-hidden="true"></span>
							<time>{{ notificationTime(notification.creation) }}</time>
						</span>
					</a>
					<button
						v-if="allNotificationsHasMore"
						type="button"
						class="kt-all-notifications-more"
						:disabled="allNotificationsLoadingMore"
						@click="loadMoreNotifications"
					>
						{{ allNotificationsLoadingMore ? __("Loading…") : __("Load more") }}
					</button>
				</div>
			</section>
		</div>
	</Teleport>
</template>

<style scoped>
.kt-rail {
	border-top: 3px solid #0b1f3b;
	display: flex;
	align-items: center;
	gap: 24px;
	height: 64px;
	flex: none;
	padding: 0 32px;
	border-bottom: 1px solid rgba(0, 102, 255, 0.1);
	background: rgba(255, 255, 255, 0.97);
	backdrop-filter: blur(20px);
	position: sticky;
	top: 0;
	z-index: 20;
}
.kt-rail-crumbs {
	display: flex;
	align-items: center;
	gap: 10px;
	flex: 1;
	min-width: 0;
	font-size: 14px;
	font-family: var(--kt-font-body);
}
.kt-rail-crumb-link {
	text-decoration: none;
	color: #374151;
	white-space: nowrap;
}
.kt-rail-crumb-link:hover {
	color: #2563eb;
	text-decoration: underline;
	text-underline-offset: 3px;
}
.kt-rail-sep {
	color: color-mix(in srgb, var(--kt-color-text) 35%, transparent);
}
.kt-rail-crumb-current {
	font-family: var(--kt-font-heading);
	font-weight: var(--kt-font-heading-weight);
	font-size: 17px;
	letter-spacing: 0.01em;
	color: #0a1929;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.kt-rail-pe {
	display: flex;
	align-items: center;
	gap: 8px;
	flex: none;
	min-width: 0;
}
.kt-rail-pe-label {
	font-size: 11px;
	letter-spacing: 0.06em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--kt-color-text) 58%, transparent);
	flex: none;
}
.kt-rail-pe-select {
	max-width: 260px;
	font-family: var(--kt-font-body);
	font-size: 13.5px;
	color: var(--kt-color-text);
	background: #fff;
	border: 1px solid var(--kt-color-divider);
	border-radius: var(--kt-radius-md);
	padding: 6px 8px;
	cursor: pointer;
}
.kt-rail-pe-current {
	font-family: var(--kt-font-body);
	font-size: 13.5px;
	color: var(--kt-color-text);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 260px;
}
.kt-rail-actions {
	display: flex;
	align-items: center;
	gap: 4px;
	flex: none;
}
.kt-rail-tools {
	position: relative;
	display: flex;
	align-items: center;
	gap: 4px;
}
.kt-rail-notification-host {
	position: relative;
	display: flex;
	align-items: center;
}
.kt-rail-notification-host :deep(.dropdown-notifications) {
	position: absolute;
	top: 0;
	right: 0;
	z-index: 35;
	width: min(440px, calc(100vw - 32px));
	height: min(72vh, 680px);
	max-height: min(72vh, 680px);
}
.kt-rail-notification-host :deep(.notifications-list) {
	position: absolute;
	top: 0;
	right: 0;
	left: auto;
	width: min(440px, calc(100vw - 32px));
	max-height: min(72vh, 680px);
	height: min(72vh, 680px);
	min-height: 320px;
	border: 1px solid rgba(148, 163, 184, 0.35);
	border-radius: 16px;
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
	box-shadow: 0 22px 60px rgb(15 23 42 / 16%);
	overflow: hidden;
}
.kt-rail-notification-host :deep(.notification-list-body) {
	max-height: calc(72vh - 72px);
	background: rgba(255, 255, 255, 0.45);
}
.kt-rail-notification-host :deep(.notification-list-header) {
	margin: 0;
	padding: 0 14px;
	background: linear-gradient(180deg, #f8fafc, #f3f4f6);
	border-bottom: 1px solid #e5e7eb;
}
.kt-rail-notification-host :deep(.notification-item-tabs) {
	display: flex;
	gap: 16px;
}
.kt-rail-notification-host :deep(.notification-item-tabs .notifications-category) {
	margin: 0;
	padding: 14px 2px 12px;
	border-bottom: 2px solid transparent;
	color: #6b7280;
	font-size: 12px;
	font-weight: 600;
}
.kt-rail-notification-host :deep(.notification-item-tabs .notifications-category.active) {
	border-bottom-color: #17191c;
	color: #17191c;
}
.kt-rail-notification-host :deep(.header-actions) {
	color: #4b5563;
}
.kt-rail-notification-host :deep(.recent-item.notification-item) {
	max-width: none;
	margin: 6px 8px;
	padding: 12px;
	border: 1px solid transparent;
	border-radius: 10px;
	background: rgba(255, 255, 255, 0.9);
	color: #17191c;
	text-decoration: none;
	transition:
		background 0.2s ease,
		border-color 0.2s ease,
		box-shadow 0.2s ease;
}
.kt-rail-notification-host :deep(.recent-item.notification-item.unread) {
	border-color: #e5e7eb;
	background: #f3f4f6;
}
.kt-rail-notification-host :deep(.recent-item.notification-item:hover) {
	border-color: #d1d5db;
	background: #f9fafb;
	color: #17191c;
	text-decoration: none;
	box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.15);
}
.kt-rail-notification-host :deep(.notification-body::before) {
	width: 7px;
	height: 7px;
	min-width: 7px;
	margin-top: 15px;
	background: #d1d5db;
}
.kt-rail-notification-host :deep(.notification-item.unread .notification-body::before) {
	background: #17191c;
}
.kt-rail-notification-host :deep(.notification-item .message),
.kt-rail-notification-host :deep(.notification-item .message a),
.kt-rail-notification-host :deep(.notification-item a),
.kt-rail-notification-host :deep(.notification-item .notification-timestamp),
.kt-rail-notification-host :deep(.list-footer) {
	text-decoration: none;
}
.kt-rail-notification-host :deep(.notification-item .message) {
	max-width: none;
	color: #17191c;
}
.kt-rail-notification-host :deep(.notification-item .notification-timestamp) {
	color: #737982;
}
.kt-rail-notification-host :deep(.list-footer) {
	margin: 8px 10px 12px;
	border: 1px solid #d1d5db;
	border-radius: 8px;
	background: #f3f4f6;
	color: #17191c;
}
.kt-rail-notification-host :deep(.list-footer:hover) {
	background: #e5e7eb;
	color: #17191c;
}
.kt-rail-notification-host :deep(.notifications-unseen) {
	position: absolute;
	top: 3px;
	right: 3px;
	color: #df3d3d;
}
.kt-rail-notification-host :deep(.notifications-icon) {
	position: relative;
	display: grid;
	place-items: center;
}
.kt-rail-notification-count {
	position: absolute;
	top: 1px;
	right: 1px;
	z-index: 2;
	min-width: 16px;
	height: 16px;
	padding: 0 4px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	border: 1px solid #f2f4f6;
	border-radius: 999px;
	background: #df3d3d;
	color: #fff;
	font-size: 9px;
	font-weight: 700;
	line-height: 1;
}
.kt-rail-btn {
	width: 40px;
	height: 40px;
	display: grid;
	place-items: center;
	border: 0;
	background: none;
	color: #374151;
	cursor: pointer;
	border-radius: var(--kt-radius-md);
	position: relative;
}
.kt-rail-btn:hover {
	background: #eff6ff;
	color: #2563eb;
}
.kt-rail-div {
	width: 1px;
	height: 28px;
	background: var(--kt-color-divider);
	flex: none;
}
.kt-rail-user-wrap {
	position: relative;
	flex: none;
}
.kt-rail-user {
	flex: none;
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 4px 10px 4px 8px;
	border: 0;
	background: none;
	cursor: pointer;
	border-radius: var(--kt-radius-md);
}
.kt-rail-user:hover {
	background: #eff6ff;
}
.kt-rail-user-menu {
	position: absolute;
	top: calc(100% + 8px);
	right: 0;
	min-width: 180px;
	display: flex;
	flex-direction: column;
	padding: 8px;
	border: 1px solid var(--kt-color-divider);
	border-radius: var(--kt-radius-md);
	background: #fff;
	box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
	z-index: 30;
}
.kt-rail-user-menu-item {
	display: inline-flex;
	align-items: center;
	gap: 10px;
	border: 0;
	background: transparent;
	color: var(--kt-color-text);
	padding: 10px 12px;
	border-radius: 8px;
	text-align: left;
	font: inherit;
	font-size: 14px;
	cursor: pointer;
}
.kt-rail-user-menu-item:hover,
.kt-rail-user-menu-item:focus-visible {
	background: #eff6ff;
	color: #2563eb;
	outline: none;
}
.kt-rail-user-menu-item.danger {
	color: color-mix(in srgb, var(--kt-color-text) 78%, transparent);
}
.kt-rail-user-menu-item.danger:hover,
.kt-rail-user-menu-item.danger:focus-visible {
	background: rgba(220, 38, 38, 0.08);
	color: #b42318;
}
.kt-rail-user-menu-icon {
	width: 16px;
	height: 16px;
	stroke: currentColor;
	fill: none;
	stroke-width: 1.8;
	stroke-linecap: round;
	stroke-linejoin: round;
	flex: none;
}
.kt-rail-user-text {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
	line-height: 1;
}
.kt-rail-user-name {
	font-family: var(--kt-font-heading);
	font-weight: var(--kt-font-heading-weight);
	font-size: 15px;
	letter-spacing: 0.01em;
	color: #0a1929;
}
.kt-rail-user-role {
	font-size: 11px;
	letter-spacing: 0.06em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--kt-color-text) 58%, transparent);
}
.kt-all-notifications-backdrop {
	position: fixed;
	inset: 0;
	z-index: 1060;
	display: flex;
	align-items: flex-start;
	justify-content: flex-end;
	padding: 72px 20px 20px;
	background: rgba(15, 23, 42, 0.12);
}
.kt-all-notifications-modal {
	display: flex;
	width: min(420px, 100%);
	max-height: min(82vh, 760px);
	flex-direction: column;
	border: 1px solid #e0e5ec;
	border-radius: 16px;
	background: #f7f8fa;
	color: #17191c;
	box-shadow: 0 18px 48px rgba(17, 24, 39, 0.18);
	overflow: hidden;
}
.kt-all-notifications-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	padding: 18px 18px 12px;
}
.kt-all-notifications-header h2 {
	margin: 0;
	color: #1f2430;
	font-size: 18px;
	font-weight: 700;
	letter-spacing: 0;
}
.kt-all-notifications-header-actions {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	gap: 10px;
}
.kt-all-notifications-settings {
	min-height: 32px;
	padding: 0 10px;
	border: 1px solid #dfe3e7;
	border-radius: 8px;
	background: #fff;
	color: #3a3e45;
	font-size: 12px;
	font-weight: 600;
	cursor: pointer;
}
.kt-all-notifications-mark-read {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	border: 0;
	background: transparent;
	color: #3c6fe4;
	font-size: 12px;
	font-weight: 700;
	cursor: pointer;
	transition: opacity 0.2s ease;
}
.kt-all-notifications-mark-read:hover:not(:disabled) {
	opacity: 0.8;
}
.kt-all-notifications-mark-read:disabled {
	cursor: not-allowed;
	opacity: 0.5;
}
.kt-all-notifications-toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	padding: 0 12px 12px;
}
.kt-all-notifications-filters {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 4px;
	width: 100%;
	padding: 4px;
	border: 1px solid #e2e7ed;
	border-radius: 10px;
	background: #eef1f5;
}
.kt-all-notifications-filters button,
.kt-all-notifications-more {
	min-height: 34px;
	padding: 0 10px;
	border: 0;
	border-radius: 7px;
	background: transparent;
	color: #3a3e45;
	font-size: 12px;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.2s ease;
}
.kt-all-notifications-filters button {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	border: 1px solid transparent;
}
.kt-all-notifications-filters button[aria-pressed="true"],
.kt-all-notifications-filters button.is-active {
	background: #fff;
	border-color: #e2e6eb;
	color: #1d2430;
	box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}
.kt-all-notifications-pill {
	display: inline-flex;
	min-width: 18px;
	height: 18px;
	padding: 0 5px;
	align-items: center;
	justify-content: center;
	border-radius: 999px;
	background: rgba(59, 90, 165, 0.12);
	color: #3b5ca5;
	font-size: 11px;
	font-weight: 700;
}
.kt-all-notifications-list {
	min-height: 180px;
	overflow: auto;
	padding: 0 10px 12px;
	background: #f7f8fa;
}
.kt-all-notification-row {
	display: grid;
	grid-template-columns: 36px minmax(0, 1fr) 10px;
	align-items: center;
	gap: 10px;
	padding: 10px 8px;
	border-radius: 10px;
	border: 1px solid transparent;
	color: #17191c;
	text-decoration: none;
	transition:
		background 0.2s ease,
		border-color 0.2s ease;
}
.kt-all-notification-row + .kt-all-notification-row {
	margin-top: 4px;
}
.kt-all-notification-row:hover,
.kt-all-notification-row:focus-visible,
.kt-all-notification-row.is-unread {
	background: #eaf1ff;
	border-color: #dfe8fb;
	color: #17191c;
	text-decoration: none;
	outline: none;
}
.kt-all-notification-avatar {
	display: grid;
	place-items: center;
	width: 32px;
	height: 32px;
	border-radius: 50%;
	background: linear-gradient(135deg, #f1e5d7, #d5dfe9);
	color: #232a35;
	font-size: 14px;
	font-weight: 700;
	border: 2px solid rgba(255, 255, 255, 0.8);
}
.kt-all-notification-content {
	display: flex;
	flex-direction: column;
	gap: 4px;
	min-width: 0;
}
.kt-all-notification-content strong {
	color: #1a1d22;
	font-size: 12px;
	font-weight: 700;
}
.kt-all-notification-content span {
	color: #4c535d;
	font-size: 12px;
	line-height: 1.5;
}
.kt-all-notification-content time,
.kt-all-notification-side time {
	color: #737b84;
	font-size: 11px;
	line-height: 1.4;
}
.kt-all-notification-side {
	display: inline-flex;
	align-items: center;
	gap: 0;
	justify-self: end;
}
.kt-all-notification-side time {
	display: none;
}
.kt-all-notification-marker {
	display: inline-block;
	width: 7px;
	height: 7px;
	margin-top: 1px;
	border-radius: 50%;
	background: #3c6fe4;
	box-shadow: 0 0 0 2px rgba(60, 111, 228, 0.12);
}
.kt-all-notification-row:not(.is-unread) .kt-all-notification-marker {
	background: rgba(60, 111, 228, 0.2);
	box-shadow: none;
}
.kt-all-notifications-state {
	padding: 52px 16px;
	color: #6b7280;
	font-size: 13px;
	text-align: center;
}
.kt-all-notifications-more {
	display: block;
	margin: 16px auto 0;
	border: 1px solid #d1d5db;
	background: #f9fafb;
	color: #17191c;
}
.kt-rail-avatar-frame {
	position: relative;
	width: 34px;
	height: 34px;
	border-radius: 8px;
	overflow: hidden;
	background: var(--kt-color-accent-100);
	display: grid;
	place-items: center;
	flex: none;
}
.kt-rail-avatar {
	width: 34px;
	height: 34px;
	border-radius: 8px;
	display: grid;
	place-items: center;
	font-family: var(--kt-font-heading);
	font-weight: var(--kt-font-heading-weight);
	font-size: 14px;
	letter-spacing: 0.04em;
	color: #fff;
	background: var(--kt-color-accent);
}
.kt-rail-avatar-photo {
	width: 34px;
	height: 34px;
	object-fit: cover;
	display: block;
	filter: grayscale(1) contrast(1.05);
}
.kt-rail-chevron {
	color: color-mix(in srgb, var(--kt-color-text) 50%, transparent);
	flex: none;
}
/* Narrow screens (≤600 px, e.g. a 390 px phone): the rail keeps the
   current page, the actions and the avatar; ancestor crumbs, the user's
   name/role text and the divider give way so nothing is clipped off-screen
   (STD-TPL-IMP-001 follow-up FU-05). */
@media (max-width: 600px) {
	.kt-rail {
		gap: 8px;
		padding: 0 12px;
	}
	.kt-rail-crumb-link,
	.kt-rail-sep,
	.kt-rail-user-text,
	.kt-rail-div,
	.kt-rail-chevron,
	.kt-rail-pe-label {
		display: none;
	}
	.kt-rail-crumb-current {
		font-size: 15px;
	}
	.kt-rail-pe-select,
	.kt-rail-pe-current {
		max-width: 120px;
	}
	.kt-rail-user {
		padding: 4px;
	}
	.kt-all-notifications-backdrop {
		align-items: end;
		padding: 0;
	}
	.kt-all-notifications-modal {
		width: 100%;
		max-height: 92vh;
		border-radius: 12px 12px 0 0;
	}
	.kt-all-notifications-header {
		padding: 18px 16px;
	}
	.kt-all-notifications-header-actions {
		gap: 6px;
	}
	.kt-all-notifications-toolbar {
		align-items: flex-start;
		flex-direction: column;
		padding: 12px 16px;
	}
	.kt-all-notifications-list {
		padding: 6px 12px 16px;
	}
	.kt-all-notification-row {
		grid-template-columns: 12px minmax(0, 1fr);
	}
	.kt-all-notification-row time {
		grid-column: 2;
	}
}
</style>
