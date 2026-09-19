<!-- TPR-DES-05/06/07 key-facts row: one .kt-kpi-card per server fact, in the
     server's order (§10.6 item 4 — Purchase/Requisition/Quantity/Approved
     value/Method/Submission deadline/Tender security/Reservation/Latest
     delivery; the AO board adds Tendering period). -->
<template>
	<div class="tnd-section" data-testid="tnd-key-facts">
		<div class="kt-kpi-row">
			<div v-for="fact in facts" :key="fact.label" class="kt-kpi-card">
				<svg class="kt-kpi-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path v-for="(d, i) in icon(fact.label)" :key="i" :d="d"></path></svg>
				<div class="kt-kpi-value" :class="wide(fact) ? 'tnd-kpi-value--sm' : 'tnd-kpi-value--md'">{{ fact.value || "—" }}</div>
				<div class="kt-kpi-sub">{{ fact.label }}</div>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({ facts: { type: Array, default: () => [] } });

const ICONS = {
	Purchase: ["M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z", "M14 2v6h6", "M16 13H8", "M16 17H8"],
	Requisition: ["M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z", "M14 2v6h6", "M16 13H8", "M16 17H8"],
	Quantity: ["M16.5 9.4 7.5 4.21", "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z", "m3.3 7 8.7 5 8.7-5", "M12 22V12"],
	"Approved value": ["M2 6h20v12H2z", "M12 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4", "M6 12h.01M18 12h.01"],
	Method: ["m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z", "m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z", "M7 21h10", "M12 3v18", "M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"],
	"Submission deadline": ["M3 4h18v18H3z", "M16 2v4M8 2v4M3 10h18"],
	"Tendering period": ["M3 4h18v18H3z", "M16 2v4M8 2v4M3 10h18"],
	"Tender security": ["M20 13c0 5-3.5 7.5-7.5 8.5-.4.1-.6.1-1 0C7.5 20.5 4 18 4 13V6l8-3 8 3z"],
	Reservation: ["M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", "M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8", "M22 21v-2a4 4 0 0 0-3-3.87", "M16 3.13a4 4 0 0 1 0 7.75"],
	"Latest delivery": ["M14 18V6a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h1", "M14 9h4l4 4v4a1 1 0 0 1-1 1h-2", "M7 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4", "M17 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4"],
};
function icon(label) {
	return ICONS[label] || ICONS.Purchase;
}
function wide(fact) {
	return String(fact.value || "").length > 14;
}
</script>
