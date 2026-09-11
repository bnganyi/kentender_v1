<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { useFiscalYearFilter } from "../../budget_shared/composables/useFiscalYearFilter.js";
import { formatKes } from "../../budget_shared/data/formatKes.js";
import {
	getBudgetWorkspace,
	getBudgetVersionDraft,
	saveBudgetVersionDraft,
	getBudgetVersionLinesEditor,
	saveBudgetLinesDraft,
	submitBudgetVersion,
	listOrganisationUnits,
	listFundingSources,
} from "../data/budgetApi.js";

const { route, go } = useRouteState("budget-funding");

const budgetIdParam = computed(() => route.value[1]);
const isNew = computed(() => budgetIdParam.value === "new");
const versionNumberParam = computed(() => route.value[3]);
const versionKey = computed(() =>
	isNew.value || !versionNumberParam.value ? null : `${budgetIdParam.value}-V${versionNumberParam.value}`
);
const tab = computed(() => route.value[5] || "overview");

const loading = ref(true);
const notFound = ref(false);
const forbidden = ref(false);
const actingError = ref(null);
const saving = ref(false);
const submitting = ref(false);

// The inline banner (rendered from actingError below) is the durable,
// authoritative error state — it must survive a re-render and not rely on
// the user having seen a transient toast. The toast is a supplementary
// attention-getter (a muted inline banner alone is easy to miss when it
// appears above the fold without any layout shift drawing the eye to it),
// never the only signal — see AGENTS.md §6.10.
function setActingError(message) {
	actingError.value = message;
	frappe.show_alert({ message, indicator: "red" }, 7);
}

// --- "new" (pre-creation) state: resolve the Fiscal Year filter only, no
// version yet. One site is one Procuring Entity — the same local Fiscal
// Year filter as the Workspace screen (shared localStorage key, so arriving
// here from "Register approved budget" already carries the year picked
// there with no query-string plumbing).
const fyFilter = useFiscalYearFilter();
const newContext = ref(null); // get_budget_workspace(fy) response for the selected year

// --- existing version state ---
const draft = ref(null); // get_budget_version_draft response
const linesEditor = ref(null); // get_budget_version_lines_editor response
const linesLoaded = ref(false);
const orgUnits = ref([]);
const fundingSources = ref([]);

const isSuccessor = computed(() => !!draft.value?.based_on);
const title = computed(() => (isSuccessor.value ? __("Budget revision") : __("Register approved budget")));
const canEdit = computed(() => (isNew.value ? true : !!draft.value?.can_edit));

// usePageRail's watch() reads railTrail.value synchronously the moment it's
// called, so every computed railTrail's callback touches (title, draft,
// budgetIdParam) must already be declared above this point — a TDZ error
// otherwise (confirmed live: "Cannot access 'title' before initialization").
const railTrail = computed(() => {
	const items = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: __("Budget & Funding"), route: ["budget-funding"] },
	];
	if (draft.value?.budget) items.push({ label: draft.value.budget.code, route: ["budget-funding", budgetIdParam.value] });
	items.push({ label: isNew.value ? __("Register approved budget") : title.value });
	return items;
});
const railEl = ref(null);
// BUD-CHG-001 v1.3 Phase 4/7 — one site is one Procuring Entity: no global
// PE switcher on this rail any more.
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const form = reactive({
	approval_reference: "",
	approval_date: "",
	authorised_total: "",
	approval_document: "",
	approval_document_name: "",
	revision_type: "Transfer",
});

function resetFormFromDraft() {
	if (isNew.value) {
		form.approval_reference = "";
		form.approval_date = "";
		form.authorised_total = "";
		form.approval_document = "";
		form.approval_document_name = "";
		return;
	}
	if (!draft.value) return;
	form.approval_reference = draft.value.version.approval_reference || "";
	form.approval_date = draft.value.version.approval_date || "";
	form.authorised_total = draft.value.version.authorised_total || "";
	form.approval_document = draft.value.approval_document || "";
	form.approval_document_name = (draft.value.approval_document || "").split("/").pop();
	form.revision_type = draft.value.revision_type || "Transfer";
}

async function loadNewContext() {
	loading.value = true;
	try {
		await fyFilter.load();
		if (!fyFilter.selected.value) return; // the fiscal-year filter renders instead of the form
		await loadNewContextForSelected();
	} finally {
		loading.value = false;
	}
}

