import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
	test: {
		projects: [
			{
				test: {
					name: "std-engine-node",
					environment: "node",
					include: ["frontend/src/**/*.spec.ts"],
				},
			},
			{
				test: {
					name: "std-engine-jsdom",
					environment: "jsdom",
					include: ["frontend/src/**/*.spec.tsx"],
				},
			},
			{
				// PLN-CHG-001 v1.2 §15.1(5) (decision D9) — real SFC component
				// tests for the Procurement Planning screens: exact fields,
				// absent fields, task detail, errors, dialog copy and action
				// visibility, alongside (never instead of) the browser layer.
				plugins: [vue()],
				test: {
					name: "procurement-planning",
					// Board comparisons parse whole .dc.html files with JSDOM; under
					// `make ui-structure-gate`'s parallel load that legitimately
					// exceeds the 5 s default (measured 24 Sep 2026: 5.3–9.2 s).
					testTimeout: 30_000,
					environment: "jsdom",
					// The shared guidance components mount through kentender_core's
					// real bundle (KT-STD-001 v1.8 §2.9).
					setupFiles: ["kentender_procurement/kentender_procurement/public/js/procurement_planning/vitest.setup.js"],
					include: [
						"kentender_procurement/kentender_procurement/public/js/procurement_planning/**/*.spec.js",
					],
				},
			},
			{
				// REQ-CHG-001 v1.6 §18.1 — real SFC component tests for the
				// Procurement Requisitions screens, alongside (never instead of)
				// the browser layer.
				plugins: [vue()],
				test: {
					name: "procurement-requisitions",
					environment: "jsdom",
					include: [
						"kentender_procurement/kentender_procurement/public/js/procurement_requisitions/**/*.spec.js",
					],
				},
			},
			{
				// TPR-CHG-001 v0.8 §11 — SFC component tests for the Tenders
				// screens and dialogs, alongside (never instead of) the browser layer.
				plugins: [vue()],
				test: {
					name: "tenders",
					environment: "jsdom",
					// TPR-CHG-001 v0.12 §10.17 — the shared guidance region mounts
					// through kentender_core's real bundle.
					setupFiles: ["kentender_procurement/kentender_procurement/public/js/tenders/vitest.setup.js"],
					include: ["kentender_procurement/kentender_procurement/public/js/tenders/**/*.spec.js"],
				},
			},
			{
				// BDS-CHG-001 v0.8 plan OD-B — the Bid Submission public portal
				// screens, alongside (never instead of) the browser layer.
				plugins: [vue()],
				test: {
					name: "bid-portal",
					environment: "jsdom",
					setupFiles: ["kentender_procurement/kentender_procurement/public/js/bid_portal/vitest.setup.js"],
					include: ["kentender_procurement/kentender_procurement/public/js/bid_portal/**/*.spec.js"],
				},
			},
			{
				// BDS-CHG-001 v0.8 owner decisions OD-G/OD-H — the Desk page for
				// the blind physical tender-security intake.
				plugins: [vue()],
				test: {
					name: "tender-security-receipts",
					environment: "jsdom",
					setupFiles: ["kentender_procurement/kentender_procurement/public/js/tender_security_receipts/vitest.setup.js"],
					include: ["kentender_procurement/kentender_procurement/public/js/tender_security_receipts/**/*.spec.js"],
				},
			},
			{
				// STD-TPL-IMP-001 v1.0 §11 — SFC component and structural-fidelity
				// tests for STD Templates, alongside (never instead of) the browser layer.
				plugins: [vue()],
				test: {
					name: "std-templates",
					environment: "jsdom",
					include: ["kentender_procurement/kentender_procurement/public/js/std_templates/**/*.spec.js"],
				},
			},
			{
				// AUTH-ADR-001 v1.6 §18.2 items 22–24 — SFC component tests for the
				// System setup tabs and dialogs: field variants per registry scope,
				// server-decided action visibility, and state rendering, alongside
				// (never instead of) the browser layer.
				plugins: [vue()],
				test: {
					name: "system-setup",
					// Board comparisons parse whole .dc.html files with JSDOM; under
					// `make ui-structure-gate`'s parallel load that legitimately
					// exceeds the 5 s default (measured 24 Sep 2026: 5.3–9.2 s).
					testTimeout: 30_000,
					environment: "jsdom",
					setupFiles: [
						"kentender_core/kentender_core/public/js/system_setup/vitest.setup.js",
					],
					include: [
						"kentender_core/kentender_core/public/js/system_setup/**/*.spec.js",
					],
				},
			},
			{
				// The shared Vue-in-Desk page runtime (kt_desk_page.js): every
				// page's route listener, pause/resume and command runner. Run by
				// `make ui-structure-gate` beside the screens that depend on it.
				plugins: [vue()],
				test: {
					name: "desk-runtime",
					environment: "jsdom",
					// KT-STD-001 v1.8 §2.9 — the shared journey tracker and next-step
					// block (kt_industry_guidance.bundle.js) are shared runtime too.
					include: [
						"kentender_core/kentender_core/public/js/kt_desk_page.spec.js",
						"kentender_core/kentender_core/public/js/kt_industry/**/*.spec.js",
						// BDS-CHG-001 v0.8 plan OD-B — the public portal runtime,
						// kept in step with kt_desk_page.js by a shared spec.
						"kentender_core/kentender_core/public/js/kt_portal/**/*.spec.js",
					],
				},
			},
			{
				// AUTH-ADR-001 §10 — the Technical record search screen's own
				// component test: Empty, No match, results + Open route, and
				// Forbidden, alongside (never instead of) the browser layer.
				plugins: [vue()],
				test: {
					name: "technical-search",
					environment: "jsdom",
					setupFiles: [
						"kentender_core/kentender_core/public/js/technical_search/vitest.setup.js",
					],
					include: [
						"kentender_core/kentender_core/public/js/technical_search/**/*.spec.js",
					],
				},
			},
			{
				// NDS-906 — the Departmental Needs presentation helpers (plain ES
				// modules, no Vue/frappe dependency) run under plain Node.
				test: {
					name: "departmental-needs",
					environment: "node",
					include: [
						"kentender_procurement/kentender_procurement/public/js/departmental_needs/data/*.spec.js",
					],
				},
			},
			{
				// NDS-DES-14/15 boundary-state remediation — real SFC component
				// tests for the Departmental Needs screens, alongside (never
				// instead of) the browser layer, matching the Procurement
				// Planning/Requisitions/Tenders precedent above.
				plugins: [vue()],
				test: {
					name: "departmental-needs-components",
					// Board comparisons parse whole .dc.html files with JSDOM; under
					// `make ui-structure-gate`'s parallel load that legitimately
					// exceeds the 5 s default (measured 24 Sep 2026: 5.3–9.2 s).
					testTimeout: 30_000,
					environment: "jsdom",
					include: [
						"kentender_procurement/kentender_procurement/public/js/departmental_needs/components/*.spec.js",
					],
				},
			},
			{
				// The structural half of design fidelity: the containers a
				// board draws and how they nest, which the landmark gate in
				// tests/ui/helpers/designFidelity.ts cannot see because it
				// compares text. Runs in Node over HTML strings — the same
				// comparator serves the browser gates.
				test: {
					name: "design-fidelity",
					environment: "node",
					include: ["tests/ui/fidelity/**/*.spec.js"],
				},
			},
		],
	},
});
