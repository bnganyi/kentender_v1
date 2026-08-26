<script setup>
import { ref, computed, onMounted } from "vue";
import { usePageRail } from "../std_configuration_shared/composables/usePageRail.js";

const railEl = ref(null);
usePageRail(railEl, computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Standard Tender Documents") },
]));

const loading = ref(true);
const error = ref(null);
const packages = ref([]);

async function refresh() {
	loading.value = true;
	error.value = null;
	try {
		packages.value = await frappe.xcall("kentender_procurement.std_configuration.api.std_configuration_api.list_std_packages");
	} catch (e) {
		error.value = e;
	} finally {
		loading.value = false;
	}
}
onMounted(refresh);

function statusClass(state) {
	if (state === "Active") return "is-live";
	if (state === "In review") return "is-pending";
	return "is-draft";
}

function activeVersionLabel(pkg) {
	return pkg.current_active_version_id || __("Not active");
}

function openPackage(pkg) {
	frappe.set_route("std-cfg-package-home", pkg.name);
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell">
			<header>
				<div class="kt-eyebrow">{{ __("Configuration and Governance") }}</div>
				<h1 style="font-size: 32px">{{ __("Standard Tender Documents") }}</h1>
				<p class="kt-muted" style="margin-top: 6px">
					{{ __("Configure and activate the standard document packages used by KenTender.") }}
				</p>
			</header>

			<div v-if="error" class="kt-card kt-empty">
				<h2>{{ __("Could not load Standard Tender Documents.") }}</h2>
				<p>{{ error.message }}</p>
			</div>
			<div v-else class="kt-card kt-blueprint">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div v-if="loading">
					<div v-for="i in 3" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
				</div>
				<div v-else-if="!packages.length" class="kt-empty">
					<h2>{{ __("No Standard Tender Documents configured yet.") }}</h2>
				</div>
				<table v-else class="kt-table">
					<thead>
						<tr>
							<th>{{ __("Standard Tender Document") }}</th>
							<th>{{ __("Profile") }}</th>
							<th>{{ __("Active version") }}</th>
							<th>{{ __("Status") }}</th>
							<th></th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="pkg in packages" :key="pkg.name">
							<td>{{ pkg.package_code }} · {{ pkg.official_title }}</td>
							<td>{{ pkg.requirement_profile }}</td>
							<td>{{ activeVersionLabel(pkg) }}</td>
							<td><span class="kt-status" :class="statusClass(pkg.state)">{{ pkg.state }}</span></td>
							<td><a href="#" @click.prevent="openPackage(pkg)">{{ __("Open package") }}</a></td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-if="!loading && !error" class="kt-muted">
				{{ __("{0} Standard Tender Document{1}", [packages.length, packages.length === 1 ? "" : "s"]) }}
			</div>
		</div>
	</div>
</template>
