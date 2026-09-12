<script setup>
// CFG-CHG-002 v0.6 §10.1/§10.2 + §11.2 — the Procuring entity tab.
//
// First run (CFG-DES-02): a setup notice, the identity card with an editable
// code, and one primary action, "Configure site" — no Cancel, no wizard, no
// draft. Configured (CFG-DES-01): the code is read-only, "Save changes" is
// disabled until a field changes and re-disables after a successful save.
import { computed, reactive, ref, watch } from "vue";
import { siteConfigApi } from "../data/siteConfigApi.js";

const props = defineProps({
	site: { type: Object, required: true },
	onUpdated: { type: Function, default: null },
});
const emit = defineEmits(["configured"]);

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

// PLN-CHG-001 v1.18 §10.11 C01 / CFG v0.9 §4.1 — the four statutory routes
// come from the server's offer; there is no None.
const routes = computed(() => props.site?.statutory_approval_routes || []);

const form = reactive({
	pe_name: pe.value?.pe_name || "",
	pe_code: pe.value?.pe_code || "",
	pe_type: pe.value?.pe_type || "",
	ppra_registration: pe.value?.ppra_registration || "",
	timezone: pe.value?.timezone || "Africa/Nairobi",
	statutory_approval_route: pe.value?.statutory_approval_route || "",
	entity_is_county: !!pe.value?.entity_is_county,
});

watch(pe, (value) => {
	form.pe_name = value?.pe_name || "";
	form.pe_code = value?.pe_code || "";
	form.pe_type = value?.pe_type || "";
	form.ppra_registration = value?.ppra_registration || "";
	form.timezone = value?.timezone || "Africa/Nairobi";
	form.statutory_approval_route = value?.statutory_approval_route || "";
	form.entity_is_county = !!value?.entity_is_county;
});

const dirty = computed(() => {
	if (!configured.value) return true;
	return (
		form.pe_name !== (pe.value?.pe_name || "") ||
		form.pe_type !== (pe.value?.pe_type || "") ||
		form.ppra_registration !== (pe.value?.ppra_registration || "") ||
		form.timezone !== (pe.value?.timezone || "") ||
		form.statutory_approval_route !== (pe.value?.statutory_approval_route || "") ||
		form.entity_is_county !== !!pe.value?.entity_is_county
	);
});

// C01-conflict — the county/type mismatch is refused server-side before any
// save; it is shown as the artboard's inline attention status, not a modal.
const countyConflict = computed(() => /County applicability does not match/.test(error.value || ""));

const canSubmit = computed(() => {
	if (busy.value) return false;
	if (!configured.value) {
		return !!(form.pe_name.trim() && form.pe_code.trim() && form.pe_type && form.statutory_approval_route);
	}
	return dirty.value;
});

function submit() {
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
			notice.value = __("Site configured. The remaining tabs are now available.");
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
			notice.value = __("Changes saved.");
		}
	});
}

function fmt(value) {
	return value || "—";
}
</script>

