<!-- Departmental Needs — NDS-CHG-001 v1.1 §10.
     One Frappe Page ("departmental-needs") carrying every §10 route; this root
     resolves the route segments and picks the screen, exactly as the Budget and
     Strategy Vue-in-Desk pages do. -->
<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<!-- §16.1 — one stable page-ready hook for every screen. A spec waits
		     for [data-testid="nds-shell"][data-loading="false"] with the
		     data-screen it expects, rather than racing a visual class. -->
		<div
			class="kt-shell"
			data-testid="nds-shell"
			:data-screen="selectionRequired ? 'context-selection' : screen"
			:data-loading="loading ? 'true' : 'false'"
			:data-refreshing="refreshing ? 'true' : 'false'"
			:data-reference="needReference || ''"
		>
			<ContextPicker
				v-if="selectionRequired"
				:contexts="workspace.contexts || []"
				:financial-years="financialYears"
				:context-key="contextKey"
				:financial-year="financialYear"
				@select-context="onSelectContext"
				@select-financial-year="onSelectFinancialYear"
			/>

			<WorkspaceScreen
				v-else-if="screen === 'workspace'"
				:loading="loading"
				:error="error"
				:outcome="workspace.outcome"
				:context="workspace.context || {}"
				:contexts="workspace.contexts || []"
				:submission="submissionState"
				:needs="workspace.needs || []"
				:actions="workspace.actions || []"
				:financial-years="financialYears"
				:selected-financial-year="financialYear"
				v-model:search="search"
				v-model:status="status"
				@clear-filters="clearFilters"
				@create="onCreateClick"
				@reload="load"
				@action="onRowAction"
				@select-financial-year="onSelectFinancialYear"
				@select-context="onSelectContext"
			/>

			<NeedEditorScreen
				v-else-if="screen === 'editor'"
				:mode="editorMode"
				:need="detail.need || {}"
				:revision="editorRevision"
				:context="editorContext"
				:department-choices="editorDepartmentChoices"
				:selected-department="selectedDepartment"
				:units="units"
				@unit-created="(unit) => units.push(unit)"
				@select-department="onSelectDepartment"
				:return-reason="needReference ? detail.latest_return : null"
				:history="needReference ? detail.history || [] : []"
				:error-summary="errorSummary"
				:field-errors="fieldErrors"
				:pending="pending"
				@save="onSaveDraft"
				@submit="onSubmit"
				@cancel="onEditorCancel"
			/>

			<NeedDetailScreen
				v-else-if="screen === 'detail'"
				:need="detail.need || {}"
				:scope-labels="detail.scope_labels || {}"
				:revision="detail.current_revision || {}"
				:accepted-revision="detail.accepted_revision || {}"
				:pinned-revision="pinnedRevision"
				:usage="usage"
				:disposition="disposition"
				:older-usage="olderUsage"
				:planning-checking="planningChecking"
				:planning-unavailable="planningUnavailable"
				:planning-checked-at="planningCheckedAt"
				:author-label="detail.author_label || ''"
				:accepted-by-label="acceptedBy.actor_label || ''"
				:accepted-at="acceptedBy.occurred_at || ''"
				:accepted-capacity="acceptedBy.capacity || ''"
				:submitted-at="(detail.submitted || {}).occurred_at || ''"
				:access-profile="detail.access_profile || ''"
				:actions="detail.actions || []"
				:latest-return="detail.latest_return || null"
				:history="detail.history || []"
				:withdrawal-open="withdrawalOpen"
				@create-update="onCreateSuccessor"
				@request-withdrawal="openWithdrawalDialog"
				@open-successor="go(needReference, 'edit')"
				@edit="go(needReference, 'edit')"
				@review="(action) => onRowAction({ reference: needReference }, action)"
				@view-plan-item="onViewPlanItem"
				@retry-planning="refreshPlanningStatus"
			/>

			<ReviewTaskScreen
				v-else-if="screen === 'task'"
				:need="task.need || {}"
				:revision="task.revision || {}"
				:accepted-revision="task.accepted_revision || {}"
				:scope="task.scope || {}"
				:requester-label="task.requester_label || ''"
				:opened-at="task.opened_at || ''"
				:task-type="task.task_type || ''"
				:permitted="task.permitted_decisions || []"
				:maker-checker-blocked="!!task.maker_checker_blocked"
				:error-summary="errorSummary"
				:pending="pending"
				@return="dialog = 'return'"
				@decline="dialog = 'decline'"
				@accept="dialog = 'accept'"
			/>

			<WithdrawalReviewScreen
				v-else-if="screen === 'withdrawal'"
				:need="task.need || {}"
				:request="task.withdrawal_request || {}"
				:revision="task.revision || {}"
				:scope="task.scope || {}"
				:dependency="dependency"
				:dependency-checking="dependencyChecking"
				:requester-label="requesterLabel"
				:requested-at="task.opened_at || ''"
				:permitted="task.permitted_decisions || []"
				:maker-checker-blocked="!!task.maker_checker_blocked"
				:error-summary="errorSummary"
				:pending="pending"
				@approve="dialog = 'approve-withdrawal'"
				@decline="dialog = 'decline-withdrawal'"
				@close="go()"
				@view-plan-item="onViewPlanItem"
				@retry-dependency="retryWithdrawalDependency"
			/>

		</div>

		<!-- §11.13 / §11.12 — the exact reason dialogs. -->
		<ReasonDialog
			v-if="reasonDialog"
			:title="reasonDialog.title"
			:subject="reasonDialog.subject || ''"
			:subject-meta="reasonDialog.subjectMeta || ''"
			:lede="reasonDialog.lede || ''"
			:field-label="reasonDialog.fieldLabel || 'Reason'"
			:confirm-label="reasonDialog.confirmLabel"
			:destructive="reasonDialog.destructive"
			v-model="reason"
			:error="reasonError"
			:pending="pending"
			@confirm="reasonDialog.onConfirm()"
			@cancel="closeDialog"
		/>

		<ConfirmDialog
			v-if="confirmDialog"
			:title="confirmDialog.title"
			:message="confirmDialog.message"
			:subject="confirmDialog.subject"
			:confirm-label="confirmDialog.confirmLabel"
			:destructive="confirmDialog.destructive"
			:pending="pending"
			@confirm="confirmDialog.onConfirm()"
			@cancel="closeDialog"
		/>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "../nds_shared/composables/useRouteState.js";