async function loadNewContextForSelected() {
	try {
		const ws = await getBudgetWorkspace(fyFilter.selected.value);
		if (!ws.can_register) {
			forbidden.value = true;
			return;
		}
		newContext.value = ws;
	} catch (e) {
		if (e.httpStatus === 403) forbidden.value = true;
		else actingError.value = e.message || String(e);
	}
}

async function onSelectNewFy(fy) {
	fyFilter.select(fy);
	if (!fy) {
		newContext.value = null;
		return;
	}
	loading.value = true;
	try {
		await loadNewContextForSelected();
	} finally {
		loading.value = false;
	}
}

// `quiet` refreshes in place — used after Save/Submit, which redisplay the
// same version's (now updated) draft rather than navigating away.
async function loadDraft(opts) {
	if (!versionKey.value) return;
	const quiet = !!(opts && opts.quiet === true);
	if (!quiet) loading.value = true;
	notFound.value = false;
	forbidden.value = false;
	try {
		const data = await getBudgetVersionDraft(versionKey.value);
		// KT-STD-001 §3A.2 — verdicts arrive as data, never as an HTTP error.
		if (data && data.outcome === "FORBIDDEN") {
			draft.value = null;
			forbidden.value = true;
			return;
		}
		if (data && data.outcome === "NOT_FOUND") {
			draft.value = null;
			notFound.value = true;
			return;
		}
		draft.value = data;
		resetFormFromDraft();
		orgUnits.value = (await listOrganisationUnits()).rows || [];
		// A direct load landing on the Budget Lines tab must still fetch it —
		// watch(tab) below only fires on a later client-side change.
		if (tab.value === "lines") loadLines();
	} catch (e) {
		if (e.httpStatus === 403) forbidden.value = true;
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else actingError.value = e.message || String(e);
	} finally {
		loading.value = false;
	}
}

async function loadLines() {
	if (!versionKey.value) return;
	linesEditor.value = await getBudgetVersionLinesEditor(versionKey.value);
	linesLoaded.value = true;
}

watch(tab, (t) => {
	if (t === "lines" && !linesLoaded.value) loadLines();
});

onMounted(async () => {
	fundingSources.value = (await listFundingSources()).rows || [];
	if (isNew.value) await loadNewContext();
	else await loadDraft();
});
watch(versionKey, (v, prev) => {
	if (v && v !== prev) loadDraft();
});

function switchTab(t) {
	go(budgetIdParam.value, "version", versionNumberParam.value, "edit", t);
}

function openFileUploader() {
	new frappe.ui.FileUploader({
		allow_multiple: false,
		restrictions: { max_number_of_files: 1 },
		on_success: (file) => {
			form.approval_document = file.file_url;
			form.approval_document_name = file.file_name || file.file_url.split("/").pop();
		},
	});
}

async function saveDraft() {
	saving.value = true;
	actingError.value = null;
	try {
		if (isNew.value) {
			const payload = {
				fiscal_year: fyFilter.selected.value,
				approval_reference: form.approval_reference,
				approval_date: form.approval_date,
				authorised_total: form.authorised_total,
				approval_document: form.approval_document,
			};
			const result = await saveBudgetVersionDraft(payload);
			if (!result.ok) {
				setActingError(Object.values(result.errors || {}).join(" ") || __("Could not save."));
				return;
			}
			frappe.show_alert({ message: __("Draft saved"), indicator: "green" });
			go(result.budget.code, "version", result.version.version_number, "edit");
			return;
		}
		const payload = {
			budget_version: versionKey.value,
			approval_reference: form.approval_reference,
			approval_date: form.approval_date,
			authorised_total: form.authorised_total,
			approval_document: form.approval_document,
			revision_type: isSuccessor.value ? form.revision_type : undefined,
			expected_modified: draft.value.version.modified,
		};
		const result = await saveBudgetVersionDraft(payload);
		if (!result.ok) {
			setActingError(Object.values(result.errors || {}).join(" ") || __("Could not save."));
			return;
		}
		if (linesLoaded.value) {
			const linesResult = await saveLinesOnly();
			if (linesResult === false) return;
		}
		frappe.show_alert({ message: __("Draft saved"), indicator: "green" });
		await loadDraft({ quiet: true });
	} catch (e) {
		setActingError(e.message || String(e));
	} finally {
		saving.value = false;
	}
}

