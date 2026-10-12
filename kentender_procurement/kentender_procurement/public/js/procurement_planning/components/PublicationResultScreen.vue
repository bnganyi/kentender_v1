<!-- PLN-CHG-001 v1.31 §10.12 — publication confirmation (U13).

     For MVP 1 the entity submits the approved plan to the National Treasury
     and publishes it on its own website outside KenTender, and the
     Procurement Planner records both completed facts here, in one
     confirmation. Four facts, four rows, and none of them proves another: the
     plan was approved; it was submitted to Treasury; it was published on the
     website; and it is or is not available for procurement.

     Nothing on this screen transmits, retries or reconciles — v1.30's
     Accounting Officer Treasury form, the Head of Procurement Function's
     Publish and the technical Retry / Check are retired. Confirming runs the
     existing activation checks; a plan that is confirmed but not activated is
     shown as published-but-held, with the evidence kept.

     The form holds the Planner's own typing (AGENTS.md §6.4): a refresh that
     carries the same Draft never refills it. -->
<template>
	<div>
		<div class="kt-page">
			<div class="kt-page-head">
				<div>
					<h1 class="kt-page-title" data-testid="pub-title">Confirm publication of the annual plan</h1>
					<p class="kt-page-desc">
						Record that the approved plan was submitted to the National Treasury and published on the entity’s website.
					</p>
					<div class="kt-page-scope" data-testid="pub-context">
						<span>{{ task.plan_reference }}</span>
						<span>· Version {{ task.version?.number }}</span>
					</div>
					<!-- The next-step line replaces the header state badge. -->
					<div ref="headEl" class="kt-guidance-mount" data-testid="pub-next-step-line"></div>
				</div>
				<div class="kt-page-actions">
					<button type="button" class="btn btn-ghost" data-testid="pub-view-plan" @click="$emit('navigate', ['annual-procurement-plan', task.plan_reference])">
						View approved plan
					</button>
					<button type="button" class="btn btn-ghost" data-testid="pub-download-plan" @click="$emit('download-plan')">
						Download approved plan
					</button>
					<button type="button" class="btn btn-ghost" data-testid="pub-download-plan-data" @click="$emit('download-plan-data')">
						Download Plan data
					</button>
				</div>
			</div>

			<!-- Always the reduced tracker: the four status rows below are the
			     working detail of stage 6, not a second tracker. -->
			<div ref="journeyEl" class="kt-guidance-mount" data-testid="pub-journey"></div>
			<div ref="bodyEl" class="kt-guidance-mount" data-testid="pub-next-step-block"></div>

			<!-- The four facts, each with its own label and state. -->
			<div class="kt-region">
				<h2>Publication status</h2>
				<table class="table" data-testid="pub-status">
					<thead>
						<tr><th>Step</th><th>State</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in statusRows" :key="row.label" data-testid="pub-status-row">
							<td>{{ row.label }}</td>
							<td><span class="kt-status" :class="`is-${row.kind}`">{{ row.state }}</span></td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- U13-WITHDRAWAL-REQUEST — a request that is open is its own state,
			     and the person who asked is named in it. -->
			<div v-if="task.withdrawal_request" class="kt-notice is-warning" data-testid="pub-withdrawal-state">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="12" cy="12" r="9"></circle><path d="M12 8h.01M11 12h1v5h1"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>Withdrawal requested — awaiting {{ task.withdrawal_request.capacity || "the approving authority" }}</strong>
					<p>{{ task.withdrawal_request.reason }}</p>
					<p class="kt-muted">
						Requested by {{ task.withdrawal_request.requested_by_name }} · {{ task.withdrawal_request.requested_display }}
					</p>
				</div>
			</div>

			<!-- A hold is a recorded control over the Planner's confirmation, not
			     a withdrawal of the approval (§5.5.2.3). -->
			<div v-if="task.hold?.active" class="kt-notice is-warning" data-testid="pub-hold">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path>
				</svg>
				<div class="kt-notice-body">
					<strong>Publication is on hold</strong>
					<p>{{ task.hold.reason }}</p>
				</div>
			</div>

			<!-- U13-CONFIRM-FORM — the Planner's one form. Save draft keeps
			     incomplete evidence; only a complete form confirms. -->
			<section v-if="showForm" class="kt-region" data-testid="pub-form">
				<h2>Publication details</h2>
				<!-- U13-DRAFT-SAVED — what is kept, and that keeping it confirms nothing. -->
				<p v-if="task.draft" class="kt-muted" data-testid="pub-draft-saved">Draft saved {{ task.draft.saved_display }}. Nothing has been confirmed yet.</p>
				<div class="kt-meta-row" data-testid="pub-form-plan">
					<div>
						<span class="kt-label">Approved plan</span>
						<span class="kt-meta-value is-plain">{{ task.plan_reference }} · Version {{ task.version?.number }}</span>
					</div>
					<div>
						<button type="button" class="btn btn-ghost" data-testid="pub-form-download" @click="$emit('download-plan')">Download approved plan</button>
					</div>
				</div>
				<div class="pln-treasury-grid">
					<div class="field" :class="{ 'pln-field-flagged': errors.treasury_submitted_on }" data-testid="pub-field-treasury_submitted_on">
						<label for="pub-treasury-date" class="kt-label">Treasury submission date</label>
						<input id="pub-treasury-date" class="input" type="date" data-testid="pub-treasury-date" v-model="form.treasury_submitted_on" :max="today">
						<div v-if="errors.treasury_submitted_on" class="pln-field-error" role="alert" data-testid="pub-error-treasury_submitted_on">{{ errors.treasury_submitted_on }}</div>
					</div>
					<div class="field" :class="{ 'pln-field-flagged': errors.treasury_reference }" data-testid="pub-field-treasury_reference">
						<label for="pub-treasury-reference" class="kt-label">Submission reference</label>
						<input id="pub-treasury-reference" class="input" data-testid="pub-treasury-reference" v-model="form.treasury_reference" maxlength="140">
						<div v-if="errors.treasury_reference" class="pln-field-error" role="alert" data-testid="pub-error-treasury_reference">{{ errors.treasury_reference }}</div>
					</div>
				</div>
				<div class="field pln-treasury-file" :class="{ 'pln-field-flagged': errors.treasury_attachment }" data-testid="pub-field-treasury_attachment">
					<label for="pub-treasury-file" class="kt-label">Submission evidence</label>
					<input id="pub-treasury-file" ref="fileInput" class="input" type="file" accept=".pdf,.png,.jpg,.jpeg" data-testid="pub-treasury-file" @change="onFile($event)">
					<div v-if="errors.treasury_attachment" class="pln-field-error" role="alert" data-testid="pub-error-treasury_attachment">{{ errors.treasury_attachment }}</div>
					<div class="kt-field-hint">
						A reference, the evidence file, or both. One is enough.
						<template v-if="carriedAttachment && !file"> A file is already attached: <a :href="carriedAttachment" target="_blank" rel="noopener" data-testid="pub-attached-file">view it</a>.</template>
					</div>
				</div>
				<div class="pln-treasury-grid pln-treasury-file">
					<div class="field" :class="{ 'pln-field-flagged': errors.website_published_on }" data-testid="pub-field-website_published_on">
						<label for="pub-website-date" class="kt-label">Entity website publication date</label>
						<input id="pub-website-date" class="input" type="date" data-testid="pub-website-date" v-model="form.website_published_on" :max="today">
						<div v-if="errors.website_published_on" class="pln-field-error" role="alert" data-testid="pub-error-website_published_on">{{ errors.website_published_on }}</div>
					</div>
					<div class="field" :class="{ 'pln-field-flagged': errors.public_plan_url }" data-testid="pub-field-public_plan_url">
						<label for="pub-public-url" class="kt-label">Public plan URL</label>
						<input id="pub-public-url" class="input" type="url" data-testid="pub-public-url" v-model="form.public_plan_url" placeholder="https://">
						<div v-if="errors.public_plan_url" class="pln-field-error" role="alert" data-testid="pub-error-public_plan_url">{{ errors.public_plan_url }}</div>
					</div>
				</div>
				<!-- The consequence sits beside the action; it starts unchecked every time. -->
				<label class="kt-checkbox pln-treasury-confirm">
					<input type="checkbox" data-testid="pub-statement" v-model="form.confirmation_acknowledged">
					<span class="box"></span>{{ task.statement }}
				</label>
				<div v-if="errors.confirmation_acknowledged" class="pln-field-error" role="alert" data-testid="pub-error-confirmation_acknowledged">{{ errors.confirmation_acknowledged }}</div>
			</section>

			<!-- Recorded evidence, in full, once it exists: every field its own
			     labelled fact, the date entered distinct from the time recorded. -->
			<section v-if="task.confirmation" class="kt-region" data-testid="pub-confirmation">
				<h2>Publication details</h2>
				<!-- One top-aligned grid: the three short facts share a row, the address has a row of its own
				     (it is long and must wrap inside the card), and who confirmed it, and when, close the block. -->
				<div class="pln-facts">
					<div data-fact="treasury_date"><span class="kt-label">Treasury submission date</span><span class="kt-meta-value is-plain">{{ task.confirmation.treasury_submitted_display }}</span></div>
					<div data-fact="reference"><span class="kt-label">Submission reference</span><span class="kt-meta-value is-plain">{{ task.confirmation.treasury_reference || "—" }}</span></div>
					<div data-fact="website_date"><span class="kt-label">Entity website publication date</span><span class="kt-meta-value is-plain">{{ task.confirmation.website_published_display }}</span></div>
					<div class="pln-fact-wide" data-fact="url" data-testid="pub-fact-url">
						<span class="kt-label">Public plan URL</span>
						<span class="kt-meta-value is-plain pln-fact-url"><a :href="task.confirmation.public_plan_url" target="_blank" rel="noopener">{{ task.confirmation.public_plan_url }}</a></span>
					</div>
					<div data-fact="confirmed_by"><span class="kt-label">Confirmed by</span><span class="kt-meta-value is-plain">{{ task.confirmation.recorded_by_name }}</span></div>
					<div data-fact="confirmed_at"><span class="kt-label">Confirmed at</span><span class="kt-meta-value is-plain">{{ task.confirmation.recorded_display }}</span></div>
				</div>
				<a
					v-if="task.confirmation.treasury_attachment"
					class="btn btn-ghost pln-flush-link"
					:href="task.confirmation.treasury_attachment"
					target="_blank"
					rel="noopener"
					data-testid="pub-view-evidence"
				>View submission evidence</a>
			</section>

			<!-- U13-CORRECT-DETAILS — a correction never overwrites: what is on
			     record stays in view, beside the new values and a reason. -->
			<section v-if="correcting && task.confirmation" class="kt-region" data-testid="pub-correct-form">
				<h2>Correct publication details</h2>
				<div class="kt-group pln-correct-prior">
					<h3 class="kt-label">Previous publication details</h3>
					<div class="pln-facts" data-testid="pub-correct-prior">
						<div><span class="kt-label">Treasury submission date</span><span class="kt-meta-value is-plain">{{ task.confirmation.treasury_submitted_display }}</span></div>
						<div><span class="kt-label">Submission reference</span><span class="kt-meta-value is-plain">{{ task.confirmation.treasury_reference || "—" }}</span></div>
						<div><span class="kt-label">Entity website publication date</span><span class="kt-meta-value is-plain">{{ task.confirmation.website_published_display }}</span></div>
						<div class="pln-fact-wide"><span class="kt-label">Public plan URL</span><span class="kt-meta-value is-plain pln-fact-url">{{ task.confirmation.public_plan_url }}</span></div>
					</div>
				</div>
				<div class="pln-treasury-grid">
					<div class="field" :class="{ 'pln-field-flagged': cErrors.treasury_submitted_on }">
						<label for="pub-correct-treasury-date" class="kt-label">Treasury submission date</label>
						<input id="pub-correct-treasury-date" class="input" type="date" data-testid="pub-correct-treasury-date" v-model="cform.treasury_submitted_on" :max="today">
						<div v-if="cErrors.treasury_submitted_on" class="pln-field-error" role="alert" data-testid="pub-correct-error-treasury_submitted_on">{{ cErrors.treasury_submitted_on }}</div>
					</div>
					<div class="field">
						<label for="pub-correct-reference" class="kt-label">Submission reference</label>
						<input id="pub-correct-reference" class="input" data-testid="pub-correct-reference" v-model="cform.treasury_reference" maxlength="140">
					</div>
					<div class="field" :class="{ 'pln-field-flagged': cErrors.website_published_on }">
						<label for="pub-correct-website-date" class="kt-label">Entity website publication date</label>
						<input id="pub-correct-website-date" class="input" type="date" data-testid="pub-correct-website-date" v-model="cform.website_published_on" :max="today">
						<div v-if="cErrors.website_published_on" class="pln-field-error" role="alert" data-testid="pub-correct-error-website_published_on">{{ cErrors.website_published_on }}</div>
					</div>
					<div class="field" :class="{ 'pln-field-flagged': cErrors.public_plan_url }">
						<label for="pub-correct-url" class="kt-label">Public plan URL</label>
						<input id="pub-correct-url" class="input" type="url" data-testid="pub-correct-url" v-model="cform.public_plan_url">
						<div v-if="cErrors.public_plan_url" class="pln-field-error" role="alert" data-testid="pub-correct-error-public_plan_url">{{ cErrors.public_plan_url }}</div>
					</div>
				</div>
				<div class="field pln-treasury-file">
					<label for="pub-correct-file" class="kt-label">Submission evidence</label>
					<input id="pub-correct-file" class="input" type="file" accept=".pdf,.png,.jpg,.jpeg" data-testid="pub-correct-file" @change="onCorrectFile($event)">
				</div>
				<div class="field pln-treasury-file">
					<label for="pub-correct-reason" class="kt-label">Reason for correction</label>
					<textarea id="pub-correct-reason" class="input" rows="3" data-testid="pub-correct-reason" v-model="reason"></textarea>
				</div>
				<p class="kt-muted" data-testid="pub-correct-note">Correcting these details does not change the approved plan, deactivate an active plan or repeat an approval.</p>
				<div class="dialog-actions">
					<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="pub-correct-cancel" @click="correcting = false">Cancel</button>
					<button type="button" class="btn btn-primary" :disabled="busy || !correctionReady" data-testid="pub-correct-submit" @click="submitCorrection">
						Save corrected details
					</button>
				</div>
			</section>

			<p v-if="hasServerErrors" class="pln-error-summary" data-testid="pub-not-saved">Nothing was saved. Fix the highlighted fields and try again.</p>
			<!-- Said once: when the refusal names fields, each field carries its own problem. -->
			<p v-if="errorSummary && !hasServerErrors" class="pln-error-summary" data-testid="pub-error">{{ errorSummary }}</p>
			<p v-if="uploadError" class="pln-error-summary" role="alert" data-testid="pub-upload-error">{{ uploadError }}</p>

			<div class="pln-footer" data-testid="pub-footer">
				<span></span>
				<div class="pln-footer-right">
					<p v-if="showForm && task.can_confirm && !ready" class="kt-muted" data-testid="pub-confirm-hint">
						{{ hasClientErrors ? "Fix the highlighted fields to confirm." : "Complete every field and tick the confirmation to confirm." }}
					</p>
					<button
						v-if="showForm && task.can_save_draft"
						type="button"
						class="btn btn-secondary"
						data-testid="pub-save-draft"
						:disabled="busy || !hasEntry"
						@click="saveDraft"
					>
						Save draft
					</button>
					<button
						v-if="showForm && task.can_confirm"
						type="button"
						class="btn btn-primary"
						data-testid="pub-confirm"
						:disabled="busy || !ready"
						@click="confirm"
					>
						Confirm plan publication
					</button>
					<button
						v-if="task.can_correct && !correcting"
						type="button"
						class="btn btn-secondary"
						data-testid="pub-correct"
						:disabled="busy"
						@click="startCorrection"
					>
						Correct publication details
					</button>
					<!-- §10.12 U13-WITHDRAWAL — the recovery route for an approved
					     plan whose content is defective and not yet confirmed. The
					     AO asks; the statutory authority decides. -->
					<button
						v-if="task.can_request_withdrawal"
						type="button"
						class="btn btn-secondary"
						data-testid="pub-request-withdrawal"
						:disabled="busy"
						@click="$emit('request-withdrawal')"
					>
						Request withdrawal for correction
					</button>
					<button
						v-if="task.can_decide_withdrawal"
						type="button"
						class="btn btn-primary"
						data-testid="pub-decide-withdrawal"
						:disabled="busy"
						@click="$emit('decide-withdrawal')"
					>
						Withdraw for correction
					</button>
				</div>
			</div>

			<!-- §10.14 / §6.3 — the Accounting Officer's own listed action when the
			     plan only became active after the financial year began. The facts
			     are stated read-only; the explanation never moves the activation
			     instant it explains, and earlier ones are kept, not replaced. -->
			<section v-if="lateActivation.applicable" class="kt-region" data-testid="pub-late-activation">
				<h2>Late start of the annual plan</h2>
				<div class="kt-meta-row">
					<div>
						<span class="kt-label">Financial year started</span>
						<span class="kt-meta-value is-plain">{{ lateActivation.financial_year_started_display }}</span>
					</div>
					<div>
						<span class="kt-label">Plan became active</span>
						<span class="kt-meta-value is-plain">{{ lateActivation.activated_display }}</span>
					</div>
				</div>
				<LateExplanationHistory
					v-if="lateActivation.explanations.length"
					:financial-year-started="lateActivation.financial_year_started_display"
					:activated-at="lateActivation.activated_display"
					:entries="lateActivation.explanations"
				/>
				<p v-else class="kt-muted" data-testid="pub-late-activation-none">No explanation has been recorded yet.</p>
				<button
					v-if="lateActivation.can_explain"
					type="button"
					class="btn btn-secondary"
					data-testid="pub-explain-late"
					:disabled="busy"
					@click="$emit('explain-late')"
				>
					{{ lateActivation.explanations.length ? "Add to the explanation" : "Explain late start of the annual plan" }}
				</button>
			</section>

			<!-- Read-only history of the v1.30 arrangements: what an attempt did,
			     and what the Accounting Officer recorded. Nothing here acts. -->
			<details v-if="attempts.length || task.historical_treasury" class="kt-disclosure" data-testid="pub-attempts">
				<summary class="kt-disclosure-head">
					<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Earlier publication attempts</span></div>
					<svg class="kt-disclosure-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
				</summary>
				<div class="kt-disclosure-body">
					<table v-if="attempts.length" class="table">
						<thead><tr><th>Attempt</th><th>Result</th><th>Attempted</th><th>External reference</th></tr></thead>
						<tbody>
							<tr v-for="row in attempts" :key="row.attempt_number">
								<td>{{ row.attempt_number }}</td>
								<td>{{ row.result }}</td>
								<td>{{ row.attempted_display || row.attempted_at }}</td>
								<td>{{ row.external_reference || "—" }}</td>
							</tr>
						</tbody>
					</table>
					<div v-if="task.historical_treasury" class="kt-meta-row" data-testid="pub-historical-treasury">
						<div><span class="kt-label">Treasury record, date and time sent</span><span class="kt-meta-value is-plain">{{ task.historical_treasury.submitted_display }}</span></div>
						<div><span class="kt-label">Channel</span><span class="kt-meta-value is-plain">{{ task.historical_treasury.channel }}</span></div>
						<div><span class="kt-label">Destination</span><span class="kt-meta-value is-plain">{{ task.historical_treasury.destination }}</span></div>
						<div><span class="kt-label">Dispatch reference</span><span class="kt-meta-value is-plain">{{ task.historical_treasury.dispatch_reference }}</span></div>
						<div><span class="kt-label">Recorded by</span><span class="kt-meta-value is-plain">{{ task.historical_treasury.recorded_by_name }}</span></div>
					</div>
				</div>
			</details>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useGuidance } from "../../pln_shared/composables/useGuidance.js";

