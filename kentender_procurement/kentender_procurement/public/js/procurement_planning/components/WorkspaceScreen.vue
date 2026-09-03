<!-- PLN-UI-01 Procurement Planning workspace (§12.1), rendering PLN-DES-01
     class-for-class plus the PLN-DES-16 no-context / load-error states. -->
<template>
	<div>
		<!-- Masthead — PLN-DES-01 page content header, present in every state. -->
		<div class="pln-masthead">
			<div>
				<div class="kt-page-kicker">PROCUREMENT PLANNING</div>
				<h1 class="kt-page-title">Annual procurement planning</h1>
				<p class="kt-page-lede">
					Turn accepted departmental plans into a funded and approved Annual
					Procurement Plan.
				</p>
			</div>
			<!-- PLN-DES-01: no header action button -->
		</div>

		<!-- loading skeleton -->
		<div
			v-if="loading"
			class="kt-card kt-blueprint"
			style="padding: 0; overflow: hidden"
			data-testid="pln-loading"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="row in 3" :key="row" class="pln-skel-row">
				<div class="kt-skel" style="width: 72%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 52%"></div>
				<div class="kt-skel" style="width: 44%"></div>
			</div>
		</div>

		<!-- PLN-DES-16 load error, with the generated support reference -->
		<div
			v-else-if="error"
			class="kt-card kt-blueprint pln-state-card"
			data-testid="pln-error"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning could not be loaded</h3>
			<p>Try again. If the problem continues, quote the support reference shown below.</p>
			<button class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
			<p class="pln-support-ref">Support reference: {{ supportRef }}</p>
		</div>

		<!-- PLN-DES-16 no authorised context -->
		<div
			v-else-if="workspace.outcome === 'NO_SCOPE'"
			class="kt-card kt-blueprint pln-state-card"
			data-testid="pln-no-scope"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Procurement Planning is not available</h3>
			<p>
				You do not have an assigned Procuring Entity scope, or no configured
				Financial Year is available for Planning.
			</p>
		</div>

		<template v-else>
			<!-- PLN-DES-01 planning context row -->
			<div class="kt-card kt-blueprint pln-strip" data-testid="pln-context-strip">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="pln-strip-field">
					<label for="pln-pe-select">Procuring Entity</label>
					<select
						id="pln-pe-select"
						class="kt-input"
						data-testid="pln-pe-select"
						:value="context.procuring_entity || ''"
						@change="$emit('select-procuring-entity', $event.target.value)"
					>
						<option
							v-for="entity in context.procuring_entities || []"
							:key="entity.id"
							:value="entity.id"
						>
							{{ entity.id }} — {{ entity.label }}
						</option>
					</select>
				</div>
				<div class="pln-strip-field">
					<label for="pln-fy-select">Financial Year</label>
					<select
						id="pln-fy-select"
						class="kt-input"
						data-testid="pln-fy-select"
						:value="context.financial_year || ''"
						@change="$emit('select-financial-year', $event.target.value)"
					>
						<option
							v-for="year in context.financial_years || []"
							:key="year.id"
							:value="year.id"
						>
							{{ year.label }}
						</option>
					</select>
				</div>
				<div v-if="annualPlanSummary" class="pln-strip-quiet" data-testid="pln-plan-summary">
					{{ annualPlanSummary }}
				</div>
			</div>

			<!-- selection required: the strip above stays operable; no record is
			     created by rendering this prompt (§12.1). -->
			<div
				v-if="workspace.outcome === 'SELECTION_REQUIRED'"
				class="kt-card kt-blueprint pln-state-card"
				data-testid="pln-selection-required"
			>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h3>Select a Procuring Entity and Financial Year</h3>
				<p>Planning shows one Procuring Entity and Financial Year at a time.</p>
			</div>

			<div v-else class="pln-cards-col">
				<!-- PLN-DES-01 Your work card — only work the actor may do now -->
				<div
					v-if="(workspace.your_work || []).length"
					class="kt-card kt-blueprint pln-card-pad"
					data-testid="pln-your-work"
				>
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">Your work</div>
					<table class="pln-table">
						<thead>
							<tr>
								<th>Work item</th>
								<th>Scope</th>
								<th>Status</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="(row, index) in workspace.your_work" :key="index">
								<td>{{ row.item }}</td>
								<td>{{ row.scope }}</td>
								<td>
									<span class="kt-status" :class="statusClass(row.status_kind)">
										{{ row.status }}
									</span>
								</td>
								<td style="text-align: right">
									<button
										class="kt-btn kt-btn-secondary"
										:disabled="pending"
										:data-testid="`pln-work-action-${index}`"
										@click="onWorkAction(row)"
									>
										{{ row.action }}
									</button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>

				<!-- PLN-DES-01 Departmental plans card -->
				<div class="kt-card kt-blueprint pln-card-pad" data-testid="pln-departmental-plans">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
					<i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">Departmental plans</div>
					<table v-if="(workspace.departmental_plans || []).length" class="pln-table">
						<thead>
							<tr>
								<th>Department</th>
								<th class="pln-num">Version</th>
								<th class="pln-num">Requirements</th>
								<th class="pln-num">Value</th>
								<th>Status</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in workspace.departmental_plans" :key="row.dpp_reference">
								<td>{{ row.department }}</td>
								<td class="pln-num">{{ row.version }}</td>
								<td class="pln-num">{{ row.requirements }}</td>
								<td class="pln-num">{{ row.value }}</td>
								<td>
									<span class="kt-status" :class="statusClass(row.status_kind)">
										{{ row.status }}
									</span>
								</td>
								<td style="text-align: right">
									<button
										v-if="row.route"
										class="kt-btn kt-btn-ghost"
										@click="$emit('navigate', row.route)"
									>
										View
									</button>
								</td>
							</tr>
						</tbody>
					</table>
					<!-- PLN-DES-16 no accepted departmental entries analogue: an
					     empty context simply reads as zero plans. -->
					<p class="pln-table-caption kt-muted" data-testid="pln-count-label">
						{{ workspace.count_label }}
					</p>
					<p
						v-if="workspace.not_included_message"
						class="pln-table-caption kt-muted"
						data-testid="pln-not-included"
					>
						{{ workspace.not_included_message }}
					</p>
				</div>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	loading: Boolean,
	error: String,
	supportRef: String,
	workspace: { type: Object, default: () => ({}) },
	pending: Boolean,
});

const emit = defineEmits([
	"reload",
	"select-procuring-entity",
	"select-financial-year",
	"open-departmental-plan",
	"navigate",
]);

const context = computed(() => props.workspace.context || {});

const annualPlanSummary = computed(
	() => (props.workspace.annual_plan || {}).summary || ""
);

const KIND_CLASS = {
	live: "is-live",
	attention: "is-attention",
	critical: "is-critical",
	muted: "is-draft",
};

function statusClass(kind) {
	return KIND_CLASS[kind] || "is-draft";
}

function onWorkAction(row) {
	const route = row.route || [];
	if (route[0] === "procurement-planning" && route[1] === "open") {
		emit("open-departmental-plan", route[2]);
		return;
	}
	emit("navigate", route);
}
</script>