async function saveLinesOnly() {
	const lines = linesEditor.value.rows
		.filter((r) => !r.identity_locked)
		.map((r) => ({
			budget_line: r.budget_line || undefined,
			title: r.title,
			owner_org_unit: r.owner_org_unit || "",
			funding_source: r.funding_source,
			approved_amount: r.approved_amount,
		}))
		.concat(
			linesEditor.value.rows
				.filter((r) => r.identity_locked)
				.map((r) => ({ budget_line: r.budget_line, title: r.title, owner_org_unit: r.owner_org_unit, funding_source: r.funding_source, approved_amount: r.approved_amount }))
		)
		.concat((linesEditor.value.removed || []).map((budget_line) => ({ budget_line, remove: true })));
	const result = await saveBudgetLinesDraft({ budget_version: versionKey.value, lines });
	if (!result.ok) {
		setActingError(Object.entries(result.errors || {})
			.map(([, v]) => v)
			.join(" ") || __("Could not save Budget Lines."));
		return false;
	}
	linesEditor.value.removed = [];
	await loadLines();
	return true;
}

function addLine() {
	linesEditor.value.rows.push({
		budget_line: null,
		budget_line_code: "",
		title: "",
		owner_org_unit: "",
		owner_org_unit_label: "",
		// The funding source <select> has no blank placeholder option (only
		// the real catalogue), so a browser renders its first option as
		// visually selected regardless of v-model's value — leaving
		// funding_source empty here reads as "already chosen" on screen but
		// fails save with "Funding source is required" (confirmed live).
		// Default to the first catalogue entry so the visible selection and
		// the bound value always agree.
		funding_source: fundingSources.value[0]?.id || "",
		approved_amount: 0,
		identity_locked: false,
		can_remove: true,
	});
}

function removeLine(row) {
	if (row.budget_line) {
		linesEditor.value.removed = linesEditor.value.removed || [];
		linesEditor.value.removed.push(row.budget_line);
	}
	linesEditor.value.rows = linesEditor.value.rows.filter((r) => r !== row);
}

async function submitForReview() {
	submitting.value = true;
	actingError.value = null;
	try {
		if (linesLoaded.value) {
			const ok = await saveLinesOnly();
			if (ok === false) return;
		}
		const result = await submitBudgetVersion(versionKey.value);
		if (!result.ok) {
			setActingError((result.blockers || []).map((b) => b.message).join(" ") || __("Not ready to submit."));
			return;
		}
		frappe.show_alert({ message: __("Submitted for review"), indicator: "green" });
		await loadDraft({ quiet: true });
	} catch (e) {
		setActingError(e.message || String(e));
	} finally {
		submitting.value = false;
	}
}

function cancel() {
	go();
}
</script>

