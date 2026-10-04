<script setup>
// STD-WF-01 — Coverage and Readiness Report (§15.16). Real readiness engine
// output (std_coverage.readiness_report via get_std_readiness_report) — no
// fabricated summary numbers.
import { ref, computed, onMounted } from "vue";
import { useRouteState } from "../std_configuration_shared/composables/useRouteState.js";
import { usePageRail } from "../std_configuration_shared/composables/usePageRail.js";

const { route } = useRouteState("std-cfg-readiness");
const draftId = computed(() => route.value[1]);

const railEl = ref(null);
const draft = ref(null);
const readiness = ref(null);
const loading = ref(true);
const error = ref(null);

async function refresh() {
	loading.value = true;
	error.value = null;
	try {
		draft.value = await frappe.db.get_doc("STD Cfg Draft", draftId.value);
		readiness.value = await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.get_std_readiness_report",
			{ reference_doctype: "STD Cfg Draft", reference_name: draftId.value }
		);
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
	{ label: draft.value ? draft.value.package_id : "", route: draft.value ? ["std-cfg-package-home", draft.value.package_id] : [] },
	{ label: __("Coverage and Readiness") },
]);
usePageRail(railEl, railTrail);

const isReady = computed(() => readiness.value && readiness.value.coverage_pass_count === readiness.value.coverage.length && readiness.value.blocking_count === 0);

function backToPackage() {
	frappe.set_route("std-cfg-package-home", draft.value.package_id);
}
function openArea(row) {
	const code = `PCFG-${String(row.number <= 9 ? row.number : 9).padStart(2, "0")}`;
	frappe.set_route("std-cfg-area", "draft", draftId.value, code);
}

const submitting = ref(false);
async function submitForReview() {
	submitting.value = true;
	try {
		const reviewers = await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.list_std_reviewers"
		);
		if (!reviewers.length) {
			frappe.show_alert({ message: __("No STD Reviewer is available."), indicator: "red" });
			return;
		}
		await frappe.xcall(
			"kentender_procurement.std_configuration.api.std_configuration_api.submit_std_for_review",
			{ draft_name: draftId.value, reviewer: reviewers[0].name, expected_record_version: draft.value.record_version }
		);
		frappe.show_alert({ message: __("Submitted for review"), indicator: "green" });
		backToPackage();
	} finally {
		submitting.value = false;
	}
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" style="padding-bottom: 88px">
			<div v-if="error" class="kt-card kt-empty">
				<h2>{{ __("Could not load coverage and readiness.") }}</h2>
				<p>{{ error.message }}</p>
			</div>
			<div v-else-if="loading" class="kt-card kt-blueprint">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div v-for="i in 3" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
			</div>
			<template v-else>
				<header style="display: flex; justify-content: space-between; align-items: flex-end; gap: 16px">
					<div>
						<h1 style="font-size: 28px">{{ __("Coverage and Readiness") }}</h1>
						<p class="kt-muted" style="margin: 4px 0 0">
							{{ __("Draft Version") }} {{ draft.proposed_version_number }}
							<span class="kt-status" :class="isReady ? 'is-live' : 'is-pending'" style="margin-left: 8px">
								{{ isReady ? __("Ready for review") : __("Incomplete") }}
							</span>
						</p>
					</div>
				</header>

				<div v-if="isReady" class="kt-card" style="padding: 14px 18px; margin-bottom: 20px; background: color-mix(in srgb, #10b981 10%, transparent); border-color: color-mix(in srgb, #10b981 33%, transparent)">
					{{ __("All sixteen STD areas are covered and the package has no blocking findings.") }}
				</div>

				<div class="kt-card kt-blueprint" style="display: grid; grid-template-columns: repeat(3, 1fr); margin-bottom: 24px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div style="text-align: center; padding: 14px">
						<div style="font-size: 26px; font-weight: 600">{{ readiness.coverage_pass_count }} {{ __("of") }} {{ readiness.coverage.length }}</div>
						<div class="kt-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em">{{ __("Coverage") }}</div>
					</div>
					<div style="text-align: center; padding: 14px">
						<div style="font-size: 26px; font-weight: 600">{{ readiness.blocking_count }}</div>
						<div class="kt-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em">{{ __("Blocking") }}</div>
					</div>
					<div style="text-align: center; padding: 14px">
						<div style="font-size: 26px; font-weight: 600">{{ readiness.warning_count }}</div>
						<div class="kt-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em">{{ __("Warnings") }}</div>
					</div>
				</div>

				<div class="kt-card kt-blueprint" style="margin-bottom: 20px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<table class="kt-table" style="border: none">
						<thead>
							<tr><th>{{ __("No.") }}</th><th>{{ __("STD area") }}</th><th>{{ __("Result") }}</th><th></th></tr>
						</thead>
						<tbody>
							<tr v-for="row in readiness.coverage" :key="row.number">
								<td>{{ row.number }}</td>
								<td>{{ row.official_area }}</td>
								<td><span class="kt-status" :class="row.result === 'Pass' ? 'is-live' : 'is-pending'">{{ row.result }}</span></td>
								<td><a href="#" class="kt-btn kt-btn-ghost" @click.prevent="openArea(row)">{{ __("View area") }}</a></td>
							</tr>
						</tbody>
					</table>
				</div>

				<template v-if="readiness.warnings.length">
					<div class="kt-card-title">{{ __("Warnings") }}</div>
					<div class="kt-card kt-blueprint" style="margin-bottom: 16px">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<table class="kt-table" style="border: none">
							<thead>
								<tr><th>{{ __("Area") }}</th><th>{{ __("Warning") }}</th><th></th></tr>
							</thead>
							<tbody>
								<tr v-for="w in readiness.warnings" :key="w.code + w.message">
									<td>{{ w.owning_area }}</td>
									<td>{{ w.message }}</td>
									<td><a href="#" class="kt-btn kt-btn-ghost" @click.prevent="frappe.set_route('std-cfg-area', 'draft', draftId, w.owning_area)">{{ __("Open") }} {{ w.owning_area }}</a></td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>

				<div class="kt-sticky-footer" style="justify-content: space-between">
					<button type="button" class="kt-btn kt-btn-ghost" @click="backToPackage">{{ __("Back to package") }}</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="submitting" @click="submitForReview">{{ __("Submit for review") }}</button>
				</div>
			</template>
		</div>
	</div>
</template>
