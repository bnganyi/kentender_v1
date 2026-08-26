<script setup>
// STD-WF-05 — Version Comparison (§15.20). Real but coarse: the backend read
// (get_std_version_comparison) reports doctype-level row-count changes
// between two Versions, not the artboard's field-level diff text ("Tender
// validity minimum 120 -> 150 days") — that needs a real structured diff
// engine, which is out of this phase's scope (documented in the API's own
// comment). This renders the real coarse signal honestly rather than
// fabricating field-level sentences the backend cannot actually produce.
import { ref, computed, onMounted } from "vue";
import { useRouteState } from "../std_configuration_shared/composables/useRouteState.js";
import { usePageRail } from "../std_configuration_shared/composables/usePageRail.js";

const DOCTYPE_LABELS = {
	"STD Cfg Content Block": __("Coverage and Document Structure"),
	"STD Cfg Parameter Definition": __("Tender Parameters"),
	"STD Cfg Requirement Schema": __("IT Requirements"),
	"STD Cfg Schedule Schema": __("Schedule, Inventory and Background (schedule)"),
	"STD Cfg Inventory Schema": __("Schedule, Inventory and Background (inventory)"),
	"STD Cfg Price Schema": __("Price Schedules"),
	"STD Cfg Evaluation Schema": __("Evaluation and Qualification"),
	"STD Cfg Form Schema": __("Forms and Evidence"),
	"STD Cfg Contract Schema": __("Contract and Outputs (values)"),
	"STD Cfg Output Mapping": __("Contract and Outputs (mappings)"),
};

const { route } = useRouteState("std-cfg-comparison");
const versionA = computed(() => route.value[1]);
const versionB = computed(() => route.value[2]);

const railEl = ref(null);
const loading = ref(true);
const error = ref(null);
const comparison = ref(null);
const docA = ref(null);
const docB = ref(null);

async function refresh() {
	loading.value = true;
	error.value = null;
	try {
		[docA.value, docB.value, comparison.value] = await Promise.all([
			frappe.db.get_doc("STD Cfg Version", versionA.value),
			frappe.db.get_doc("STD Cfg Version", versionB.value),
			frappe.xcall(
				"kentender_procurement.std_configuration.api.std_configuration_api.get_std_version_comparison",
				{ version_a: versionA.value, version_b: versionB.value }
			),
		]);
	} catch (e) {
		error.value = e;
	} finally {
		loading.value = false;
	}
}
onMounted(refresh);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Standard Tender Documents"), route: ["std-cfg-documents"] },
	{ label: __("Review") },
	{ label: docB.value ? `${docB.value.package_id} ${__("Version")} ${docB.value.version_number}` : "" },
	{ label: __("Comparison") },
]);
usePageRail(railEl, railTrail);

function label(doctype) {
	return DOCTYPE_LABELS[doctype] || doctype;
}

function viewChange() {
	frappe.show_alert({ message: __("Field-level change detail is not available yet."), indicator: "orange" });
}

function backToReview() {
	window.history.back();
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell">
			<div v-if="error" class="kt-card kt-empty">
				<h2>{{ __("Could not load this comparison.") }}</h2>
				<p>{{ error.message }}</p>
			</div>
			<div v-else-if="loading" class="kt-card kt-blueprint">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div v-for="i in 3" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
			</div>
			<template v-else>
				<header style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px">
					<div>
						<h1 style="font-size: 28px">{{ __("Changes from Active Version") }} {{ docA.version_number }}</h1>
						<p class="kt-muted" style="margin: 6px 0 0">
							{{ __("Version") }} {{ docB.version_number }} · {{ docB.official_issue_label }}
						</p>
					</div>
					<span class="kt-status is-pending">{{ docB.status }}</span>
				</header>

				<div class="kt-card kt-blueprint" style="display: grid; grid-template-columns: repeat(2, 1fr); margin-bottom: 24px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div style="text-align: center; padding: 14px">
						<div style="font-size: 24px; font-weight: 600">{{ comparison.changed.length }}</div>
						<div class="kt-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em">{{ __("Changed areas") }}</div>
					</div>
					<div style="text-align: center; padding: 14px">
						<div style="font-size: 24px; font-weight: 600">{{ comparison.unchanged.length }}</div>
						<div class="kt-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em">{{ __("Unchanged areas") }}</div>
					</div>
				</div>

				<div class="kt-card kt-blueprint" style="margin-bottom: 16px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<table class="kt-table" style="border: none">
						<thead>
							<tr>
								<th>{{ __("Area") }}</th>
								<th>{{ __("Active Version") }} {{ docA.version_number }}</th>
								<th>{{ __("Submitted Version") }} {{ docB.version_number }}</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in comparison.changed" :key="row.doctype">
								<td>{{ label(row.doctype) }}</td>
								<td>{{ row.count_a }} {{ __("row(s)") }}</td>
								<td>{{ row.count_b }} {{ __("row(s)") }}</td>
								<td><a href="#" class="kt-btn kt-btn-ghost" @click.prevent="viewChange">{{ __("View change") }}</a></td>
							</tr>
							<tr v-if="!comparison.changed.length">
								<td colspan="4" class="kt-muted">{{ __("No changed areas.") }}</td>
							</tr>
						</tbody>
					</table>
				</div>

				<p class="kt-muted">
					{{ __("{0} area(s) have no configured change.", [comparison.unchanged.length]) }}
				</p>

				<a href="#" class="kt-btn kt-btn-ghost" @click.prevent="backToReview">{{ __("Back to review") }}</a>
			</template>
		</div>
	</div>
</template>
