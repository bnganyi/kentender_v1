<!-- Tenders — TPR-CHG-001 v0.8 §11. One Page ("tenders") owns every route:
       /app/tenders                              workspace (TPR-DES-01)
       /app/tenders/new/{handoff}                Start dialog over the workspace (TPR-DES-02)
       /app/tenders/{ref}[/details|requirements|review]   the record — the server's
                                                 `screen` picks editor / approval /
                                                 authorisation / publication / published /
                                                 correction / cancelled / record
       /app/tenders/{ref}/publication            publication confirmation (TPR-DES-08) or
                                                 AO authorisation (TPR-DES-07)
       /app/tenders/{ref}/addenda/{a}            addendum (TPR-DES-10)
       /app/tenders/{ref}/inquiries/{i}          inquiry (TPR-DES-11)
       /app/tenders/{ref}/cancel                 cancellation (TPR-DES-12)
       /app/tenders/{ref}/history                history (D22)
     The root reads the route through core's useRoute adapter, keeps one
     payload cache per screen identity, guards every loader with a sequence
     token and every command with one pending gate (AGENTS.md §6.4). -->
<template>
	<div class="kt-industry kt-tnd">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="tnd-shell" :data-screen="screen" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'" :data-pending="pending ? 'true' : 'false'">
			<!-- inline states first: a verdict never renders behind content (KT-STD-001 §3A) -->
			<CommonState v-if="state" :kind="state.kind" :heading="state.heading" :text="state.text" :support-ref="state.kind === 'failure' ? supportRef : ''" @action="onStateAction" />

			<template v-else-if="kind === 'workspace' || kind === 'start'">
				<div :class="{ 'tnd-blurred': kind === 'start' }">
					<WorkspaceScreen :loading="loading && !workspace.outcome" :workspace="workspace" :filters="filters" :pending="pending" @navigate="onNavigate" @filter="onFilter" @clear-filters="onFilter({ search: '', status: '', fiscal_year: '' })" />
				</div>
				<StartTenderDialog v-if="kind === 'start' && startDetail.outcome === 'OK'" :detail="startDetail" :pending="pending" :error="dialogError" @confirm="onStart" @cancel="go()" />
			</template>

			<template v-else-if="kind === 'record'">
				<div v-if="loading" class="tnd-page"><div class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="tnd-record-loading"><div v-for="row in 3" :key="row" class="tnd-skel-row"><div class="kt-skel" style="width: 72%"></div><div class="kt-skel" style="width: 52%"></div><div class="kt-skel" style="width: 44%"></div></div></div></div>
				<EditorScreen v-else-if="screen === 'details' || screen === 'requirements'" ref="editorRef" :record="record" :task="screen" :field-errors="fieldErrors" :error="error" :pending="pending" @go-task="goTask" @open-drawer="drawer = $event === true ? 'full' : 'context'" @add-evidence="evidenceDialog = { row: null }" @edit-evidence="evidenceDialog = { row: $event }" @remove-evidence="onRemoveEvidence" @save="onSaveDraft(false)" @continue="onSaveDraft(true)" @back="onEditorBack" @request-correction="correctionDialog = true" />
				<ReviewScreen v-else-if="screen === 'review'" :record="record" :review="review" :pending="pending" @back="goTask('requirements')" @submit="submitDialog = true" @preview="onPreview" @go-finding="onGoFinding" />
				<ApprovalScreen v-else-if="screen === 'approval'" :record="record" :review="review" :pending="pending" @back="go()" @return="returnDialog = true" @approve="approveDialog = true" @preview="onPreview" @request-correction="correctionDialog = true" />
				<AuthorisationScreen v-else-if="screen === 'authorisation'" :pub="pub" :requisition-reference="record.tender.requisition_reference" :pending="pending" @authorise="authoriseDialog = true" @view-document="onViewDocument" />
				<PublicationScreen v-else-if="screen === 'publication'" :pub="pub" :invalid-evidence="invalidEvidence" :conflict="conflictRow" :withdrawn="withdrawnText" :pending="pending" @confirm-channel="channelDialog = { row: $event, subject: 'publication' }" @view-confirmation="confirmationView = $event" @view-document="onViewDocument" @withdraw="withdrawDialog = true" />
				<CorrectionRequestedScreen v-else-if="screen === 'correction'" :record="record" :pending="pending" @start-corrected="onStartCorrected" @view-requisition="onViewRequisition" @history="go(tenderRef, 'history')" />
				<CancelScreen v-else-if="screen === 'cancelled'" :data="cancelData" :pending="pending" :error="dialogError" @back="go()" @record-evidence="obligationDialog = { row: $event }" />
				<PublishedScreen v-else :record="record" :review="review" :pending="pending" @view-document="onViewDocument" @view-confirmation="confirmationView = $event" @open-addendum="go(tenderRef, 'addenda', $event)" @open-inquiry="go(tenderRef, 'inquiries', $event)" @prepare-addendum="onPrepareAddendum" @cancel-screen="go(tenderRef, 'cancel')" @history="go(tenderRef, 'history')" @reopen="reopenDialog = true" @request-correction="correctionDialog = true" @publication="go(tenderRef, 'publication')" />
			</template>

			<template v-else-if="kind === 'addendum'">
				<div v-if="loading" class="tnd-page"><div class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="tnd-record-loading"><div v-for="row in 3" :key="row" class="tnd-skel-row"><div class="kt-skel" style="width: 72%"></div><div class="kt-skel" style="width: 52%"></div></div></div></div>
				<AddendumScreen v-else :data="addendumData" :identity="addendumIdentity" :errors="fieldErrors" :pending="pending" @back="go(tenderRef)" @save="onSaveAddendum($event, false)" @submit="onSaveAddendum($event, true)" @return="addendumReturnDialog = true" @issue="issueDialog = true" @confirm-channel="channelDialog = { row: $event, subject: 'addendum' }" @view-confirmation="confirmationView = $event" @cancel-screen="go(tenderRef, 'cancel')" />
				<div v-if="error && !loading" class="tnd-page" style="padding-top: 12px"><div class="kt-notice is-critical" role="alert" data-testid="tnd-command-error"><div class="kt-notice-body">{{ error }}</div></div></div>
			</template>

			<template v-else-if="kind === 'inquiry'">
				<div v-if="loading" class="tnd-page"><div class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="tnd-record-loading"><div v-for="row in 3" :key="row" class="tnd-skel-row"><div class="kt-skel" style="width: 72%"></div></div></div></div>
				<InquiryScreen v-else :data="inquiryData" :pending="pending" :error="error" @back="go(tenderRef)" @send="onSendResponse" />
			</template>

			<template v-else-if="kind === 'cancel'">
				<div v-if="loading" class="tnd-page"><div class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="tnd-record-loading"><div v-for="row in 3" :key="row" class="tnd-skel-row"><div class="kt-skel" style="width: 72%"></div></div></div></div>
				<CancelScreen v-else :data="cancelData" :pending="pending" :error="error" @back="go(tenderRef)" @recommend="recommendDialog = $event" @cancel="cancelDialog = $event" @record-evidence="obligationDialog = { row: $event }" />
			</template>

			<template v-else-if="kind === 'history'">
				<div v-if="loading" class="tnd-page"><div class="kt-card kt-blueprint" style="padding: 0; overflow: hidden" data-testid="tnd-record-loading"><div v-for="row in 3" :key="row" class="tnd-skel-row"><div class="kt-skel" style="width: 72%"></div></div></div></div>
				<HistoryScreen v-else :data="historyData" @back="go(tenderRef)" @view-digest="onViewDigest" />
			</template>

			<!-- dialogs (in-Vue only, §6.3) -->
			<RequisitionDrawer v-if="drawer" :inherited="record.inherited || {}" :template-label="templateLabel" :opening-label="openingLabel" :full="drawer === 'full'" @close="drawer = ''" />
			<EvidenceDialog v-if="evidenceDialog" :row="evidenceDialog.row" :inherited="record.inherited || {}" :pending="pending" :error="dialogError" :server-errors="fieldErrors" @confirm="onEvidenceConfirm" @cancel="closeDialogs" />
			<ConfirmDialog v-if="submitDialog" testid="tnd-submit-dialog" title="Submit this Tender for approval?" note="The submitted Version will be locked. The Head of Procurement Function can return it or approve the package for publication review." confirm-label="Submit for approval" :pending="pending" :error="dialogError" @confirm="onSubmitForApproval" @cancel="closeDialogs" />
			<ReasonDialog v-if="returnDialog" testid="tnd-return-dialog" title="Return this Tender for correction?" reason-label="Correction required" placeholder="20–2,000 characters" after-label="Affected task" :options="affectedTaskOptions" :initial-choice="affectedTaskOptions[1]" note="The submitted Version will remain in history and a copied Draft will be created." confirm-label="Return for correction" :pending="pending" :error="dialogError" @confirm="onReturnForCorrection" @cancel="closeDialogs" />
			<ConfirmDialog v-if="approveDialog" testid="tnd-approve-dialog" title="Approve this Tender package?" :facts="approveFacts" note="The Accounting Officer must separately authorise publication. Suppliers cannot see this Tender yet." confirm-label="Approve Tender package" :pending="pending" :error="dialogError" @confirm="onApprove" @cancel="closeDialogs" />
			<ReasonDialog v-if="reopenDialog" testid="tnd-reopen-dialog" title="Reopen this approved Tender for correction?" reason-label="Reason" note="The approved Version stays in history and a copied Draft is created. Publication has not started." confirm-label="Reopen for correction" :pending="pending" :error="dialogError" @confirm="onReopen" @cancel="closeDialogs" />
			<ReasonDialog v-if="correctionDialog" testid="tnd-correction-dialog" title="Request a requisition correction?" reason-label="Reason" note="This Tender Version will stop and remain in history. Work can continue only from a newly authorised corrected Requisition." confirm-label="Request requisition correction" danger :pending="pending" :error="dialogError" @confirm="onRequestCorrection" @cancel="closeDialogs" />
			<ConfirmDialog v-if="authoriseDialog" testid="tnd-authorise-dialog" title="Authorise publication of this Tender?" intro="This allows the Head of Procurement Function to publish the exact approved Invitation and Tender through every required channel and confirm the evidence. It does not itself publish the Tender or edit the package." :facts="authoriseFacts" confirm-label="Authorise publication" :pending="pending" :error="dialogError" @confirm="onAuthorise" @cancel="closeDialogs" />
			<ChannelConfirmationDialog v-if="channelDialog" :channel="channelDialog.row" :attestation="attestationFor(channelDialog)" :subject-word="channelDialog.subject === 'addendum' ? 'addendum' : 'Invitation and complete Tender'" :pending="pending" :error="dialogError" :server-errors="fieldErrors" @confirm="onConfirmChannel" @cancel="closeDialogs" />
			<ConfirmationViewDialog v-if="confirmationView" :row="confirmationView" @close="confirmationView = null" />
			<ReasonDialog v-if="withdrawDialog" testid="tnd-withdraw-dialog" title="Withdraw publication authorisation?" reason-label="Reason and evidence that nothing was published" note="Possible only while no channel is confirmed. The Tender returns to Approved." confirm-label="Withdraw authorisation" danger :pending="pending" :error="dialogError" @confirm="onWithdraw" @cancel="closeDialogs" />
			<DocumentDialog v-if="documentDialog" v-bind="documentDialog" @close="documentDialog = null" />
			<ConfirmDialog v-if="issueDialog" testid="tnd-issue-dialog" title="Issue this addendum?" note="Issue is immutable. Channel confirmation follows separately from this decision." confirm-label="Issue addendum" :pending="pending" :error="dialogError" @confirm="onIssueAddendum" @cancel="closeDialogs" />
			<ReasonDialog v-if="addendumReturnDialog" testid="tnd-addendum-return-dialog" title="Return this addendum for correction?" reason-label="Correction required" :min="5" confirm-label="Return for correction" :pending="pending" :error="dialogError" @confirm="onReturnAddendum" @cancel="closeDialogs" />
			<ConfirmDialog v-if="recommendDialog" testid="tnd-recommend-dialog" title="Recommend cancellation of this Tender?" :facts="[{ label: 'Ground', value: recommendDialog.ground_label }, { label: 'Tender', value: tenderRef }]" note="A recommendation is recorded for the Accounting Officer. It does not change the Tender's status." confirm-label="Recommend cancellation" :pending="pending" :error="dialogError" @confirm="onRecommend" @cancel="closeDialogs" />
			<ConfirmDialog v-if="cancelDialog" testid="tnd-cancel-dialog" title="Cancel this Tender?" :facts="cancelFacts" note="The decision is final and the cancellation notices and reports will remain due until evidence is recorded." confirm-label="Cancel Tender" cancel-label="Keep Tender" danger :pending="pending" :error="dialogError" @confirm="onCancelTender" @cancel="closeDialogs" />
			<ObligationEvidenceDialog v-if="obligationDialog" :obligation="obligationDialog.row" :pending="pending" :error="dialogError" :server-errors="fieldErrors" @confirm="onRecordObligation" @cancel="closeDialogs" />
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouteState } from "../tnd_shared/composables/useRouteState.js";
import { usePageRail } from "../tnd_shared/composables/usePageRail.js";
import * as api from "./data/tendersApi.js";
import { fileSize } from "./data/format.js";
import CommonState from "./components/CommonState.vue";
import WorkspaceScreen from "./components/WorkspaceScreen.vue";
import StartTenderDialog from "./components/StartTenderDialog.vue";
import EditorScreen from "./components/EditorScreen.vue";
import RequisitionDrawer from "./components/RequisitionDrawer.vue";
import EvidenceDialog from "./components/EvidenceDialog.vue";
import ReviewScreen from "./components/ReviewScreen.vue";
import ApprovalScreen from "./components/ApprovalScreen.vue";
import AuthorisationScreen from "./components/AuthorisationScreen.vue";
import PublicationScreen from "./components/PublicationScreen.vue";
import PublishedScreen from "./components/PublishedScreen.vue";
import CorrectionRequestedScreen from "./components/CorrectionRequestedScreen.vue";
import AddendumScreen from "./components/AddendumScreen.vue";
import InquiryScreen from "./components/InquiryScreen.vue";
import CancelScreen from "./components/CancelScreen.vue";
import HistoryScreen from "./components/HistoryScreen.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import ReasonDialog from "./components/ReasonDialog.vue";
import ChannelConfirmationDialog from "./components/ChannelConfirmationDialog.vue";
import ConfirmationViewDialog from "./components/ConfirmationViewDialog.vue";
import DocumentDialog from "./components/DocumentDialog.vue";
import ObligationEvidenceDialog from "./components/ObligationEvidenceDialog.vue";