import { usePageRail } from "../nds_shared/composables/usePageRail.js";
import * as api from "./data/needsApi.js";
import { quantityWithUnit } from "./data/format.js";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import ContextPicker from "./components/ContextPicker.vue";
import NeedDetailScreen from "./components/NeedDetailScreen.vue";
import NeedEditorScreen from "./components/NeedEditorScreen.vue";
import ReasonDialog from "./components/ReasonDialog.vue";
import ReviewTaskScreen from "./components/ReviewTaskScreen.vue";
import WithdrawalReviewScreen from "./components/WithdrawalReviewScreen.vue";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";

const PAGE = "departmental-needs";
const { route, go, epoch } = useRouteState(PAGE);
// Last payload per screen identity: a revisited screen renders from here at
// once and refreshes in place; the skeleton is only for a screen never
// loaded in this session.
const cache = kentender_core.desk_page.createScreenCache();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const pending = ref(false);
const error = ref("");
const errorSummary = ref("");
const fieldErrors = ref({});
const search = ref("");
const status = ref("");

const workspace = ref({});
const detail = ref({});
const task = ref({});
// get_needs_submission_state() shape: { open, financial_year, label, closes_at }.
const submissionState = ref({ open: false, financial_year: "", label: "", closes_at: "" });
const usage = ref({});
const disposition = ref(null);
const olderUsage = ref(null);
const planningChecking = ref(false);
const planningUnavailable = ref(false);
const planningCheckedAt = ref("");
const dependency = ref({});
const dependencyChecking = ref(false);
const units = ref([]);
const acceptedBy = ref({});
const dialog = ref("");
const reason = ref("");
const reasonError = ref("");
const financialYears = ref([]);
// The eligible departments + the one open Fiscal Year resolved for the Need
// currently being created — from list_need_create_targets, never from the
// workspace's FY filter (see editorContext). NDS-CHG-001 v1.13 §11.16 — the
// create form itself hosts the department choice; there is no longer a
// separate preliminary dialog for the multi-department case.
const createTargets = ref(null);
// The user's in-form pick, NDS-DES-15-MULTIPLE only; empty until chosen.
const selectedDepartment = ref("");

