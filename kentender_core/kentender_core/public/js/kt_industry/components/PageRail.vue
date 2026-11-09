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
const notificationsOpen = ref(false);
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

function setNotificationsOpen(open) {
	if (!notificationWrapper.value) return;
	const dropdown = $(notificationWrapper.value).find(".dropdown-notifications");
	dropdown.toggleClass("hidden", !open);
	notificationsOpen.value = open;
}

function toggleNotifications() {
	setNotificationsOpen(!notificationsOpen.value);
	if (notificationsOpen.value) {
		menuOpen.value = false;
		refreshUnreadNotificationCount();
	}
}

function closeRailNotifications() {
	setNotificationsOpen(false);
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
}

function onNotificationIndicatorHide() {
	refreshUnreadNotificationCount();
}

function onNotificationReadAction() {
	window.setTimeout(refreshUnreadNotificationCount, 400);
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
		const filters = { for_user: frappe.session.user };
		if (allNotificationsFilter.value === "unread") filters.read = 0;
		const response = await frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Notification Log",
				fields: ["name", "subject", "type", "read", "from_user", "creation", "link", "document_type", "document_name"],
				filters,
				order_by: "creation desc",
				limit_start: reset ? 0 : allNotifications.value.length,
				limit_page_length: NOTIFICATION_PAGE_SIZE + 1,
			},
		});
		const rows = response.message || [];
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
	setNotificationsOpen(false);
	menuOpen.value = false;
	allNotificationsFilter.value = "all";
	allNotificationsOpen.value = true;
	loadAllNotifications(true);
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
		await frappe.call("frappe.desk.doctype.notification_log.notification_log.mark_all_as_read");
		allNotifications.value = allNotificationsFilter.value === "unread"
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
	return frappe.utils?.strip_html ? frappe.utils.strip_html(subject) : String(subject).replace(/<[^>]*>/g, "");
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

function onNotificationFooterClick(event) {
	const footer = event.target.closest(".list-footer");
	if (!footer || !notificationWrapper.value?.contains(footer)) return;
	event.preventDefault();
	event.stopImmediatePropagation();
	openAllNotifications();
}

function handleClickOutside(event) {
	if (userMenu.value && !userMenu.value.contains(event.target)) {
		closeMenu();
	}
	if (
		notificationsOpen.value &&
		notificationWrapper.value &&
		!notificationWrapper.value.contains(event.target) &&
		!event.target.closest(".notifications-list")
	) {
		closeRailNotifications();
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
	if (notificationsEnabled.value && frappe.ui?.Notifications && notificationWrapper.value) {
		const notifications = frappe.app?.sidebar?.notifications;
		if (notifications?.dropdown?.length) {
			$(notificationWrapper.value).find(".dropdown-notifications").remove();
			$(notificationWrapper.value).append(notifications.dropdown);
			const view = notifications.tabs?.notifications;
			if (view) {
				view.notifications_icon = $(notificationWrapper.value).find(".notifications-icon");
			}
		} else {
			new frappe.ui.Notifications({
				full_height: true,
				wrapper: $(notificationWrapper.value),
			});
		}
		notificationWrapper.value.addEventListener("click", onNotificationFooterClick, true);
		document.querySelector(".body-sidebar .sidebar-notification")?.classList.add("hidden");
		refreshUnreadNotificationCount();
		frappe.realtime?.on("notification", onNewNotification);
		frappe.realtime?.on("indicator_hide", onNotificationIndicatorHide);
		$(notificationWrapper.value).on(
			"click.ktIndustryRailCount",
			".notification-item, .mark-all-read",
			onNotificationReadAction,
		);
	}
	$(document).on("page-change.ktIndustryRail", closeRailNotifications);
});

onBeforeUnmount(() => {
	document.removeEventListener("click", handleClickOutside);
	$(document).off("page-change.ktIndustryRail", closeRailNotifications);
	notificationWrapper.value?.removeEventListener("click", onNotificationFooterClick, true);
	frappe.realtime?.off?.("notification", onNewNotification);
	frappe.realtime?.off?.("indicator_hide", onNotificationIndicatorHide);
	$(notificationWrapper.value).off(".ktIndustryRailCount");
});