const PAGE = "tenders";
const { route, epoch } = useRouteState(PAGE);
const cache = kentender_core.desk_page.createScreenCache();
const loadGuard = kentender_core.desk_page.createSequenceGuard();

const railEl = ref(null);
const loading = ref(true);
const refreshing = ref(false);
const pending = ref(false);
const error = ref("");
const errorCode = ref("");
const dialogError = ref("");
const fieldErrors = ref({});
const supportRef = ref("");
const staleWrite = ref(false);
const filters = ref({ search: "", status: "", fiscal_year: "" });

const workspace = ref({});
const startDetail = ref({});
const record = ref({ tender: {} });
const review = ref({});
const pub = ref({ tender: {} });
const addendumData = ref({ tender: {} });
const inquiryData = ref({ tender: {}, inquiry: {} });
const cancelData = ref({ tender: {} });
const historyData = ref({ tender: {} });

const editorRef = ref(null);
const drawer = ref("");
const evidenceDialog = ref(null);
const submitDialog = ref(false);
const returnDialog = ref(false);
const approveDialog = ref(false);
const reopenDialog = ref(false);
const correctionDialog = ref(false);
const authoriseDialog = ref(false);
const channelDialog = ref(null);
const confirmationView = ref(null);
const withdrawDialog = ref(false);
const documentDialog = ref(null);
const issueDialog = ref(false);
const addendumReturnDialog = ref(false);
const recommendDialog = ref(null);
const cancelDialog = ref(null);
const obligationDialog = ref(null);
const invalidEvidence = ref(false);
const conflictRow = ref(null);
const withdrawnText = ref("");