// CTX-CHG-001 — the working context is a SERVER-SIDE user preference. These
// refs carry only the current screen's resolved/explicit values; a bare load
// sends nothing and the server resolves the caller's own remembered context
// (this module's department and financial year). AUTH-ADR-001 v1.6 §1.1 — the
// site is exactly one implicit Procuring Entity, so there is no PE dimension
// to remember. Browser storage grants nothing and is not even used as a
// cache — the old per-origin localStorage leaked one user's context into the
// next login.
const contextKey = ref("");
const financialYear = ref("");

// NDS-CHG-001 v1.13 §11.2 — the Financial year control is an optional filter
// ("All financial years" is a valid default), not a mandatory pre-selection:
// `get_workspace` already lists across every year when none is selected
// (AUTH-ADR-001 v1.7 §16.3 step 9 — never trapped by a remembered year). The
// full-screen picker is reserved for the one case the server cannot resolve
// on its own: no remembered Organisation Unit and more than one eligible.
const selectionRequired = computed(
	() =>
		!loading.value &&
		!error.value &&
		screen.value === "workspace" &&
		workspace.value.outcome === "CONTEXT_SELECTION_REQUIRED"
);

function onSelectContext(value) {
	contextKey.value = value;
	load({ quiet: true });
}

function onSelectFinancialYear(value) {
	financialYear.value = value;
	load({ quiet: true });
}

// --- routing ---------------------------------------------------------------
// Segments after the page slug. §10's routes are distinguished by shape, so
// the mapping is read top-down and never guesses from a partial match.
const segments = computed(() => route.value.slice(1).filter(Boolean));

const screen = computed(() => {
	const [first, second, third] = segments.value;
	if (!first) return "workspace";
	if (first === "new") return "editor";
	if (first === "review") {
		// The queue landing was removed (2026-08-30): review decisions reach
		// the reviewer through My Work and notifications, and the workspace's
		// own role-aware rows. A bare /review deep link redirects (below).
		if (!second) return "workspace";
		return third === "withdrawal" ? "withdrawal" : "task";
	}
	if (second === "edit") return "editor";
	if (second === "accepted") return "detail";
	return "detail";
});

const needReference = computed(() => {
	const [first, second] = segments.value;
	if (!first || ["new", "review"].includes(first)) return "";
	return first;
});

const taskId = computed(() => (segments.value[0] === "review" ? segments.value[1] || "" : ""));

// NDS-UI-06 pins the accepted revision number in the route.
const pinnedRevisionNumber = computed(() =>
	segments.value[1] === "accepted" ? Number(segments.value[2]) : null
);

const pinnedRevision = computed(() => {
	if (!pinnedRevisionNumber.value) return null;
	const accepted = detail.value.accepted_revision;
	if (accepted && Number(accepted.revision_number) === pinnedRevisionNumber.value) return accepted;
	// The route asked for a revision that is no longer current: keep it readable
	// rather than redirecting (§12.4).
	return accepted || null;
});

const editorMode = computed(() => {
	if (!needReference.value) return "create";
	const state = (detail.value.need || {}).current_state;
	if (state === "Accepted for planning") return "successor";
	// Only a Returned Need is being *corrected*; a Draft is simply continued.
	return state === "Returned" ? "correct" : "draft";
});

// `detail` is the last need loaded this session and /new never reloads it, so
// the create editor must not read it — it would hydrate from that need.
const editorRevision = computed(() =>
	needReference.value ? detail.value.current_revision || {} : {}
);

