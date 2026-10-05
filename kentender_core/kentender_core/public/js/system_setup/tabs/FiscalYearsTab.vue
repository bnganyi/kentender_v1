<script setup>
// CFG-CHG-002 v0.14 §10.3–§10.4 (C02; tracker CFG14-5B) — the Financial
// years tab, re-ported class-for-class from design/C02-Financial-Years.dc.html:
// #overview (a plain table under the header row, not a card within the card),
// #overview-disabled, #narrow (one card per year below 700px), #empty,
// #detail (Submission periods for one year, with the row variants "No closing
// date" and "Closed at"), the Change history disclosure, and the open/close/
// deadline forms as an inline panel in the detail (D18). The add-year and
// disable boards are dialogs. Every action is IntakeControl-backed (§4.3)
// through the site_configuration commands; nothing here re-implements the
// one-open-year rule client-side.
import { computed, onMounted, reactive, ref, watch } from "vue";
import { onSetupRevalidate } from "../composables/useRouteState.js";
import AddFiscalYearDialog from "../components/AddFiscalYearDialog.vue";
import IntakeForm from "../components/IntakeForm.vue";
import DisableFiscalYearDialog from "../components/DisableFiscalYearDialog.vue";
import { siteConfigApi } from "../data/siteConfigApi.js";
import { toDatetimeLocal } from "../data/format.js";

const props = defineProps({
	subpath: { type: String, default: "" },
});
const emit = defineEmits(["changed", "navigate"]);

// §4.3 — the three registered module keys, in the artboard's own order.
// Row/history field names already carry these prefixes verbatim (the server
// projection is keyed the same way — see MODULE_FLAG_FIELDS).
const MODULE_ORDER = ["needs", "dpp", "disposal_plan"];
// §10.3 tables and rows use the plural activity names; the forms' own titles
// use §8's singular labels (IntakeForm).
const ACTIVITY_LABELS = { needs: "Departmental needs", dpp: "Departmental plans", disposal_plan: "Disposal plans" };
// §8's activity labels, which composed messages extend with "submissions".
const ACTIVITY_NAMES = { needs: "Departmental needs", dpp: "Departmental plan", disposal_plan: "Disposal plan" };
// IntakeDialog's own `purpose` prop predates the disposal-plan module and
// still calls the dpp variant "plan"; keep that one alias local to the call.
const DIALOG_PURPOSE = { needs: "needs", dpp: "plan", disposal_plan: "disposal_plan" };
const MODULE_OPS = {
	needs: { open: siteConfigApi.openNeedsSubmission, close: siteConfigApi.closeNeedsSubmission },
	dpp: { open: siteConfigApi.openDppSubmission, close: siteConfigApi.closeDppSubmission },
	disposal_plan: { open: siteConfigApi.openDisposalPlanSubmission, close: siteConfigApi.closeDisposalPlanSubmission },
};

const loading = ref(true);
const busy = ref(false);
const loadError = ref("");
const rows = ref([]);
const includeDisabled = ref(false);
const accountingOpen = ref(false);
const historyOpen = ref(false);
const history = ref(null);
const historyLoading = ref(false);
const enableBusy = ref(false);
const enableError = ref("");
const dialog = reactive({ kind: "", moduleKey: "", mode: "", row: null, error: "" });

const view = computed(() => {
	const [kind, ...rest] = (props.subpath || "").split("/");
	if (kind === "year" && rest.length) return { kind: "year", fiscalYear: rest.join("/") };
	return { kind: "list" };
});
const visibleRows = computed(() => rows.value.filter((row) => includeDisabled.value || !row.disabled));
const detailRow = computed(() => rows.value.find((row) => row.fiscal_year === view.value.fiscalYear) || null);

async function load({ quiet = false } = {}) {
	if (!quiet) loading.value = true;
	loadError.value = "";
	try {
		const result = await siteConfigApi.listFiscalYears();
		rows.value = result.fiscal_years;
	} catch (error) {
		loadError.value = error.message;
		rows.value = [];
	} finally {
		loading.value = false;
	}
}
onMounted(load);
// Kept alive by the root: a return to this tab re-reads the years in place.
onSetupRevalidate(load);

async function loadHistory(fiscalYear) {
	historyLoading.value = true;
	try {
		history.value = await siteConfigApi.listFiscalYearIntakeHistory(fiscalYear);
	} catch (error) {
		history.value = null;
	} finally {
		historyLoading.value = false;
	}
}
watch(
	() => (view.value.kind === "year" ? view.value.fiscalYear : ""),
	(fiscalYear) => {
		historyOpen.value = false;
		if (fiscalYear) loadHistory(fiscalYear);
	},
	{ immediate: true }
);