// ---------------------------------------------------------------- routing
const segments = computed(() => route.value.slice(1).filter(Boolean));
const tenderRef = computed(() => (segments.value[0] && segments.value[0] !== "new" ? segments.value[0] : ""));
const handoff = computed(() => (segments.value[0] === "new" ? segments.value[1] || "" : ""));
const sub = computed(() => segments.value[1] || "");
const subId = computed(() => segments.value[2] || "");
const TASKS = ["details", "requirements", "review"];

const kind = computed(() => {
	if (!segments.value.length) return "workspace";
	if (segments.value[0] === "new") return "start";
	if (sub.value === "addenda" && subId.value) return "addendum";
	if (sub.value === "inquiries" && subId.value) return "inquiry";
	if (sub.value === "cancel") return "cancel";
	if (sub.value === "history") return "history";
	return "record";
});
const screenKey = computed(() => {
	if (kind.value === "workspace") return "workspace";
	if (kind.value === "start") return `start:${handoff.value}`;
	if (kind.value === "record") return `record:${tenderRef.value}`;
	return `${kind.value}:${tenderRef.value}:${subId.value}`;
});

// The rendered screen: the server's verdict first, then its `screen`, then
// the route's task segment for the officer's editor.
const screen = computed(() => {
	if (state.value) return state.value.kind;
	if (kind.value !== "record") return kind.value;
	const s = record.value.screen || "record";
	if (s === "editor") return TASKS.includes(sub.value) ? sub.value : "details";
	if (sub.value === "publication") return ["authorisation", "publication"].includes(s) ? s : s === "published" ? "published" : s;
	if (s === "approval" && sub.value === "review") return "approval";
	return s;
});

