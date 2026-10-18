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
	frappe.set_route("Form", "User", frappe.session.user);
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
			<button
				type="button"
				class="kt-rail-btn"
				:aria-label="__('Help')"
				@click="frappe.set_route('List', 'Help Article')"
			>
				<svg
					width="20"
					height="20"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<circle cx="12" cy="12" r="10"></circle>
					<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
					<path d="M12 17h.01"></path>
				</svg>
			</button>
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
</template>

<style scoped>
.kt-rail {
	display: flex;
	align-items: center;
	gap: 24px;
	height: 64px;
	flex: none;
	padding: 0 32px;
	border-bottom: 1px solid var(--kt-color-divider);
	background: #f2f4f6;
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
	color: color-mix(in srgb, var(--kt-color-text) 62%, transparent);
	white-space: nowrap;
}
.kt-rail-crumb-link:hover {
	color: var(--kt-color-text);
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
	color: var(--kt-color-text);
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
}
.kt-rail-notification-host :deep(.notifications-list) {
	position: absolute;
	top: 0;
	right: 0;
	left: auto;
	width: min(360px, calc(100vw - 32px));
	max-height: min(70vh, 640px);
	height: min(70vh, 640px);
	min-height: 360px;
	border: 1px solid var(--kt-color-divider);
	border-radius: var(--kt-radius-md);
	box-shadow: 0 16px 32px rgba(15, 23, 42, 0.12);
}
.kt-rail-notification-host :deep(.notification-list-body) {
	max-height: calc(70vh - 64px);
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
	color: color-mix(in srgb, var(--kt-color-text) 70%, transparent);
	cursor: pointer;
	border-radius: var(--kt-radius-md);
	position: relative;
}
.kt-rail-btn:hover {
	background: var(--kt-color-accent-100);
	color: var(--kt-color-accent-800);
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
	background: var(--kt-color-accent-100);
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
	background: var(--kt-color-accent-100);
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
	color: var(--kt-color-text);
}
.kt-rail-user-role {
	font-size: 11px;
	letter-spacing: 0.06em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--kt-color-text) 58%, transparent);
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
}
</style>
