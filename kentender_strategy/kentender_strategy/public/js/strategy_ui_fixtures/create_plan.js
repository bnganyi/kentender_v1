// Extracted from docs/mvp-1/01_strategy/ui_design/create_plan/code.html <main>
// Stitch classes preserved byte-for-byte; only surgical data-testid / data-kt-str-* hooks.
frappe.provide("kentender_strategy.ui_fixtures");
kentender_strategy.ui_fixtures.create_plan = function () {
	return `<div class="kt-str-root" data-testid="kt-str-create-plan">
<main class="flex-1 bg-surface-container-low p-section-gap overflow-y-auto" data-testid="kt-str-create-main-surface">
<div class="max-w-5xl mx-auto space-y-section-gap">
<!-- Page Header -->
<div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
<div>
<nav class="flex items-center gap-2 text-on-surface-variant mb-2">
<span class="text-xs uppercase font-bold tracking-widest">Strategy Alignment</span>
<span class="material-symbols-outlined text-sm">chevron_right</span>
<span class="text-xs uppercase font-bold tracking-widest text-primary">New Plan</span>
</nav>
<h1 class="font-manrope font-headline-lg text-headline-lg text-primary">Create strategic plan</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant">Set up a new strategic framework to guide procurement outcomes.</p>
</div>
</div>
<!-- Bento Grid Layout for Form -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-section-gap" data-testid="kt-str-create-bento">
<!-- Main Form Section (Col Span 8) -->
<div class="lg:col-span-8 space-y-section-gap" data-kt-str-create-main="1">
<section class="bg-surface-container-lowest p-card-padding rounded-xl border border-outline-variant shadow-sm">
<div class="flex items-center gap-2 mb-6 pb-4 border-b border-surface-container">
<span class="material-symbols-outlined text-primary">description</span>
<h2 class="font-manrope font-headline-sm text-headline-sm">Basic Information</h2>
</div>
<form class="space-y-6 kt-str-create-plan-form" id="planForm" data-testid="kt-str-create-plan-form" novalidate>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<!-- Plan Code -->
<div class="space-y-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase" for="plan_code">Plan code <span class="text-error">*</span></label>
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 font-data-mono text-data-mono focus:ring-2 focus:ring-primary focus:border-primary transition-all uppercase" id="plan_code" name="plan_code" data-kt-str-field="plan_code" placeholder="e.g., MOH-SP-2026-2030" required="" type="text" autocomplete="off">
<p class="text-xs text-error hidden" data-kt-str-error="plan_code"></p>
</div>
<!-- Plan Type -->
<div class="space-y-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase" for="plan_type">Plan type <span class="text-error">*</span></label>
<select class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 font-body-md text-body-md focus:ring-2 focus:ring-primary focus:border-primary transition-all" id="plan_type" name="plan_type" data-kt-str-field="plan_type" required="">
<option disabled="" selected="" value="">Select plan type</option>
<option value="entity">Entity Strategic Plan</option>
<option value="sector">Sector Strategy</option>
<option value="programme">Programme Strategy</option>
<option value="other">Other</option>
</select>
<p class="text-xs text-error hidden" data-kt-str-error="plan_type"></p>
</div>
</div>
<!-- Plan Title -->
<div class="space-y-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase" for="plan_title">Plan title <span class="text-error">*</span></label>
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 font-body-md text-body-md focus:ring-2 focus:ring-primary focus:border-primary transition-all" id="plan_title" name="plan_title" data-kt-str-field="title" placeholder="e.g., Ministry of Health Strategic Plan" required="" type="text">
<p class="text-xs text-error hidden" data-kt-str-error="title"></p>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
<!-- Start Date -->
<div class="space-y-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase" for="start_date">Start date <span class="text-error">*</span></label>
<div class="relative">
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 font-body-md text-body-md focus:ring-2 focus:ring-primary focus:border-primary transition-all appearance-none" id="start_date" name="start_date" data-kt-str-field="start_date" required="" type="date">
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none">calendar_today</span>
</div>
<p class="text-xs text-error hidden" data-kt-str-error="start_date"></p>
</div>
<!-- End Date -->
<div class="space-y-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase" for="end_date">End date <span class="text-error">*</span></label>
<div class="relative">
<input class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 font-body-md text-body-md focus:ring-2 focus:ring-primary focus:border-primary transition-all appearance-none" id="end_date" name="end_date" data-kt-str-field="end_date" required="" type="date">
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none">calendar_today</span>
</div>
<p class="text-xs text-error hidden" data-kt-str-error="end_date"></p>
</div>
</div>
<!-- Description -->
<div class="space-y-2">
<label class="block font-label-caps text-label-caps text-on-surface-variant uppercase" for="description">Description (Optional)</label>
<textarea class="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 font-body-md text-body-md focus:ring-2 focus:ring-primary focus:border-primary transition-all resize-none" id="description" name="description" data-kt-str-field="description" placeholder="Briefly describe the purpose and core mission of this strategic framework..." rows="4"></textarea>
<p class="text-xs text-error hidden" data-kt-str-error="description"></p>
</div>
</form>
</section>
</div>
<!-- Sidebar Info / Metadata Section (Col Span 4) -->
<div class="lg:col-span-4 space-y-section-gap" data-kt-str-create-aside="1">
<!-- System Context Metadata -->
<div class="bg-surface-container-lowest p-card-padding rounded-xl border border-outline-variant shadow-sm space-y-gutter" data-testid="kt-str-create-plan-context">
<div class="flex items-center gap-2 pb-2 border-b border-surface-container">
<span class="material-symbols-outlined text-secondary">info</span>
<h3 class="font-manrope font-headline-sm text-[16px]">Plan Context</h3>
</div>
<div class="space-y-4">
<div class="flex flex-col gap-1">
<span class="font-label-caps text-[10px] text-on-surface-variant uppercase">Procuring Entity</span>
<select class="w-full bg-surface-container border border-outline-variant/30 rounded-lg px-3 py-2 font-body-md text-body-md focus:ring-2 focus:ring-primary focus:border-primary transition-all" data-kt-str-field="procuring_entity_select" aria-label="Procuring entity">
<option value="">Select procuring entity</option>
</select>
<input type="hidden" name="procuring_entity" data-kt-str-field="procuring_entity">
<p class="text-xs text-error hidden" data-kt-str-error="procuring_entity"></p>
</div>
<div class="grid grid-cols-2 gap-4">
<div class="flex flex-col gap-1">
<span class="font-label-caps text-[10px] text-on-surface-variant uppercase">Version</span>
<span class="font-data-mono text-data-mono text-primary px-3 py-1 bg-primary-fixed rounded w-fit">v1.0.0</span>
</div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-[10px] text-on-surface-variant uppercase">Status</span>
<span class="font-label-caps text-[10px] px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-full border border-outline-variant w-fit">DRAFT</span>
</div>
</div>
<div class="flex flex-col gap-1">
<span class="font-label-caps text-[10px] text-on-surface-variant uppercase">Created by</span>
<div class="flex items-center gap-2" data-kt-str-created-by="1">
<div class="w-6 h-6 rounded-full bg-secondary-fixed flex items-center justify-center text-[10px] font-bold text-on-secondary-fixed" data-kt-str-created-by-initials>—</div>
<span class="font-body-md text-body-md"><span data-kt-str-created-by-name>—</span> <span class="text-on-surface-variant text-xs" data-kt-str-created-by-role>(Lead)</span></span>
</div>
</div>
</div>
</div>
<!-- Visual Reinforcement / Quote -->
<div class="relative overflow-hidden rounded-xl h-48 bg-primary-container p-card-padding flex flex-col justify-end text-white group" data-testid="kt-str-create-quote">
<div class="absolute inset-0 transition-transform duration-700 group-hover:scale-110 opacity-40" data-alt="Abstract architectural lines and geometric patterns in blue and white, representing strategic framework and structural integrity. The lighting is crisp and modern, reflecting a sense of precision and enterprise growth. High-end professional corporate aesthetic with subtle gradients." style="background-image: url(&quot;https://lh3.googleusercontent.com/aida-public/AB6AXuATiL1JvHEV2g0CuEv2S0iHfARYzoUJCiORsX7LZXWMjzBv5xSQ_myEdEaJ4MKuy8eio8RBGufXjk-tInB8QU54MB5QGmqTnVjZHb7V3SjrSNwVO3fus0czG0qV2zYc8OMYhxvYmrC2vLrxDg4gPihPRpYuXz6GhfgcETO1S9E6mOWBfyP6OyhOSSWD2TF_5SbfbOyRq7NxBVJ5TOKChgPdMTGdLQ9N5yj6aVlcKAIPAgfEuiD0cE_XYw&quot;);"></div><div class="absolute inset-0 bg-primary/60 z-0"></div>
<div class="relative z-10">
<span class="material-symbols-outlined text-4xl mb-2 text-primary-fixed">architecture</span>
<p class="font-headline-sm text-headline-sm leading-tight italic font-bold shadow-sm">"Strategic procurement is the engine of institutional efficiency."</p>
</div>
</div>
</div>
</div>
<!-- Bottom Action Bar -->
<div class="flex flex-col sm:flex-row items-center justify-between gap-gutter pt-section-gap border-t border-outline-variant" data-testid="kt-str-create-actions">
<p class="text-body-md text-on-surface-variant italic">
<span class="material-symbols-outlined align-middle text-sm mr-1">info</span>
                        Once created, you will be redirected to define goals and objectives.
                    </p>
<div class="flex items-center gap-4 w-full sm:w-auto">
<button class="flex-1 sm:flex-none px-6 py-2.5 font-manrope font-bold text-primary border-2 border-primary rounded-lg hover:bg-primary/5 transition-all active:scale-95" type="button" data-kt-str-action="cancel-create" data-testid="kt-str-create-plan-cancel">
                            Cancel
                        </button>
<button class="flex-1 sm:flex-none px-8 py-2.5 font-manrope font-bold text-white bg-primary rounded-lg shadow-md hover:bg-primary-container hover:shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2" form="planForm" type="submit" data-kt-str-action="submit-create" data-testid="kt-str-create-plan-submit">
                            Create plan
                            <span class="material-symbols-outlined text-sm">arrow_forward</span>
</button>
</div>
</div>
</div>
</main>
<!-- Success Feedback (Hidden by default) -->
<div class="fixed bottom-6 right-6 z-[100] transform translate-y-24 opacity-0 transition-all duration-500 pointer-events-none" id="successToast" data-testid="kt-str-create-toast" aria-hidden="true">
<div class="bg-primary text-white p-4 rounded-xl shadow-2xl flex items-center gap-4 border border-primary-fixed/20">
<div class="bg-white/20 p-2 rounded-lg">
<span class="material-symbols-outlined">check_circle</span>
</div>
<div>
<p class="font-bold">Plan framework initialized</p>
<p class="text-xs opacity-80" data-kt-str-toast-detail>Opening Plan Overview for "MOH Strategic Plan"...</p>
</div>
</div>
</div>
</div>`;
};