import LateExplanationHistory from "./LateExplanationHistory.vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
	// What the server refused, by field (`detail.fields` of the refusal).
	errorFields: { type: Object, default: () => ({}) },
});

const emit = defineEmits([
	"save-draft", "confirm", "correct", "request-withdrawal", "decide-withdrawal", "explain-late", "navigate", "back",
	"download-plan", "download-plan-data",
]);

// The site's own date, from the server (Nairobi, not the browser's UTC date: between midnight and 3 am the two
// differ, and today's date must never read as "in the future").
function localIso() {
	const d = new Date();
	return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
const today = computed(() => props.task.today || localIso());

// The rules the server applies (PLN-CHG-001 v1.31 §5.5.2.2), applied as the Planner types so a bad value is
// named at its field before they press anything. The server stays the authority.
function formatDay(iso) {
	return new Date(`${iso}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function fieldProblems(values, approvedOn, todayIso) {
	const problems = {};
	const treasury = values.treasury_submitted_on;
	const website = values.website_published_on;
	if (treasury && treasury > todayIso) problems.treasury_submitted_on = "A date in the future cannot be confirmed.";
	else if (treasury && approvedOn && treasury < approvedOn) {
		problems.treasury_submitted_on = `The plan was approved on ${formatDay(approvedOn)}. It cannot have been submitted before then.`;
	}
	if (website && website > todayIso) problems.website_published_on = "A date in the future cannot be confirmed.";
	else if (website && treasury && website < treasury) {
		problems.website_published_on = "The website publication date cannot be before the Treasury submission date.";
	}
	const url = (values.public_plan_url || "").trim();
	if (url && !/^https?:\/\/[^\s/]+\S*$/i.test(url)) {
		problems.public_plan_url = "Enter the address of the published plan, starting with http:// or https://.";
	}
	return problems;
}

const statusRows = computed(() => props.task.status_rows || []);
const attempts = computed(() => props.task.attempts || []);

const lateActivation = computed(() => ({
	applicable: false,
	financial_year_started_display: "",
	activated_display: "",
	explanations: [],
	can_explain: false,
	...(props.task.late_activation || {}),
}));

// The form is the Planner's: it is drawn while the plan is waiting to be
// confirmed and nothing has been confirmed, for whoever may save a Draft.
const showForm = computed(() => Boolean(props.task.can_save_draft || props.task.can_confirm) && !props.task.confirmation);

const form = reactive({ treasury_submitted_on: "", treasury_reference: "", website_published_on: "", public_plan_url: "", confirmation_acknowledged: false });
const file = ref(null);
const fileInput = ref(null);
const carriedAttachment = ref("");
const uploading = ref(false);
const uploadError = ref("");
const busy = computed(() => props.pending || uploading.value);

function hydrate(draft) {
	form.treasury_submitted_on = draft?.treasury_submitted_on || "";
	form.treasury_reference = draft?.treasury_reference || "";
	form.website_published_on = draft?.website_published_on || "";
	form.public_plan_url = draft?.public_plan_url || "";
	// The statement is never carried over: it starts unchecked every time.
	form.confirmation_acknowledged = false;
	carriedAttachment.value = draft?.treasury_attachment || "";
	file.value = null;
	// the saved file now lives on the Draft; the chooser must not keep showing the one just uploaded
	if (fileInput.value) fileInput.value.value = "";
}
hydrate(props.task.draft);
// Refill only when the saved Draft really changed, never on a refresh that carries the same one.
watch(
	() => (props.task.draft ? `${props.task.draft.id}:${props.task.draft.record_version}` : ""),
	(next, previous) => {
		if (next !== previous) hydrate(props.task.draft);
	},
);

// What the server refused is shown at its field until the Planner edits that field.
const serverErrors = reactive({ ...(props.errorFields || {}) });
watch(
	() => props.errorFields,
	(next) => {
		for (const key of Object.keys(serverErrors)) delete serverErrors[key];
		Object.assign(serverErrors, next || {});
	},
);
watch(
	() => ({ ...form }),
	(next, previous) => {
		for (const key of Object.keys(next)) if (next[key] !== previous[key]) delete serverErrors[key];
	},
);
watch(file, () => {
	delete serverErrors.treasury_attachment;
});
const clientErrors = computed(() => fieldProblems(form, props.task.version?.approved_on || "", today.value));
const errors = computed(() => ({ ...serverErrors, ...clientErrors.value }));
const hasClientErrors = computed(() => Object.keys(clientErrors.value).length > 0);
const hasServerErrors = computed(() => Object.keys(serverErrors).length > 0);

const hasEntry = computed(() =>
	Boolean(form.treasury_submitted_on || form.treasury_reference.trim() || form.website_published_on || form.public_plan_url.trim() || file.value),
);
const hasEvidence = computed(() => Boolean(form.treasury_reference.trim() || file.value || carriedAttachment.value));
const ready = computed(() =>
	Boolean(
		form.treasury_submitted_on && form.website_published_on && form.public_plan_url.trim() && hasEvidence.value && form.confirmation_acknowledged
		&& !hasClientErrors.value,
	),
);

function onFile(event) {
	file.value = (event.target.files || [])[0] || null;
	uploadError.value = "";
}

async function upload(chosen) {
	const data = new FormData();
	data.append("file", chosen, chosen.name);
	data.append("is_private", "1");
	data.append("folder", "Home/Attachments");
	const response = await fetch("/api/method/upload_file", { method: "POST", body: data, headers: { "X-Frappe-CSRF-Token": window.frappe.csrf_token } });
	const body = await response.json().catch(() => ({}));
	if (!response.ok || !body.message || !body.message.name) throw new Error("The file could not be uploaded. Try again.");
	return body.message.name;
}

// The attachment sent is the File the Planner just uploaded, or the one already
// carried by the Draft; the server checks it is theirs, a PDF/PNG/JPG and small.
async function attachment(chosen, carried) {
	uploadError.value = "";
	if (!chosen) return carried || "";
	uploading.value = true;
	try {
		return await upload(chosen);
	} catch (e) {
		uploadError.value = e.message;
		return null;
	} finally {
		uploading.value = false;
	}
}

function valuesFor(attached) {
	return {
		treasury_submitted_on: form.treasury_submitted_on,
		treasury_reference: form.treasury_reference.trim(),
		treasury_attachment: attached,
		website_published_on: form.website_published_on,
		public_plan_url: form.public_plan_url.trim(),
		confirmation_acknowledged: form.confirmation_acknowledged ? 1 : 0,
	};
}

async function saveDraft() {
	const attached = await attachment(file.value, carriedAttachment.value);
	if (attached === null) return;
	emit("save-draft", valuesFor(attached));
}

async function confirm() {
	const attached = await attachment(file.value, carriedAttachment.value);
	if (attached === null) return;
	emit("confirm", valuesFor(attached));
}

// --- Correct publication details -------------------------------------------

const correcting = ref(false);
const reason = ref("");
const correctionFile = ref(null);
const cform = reactive({ treasury_submitted_on: "", treasury_reference: "", website_published_on: "", public_plan_url: "" });

function startCorrection() {
	const current = props.task.confirmation || {};
	cform.treasury_submitted_on = current.treasury_submitted_on || "";
	cform.treasury_reference = current.treasury_reference || "";
	cform.website_published_on = current.website_published_on || "";
	cform.public_plan_url = current.public_plan_url || "";
	reason.value = "";
	correctionFile.value = null;
	correcting.value = true;
}

function onCorrectFile(event) {
	correctionFile.value = (event.target.files || [])[0] || null;
}

const changed = computed(() => {
	const current = props.task.confirmation || {};
	return (
		cform.treasury_submitted_on !== (current.treasury_submitted_on || "")
		|| cform.treasury_reference.trim() !== (current.treasury_reference || "")
		|| cform.website_published_on !== (current.website_published_on || "")
		|| cform.public_plan_url.trim() !== (current.public_plan_url || "")
		|| Boolean(correctionFile.value)
	);
});
const cErrors = computed(() => fieldProblems(cform, props.task.version?.approved_on || "", today.value));
const correctionReady = computed(() =>
	changed.value && reason.value.trim().length >= 10
	&& Boolean(cform.treasury_submitted_on && cform.website_published_on && cform.public_plan_url.trim())
	&& Object.keys(cErrors.value).length === 0,
);

async function submitCorrection() {
	const attached = await attachment(correctionFile.value, props.task.confirmation?.treasury_attachment || "");
	if (attached === null) return;
	emit("correct", {
		confirmation: props.task.confirmation.id,
		reason: reason.value.trim(),
		values: {
			treasury_submitted_on: cform.treasury_submitted_on,
			treasury_reference: cform.treasury_reference.trim(),
			treasury_attachment: attached,
			website_published_on: cform.website_published_on,
			public_plan_url: cform.public_plan_url.trim(),
		},
	});
}

// A corrected record closes the form.
watch(
	() => props.task.confirmation?.id,
	() => {
		correcting.value = false;
	},
);

const headEl = ref(null);
const journeyEl = ref(null);
const bodyEl = ref(null);
useGuidance({ journeyEl, headEl, bodyEl }, { answer: () => props.task.next_step, journey: () => props.task.journey, pending: () => props.pending });
</script>