const editorContext = computed(() => {
	// NDS-DES-15 / §12.1 — the create target's own resolved department and the
	// one open Fiscal Year, never the workspace's FY *filter* (which offers
	// only years already represented by existing Needs — empty on a first
	// Need, and unrelated to which year is open for creation). Falls back to
	// the workspace context only for a direct URL load of /new (no
	// createTargets yet resolved).
	if (!needReference.value) {
		const targets = createTargets.value;
		if (!targets) return workspace.value.context || {};
		const chosen = (targets.organisation_units || []).find(
			(row) => row.organisation_unit === selectedDepartment.value
		);
		return {
			organisation_unit: selectedDepartment.value,
			organisation_unit_label: chosen ? chosen.organisation_unit_label : "",
			financial_year: targets.financial_year,
			financial_year_label: targets.financial_year_label,
		};
	}
	// The artboards show scope by name, never by ID.
	const need = detail.value.need || {};
	const labels = detail.value.scope_labels || {};
	return {
		organisation_unit_label: labels.organisation_unit || need.organisation_unit,
		financial_year_label: labels.financial_year || need.financial_year,
	};
});

// NDS-DES-15-MULTIPLE — offered only while creating and more than one
// department is eligible; a single eligible department resolves silently
// (SINGLE) and this stays empty, so the editor renders it read-only instead.
const editorDepartmentChoices = computed(() => {
	if (needReference.value || !createTargets.value) return [];
	const units = createTargets.value.organisation_units || [];
	return units.length > 1 ? units : [];
});

function onSelectDepartment(value) {
	selectedDepartment.value = value;
	// Reuses the same server-side preference persistence the workspace filter
	// uses, so the list reflects the chosen department on return.
	contextKey.value = value;
}

const withdrawalOpen = computed(
	() => (detail.value.open_task || {}).task_type === "Withdrawal"
);

const requesterLabel = computed(
	() => (task.value.withdrawal_request || {}).requested_by || ""
);

// --- loading ---------------------------------------------------------------

// A monotonic token so a superseded load (the user kept typing, or navigated
// away mid-flight) can never overwrite the newer response's state.
let loadSeq = 0;
let inFlightKey = "";

const screenKey = computed(() => {
	if (screen.value === "task" || screen.value === "withdrawal") return `task:${taskId.value}`;
	if (needReference.value) return `need:${needReference.value}`;
	return "workspace";
});

async function fetchFor(scr) {
	if (scr === "task" || scr === "withdrawal") {
		const loadedTask = await api.getDepartmentalReviewTask(taskId.value);
		let loadedDependency = null;
		if (scr === "withdrawal") {
			// NDS-DES-12-UNAVAILABLE — the check itself can fail independently of
			// the task load; caught here rather than left to abort the whole
			// screen navigation, so the withdrawal review still renders with an
			// explicit "could not be checked" state and a Try again action.
			const request = loadedTask.withdrawal_request || {};
			try {
				loadedDependency = await api.checkWithdrawalDependency(
					(loadedTask.need || {}).name,
					request.accepted_revision
				);
			} catch (e) {
				loadedDependency = { unavailable: true };
			}
		}
		return { task: loadedTask, dependency: loadedDependency };
	}
	if (needReference.value) {
		return { detail: await api.getDepartmentalNeed(needReference.value) };
	}
	return {
		workspace: await api.getNeedsWorkspace({
			organisation_unit: contextKey.value || "",
			financial_year: financialYear.value,
			search: search.value,
			status: status.value,
		}),
	};
}

function applyLoaded(loaded) {
	if (loaded.task) {
		task.value = loaded.task;
		if (loaded.dependency) dependency.value = loaded.dependency;
		return;
	}
	if (loaded.detail) {
		detail.value = loaded.detail;
		// §4.7/§11.8 — the full detail (usage + Plan/Plan Item references), not
		// just the bare value: the workspace table's own status pill still
		// reads `row.planning_usage` (a plain string) unaffected by this.
		usage.value = detail.value.planning_usage || {};
		disposition.value = detail.value.planning_disposition || null;
		olderUsage.value = null;
		planningUnavailable.value = false;
		planningCheckedAt.value = "";
		acceptedBy.value = detail.value.accepted || {};
		return;
	}
	workspace.value = loaded.workspace;
	financialYears.value = workspace.value.financial_years || [];
	// One eligible context loads directly (§12.1).
	const resolved = workspace.value.context;
	if (resolved && resolved.organisation_unit) {
		// Mirror the server's resolution; the server is the memory.
		contextKey.value = resolved.organisation_unit;
		if (resolved.financial_year) financialYear.value = resolved.financial_year;
	}
}

