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
				:submission="submissionState"
				:needs="workspace.needs || []"
				:actions="workspace.actions || []"
				:count-label="workspace.count_label || ''"
				:financial-years="financialYears"
				:selected-financial-year="financialYear"
				v-model:search="search"
				v-model:status="status"
				@clear-filters="clearFilters"
				@create="onCreateClick"
				@reload="load"
				@action="onRowAction"
				@select-financial-year="onSelectFinancialYear"
				@change-context="onChangeContext"
			/>

			<NeedEditorScreen
				v-else-if="screen === 'editor'"
				:mode="editorMode"
				:version="detail.current_version || {}"
				:context="editorContext"
				:units="units"
				@unit-created="(unit) => units.push(unit)"
				:return-reason="detail.latest_return"
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
				:version="detail.current_version || {}"
				:accepted-version="detail.accepted_version || {}"
				:pinned-version="pinnedVersion"
				:usage="usage"
				:author-label="detail.author_label || ''"
				:accepted-by-label="acceptedBy.actor_label || ''"
				:accepted-at="acceptedBy.occurred_at || ''"
				:access-profile="detail.access_profile || ''"
				:withdrawal-open="withdrawalOpen"
				@create-update="onCreateSuccessor"
				@request-withdrawal="openWithdrawalDialog"
				@open-successor="go(needReference, 'edit')"
				@view-plan-item="onViewPlanItem"
			/>

			<ReviewTaskScreen
				v-else-if="screen === 'task'"
				:need="task.need || {}"
				:version="task.version || {}"
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
				:request="task.withdrawal_request || {}"
				:version="task.version || {}"
				:dependency="dependency"
				:requester-label="requesterLabel"
				:requested-at="task.opened_at || ''"
				:maker-checker-blocked="!!task.maker_checker_blocked"
				:error-summary="errorSummary"
				:pending="pending"
				@approve="dialog = 'approve-withdrawal'"
				@decline="dialog = 'decline-withdrawal'"
				@close="go()"
				@view-plan-item="onViewPlanItem"
			/>

		</div>

		<!-- §11.13 / §11.12 — the exact reason dialogs. -->
		<ReasonDialog
			v-if="reasonDialog"
			:title="reasonDialog.title"
			:lede="reasonDialog.lede"
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

		<!-- NDS-DES-15 §11.16/§12.1 — shown only when more than one authorised
		     Organisation Unit is eligible to create in the one open Fiscal Year. -->
		<CreateTargetDialog
			v-if="createTargetDialog"
			:organisation-units="createTargetChoices.organisation_units || []"
			:financial-year-label="createTargetChoices.financial_year_label || ''"
			:pending="pending"
			@continue="onCreateTargetContinue"
			@cancel="createTargetDialog = false"
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
import CreateTargetDialog from "./components/CreateTargetDialog.vue";
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
const dependency = ref({});
const units = ref([]);
const acceptedBy = ref({});
const dialog = ref("");
const reason = ref("");
const reasonError = ref("");
const financialYears = ref([]);
const createTargetDialog = ref(false);
const createTargetChoices = ref({});
// The exact department + the one open Fiscal Year resolved for the Need
// currently being created — from list_need_create_targets, never from the
// workspace's FY filter (see editorContext).
const createContext = ref(null);

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
// Rule 5.4 — "Change context" is always available: when set, the picker shows
// even though the server could resolve a remembered context.
const changingContext = ref(false);

const selectionRequired = computed(
	() =>
		!loading.value &&
		!error.value &&
		screen.value === "workspace" &&
		(changingContext.value ||
			workspace.value.outcome === "CONTEXT_SELECTION_REQUIRED" ||
			// The context is department *and* FY (§12.1). With several selectable
			// years, rows must not be listed against an unresolved one.
			(financialYears.value.length > 1 && !financialYear.value))
);

function onSelectContext(value) {
	contextKey.value = value;
	changingContext.value = false;
	load({ quiet: true });
}

function onSelectFinancialYear(value) {
	financialYear.value = value;
	load({ quiet: true });
}

function onChangeContext() {
	// Rule 5.4 — reopen the picker; the pick itself re-persists server-side.
	contextKey.value = "";
	changingContext.value = true;
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

// NDS-UI-06 pins the accepted version number in the route.
const pinnedVersionNumber = computed(() =>
	segments.value[1] === "accepted" ? Number(segments.value[2]) : null
);

const pinnedVersion = computed(() => {
	if (!pinnedVersionNumber.value) return null;
	const accepted = detail.value.accepted_version;
	if (accepted && Number(accepted.version_number) === pinnedVersionNumber.value) return accepted;
	// The route asked for a version that is no longer current: keep it readable
	// rather than redirecting (§12.4).
	return detail.value.pinned_version || accepted || null;
});

const editorMode = computed(() => {
	if (!needReference.value) return "create";
	const state = (detail.value.need || {}).current_state;
	if (state === "Accepted for planning") return "successor";
	// Only a Returned Need is being *corrected*; a Draft is simply continued.
	return state === "Returned" ? "correct" : "draft";
});

const editorContext = computed(() => {
	// NDS-DES-15 / §12.1 — the create target's own resolved department and the
	// one open Fiscal Year, never the workspace's FY *filter* (which offers
	// only years already represented by existing Needs — empty on a first
	// Need, and unrelated to which year is open for creation). Falls back to
	// the workspace context only for a direct URL load of /new (no
	// createContext yet resolved).
	if (!needReference.value) return createContext.value || workspace.value.context || {};
	// The artboards show scope by name, never by ID.
	const need = detail.value.need || {};
	const labels = detail.value.scope_labels || {};
	return {
		organisation_unit_label: labels.organisation_unit || need.organisation_unit,
		financial_year_label: labels.financial_year || need.financial_year,
	};
});

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
			const request = loadedTask.withdrawal_request || {};
			loadedDependency = await api.checkWithdrawalDependency(
				(loadedTask.need || {}).name,
				request.accepted_version
			);
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
		usage.value = { usage: detail.value.planning_usage };
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
		if (dialog.value) reasonError.value = e.message;
		else errorSummary.value = e.message;
		return null;
	} finally {
		pending.value = false;
	}
}