<template>
	<div class="kt-industry kt-bud-editor">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div v-if="loading" class="kt-shell">
			<div class="kt-card kt-blueprint">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-skel" style="width: 240px; height: 20px"></div>
			</div>
		</div>
		<div v-else-if="notFound" class="kt-shell"><div class="kt-card kt-empty"><h2>{{ __("This budget version could not be found.") }}</h2></div></div>
		<div v-else-if="forbidden" class="kt-shell"><div class="kt-card kt-empty"><h2>{{ __("You do not have access to register or edit this budget.") }}</h2></div></div>

		<!-- BUD-DES-02 — pre-creation: no tabs, footer actions -->
		<template v-else-if="isNew">
			<!-- Fiscal Year filter (BUD-CHG-001 v1.3) — a fresh Budget can't be
			     registered without a selected year; never auto-picked. -->
			<div v-if="fyFilter.loading.value || !fyFilter.selected.value" class="kt-shell">
				<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px">
					<label class="kt-field-label" style="margin: 0" for="bud-new-fy">{{ __("Fiscal Year") }}</label>
					<select
						id="bud-new-fy"
						class="kt-input"
						style="width: auto; min-width: 160px"
						:disabled="fyFilter.loading.value"
						:value="fyFilter.selected.value"
						@change="onSelectNewFy($event.target.value)"
					>
						<option value="" disabled>{{ __("Select a fiscal year") }}</option>
						<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
					</select>
				</div>
				<div v-if="!fyFilter.loading.value" class="kt-card kt-blueprint kt-empty">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<h2>{{ __("Select a fiscal year to register its procurement budget.") }}</h2>
				</div>
			</div>
			<div v-else class="kt-shell" style="padding-bottom: 96px">
				<header style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px">
					<h1 style="margin: 0">{{ __("Register approved budget") }}</h1>
					<span class="kt-status is-draft">{{ __("Draft") }}</span>
				</header>

				<KtErrorBanner :message="actingError" style="margin-bottom: 16px" @dismiss="actingError = null" />

				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Budget context") }}</div>
					<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px">
						<div><label class="kt-field-label">{{ __("Budget reference") }}</label><div class="kt-field-static">{{ __("Not assigned") }}</div></div>
						<div><label class="kt-field-label">{{ __("Financial Year") }}</label><div class="kt-field-static">{{ newContext?.fiscal_year?.label || fyFilter.selected.value }}</div></div>
						<div><label class="kt-field-label">{{ __("Currency") }}</label><div class="kt-field-static">KES</div></div>
					</div>
				</div>

				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("External approval") }}</div>
					<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px">
						<div class="kt-field">
							<label>{{ __("Approval reference") }}</label>
							<input v-model="form.approval_reference" class="kt-input" type="text" />
						</div>
						<div class="kt-field">
							<label>{{ __("Approval date") }}</label>
							<input v-model="form.approval_date" class="kt-input" type="date" />
						</div>
						<div class="kt-field">
							<label>{{ __("Authorised total") }}</label>
							<div class="kt-input-prefix"><span class="prefix">KES</span><input v-model="form.authorised_total" type="number" min="0" /></div>
						</div>
						<div class="kt-field">
							<label>{{ __("Approval document") }}</label>
							<div class="kt-file-row" style="justify-content: space-between">
								<div style="display: flex; align-items: center; gap: 8px; overflow: hidden">
									<span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{ form.approval_document_name || __("No file attached") }}</span>
								</div>
								<button type="button" class="kt-btn kt-btn-ghost" style="flex: none; font-size: 13px" @click="openFileUploader">
									{{ form.approval_document ? __("Replace") : __("Upload") }}
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
			<div class="kt-sticky-footer">
				<button type="button" class="kt-btn kt-btn-secondary" @click="cancel">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" @click="saveDraft" data-testid="bud-editor-save-btn">{{ __("Save draft") }}</button>
			</div>
		</template>

		<!-- BUD-DES-03/14/15 — existing Draft (baseline or successor), tabbed -->
		<template v-else-if="draft">
			<div class="kt-shell">
				<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px">
					<div>
						<div class="kt-eyebrow" style="margin-bottom: 8px">{{ draft.budget.code }} · {{ __("VERSION {0}", [draft.version.version_number]) }}</div>
						<div style="display: flex; align-items: center; gap: 12px">
							<h1 style="margin: 0">{{ title }}</h1>
							<span class="kt-status" :class="draft.version.status === 'Draft' ? 'is-draft' : 'is-pending'">{{ draft.version.status }}</span>
						</div>
					</div>
					<div v-if="canEdit" style="display: flex; gap: 12px; flex: none; margin-top: 4px">
						<button type="button" class="kt-btn kt-btn-secondary" :disabled="saving" @click="saveDraft" data-testid="bud-editor-save-btn">{{ __("Save draft") }}</button>
						<button type="button" class="kt-btn kt-btn-primary" :disabled="submitting" @click="submitForReview" data-testid="bud-editor-submit-btn">{{ __("Submit for review") }}</button>
					</div>
				</div>

				<KtErrorBanner :message="actingError" style="margin-bottom: 16px" @dismiss="actingError = null" />

				<!-- §6 Return — the Approver's required reason, shown to the
				     Officer on the returned Draft until it is resubmitted. -->
				<div v-if="draft.returned" class="kt-card kt-blueprint" style="margin-bottom: 16px" role="status" data-testid="bud-editor-returned">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Returned for correction") }}</div>
					<p style="margin: 0 0 6px 0; font-size: 14px">{{ draft.returned.reason }}</p>
					<div class="kt-muted" style="font-size: 13px">{{ __("Returned by {0}, {1}", [draft.returned.by, draft.returned.at]) }}</div>
				</div>

				<div class="kt-tabs">
					<div class="kt-tab" :aria-selected="tab === 'overview'" @click="switchTab('overview')" data-testid="bud-editor-tab-overview">{{ __("Overview") }}</div>
					<div class="kt-tab" :aria-selected="tab === 'lines'" @click="switchTab('lines')" data-testid="bud-editor-tab-lines">{{ __("Budget Lines") }}</div>
				</div>

				<template v-if="tab === 'overview'">
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title">{{ isSuccessor ? __("Version context") : __("Budget context") }}</div>
						<div :style="{ display: 'grid', gridTemplateColumns: isSuccessor ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)', gap: '20px' }">
							<div v-if="!isSuccessor"><label class="kt-field-label">{{ __("Budget reference") }}</label><div class="kt-field-static">{{ draft.budget.code }}</div></div>
							<div><label class="kt-field-label">{{ __("Financial Year") }}</label><div class="kt-field-static">{{ draft.budget.fiscal_year.label }}</div></div>
							<div><label class="kt-field-label">{{ __("Currency") }}</label><div class="kt-field-static">{{ draft.budget.currency }}</div></div>
							<template v-if="isSuccessor">
								<div><label class="kt-field-label">{{ __("Based on") }}</label><div class="kt-field-static">{{ __("Active Version {0}", [draft.based_on.version_number]) }}</div></div>
								<div class="kt-field">
									<label>{{ __("Revision type") }}</label>
									<select v-model="form.revision_type" class="kt-input" :disabled="!canEdit">
										<option>Supplementary allocation</option>
										<option>Reduction</option>
										<option>Transfer</option>
										<option>Correction</option>
									</select>
								</div>
							</template>
						</div>
					</div>

					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title">{{ __("External approval") }}</div>
						<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px">
							<div class="kt-field">
								<label>{{ __("Approval reference") }}</label>
								<input v-model="form.approval_reference" class="kt-input" type="text" :disabled="!canEdit" />
							</div>
							<div class="kt-field">
								<label>{{ __("Approval date") }}</label>
								<input v-model="form.approval_date" class="kt-input" type="date" :disabled="!canEdit" />
							</div>
							<div class="kt-field">
								<label>{{ __("Authorised total") }}</label>
								<div class="kt-input-prefix"><span class="prefix">KES</span><input v-model="form.authorised_total" type="number" min="0" :disabled="!canEdit" /></div>
							</div>
							<div class="kt-field">
								<label>{{ __("Approval document") }}</label>
								<div class="kt-file-row" style="justify-content: space-between">
									<div style="display: flex; align-items: center; gap: 8px; overflow: hidden">
										<span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{ form.approval_document_name || __("No file attached") }}</span>
									</div>
									<button v-if="canEdit" type="button" class="kt-btn kt-btn-ghost" style="flex: none; font-size: 13px" @click="openFileUploader">
										{{ form.approval_document ? __("Replace") : __("Upload") }}
									</button>
								</div>
							</div>
						</div>
					</div>
				</template>

				<template v-else-if="linesEditor">
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px">
							<div><div class="kt-eyebrow">{{ __("Authorised total") }}</div><div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 20px">{{ formatKes(linesEditor.totals.authorised_total, draft.budget.currency) }}</div></div>
							<div><div class="kt-eyebrow">{{ __("Budget Line total") }}</div><div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 20px">{{ formatKes(linesEditor.totals.line_total, draft.budget.currency) }}</div></div>
							<div><div class="kt-eyebrow">{{ __("Difference") }}</div><div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 20px">{{ formatKes(linesEditor.totals.difference, draft.budget.currency) }}</div></div>
						</div>
					</div>

					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<table class="kt-table" data-testid="bud-editor-lines-table">
							<thead>
								<tr>
									<th>{{ __("Budget Line") }}</th>
									<th>{{ __("Line title") }}</th>
									<th>{{ __("Owner scope") }}</th>
									<th>{{ __("Funding source") }}</th>
									<th v-if="linesEditor.is_successor" style="text-align: right">{{ __("Active amount") }}</th>
									<th style="text-align: right">{{ linesEditor.is_successor ? __("Proposed amount") : __("Approved amount") }}</th>
									<th v-if="linesEditor.is_successor" style="text-align: right">{{ __("Change") }}</th>
									<th v-else></th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="row in linesEditor.rows" :key="row.budget_line || row">
									<td class="kt-muted" style="white-space: nowrap">{{ row.budget_line_code || "—" }}</td>
									<td>
										<input v-if="canEdit && !row.identity_locked" v-model="row.title" class="kt-input" />
										<span v-else>{{ row.title }}</span>
									</td>
									<td>
										<select v-if="canEdit && !row.identity_locked" v-model="row.owner_org_unit" class="kt-input">
											<option value="">{{ __("Entity-wide") }}</option>
											<option v-for="o in orgUnits" :key="o.id" :value="o.id">{{ o.label }}</option>
										</select>
										<span v-else>{{ row.owner_org_unit_label || __("Entity-wide") }}</span>
									</td>
									<td>
										<select v-if="canEdit && !row.identity_locked" v-model="row.funding_source" class="kt-input">
											<option v-for="f in fundingSources" :key="f.id" :value="f.id">{{ f.label }}</option>
										</select>
										<span v-else>{{ row.funding_source }}</span>
									</td>
									<td v-if="linesEditor.is_successor" style="text-align: right">{{ formatKes(row.active_amount, draft.budget.currency) }}</td>
									<td style="text-align: right">
										<div v-if="canEdit" class="kt-input-prefix"><span class="prefix">KES</span><input v-model="row.approved_amount" type="number" min="0" style="text-align: right" /></div>
										<span v-else>{{ formatKes(row.approved_amount, draft.budget.currency) }}</span>
									</td>
									<td v-if="linesEditor.is_successor" style="text-align: right" :style="{ color: row.change < 0 ? '#b91c1c' : row.change > 0 ? '#047857' : undefined, fontWeight: 500 }">
										{{ row.change === 0 ? formatKes(0, draft.budget.currency) : (row.change > 0 ? "+ " : "− ") + formatKes(Math.abs(row.change), draft.budget.currency) }}
									</td>
									<td v-else style="white-space: nowrap">
										<button v-if="canEdit && row.can_remove" type="button" class="btn-danger-outline" @click="removeLine(row)">{{ __("Remove") }}</button>
									</td>
								</tr>
							</tbody>
						</table>
						<button v-if="canEdit" type="button" class="kt-btn kt-btn-secondary" style="align-self: flex-start" @click="addLine" data-testid="bud-editor-add-line-btn">{{ __("Add Budget Line") }}</button>
					</div>
				</template>
			</div>
		</template>
	</div>