<template>
	<section class="kt-setup-section" data-testid="kt-setup-pe">
		<!-- CFG-DES-02 setup notice — first run only -->
		<div v-if="!configured" class="kt-setup-notice" data-testid="kt-setup-pe-notice">
			<h2>{{ __("Configure this site") }}</h2>
			<p>{{ __("KenTender represents one procuring entity. Enter its details to create the site and its root organisation unit.") }}</p>
		</div>

		<div class="kt-card kt-blueprint" data-testid="kt-setup-pe-card">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-card-title">{{ __("Procuring entity") }}</div>
			<p v-if="configured" class="kt-muted kt-card-lede">
				{{ __("This site represents one procuring entity. The code is fixed once the site is configured.") }}
			</p>

			<div class="kt-setup-grid">
				<div class="kt-field">
					<label for="kt-pe-code">{{ __("Entity code") }}</label>
					<div v-if="configured" class="kt-ro" data-testid="kt-setup-pe-code-ro">{{ form.pe_code }}</div>
					<input
						v-else
						id="kt-pe-code"
						v-model="form.pe_code"
						class="kt-input"
						data-testid="kt-setup-pe-code"
					>
				</div>
				<div class="kt-field">
					<label for="kt-pe-name">{{ __("Entity name") }}</label>
					<input id="kt-pe-name" v-model="form.pe_name" class="kt-input" data-testid="kt-setup-pe-name">
				</div>
				<div class="kt-field">
					<label for="kt-pe-type">{{ __("Entity type") }}</label>
					<select id="kt-pe-type" v-model="form.pe_type" class="kt-input" data-testid="kt-setup-pe-type">
						<option value="">{{ __("Select the entity type") }}</option>
						<option v-for="kind in peTypes" :key="kind" :value="kind">{{ kind }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-pe-ppra">{{ __("PPRA registration") }}</label>
					<input
						id="kt-pe-ppra"
						v-model="form.ppra_registration"
						class="kt-input"
						:placeholder="__('Optional')"
						data-testid="kt-setup-pe-ppra"
					>
				</div>
				<div class="kt-field">
					<label for="kt-pe-tz">{{ __("Timezone") }}</label>
					<!-- CFG-DES-01 draws Timezone as a dropdown -->
					<select id="kt-pe-tz" v-model="form.timezone" class="kt-input" data-testid="kt-setup-pe-tz">
						<option v-for="zone in site.timezones || ['Africa/Nairobi']" :key="zone" :value="zone">
							{{ zone }}
						</option>
					</select>
				</div>
				<!-- C01 — statutory approval route (four values, no None) -->
				<div class="kt-field">
					<label for="kt-pe-route">{{ __("Statutory approval route") }}</label>
					<select id="kt-pe-route" v-model="form.statutory_approval_route" class="kt-input" data-testid="kt-setup-pe-route">
						<option v-if="!form.statutory_approval_route" value="">{{ __("Select the statutory approval route") }}</option>
						<option v-for="route in routes" :key="route" :value="route">{{ route }}</option>
					</select>
					<p class="kt-hint">{{ __("Select the authority that approves this entity's Annual Procurement Plan.") }}</p>
				</div>
			</div>
			<!-- C01 — county entity flag (regulation 40(5)) -->
			<label class="kt-setup-check" data-testid="kt-setup-pe-county-label">
				<input v-model="form.entity_is_county" type="checkbox" data-testid="kt-setup-pe-county">
				{{ __("County entity") }}
			</label>
			<span
				v-if="countyConflict"
				class="kt-status is-attention"
				role="alert"
				data-testid="kt-setup-pe-county-conflict"
			>{{ error }}</span>
		</div>

		<!-- CFG-DES-01 configuration record card — configured only -->
		<div v-if="configured" class="kt-card kt-blueprint" data-testid="kt-setup-pe-record">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-card-title">{{ __("Configuration record") }}</div>
			<div class="kt-record-rows">
				<div class="kt-record-row">
					<span class="kt-label">{{ __("Configured by") }}</span>
					<span>{{ fmt(pe?.configured_by) }}</span>
				</div>
				<div class="kt-record-row">
					<span class="kt-label">{{ __("Configured at") }}</span>
					<span>{{ fmt(pe?.configured_at_label || pe?.configured_at) }}</span>
				</div>
				<div class="kt-record-row">
					<span class="kt-label">{{ __("Root organisation unit") }}</span>
					<span>{{ site.root_unit ? site.root_unit.name + " · " + site.root_unit.code : __("Missing — see Organisation structure") }}</span>
				</div>
			</div>
		</div>

		<p v-if="error && !countyConflict" class="kt-inline-error" role="alert" data-testid="kt-setup-pe-error">{{ error }}</p>
		<p v-else-if="notice" class="kt-setup-success" data-testid="kt-setup-pe-success">{{ notice }}</p>

		<div class="kt-setup-footer">
			<button
				type="button"
				class="kt-btn kt-btn-primary"
				:disabled="!canSubmit"
				data-testid="kt-setup-pe-submit"
				@click="submit"
			>{{ configured ? __("Save changes") : __("Configure site") }}</button>
		</div>
	</section>
</template>
