<script setup>
// CFG-CHG-002 v0.14 §10.2 (C01) — the Procuring entity tab, re-ported
// class-for-class from design/C01-Procuring-Entity.dc.html (tracker
// CFG14-5A): the content sits directly in the page's one card (no card within
// the card), titled by the board's h3, with the fixed code and timezone as
// disabled inputs. Artboards: #configured, #first-run, #conflict (the county
// notice directly after the county answer), #missing-authority (the notice
// directly after the approval-authority field). The saved notices follow the
// footer, as the board places them. Never a generic "Ready" badge.
import { computed, nextTick, reactive, ref, watch } from "vue";
import { siteConfigApi } from "../data/siteConfigApi.js";

const props = defineProps({
	site: { type: Object, required: true },
	onUpdated: { type: Function, default: null },
});
const emit = defineEmits(["configured", "navigate"]);

const error = ref("");
const notice = ref("");
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{
		onStart: () => {
			error.value = "";
			notice.value = "";
		},
		onError: (e) => (error.value = e.message),
	}
);

const configured = computed(() => !!props.site?.configured);
const pe = computed(() => props.site?.procuring_entity || null);
const peTypes = computed(() => props.site?.pe_types || []);

// C01 — the four statutory routes come from the server's offer; there is no
// None (CFG v0.11 §4.1).
const routes = computed(() => props.site?.statutory_approval_routes || []);

const form = reactive({
	pe_name: pe.value?.pe_name || "",
	pe_code: pe.value?.pe_code || "",
	pe_type: pe.value?.pe_type || "",
	ppra_registration: pe.value?.ppra_registration || "",
	timezone: pe.value?.timezone || "Africa/Nairobi",
	statutory_approval_route: pe.value?.statutory_approval_route || "",
	entity_is_county: pe.value ? !!pe.value.entity_is_county : null,
});

watch(pe, (value) => {
	form.pe_name = value?.pe_name || "";
	form.pe_code = value?.pe_code || "";
	form.pe_type = value?.pe_type || "";
	form.ppra_registration = value?.ppra_registration || "";
	form.timezone = value?.timezone || "Africa/Nairobi";
	form.statutory_approval_route = value?.statutory_approval_route || "";
	form.entity_is_county = value ? !!value.entity_is_county : null;
});

const dirty = computed(() => {
	if (!configured.value) return true;
	return (
		form.pe_name !== (pe.value?.pe_name || "") ||
		form.pe_type !== (pe.value?.pe_type || "") ||
		form.ppra_registration !== (pe.value?.ppra_registration || "") ||
		form.statutory_approval_route !== (pe.value?.statutory_approval_route || "") ||
		form.entity_is_county !== !!pe.value?.entity_is_county
	);
});

// C01-conflict — the county/type mismatch is refused server-side before any
// save; shown as its own critical notice, not folded into the generic error.
const countyConflict = computed(() => /county answer does not match/i.test(error.value || ""));

// C01 missing-authority — pressing Configure without an approval authority
// shows the board's notice beside that field and moves focus to it; the
// server refuses the same (CFG_APPROVAL_ROUTE_REQUIRED). Any other missing
// fact is refused by the server with its own message.
const routeMissing = ref(false);
const routeSelect = ref(null);
watch(
	() => form.statutory_approval_route,
	(value) => {
		if (value) routeMissing.value = false;
	}
);

const canSubmit = computed(() => {
	if (busy.value) return false;
	return configured.value ? dirty.value : true;
});

async function submit() {
	if (!form.statutory_approval_route) {
		routeMissing.value = true;
		await nextTick();
		routeSelect.value?.focus();
		return;
	}
	return run(async () => {
		if (!configured.value) {
			await siteConfigApi.configure({
				pe_name: form.pe_name,
				pe_code: form.pe_code,
				pe_type: form.pe_type,
				ppra_registration: form.ppra_registration,
				timezone: form.timezone,
				statutory_approval_route: form.statutory_approval_route,
				entity_is_county: form.entity_is_county ? 1 : 0,
			});
			emit("configured");
			notice.value = __("Site configured");
		} else {
			await siteConfigApi.update(
				{
					pe_name: form.pe_name,
					pe_type: form.pe_type,
					ppra_registration: form.ppra_registration,
					timezone: form.timezone,
					statutory_approval_route: form.statutory_approval_route,
					entity_is_county: form.entity_is_county,
				},
				pe.value?.expected_version
			);
			// Await the parent's refresh before `run()` clears `busy` — otherwise
			// a fast second Save reads `expected_version` off `pe`, which is a
			// computed over the still-stale `site` prop until this resolves
			// (RUN-CHG-001; confirmed live 2026-09-11).
			if (props.onUpdated) await props.onUpdated();
			notice.value = __("Site details saved");
		}
	});
}

