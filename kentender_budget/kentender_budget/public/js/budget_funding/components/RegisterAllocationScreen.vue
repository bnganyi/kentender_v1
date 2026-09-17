<script setup>
import { ref, reactive, computed, onMounted, onActivated, watch } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { useFiscalYearFilter } from "../../budget_shared/composables/useFiscalYearFilter.js";
import { mintKey } from "../../budget_shared/data/formatKes.js";
import { getBudgetWorkspace, saveBudgetVersionDraft } from "../data/budgetApi.js";

// BUD-UI-02 pre-creation — BUD-DES-02 Record approved allocation (BUD-CHG-001
// v1.9 §9.3, §11.2, §12.2). Save and add budget lines creates the Budget and
// its Draft once; the four approval details, the explicit year and the
// verified currency are required before that first save. Tracker D3: this
// is its own screen, not the editor with a "new" branch.
const { go, epoch } = useRouteState("budget-funding");

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: __("Record approved allocation") },
]);
const railEl = ref(null);
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const fyFilter = useFiscalYearFilter();
const guard = kentender_core.desk_page.createSequenceGuard();
const loading = ref(true);
const forbidden = ref(null);
const serverError = ref(false);
const context = ref(null);
const existing = ref(null); // BUDGET_ALREADY_EXISTS → the authorised existing route
const savedButLost = ref(null); // save confirmed, navigation failed → Open saved draft
const actingError = ref(null);
const fieldErrors = ref({});

const form = reactive({ approval_reference: "", approval_date: "", authorised_total: "", approval_document: "", approval_document_name: "" });
const uploadState = ref("none"); // none | uploading | attached | failed

async function loadContext() {
	const token = guard.next();
	loading.value = true;
	forbidden.value = null;
	serverError.value = false;
	existing.value = null;
	try {
		// KT-STD-001 §3A — resolve access before the year selector or any
		// field paints: the workspace read answers Forbidden with or without a year.
		await fyFilter.load();
		const ws = await getBudgetWorkspace(fyFilter.selected.value || "");
		if (!guard.isCurrent(token)) return;
		if (ws && ws.outcome === "FORBIDDEN") {
			forbidden.value = ws.forbidden;
			return;
		}
		if (!fyFilter.selected.value) return;
		context.value = ws;
		if (ws.has_budget) {
			existing.value = ws;
		} else if (!ws.can_register) {
			forbidden.value = {
				heading: __("You do not have access to record an allocation"),
				text: __("Recording an allocation needs the Budget Officer responsibility. Ask your KenTender administrator to assign it in System setup."),
			};
		}
	} catch (e) {
		if (guard.isCurrent(token)) serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) loading.value = false;
	}
}

onMounted(loadContext);
let activations = 0;
onActivated(() => {
	if (activations++ === 0) return;
	loadContext();
});
watch(epoch, () => loadContext());

async function onSelectFy(fy) {
	fyFilter.select(fy);
	if (fy) await loadContext();
}

function openFileUploader() {
	uploadState.value = "uploading";
	new frappe.ui.FileUploader({
		allow_multiple: false,
		restrictions: { max_number_of_files: 1 },
		on_success: (file) => {
			form.approval_document = file.file_url;
			form.approval_document_name = file.file_name || file.file_url.split("/").pop();
			uploadState.value = "attached";
			delete fieldErrors.value.approval_document;
		},
	});
	// The uploader closes silently on cancel; treat "no file" as not attached, never as attached.
	setTimeout(() => {
		if (uploadState.value === "uploading" && !form.approval_document) uploadState.value = "none";
	}, 60000);
}

const runner = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{
		onStart: () => {
			actingError.value = null;
			fieldErrors.value = {};
		},
		onError: (e) => {
			actingError.value = (e && e.message) || __("We could not confirm the result. Checking the existing request…");
		},
		mintKey: (label) => mintKey(label),
	}
);
const saving = runner.pending;

