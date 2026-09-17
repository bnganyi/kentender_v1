<script setup>
import { ref, reactive, computed, watch, onMounted, onActivated, nextTick } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatKes, formatSignedKes, mintKey } from "../../budget_shared/data/formatKes.js";
import {
	getBudgetVersionDraft,
	saveBudgetVersionDraft,
	getBudgetVersionLinesEditor,
	saveBudgetLinesDraft,
	submitBudgetVersion,
	listOrganisationUnits,
	listFundingSources,
} from "../data/budgetApi.js";

// BUD-UI-02 — BUD-DES-03 (initial Draft lines) and BUD-DES-14/15 (successor
// Draft): Approval details and Budget lines as two named save scopes, one
// Submit for review that saves pending valid scopes first (BUD-CHG-001 v1.9
// §9.3, §11.3, §11.14–11.15, §12.2). Read-only for a Submitted version and
// for AUTH §8 technical readers (`can_edit: false`).
const { route, go, epoch } = useRouteState("budget-funding");

const budgetIdParam = computed(() => route.value[1]);
const versionNumberParam = computed(() => route.value[3]);
const versionKey = computed(() => (budgetIdParam.value && versionNumberParam.value ? `${budgetIdParam.value}-V${versionNumberParam.value}` : null));
const tab = computed(() => (route.value[5] === "lines" ? "lines" : "details"));

const draft = ref(null);
const linesEditor = ref(null);
const orgUnits = ref([]);
const fundingSources = ref([]);
const loading = ref(true);
const refreshing = ref(false);
const notFound = ref(false);
const forbidden = ref(null);
const serverError = ref(false);
const actingError = ref(null);
const blockers = ref([]);
const stale = ref(false);
const savedNotSubmitted = ref(false);
const unknownOutcome = ref(false);

const isSuccessor = computed(() => !!draft.value?.based_on);
const canEdit = computed(() => !!draft.value?.can_edit);
const currency = computed(() => draft.value?.budget?.currency || "KES");
const title = computed(() => (isSuccessor.value ? __("Update registered allocation") : __("Record approved allocation")));
const statusLabel = computed(() => {
	if (!draft.value) return "";
	if (draft.value.returned) return __("Changes requested");
	return draft.value.version.status === "Draft" ? __("Draft") : __("Submitted for approval");
});
const statusClass = computed(() => (draft.value?.returned ? "is-attention" : draft.value?.version.status === "Draft" ? "is-draft" : "is-pending"));