function fmt(value) {
	return value || "—";
}

// §4.2 `approval_applicability` — Verified / Verification required /
// Configuration conflict; never a universal "Ready" badge (§8.1).
const approval = computed(() => pe.value?.approval_applicability || null);
const approvalStatusClass = computed(() => {
	const result = approval.value?.result;
	if (result === "Verified") return "is-live";
	if (result === "Configuration conflict") return "is-critical";
	return "is-attention";
});
const approvalStatusLabel = computed(() => {
	const result = approval.value?.result;
	if (result === "Verified") return __("Sources verified");
	if (result === "Configuration conflict") return __("Configuration conflict");
	// §8.1's closed vocabulary: a rule in force whose sources are unchecked is
	// "Source check needed"; no rule at all is "No rule covers this date".
	if (result === "Rule not source-checked") return __("Source check needed");
	return __("No rule covers this date");
});
const approvalStatusText = computed(() => {
	const result = approval.value?.result;
	if (result === "Verified") return __("The configured approval authority is verified against a current rule.");
	if (result === "Configuration conflict")
		return __("The approval rule in force names a different authority than this entity's configured route.");
	// §10.2 — the same plain sentence whether the rule is missing or only
	// unchecked; the status label above says which.
	return __("The approval authority's supporting evidence must be completed before Plan approval.");
});

function goToProcurementRules() {
	emit("navigate", "procurement-rules");
}

</script>

