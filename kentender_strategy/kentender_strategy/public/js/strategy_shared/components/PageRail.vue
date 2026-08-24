<script setup>
// STR-CHG-001 v1.3 — shared top page rail, rendered inside the Vue root
// (.kt-strategy-ui scope) rather than reusing kentender_core.cl_shell's Civic
// Ledger toolbar, which is a different design system entirely (Tailwind/
// Material Symbols). Ported from kentender_core's reference_data PageRail.vue
// (CFG-PEFY-DES-12) — same structure, --kt-* tokens renamed to this app's own
// --ktstr-* tokens rather than depending on kentender_core's .kt-industry
// scope (AGENTS.md §6.6: port the pattern, don't cross-app deep-import).
const props = defineProps({
	trail: { type: Array, required: true }, // [{label, route?}] — last item has no route (current)
});

function initials(name) {
	const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
	if (!parts.length) return "U";
	if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
	return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

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
function sessionAvatarUrl() {
	try {
		const user = (frappe.session && frappe.session.user) || "";
		if (frappe.user_info && user) {
			const info = frappe.user_info(user);
			if (info && info.image) return info.image;
		}
		if (frappe.boot && frappe.boot.user && frappe.boot.user.image) return frappe.boot.user.image;
	} catch (e) {
		/* ignore */
	}
	return "";
}

const userName = sessionUserLabel();
const userRole = sessionUserRole();
const avatarUrl = sessionAvatarUrl();
const userInitials = initials(userName);

function goRoute(route) {
	if (!route) return;
	frappe.set_route.apply(frappe, route);
}

function openProfile() {
	frappe.set_route("Form", "User", frappe.session.user);
}
</script>

<template>
	<header class="kt-rail">
		<nav class="kt-rail-crumbs" aria-label="Breadcrumb">
			<template v-for="(item, i) in trail" :key="i">
				<a v-if="item.route" href="#" class="kt-rail-crumb-link" @click.prevent="goRoute(item.route)">{{ item.label }}</a>
				<span v-else class="kt-rail-crumb-current" aria-current="page">{{ item.label }}</span>
				<span v-if="i < trail.length - 1" class="kt-rail-sep">/</span>
			</template>
		</nav>
		<div class="kt-rail-actions">
			<button type="button" class="kt-rail-btn" :aria-label="__('Notifications')" @click="frappe.set_route('List', 'Notification Log')">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.268 21a2 2 0 0 0 3.464 0"></path><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"></path></svg>
			</button>
			<button type="button" class="kt-rail-btn" :aria-label="__('Help')" @click="frappe.set_route('List', 'Help Article')">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><path d="M12 17h.01"></path></svg>
			</button>
		</div>
		<div class="kt-rail-div"></div>
		<button type="button" class="kt-rail-user" @click="openProfile">
			<span class="kt-rail-user-text">
				<span class="kt-rail-user-name">{{ userName }}</span>
				<span v-if="userRole" class="kt-rail-user-role">{{ userRole }}</span>
			</span>
			<span class="kt-rail-avatar-frame">
				<img v-if="avatarUrl" class="kt-rail-avatar-photo" :src="avatarUrl" alt="" />
				<span v-else class="kt-rail-avatar">{{ userInitials }}</span>
			</span>
			<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="kt-rail-chevron"><path d="m6 9 6 6 6-6"></path></svg>
		</button>
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
	border-bottom: 1px solid var(--ktstr-color-divider);
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
	font-family: var(--ktstr-font-body);
}
.kt-rail-crumb-link {
	text-decoration: none;
	color: color-mix(in srgb, var(--ktstr-color-text) 62%, transparent);
	white-space: nowrap;
}
.kt-rail-crumb-link:hover {
	color: var(--ktstr-color-text);
	text-decoration: underline;
	text-underline-offset: 3px;
}
.kt-rail-sep {
	color: color-mix(in srgb, var(--ktstr-color-text) 35%, transparent);
}
.kt-rail-crumb-current {
	font-family: var(--ktstr-font-heading);
	font-weight: var(--ktstr-font-heading-weight);
	font-size: 17px;
	letter-spacing: 0.01em;
	color: var(--ktstr-color-text);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.kt-rail-actions {
	display: flex;
	align-items: center;
	gap: 4px;
	flex: none;
}
.kt-rail-btn {
	width: 40px;
	height: 40px;
	display: grid;
	place-items: center;
	border: 0;
	background: none;
	color: color-mix(in srgb, var(--ktstr-color-text) 70%, transparent);
	cursor: pointer;
	border-radius: var(--ktstr-radius-md);
}
.kt-rail-btn:hover {
	background: color-mix(in srgb, var(--ktstr-color-accent) 10%, transparent);
	color: var(--ktstr-color-accent-700);
}
.kt-rail-div {
	width: 1px;
	height: 28px;
	background: var(--ktstr-color-divider);
	flex: none;
}
.kt-rail-user {
	flex: none;
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 4px 4px 4px 8px;
	border: 0;
	background: none;
	cursor: pointer;
	border-radius: var(--ktstr-radius-md);
}
.kt-rail-user:hover {
	background: color-mix(in srgb, var(--ktstr-color-accent) 10%, transparent);
}
.kt-rail-user-text {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
	line-height: 1;
}
.kt-rail-user-name {
	font-family: var(--ktstr-font-heading);
	font-weight: var(--ktstr-font-heading-weight);
	font-size: 15px;
	letter-spacing: 0.01em;
	color: var(--ktstr-color-text);
}
.kt-rail-user-role {
	font-size: 11px;
	letter-spacing: 0.06em;
	text-transform: uppercase;
	color: color-mix(in srgb, var(--ktstr-color-text) 58%, transparent);
}
.kt-rail-avatar-frame {
	position: relative;
	width: 34px;
	height: 34px;
	border-radius: 8px;
	overflow: hidden;
	background: color-mix(in srgb, var(--ktstr-color-accent) 12%, transparent);
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
	font-family: var(--ktstr-font-heading);
	font-weight: var(--ktstr-font-heading-weight);
	font-size: 14px;
	letter-spacing: 0.04em;
	color: #fff;
	background: var(--ktstr-color-accent);
}
.kt-rail-avatar-photo {
	width: 34px;
	height: 34px;
	object-fit: cover;
	display: block;
	filter: grayscale(1) contrast(1.05);
}
.kt-rail-chevron {
	color: color-mix(in srgb, var(--ktstr-color-text) 50%, transparent);
	flex: none;
}
</style>
