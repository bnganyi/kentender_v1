<script setup>
// CFG-CHG-002 v0.6 §10.3 + §11.3 — the Fiscal years tab (CFG-DES-03).
//
// Rows come ordered from the server with the phase derived there; the
// per-row action is Open OR Close, never both; the Manage-units link opens
// the standard ERPNext UOM list (KenTender renders no unit editor, §4.4).
import { computed, onMounted, reactive, ref } from "vue";
import AddFiscalYearDialog from "../components/AddFiscalYearDialog.vue";
import IntakeDialog from "../components/IntakeDialog.vue";
import { siteConfigApi } from "../data/siteConfigApi.js";

const emit = defineEmits(["changed"]);

const loading = ref(true);
const busy = ref(false);
const loadError = ref("");
const rows = ref([]);
const dialog = reactive({ kind: "", row: null, error: "" });

const openRow = computed(() => rows.value.find((row) => row.needs_submission_open) || null);

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

function openDialog(kind, row = null) {
	dialog.kind = kind;
	dialog.row = row;
	dialog.error = "";
}
function closeDialog() {
	dialog.kind = "";
	dialog.row = null;
	dialog.error = "";
}

async function run(action) {
	busy.value = true;
	dialog.error = "";
	try {
		await action();
		closeDialog();
		await load({ quiet: true });
		emit("changed");
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}

const addYear = (startYear) => run(() => siteConfigApi.addFiscalYear(startYear));
const openIntake = ({ closes_at, reason }) =>
	run(() =>
		siteConfigApi.openNeedsSubmission(
			dialog.row.fiscal_year, closes_at, reason, dialog.row.expected_version
		)
	);
const closeIntake = ({ reason }) =>
	run(() =>
		siteConfigApi.closeNeedsSubmission(
			dialog.row.fiscal_year, reason, dialog.row.expected_version
		)
	);

function openUomList() {
	frappe.set_route("List", "UOM");
}

function intakeLabel(row) {
	if (!row.needs_submission_open) return __("Closed");
	if (row.needs_submission_closes_label) {
		return __("Open until {0}", [row.needs_submission_closes_label]);
	}
	return __("Open");
}
</script>

<template>
	<section class="kt-setup-section" data-testid="kt-setup-fy">
		<div class="kt-section-head">
			<div>
				<h2 class="kt-section-title">{{ __("Financial years") }}</h2>
				<p class="kt-muted">
					{{ __("Financial years are shared with accounting. Needs submission may be open for one year at a time.") }}
				</p>
			</div>
			<button
				type="button"
				class="kt-btn kt-btn-primary"
				data-testid="kt-fy-add-open"
				@click="openDialog('add')"
			>{{ __("Add financial year") }}</button>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-fy-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<span class="kt-eyebrow">{{ __("Loading financial years…") }}</span>
			<div class="kt-skel" style="width:84%" />
			<div class="kt-skel" style="width:62%" />
		</div>

		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-fy-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("System setup could not be loaded") }}</h2>
			<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>

		<div v-else-if="!rows.length" class="kt-card kt-blueprint kt-empty" data-testid="kt-fy-empty">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("No financial years yet") }}</h2>
			<p>{{ __("Add the first financial year for this site.") }}</p>
			<button type="button" class="kt-btn kt-btn-primary" @click="openDialog('add')">
				{{ __("Add financial year") }}
			</button>
		</div>

		<div v-else class="kt-card kt-blueprint kt-table-card" data-testid="kt-fy-table">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-table-scroll">
				<table class="kt-table">
					<thead>
						<tr>
							<th>{{ __("Financial year") }}</th>
							<th>{{ __("Period") }}</th>
							<th>{{ __("Phase") }}</th>
							<th>{{ __("Needs submission") }}</th>
							<th>{{ __("Action") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in rows" :key="row.fiscal_year" :data-testid="'kt-fy-row-' + row.fiscal_year">
							<td class="kt-row-name">{{ row.label }}</td>
							<td>{{ row.period_label }}</td>
							<td>{{ row.phase }}</td>
							<td>
								<span v-if="row.needs_submission_open" class="kt-status is-live">{{ intakeLabel(row) }}</span>
								<span v-else class="kt-tag kt-tag-neutral">{{ __("Closed") }}</span>
							</td>
							<td>
								<a
									v-if="!row.needs_submission_open && !row.disabled"
									href="#"
									:data-testid="'kt-fy-open-' + row.fiscal_year"
									@click.prevent="openDialog('open', row)"
								>{{ __("Open needs submission") }}</a>
								<a
									v-else-if="row.needs_submission_open"
									href="#"
									:data-testid="'kt-fy-close-' + row.fiscal_year"
									@click.prevent="openDialog('close', row)"
								>{{ __("Close needs submission") }}</a>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
		<p v-if="!loading && !loadError && rows.length" class="kt-count">
			{{ rows.length === 1 ? __("1 financial year") : __("{0} financial years", [rows.length]) }}
		</p>

		<div class="kt-uom-link">
			<a href="#" data-testid="kt-fy-uom-link" @click.prevent="openUomList">{{ __("Manage units of measure") }}</a>
			<p class="kt-muted">{{ __("Units are shared with accounting and maintained in the standard units list.") }}</p>
		</div>

		<AddFiscalYearDialog
			v-if="dialog.kind === 'add'"
			:busy="busy"
			:error="dialog.error"
			@confirm="addYear"
			@cancel="closeDialog"
		/>
		<IntakeDialog
			v-if="dialog.kind === 'open' && dialog.row"
			mode="open"
			:row="dialog.row"
			:replaces="openRow && openRow.fiscal_year !== dialog.row.fiscal_year ? openRow : null"
			:busy="busy"
			:error="dialog.error"
			@confirm="openIntake"
			@cancel="closeDialog"
		/>
		<IntakeDialog
			v-if="dialog.kind === 'close' && dialog.row"
			mode="close"
			:row="dialog.row"
			:busy="busy"
			:error="dialog.error"
			@confirm="closeIntake"
			@cancel="closeDialog"
		/>
	</section>
</template>