<template>
	<section class="kt-setup-section" data-testid="kt-setup-pe">
		<div data-testid="kt-setup-pe-card">
			<h3>{{ configured ? __("Procuring entity") : __("Configure this site") }}</h3>
			<p class="card-body">
				{{
					configured
						? __("This site represents one procuring entity. Its code is fixed after setup.")
						: __("Enter the procuring entity's details to set up this site.")
				}}
			</p>

			<div class="kt-setup-grid">
				<div class="field">
					<label for="kt-pe-name">{{ __("Entity name") }}</label>
					<input id="kt-pe-name" v-model="form.pe_name" class="input" data-testid="kt-setup-pe-name">
				</div>
				<div class="field">
					<label for="kt-pe-code">{{ __("Entity code") }}</label>
					<input
						id="kt-pe-code"
						v-model="form.pe_code"
						class="input"
						:disabled="configured"
						data-testid="kt-setup-pe-code"
					>
				</div>
				<div class="field">
					<label for="kt-pe-type">{{ __("Entity type") }}</label>
					<select id="kt-pe-type" v-model="form.pe_type" class="input" data-testid="kt-setup-pe-type">
						<option v-if="!form.pe_type" value="">{{ __("— Select —") }}</option>
						<option v-for="kind in peTypes" :key="kind" :value="kind">{{ kind }}</option>
					</select>
				</div>
				<div class="field">
					<label for="kt-pe-ppra">{{ __("PPRA registration") }}</label>
					<input id="kt-pe-ppra" v-model="form.ppra_registration" class="input" data-testid="kt-setup-pe-ppra">
				</div>
				<div class="field">
					<label for="kt-pe-tz">{{ __("Timezone") }}</label>
					<input id="kt-pe-tz" :value="form.timezone" class="input" disabled data-testid="kt-setup-pe-tz">
				</div>
				<div class="field">
					<label for="kt-pe-route">{{ __("Who approves the Annual Procurement Plan?") }}</label>
					<select
						id="kt-pe-route"
						ref="routeSelect"
						v-model="form.statutory_approval_route"
						class="input"
						:aria-invalid="routeMissing ? 'true' : 'false'"
						:aria-describedby="routeMissing ? 'kt-pe-route-missing' : undefined"
						data-testid="kt-setup-pe-route"
					>
						<option v-if="!form.statutory_approval_route" value="">{{ __("— Select —") }}</option>
						<option v-for="route in routes" :key="route" :value="route">{{ route }}</option>
					</select>
				</div>
				<div
					v-if="routeMissing"
					id="kt-pe-route-missing"
					class="kt-notice is-critical"
					role="alert"
					style="grid-column:1/-1"
					data-testid="kt-setup-pe-route-missing"
				>
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body"><strong>{{ __("Missing.") }}</strong> {{ __("Select who approves this entity's Annual Procurement Plan.") }}</div>
				</div>
			</div>

			<!-- An explicit Yes/No choice (regulation 40(5)), never a checkbox. -->
			<div class="field" style="margin-bottom:20px" data-testid="kt-setup-pe-county">
				<label id="kt-pe-county-label">{{ __("Is this a county entity?") }}</label>
				<div style="display:flex;gap:16px" role="radiogroup" aria-labelledby="kt-pe-county-label">
					<label class="radio" data-testid="kt-setup-pe-county-yes">
						<input
							type="radio"
							name="kt-pe-county"
							:checked="form.entity_is_county === true"
							@change="form.entity_is_county = true"
						>
						<span class="dot" />{{ __("Yes") }}
					</label>
					<label class="radio" data-testid="kt-setup-pe-county-no">
						<input
							type="radio"
							name="kt-pe-county"
							:checked="form.entity_is_county === false"
							@change="form.entity_is_county = false"
						>
						<span class="dot" />{{ __("No") }}
					</label>
				</div>
			</div>

			<!-- C01 #conflict — directly after the county answer it concerns. -->
			<div v-if="countyConflict" class="kt-notice is-critical" role="alert" data-testid="kt-setup-pe-county-conflict">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
				<div class="kt-notice-body"><strong>{{ __("Conflict.") }}</strong> {{ error }}</div>
			</div>

			<template v-if="configured">
				<div class="kt-section" style="margin-bottom:16px" data-testid="kt-setup-pe-record">
					<h6 class="kt-card-title">{{ __("Setup record") }}</h6>
					<div class="kt-panel">
						<div class="kt-meta-row">
							<div><span class="kt-label">{{ __("Configured by") }}</span><span class="kt-meta-value">{{ fmt(pe?.configured_by) }}</span></div>
							<div><span class="kt-label">{{ __("Configured at") }}</span><span class="kt-meta-value">{{ fmt(pe?.configured_at_label) }}</span></div>
							<div><span class="kt-label">{{ __("Top-level organisation unit") }}</span><span class="kt-meta-value">{{ fmt(site.root_unit?.name) }}</span></div>
							<div><span class="kt-label">{{ __("Unit code") }}</span><span class="kt-meta-value">{{ fmt(site.root_unit?.code) }}</span></div>
						</div>
					</div>
				</div>

				<div class="kt-section" style="margin-bottom:20px" data-testid="kt-setup-pe-approval">
					<h6 class="kt-card-title">{{ __("Plan approval authority") }}</h6>
					<div class="kt-panel">
						<div style="margin-bottom:8px">
							<span class="kt-status" :class="approvalStatusClass" data-testid="kt-setup-pe-approval-status">{{ approvalStatusLabel }}</span>
						</div>
						<p class="card-body">{{ approvalStatusText }}</p>
						<a href="#" data-testid="kt-setup-pe-approval-link" @click.prevent="goToProcurementRules">{{ __("View procurement rules") }}</a>
					</div>
				</div>
			</template>

			<p v-else class="text-muted" style="font-size:13px" data-testid="kt-setup-pe-first-run-note">
				{{ __("Other four tabs unavailable until this save succeeds.") }}
			</p>

			<div v-if="error && !countyConflict" class="kt-notice is-critical" role="alert" data-testid="kt-setup-pe-error">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
				<div class="kt-notice-body">{{ error }}</div>
			</div>

			<div style="display:flex;justify-content:flex-end">
				<button
					type="button"
					class="btn btn-primary"
					:disabled="!canSubmit"
					data-testid="kt-setup-pe-submit"
					@click="submit"
				>{{ configured ? __("Save changes") : __("Configure site") }}</button>
			</div>
		</div>

		<!-- C01 places the saved/configured notice after the form it reports on. -->
		<div v-if="notice && !error" class="kt-notice is-live" role="status" data-testid="kt-setup-pe-success">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M20 6L9 17l-5-5" /></svg>
			<div class="kt-notice-body">{{ notice }}</div>
		</div>
	</section>
</template>