const railTrail = computed(() => {
	const items = [
		{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
		{ label: __("Budget & Funding"), route: ["budget-funding"] },
	];
	if (draft.value?.budget) items.push({ label: draft.value.budget.code, route: ["budget-funding", budgetIdParam.value] });
	items.push({ label: draft.value ? __("Version {0}", [draft.value.version.version_number]) : title.value });
	return items;
});
const railEl = ref(null);
usePageRail(railEl, railTrail, { showPeSwitcher: false });

// --- Approval details scope ---
const form = reactive({ approval_reference: "", approval_date: "", authorised_total: "", approval_document: "", approval_document_name: "", revision_type: "Transfer" });
let formSignature = "";
function signature() {
	return JSON.stringify([form.approval_reference, form.approval_date, String(form.authorised_total), form.approval_document, form.revision_type]);
}
function hydrateForm() {
	if (!draft.value) return;
	form.approval_reference = draft.value.version.approval_reference || "";
	form.approval_date = draft.value.version.approval_date || "";
	form.authorised_total = draft.value.version.authorised_total || "";
	form.approval_document = draft.value.approval_document || "";
	form.approval_document_name = (draft.value.approval_document || "").split("/").pop();
	form.revision_type = draft.value.revision_type || "Transfer";
	formSignature = signature();
}
const detailsDirty = computed(() => !!draft.value && signature() !== formSignature);

// --- Budget lines scope ---
const linesDirty = ref(false);
const omitted = ref([]); // previously approved lines omitted from this update (BUD-BR-020)
const guard = kentender_core.desk_page.createSequenceGuard();
const linesGuard = kentender_core.desk_page.createSequenceGuard();

async function loadDraft(opts) {
	if (!versionKey.value) return;
	const quiet = !!(opts && opts.quiet) && !!draft.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	notFound.value = false;
	forbidden.value = null;
	serverError.value = false;
	try {
		const data = await getBudgetVersionDraft(versionKey.value);
		if (!guard.isCurrent(token)) return;
		if (data && data.outcome === "FORBIDDEN") {
			draft.value = null;
			forbidden.value = data.forbidden;
			return;
		}
		if (data && data.outcome === "NOT_FOUND") {
			draft.value = null;
			notFound.value = true;
			return;
		}
		// §6.4 — never re-hydrate a form the user is editing from a refresh
		// that carries nothing new.
		const changed = !draft.value || draft.value.version.modified !== data.version.modified || draft.value.version.status !== data.version.status;
		const userEditing = !!draft.value && detailsDirty.value;
		draft.value = data;
		if (changed && !userEditing) hydrateForm();
		if (!orgUnits.value.length) orgUnits.value = (await listOrganisationUnits()).rows || [];
		if (!fundingSources.value.length) fundingSources.value = (await listFundingSources()).rows || [];
		// A direct load landing on the lines tab must still fetch it.
		if (tab.value === "lines" && !(opts && opts.lines === false)) await loadLines();
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.httpStatus === 403) forbidden.value = { heading: __("You do not have access to this budget version"), text: "" };
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

async function loadLines() {
	if (!versionKey.value) return;
	if (linesDirty.value) return; // never clobber unsaved rows
	const token = linesGuard.next();
	const data = await getBudgetVersionLinesEditor(versionKey.value);
	if (!linesGuard.isCurrent(token)) return;
	if (data && data.outcome) return;
	linesEditor.value = data;
	omitted.value = data.omitted || [];
	linesDirty.value = false;
}

onMounted(loadDraft);
watch(versionKey, (v, prev) => {
	if (v && v !== prev) {
		draft.value = null;
		linesEditor.value = null;
		linesDirty.value = false;
		loadDraft();
	}
});
watch(tab, (t) => {
	if (t === "lines" && !linesEditor.value) loadLines();
});
let activations = 0;
onActivated(() => {
	if (activations++ === 0 || !draft.value) return;
	loadDraft({ quiet: true });
});
watch(epoch, () => draft.value && loadDraft({ quiet: true }));

// --- Unsaved-navigation guard (§11.3): Save changes / Discard / Stay here ---
const navGuard = ref(null); // { scope, proceed }
function switchTab(t) {
	if (t === tab.value) return;
	const dirtyScope = tab.value === "details" && detailsDirty.value ? "details" : tab.value === "lines" && linesDirty.value ? "lines" : null;
	if (dirtyScope) {
		navGuard.value = { scope: dirtyScope, proceed: () => go(budgetIdParam.value, "version", versionNumberParam.value, "edit", t === "lines" ? "lines" : undefined) };
		return;
	}
	go(budgetIdParam.value, "version", versionNumberParam.value, "edit", t === "lines" ? "lines" : undefined);
}
async function navSave() {
	const g = navGuard.value;
	navGuard.value = null;
	const ok = g.scope === "details" ? await saveDetails() : await saveLines();
	if (ok) g.proceed();
}
function navDiscard() {
	const g = navGuard.value;
	navGuard.value = null;
	if (g.scope === "details") hydrateForm();
	else {
		linesDirty.value = false;
		loadLines();
	}
	g.proceed();
}

// --- Commands ---
const runner = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{
		onStart: () => {
			actingError.value = null;
			blockers.value = [];
			stale.value = false;
			savedNotSubmitted.value = false;
			unknownOutcome.value = false;
		},
		onError: (e) => {
			unknownOutcome.value = true;
			actingError.value = (e && e.message) || __("We could not confirm the result. Checking the existing request…");
		},
		mintKey: (label) => mintKey(label),
	}
);
const busy = runner.pending;
const scopeLabel = computed(() => (tab.value === "lines" ? __("Budget lines") : __("Approval details")));

function applyTyped(result) {
	if (result.code === "BUDGET_STALE_WRITE" || result.code === "BUDGET_INVALID_STATE") {
		stale.value = true;
		actingError.value = Object.values(result.errors || {}).join(" ");
		return false;
	}
	if (result.code === "BUDGET_NOT_READY" && result.blockers) {
		blockers.value = result.blockers;
		actingError.value = __("Complete the highlighted details before submitting.");
		nextTick(() => focusFirstBlocker());
		return false;
	}
	actingError.value = Object.values(result.errors || {}).join(" ") || __("Could not save.");
	return false;
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

async function saveDetails(key) {
	const payload = {
		budget_version: versionKey.value,
		approval_reference: form.approval_reference,
		approval_date: form.approval_date,
		authorised_total: form.authorised_total,
		approval_document: form.approval_document,
		revision_type: isSuccessor.value ? form.revision_type : undefined,
		expected_modified: draft.value.version.modified,
		idempotency_key: key || mintKey("details"),
	};
	const result = await saveBudgetVersionDraft(payload);
	if (!result.ok) return applyTyped(result);
	draft.value = { ...draft.value, version: result.version };
	formSignature = signature();
	return true;
}

function linePayload() {
	const rows = (linesEditor.value?.rows || []).map((r) => ({
		budget_line: r.budget_line || undefined,
		title: r.title,
		owner_org_unit: r.owner_org_unit || "",
		funding_source: r.funding_source,
		approved_amount: r.approved_amount,
	}));
	for (const o of omitted.value) rows.push({ budget_line: o.budget_line, omit: true });
	for (const removed of linesEditor.value?.removed || []) rows.push({ budget_line: removed, remove: true });
	return rows;
}

async function saveLines(key) {
	const result = await saveBudgetLinesDraft({ budget_version: versionKey.value, lines: linePayload(), expected_modified: draft.value.version.modified, idempotency_key: key || mintKey("lines") });
	if (!result.ok) {
		if (result.errors && !result.code) {
			actingError.value = Object.values(result.errors).join(" ");
			return false;
		}
		return applyTyped(result);
	}
	linesDirty.value = false;
	linesEditor.value = { ...(linesEditor.value || {}), rows: result.rows, totals: result.totals, removed: [] };
	omitted.value = (await getBudgetVersionLinesEditor(versionKey.value)).omitted || [];
	if (result.version) draft.value = { ...draft.value, version: result.version };
	return true;
}

// Save changes — the current scope, clearly named (§9.3).
function saveChanges() {
	return runner.run(async (key) => {
		const ok = tab.value === "lines" ? await saveLines(key) : await saveDetails(key);
		if (ok) {
			frappe.show_alert({ message: __("{0} saved", [scopeLabel.value]), indicator: "green" });
			await loadDraft({ quiet: true, lines: tab.value !== "lines" });
		}
	}, "save");
}

// Submit for review — saves pending valid scopes first, then submits the
// exact confirmed version with its own key; partial outcomes are named.
function submitForReview() {
	return runner.run(async (key) => {
		let savedSomething = false;
		if (detailsDirty.value) {
			if (!(await saveDetails(mintKey("details")))) return;
			savedSomething = true;
		}
		if (linesDirty.value) {
			if (!(await saveLines(mintKey("lines")))) {
				if (savedSomething) actingError.value = __("Your approval details were saved, but the budget lines were not. ") + (actingError.value || "");
				return;
			}
			savedSomething = true;
		}
		let result;
		try {
			result = await submitBudgetVersion(versionKey.value, draft.value.version.modified, key);
		} catch (e) {
			// Unknown outcome: resolve the original request by replaying the same key.
			unknownOutcome.value = true;
			actingError.value = __("We could not confirm the result. Checking the existing request…");
			result = await submitBudgetVersion(versionKey.value, draft.value.version.modified, key);
			unknownOutcome.value = false;
			actingError.value = null;
		}
		if (!result.ok) {
			applyTyped(result);
			if (savedSomething) savedNotSubmitted.value = true;
			return;
		}
		frappe.show_alert({ message: __("Submitted for review"), indicator: "green" });
		await loadDraft({ quiet: true });
	}, "submit");
}

const BLOCKER_FIELDS = { "evidence.approval_reference": "bud-editor-approval-ref", "evidence.approval_date": "bud-editor-approval-date", "evidence.authorised_total": "bud-editor-approved-allocation", "evidence.approval_document": "bud-editor-upload-btn" };
function focusFirstBlocker() {
	const first = blockers.value[0];
	if (!first) return;
	const id = BLOCKER_FIELDS[first.code];
	if (id && tab.value !== "details") {
		go(budgetIdParam.value, "version", versionNumberParam.value, "edit");
		nextTick(() => document.getElementById(id)?.focus());
		return;
	}
	if (id) document.getElementById(id)?.focus();
	else if (first.code.startsWith("lines.") || first.code.startsWith("transfer.")) {
		if (tab.value !== "lines") go(budgetIdParam.value, "version", versionNumberParam.value, "edit", "lines");
		nextTick(() => document.querySelector('[data-testid="bud-editor-lines-table"] input')?.focus());
	}
}

// --- Lines editing ---
const totals = computed(() => linesEditor.value?.totals || null);
const previewTotals = computed(() => {
	const rows = linesEditor.value?.rows || [];
	const entered = rows.reduce((sum, r) => sum + (Number(r.approved_amount) || 0), 0);
	const approved = Number(form.authorised_total || draft.value?.version.authorised_total || 0);
	const diff = approved - entered;
	let movedOut = 0;
	let movedIn = 0;
	if (isSuccessor.value) {
		for (const r of rows) {
			const delta = (Number(r.approved_amount) || 0) - (Number(r.current_amount) || 0);
			if (delta > 0) movedIn += delta;
			else movedOut += -delta;
		}
		for (const o of omitted.value) movedOut += Number(o.current_amount) || 0;
	}
	return { approved, entered, match: Math.abs(diff) < 0.005, still: diff >= 0.005 ? diff : 0, over: diff <= -0.005 ? -diff : 0, movedOut, movedIn };
});

function markLinesDirty() {
	linesDirty.value = true;
}
function addLine() {
	if (!linesEditor.value) return;
	linesEditor.value.rows.push({ budget_line: null, budget_line_code: "", title: "", owner_org_unit: "", owner_org_unit_label: __("All departments"), funding_source: fundingSources.value[0]?.id || "", approved_amount: 0, identity_locked: false, can_remove: true, can_omit: false, current_amount: 0, change: 0 });
	linesDirty.value = true;
	nextTick(() => document.querySelector('[data-testid="bud-editor-lines-table"] tbody tr:last-child input')?.focus());
}
function removeLine(row) {
	if (row.budget_line) {
		linesEditor.value.removed = linesEditor.value.removed || [];
		linesEditor.value.removed.push(row.budget_line);
	}
	linesEditor.value.rows = linesEditor.value.rows.filter((r) => r !== row);
	linesDirty.value = true;
}
function omitLine(row) {
	omitted.value.push({ budget_line: row.budget_line, title: row.title, current_amount: row.current_amount });
	linesEditor.value.rows = linesEditor.value.rows.filter((r) => r !== row);
	linesDirty.value = true;
}
function restoreLine(o) {
	omitted.value = omitted.value.filter((x) => x !== o);
	linesEditor.value.rows.push({ budget_line: o.budget_line, budget_line_code: "", title: o.title, owner_org_unit: "", funding_source: "", approved_amount: o.current_amount, identity_locked: true, can_remove: false, can_omit: true, current_amount: o.current_amount, change: 0, protected_amount: 0 });
	linesDirty.value = true;
}
</script>

<template>
	<div class="kt-industry kt-bud-editor" data-testid="bud-editor" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div v-if="loading" class="kt-shell"><div class="kt-card kt-blueprint"><div class="kt-skel" style="width: 240px; height: 20px"></div></div></div>
		<div v-else-if="notFound" class="kt-shell"><div class="kt-card kt-blueprint kt-empty" data-testid="bud-editor-not-found"><h2>{{ __("This budget version could not be found.") }}</h2></div></div>
		<div v-else-if="forbidden" class="kt-shell"><div class="kt-card kt-blueprint kt-empty" data-testid="bud-editor-forbidden"><h2>{{ __(forbidden.heading) }}</h2><p v-if="forbidden.text" class="kt-muted">{{ __(forbidden.text) }}</p></div></div>
		<div v-else-if="serverError" class="kt-shell"><div class="kt-card kt-blueprint kt-empty"><h2>{{ __("This budget version could not be loaded.") }}</h2><button type="button" class="kt-btn kt-btn-primary" @click="loadDraft()">{{ __("Try again") }}</button></div></div>

		<template v-else-if="draft">
			<div class="kt-shell" style="padding-bottom: 32px">
				<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 16px" data-testid="bud-editor-header">
					<div>
						<div class="kt-eyebrow" style="margin-bottom: 6px">{{ draft.budget.code }} · {{ __("VERSION {0}", [draft.version.version_number]) }}</div>
						<div style="display: flex; align-items: center; gap: 12px">
							<h1 style="margin: 0">{{ title }}</h1>
							<span class="kt-status" :class="statusClass" data-testid="bud-editor-status">{{ statusLabel }}</span>
						</div>
					</div>
					<div v-if="canEdit" style="display: flex; align-items: center; gap: 10px; flex: none">
						<span class="kt-muted" style="font-size: 12px" data-testid="bud-editor-scope">{{ __("Save scope: {0}", [scopeLabel]) }}</span>
						<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="bud-editor-save-btn" @click="saveChanges">{{ __("Save changes") }}</button>
						<button type="button" class="kt-btn kt-btn-primary" :disabled="busy" data-testid="bud-editor-submit-btn" @click="submitForReview">{{ __("Submit for review") }}</button>
					</div>
					<span v-else class="kt-muted" style="font-size: 13px" data-testid="bud-editor-readonly">{{ __("Read-only") }}</span>
				</div>

				<KtErrorBanner :message="actingError" style="margin-bottom: 12px" @dismiss="actingError = null" />
				<div v-if="stale" class="kt-notice is-warning" style="margin-bottom: 12px" data-testid="bud-editor-stale">
					<div class="kt-notice-body">{{ __("This budget has changed since you opened it.") }} <a href="#" @click.prevent="loadDraft({ quiet: true })">{{ __("Refresh to see the current details") }}</a></div>
				</div>
				<div v-if="savedNotSubmitted" class="kt-notice is-warning" style="margin-bottom: 12px" data-testid="bud-editor-saved-not-submitted">
					<div class="kt-notice-body"><strong>{{ __("Your changes were saved, but the allocation was not submitted.") }}</strong> {{ __("Resolve the items below and submit again.") }}</div>
				</div>
				<ul v-if="blockers.length" class="kt-card kt-blueprint" style="margin: 0 0 12px; padding: 14px 14px 14px 30px; font-size: 14px" data-testid="bud-editor-blockers">
					<li v-for="b in blockers" :key="b.code">{{ b.message }}</li>
				</ul>

				<div v-if="draft.returned" class="kt-notice is-warning" style="margin-bottom: 16px" data-testid="bud-editor-returned">
					<div class="kt-notice-body">
						<strong>{{ __("Changes requested by {0}, {1}.", [draft.returned.by, draft.returned.at]) }}</strong> {{ draft.returned.reason }}
						{{ __("Correct the draft and submit it again; the earlier submission and its document are retained.") }}
					</div>
				</div>

				<div class="kt-tabs" role="tablist">
					<div class="kt-tab" role="tab" :aria-selected="tab === 'details'" tabindex="0" data-testid="bud-editor-tab-overview" @click="switchTab('details')" @keydown.enter="switchTab('details')">{{ __("Approval details") }}</div>
					<div class="kt-tab" role="tab" :aria-selected="tab === 'lines'" tabindex="0" data-testid="bud-editor-tab-lines" @click="switchTab('lines')" @keydown.enter="switchTab('lines')">{{ __("Budget lines") }}</div>
				</div>

				<!-- Approval details (BUD-DES-14 / BUD-DES-02 fields) -->
				<template v-if="tab === 'details'">
					<div v-if="isSuccessor" class="kt-notice is-info" style="margin-bottom: 16px" data-testid="bud-editor-successor-note">
						<div class="kt-notice-body">{{ __("The current allocation stays in use until this update is approved.") }}</div>
					</div>
					<div class="kt-card kt-blueprint">
						<h3 class="kt-card-title">{{ isSuccessor ? __("Version context") : __("Budget context") }}</h3>
						<div class="kt-grid-2" style="gap: 16px">
							<div class="kt-field"><label>{{ __("Financial Year") }}</label><input class="kt-input" type="text" :value="draft.budget.fiscal_year.label" disabled /></div>
							<div class="kt-field"><label>{{ __("Currency") }}</label><input class="kt-input" type="text" :value="draft.budget.currency" disabled /></div>
							<template v-if="isSuccessor">
								<div class="kt-field"><label>{{ __("Based on") }}</label><input class="kt-input" type="text" :value="__('Active Version {0}', [draft.based_on.version_number])" disabled /></div>
								<div class="kt-field">
									<label for="bud-editor-type">{{ __("Type of change") }}</label>
									<select id="bud-editor-type" v-model="form.revision_type" class="kt-input" :disabled="!canEdit" data-testid="bud-editor-revision-type">
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
						<h3 class="kt-card-title">{{ __("External approval") }}</h3>
						<div class="kt-grid-2" style="gap: 16px">
							<div class="kt-field">
								<label for="bud-editor-approval-ref">{{ __("Approval reference") }}</label>
								<input id="bud-editor-approval-ref" v-model="form.approval_reference" class="kt-input" type="text" :disabled="!canEdit" data-testid="bud-editor-approval-ref" />
							</div>
							<div class="kt-field">
								<label for="bud-editor-approval-date">{{ __("Approval date") }}</label>
								<input id="bud-editor-approval-date" v-model="form.approval_date" class="kt-input" type="date" :disabled="!canEdit" data-testid="bud-editor-approval-date" />
							</div>
							<div class="kt-field">
								<label for="bud-editor-approved-allocation">{{ __("Approved allocation") }}</label>
								<div class="kt-input-prefix"><span class="prefix">{{ currency }}</span><input id="bud-editor-approved-allocation" v-model="form.authorised_total" type="number" min="0" :disabled="!canEdit" data-testid="bud-editor-approved-allocation" /></div>
							</div>
							<div class="kt-field">
								<label>{{ __("Approval document") }}</label>
								<div class="kt-file-row" style="justify-content: space-between">
									<a v-if="form.approval_document" :href="form.approval_document" target="_blank" rel="noopener" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis" data-testid="bud-editor-document-name">{{ form.approval_document_name }}</a>
									<span v-else data-testid="bud-editor-document-name">{{ __("No file attached") }}</span>
									<button v-if="canEdit" id="bud-editor-upload-btn" type="button" class="kt-btn kt-btn-ghost" style="flex: none; font-size: 13px" data-testid="bud-editor-upload-btn" @click="openFileUploader">{{ form.approval_document ? __("Replace") : __("Attach") }}</button>
								</div>
								<p class="kt-field-hint">{{ __("Exactly one document. Replacing it in this draft keeps every earlier submitted attempt's evidence.") }}</p>
							</div>
						</div>
					</div>
				</template>

				<!-- Budget lines (BUD-DES-03 / BUD-DES-15) -->
				<template v-else>
					<div v-if="!linesEditor" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 240px; height: 16px"></div></div>
					<template v-else>
						<div class="kt-kpi-row" style="margin-bottom: 14px" data-testid="bud-editor-totals">
							<div class="kt-kpi-card"><div class="kt-kpi-value">{{ formatKes(previewTotals.approved, currency) }}</div><div class="kt-kpi-sub">{{ __("Approved allocation") }}</div></div>
							<div class="kt-kpi-card"><div class="kt-kpi-value">{{ formatKes(previewTotals.entered, currency) }}</div><div class="kt-kpi-sub">{{ __("Total entered") }}</div></div>
						</div>
						<div class="kt-notice" :class="previewTotals.match ? 'is-live' : previewTotals.still ? 'is-warning' : 'is-critical'" style="margin-bottom: 16px" data-testid="bud-editor-reconcile">
							<div class="kt-notice-body">
								<template v-if="previewTotals.match">{{ __("Budget lines match the approved allocation.") }}</template>
								<template v-else-if="previewTotals.still">{{ __("Amount still to assign: {0}", [formatKes(previewTotals.still, currency)]) }}</template>
								<template v-else>{{ __("Amount over allocation: {0}", [formatKes(previewTotals.over, currency)]) }}</template>
							</div>
						</div>
						<div v-if="isSuccessor && form.revision_type === 'Transfer'" style="display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap" data-testid="bud-editor-transfer-totals">
							<span class="kt-tag kt-tag-neutral">{{ __("Total moved out: {0}", [formatKes(previewTotals.movedOut, currency)]) }}</span>
							<span class="kt-tag kt-tag-accent-2">{{ __("Total moved in: {0}", [formatKes(previewTotals.movedIn, currency)]) }}</span>
						</div>
						<p v-if="canEdit && !isSuccessor" class="kt-label" style="margin: 0 0 10px">{{ __("Which department may use this budget line?") }}</p>
						<div v-if="isSuccessor" class="kt-muted" style="font-size: 13px; margin: 0 0 10px">{{ __("Existing lines keep their name, department and funding source. Add a new budget line for a changed purpose, department or funding source.") }}</div>

						<div class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto">
							<table class="kt-table" data-testid="bud-editor-lines-table">
								<thead>
									<tr>
										<th>{{ __("Budget line") }}</th>
										<th>{{ __("Available to") }}</th>
										<th>{{ __("Funding source") }}</th>
										<th v-if="isSuccessor" class="is-num">{{ __("Current allocation") }}</th>
										<th class="is-num">{{ isSuccessor ? __("Proposed amount") : __("Amount") }}</th>
										<th v-if="isSuccessor" class="is-num">{{ __("Change") }}</th>
										<th></th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="(row, i) in linesEditor.rows" :key="row.budget_line || 'new-' + i">
										<td style="min-width: 240px">
											<input v-if="canEdit && !row.identity_locked" v-model="row.title" class="kt-input" style="min-width: 240px" :aria-label="__('Budget line')" @input="markLinesDirty" />
											<div v-else>{{ row.title }}</div>
											<div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ row.budget_line_code || __("Reference assigned on save") }}</div>
											<a v-if="canEdit && row.can_omit" href="#" style="font-size: 11px" data-testid="bud-editor-omit-link" @click.prevent="omitLine(row)">{{ __("Omit from this update") }}</a>
										</td>
										<td>
											<select v-if="canEdit && !row.identity_locked" v-model="row.owner_org_unit" class="kt-input" :aria-label="__('Available to')" @change="markLinesDirty">
												<option value="">{{ __("All departments") }}</option>
												<option v-for="o in orgUnits" :key="o.id" :value="o.id">{{ o.label }}</option>
											</select>
											<span v-else>{{ row.owner_org_unit_label || __("All departments") }}</span>
										</td>
										<td>
											<select v-if="canEdit && !row.identity_locked" v-model="row.funding_source" class="kt-input" :aria-label="__('Funding source')" @change="markLinesDirty">
												<option v-for="f in fundingSources" :key="f.id" :value="f.id">{{ f.label }}</option>
											</select>
											<span v-else>{{ row.funding_source }}</span>
										</td>
										<td v-if="isSuccessor" class="is-num">{{ formatKes(row.current_amount, currency) }}</td>
										<td class="is-num">
											<div v-if="canEdit" class="kt-input-prefix" style="min-width: 170px"><span class="prefix">{{ currency }}</span><input v-model="row.approved_amount" type="number" min="0" style="text-align: right" :aria-label="__('Amount')" @input="markLinesDirty" /></div>
											<span v-else>{{ formatKes(row.approved_amount, currency) }}</span>
										</td>
										<td v-if="isSuccessor" class="is-num">{{ formatSignedKes((Number(row.approved_amount) || 0) - (Number(row.current_amount) || 0), currency) }}</td>
										<td style="white-space: nowrap">
											<button v-if="canEdit && row.can_remove && !row.identity_locked" type="button" class="kt-btn kt-btn-secondary kt-danger" style="font-size: 13px; padding: 5px 10px" @click="removeLine(row)">{{ __("Remove") }}</button>
										</td>
									</tr>
								</tbody>
							</table>
						</div>
						<div v-if="omitted.length" class="kt-card kt-blueprint" style="margin-top: 12px" data-testid="bud-editor-omitted">
							<h3 class="kt-card-title">{{ __("Omitted from this update") }}</h3>
							<div v-for="o in omitted" :key="o.budget_line" style="display: flex; justify-content: space-between; align-items: center; gap: 12px; font-size: 14px; padding: 6px 0">
								<span>{{ o.title }} · {{ formatKes(o.current_amount, currency) }}</span>
								<a v-if="canEdit" href="#" @click.prevent="restoreLine(o)">{{ __("Keep in this update") }}</a>
							</div>
							<p class="kt-muted" style="font-size: 12px; margin: 8px 0 0">{{ __("The line and its history remain; it is left out of the proposed version only.") }}</p>
						</div>
						<button v-if="canEdit" type="button" class="kt-btn kt-btn-secondary" style="margin-top: 12px" data-testid="bud-editor-add-line-btn" @click="addLine">{{ __("Add Budget Line") }}</button>
					</template>
				</template>
			</div>

			<div v-if="navGuard" class="kt-dialog-backdrop" tabindex="-1" @keydown.esc="navGuard = null">
				<div class="kt-dialog" style="width: 440px" role="dialog" aria-modal="true" data-testid="bud-editor-unsaved-dialog">
					<h2 class="kt-dialog-title">{{ __("Unsaved changes") }}</h2>
					<p class="kt-muted">{{ __("Your {0} changes are not saved yet.", [navGuard.scope === "lines" ? __("budget line") : __("approval detail")]) }}</p>
					<div class="kt-dialog-actions">
						<button type="button" class="kt-btn kt-btn-ghost" @click="navGuard = null">{{ __("Stay here") }}</button>
						<button type="button" class="kt-btn kt-btn-secondary" @click="navDiscard">{{ __("Discard unsaved changes") }}</button>
						<button type="button" class="kt-btn kt-btn-primary" @click="navSave">{{ __("Save changes") }}</button>
					</div>
				</div>
			</div>
		</template>
	</div>
</template>

<style scoped>
.kt-bud-editor .kt-input-prefix { min-height: 36px; padding: 6px 10px; font-size: 14px; display: flex; align-items: center; gap: 6px; background: var(--kt-color-surface); border: 1px solid var(--kt-color-divider); }
.kt-bud-editor .kt-input-prefix span.prefix { color: var(--kt-color-neutral-700); }
.kt-bud-editor .kt-input-prefix input { border: none; background: transparent; padding: 0; min-height: auto; width: 100%; }
.kt-bud-editor .kt-file-row { min-height: 36px; padding: 6px 10px; font-size: 14px; display: flex; align-items: center; gap: 8px; background: var(--kt-color-surface); border: 1px solid var(--kt-color-divider); }
</style>