function recordVersion() {
	return (detail.value.need || {}).record_version;
}

async function onSaveDraft(form) {
	const result = await run("save-draft", (key) =>
		api.saveNeedDraft({
			need: needReference.value || "",
			...(needReference.value ? { expected_version: recordVersion() } : contextArgs()),
			...form,
			idempotency_key: key,
		})
	);
	if (!result) return;
	// §12.3 — the first save replaces the route with the generated reference.
	if (!needReference.value) go(result.need_reference, "edit");
	else await load({ quiet: true });
}

async function onSubmit(form) {
	const saved = await run("save-before-submit", (key) =>
		api.saveNeedDraft({
			need: needReference.value || "",
			...(needReference.value ? { expected_version: recordVersion() } : contextArgs()),
			...form,
			idempotency_key: key,
		})
	);
	if (!saved) return;
	const result = await run("submit", (key) =>
		api.submitNeedVersion({
			need: saved.need,
			expected_version: saved.record_version,
			idempotency_key: key,
		})
	);
	if (result) go(result.need_reference);
}

function contextArgs() {
	const context = createContext.value || workspace.value.context || {};
	return {
		organisation_unit: context.organisation_unit,
		financial_year: context.financial_year,
	};
}

// NDS-DES-15 / §12.1 — resolved at click time from the exact authorised
// create targets, never from a Fiscal Year permission, the list's current FY
// filter or a browser-stored context.
async function onCreateClick() {
	const targets = await api.listNeedCreateTargets();
	if (!targets.open || !(targets.organisation_units || []).length) {
		// Server state moved since the last load (flag just closed, or the
		// actor's create scope changed) — refresh the list rather than guess.
		await load({ quiet: true });
		return;
	}
	if (targets.organisation_units.length === 1) {
		await enterCreateEditor(targets, targets.organisation_units[0].organisation_unit);
		return;
	}
	createTargetChoices.value = targets;
	createTargetDialog.value = true;
}

async function enterCreateEditor(targets, organisationUnit) {
	const selected = (targets.organisation_units || []).find(
		(row) => row.organisation_unit === organisationUnit
	);
	createContext.value = {
		organisation_unit: organisationUnit,
		organisation_unit_label: selected?.organisation_unit_label || organisationUnit,
		financial_year: targets.financial_year,
		financial_year_label: targets.financial_year_label,
	};
	// Reuses the same server-side preference persistence the department picker
	// uses, so the workspace list reflects the chosen department on return —
	// a convenience, not what the editor itself reads (see editorContext).
	if (contextKey.value !== organisationUnit) {
		contextKey.value = organisationUnit;
		changingContext.value = false;
		await load({ quiet: true });
	}
	go("new");
}

function onCreateTargetContinue(organisationUnit) {
	createTargetDialog.value = false;
	enterCreateEditor(createTargetChoices.value, organisationUnit);
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
	go(needReference.value);
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
	// NDS-DES-13a
	return: {
		title: "Return for correction",
		lede: "Explain what the requester must correct before resubmission.",
		confirmLabel: "Return need",
		onConfirm: () => decide(api.returnNeedVersion, "return"),
	},
	// NDS-DES-13b
	decline: {
		title: "Do not take forward",
		lede: "Explain why this requirement will not be taken forward.",
		confirmLabel: "Do not take forward",
		destructive: true,
		onConfirm: () => decide(api.declineNeedVersion, "decline"),
	},
	// NDS-DES-11
	"request-withdrawal": {
		title: "Request withdrawal",
		lede: "Explain why this accepted need should no longer be used for procurement planning.",
		confirmLabel: "Submit request",
		onConfirm: () => requestWithdrawal(),
	},
	"decline-withdrawal": {
		title: "Decline withdrawal",
		lede: "Explain why this withdrawal request is declined.",
		confirmLabel: "Decline withdrawal",
		destructive: true,
		onConfirm: () => decideWithdrawal("decline"),
	},
};

const reasonDialog = computed(() => REASON_DIALOGS[dialog.value] || null);

const confirmDialog = computed(() => {
	if (dialog.value === "accept") {
		const version = task.value.version || {};
		return {
			title: "Accept for planning",
			subject: `${(task.value.need || {}).need_reference} · Version ${version.version_number}`,
			// §12.5 fixes this sentence exactly.
			message:
				"Acceptance makes this version available to Procurement Planning. It does not approve expenditure or create procurement authority.",
			confirmLabel: "Accept for planning",
			onConfirm: () => decide(api.acceptNeedVersion, "accept"),
		};
	}
	if (dialog.value === "approve-withdrawal") {
		return {
			title: "Approve withdrawal",
			message:
				"The accepted need will be withdrawn and Procurement Planning will be notified. This cannot be undone.",
			confirmLabel: "Approve withdrawal",
			onConfirm: () => decideWithdrawal("approve"),
		};
	}
	if (dialog.value === "cancel-successor") {
		return {
			title: "Cancel update",
			message:
				"The open update will be withdrawn. The earlier accepted version stays current.",
			confirmLabel: "Cancel update",
			destructive: true,
			onConfirm: () => cancelSuccessor(),
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

function clearFilters() {
	search.value = "";
	status.value = "";
}
</script>
