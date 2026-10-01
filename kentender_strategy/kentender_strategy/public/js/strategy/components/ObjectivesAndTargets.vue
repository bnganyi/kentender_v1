<script setup>
// STR-DES-03 "Objectives and targets" / STR-DES-06 "Proposed plan" — the
// strategy's meaning, objective by objective: full statement, each
// Indicator with its complete "How it is measured" definition and unit, and
// every Target as a KPI card. `previousByTargetId` (from the server
// comparison) adds "was 80%" beside a changed proposed target.
defineProps({
	objectives: { type: Array, required: true },
	previousByTargetId: { type: Object, default: () => ({}) },
	emptyMessage: { type: String, default: "" },
});

// An objective with no indicator still shows its heading and "No indicator yet."
const rowsOf = (objective) => (objective.indicators && objective.indicators.length ? objective.indicators : [null]);
</script>

<template>
	<div v-if="!objectives.length" class="kt-muted" data-testid="str-objectives-empty">{{ emptyMessage || __("No objectives yet.") }}</div>
	<div v-else style="display: grid; gap: var(--kt-space-6)" data-testid="str-objectives">
		<!-- GitHub #27 — one row per indicator, its own targets beside it, so a
		     target card is never left level with a different indicator. The
		     objective's own heading leads the first row, which for the usual
		     single-indicator objective is exactly the STR-DES-03 artboard. -->
		<div
			v-for="objective in objectives"
			:key="objective.id"
			style="display: grid; gap: var(--kt-space-3)"
			data-testid="str-objective"
		>
			<div
				v-for="(indicator, index) in rowsOf(objective)"
				:key="indicator ? indicator.id : 'none'"
				class="kt-objective-grid"
				data-testid="str-objective-row"
			>
				<div style="display: grid; gap: var(--kt-space-3)">
					<template v-if="index === 0">
						<div v-if="objective.path_label" style="font-size: 12px; color: var(--kt-color-neutral-700)">{{ objective.path_label }}</div>
						<div>
							<div class="kt-label">{{ __("Objective") }}</div>
							<div style="font-size: 14px; margin-top: 3px; font-weight: 600" data-testid="str-objective-title">{{ objective.title }}</div>
						</div>
					</template>
					<template v-if="indicator">
						<div>
							<div class="kt-label">{{ __("Indicator") }}</div>
							<div style="font-size: 14px; margin-top: 3px" data-testid="str-objective-indicator">{{ indicator.name }}</div>
						</div>
						<div style="border-top: 1px solid var(--kt-color-divider); padding-top: var(--kt-space-3); display: grid; grid-template-columns: 1fr auto; gap: var(--kt-space-6)">
							<div>
								<div class="kt-label">{{ __("How it is measured") }}</div>
								<div style="font-size: 13px; margin-top: 3px; color: var(--kt-color-neutral-800)" data-testid="str-objective-definition">{{ indicator.definition }}</div>
							</div>
							<div>
								<div class="kt-label">{{ __("Unit") }}</div>
								<div style="font-size: 14px; margin-top: 3px">{{ indicator.unit }}</div>
							</div>
						</div>
					</template>
					<div v-else class="kt-muted" style="font-size: 13px">{{ __("No indicator yet.") }}</div>
				</div>
				<div style="display: grid; gap: var(--kt-space-3)">
					<template v-if="indicator">
						<div v-for="target in indicator.targets" :key="target.id" class="kt-kpi-card" data-testid="str-target-kpi">
							<svg class="kt-kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
							<div class="kt-kpi-value">
								{{ target.value_label }}
								<span v-if="previousByTargetId[target.id]" style="font-size: 12px; font-weight: 400; color: var(--kt-color-neutral-700)" data-testid="str-target-was">{{ __("was {0}", [previousByTargetId[target.id]]) }}</span>
							</div>
							<div class="kt-kpi-sub">{{ target.comparison }} &middot; {{ target.period_label }}</div>
						</div>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>