// The skeleton shows only for a screen with nothing to show yet. A screen
// already loaded this session (Back, Cancel, a decision that routes) renders
// its last payload at once and refreshes in place; `quiet` forces the
// in-place path for filter changes and post-action refreshes.
async function load(opts) {
	const scr = screen.value;
	const key = screenKey.value;
	const cached = cache.get(key);
	if (opts && opts.entering && cached) applyLoaded(cached);
	const quiet = !!(opts && opts.quiet === true) || !!cached;
	if (quiet && inFlightKey === key) return;
	const seq = ++loadSeq;
	inFlightKey = key;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = "";
	errorSummary.value = "";
	try {
		const loaded = await fetchFor(scr);
		if (seq !== loadSeq) return;
		cache.set(key, loaded);
		applyLoaded(loaded);
		if (loaded.detail && (loaded.detail.need || {}).current_state === "Accepted for planning") {
			// Fire-and-forget: the atomic payload just applied already has a
			// usable "last confirmed" value, so this revalidation never blocks
			// first paint (AGENTS.md §6.4).
			refreshPlanningStatus();
		}
		if (loaded.workspace && !quiet) {
			// The Needs-submission flag is a site-wide read, independent of the
			// selected department, so a quiet filter refresh keeps the one
			// already shown.
			submissionState.value = await api.getNeedsSubmissionState();
			if (seq !== loadSeq) return;
		}
		if (scr === "editor") await loadUnits();
	} catch (e) {
		if (seq === loadSeq) error.value = e.message;
	} finally {
		if (seq === loadSeq) {
			loading.value = false;
			refreshing.value = false;
			inFlightKey = "";
		}
	}
}

async function loadUnits() {
	if (units.value.length) return;
	// NDS-CHG-001 v1.6 §1.1/§16.4.11 — units come from ERPNext's native `UOM`,
	// enabled only. `uom_name` is mapped to `unit_label` so NeedEditorScreen's
	// dropdown needs no separate field-name awareness.
	const rows = await frappe.db.get_list("UOM", {
		filters: { enabled: 1 },
		fields: ["name", "uom_name"],
		order_by: "uom_name asc",
		limit: 200,
	});
	units.value = rows.map((row) => ({ name: row.name, unit_label: row.uom_name || row.name }));
}


watch(
	segments,
	(value) => {
		// Normalise the retired queue URL so history and bookmarks stay honest.
		if (value[0] === "review" && !value[1]) go();
	},
	{ immediate: true }
);

watch([screen, needReference, taskId], () => load({ entering: true }), { immediate: true });
// The page came back into view on the same route: revalidate what is shown.
watch(epoch, () => {
	if (cache.has(screenKey.value)) load({ quiet: true });
});

// §12.1 filters — refresh quietly (rows stay on screen) and debounce typing,
// so the search asks the server once per pause, not once per keystroke.
let searchDebounce = null;
function refreshFilters(debounced) {
	if (screen.value !== "workspace") return;
	clearTimeout(searchDebounce);
	if (debounced) {
		searchDebounce = setTimeout(() => load({ quiet: true }), 250);
	} else {
		load({ quiet: true });
	}
}
watch(search, () => refreshFilters(true));
watch(status, () => refreshFilters(false));

// AUTH-ADR-001 v1.6 §1.1 — the site is exactly one implicit Procuring Entity,
// so the rail's PE switcher stays dormant here (matching Budget's and
// Strategy's own already-cut-over pages); there is nothing to switch between.
usePageRail(
	railEl,
	computed(() => [
		{ label: "Departmental Needs", route: [PAGE] },
		...(needReference.value ? [{ label: needReference.value }] : []),
	])
);

// --- commands --------------------------------------------------------------
// Each handler mints one idempotency key for the attempt and disables the
// initiating button while the command is pending (§12.3).

async function run(action, fn) {
	if (pending.value) return null;
	pending.value = true;
	errorSummary.value = "";
	fieldErrors.value = {};
	reasonError.value = "";
	try {
		return await fn(api.newIdempotencyKey(action));
	} catch (e) {
		// Only a ReasonDialog renders `reasonError` inline; a ConfirmDialog has
		// no error slot of its own (a failure there was previously silent —
		// found while wiring the new withdraw-draft confirmation).
		if (reasonDialog.value) reasonError.value = e.message;
		else errorSummary.value = e.message;
		return null;
	} finally {
		pending.value = false;
	}
}

