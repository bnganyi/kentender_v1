/**
 * Civic Ledger — offline Tailwind build.
 *
 * theme.extend is copied verbatim from the inline tailwind.config in
 * docs/std-prod-impl/IT-STD-Wizard-v3/B-Components/code.html (lines 6-160).
 *
 * Output is compiled once and committed to
 * kentender_core/public/css/civic_ledger.css. This is NOT part of `bench build`.
 * See README.md for the single regen command.
 *
 * important: '.kt-cl-shell' scopes every utility under body.kt-cl-shell and
 * raises specificity so it wins over Frappe's Bootstrap without leaking.
 * preflight is disabled so we never reset Frappe Desk globally.
 */
module.exports = {
	content: [
		"./sources/**/*.html",
		// Live mocks (C1-M1 dashboard + C1-M2 create modal) — keep CSS in sync with screens
		"../../docs/std-prod-impl/IT-STD-Wizard-v3/C1-M1/*.html",
		"../../docs/std-prod-impl/IT-STD-Wizard-v3/C1-M2/*.html",
		"../../kentender_core/kentender_core/public/js/kt_cl_*.js",
		"../../kentender_procurement/kentender_procurement/public/js/kt_cl_*.js",
		"../../kentender_procurement/kentender_procurement/public/js/it_tender_*.js",
	],
	darkMode: "class",
	important: ".kt-cl-shell",
	corePlugins: { preflight: false, container: false },
	theme: {
		extend: {
			colors: {
				"on-error-container": "#93000a",
				"outline-variant": "#c4c6cf",
				background: "#f7f9fb",
				tertiary: "#030a1d",
				"tertiary-container": "#192135",
				"tertiary-fixed-dim": "#bec6e0",
				"error-container": "#ffdad6",
				"primary-container": "#002244",
				"secondary-fixed-dim": "#b9c7e0",
				"surface-container-lowest": "#ffffff",
				"on-secondary-fixed-variant": "#3a485c",
				"secondary-fixed": "#d5e3fd",
				"on-secondary-fixed": "#0d1c2f",
				outline: "#74777f",
				primary: "#000b1d",
				"on-secondary": "#ffffff",
				"tertiary-fixed": "#dae2fd",
				"surface-container-high": "#e6e8ea",
				"on-tertiary-fixed": "#131b2e",
				"surface-container-low": "#f2f4f6",
				"surface-bright": "#f7f9fb",
				"primary-fixed": "#d4e3ff",
				"surface-container": "#eceef0",
				"on-secondary-container": "#57657b",
				"on-primary": "#ffffff",
				"on-tertiary-fixed-variant": "#3f465c",
				"surface-tint": "#456085",
				"secondary-container": "#d5e3fd",
				"on-surface": "#191c1e",
				"inverse-surface": "#2d3133",
				"inverse-on-surface": "#eff1f3",
				error: "#ba1a1a",
				secondary: "#515f74",
				"inverse-primary": "#adc8f3",
				"on-surface-variant": "#43474e",
				"on-tertiary": "#ffffff",
				"surface-dim": "#d8dadc",
				"surface-variant": "#e0e3e5",
				"on-error": "#ffffff",
				"on-background": "#191c1e",
				"on-tertiary-container": "#8188a0",
				"on-primary-fixed-variant": "#2d486c",
				surface: "#f7f9fb",
				"surface-container-highest": "#e0e3e5",
				"primary-fixed-dim": "#adc8f3",
				"on-primary-container": "#708ab2",
				"on-primary-fixed": "#001c3a",
			},
			borderRadius: {
				DEFAULT: "0.125rem",
				lg: "0.25rem",
				xl: "0.5rem",
				full: "0.75rem",
			},
			spacing: {
				"input-height": "28px",
				"component-gap": "8px",
				unit: "4px",
				gutter: "12px",
				"container-padding": "16px",
				"table-row-height": "32px",
			},
			fontFamily: {
				display: ["Public Sans"],
				"label-md": ["JetBrains Mono"],
				"body-md": ["Public Sans"],
				"headline-lg": ["Public Sans"],
				"headline-md": ["Public Sans"],
				"label-sm": ["JetBrains Mono"],
				"body-lg": ["Public Sans"],
				"body-sm": ["Public Sans"],
			},
			fontSize: {
				display: ["32px", { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700" }],
				"label-md": ["11px", { lineHeight: "14px", letterSpacing: "0.02em", fontWeight: "500" }],
				"body-md": ["13px", { lineHeight: "18px", letterSpacing: "0", fontWeight: "400" }],
				"headline-lg": ["24px", { lineHeight: "32px", letterSpacing: "-0.01em", fontWeight: "600" }],
				"headline-md": ["18px", { lineHeight: "24px", letterSpacing: "0", fontWeight: "600" }],
				"label-sm": ["10px", { lineHeight: "12px", letterSpacing: "0.04em", fontWeight: "500" }],
				"body-lg": ["14px", { lineHeight: "20px", letterSpacing: "0", fontWeight: "400" }],
				"body-sm": ["12px", { lineHeight: "16px", letterSpacing: "0", fontWeight: "400" }],
			},
		},
	},
};
