import React from "react";

/**
 * KenTender context-preserving navigation — engineer reference canvas.
 * Canonical: docs/prompts/strategy/1. ken_tender_frappe_context_preserving_form_navigation_pattern.md
 */
export default function ContextPreservingNavigationCanvas() {
	return (
		<div style={{ fontFamily: "system-ui, sans-serif", padding: 24, maxWidth: 960, lineHeight: 1.5 }}>
			<h1 style={{ fontSize: 22, marginBottom: 8 }}>Context-preserving navigation</h1>
			<p style={{ color: "#555", marginTop: 0 }}>
				Forms and builders stay on separate Frappe routes, but users never lose module context.
			</p>

			<h2 style={{ fontSize: 16 }}>Shell layout</h2>
			<pre
				style={{
					background: "#f4f6f8",
					padding: 16,
					borderRadius: 8,
					fontSize: 13,
					overflow: "auto",
				}}
			>{`┌ Global KenTender left nav (stable) ─┬ Module breadcrumb + record title ─┐
│  Strategy / DIA / Budget active    │ [Back to Workbench]  [Save] [Submit] │
├────────────────────────────────────┴──────────────────────────────────────┤
│  Form / builder / review content (Desk Page or Form route)                 │
└────────────────────────────────────────────────────────────────────────────┘`}</pre>

			<h2 style={{ fontSize: 16 }}>Navigation flow</h2>
			<pre style={{ background: "#f4f6f8", padding: 16, borderRadius: 8, fontSize: 13 }}>
				{`Workbench ──kt_nav.toBuilder/toForm──► Builder or Form
     ▲                                      │
     └──── kt_nav.toWorkbench + kt_state ───┘`}
			</pre>

			<h2 style={{ fontSize: 16 }}>Shared APIs (kentender_core)</h2>
			<ul style={{ fontSize: 14 }}>
				<li>
					<code>kt_module_registry</code> — module definitions
				</li>
				<li>
					<code>kt_nav.toWorkbench / toBuilder / toForm</code>
				</li>
				<li>
					<code>kt_state.save / restore / setSelectedRecord</code>
				</li>
				<li>
					<code>kt_shell.mountHeader</code> → <code>data-testid="back-to-workbench"</code>
				</li>
			</ul>

			<h2 style={{ fontSize: 16 }}>New module checklist</h2>
			<ol style={{ fontSize: 14 }}>
				<li>Register in kt_module_registry.js + module_registry.py</li>
				<li>Wire workbench leave → kt_state.save</li>
				<li>Wire builder/form → kt_shell header + back-to-workbench</li>
				<li>Add route prefix to boot sidebar map</li>
				<li>Playwright: expectBackToWorkbench</li>
			</ol>
		</div>
	);
}
