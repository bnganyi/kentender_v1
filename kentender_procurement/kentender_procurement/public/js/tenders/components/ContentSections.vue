<!-- The six content disclosures every review/decision/published board carries
     (§10.6 items 5–7): Tender details, Requirements from the authorised
     requisition, Supplier pricing schedule, Supplier and evaluation
     requirements, Contract terms, Technical evidence. Each head gives the
     title, a plain summary and — for a section holding a Must fix or Review
     note — its count tag; such a section starts open. The body is the
     server's content blocks (fact grids, titled tables, the evaluation list),
     drawn as the boards draw them. -->
<template>
	<div class="tnd-disclosure-stack" :class="{ 'tnd-disclosure-nested': nested }" data-testid="tnd-content-sections">
		<div v-for="section in sections" :key="section.key" class="kt-disclosure" :data-testid="`tnd-section-${section.key}`">
			<div class="kt-disclosure-head" role="button" tabindex="0" :aria-expanded="isOpen(section) ? 'true' : 'false'" @click="toggle(section)" @keydown.enter.prevent="toggle(section)">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ section.title }}</span><span v-if="section.summary" class="tnd-disclosure-summary">{{ section.summary }}</span></div>
				<div class="tnd-disclosure-head-right">
					<span v-if="section.tag" class="tnd-tag tnd-tag-accent" :data-testid="`tnd-section-tag-${section.key}`">{{ section.tag }}</span>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': isOpen(section) }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg>
				</div>
			</div>
			<div v-if="isOpen(section)" class="kt-disclosure-body">
				<template v-for="(block, index) in section.blocks || []" :key="index">
					<div v-if="block.kind === 'facts'" class="tnd-fact-grid tnd-fact-grid--2">
						<div v-for="fact in block.facts" :key="fact.label" class="tnd-fact" :class="{ 'tnd-span-2': fact.wide }"><div class="kt-label">{{ fact.label }}</div><div class="tnd-fact-value tnd-break">{{ fact.value || "—" }}</div></div>
					</div>
					<template v-else-if="block.kind === 'table'">
						<h4 v-if="block.title" class="tnd-block-title" :class="{ 'tnd-block-title--later': index > 0 }">{{ block.title }}</h4>
						<table class="kt-table">
							<thead><tr><th v-for="column in block.columns" :key="column.label" :class="{ 'is-num': column.num }">{{ column.label }}</th></tr></thead>
							<tbody>
								<tr v-for="(row, r) in block.rows" :key="r"><td v-for="(cell, c) in row" :key="c" :class="{ 'is-num': block.columns[c] && block.columns[c].num, 'tnd-muted-700': (block.muted || []).includes(c) }">{{ cell }}</td></tr>
							</tbody>
						</table>
					</template>
					<template v-else-if="block.kind === 'list'">
						<h4 class="tnd-block-title" :class="{ 'tnd-block-title--later': index > 0 }">{{ block.title }}</h4>
						<ol class="tnd-ol"><li v-for="item in block.items" :key="item">{{ item }}</li></ol>
					</template>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
import { reactive } from "vue";

const props = defineProps({
	sections: { type: Array, default: () => [] },
	nested: Boolean,
	// TPR-DES-05's board alone draws the pricing body open unconditionally;
	// DES-06/07/09 draw it closed like every other section without a finding.
	openPricing: Boolean,
});
const state = reactive({});

function isOpen(section) {
	if (section.key === "pricing" && props.openPricing && !(section.key in state)) return true;
	return section.key in state ? state[section.key] : !!section.open;
}
/** Open one section and bring it into view (a review note's own link). */
function openSection(key) {
	state[key] = true;
	setTimeout(() => {
		const el = document.querySelector(`[data-testid="tnd-section-${key}"]`);
		if (el && el.scrollIntoView) el.scrollIntoView({ block: "start", behavior: "smooth" });
	}, 0);
}
defineExpose({ openSection });
function toggle(section) {
	state[section.key] = !isOpen(section);
}
</script>
