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
					environment: "jsdom",
					include: [
						"kentender_procurement/kentender_procurement/public/js/procurement_planning/**/*.spec.js",
					],
				},
			},
			{
				// NDS-906 — the Departmental Needs presentation helpers. These are
				// plain ES modules with no Vue or frappe dependency, so they need
				// no component toolchain; the components that consume them are
				// asserted in the browser layer (tests/ui/smoke/departmental_needs).
				test: {
					name: "departmental-needs",
					environment: "node",
					include: [
						"kentender_procurement/kentender_procurement/public/js/departmental_needs/**/*.spec.js",
					],
				},
			},
		],
	},
});