// §9.3 Save and add budget lines — one create; a duplicate-year result opens
// the existing record instead; a confirmed save whose navigation fails offers
// Open saved draft rather than a second registration.
function saveAndAddLines() {
	return runner.run(async (key) => {
		const payload = {
			fiscal_year: fyFilter.selected.value,
			approval_reference: form.approval_reference,
			approval_date: form.approval_date,
			authorised_total: form.authorised_total,
			approval_document: form.approval_document,
			idempotency_key: key,
		};
		const result = await saveBudgetVersionDraft(payload);
		if (!result.ok) {
			if (result.code === "BUDGET_ALREADY_EXISTS") {
				existing.value = result;
				return;
			}
			fieldErrors.value = result.errors || {};
			actingError.value = Object.values(result.errors || {}).join(" ") || __("Could not save.");
			return;
		}
		try {
			go(result.budget.code, "version", String(result.version.version_number), "edit", "lines");
		} catch (e) {
			savedButLost.value = result;
		}
	}, "record");
}

function openExisting() {
	const route = existing.value?.route;
	if (route) go(...route.slice(1));
	else if (existing.value?.budget?.code) go(existing.value.budget.code);
}
function cancel() {
	go();
}
</script>

<template>
	<div class="kt-industry" data-testid="bud-reg" :data-loading="loading ? 'true' : 'false'" data-refreshing="false">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div v-if="loading" class="kt-shell">
			<div class="kt-card kt-blueprint"><div class="kt-skel" style="width: 240px; height: 20px"></div></div>
		</div>

		<div v-else-if="forbidden" class="kt-shell">
			<div class="kt-card kt-blueprint kt-empty" data-testid="bud-reg-forbidden">
				<h2>{{ __(forbidden.heading) }}</h2>
				<p class="kt-muted">{{ __(forbidden.text) }}</p>
			</div>
		</div>

		<div v-else-if="serverError" class="kt-shell">
			<div class="kt-card kt-blueprint kt-empty">
				<h2>{{ __("Budget & Funding could not be loaded.") }}</h2>
				<p class="kt-muted">{{ __("Try again. If the problem continues, contact KenTender support.") }}</p>
				<button type="button" class="kt-btn kt-btn-primary" @click="loadContext">{{ __("Try again") }}</button>
			</div>
		</div>

		<!-- The explicit target year is chosen before anything is written (§11.2). -->
		<div v-else-if="!fyFilter.selected.value" class="kt-shell">
			<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px">
				<label class="kt-label" style="margin: 0" for="bud-new-fy">{{ __("Financial year") }}</label>
				<select id="bud-new-fy" class="kt-input" style="width: auto; min-width: 160px" :value="fyFilter.selected.value" data-testid="bud-reg-fy" @change="onSelectFy($event.target.value)">
					<option value="" disabled>{{ __("Select a financial year") }}</option>
					<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
				</select>
			</div>
			<div class="kt-card kt-blueprint kt-empty"><h2>{{ __("Select the financial year whose approved allocation you are recording.") }}</h2></div>
		</div>

		<!-- §13 BUDGET_ALREADY_EXISTS — never a second registration. -->
		<div v-else-if="existing" class="kt-shell">
			<div class="kt-card kt-blueprint kt-empty" data-testid="bud-reg-exists">
				<h2>{{ __("An allocation record already exists for FY {0}.", [fyFilter.selected.value]) }}</h2>
				<p class="kt-muted">{{ __("Open it to continue.") }}</p>
				<div style="display: flex; gap: 12px; justify-content: center">
					<button type="button" class="kt-btn kt-btn-secondary" @click="cancel">{{ __("Back to Budget & Funding") }}</button>
					<button type="button" class="kt-btn kt-btn-primary" data-testid="bud-reg-open-existing" @click="openExisting">{{ __("Open existing record") }}</button>
				</div>
			</div>
		</div>

		<template v-else>
			<div class="kt-shell" style="max-width: 760px; padding-bottom: 96px">
				<header style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px">
					<h1 style="margin: 0">{{ __("Record approved allocation") }}</h1>
					<span class="kt-status is-draft">{{ __("Draft") }}</span>
				</header>
				<p class="kt-page-lede" style="margin: 0 0 24px">{{ __("Enter the allocation approved outside KenTender and attach its approval document.") }}</p>

				<KtErrorBanner :message="actingError" style="margin-bottom: 16px" @dismiss="actingError = null" />

				<div v-if="savedButLost" class="kt-notice is-warning" style="margin-bottom: 16px" data-testid="bud-reg-saved-lost">
					<div class="kt-notice-body">
						<strong>{{ __("Your allocation was saved.") }}</strong> {{ __("The next screen could not be opened.") }}
						<a href="#" @click.prevent="go(savedButLost.budget.code, 'version', String(savedButLost.version.version_number), 'edit', 'lines')">{{ __("Open saved draft") }}</a>
					</div>
				</div>

				<div class="kt-card kt-blueprint">
					<h3 class="kt-card-title">{{ __("Budget context") }}</h3>
					<div class="kt-grid-2" style="gap: 16px">
						<div class="kt-field">
							<label for="bud-reg-year">{{ __("Financial Year") }}</label>
							<select id="bud-reg-year" class="kt-input" :value="fyFilter.selected.value" data-testid="bud-reg-fy" @change="onSelectFy($event.target.value)">
								<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
							</select>
							<p class="kt-field-hint">{{ __("The year becomes fixed once the allocation is saved.") }}</p>
						</div>
						<div class="kt-field">
							<label>{{ __("Currency") }}</label>
							<input class="kt-input" type="text" value="KES" disabled data-testid="bud-reg-currency" />
						</div>
					</div>
				</div>

				<div class="kt-card kt-blueprint">
					<h3 class="kt-card-title">{{ __("External approval") }}</h3>
					<div class="kt-grid-2" style="gap: 16px">
						<div class="kt-field">
							<label for="bud-reg-ref">{{ __("Approval reference") }}</label>
							<input id="bud-reg-ref" v-model="form.approval_reference" class="kt-input" type="text" data-testid="bud-reg-approval-ref" />
							<p v-if="fieldErrors.approval_reference" class="kt-field-error">{{ fieldErrors.approval_reference }}</p>
						</div>
						<div class="kt-field">
							<label for="bud-reg-date">{{ __("Approval date") }}</label>
							<input id="bud-reg-date" v-model="form.approval_date" class="kt-input" type="date" data-testid="bud-reg-approval-date" />
							<p v-if="fieldErrors.approval_date" class="kt-field-error">{{ fieldErrors.approval_date }}</p>
						</div>
						<div class="kt-field">
							<label for="bud-reg-total">{{ __("Approved allocation") }}</label>
							<div class="kt-input-prefix"><span class="prefix">KES</span><input id="bud-reg-total" v-model="form.authorised_total" type="number" min="0" data-testid="bud-reg-approved-allocation" /></div>
							<p v-if="fieldErrors.authorised_total" class="kt-field-error">{{ fieldErrors.authorised_total }}</p>
						</div>
						<div class="kt-field">
							<label>{{ __("Approval document") }}</label>
							<div class="kt-file-row" style="justify-content: space-between">
								<span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis" data-testid="bud-reg-document-name">{{ form.approval_document_name || __("No file attached") }}</span>
								<button type="button" class="kt-btn kt-btn-ghost" style="flex: none; font-size: 13px" data-testid="bud-reg-upload-btn" @click="openFileUploader">
									{{ form.approval_document ? __("Replace") : __("Attach") }}
								</button>
							</div>
							<p v-if="fieldErrors.approval_document" class="kt-field-error">{{ fieldErrors.approval_document }}</p>
							<p v-else class="kt-field-hint">{{ __("Exactly one approval document. It is required before the allocation is saved.") }}</p>
						</div>
					</div>
				</div>
			</div>
			<div class="kt-sticky-footer">
				<button type="button" class="kt-btn kt-btn-secondary" @click="cancel">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" data-testid="bud-reg-save-btn" @click="saveAndAddLines">{{ __("Save and add budget lines") }}</button>
			</div>
		</template>
	</div>
</template>

<style scoped>
.kt-input-prefix { min-height: 36px; padding: 6px 10px; font-size: 14px; display: flex; align-items: center; gap: 6px; background: var(--kt-color-surface); border: 1px solid var(--kt-color-divider); }
.kt-input-prefix span.prefix { color: var(--kt-color-neutral-700); }
.kt-input-prefix input { border: none; background: transparent; padding: 0; min-height: auto; width: 100%; }
.kt-file-row { min-height: 36px; padding: 6px 10px; font-size: 14px; display: flex; align-items: center; gap: 8px; background: var(--kt-color-surface); border: 1px solid var(--kt-color-divider); }
</style>