function toggleMenu() {
	menuOpen.value = !menuOpen.value;
	if (menuOpen.value) closeRailNotifications();
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
				<div class="dropdown-notifications" :class="{ hidden: !notificationsOpen }">
					<div class="notifications-list" role="menu">
						<div class="notification-list-header">
							<div class="header-items"></div>
							<div class="header-actions"></div>
						</div>
						<div class="notification-list-body">
							<div class="panel-notifications"></div>
							<div class="panel-events"></div>
							<div class="panel-changelog-feed"></div>
						</div>
					</div>
				</div>
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
		<div v-if="allNotificationsOpen" class="kt-all-notifications-backdrop" @click.self="closeAllNotifications" @keydown.esc="closeAllNotifications">
			<section class="kt-all-notifications-modal" role="dialog" aria-modal="true" aria-labelledby="kt-all-notifications-title">
				<header class="kt-all-notifications-header">
					<div><p>{{ __("ACCOUNT ACTIVITY") }}</p><h2 id="kt-all-notifications-title">{{ __("All Notifications") }}</h2></div>
					<button type="button" class="kt-all-notifications-close" :aria-label="__('Close notifications')" @click="closeAllNotifications">×</button>
				</header>
				<div class="kt-all-notifications-toolbar">
					<div class="kt-all-notifications-filters" role="group" :aria-label="__('Filter notifications')">
						<button type="button" :aria-pressed="allNotificationsFilter === 'all'" @click="filterAllNotifications('all')">{{ __("All") }}</button>
						<button type="button" :aria-pressed="allNotificationsFilter === 'unread'" @click="filterAllNotifications('unread')">{{ __("Unread") }}<span v-if="unreadNotificationCount">{{ unreadNotificationCount > 99 ? "99+" : unreadNotificationCount }}</span></button>
					</div>
					<button type="button" class="kt-all-notifications-mark-read" :disabled="markingAllNotificationsRead || unreadNotificationCount === 0" @click="markAllNotificationsRead">{{ markingAllNotificationsRead ? __("Marking…") : __("Mark all as read") }}</button>
				</div>
				<div class="kt-all-notifications-list" aria-live="polite">
					<p v-if="allNotificationsLoading && !allNotifications.length" class="kt-all-notifications-state" role="status">{{ __("Loading notifications…") }}</p>
					<p v-else-if="allNotificationsError" class="kt-all-notifications-state" role="alert">{{ allNotificationsError }}</p>
					<p v-else-if="!allNotifications.length" class="kt-all-notifications-state">{{ allNotificationsFilter === 'unread' ? __("You are all caught up.") : __("No notifications yet.") }}</p>
					<a v-for="notification in allNotifications" :key="notification.name" class="kt-all-notification-row" :class="{ 'is-unread': !notification.read }" :href="notificationHref(notification)" @click.prevent="openNotification(notification)">
						<span class="kt-all-notification-marker" aria-hidden="true"></span>
						<span class="kt-all-notification-content"><strong>{{ notificationSubject(notification) }}</strong><span>{{ notification.from_user || __("KenTender") }}<template v-if="notification.type"> · {{ notification.type }}</template></span></span>
						<time>{{ notificationTime(notification.creation) }}</time>
					</a>
					<button v-if="allNotificationsHasMore" type="button" class="kt-all-notifications-more" :disabled="allNotificationsLoadingMore" @click="loadMoreNotifications">{{ allNotificationsLoadingMore ? __("Loading…") : __("Load more") }}</button>
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
	width: min(390px, calc(100vw - 32px));
	height: min(72vh, 680px);
	max-height: min(72vh, 680px);
}
.kt-rail-notification-host :deep(.notifications-list) {
	position: absolute;
	top: 0;
	right: 0;
	left: auto;
	width: min(390px, calc(100vw - 32px));
	max-height: min(72vh, 680px);
	height: min(72vh, 680px);
	min-height: 320px;
	border: 1px solid #d9dde1;
	border-radius: 12px;
	background: #fff;
	box-shadow: 0 18px 48px rgb(0 0 0 / 16%);
}
.kt-rail-notification-host :deep(.notification-list-body) {
	max-height: calc(72vh - 72px);
}
.kt-rail-notification-host :deep(.notification-list-header) {
	margin: 0;
	padding: 0 14px;
	background: #f3f4f6;
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
	border-radius: 8px;
	background: #fff;
	color: #17191c;
}
.kt-rail-notification-host :deep(.recent-item.notification-item.unread) {
	border-color: #e5e7eb;
	background: #f3f4f6;
}
.kt-rail-notification-host :deep(.recent-item.notification-item:hover) {
	border-color: #d1d5db;
	background: #f9fafb;
	color: #17191c;
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
.kt-rail-notification-host :deep(.notification-item .message) {
	max-width: none;
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
	display: grid;
	place-items: center;
	padding: 24px;
	background: rgb(17 24 39 / 38%);
}
.kt-all-notifications-modal {
	display: flex;
	width: min(920px, 100%);
	max-height: min(88vh, 820px);
	flex-direction: column;
	border: 1px solid #d9dde1;
	border-radius: 12px;
	background: #fff;
	color: #17191c;
	box-shadow: 0 24px 70px rgb(0 0 0 / 20%);
}
.kt-all-notifications-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 20px;
	padding: 22px 24px;
	border-bottom: 1px solid #e5e7eb;
}
.kt-all-notifications-header p {
	margin: 0 0 4px;
	color: #6b7280;
	font-size: 10px;
	font-weight: 700;
	letter-spacing: 0.08em;
}
.kt-all-notifications-header h2 {
	margin: 0;
	color: #17191c;
	font-size: 21px;
	font-weight: 650;
}
.kt-all-notifications-close {
	display: grid;
	width: 36px;
	height: 36px;
	place-items: center;
	border: 1px solid #d9dde1;
	border-radius: 8px;
	background: #fff;
	color: #4b5563;
	font-size: 22px;
	cursor: pointer;
}
.kt-all-notifications-close:hover {
	background: #f3f4f6;
	color: #17191c;
}
.kt-all-notifications-toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	padding: 14px 24px;
	border-bottom: 1px solid #e5e7eb;
	background: #f9fafb;
}
.kt-all-notifications-filters {
	display: inline-flex;
	gap: 4px;
	padding: 3px;
	border: 1px solid #e5e7eb;
	border-radius: 8px;
	background: #fff;
}
.kt-all-notifications-filters button,
.kt-all-notifications-mark-read,
.kt-all-notifications-more {
	min-height: 36px;
	padding: 0 12px;
	border: 0;
	border-radius: 6px;
	background: transparent;
	color: #5b616a;
	font-size: 12px;
	font-weight: 600;
	cursor: pointer;
}
.kt-all-notifications-filters button[aria-pressed="true"] {
	background: #e5e7eb;
	color: #17191c;
}
.kt-all-notifications-filters button span {
	margin-left: 6px;
	color: #17191c;
}
.kt-all-notifications-mark-read {
	border: 1px solid #d1d5db;
	background: #fff;
	color: #17191c;
}
.kt-all-notifications-mark-read:hover:not(:disabled),
.kt-all-notifications-more:hover:not(:disabled) {
	background: #e5e7eb;
	color: #17191c;
}
.kt-all-notifications-mark-read:disabled,
.kt-all-notifications-more:disabled {
	cursor: not-allowed;
	opacity: 0.55;
}
.kt-all-notifications-list {
	min-height: 240px;
	overflow: auto;
	padding: 8px 24px 20px;
}
.kt-all-notification-row {
	display: grid;
	grid-template-columns: 12px minmax(0, 1fr) auto;
	align-items: start;
	gap: 12px;
	padding: 15px 12px;
	border-bottom: 1px solid #eceff1;
	color: #17191c;
	text-decoration: none;
}
.kt-all-notification-row:hover,
.kt-all-notification-row.is-unread {
	background: #f3f4f6;
	color: #17191c;
}
.kt-all-notification-row:hover {
	text-decoration: none;
}
.kt-all-notification-marker {
	width: 7px;
	height: 7px;
	margin-top: 5px;
	border: 1px solid #9ca3af;
	border-radius: 50%;
	background: #fff;
}
.kt-all-notification-row.is-unread .kt-all-notification-marker {
	border-color: #17191c;
	background: #17191c;
}
.kt-all-notification-content {
	display: grid;
	gap: 4px;
	min-width: 0;
}
.kt-all-notification-content strong {
	color: #17191c;
	font-size: 13px;
	font-weight: 600;
}
.kt-all-notification-content span,
.kt-all-notification-row time {
	color: #737982;
	font-size: 11px;
}
.kt-all-notification-row time {
	white-space: nowrap;
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
	.kt-rail-notification-host :deep(.notifications-list) {
		right: -44px;
		width: calc(100vw - 24px);
		min-width: 0;
	}
	.kt-rail-notification-host :deep(.dropdown-notifications) {
		width: calc(100vw - 24px);
		height: min(72vh, 680px);
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
