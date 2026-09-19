<!-- The six content disclosures every review/decision/published board carries
     (§10.6 items 5–7): Tender details, Requirements from the authorised
     requisition, Supplier pricing schedule, Supplier and evaluation
     requirements, Contract terms, Technical evidence — each a plain summary
     head plus details; a section holding a Must fix or Review note starts
     open and carries the count tag. Rendered from the server's `sections`. -->
<template>
	<div class="tnd-disclosure-stack" :class="{ 'tnd-disclosure-nested': nested }" data-testid="tnd-content-sections">
		<div v-for="section in sections" :key="section.key" class="kt-disclosure" :data-testid="`tnd-section-${section.key}`">
			<div class="kt-disclosure-head" role="button" tabindex="0" @click="toggle(section.key)" @keydown.enter.prevent="toggle(section.key)">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ section.title }}</span></div>
				<div class="tnd-disclosure-head-right">
					<span v-if="tagFor(section.key)" class="tnd-tag tnd-tag-accent">{{ tagFor(section.key) }}</span>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': isOpen(section) }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m6 9 6 6 6-6"/></svg>
				</div>
			</div>
			<div v-if="isOpen(section) || section.key === 'pricing'" class="kt-disclosure-body">
				<p class="tnd-card-body" style="margin: 0 0 12px">{{ section.summary }}</p>

				<template v-if="section.key === 'details' || section.key === 'contract'">
					<div class="tnd-grid-2">
						<div v-for="f in (section.details || {}).facts || []" :key="f.label" class="tnd-fact"><div class="kt-label">{{ f.label }}</div><div class="tnd-fact-value">{{ f.value || "—" }}</div></div>
					</div>
					<div v-if="((section.details || {}).fields || []).length" class="tnd-grid-2" style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--color-divider)">
						<div v-for="f in section.details.fields" :key="f.label" class="tnd-fact"><div class="kt-label">{{ f.label }}</div><div class="tnd-fact-value">{{ f.value || "—" }}</div></div>
					</div>
				</template>

				<template v-else-if="section.key === 'requirements'">
					<table class="kt-table"><thead><tr><th>Item</th><th>Specification</th><th class="is-num">Quantity</th></tr></thead>
						<tbody><tr v-for="line in (section.details || {}).goods_lines || (section.details || {}).items || []" :key="line.line_number || line.requisition_item_id"><td>{{ line.description || line.item_name }}</td><td>{{ specOf(section.details, line) }}</td><td class="is-num">{{ line.quantity }} {{ line.unit }}</td></tr></tbody>
					</table>
					<table v-if="((section.details || {}).technical_requirements || []).length" class="kt-table" style="margin-top: 12px"><thead><tr><th>Technical requirement</th><th>Required value</th></tr></thead>
						<tbody><tr v-for="t in section.details.technical_requirements" :key="t.technical_requirement_id"><td>{{ t.label }}</td><td>{{ t.required_value }} {{ t.unit }}</td></tr></tbody>
					</table>
				</template>

				<table v-else-if="section.key === 'pricing'" class="kt-table"><thead><tr><th>Line</th><th style="text-align: right">Quantity</th><th style="text-align: right">Unit price</th><th style="text-align: right">Total</th></tr></thead>
					<tbody><tr v-for="line in (section.details || {}).rows || (Array.isArray(section.details) ? section.details : [])" :key="line.line"><td>{{ line.description }}</td><td class="is-num">{{ line.quantity }} {{ line.unit }}</td><td class="is-num tnd-muted">{{ line.unit_price }}</td><td class="is-num tnd-muted">{{ line.line_total }}</td></tr></tbody>
				</table>

				<template v-else-if="section.key === 'supplier'">
					<table class="kt-table"><thead><tr><th>Requirement</th><th>Detail</th></tr></thead>
						<tbody>
							<tr v-for="q in (section.details || {}).qualification || []" :key="q.criterion"><td>{{ q.criterion }}</td><td>{{ qualificationDetail(q) }}</td></tr>
							<tr v-for="e in (section.details || {}).evidence_requirements || []" :key="e.evidence_requirement_id"><td>{{ e.label }}</td><td>{{ e.mandatory ? "Required" : "Optional" }} · {{ e.proves }}</td></tr>
						</tbody>
					</table>
				</template>

				<template v-else-if="section.key === 'technical'">
					<table class="kt-table"><thead><tr><th>Evidence</th><th>Proves</th><th>Status</th></tr></thead>
						<tbody>
							<tr><td>Template release</td><td>{{ (section.details || {}).template_release_id }}</td><td><span class="kt-status is-live">Bound</span></td></tr>
							<tr v-for="l in (section.details || {}).lineage || []" :key="l.line"><td>Line {{ l.line }} — {{ l.description }}</td><td>{{ l.quantity }} from {{ (l.source_items || []).length }} authorised item{{ (l.source_items || []).length === 1 ? "" : "s" }}</td><td><span class="kt-status is-live">Traced</span></td></tr>
							<tr><td>Requirement mappings</td><td>{{ mappingsLine(section.details) }}</td><td><span class="kt-status is-live">Complete</span></td></tr>
						</tbody>
					</table>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
import { reactive } from "vue";

const props = defineProps({
	sections: { type: Array, default: () => [] },
	findings: { type: Array, default: () => [] },
	nested: Boolean,
});
const state = reactive({});

function isOpen(section) {
	// TPR-DES-05/06/07/09's own boards never wrap the pricing table's body in
	// a collapse guard — it is drawn open, unconditionally, in every one of
	// them (verbatim: their disclosure-head onclick only spins the chevron,
	// with no sc-if on the body). Ported literally: the section is always
	// expanded and its chevron toggle is decorative for this one section.
	if (section.key === "pricing") return true;
	return section.key in state ? state[section.key] : !!section.open;
}
function toggle(key) {
	const section = props.sections.find((s) => s.key === key);
	state[key] = !isOpen(section);
}
function tagFor(key) {
	const mine = props.findings.filter((f) => (key === "contract" ? f.link_label === "Review contract terms" : key === "supplier" ? f.task === "requirements" && f.link_label !== "Review contract terms" : key === "details" ? f.task === "details" : false));
	if (!mine.length) return "";
	const must = mine.filter((f) => f.severity === "Must fix").length;
	const notes = mine.length - must;
	const parts = [];
	if (must) parts.push(`${must} must fix`);
	if (notes) parts.push(`${notes} review note${notes === 1 ? "" : "s"}`);
	return parts.join(" · ");
}
function specOf(details, line) {
	const techs = (details || {}).technical_requirements || [];
	return techs.length ? techs.slice(0, 4).map((t) => `${t.label} ${t.required_value}${t.unit ? " " + t.unit : ""}`).join(", ") : line.intended_use || line.equipment_category || "";
}
function qualificationDetail(q) {
	if (!q.required) return "Not required";
	if (q.minimum_contracts) return `${q.minimum_contracts} contracts / ${q.period_years} years`;
	if (q.evidence) return q.evidence;
	return "Required";
}
function mappingsLine(details) {
	const m = (details || {}).mappings || {};
	return `${m.technical_requirements || 0} technical requirements → ${m.responses || 0} supplier responses, ${m.evaluation || 0} evaluation checks, ${m.contract || 0} contract obligations`;
}
</script>
