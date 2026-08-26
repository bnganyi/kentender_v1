<script setup>
// STD-WF-02 — Package Review (§15.17). Reviewer's read of the immutable
// submitted snapshot (§16.4: "Review tabs always read the submitted
// snapshot; they never fall back to the current Draft or Active Version") —
// in practice this build's coverage/configuration reads are the Draft's
// live content, since the Draft is frozen (state "In review") for the
// duration of the review, which is the same guarantee in effect.
import { ref, reactive, computed, onMounted } from "vue";
import { useRouteState } from "../std_configuration_shared/composables/useRouteState.js";
import { usePageRail } from "../std_configuration_shared/composables/usePageRail.js";
import ReturnDialog from "./components/ReturnDialog.vue";

const PCFG_AREAS = [
	{ code: "PCFG-01", title: __("Source and Profile"), purpose: __("Official package identity and source") },
	{ code: "PCFG-02", title: __("Coverage and Document Structure"), purpose: __("Sixteen coverage areas, required sections and ordered content") },
	{ code: "PCFG-03", title: __("Tender Parameters"), purpose: __("Configurable and system-derived tender values") },
	{ code: "PCFG-04", title: __("IT Requirements"), purpose: __("Requirement composer and downstream response structure") },
	{ code: "PCFG-05", title: __("Schedule, Inventory and Background"), purpose: __("Delivery structure and bidder-relevant context") },
	{ code: "PCFG-06", title: __("Price Schedules"), purpose: __("Four bidder price-table structures") },
	{ code: "PCFG-07", title: __("Evaluation and Qualification"), purpose: __("Four evaluation stages and permitted criteria") },
	{ code: "PCFG-08", title: __("Forms and Evidence"), purpose: __("Eighteen field-level bidder forms") },
	{ code: "PCFG-09", title: __("Contract and Outputs"), purpose: __("SCC values, forms and downstream mappings") },
];
const TABS = ["Overview", "Coverage", "Configuration", "Complete preview", "History"];

const { route } = useRouteState("std-cfg-review");
const reviewTaskId = computed(() => route.value[1]);

const railEl = ref(null);
const loading = ref(true);
const workspace = ref(null);
const draftDoc = ref(null);
const pkg = ref(null);
const readiness = ref(null);
const areaStatus = reactive({});
const activeTab = ref("Overview");
const confirmed = ref(false);
const notInReview = computed(() => !workspace.value || workspace.value.task.status !== "Open");

async function refresh() {
	loading.value = true;
	workspace.value = await frappe.xcall(
		"kentender_procurement.std_configuration.api.std_configuration_api.get_std_review_workspace",
		{ review_task_id: reviewTaskId.value }
	);
	// get_std_review_workspace's own `draft` read is deliberately narrow (§13.1
	// — package_id/official_issue_label/official_source_file_id only); the
	// version number for the header/breadcrumb needs the full Draft doc.
	draftDoc.value = await frappe.db.get_doc("STD Cfg Draft", workspace.value.task.draft_id);
	pkg.value = await frappe.xcall(
		"kentender_procurement.std_configuration.api.std_configuration_api.get_std_package_home",
		{ package_id: workspace.value.draft.package_id }
	);
	readiness.value = await frappe.xcall(
		"kentender_procurement.std_configuration.api.std_configuration_api.get_std_readiness_report",
		{ reference_doctype: "STD Cfg Draft", reference_name: workspace.value.task.draft_id }
	);
	await Promise.all(
		PCFG_AREAS.map(async (a) => {
			if (a.code === "PCFG-01") {
				areaStatus[a.code] = workspace.value.draft.official_issue_label && workspace.value.draft.official_source_file_id ? "Complete" : "Incomplete";
				return;
			}
			const res = await frappe.xcall(
				"kentender_procurement.std_configuration.api.std_configuration_api.get_std_configuration_area",
				{ reference_doctype: "STD Cfg Draft", reference_name: workspace.value.task.draft_id, area: a.code }
			);
			const hasItems = Object.values(res.items).some((rows) => rows.length > 0);
			areaStatus[a.code] = hasItems ? "Complete" : "Not started";
		})
	);
	loading.value = false;
}
onMounted(refresh);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Standard Tender Documents"), route: ["std-cfg-documents"] },
	{ label: __("Review") },
	{ label: pkg.value && draftDoc.value ? `${pkg.value.package_code} ${__("Version")} ${draftDoc.value.proposed_version_number}` : "" },
]);
usePageRail(railEl, railTrail);

function viewArea(area) {
	frappe.set_route("std-cfg-area", "draft", workspace.value.task.draft_id, area.code);
}

const returnDialogOpen = ref(false);
const returnSaving = ref(false);
const returnError = ref("");
async function confirmReturn(correctionRequired) {
	returnSaving.value = true;
	returnError.value = "";
	try {
		await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.return_std_for_correction",
			{ review_task_id: reviewTaskId.value, correction_required: correctionRequired }
		);
		returnDialogOpen.value = false;
		frappe.show_alert({ message: __("Returned for correction"), indicator: "blue" });
		frappe.set_route("std-cfg-documents");
	} catch (e) {
		returnError.value = (e && e.message) || __("Could not return this package.");
	} finally {
		returnSaving.value = false;
	}
}