</template>

<style scoped>
/* Page-local field chrome ported from the BUD-DES-02/03/14/15 artboards'
   own <style> blocks — not part of kt_industry_tokens.css's shared
   vocabulary (AGENTS.md §6.6: scoped styles are the correct home for
   page-specific chrome, not a token-file fork). */
.kt-bud-editor .kt-field-label {
	font-size: 12px;
	margin-bottom: 5px;
	color: color-mix(in srgb, var(--kt-color-text) 70%, transparent);
	display: block;
}
.kt-bud-editor .kt-field-static {
	min-height: 36px;
	padding: 6px 10px;
	font-size: 14px;
	display: flex;
	align-items: center;
	background: var(--kt-color-surface);
	border: 1px solid var(--kt-color-divider);
	border-radius: var(--kt-radius-md);
	color: color-mix(in srgb, var(--kt-color-text) 85%, transparent);
}
.kt-bud-editor .kt-input-prefix {
	min-height: 36px;
	padding: 6px 10px;
	font-size: 14px;
	display: flex;
	align-items: center;
	gap: 6px;
	background: var(--kt-color-surface);
	border: 1px solid var(--kt-color-divider);
	border-radius: var(--kt-radius-md);
}
.kt-bud-editor .kt-input-prefix span.prefix {
	color: color-mix(in srgb, var(--kt-color-text) 55%, transparent);
}
.kt-bud-editor .kt-input-prefix input {
	border: none;
	background: transparent;
	padding: 0;
	min-height: auto;
	width: 100%;
}
.kt-bud-editor .kt-file-row {
	min-height: 36px;
	padding: 6px 10px;
	font-size: 14px;
	display: flex;
	align-items: center;
	gap: 8px;
	background: var(--kt-color-surface);
	border: 1px solid var(--kt-color-divider);
	border-radius: var(--kt-radius-md);
}
.kt-bud-editor .btn-danger-outline {
	border: 1px solid color-mix(in srgb, #b91c1c 55%, transparent);
	color: #b91c1c;
	background: transparent;
	font-size: 13px;
	padding: 5px 10px;
	border-radius: var(--kt-radius-md);
	cursor: pointer;
}
.kt-bud-editor .btn-danger-outline:hover {
	background: color-mix(in srgb, #b91c1c 8%, transparent);
}
</style>