function openYear(fiscalYear) {
	emit("navigate", `year/${fiscalYear}`);
}

function openDialog(kind, row = null) {
	dialog.kind = kind;
	dialog.moduleKey = "";
	dialog.mode = "";
	dialog.row = row;
	dialog.error = "";
}
function closeDialog() {
	dialog.kind = "";
	dialog.moduleKey = "";
	dialog.mode = "";
	dialog.row = null;
	dialog.error = "";
}

async function run(action, { closeOnSuccess = true } = {}) {
	busy.value = true;
	dialog.error = "";
	try {
		await action();
		if (closeOnSuccess) closeDialog();
		await load({ quiet: true });
		if (view.value.kind === "year") await loadHistory(view.value.fiscalYear);
		emit("changed");
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}

async function refreshDialog() {
	await load({ quiet: true });
	if (view.value.kind === "year") await loadHistory(view.value.fiscalYear);
	closeDialog();
}

const addYear = (startYear) => run(() => siteConfigApi.addFiscalYear(startYear));

function openOpenDialog(moduleKey) {
	dialog.kind = "intake";
	dialog.moduleKey = moduleKey;
	dialog.mode = "open";
	dialog.row = detailRow.value;
	dialog.error = "";
}
function openCloseDialog(moduleKey) {
	dialog.kind = "intake";
	dialog.moduleKey = moduleKey;
	dialog.mode = "close";
	dialog.row = detailRow.value;
	dialog.error = "";
}
function openDeadlineDialog(moduleKey) {
	const row = detailRow.value;
	dialog.kind = "intake";
	dialog.moduleKey = moduleKey;
	dialog.mode = "deadline";
	dialog.row = { ...row, closes_at_local: toDatetimeLocal(row[`${moduleKey}_submission_closes_at`]) };
	dialog.error = "";
}
const replacesRow = computed(() => {
	if (dialog.kind !== "intake" || dialog.mode !== "open" || !dialog.row) return null;
	const other = rows.value.find((row) => row[`${dialog.moduleKey}_submission_open`]);
	return other && other.fiscal_year !== dialog.row.fiscal_year ? other : null;
});

function confirmIntake({ closes_at, reason }) {
	const { moduleKey, mode, row } = dialog;
	if (mode === "open") {
		return run(() => MODULE_OPS[moduleKey].open(row.fiscal_year, closes_at, reason, row.expected_version));
	}
	if (mode === "close") {
		return run(() => MODULE_OPS[moduleKey].close(row.fiscal_year, reason, row.expected_version));
	}
	return run(() =>
		siteConfigApi.updateIntakeCloseInstant(moduleKey, row.fiscal_year, closes_at, reason, row.expected_version)
	);
}

function openDisableDialog(row) {
	dialog.kind = "disable";
	dialog.moduleKey = "";
	dialog.mode = "";
	dialog.row = row;
	dialog.error = "";
}
const disableBlockers = computed(() => {
	const row = dialog.row;
	if (!row) return [];
	const blockers = [];
	for (const key of MODULE_ORDER) {
		if (row[`${key}_submission_open`]) {
			blockers.push(__("{0} submissions are still open.", [ACTIVITY_NAMES[key]]));
		}
	}
	if (row.reference_count) {
		blockers.push(__("{0} KenTender records reference this financial year.", [row.reference_count]));
	}
	return blockers;
});
function confirmDisable() {
	return run(() => siteConfigApi.setFiscalYearDisabled(dialog.row.fiscal_year, true, dialog.row.expected_version));
}
async function enableYear(row) {
	enableBusy.value = true;
	enableError.value = "";
	try {
		await siteConfigApi.setFiscalYearDisabled(row.fiscal_year, false, row.expected_version);
		await load({ quiet: true });
		emit("changed");
	} catch (error) {
		enableError.value = error.message;
	} finally {
		enableBusy.value = false;
	}
}

function openUomList() {
	frappe.set_route("List", "UOM");
}
</script>

<template>
	<section v-if="view.kind === 'list'" class="kt-setup-section is-flow" data-testid="kt-setup-fy">
		<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap">
			<div>
				<h3 style="margin-bottom:4px">{{ __("Financial years") }}</h3>
				<p class="card-body" style="margin-bottom:0">{{ __("Set when departments can submit needs and plans.") }}</p>
			</div>
			<button type="button" class="btn btn-primary" data-testid="kt-fy-add-open" @click="openDialog('add')">
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add financial year") }}
			</button>
		</div>

		<div v-if="loading" data-testid="kt-fy-loading" role="status" style="padding:24px 0">
			<div class="kt-skel" style="width:84%" />
			<div class="kt-skel" style="width:62%" />
		</div>

		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" style="margin-top:16px" data-testid="kt-fy-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("System setup could not be loaded.") }}</strong> {{ __("Try again. If the problem continues, contact support.") }}</div>
			<button type="button" class="btn btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>

		<!-- C02 #empty -->
		<div v-else-if="!rows.length" class="kt-fy-empty" data-testid="kt-fy-empty">
			<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-neutral-400)" stroke-width="1.5" aria-hidden="true" style="margin:0 auto 12px"><rect x="3" y="4" width="18" height="18" rx="0" /><path d="M16 2v4" /><path d="M8 2v4" /><path d="M3 10h18" /></svg>
			<p style="font-weight:600;margin-bottom:4px">{{ __("No financial years yet.") }}</p>
			<p class="card-body">{{ __("Add the first financial year for this site.") }}</p>
			<button type="button" class="btn btn-primary" @click="openDialog('add')">
				<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add financial year") }}
			</button>
		</div>

		<template v-else>
			<label class="kt-checkbox" style="margin:14px 0" data-testid="kt-fy-include-disabled">
				<input v-model="includeDisabled" type="checkbox">
				<span class="box" />{{ __("Include disabled years") }}
			</label>

			<div class="kt-table-scroll kt-fy-wide" data-testid="kt-fy-table">
				<table class="table">
					<thead>
						<tr>
							<th>{{ __("Financial year") }}</th>
							<th>{{ __("Period") }}</th>
							<th>{{ __("Phase") }}</th>
							<th v-for="key in MODULE_ORDER" :key="key">{{ ACTIVITY_LABELS[key] }}</th>
							<th>{{ __("Action") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in visibleRows" :key="row.fiscal_year" :data-testid="'kt-fy-row-' + row.fiscal_year">
							<td>
								{{ row.label }}
								<template v-if="row.disabled"><br><span class="tag tag-neutral">{{ __("Disabled") }}</span></template>
							</td>
							<td>{{ row.period_label }}</td>
							<td><span class="tag tag-neutral">{{ __(row.phase) }}</span></td>
							<td v-for="key in MODULE_ORDER" :key="key" :data-testid="'kt-fy-' + key + '-' + row.fiscal_year">
								<template v-if="row[key + '_submission_open']">
									<span class="kt-status is-live">{{ __("Open") }}</span>
									<template v-if="row[key + '_submission_closes_label']">
										<br><span class="text-muted" style="font-size:12px">{{ __("Closes at: {0}", [row[key + "_submission_closes_label"]]) }}</span>
									</template>
								</template>
								<span v-else class="kt-status is-critical">{{ __("Closed") }}</span>
							</td>
							<td>
								<a href="#" :data-testid="'kt-fy-detail-' + row.fiscal_year" @click.prevent="openYear(row.fiscal_year)">{{ __("Submission periods") }}</a>
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- C02 #narrow — one card per year, every activity and its deadline kept. -->
			<div class="kt-fy-narrow" data-testid="kt-fy-cards">
				<div v-for="row in visibleRows" :key="row.fiscal_year" class="card kt-fy-card" :data-testid="'kt-fy-card-' + row.fiscal_year">
					<div class="kt-meta-row">
						<div><span class="kt-label">{{ __("Year") }}</span><span class="kt-meta-value">{{ row.label }}</span></div>
						<div><span class="kt-label">{{ __("Period") }}</span><span class="kt-meta-value">{{ row.period_label }}</span></div>
						<div><span class="kt-label">{{ __("Phase") }}</span><span class="kt-meta-value"><span class="tag tag-neutral">{{ __(row.phase) }}</span></span></div>
					</div>
					<table class="table" style="margin-top:12px">
						<tbody>
							<tr v-for="key in MODULE_ORDER" :key="key" :data-testid="'kt-fy-card-' + key + '-' + row.fiscal_year">
								<td>{{ ACTIVITY_LABELS[key] }}</td>
								<td>
									<template v-if="row[key + '_submission_open']">
										<span class="kt-status is-live">{{ __("Open") }}</span>
										<template v-if="row[key + '_submission_closes_label']">
											<br><span class="text-muted" style="font-size:12px">{{ __("Closes at: {0}", [row[key + "_submission_closes_label"]]) }}</span>
										</template>
									</template>
									<span v-else class="kt-status is-critical">{{ __("Closed") }}</span>
								</td>
							</tr>
						</tbody>
					</table>
					<a href="#" style="display:block;margin-top:10px" @click.prevent="openYear(row.fiscal_year)">{{ __("Submission periods") }}</a>
				</div>
			</div>

			<p class="text-muted" style="font-size:13px;margin-top:12px">{{ __("Each activity can be open for one financial year at a time.") }}</p>
			<p class="text-muted" style="font-size:13px" data-testid="kt-fy-count">
				{{ rows.length === 1 ? __("1 financial year") : __("{0} financial years", [rows.length]) }}
			</p>

			<div class="kt-disclosure">
				<div
					class="kt-disclosure-head"
					role="button"
					tabindex="0"
					:aria-expanded="accountingOpen ? 'true' : 'false'"
					data-testid="kt-fy-accounting-toggle"
					@click="accountingOpen = !accountingOpen"
					@keydown.enter.prevent="accountingOpen = !accountingOpen"
					@keydown.space.prevent="accountingOpen = !accountingOpen"
				>
					<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ __("Shared accounting settings") }}</span></div>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': accountingOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
				</div>
				<div v-show="accountingOpen" class="kt-disclosure-body">
					<p class="card-body">{{ __("Financial years and units of measure are shared with accounting.") }}</p>
					<a href="#" data-testid="kt-fy-uom-link" @click.prevent="openUomList">{{ __("Manage units of measure") }}</a>
				</div>
			</div>
		</template>

		<AddFiscalYearDialog v-if="dialog.kind === 'add'" :busy="busy" :error="dialog.error" @confirm="addYear" @cancel="closeDialog" @view-year="(fy) => { closeDialog(); openYear(fy); }" />
	</section>

	<section v-else-if="view.kind === 'year' && detailRow" class="kt-setup-section" data-testid="kt-setup-fy-detail">
		<div data-testid="kt-setup-fy-detail-card">
			<h3>{{ __("Submission periods") }}</h3>
			<div class="kt-panel" style="margin-bottom:16px">
				<div class="kt-meta-row">
					<div><span class="kt-label">{{ __("Financial year") }}</span><span class="kt-meta-value">{{ detailRow.label }}</span></div>
					<div><span class="kt-label">{{ __("Period") }}</span><span class="kt-meta-value">{{ detailRow.period_label }}</span></div>
					<div><span class="kt-label">{{ __("Financial year enabled") }}</span><span class="kt-meta-value" data-testid="kt-fy-detail-enabled">{{ detailRow.disabled ? __("No") : __("Yes") }}</span></div>
				</div>
			</div>

			<div class="kt-table-scroll">
				<table class="table">
					<thead>
						<tr>
							<th>{{ __("Activity") }}</th>
							<th>{{ __("Status") }}</th>
							<th>{{ __("Closes at") }}</th>
							<th>{{ __("Actions") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="key in MODULE_ORDER" :key="key" :data-testid="'kt-fy-activity-' + key">
							<td>{{ ACTIVITY_LABELS[key] }}</td>
							<td>
								<span v-if="detailRow[key + '_submission_open']" class="kt-status is-live">{{ __("Open") }}</span>
								<span v-else class="kt-status is-critical">{{ __("Closed") }}</span>
							</td>
							<td :data-testid="'kt-fy-closes-' + key">
								<template v-if="detailRow[key + '_submission_open']">{{ detailRow[key + "_submission_closes_label"] || __("No closing date") }}</template>
								<template v-else-if="detailRow[key + '_submission_closed_at_label']">{{ __("Closed at: {0}", [detailRow[key + "_submission_closed_at_label"]]) }}</template>
								<template v-else>{{ __("Not set") }}</template>
							</td>
							<td>
								<template v-if="!detailRow.disabled">
									<template v-if="detailRow[key + '_submission_open']">
										<button type="button" class="btn btn-ghost" :data-testid="'kt-fy-deadline-' + key" @click="openDeadlineDialog(key)">{{ __("Change closing time") }}</button>
										{{ " " }}
										<button type="button" class="btn btn-secondary" :data-testid="'kt-fy-close-' + key" @click="openCloseDialog(key)">{{ __("Close submissions") }}</button>
									</template>
									<button v-else type="button" class="btn btn-secondary" :data-testid="'kt-fy-open-' + key" @click="openOpenDialog(key)">{{ __("Open submissions") }}</button>
								</template>
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- §10.4 — the focused form for the chosen action, in the detail it concerns (D18). -->
			<IntakeForm
				v-if="dialog.kind === 'intake' && dialog.row"
				:key="dialog.moduleKey + dialog.mode"
				style="margin-top:16px"
				:mode="dialog.mode"
				:purpose="DIALOG_PURPOSE[dialog.moduleKey]"
				:row="dialog.row"
				:replaces="replacesRow"
				:busy="busy"
				:error="dialog.error"
				@confirm="confirmIntake"
				@cancel="closeDialog"
				@refresh="refreshDialog"
			/>

			<!-- §10.3 — the year-level action, separate from submission actions. -->
			<div style="margin-top:16px">
				<button
					v-if="detailRow.disabled"
					type="button"
					class="btn btn-secondary"
					:disabled="enableBusy"
					data-testid="kt-fy-enable"
					@click="enableYear(detailRow)"
				>{{ __("Enable financial year") }}</button>
				<button v-else type="button" class="btn btn-secondary" data-testid="kt-fy-disable-open" @click="openDisableDialog(detailRow)">{{ __("Disable financial year") }}</button>
				<div v-if="enableError" class="kt-notice is-critical" role="alert" style="margin-top:8px">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ enableError }}</div>
				</div>
			</div>

			<div class="kt-disclosure" style="margin-top:16px">
				<div
					class="kt-disclosure-head"
					role="button"
					tabindex="0"
					:aria-expanded="historyOpen ? 'true' : 'false'"
					data-testid="kt-fy-history-toggle"
					@click="historyOpen = !historyOpen"
					@keydown.enter.prevent="historyOpen = !historyOpen"
					@keydown.space.prevent="historyOpen = !historyOpen"
				>
					<div class="kt-disclosure-title-row">
						<span class="kt-disclosure-title">{{ __("Change history") }}</span>
						<span class="tag tag-neutral">{{ history && history.count === 1 ? __("1 entry") : __("{0} entries", [history ? history.count : 0]) }}</span>
					</div>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': historyOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
				</div>
				<div v-show="historyOpen" class="kt-disclosure-body" data-testid="kt-fy-history-body">
					<p v-if="historyLoading" class="text-muted">{{ __("Loading…") }}</p>
					<div v-else-if="history && history.entries.length" class="kt-table-scroll">
						<table class="table">
							<thead>
								<tr>
									<th>{{ __("Activity") }}</th>
									<th>{{ __("Financial year") }}</th>
									<th>{{ __("Change") }}</th>
									<th>{{ __("Previous value") }}</th>
									<th>{{ __("New value") }}</th>
									<th>{{ __("Reason") }}</th>
									<th>{{ __("Changed by") }}</th>
									<th>{{ __("Changed at") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="(entry, index) in history.entries" :key="index">
									<td>{{ entry.activity }}</td>
									<td>{{ entry.financial_year }}</td>
									<td>{{ entry.change }}</td>
									<td>{{ entry.previous_value }}</td>
									<td>{{ entry.new_value }}</td>
									<td>{{ entry.reason || "—" }}</td>
									<td>{{ entry.changed_by }}</td>
									<td>{{ entry.changed_at }}</td>
								</tr>
							</tbody>
						</table>
					</div>
					<p v-if="history && history.entries.length && history.entries.length < history.count" class="text-muted" style="font-size:12px">
						{{ __("Showing the most recent {0} of {1} entries.", [history.entries.length, history.count]) }}
					</p>
					<p v-else-if="!(history && history.entries.length)" class="text-muted">{{ __("No changes recorded yet.") }}</p>
				</div>
			</div>
		</div>

		<DisableFiscalYearDialog
			v-if="dialog.kind === 'disable' && dialog.row"
			:row="dialog.row"
			:blockers="disableBlockers"
			:busy="busy"
			:error="dialog.error"
			@confirm="confirmDisable"
			@cancel="closeDialog"
		/>
	</section>

	<section v-else-if="loading" class="kt-setup-section" data-testid="kt-setup-fy-detail-loading">
		<div data-testid="kt-fy-loading" role="status" style="padding:24px 0">
			<div class="kt-skel" style="width:84%" />
			<div class="kt-skel" style="width:62%" />
		</div>
	</section>

	<section v-else class="kt-setup-section" data-testid="kt-setup-fy-detail-missing">
		<div class="kt-notice is-critical" role="alert">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("That financial year could not be found.") }}</strong> {{ __("It may have been removed.") }}</div>
		</div>
	</section>
</template>