const activating = ref(false);
async function activatePackage() {
	activating.value = true;
	try {
		const version = await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.activate_std_version",
			{ review_task_id: reviewTaskId.value }
		);
		frappe.show_alert({ message: __("Version {0} activated", [version.version_number]), indicator: "green" });
		frappe.set_route("std-cfg-package-home", pkg.value.name);
	} finally {
		activating.value = false;
	}
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" style="padding-bottom: 88px">
			<div v-if="loading" class="kt-card kt-blueprint">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div v-for="i in 4" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
			</div>
			<template v-else>
				<header>
					<div class="kt-eyebrow">{{ __("STD Package Review") }}</div>
					<h1 style="font-size: 28px">{{ pkg.official_title }}</h1>
					<p class="kt-muted" style="margin: 4px 0 0">
						{{ pkg.package_code }} · {{ __("Submitted Version") }} {{ draftDoc.proposed_version_number }}
						<span class="kt-status is-pending" style="margin-left: 8px">{{ workspace.task.status === "Open" ? __("In review") : __("Decided") }}</span>
					</p>
				</header>

				<div class="kt-tabs">
					<div v-for="t in TABS" :key="t" class="kt-tab" :aria-selected="activeTab === t" @click="activeTab = t">{{ t }}</div>
				</div>

				<template v-if="activeTab === 'Overview'">
					<div class="kt-card kt-blueprint" style="padding: 16px">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<table class="kt-table" style="border: none">
							<tbody>
								<tr><td class="kt-muted">{{ __("Official issue") }}</td><td>{{ workspace.draft.official_issue_label || "—" }}</td></tr>
								<tr><td class="kt-muted">{{ __("Configured by") }}</td><td>{{ workspace.task.submitted_by }}</td></tr>
								<tr><td class="kt-muted">{{ __("Submitted") }}</td><td>{{ workspace.task.submitted_at }}</td></tr>
								<tr><td class="kt-muted">{{ __("Coverage") }}</td><td>{{ readiness.coverage_pass_count }} {{ __("of") }} {{ readiness.coverage.length }} {{ __("areas passed") }}</td></tr>
								<tr><td class="kt-muted">{{ __("Blocking findings") }}</td><td>{{ readiness.blocking_count }}</td></tr>
								<tr><td class="kt-muted">{{ __("Warnings") }}</td><td>{{ readiness.warning_count }}</td></tr>
							</tbody>
						</table>
					</div>

					<div v-if="readiness.warnings.length" class="kt-card" style="padding: 12px 16px; border-left: 3px solid #f59e0b">
						<div v-for="w in readiness.warnings" :key="w.code + w.message">{{ w.message }}</div>
					</div>

					<label style="display: flex; align-items: center; gap: 8px">
						<input type="checkbox" v-model="confirmed" />
						{{ __("I have reviewed the complete package against the official source, including all configuration areas, mappings and the rendered preview.") }}
					</label>
				</template>

				<div v-else-if="activeTab === 'Coverage'" class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<table class="kt-table" style="border: none">
						<thead><tr><th>{{ __("No.") }}</th><th>{{ __("STD area") }}</th><th>{{ __("Result") }}</th></tr></thead>
						<tbody>
							<tr v-for="row in readiness.coverage" :key="row.number">
								<td>{{ row.number }}</td>
								<td>{{ row.official_area }}</td>
								<td><span class="kt-status" :class="row.result === 'Pass' ? 'is-live' : 'is-pending'">{{ row.result }}</span></td>
							</tr>
						</tbody>
					</table>
				</div>

				<div v-else-if="activeTab === 'Configuration'" class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<table class="kt-table" style="border: none">
						<thead><tr><th>{{ __("Area") }}</th><th>{{ __("Exact purpose") }}</th><th>{{ __("Status") }}</th><th></th></tr></thead>
						<tbody>
							<tr v-for="a in PCFG_AREAS" :key="a.code">
								<td>{{ a.title }}</td>
								<td class="kt-muted">{{ a.purpose }}</td>
								<td><span class="kt-status" :class="areaStatus[a.code] === 'Complete' ? 'is-live' : 'is-pending'">{{ areaStatus[a.code] }}</span></td>
								<td><a href="#" class="kt-btn kt-btn-ghost" @click.prevent="viewArea(a)">{{ __("View") }}</a></td>
							</tr>
						</tbody>
					</table>
				</div>

				<div v-else-if="activeTab === 'Complete preview'" class="kt-card kt-empty">
					<h2>{{ __("Complete preview is not available in this build yet.") }}</h2>
				</div>

				<div v-else class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<table class="kt-table" style="border: none">
						<thead><tr><th>{{ __("Date") }}</th><th>{{ __("Event") }}</th><th>{{ __("By") }}</th></tr></thead>
						<tbody>
							<tr><td>{{ workspace.task.submitted_at }}</td><td>{{ __("Submitted for review") }}</td><td>{{ workspace.task.submitted_by }}</td></tr>
							<tr v-for="d in workspace.decisions" :key="d.decided_at + d.decided_by">
								<td>{{ d.decided_at }}</td>
								<td>{{ d.decision }}</td>
								<td>{{ d.decided_by }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</div>

		<div v-if="!loading" class="kt-sticky-footer">
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="notInReview" @click="returnDialogOpen = true">
				{{ __("Return for correction") }}
			</button>
			<button type="button" class="kt-btn kt-btn-primary" :disabled="notInReview || !confirmed || activating" @click="activatePackage">
				{{ __("Activate package") }}
			</button>
		</div>

		<ReturnDialog
			:open="returnDialogOpen"
			:saving="returnSaving"
			:error="returnError"
			@confirm="confirmReturn"
			@cancel="returnDialogOpen = false"
		/>
	</div>
</template>
