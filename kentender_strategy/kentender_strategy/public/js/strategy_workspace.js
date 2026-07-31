// Strategy Management workspace — Portfolio Hub with live backend wiring.
// Stitch source: docs/misc/strategy_management_home_code.html
(function () {
	const WS_LABEL = "Strategy Management";
	let bound = false;
	let observer = null;

	function ensureFonts() {
		if (!document.getElementById("kt-sph-fonts")) {
			const l = document.createElement("link");
			l.id = "kt-sph-fonts";
			l.rel = "stylesheet";
			l.href =
				"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700" +
				"&family=Manrope:wght@500;600;700;800" +
				"&family=JetBrains+Mono:wght@500;600&display=swap";
			document.head.appendChild(l);
		}
		if (!document.getElementById("kt-sph-icons")) {
			const l = document.createElement("link");
			l.id = "kt-sph-icons";
			l.rel = "stylesheet";
			l.href =
				"https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap";
			document.head.appendChild(l);
		}
	}

	function userInitial() {
		try {
			let name = "";
			if (typeof frappe !== "undefined" && frappe.boot && frappe.boot.user_info && frappe.session) {
				const info = frappe.boot.user_info[frappe.session.user] || {};
				name = info.fullname || info.name || frappe.session.user || "";
			}
			name = String(name).trim();
			if (!name || name === "Guest") return "A";
			return name.charAt(0).toUpperCase();
		} catch (_) {
			return "A";
		}
	}

	function slug(v) {
		return String(v || "")
			.toLowerCase()
			.replace(/\s+/g, "-");
	}

	function isStrategyWorkspaceRoute() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const w = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					return slug(w) === slug(WS_LABEL);
				}
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const href = (window.location && (window.location.pathname + window.location.hash)) || "";
			return decodeURIComponent(href).toLowerCase().includes("strategy-management");
		} catch (e) {
			return false;
		}
	}

	function resolveMount() {
		const page =
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]');
		if (page) {
			return (
				page.querySelector(".layout-main-section .editor-js-container") ||
				page.querySelector(".editor-js-container") ||
				page.querySelector(".layout-main-section")
			);
		}
		return document.querySelector(".editor-js-container");
	}

	function staticHierarchyWorkbenchHtml() {
		return `
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;900&display=swap">
<style>
/* ── Strategic Workbench skin – scoped to .kt-swb ── */
.kt-swb,.kt-swb *,.kt-swb *::before,.kt-swb *::after{box-sizing:border-box;margin:0;padding:0}
.kt-swb{font-family:'Hanken Grotesk',-apple-system,BlinkMacSystemFont,sans-serif;color:#191c1e}
/* breadcrumb */
.kt-swb-crumb{display:flex;align-items:center;gap:4px;font-size:11px;font-weight:500;line-height:14px;color:#45464d;margin-bottom:8px;flex-wrap:wrap}
.kt-swb-crumb a{display:flex;align-items:center;gap:4px;color:#45464d;text-decoration:none;margin-right:16px}
.kt-swb-crumb a:hover{color:#000}
.kt-swb-crumb a .material-symbols-outlined{font-size:14px}
.kt-swb-crumb-sep{color:#c6c6cd;margin-right:16px}
.kt-swb-crumb-current{color:#000;font-weight:700}
/* page header */
.kt-swb-page-hdr{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:24px}
.kt-swb-page-title{font-size:30px;line-height:36px;letter-spacing:-0.02em;font-weight:700;color:#000}
.kt-swb-page-sub{font-size:14px;line-height:20px;color:#45464d;margin-top:4px}
.kt-swb-hdr-actions{display:flex;gap:16px;flex-shrink:0}
.kt-swb-btn-outline{padding:8px 24px;border:1px solid #76777d;color:#000;border-radius:4px;font-weight:700;font-size:12px;letter-spacing:.05em;background:transparent;cursor:pointer;font-family:inherit;line-height:16px}
.kt-swb-btn-outline:hover{background:#f2f4f6}
.kt-swb-btn-primary{padding:8px 24px;background:#000;color:#fff;border:none;border-radius:4px;font-weight:700;font-size:12px;letter-spacing:.05em;cursor:pointer;font-family:inherit;line-height:16px}
/* KPI grid */
.kt-swb-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin-bottom:32px}
.kt-swb-kpi{background:#fff;border:1px solid #c6c6cd;padding:24px;border-radius:4px}
.kt-swb-kpi-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}
.kt-swb-kpi-label{font-size:12px;font-weight:600;letter-spacing:.05em;color:#45464d;text-transform:uppercase;line-height:16px}
.kt-swb-kpi-head .material-symbols-outlined{font-size:24px}
.kt-swb-icon-def{color:#000}
.kt-swb-icon-sec{color:#57657b}
.kt-swb-icon-err{color:#ba1a1a}
.kt-swb-kpi-val{font-size:30px;line-height:36px;letter-spacing:-0.02em;font-weight:900;margin-bottom:8px}
.kt-swb-kpi-bar{width:100%;height:8px;background:#e6e8ea;border-radius:9999px;overflow:hidden}
.kt-swb-kpi-bar-fill{height:100%;background:#000;border-radius:9999px}
.kt-swb-kpi-sub{display:flex;align-items:center;gap:4px;font-size:11px;font-weight:500;line-height:14px;color:#57657b}
.kt-swb-kpi-sub .material-symbols-outlined{font-size:14px}
.kt-swb-kpi-err{font-size:11px;font-weight:500;line-height:14px;color:#ba1a1a}
.kt-swb-kpi-date{font-size:20px;line-height:28px;font-weight:700;margin-bottom:4px}
.kt-swb-kpi-note{font-size:11px;font-weight:500;line-height:14px;color:#45464d}
.kt-swb-kpi--milestone{position:relative;overflow:hidden}
.kt-swb-kpi-bg{position:absolute;inset:0;opacity:.1;background:radial-gradient(circle at 70% 50%,#0f172a 0%,transparent 70%)}
.kt-swb-kpi-inner{position:relative;z-index:1}
/* hierarchy section */
.kt-swb-hier{background:#fff;border:1px solid #c6c6cd;border-radius:4px;box-shadow:0 1px 2px rgba(0,0,0,.05);overflow:hidden;margin-bottom:32px}
.kt-swb-hier-hdr{background:#f2f4f6;padding:16px 24px;border-bottom:1px solid #c6c6cd;display:flex;justify-content:space-between;align-items:center}
.kt-swb-hier-legend{display:flex;align-items:center;gap:24px}
.kt-swb-hier-title{font-size:12px;font-weight:700;letter-spacing:.05em;color:#000;text-transform:uppercase}
.kt-swb-legend-items{display:flex;align-items:center;gap:8px}
.kt-swb-dot{width:12px;height:12px;border-radius:9999px;display:inline-block;flex-shrink:0}
.kt-swb-dot-green{background:#22c55e}
.kt-swb-dot-amber{background:#f59e0b;margin-left:16px}
.kt-swb-legend-lbl{font-size:11px;font-weight:500;line-height:14px;color:#45464d}
.kt-swb-hier-ctrl{display:flex;align-items:center;gap:8px}
.kt-swb-search-wrap{position:relative;width:256px;margin-right:16px}
.kt-swb-search-wrap .material-symbols-outlined{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#45464d;font-size:18px;pointer-events:none}
.kt-swb-search-wrap input{width:100%;padding:4px 16px 4px 40px;background:#fff;border:1px solid #c6c6cd;border-radius:4px;font-size:11px;font-family:inherit;outline:none;line-height:16px}
.kt-swb-search-wrap input:focus{border-color:#000;box-shadow:0 0 0 1px #000}
.kt-swb-btn-add-prog{padding:4px 16px;background:#000;color:#fff;font-size:11px;font-weight:700;letter-spacing:.05em;border:none;border-radius:4px;cursor:pointer;display:flex;align-items:center;gap:4px;margin-right:16px;font-family:inherit}
.kt-swb-btn-add-prog .material-symbols-outlined{font-size:16px}
.kt-swb-btn-add-prog:hover{opacity:.9}
.kt-swb-icon-btn{padding:8px;background:transparent;border:none;border-radius:4px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.kt-swb-icon-btn:hover{background:#e6e8ea}
.kt-swb-icon-btn .material-symbols-outlined{font-size:24px;display:block}
.kt-swb-tree-body{padding:24px}
/* program row */
.kt-swb-prog-wrap{margin-bottom:24px}
.kt-swb-prog-row{display:flex;align-items:center;gap:16px;border:1px solid #c6c6cd;background:#fff;padding:16px;border-radius:4px;box-shadow:0 1px 2px rgba(0,0,0,.05);transition:border-color .15s;margin-bottom:4px}
.kt-swb-prog-row:hover{border-color:#000}
.kt-swb-prog-icon{width:40px;height:40px;background:#d5e3fd;display:flex;align-items:center;justify-content:center;border-radius:4px;flex-shrink:0}
.kt-swb-prog-icon .material-symbols-outlined{color:#0d1c2f;font-size:24px}
.kt-swb-prog-body{flex:1;min-width:0}
.kt-swb-prog-title-row,.kt-swb-obj-title-row{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.kt-swb-node-code{font-size:11px;font-weight:700;color:#45464d;line-height:14px}
.kt-swb-prog-name{font-size:16px;line-height:24px;font-weight:700;color:#000}
.kt-swb-prog-meta,.kt-swb-obj-meta{display:flex;align-items:center;gap:24px;margin-top:4px}
.kt-swb-pbar-wrap{display:flex;align-items:center;gap:8px}
.kt-swb-pbar-wrap--prog{width:192px}
.kt-swb-pbar-wrap--obj{width:128px}
.kt-swb-pbar-track{flex:1;background:#f2f4f6;border-radius:9999px;overflow:hidden}
.kt-swb-pbar-track--prog{height:6px}
.kt-swb-pbar-track--obj{height:4px}
.kt-swb-pbar-fill{height:100%;background:#000;border-radius:9999px}
.kt-swb-pbar-fill--amber{background:#f59e0b}
.kt-swb-pbar-pct{font-size:11px;font-weight:700;color:#191c1e}
.kt-swb-meta-txt{font-size:11px;font-weight:500;color:#45464d;line-height:14px}
.kt-swb-row-actions{display:flex;align-items:center;gap:8px}
/* expand button */
.kt-swb-expand{padding:4px;background:transparent;border:none;border-radius:4px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.kt-swb-expand:hover{background:#f2f4f6}
.kt-swb-expand .material-symbols-outlined{font-size:24px;display:block}
/* secondary action buttons in rows */
.kt-swb-btn-sm{padding:4px 16px;border:1px solid #76777d;color:#000;font-size:11px;font-weight:700;border-radius:4px;background:transparent;cursor:pointer;display:flex;align-items:center;gap:4px;font-family:inherit;line-height:14px}
.kt-swb-btn-sm:hover{background:#f2f4f6}
.kt-swb-btn-sm .material-symbols-outlined{font-size:16px}
.kt-swb-btn-xs{padding:4px 8px;border:1px solid #76777d;color:#000;font-size:11px;font-weight:700;border-radius:4px;background:transparent;cursor:pointer;display:flex;align-items:center;gap:4px;font-family:inherit;line-height:14px}
.kt-swb-btn-xs:hover{background:#f2f4f6}
.kt-swb-btn-xs .material-symbols-outlined{font-size:14px}
.kt-swb-btn-more{padding:8px;background:transparent;border:none;cursor:pointer;color:#45464d;display:flex;align-items:center;justify-content:center}
.kt-swb-btn-more:hover{color:#000}
.kt-swb-btn-more .material-symbols-outlined{font-size:24px;display:block}
/* status pills */
.kt-swb-pill{font-size:10px;font-weight:700;text-transform:uppercase;padding:2px 8px;border-radius:9999px;line-height:14px;white-space:nowrap}
.kt-swb-pill--green{background:#dcfce7;color:#166534}
.kt-swb-pill--amber{background:#fef3c7;color:#92400e}
.kt-swb-pill--blue{background:#dbeafe;color:#1e40af}
/* tree connectors + objective indent */
.kt-swb-children{margin-left:32px;position:relative}
.kt-swb-tree-v{position:absolute;left:15px;top:0;bottom:0;width:1px;background:#e2e8f0}
.kt-swb-branch{position:relative;padding:8px 0}
.kt-swb-tree-h{position:absolute;left:15px;top:24px;width:16px;height:1px;background:#e2e8f0}
.kt-swb-obj-row{display:flex;align-items:center;gap:16px;margin-left:24px;border:1px solid #c6c6cd;background:#fff;padding:8px;border-radius:4px;transition:background .15s;margin-bottom:4px}
.kt-swb-obj-row:hover{background:#f7f9fb}
.kt-swb-obj-body{flex:1;min-width:0}
.kt-swb-obj-name{font-size:14px;line-height:20px;font-weight:700;color:#000}
.kt-swb-obj-fill{height:100%;border-radius:9999px}
.kt-swb-obj-fill--amber{background:#f59e0b}
.kt-swb-obj-fill--green{background:#22c55e}
/* target indent */
.kt-swb-targets{margin-left:32px;position:relative}
.kt-swb-tgt-branch{position:relative;padding:4px 0}
.kt-swb-tgt-row{display:flex;align-items:flex-start;gap:12px;margin-left:24px;background:#f2f4f6;padding:12px 16px;border-radius:8px;border-left:4px solid #000;margin-bottom:4px;cursor:pointer;transition:background .12s}
.kt-swb-tgt-row:hover{background:#e8edf4}
.kt-swb-tgt-body{flex:1;min-width:0}
.kt-swb-tgt-head{display:flex;justify-content:space-between;margin-bottom:2px}
.kt-swb-tgt-code{font-size:11px;font-weight:700;color:#45464d;line-height:14px}
.kt-swb-tgt-due{font-size:11px;font-weight:500;color:#45464d;line-height:14px}
.kt-swb-tgt-title{font-size:14px;line-height:20px;font-weight:500;color:#000;margin-bottom:8px}
.kt-swb-tgt-progress{display:flex;align-items:center;justify-content:space-between}
.kt-swb-tgt-track{width:66.66%;height:6px;background:#e6e8ea;border-radius:9999px;overflow:hidden}
.kt-swb-tgt-fill{height:100%;background:#000;border-radius:9999px}
.kt-swb-tgt-count{font-size:11px;font-weight:900;color:#000}
.kt-swb-btn-edit{padding:6px;background:transparent;border:none;cursor:pointer;border-radius:4px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.kt-swb-btn-edit:hover{background:#d4dce8}
.kt-swb-btn-edit .material-symbols-outlined{font-size:20px;display:block;color:#45464d}
/* add program dashed btn */
.kt-swb-add-prog{margin-top:24px;width:100%;padding:16px;border:2px dashed #c6c6cd;border-radius:8px;color:#45464d;background:transparent;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;font-weight:700;font-size:12px;letter-spacing:.05em;font-family:inherit;transition:all .15s}
.kt-swb-add-prog:hover{color:#000;border-color:#000;background:#fff}
.kt-swb-add-prog .material-symbols-outlined{font-size:24px}
/* selected node */
.kt-swb-prog-row.kt-swb-selected{border-color:#000!important;background:#f0f4ff!important}
.kt-swb-obj-row.kt-swb-selected{border-color:#000!important;background:#f0f4ff!important}
.kt-swb-tgt-row.kt-swb-selected{background:#e8edf4!important;border-left-color:#5e64ff!important}
/* hover on interactive rows */
.kt-swb-prog-row{cursor:pointer}.kt-swb-obj-row{cursor:pointer}
/* inline add row */
.kt-swb-add-row{opacity:.7;transition:opacity .12s}
.kt-swb-add-row:hover{opacity:1}
/* empty tree */
.kt-swb-empty-tree{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:48px 24px;text-align:center;color:#45464d}
/* bottom grid */
.kt-swb-bottom{display:grid;grid-template-columns:repeat(12,1fr);gap:24px}
.kt-swb-activity-col{grid-column:span 8}
.kt-swb-side-col{grid-column:span 4;display:flex;flex-direction:column;gap:24px}
/* activity feed */
.kt-swb-feed{background:#fff;border:1px solid #c6c6cd;border-radius:4px;padding:24px}
.kt-swb-feed h3{font-size:12px;font-weight:700;letter-spacing:.05em;color:#000;text-transform:uppercase;margin-bottom:24px}
.kt-swb-feed-list{display:flex;flex-direction:column;gap:24px}
.kt-swb-feed-item{display:flex;gap:16px}
.kt-swb-feed-icon-wrap{position:relative;flex-shrink:0}
.kt-swb-feed-icon{width:32px;height:32px;border-radius:9999px;background:#e6e8ea;display:flex;align-items:center;justify-content:center}
.kt-swb-feed-icon .material-symbols-outlined{font-size:18px;color:#000}
.kt-swb-feed-icon.is-err .material-symbols-outlined{color:#ba1a1a}
.kt-swb-feed-line{position:absolute;top:32px;left:16px;width:1px;height:100%;background:#c6c6cd}
.kt-swb-feed-copy p{font-size:14px;line-height:20px;color:#000}
.kt-swb-feed-copy small{font-size:11px;font-weight:500;line-height:14px;color:#45464d;display:block;margin-top:2px}
.kt-swb-feed-copy strong{font-weight:700}
.kt-swb-feed-copy .ref{color:#515f74;font-weight:700}
.kt-swb-feed-copy .err{color:#ba1a1a;font-weight:700}
/* feed header row */
.kt-swb-feed-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.kt-swb-feed-hdr h3{margin-bottom:0}
.kt-swb-feed-refresh{background:transparent;border:none;cursor:pointer;color:#45464d;display:flex;align-items:center;padding:4px;border-radius:4px}
.kt-swb-feed-refresh:hover{background:#f2f4f6;color:#000}
.kt-swb-feed-refresh .material-symbols-outlined{font-size:18px}
/* loading state */
.kt-swb-feed-loading{display:flex;align-items:center;gap:8px;padding:24px 0;color:#45464d;font-size:13px}
.kt-swb-feed-empty{padding:24px 0;color:#45464d;font-size:13px;font-style:italic}
@keyframes kt-spin{to{transform:rotate(360deg)}}
/* insights card */
.kt-swb-insights{background:#000;color:#fff;padding:24px;border-radius:4px;position:relative}
.kt-swb-insights h4{font-size:20px;line-height:28px;font-weight:700;margin-bottom:16px;color:#fff}
.kt-swb-insights p{font-size:14px;line-height:20px;opacity:.9;margin-bottom:24px;color:#fff}
.kt-swb-btn-light{width:100%;padding:8px;background:#fff;color:#000;border:none;border-radius:4px;font-weight:700;font-size:12px;letter-spacing:.05em;cursor:pointer;font-family:inherit}
.kt-swb-btn-light:disabled{opacity:.5;cursor:not-allowed}
/* placeholder badge */
.kt-swb-placeholder-badge{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:9999px;background:rgba(255,255,255,.15);color:rgba(255,255,255,.9);border:1px solid rgba(255,255,255,.3);margin-bottom:12px}
.kt-swb-placeholder-badge--dark{background:#f2f4f6;color:#45464d;border-color:#c6c6cd}
/* stakeholders card */
.kt-swb-stk{background:#fff;border:1px solid #c6c6cd;border-radius:4px;padding:24px;margin-top:16px}
.kt-swb-stk-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.kt-swb-stk-hdr h3{margin-bottom:0}
.kt-swb-avatars{display:flex;margin-bottom:12px}
.kt-swb-avatar{width:40px;height:40px;border-radius:9999px;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;margin-left:-8px;flex-shrink:0}
.kt-swb-avatar:first-child{margin-left:0}
.kt-swb-av-1{background:#cbd5e1;color:#334155}
.kt-swb-av-2{background:#94a3b8;color:#fff}
.kt-swb-av-3{background:#64748b;color:#fff}
.kt-swb-av-4{background:#d5e3fd;color:#57657b}
.kt-swb-stk-note{font-size:12px;color:#45464d;margin:0}
.kt-swb-btn-link{background:transparent;border:none;color:#000;font-weight:700;font-size:12px;letter-spacing:.05em;cursor:pointer;display:flex;align-items:center;gap:4px;font-family:inherit;padding:0}
.kt-swb-btn-link:hover{text-decoration:underline}
.kt-swb-btn-link .material-symbols-outlined{font-size:18px}
</style>
<!-- ── Sticky topbar (identical to Strategy Management landing) ── -->
<header class="kt-sph-topbar" data-testid="swb-topbar" style="border-radius:0">
  <div class="kt-sph-topbar__left">
    <h2 class="kt-sph-topbar__title">Strategic Alignment</h2>
  </div>
  <div class="kt-sph-topbar__right">
    <button type="button" class="kt-sph-icon-btn" title="Notifications"><span class="material-symbols-outlined">notifications</span></button>
    <button type="button" class="kt-sph-icon-btn" title="Recent"><span class="material-symbols-outlined">history</span></button>
    <div class="kt-sph-avatar"></div>
  </div>
</header>
<div class="kt-swb" data-testid="strategy-workbench-v2" style="padding:32px 32px 48px">

  <!-- Breadcrumb + Header -->
  <div style="margin-bottom:24px">
    <div class="kt-swb-crumb">
      <a href="#" data-swb="back-link">
        <span class="material-symbols-outlined">arrow_back</span>
        <span style="font-weight:500">Back to Strategy Hub</span>
      </a>
      <span class="kt-swb-crumb-sep">|</span>
      <span data-swb="crumb-entity">All Strategic Plans</span>
      <span class="material-symbols-outlined" style="font-size:14px">chevron_right</span>
      <span class="kt-swb-crumb-current" data-swb="crumb-plan">Loading…</span>
    </div>
    <div class="kt-swb-page-hdr">
      <div>
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:4px">
          <h2 class="kt-swb-page-title" data-swb="page-title" style="margin-bottom:0">Loading…</h2>
          <span class="kt-swb-pill kt-swb-pill--blue" data-swb="status-chip" data-testid="strategy-plan-status">Draft</span>
        </div>
        <p class="kt-swb-page-sub" data-swb="page-sub"></p>
      </div>
      <div class="kt-swb-hdr-actions">
        <button type="button" class="kt-swb-btn-outline">Export Report</button>
        <span data-swb="workflow-actions" data-testid="swb-workflow-actions" style="display:inline-flex;gap:8px;align-items:center"></span>
        <button type="button" class="kt-swb-btn-primary" data-swb="edit-plan-btn">Edit Plan</button>
      </div>
    </div>
  </div>

  <!-- KPI Bento -->
  <div class="kt-swb-kpis">
    <div class="kt-swb-kpi">
      <div class="kt-swb-kpi-head">
        <span class="kt-swb-kpi-label">Overall Completion</span>
        <span class="material-symbols-outlined kt-swb-icon-def">trending_up</span>
      </div>
      <div class="kt-swb-kpi-val" data-swb="kpi-completion-val">—</div>
      <div class="kt-swb-kpi-bar"><div class="kt-swb-kpi-bar-fill" data-swb="kpi-completion-bar" style="width:0%"></div></div>
      <div class="kt-swb-kpi-sub" data-swb="kpi-completion-sub" style="margin-top:6px">
        <span class="material-symbols-outlined">data_thresholding</span>
        <span>Loading…</span>
      </div>
    </div>
    <div class="kt-swb-kpi">
      <div class="kt-swb-kpi-head">
        <span class="kt-swb-kpi-label">Programs</span>
        <span class="material-symbols-outlined kt-swb-icon-sec">layers</span>
      </div>
      <div class="kt-swb-kpi-val" data-swb="kpi-programs-val">—</div>
      <div class="kt-swb-kpi-sub" data-swb="kpi-programs-sub">
        <span class="material-symbols-outlined">hub</span>
        <span>Loading…</span>
      </div>
    </div>
    <div class="kt-swb-kpi">
      <div class="kt-swb-kpi-head">
        <span class="kt-swb-kpi-label">Indicators</span>
        <span class="material-symbols-outlined kt-swb-icon-sec">track_changes</span>
      </div>
      <div class="kt-swb-kpi-val" data-swb="kpi-indicators-val">—</div>
      <div class="kt-swb-kpi-sub" data-swb="kpi-indicators-sub">
        <span class="material-symbols-outlined">flag</span>
        <span>Loading…</span>
      </div>
    </div>
    <div class="kt-swb-kpi kt-swb-kpi--milestone">
      <div class="kt-swb-kpi-bg"></div>
      <div class="kt-swb-kpi-inner">
        <div class="kt-swb-kpi-head">
          <span class="kt-swb-kpi-label">Next Milestone</span>
          <span class="material-symbols-outlined kt-swb-icon-def">calendar_today</span>
        </div>
        <div class="kt-swb-kpi-date" data-swb="kpi-milestone-date">—</div>
        <p class="kt-swb-kpi-note" data-swb="kpi-milestone-note">Loading…</p>
      </div>
    </div>
  </div>

  <!-- Readiness bar -->
  <div data-swb="readiness-bar" data-testid="swb-readiness-bar" style="margin-bottom:16px"></div>

  <!-- Hierarchy Workbench -->
  <div class="kt-swb-hier">
    <div class="kt-swb-hier-hdr">
      <div class="kt-swb-hier-legend">
        <h3 class="kt-swb-hier-title">Strategic Hierarchy</h3>
        <div class="kt-swb-legend-items">
          <span class="kt-swb-dot kt-swb-dot-green"></span>
          <span class="kt-swb-legend-lbl">On Track</span>
          <span class="kt-swb-dot kt-swb-dot-amber"></span>
          <span class="kt-swb-legend-lbl">At Risk</span>
        </div>
      </div>
      <div class="kt-swb-hier-ctrl">
        <div class="kt-swb-search-wrap">
          <span class="material-symbols-outlined">search</span>
          <input type="text" placeholder="Search strategy tree..." data-testid="swb-tree-search">
        </div>
        <button type="button" class="kt-swb-btn-add-prog" data-testid="swb-add-program-btn">
          <span class="material-symbols-outlined">add</span> Program
        </button>
        <button type="button" class="kt-swb-icon-btn" title="Expand / Collapse All" data-testid="swb-expand-all-btn" data-expanded="false">
          <span class="material-symbols-outlined">unfold_more</span>
        </button>
        <button type="button" class="kt-swb-icon-btn" title="Filter Tree">
          <span class="material-symbols-outlined">filter_list</span>
        </button>
      </div>
    </div>
    <div class="kt-swb-tree-body" data-testid="swb-tree-body" style="padding:24px">
      <div style="color:#57657b;font-size:13px">Loading hierarchy…</div>
    </div>
  </div>

  <!-- Bottom: Activity + Side -->
  <div class="kt-swb-bottom">
    <div class="kt-swb-activity-col">
      <div class="kt-swb-feed" data-testid="swb-activity-feed">
        <div class="kt-swb-feed-hdr">
          <h3>Recent Activity</h3>
          <button type="button" class="kt-swb-feed-refresh" data-testid="swb-activity-refresh" title="Refresh">
            <span class="material-symbols-outlined">refresh</span>
          </button>
        </div>
        <div class="kt-swb-feed-list" data-testid="swb-activity-list">
          <div class="kt-swb-feed-loading" data-testid="swb-activity-loading">
            <span class="material-symbols-outlined" style="font-size:18px;opacity:.4;animation:kt-spin 1s linear infinite">progress_activity</span>
            <span>Loading activity&hellip;</span>
          </div>
        </div>
      </div>
    </div>
    <div class="kt-swb-side-col">
      <div class="kt-swb-insights" data-testid="swb-insights-card">
        <div class="kt-swb-placeholder-badge">Coming Soon</div>
        <h4>Insights Engine</h4>
        <p>AI-powered analysis of plan health, budget risk, and delivery trends will appear here.</p>
        <button type="button" class="kt-swb-btn-light" disabled>View Recommendations</button>
      </div>
      <div class="kt-swb-stk" data-testid="swb-stakeholders-card">
        <div class="kt-swb-stk-hdr">
          <h3>Stakeholders</h3>
          <span class="kt-swb-placeholder-badge kt-swb-placeholder-badge--dark">Coming Soon</span>
        </div>
        <div class="kt-swb-avatars">
          <div class="kt-swb-avatar kt-swb-av-1" title="Plan Owner">—</div>
        </div>
        <p class="kt-swb-stk-note">Stakeholder management will be available in the next release.</p>
      </div>
    </div>
  </div>

</div>
`;
	}

	/* ── Portfolio Hub shell — Stitch: docs/misc/strategy_management_home_code.html ── */
	function portfolioHubShellHtml() {
		const initial = userInitial();
		return `
			<div class="kt-sph-shell" data-testid="strategy-portfolio-hub">
				<header class="kt-sph-topbar" data-testid="sph-topbar">
					<div class="kt-sph-topbar__left">
						<h2 class="kt-sph-topbar__title">Strategic Alignment</h2>
						<div class="kt-sph-search-wrap">
							<span class="material-symbols-outlined kt-sph-search-icon">search</span>
							<input class="kt-sph-search" placeholder="Search strategies..." type="text" data-testid="sph-search-input">
						</div>
					</div>
					<div class="kt-sph-topbar__right">
						<button type="button" class="kt-sph-icon-btn" aria-label="Notifications"><span class="material-symbols-outlined">notifications</span></button>
						<button type="button" class="kt-sph-icon-btn" aria-label="History"><span class="material-symbols-outlined">history</span></button>
						<div class="kt-sph-avatar" data-testid="sph-user-avatar">${initial}</div>
					</div>
				</header>

				<div class="kt-sph-body">
					<div class="kt-sph-canvas" data-testid="sph-canvas">
						<main class="kt-sph-main" data-testid="sph-main">
							<div class="kt-sph-page-header">
								<div>
									<nav class="kt-sph-breadcrumb" data-testid="sph-breadcrumb">
										<span>Portfolio</span>
										<span class="material-symbols-outlined">chevron_right</span>
										<span class="kt-sph-breadcrumb__active">Active Plans</span>
									</nav>
									<h1 class="kt-sph-page-title" data-testid="sph-page-title">Strategy Management</h1>
								</div>
								<div class="kt-sph-page-actions">
									<button type="button" class="kt-sph-btn kt-sph-btn--outline">Export Portfolio</button>
									<button type="button" class="kt-sph-btn kt-sph-btn--primary" data-testid="sph-create-plan-btn">
										<span class="material-symbols-outlined">add</span> Create New Plan
									</button>
								</div>
							</div>

							<div class="kt-sph-metrics" data-testid="sph-metrics-grid" data-sph-metrics>
								${skeletonKpiHtml()}
							</div>

							<div class="kt-sph-plans-grid" data-testid="sph-plans-grid" data-sph-plans>
								${skeletonCardsHtml()}
							</div>
						</main>

						<aside class="kt-sph-aside" data-testid="sph-aside">
							<div class="kt-sph-aside__hdr">
								<h3 class="kt-sph-aside__title" data-testid="sph-activity-heading">Lineage Activity</h3>
							</div>
							<div class="kt-sph-timeline" data-testid="sph-activity-table" data-sph-activity-body>
								<div class="kt-sph-tl-loading">Loading activity…</div>
							</div>
						</aside>
					</div>
				</div>
			</div>
		`;
	}

	function skeletonKpiHtml() {
		return [
			{ label: "Total Budget", value: "—", sub: "Loading…", subClass: "", mono: true },
			{ label: "Active Programs", value: "—", sub: "Loading…", subClass: "", mono: false },
			{ label: "Success Rate", value: "—", sub: "Loading…", subClass: "", mono: false },
			{ label: "Draft Plans", value: "—", sub: "Loading…", subClass: "kt-sph-metric-sub--warn", mono: false },
		]
			.map(
				(k) => `
			<div class="kt-sph-metric-card">
				<p class="kt-sph-metric-label">${k.label}</p>
				<div>
					<div class="kt-sph-metric-value${k.mono ? " kt-sph-metric-value--mono" : ""}">${k.value}</div>
					${k.sub ? `<p class="kt-sph-metric-sub ${k.subClass}">${k.sub}</p>` : ""}
				</div>
			</div>`
			)
			.join("");
	}

	function skeletonCardsHtml() {
		return `<div class="kt-sph-skeleton-row">Loading plans…</div>`;
	}

	/* ── Status helpers ── */
	function chipClass(status) {
		const map = {
			Active: "kt-sph-chip--active",
			Draft: "kt-sph-chip--draft",
			Submitted: "kt-sph-chip--submitted",
			Approved: "kt-sph-chip--approved",
			Archived: "kt-sph-chip--archived",
		};
		return map[status] || "kt-sph-chip--draft";
	}

	function prettyTime(isoStr) {
		if (!isoStr) return "";
		try {
			if (typeof frappe !== "undefined" && frappe.datetime && frappe.datetime.prettyDate) {
				return frappe.datetime.prettyDate(isoStr);
			}
			const d = new Date(isoStr.replace(" ", "T"));
			const diff = Date.now() - d.getTime();
			const mins = Math.floor(diff / 60000);
			if (mins < 2) return "just now";
			if (mins < 60) return `${mins}m ago`;
			const hrs = Math.floor(mins / 60);
			if (hrs < 24) return `${hrs}h ago`;
			const days = Math.floor(hrs / 24);
			if (days === 1) return "Yesterday";
			return `${days} days ago`;
		} catch (_) {
			return isoStr;
		}
	}

	function fmtBudget(val) {
		if (!val || val === 0) return "—";
		if (val >= 1e9) return (val / 1e9).toFixed(1) + "B";
		if (val >= 1e6) return (val / 1e6).toFixed(1) + "M";
		if (val >= 1e3) return (val / 1e3).toFixed(1) + "K";
		return String(Math.round(val));
	}

	/* ── Plan card HTML builder ── */
	function planCardHtml(plan) {
		const title = plan.strategic_plan_name || plan.name;
		const status = plan.status || "Draft";
		const fyLabel = plan.start_year && plan.end_year ? `FY ${plan.start_year} – ${plan.end_year}` : "";
		const programs = plan.program_count != null ? plan.program_count : "—";
		const objectives = plan.objective_count != null ? plan.objective_count : "—";
		const budget = plan.total_budget != null ? plan.total_budget : 0;
		const isDraft = status === "Draft" || status === "Submitted";
		const modifiedStr = prettyTime(plan.modified);

		const footer = isDraft
			? `<div class="kt-sph-draft-hint">
					<span class="material-symbols-outlined kt-sph-draft-hint__icon">edit_square</span>
					<span class="kt-sph-draft-hint__text">Last edited ${modifiedStr}</span>
				</div>
				<a href="#" class="kt-sph-card-cta" data-testid="sph-plan-cta" data-plan="${encodeURIComponent(plan.name)}" aria-label="Continue setup for ${title}">Continue Setup <span class="material-symbols-outlined">arrow_forward</span></a>`
			: `<div class="kt-sph-avatar-stack">
					<span class="kt-sph-avatar kt-sph-avatar--slate-300"></span>
					<span class="kt-sph-avatar kt-sph-avatar--slate-400"></span>
				</div>
				<a href="#" class="kt-sph-card-cta" data-testid="sph-plan-cta" data-plan="${encodeURIComponent(plan.name)}" aria-label="View workbench for ${title}">View Workbench <span class="material-symbols-outlined">arrow_forward</span></a>`;

		return `
			<div class="kt-sph-plan-card" data-testid="sph-plan-card" data-plan-name="${encodeURIComponent(plan.name)}">
				<div class="kt-sph-card-main">
					<div class="kt-sph-card-header">
						<div class="kt-sph-card-header__row">
							<span class="kt-sph-chip ${chipClass(status)}">${status}</span>
							${fyLabel ? `<span class="kt-sph-fiscal-year">${fyLabel}</span>` : ""}
						</div>
						<button type="button" class="kt-sph-icon-btn" aria-label="More actions"><span class="material-symbols-outlined">more_vert</span></button>
					</div>
					<h3 class="kt-sph-card-title">${title}</h3>
					<div class="kt-sph-card-body">
						<div class="kt-sph-stat">
							<p class="kt-sph-stat-label">Budget</p>
							<p class="kt-sph-stat-value kt-sph-stat-value--mono">${fmtBudget(budget)}</p>
						</div>
						<div class="kt-sph-stat">
							<p class="kt-sph-stat-label">Programs</p>
							<p class="kt-sph-stat-value">${programs}</p>
						</div>
						<div class="kt-sph-stat">
							<p class="kt-sph-stat-label">Objectives</p>
							<p class="kt-sph-stat-value">${objectives}</p>
						</div>
					</div>
				</div>
				<div class="kt-sph-card-footer${isDraft ? " kt-sph-card-footer--draft" : ""}">
					${footer}
				</div>
			</div>`;
	}

	function emptyStateCardHtml() {
		/* Shown only when the plan grid is empty (no plans / no search matches). */
		return `
			<div class="kt-sph-plan-card kt-sph-plan-card--empty" data-testid="sph-create-new-card">
				<div class="kt-sph-empty-icon-wrap">
					<span class="material-symbols-outlined">add</span>
				</div>
				<h4 class="kt-sph-empty-title">Create New Strategy</h4>
				<p class="kt-sph-empty-text">Define a new planning horizon and budget lineage.</p>
			</div>`;
	}

	/* ── DOM patch helpers ── */
	function applyPortfolioData(shell, payload) {
		const portfolio = payload.portfolio || {};
		const plans = Array.isArray(payload.plans) ? payload.plans : [];

		/* KPI cards */
		const metricsEl = shell.querySelector("[data-sph-metrics]");
		if (metricsEl) {
			const activeCount = portfolio.active_count || 0;
			const draftCount = portfolio.draft_count || 0;
			const totalPlans = portfolio.total_plans || 0;
			const totalPrograms = portfolio.total_programs || 0;
			const totalBudget = portfolio.total_budget || 0;
			const successRate = portfolio.success_rate || 0;
			const dataCoverage = portfolio.data_coverage || 0;
			const successSub = successRate
				? `Weighted achievement${dataCoverage ? `. Data coverage: ${dataCoverage}%` : ""}`
				: "No KPI targets with actuals yet";
			metricsEl.innerHTML = `
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Total Budget</p>
					<div>
						<div class="kt-sph-metric-value kt-sph-metric-value--mono">${fmtBudget(totalBudget)}</div>
						<p class="kt-sph-metric-sub">${totalBudget ? "Sum of linked demands" : "No linked demands yet"}</p>
					</div>
				</div>
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Active Programs</p>
					<div>
						<div class="kt-sph-metric-value">${totalPrograms}</div>
						<p class="kt-sph-metric-sub">Across ${activeCount} Active Plan${activeCount !== 1 ? "s" : ""}</p>
					</div>
				</div>
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Success Rate</p>
					<div>
						<div class="kt-sph-metric-value">${successRate ? successRate + "%" : "—"}</div>
						<p class="kt-sph-metric-sub">${successSub}</p>
					</div>
				</div>
				<div class="kt-sph-metric-card">
					<p class="kt-sph-metric-label">Draft Plans</p>
					<div>
						<div class="kt-sph-metric-value">${draftCount}</div>
						<p class="kt-sph-metric-sub kt-sph-metric-sub--warn">${draftCount > 0 ? "Awaiting Review" : `${totalPlans} plan${totalPlans !== 1 ? "s" : ""} total`}</p>
					</div>
				</div>`;
		}

		/* Plan cards — Stitch shows plan cards only; empty card when none */
		const plansEl = shell.querySelector("[data-sph-plans]");
		if (plansEl) {
			if (plans.length === 0) {
				plansEl.innerHTML = emptyStateCardHtml();
			} else {
				plansEl.innerHTML = plans.map((p) => planCardHtml(p)).join("");
			}
		}

		/* Activity rail — populated by parallel loadPortfolioActivity call */
		const activityBody = shell.querySelector("[data-sph-activity-body]");
		if (activityBody) {
			activityBody.innerHTML = `<div class="kt-sph-tl-loading">Loading activity…</div>`;
		}

		/* Client-side search */
		wireSearch(shell, plans);
	}

	function wireSearch(shell, allPlans) {
		const input = shell.querySelector("[data-testid='sph-search-input']");
		const grid = shell.querySelector("[data-sph-plans]");
		if (!input || !grid) return;
		input.addEventListener("input", function () {
			const term = (this.value || "").toLowerCase().trim();
			const matched = term
				? allPlans.filter(function (p) {
						const title = (p.strategic_plan_name || p.name || "").toLowerCase();
						const status = (p.status || "").toLowerCase();
						const fy =
							p.start_year && p.end_year ? `${p.start_year} ${p.end_year}` : "";
						return title.includes(term) || status.includes(term) || fy.includes(term);
				  })
				: allPlans;
			if (matched.length === 0) {
				grid.innerHTML = emptyStateCardHtml();
			} else {
				grid.innerHTML = matched.map(planCardHtml).join("");
			}
		});
	}

	/* ── API call ── */
	function loadPortfolioHub(shell) {
		if (typeof frappe === "undefined" || typeof frappe.call !== "function") return;
		frappe.call({
			method: "kentender_strategy.api.landing.get_strategy_landing_data",
			callback: function (r) {
				if (r && r.message) {
					applyPortfolioData(shell, r.message);
				}
			},
			error: function () {
				const plansEl = shell.querySelector("[data-sph-plans]");
				if (plansEl) {
					plansEl.innerHTML =
						`<div class="kt-sph-error-row">Could not load plans. Please refresh.</div>` +
						emptyStateCardHtml();
				}
			},
		});
	}

	/* ── Activity helpers (right-rail timeline) ── */
	function activityItemHtml(item, isLast) {
		const dot = item.dot_class || "slate";
		const label = item.action || "Updated";
		const plan = item.plan_name || "—";
		const user = item.user || "—";
		const time = prettyTime(item.time);
		return `<div class="kt-sph-tl-item" data-testid="sph-activity-item">
			<div class="kt-sph-tl-rail">
				<span class="kt-sph-dot kt-sph-dot--${dot}"></span>
				${isLast ? "" : '<span class="kt-sph-tl-line"></span>'}
			</div>
			<div class="kt-sph-tl-body">
				<div class="kt-sph-tl-action kt-sph-action-label">${label}</div>
				<div class="kt-sph-tl-plan">${plan}</div>
				<div class="kt-sph-tl-meta">
					<span>${time}</span>
					<span aria-hidden="true">•</span>
					<span>${user}</span>
				</div>
			</div>
		</div>`;
	}

	function loadPortfolioActivity(shell) {
		if (typeof frappe === "undefined" || typeof frappe.call !== "function") return;
		frappe.call({
			method: "kentender_strategy.api.landing.get_portfolio_activity",
			args: { limit: 20 },
			callback: function (r) {
				const activityBody = shell.querySelector("[data-sph-activity-body]");
				if (!activityBody) return;
				const rows = Array.isArray(r && r.message) ? r.message : [];
				if (rows.length === 0) {
					activityBody.innerHTML = `<div class="kt-sph-tl-empty">No activity recorded yet.</div>`;
					return;
				}
				activityBody.innerHTML = rows
					.map(function (item, idx) {
						return activityItemHtml(item, idx === rows.length - 1);
					})
					.join("");
			},
			error: function () {
				const activityBody = shell.querySelector("[data-sph-activity-body]");
				if (activityBody) {
					activityBody.innerHTML = `<div class="kt-sph-tl-empty">Could not load activity.</div>`;
				}
			},
		});
	}

	function renderShell() {
		if (!isStrategyWorkspaceRoute()) {
			document.body.classList.remove("kt-strategy-shell");
			document.querySelectorAll(".kt-strategy-injected-shell").forEach((el) => el.remove());
			return;
		}
		ensureFonts();
		document.body.classList.add("kt-strategy-shell");
		const mount = resolveMount();
		if (!mount) return;
		let shell = mount.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]');
		if (!shell) {
			shell = document.createElement("div");
			shell.className = "kt-strategy-injected-shell";
			shell.setAttribute("data-testid", "strategy-landing-page");
			const ed = document.getElementById("editorjs");
			if (ed && mount.contains(ed)) {
				mount.insertBefore(shell, ed);
				ed.style.display = "none";
			} else {
				mount.insertBefore(shell, mount.firstChild);
			}
		}
		if (shell.getAttribute("data-kt-rendered") === "1") return;
		shell.innerHTML = portfolioHubShellHtml();
		shell.setAttribute("data-kt-rendered", "1");
		loadPortfolioHub(shell);
		loadPortfolioActivity(shell);
	}

	function openPlanWorkbench(planName) {
		if (!planName) return;
		if (typeof frappe !== "undefined" && typeof frappe.set_route === "function") {
			frappe.set_route("strategy-builder", planName);
		}
	}

	function bindEvents() {
		if (bound) return;
		bound = true;
		document.addEventListener("click", function (ev) {
			const t = ev.target;
			if (!(t && t.closest)) return;

			/* Create New Plan button */
			if (t.closest('[data-testid="sph-create-plan-btn"]') || t.closest('[data-testid="sph-create-new-card"]')) {
				if (typeof frappe !== "undefined" && typeof frappe.new_doc === "function") {
					frappe.new_doc("Strategic Plan");
				}
				return;
			}

			/* Plan card CTA (View Workbench / Continue Setup) */
			const ctaEl = t.closest('[data-testid="sph-plan-cta"]');
			if (ctaEl) {
				ev.preventDefault();
				const planName = decodeURIComponent(ctaEl.getAttribute("data-plan") || "");
				openPlanWorkbench(planName);
				return;
			}

			/* Clicking anywhere on the plan card body (not the ⋮ menu) navigates to the workbench */
			const cardEl = t.closest('[data-testid="sph-plan-card"]');
			if (cardEl && !t.closest(".kt-sph-icon-btn")) {
				ev.preventDefault();
				const planName = decodeURIComponent(cardEl.getAttribute("data-plan-name") || "");
				openPlanWorkbench(planName);
				return;
			}
		});
		if (window.jQuery) {
			window.jQuery(document).on("page-change app_ready", renderShell);
		}
		if (typeof frappe !== "undefined" && frappe.router && frappe.router.on) {
			frappe.router.on("change", renderShell);
		}
		if (typeof MutationObserver !== "undefined" && !observer) {
			observer = new MutationObserver(function () {
				if (!isStrategyWorkspaceRoute()) return;
				const existing = document.querySelector('.kt-strategy-injected-shell[data-testid="strategy-landing-page"]');
				if (!existing) renderShell();
			});
			observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
		}
	}

	function boot() {
		bindEvents();
		renderShell();
		setTimeout(renderShell, 200);
		setTimeout(renderShell, 800);
	}

	function waitForFrappe() {
		if (typeof window.frappe === "undefined") {
			setTimeout(waitForFrappe, 20);
			return;
		}
		boot();
		if (typeof frappe.ready === "function") frappe.ready(boot);
	}

	/* Expose the workbench HTML builder globally so the strategy-builder page can use it */
	window._ktStaticWorkbenchHtml = staticHierarchyWorkbenchHtml;

	waitForFrappe();
	window.addEventListener("load", boot);
})();
