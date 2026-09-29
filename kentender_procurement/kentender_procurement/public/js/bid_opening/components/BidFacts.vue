<!-- One opened bid's facts as the boards draw them (c5, c6): from the opened
     bid itself, never editable. -->
<template>
	<div class="kt-meta-row" data-testid="bop-bid-facts"><div><span class="kt-label">Bid</span><span class="kt-meta-value">{{ bid.number }}</span></div><div><span class="kt-label">Tenderer</span><span class="kt-meta-value">{{ bid.tenderer }}</span></div><div><span class="kt-label">Submitted total</span><span class="kt-meta-value">{{ bid.submitted_total }}</span></div><div><span class="kt-label">Tender security given</span><span class="kt-meta-value">{{ bid.security_given || "None" }}</span></div><div><span class="kt-label">Pages</span><span class="kt-meta-value">{{ bid.page_count }}<template v-if="bid.price_page"> · price on page {{ bid.price_page }}</template></span></div></div>
</template>

<script setup>
defineProps({ bid: { type: Object, required: true } });
</script>