const state = computed(() => {
	if (error.value && staleWrite.value) return { kind: "stale" };
	if (error.value && !dialogOpen.value && kind.value !== "addendum" && kind.value !== "inquiry" && kind.value !== "cancel" && !(kind.value === "record" && ["details", "requirements"].includes(record.value.screen === "editor" ? (TASKS.includes(sub.value) ? sub.value : "details") : ""))) return { kind: "failure" };
	if (kind.value === "workspace" || kind.value === "start") {
		if (workspace.value.outcome === "FORBIDDEN") return { kind: "forbidden", ...(workspace.value.forbidden || {}) };
		if (kind.value === "start" && startDetail.value.outcome) {
			const o = startDetail.value.outcome;
			if (o === "NOT_FOUND") return { kind: "not-found" };
			if (o === "SOURCE_UNAVAILABLE") return { kind: "source-unavailable", heading: startDetail.value.heading, text: startDetail.value.text };
			if (o === "ALREADY_STARTED") return { kind: "already-started", heading: startDetail.value.heading, text: startDetail.value.text };
			if (o === "OK" && startDetail.value.template && startDetail.value.template.available === false) return { kind: "template-unavailable" };
		}
		return null;
	}
	const data = { record: record.value, addendum: addendumData.value, inquiry: inquiryData.value, cancel: cancelData.value, history: historyData.value }[kind.value] || record.value;
	if (data && data.outcome === "NOT_FOUND") return { kind: "not-found", heading: data.heading, text: data.text };
	if (kind.value === "record" && pub.value && pub.value.rule_error === "TND_PUBLICATION_RULE_UNAVAILABLE" && record.value.screen === "authorisation") return { kind: "rule-unavailable" };
	return null;
});
const dialogOpen = computed(() => !!(evidenceDialog.value || submitDialog.value || returnDialog.value || approveDialog.value || reopenDialog.value || correctionDialog.value || authoriseDialog.value || channelDialog.value || withdrawDialog.value || issueDialog.value || addendumReturnDialog.value || recommendDialog.value || cancelDialog.value || obligationDialog.value));