function recordVersion() {
	return (detail.value.need || {}).record_version;
}

// The version stamp the next command must carry is the one the server just
// returned — stamped synchronously from the save response, never left to
// the post-save reload. `run` re-enables the buttons before that reload
// resolves, so a Save draft followed straight away by Submit for review (or a
// second Save) used to send the pre-save stamp and be refused as a stale
// write ("This Departmental Need changed after it was opened") with nobody
// else editing (2026-09-11).
function stampSavedVersion(result) {
	if (result && detail.value && detail.value.need) detail.value.need.record_version = result.record_version;
}

async function saveDraftCommand(action, form) {
	return run(action, async (key) => {
		const result = await api.saveNeedDraft({
			need: needReference.value || "",
			...(needReference.value ? { expected_version: recordVersion() } : contextArgs()),
			...form,
			idempotency_key: key,
		});
		stampSavedVersion(result);
		return result;
	});
}

async function onSaveDraft(form) {
	const result = await saveDraftCommand("save-draft", form);
	if (!result) return;
	// §12.3 — the first save replaces the route with the generated reference.
	if (!needReference.value) go(result.need_reference, "edit");
	else await load({ quiet: true });
}

async function onSubmit(form) {
	const saved = await saveDraftCommand("save-before-submit", form);
	if (!saved) return;
	const result = await run("submit", (key) =>
		api.submitNeedRevision({
			need: saved.need,
			expected_version: saved.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(result.need_reference);
}

function contextArgs() {
	if (createTargets.value) {
		return { organisation_unit: selectedDepartment.value, financial_year: createTargets.value.financial_year };
	}
	const context = workspace.value.context || {};
	return {
		organisation_unit: context.organisation_unit,
		financial_year: context.financial_year,
	};
}

// NDS-CHG-001 v1.13 §11.16/§12.1 — resolved at click time from the exact
// authorised create targets, never from a Fiscal Year permission, the list's
// current FY filter or a browser-stored context. A single eligible
// department resolves silently; several go straight to the form, which hosts
// the choice itself (NDS-DES-15-MULTIPLE) — there is no separate dialog.
async function onCreateClick() {
	const targets = await api.listNeedCreateTargets();
	if (!targets.open || !(targets.organisation_units || []).length) {
		// Server state moved since the last load (flag just closed, or the
		// actor's create scope changed) — refresh the list rather than guess.
		await load({ quiet: true });
		return;
	}
	createTargets.value = targets;
	const units = targets.organisation_units;
	selectedDepartment.value = units.length === 1 ? units[0].organisation_unit : "";
	if (selectedDepartment.value && contextKey.value !== selectedDepartment.value) {
		// Reuses the same server-side preference persistence the workspace
		// filter uses, so the list reflects the chosen department on return —
		// a convenience, not what the editor itself reads (see editorContext).
		contextKey.value = selectedDepartment.value;
		await load({ quiet: true });
	}
	go("new");
}

async function onCreateSuccessor() {
	const result = await run("create-successor", (key) =>
		api.createAcceptedNeedSuccessor({
			need: (detail.value.need || {}).name,
			expected_version: recordVersion(),
			idempotency_key: key,
		})
	);
	if (result) go(needReference.value, "edit");
}

// NDS-CHG-001 v1.13 §11.5/§11.16 — the editor's destructive footer button
// means something different per mode: a successor's is "Cancel update"
// (unwinds the proposal only), a Draft/Returned's is "Withdraw need" (a real
// lifecycle command via NDS-DES-13 WITHDRAW-DRAFT), and a brand new unsaved
// form's is a plain, mutation-free "Cancel".
function onEditorCancel() {
	if (editorMode.value === "successor") {
		dialog.value = "cancel-successor";
		return;
	}
	if (!needReference.value) {
		// §12.3 — Cancel on a new unsaved form creates no mutation.
		go();
		return;
	}
	dialog.value = "withdraw-draft";
}

function onRowAction(row, action) {
	if (action.code === "review") {
		go("review", action.task);
	} else if (action.code === "withdrawal") {
		// §12.6 — a withdrawal decision is its own screen (NDS-UI-07) under the
		// same task, not the acceptance task screen.
		go("review", action.task, "withdrawal");
	} else if (action.code === "edit") {
		go(row.reference, "edit");
	} else {
		go(row.reference);
	}
}

function onViewPlanItem() {
	const item = usage.value.active_plan_item || dependency.value.active_plan_item;
	if (item) frappe.set_route("procurement-plan-item", item);
}

// NDS-DES-12-UNAVAILABLE — Try again re-runs the exact same check; a second
// failure simply leaves `dependency.unavailable` set, no different from the
// first.
async function retryWithdrawalDependency() {
	const request = task.value.withdrawal_request || {};
	const needName = (task.value.need || {}).name;
	if (!needName) return;
	dependencyChecking.value = true;
	try {
		dependency.value = await api.checkWithdrawalDependency(needName, request.accepted_revision);
	} catch (e) {
		dependency.value = { unavailable: true };
	} finally {
		dependencyChecking.value = false;
	}
}

// §11.8A — a dedicated, independently-retriable re-check of the Planning
// status section, separate from the detail screen's own atomic load: fired
// once after the detail screen first renders (revalidate in place, AGENTS.md
// §6.4), and again from the UNAVAILABLE state's own Try again. The atomic
// `get_departmental_need()` payload already loaded into `usage`/`disposition`
// is kept as the pre-existing "last confirmed" value if this call is slow or
// fails, so the common case (this call succeeds quickly) is visually
// unchanged from before Phase 2.
async function refreshPlanningStatus() {
	const needName = needReference.value;
	if (!needName) return;
	planningChecking.value = true;
	try {
		const result = await api.getNeedPlanningStatus(needName);
		if (needReference.value !== needName) return; // superseded by navigation
		usage.value = result.planning_usage || {};
		disposition.value = result.planning_disposition || null;
		olderUsage.value = result.older_usage || null;
		planningCheckedAt.value = result.checked_at || "";
		planningUnavailable.value = false;
	} catch (e) {
		if (needReference.value !== needName) return;
		planningUnavailable.value = true;
	} finally {
		if (needReference.value === needName) planningChecking.value = false;
	}
}

// --- dialogs ---------------------------------------------------------------

function closeDialog() {
	dialog.value = "";
	reason.value = "";
	reasonError.value = "";
}

function openWithdrawalDialog() {
	dialog.value = "request-withdrawal";
}

const REASON_DIALOGS = {
	// NDS-DES-13 RETURN-INITIAL / RETURN-UPDATE — same title/field label
	// either way; only the confirm command differs.
	return: {
		title: "What needs to change?",
		fieldLabel: "Correction required",
		confirmLabel: "Return for correction",
		onConfirm: () => decide(api.returnNeedRevision, "return"),
	},
	// NDS-DES-13 DECLINE-INITIAL / DECLINE-UPDATE — title, field label and
	// confirm label all split by whether this is the initial submission or a
	// proposed update (§8.5).
	get decline() {
		const isSuccessor = task.value.task_type === "Successor acceptance";
		return {
			title: isSuccessor ? "Decline proposed changes" : "Do not take forward",
			fieldLabel: isSuccessor
				? "Why are you declining these changes?"
				: "Why are you declining this requirement?",
			confirmLabel: isSuccessor ? "Decline proposed changes" : "Do not take forward",
			destructive: true,
			onConfirm: () => decide(api.declineNeedRevision, "decline"),
		};
	},
	// NDS-DES-11 — exact copy; subject/subjectMeta name the accepted Need
	// unambiguously before the reason field.
	get "request-withdrawal"() {
		const need = detail.value.need || {};
		const revision = detail.value.current_revision || {};
		return {
			title: "Request withdrawal",
			subject: revision.title || "",
			subjectMeta: `${need.need_reference || ""} · Accepted revision ${revision.revision_number || ""}`,
			lede: "Explain why this accepted requirement should no longer be available for procurement planning.",
			fieldLabel: "Reason for withdrawal",
			confirmLabel: "Request withdrawal",
			onConfirm: () => requestWithdrawal(),
		};
	},
	// NDS-DES-13 DECLINE-WITHDRAWAL — exact copy.
	"decline-withdrawal": {
		title: "Decline withdrawal",
		fieldLabel: "Reason",
		confirmLabel: "Decline withdrawal",
		destructive: true,
		onConfirm: () => decideWithdrawal("decline"),
	},
};

const reasonDialog = computed(() => REASON_DIALOGS[dialog.value] || null);

const confirmDialog = computed(() => {
	if (dialog.value === "accept") {
		const revision = task.value.revision || {};
		return {
			title: "Accept for planning",
			subject: `${(task.value.need || {}).need_reference} · Revision ${revision.revision_number}`,
			// §12.5 fixes this sentence exactly.
			message:
				"Acceptance makes this revision available to Procurement Planning. It does not approve expenditure or create procurement authority.",
			confirmLabel: "Accept for planning",
			onConfirm: () => decide(api.acceptNeedRevision, "accept"),
		};
	}
	if (dialog.value === "approve-withdrawal") {
		// NDS-DES-13 APPROVE-WITHDRAWAL — exact copy.
		return {
			title: "Approve withdrawal?",
			message: "This withdraws the accepted requirement. Earlier decisions remain in history.",
			confirmLabel: "Approve withdrawal",
			onConfirm: () => decideWithdrawal("approve"),
		};
	}
	if (dialog.value === "cancel-successor") {
		// NDS-DES-13 CANCEL-UPDATE — exact copy.
		return {
			title: "Cancel these proposed changes?",
			message: "The previously accepted requirement will remain in effect.",
			confirmLabel: "Cancel update",
			destructive: true,
			onConfirm: () => cancelSuccessor(),
		};
	}
	if (dialog.value === "withdraw-draft") {
		// NDS-DES-13 WITHDRAW-DRAFT — exact copy.
		return {
			title: "Withdraw this need?",
			message:
				"This withdraws the unaccepted requirement. Earlier submissions and decisions remain in history.",
			confirmLabel: "Withdraw need",
			destructive: true,
			onConfirm: () => withdrawDraft(),
		};
	}
	return null;
});

async function decide(command, action) {
	const result = await run(action, (key) =>
		command({
			need: (task.value.need || {}).name,
			task: task.value.task,
			expected_version: (task.value.need || {}).record_version,
			decision_token: task.value.decision_token,
			idempotency_key: key,
			reason: reason.value,
		})
	);
	if (!result) return;
	closeDialog();
	go(result.need_reference);
}

async function requestWithdrawal() {
	const result = await run("request-withdrawal", (key) =>
		api.requestAcceptedNeedWithdrawal({
			need: (detail.value.need || {}).name,
			expected_version: recordVersion(),
			idempotency_key: key,
			reason: reason.value,
		})
	);
	if (!result) return;
	closeDialog();
	await load({ quiet: true });
}

async function decideWithdrawal(decision) {
	const result = await run(`withdrawal-${decision}`, (key) =>
		api.decideAcceptedNeedWithdrawal({
			need: (task.value.need || {}).name,
			task: task.value.task,
			decision,
			expected_version: (task.value.need || {}).record_version,
			decision_token: task.value.decision_token,
			idempotency_key: key,
			reason: reason.value,
		})
	);
	if (!result) return;
	closeDialog();
	// The decision is done; the workspace is the module's one landing (the
	// queue screen was removed — My Work is the cross-module inbox).
	go();
}

async function cancelSuccessor() {
	const result = await run("cancel-successor", (key) =>
		api.cancelAcceptedNeedSuccessor({
			need: (detail.value.need || {}).name,
			expected_version: recordVersion(),
			idempotency_key: key,
		})
	);
	if (!result) return;
	closeDialog();
	go(needReference.value);
}

// NDS-DES-13 WITHDRAW-DRAFT — §5.1: a Draft or Returned Need's own Author may
// withdraw it before acceptance.
async function withdrawDraft() {
	const result = await run("withdraw", (key) =>
		api.withdrawUnacceptedNeed({
			need: (detail.value.need || {}).name,
			expected_version: recordVersion(),
			idempotency_key: key,
		})
	);
	if (!result) return;
	closeDialog();
	go();
}

function clearFilters() {
	search.value = "";
	status.value = "";
}
</script>