function go(...parts) {
	frappe.set_route(PAGE, ...parts.filter(Boolean));
}
function goTask(task) {
	go(tenderRef.value, task);
}
function onNavigate(routeSegments) {
	if (routeSegments && routeSegments.length) frappe.set_route(...routeSegments);
}

// ---------------------------------------------------------------- loading
function newSupportRef() {
	const now = new Date();
	const pad = (n) => String(n).padStart(2, "0");
	return `TND-ERR-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
}

async function fetchFor() {
	switch (kind.value) {
		case "workspace":
			return { workspace: await api.getTendersWorkspace(filters.value) };
		case "start": {
			const [ws, detail] = await Promise.all([api.getTendersWorkspace(filters.value), api.getTenderStart(handoff.value)]);
			return { workspace: ws, startDetail: detail };
		}
		case "record": {
			const rec = await api.getTender(tenderRef.value);
			if (rec.outcome !== "OK") return { record: rec };
			const s = rec.screen;
			const out = { record: rec };
			if (s === "authorisation" || s === "publication" || sub.value === "publication") out.pub = await api.getTenderPublication(tenderRef.value);
			else if (s === "cancelled") out.cancelData = await api.getTenderCancellation(tenderRef.value);
			else if (!(s === "editor" && sub.value !== "review")) out.review = await api.getTenderReview(tenderRef.value);
			return out;
		}
		case "addendum":
			return { addendumData: await api.getTenderAddendum(tenderRef.value, subId.value) };
		case "inquiry":
			return { inquiryData: await api.getAddendumInquiry(tenderRef.value, subId.value) };
		case "cancel":
			return { cancelData: await api.getTenderCancellation(tenderRef.value) };
		case "history":
			return { historyData: await api.getTenderHistory(tenderRef.value) };
		default:
			return {};
	}
}
function applyLoaded(loaded) {
	if (loaded.workspace) workspace.value = loaded.workspace;
	if (loaded.startDetail) startDetail.value = loaded.startDetail;
	if (loaded.record) record.value = loaded.record;
	if (loaded.review) review.value = loaded.review;
	if (loaded.pub) pub.value = loaded.pub;
	if (loaded.addendumData) addendumData.value = loaded.addendumData;
	if (loaded.inquiryData) inquiryData.value = loaded.inquiryData;
	if (loaded.cancelData) cancelData.value = loaded.cancelData;
	if (loaded.historyData) historyData.value = loaded.historyData;
}
let inFlightKey = "";
async function load(opts) {
	const key = screenKey.value;
	const cached = cache.get(key);
	if (opts && opts.entering && cached) applyLoaded(cached);
	const quiet = !!(opts && opts.quiet === true) || !!cached;
	if (quiet && inFlightKey === key) return;
	const token = loadGuard.next();
	inFlightKey = key;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = "";
	errorCode.value = "";
	staleWrite.value = false;
	try {
		const loaded = await fetchFor();
		if (!loadGuard.isCurrent(token)) return;
		cache.set(key, loaded);
		applyLoaded(loaded);
	} catch (e) {
		if (!loadGuard.isCurrent(token)) return;
		error.value = e.message;
		errorCode.value = e.code || "";
		supportRef.value = newSupportRef();
	} finally {
		if (loadGuard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
			inFlightKey = "";
		}
	}
}
function onFilter(next) {
	filters.value = next;
	cache.set(screenKey.value, null);
	load({ quiet: true });
}
function onStateAction(k) {
	if (k === "stale" || k === "failure") {
		error.value = "";
		staleWrite.value = false;
		load({ quiet: !!cache.get(screenKey.value) });
		return;
	}
	if (k === "already-started" && startDetail.value.route) {
		onNavigate(startDetail.value.route);
		return;
	}
	if (k === "rule-unavailable") {
		frappe.set_route("system-setup");
		return;
	}
	go();
}

// ---------------------------------------------------------------- commands
// One pending gate for every command; the post-mutation reload is awaited
// inside the guarded function (AGENTS.md §6.4). A TND_STALE_VERSION refusal
// becomes the Stale write state; a `{ok:false, errors}` result becomes
// inline field errors; anything else the dialog's (or the screen's) own
// inline message — never a Frappe modal (§6.10).
async function run(fn, opts) {
	if (pending.value) return null;
	pending.value = true;
	dialogError.value = "";
	fieldErrors.value = {};
	if (!(opts && opts.keepError)) error.value = "";
	try {
		const result = await fn();
		if (result && result.ok === false && result.errors) {
			fieldErrors.value = result.errors;
			const first = Object.values(result.errors)[0];
			(opts && opts.dialog ? dialogError : error).value = typeof first === "string" ? first : "Correct the highlighted fields.";
			return null;
		}
		return result;
	} catch (e) {
		if (e.code === "TND_STALE_VERSION") {
			staleWrite.value = true;
			error.value = e.message;
			closeDialogs();
			return null;
		}
		if (e.detail && e.detail.fields) fieldErrors.value = e.detail.fields;
		(opts && opts.dialog ? dialogError : error).value = e.message;
		if (opts && opts.onError) opts.onError(e);
		return null;
	} finally {
		pending.value = false;
	}
}
function closeDialogs() {
	evidenceDialog.value = null;
	submitDialog.value = returnDialog.value = approveDialog.value = reopenDialog.value = correctionDialog.value = authoriseDialog.value = withdrawDialog.value = issueDialog.value = addendumReturnDialog.value = false;
	channelDialog.value = recommendDialog.value = cancelDialog.value = obligationDialog.value = null;
	dialogError.value = "";
}
const rv = () => (record.value.tender || {}).record_version;

async function onStart() {
	const result = await run(() => api.startTender({ handoff: handoff.value, idempotency_key: api.newIdempotencyKey("start") }), { dialog: true });
	if (!result) return;
	cache.set("workspace", null);
	go(result.tender_reference || result.tender, "details");
}
async function onSaveDraft(continueNext) {
	const task = screen.value;
	const payload = editorRef.value ? editorRef.value.getPayload() : {};
	const result = await run(async () => {
		const r = await api.saveTenderDraft({ tender: tenderRef.value, draft_values: JSON.stringify(payload), expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("save") });
		if (r && r.ok !== false) await load({ quiet: true });
		return r;
	});
	if (!result) return;
	if (continueNext) goTask(task === "details" ? "requirements" : "review");
}
async function onEditorBack() {
	if (editorRef.value && editorRef.value.isDirty()) {
		const saved = await run(async () => {
			const r = await api.saveTenderDraft({ tender: tenderRef.value, draft_values: JSON.stringify(editorRef.value.getPayload()), expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("save") });
			if (r && r.ok !== false) await load({ quiet: true });
			return r;
		});
		if (!saved) return;
	}
	if (screen.value === "requirements") goTask("details");
	else go();
}
async function onEvidenceConfirm(values) {
	const editing = evidenceDialog.value && evidenceDialog.value.row;
	const result = await run(async () => {
		const args = { tender: tenderRef.value, evidence_values: JSON.stringify(values), expected_record_version: rv(), idempotency_key: api.newIdempotencyKey(editing ? "update-evidence" : "add-evidence") };
		const r = editing ? await api.updateTenderEvidenceRequirement({ ...args, evidence_requirement_id: editing.evidence_requirement_id }) : await api.addTenderEvidenceRequirement(args);
		if (r && r.ok !== false) await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) evidenceDialog.value = null;
}
async function onRemoveEvidence(row) {
	await run(async () => {
		const r = await api.removeTenderEvidenceRequirement({ tender: tenderRef.value, evidence_requirement_id: row.evidence_requirement_id, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("remove-evidence") });
		await load({ quiet: true });
		return r;
	});
}
async function onSubmitForApproval() {
	const result = await run(() => api.submitTenderForApproval({ tender: tenderRef.value, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("submit") }), { dialog: true });
	if (!result) return;
	closeDialogs();
	cache.set(screenKey.value, null);
	cache.set("workspace", null);
	go();
}
const affectedTaskOptions = computed(() => (record.value.options || {}).affected_tasks || ["Tender details", "Supplier and contract requirements", "Review and generated documents"]);
async function onReturnForCorrection({ reason, choice }) {
	const result = await run(() => api.returnTenderForCorrection({ tender: tenderRef.value, reason, affected_task: choice, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("return") }), { dialog: true });
	if (!result) return;
	closeDialogs();
	cache.set(screenKey.value, null);
	cache.set("workspace", null);
	go();
}
const approveFacts = computed(() => [
	{ label: "Tender", value: tenderRef.value },
	{ label: "Version", value: `Version ${(record.value.version || {}).version_number || ""}` },
	{ label: "Submission deadline", value: ((review.value.key_facts || []).find((f) => f.label === "Submission deadline") || {}).value || "" },
	{ label: "Documents", value: "Invitation and complete Tender" },
]);
async function onApprove() {
	const result = await run(() => api.approveTenderPackage({ tender: tenderRef.value, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("approve") }), { dialog: true });
	if (!result) return;
	closeDialogs();
	cache.set(screenKey.value, null);
	cache.set("workspace", null);
	go();
}
async function onReopen({ reason }) {
	const result = await run(async () => {
		const r = await api.reopenApprovedTender({ tender: tenderRef.value, reason, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("reopen") });
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}
async function onRequestCorrection({ reason }) {
	const result = await run(async () => {
		const r = await api.requestRequisitionCorrection({ tender: tenderRef.value, reason, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("correction") });
		cache.set(screenKey.value, null);
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}
async function onStartCorrected(handoffName) {
	const result = await run(() => api.startCorrectedTenderVersion({ tender: tenderRef.value, handoff: handoffName, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("start-corrected") }));
	if (!result) return;
	cache.set(screenKey.value, null);
	go(tenderRef.value, "details");
}
function onViewRequisition(name) {
	frappe.set_route("procurement-requisitions", name);
}
const authoriseFacts = computed(() => [
	{ label: "Package", value: `Version ${((pub.value || {}).approval_trail || {}).version_number || ""}` },
	{ label: "Submission deadline", value: (pub.value.tender || {}).submission_deadline_label || ((pub.value.key_facts || []).find((f) => f.label === "Submission deadline") || {}).value || "" },
	{ label: "Required channels", value: String((pub.value.proposed_channels || []).length) },
]);
async function onAuthorise() {
	const task = pub.value.ao_task || {};
	const result = await run(async () => {
		const r = await api.authoriseTenderPublication({ tender: tenderRef.value, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("authorise"), task: task.name || "", task_token: task.task_token || "" });
		cache.set(screenKey.value, null);
		cache.set("workspace", null);
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}
function attestationFor(dialog) {
	const source = dialog.subject === "addendum" ? addendumData.value.attestations : pub.value.attestations;
	return (source || {})[dialog.row.channel] || `I confirm that the exact approved package was publicly available through ${dialog.row.channel_label} at the date and time stated above.`;
}
async function onConfirmChannel(values) {
	const d = channelDialog.value;
	invalidEvidence.value = false;
	conflictRow.value = null;
	const result = await run(async () => {
		let r;
		if (d.subject === "addendum") {
			r = await api.confirmAddendumPublicationChannel({ tender: tenderRef.value, addendum: subId.value, channel: d.row.channel, addendum_digest: (addendumData.value.addendum || {}).addendum_digest, expected_record_version: (addendumData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("confirm-addendum-channel"), ...values });
		} else {
			r = await api.confirmPublicationChannel({ tender: tenderRef.value, channel: d.row.channel, package_digest: (pub.value.publication || {}).package_digest, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("confirm-channel"), ...values });
		}
		cache.set(screenKey.value, null);
		await load({ quiet: true });
		return r;
	}, {
		dialog: true,
		onError: (e) => {
			if (e.code === "TND_PUBLICATION_EVIDENCE_INVALID") {
				invalidEvidence.value = true;
				closeDialogs();
			}
			if (e.code === "TND_PUBLICATION_ALREADY_CONFIRMED") {
				conflictRow.value = d.row;
				closeDialogs();
				load({ quiet: true });
			}
		},
	});
	if (result) {
		closeDialogs();
		if (result.published_at || (result.publication_status === "Published")) {
			cache.set("workspace", null);
		}
	}
}
async function onWithdraw({ reason }) {
	const result = await run(async () => {
		const r = await api.withdrawPublicationAuthorisation({ tender: tenderRef.value, reason, evidence: reason, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("withdraw") });
		cache.set(screenKey.value, null);
		cache.set("workspace", null);
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) {
		closeDialogs();
		withdrawnText.value = "The Tender is back at Approved.";
		go(tenderRef.value);
	}
}
async function onPreview(which) {
	documentDialog.value = { title: which === "invitation" ? "Preview Invitation" : "Preview complete Tender", fileName: which === "invitation" ? "Invitation (preview)" : "Complete Tender (preview)", format: "HTML", loading: true };
	try {
		const out = await api.previewTenderDocuments(tenderRef.value);
		if (out.outcome !== "OK") throw new Error(out.text || "Preview unavailable.");
		documentDialog.value = { ...documentDialog.value, loading: false, html: which === "invitation" ? out.invitation_html : out.issued_tender_html, digest: which === "invitation" ? out.invitation_digest : out.issued_tender_digest };
	} catch (e) {
		documentDialog.value = { ...documentDialog.value, loading: false, error: e.message };
	}
}
async function onViewDocument(kindName, audience) {
	const docs = record.value.documents || pub.value.documents || [];
	const doc = [...docs].reverse().find((d) => d.kind === kindName);
	if (!doc) {
		documentDialog.value = { title: `View ${kindName}`, loading: false, error: "This document has not been generated yet." };
		return;
	}
	await onViewDigest(doc, audience);
}
async function onViewDigest(doc, audience) {
	documentDialog.value = { title: `View ${doc.kind}`, fileName: doc.file_name || doc.kind, format: doc.format || "HTML", size: doc.size ? fileSize(doc.size) : "", digest: doc.digest, loading: true };
	try {
		const out = await api.getTenderDocument(doc.digest, audience || "Internal");
		if (out.outcome !== "OK") throw new Error(out.text || "Document unavailable.");
		documentDialog.value = { ...documentDialog.value, loading: false, html: out.html, fileName: out.pdf ? out.pdf.file_name : documentDialog.value.fileName, format: out.pdf ? "PDF" : "HTML", size: out.pdf ? fileSize(out.pdf.size) : "", downloadUrl: out.pdf ? out.pdf.url : "" };
	} catch (e) {
		documentDialog.value = { ...documentDialog.value, loading: false, error: e.message };
	}
}
function onGoFinding(f) {
	const task = f.task === "details" ? "details" : f.task === "requirements" ? "requirements" : "review";
	goTask(task);
}
async function onPrepareAddendum() {
	const result = await run(() => api.createAddendumDraft({ tender: tenderRef.value, expected_record_version: rv(), idempotency_key: api.newIdempotencyKey("addendum") }));
	if (!result) return;
	cache.set(screenKey.value, null);
	go(tenderRef.value, "addenda", result.addendum.name);
}
const addendumIdentity = computed(() => `${subId.value}:${(addendumData.value.addendum || {}).record_version}:${(addendumData.value.tender || {}).record_version}`);
async function onSaveAddendum(values, submitAfter) {
	const result = await run(async () => {
		const r = await api.updateAddendumDraft({ tender: tenderRef.value, addendum: subId.value, addendum_values: JSON.stringify(values), expected_record_version: (addendumData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("save-addendum") });
		if (r && r.ok !== false) await load({ quiet: true });
		return r;
	});
	if (!result || !submitAfter) return;
	await run(async () => {
		const r = await api.submitAddendumForIssue({ tender: tenderRef.value, addendum: subId.value, expected_record_version: (addendumData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("submit-addendum") });
		cache.set(`record:${tenderRef.value}`, null);
		await load({ quiet: true });
		return r;
	});
}
async function onReturnAddendum({ reason }) {
	const result = await run(async () => {
		const r = await api.returnAddendumForCorrection({ tender: tenderRef.value, addendum: subId.value, reason, expected_record_version: (addendumData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("return-addendum") });
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}
async function onIssueAddendum() {
	const task = addendumData.value.task || {};
	const result = await run(async () => {
		const r = await api.issueAddendum({ tender: tenderRef.value, addendum: subId.value, expected_record_version: (addendumData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("issue-addendum"), task: task.name || "", task_token: task.task_token || "" });
		cache.set(`record:${tenderRef.value}`, null);
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}
async function onSendResponse({ response, affects_requirements }) {
	const result = await run(async () => {
		const r = await api.respondToAddendumInquiry({ tender: tenderRef.value, inquiry: subId.value, response, affects_requirements, expected_record_version: (inquiryData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("respond") });
		cache.set(`record:${tenderRef.value}`, null);
		await load({ quiet: true });
		return r;
	});
	if (result) go(tenderRef.value);
}
async function onRecommend() {
	const v = recommendDialog.value;
	const result = await run(async () => {
		const r = await api.recommendTenderCancellation({ tender: tenderRef.value, ground: v.ground, reason: v.reason, expected_record_version: (cancelData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("recommend") });
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}
const cancelFacts = computed(() => [
	{ label: "Ground", value: (cancelDialog.value || {}).ground_label || "" },
	{ label: "Tender", value: tenderRef.value },
	{ label: "Decision date", value: new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) },
	{ label: "Channels", value: String(((cancelData.value.summary || {}).channel_count) || 0) },
]);
async function onCancelTender() {
	const v = cancelDialog.value;
	const result = await run(async () => {
		const r = await api.cancelTender({ tender: tenderRef.value, ground: v.ground, reason: v.reason, expected_record_version: (cancelData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("cancel") });
		cache.set(`record:${tenderRef.value}`, null);
		cache.set("workspace", null);
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}
async function onRecordObligation(values) {
	const o = obligationDialog.value.row;
	const result = await run(async () => {
		const r = await api.recordCancellationComplianceEvidence({ tender: tenderRef.value, obligation_id: o.obligation_id, expected_record_version: (cancelData.value.tender || {}).record_version, idempotency_key: api.newIdempotencyKey("obligation"), ...values });
		cache.set(screenKey.value, null);
		await load({ quiet: true });
		return r;
	}, { dialog: true });
	if (result) closeDialogs();
}

// ---------------------------------------------------------------- derived
const templateLabel = computed(() => {
	const id = (record.value.tender || {}).template_release_id || "";
	return id ? `IT Equipment — Open Tender · ${id}` : "";
});
const openingLabel = computed(() => {
	const v = record.value.officer_values || {};
	const label = ((review.value.key_facts || []).find((f) => f.label === "Submission deadline") || {}).value;
	return v.submission_deadline ? `${label || v.submission_deadline} (generated, equal to submission deadline)` : "";
});

// ---------------------------------------------------------------- watches
watch(segments, () => {
	closeDialogs();
	drawer.value = "";
	documentDialog.value = null;
	confirmationView.value = null;
	invalidEvidence.value = false;
	conflictRow.value = null;
	fieldErrors.value = {};
	load({ entering: true });
}, { immediate: true, deep: true });
watch(epoch, () => {
	if (cache.has(screenKey.value)) load({ quiet: true });
});

const railTrail = computed(() => {
	const trail = [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "Tenders", route: [PAGE] }];
	if (kind.value === "start") trail.push({ label: "Start Tender" });
	if (tenderRef.value) trail.push({ label: tenderRef.value, route: [PAGE, tenderRef.value] });
	const subLabels = { publication: "Publication", addenda: "Addendum", inquiries: "Inquiry", cancel: "Cancellation", history: "History", review: "Review", requirements: "Requirements", details: "Details" };
	if (sub.value && subLabels[sub.value]) trail.push({ label: subLabels[sub.value] });
	return trail;
});
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
