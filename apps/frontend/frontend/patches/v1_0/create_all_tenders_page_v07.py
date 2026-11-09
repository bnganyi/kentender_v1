import frappe


def execute():
    create_all_tenders_page()


def create_all_tenders_page():
    frappe.db.sql("DELETE FROM `tabWeb Page` WHERE name = 'all-tenders' OR route = 'all-tenders'")
    frappe.db.commit()

    page = frappe.new_doc("Web Page")
    page.title = "All Tenders"
    page.route = "all-tenders"
    page.published = 1
    page.content_type = "HTML"
    page.dynamic_template = 1
    page.full_width = 1
    page.show_title = 0
    page.main_section_html = PAGE_HTML
    page.insert(ignore_permissions=True, ignore_if_duplicate=True)

    frappe.db.commit()
    frappe.clear_cache()


PAGE_HTML = r"""
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/frontend/css/public_profile_menu.css?v=1">

<style>
*, *::before, *::after { box-sizing: border-box; }
html, body { width: 100%; margin: 0 !important; padding: 0 !important; overflow-x: hidden; }
body { color: #0a1929; background: #f8fafc; font-family: 'Outfit', sans-serif; }
.navbar, nav.navbar, .navbar-light, header.navbar, .web-footer, .page-header-wrapper, .page-breadcrumbs { display: none !important; }
.navbar-blur { position: sticky; top: 0; z-index: 50; background: rgba(255,255,255,.97); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(0,102,255,.1); }
#topBar { position: relative; overflow: hidden; background: #0b1f3b; color: #fff; }
.pattern-dots { background-image: radial-gradient(circle, rgba(255,255,255,.15) 1px, transparent 1px); background-size: 30px 30px; }
#topBar-inner, #site-nav, #mobile-menu-inner { width: min(1536px, calc(100% - 32px)); margin: 0 auto; padding-right: 16px; padding-left: 16px; }
#topBar-inner { position: relative; z-index: 10; min-height: 36px; display: flex; align-items: center; gap: 16px; font: 12px 'Space Mono', monospace; }
#site-nav { min-height: 80px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
#site-logo img { display: block; width: auto; height: 48px; object-fit: contain; }
#mainNav, .kt-header-actions { display: flex; align-items: center; gap: 32px; }
#mainNav a, .dropdown-toggle { color: #374151; font-size: 15px; font-weight: 500; text-decoration: none; }
#mainNav a:hover, .dropdown-toggle:hover { color: #2563eb; }
.dropdown { position: relative; }
.dropdown-toggle { display: inline-flex; align-items: center; gap: 6px; padding: 0; border: 0; background: transparent; cursor: pointer; }
.dropdown-menu { position: absolute; top: calc(100% + 10px); left: 0; z-index: 60; min-width: 200px; padding: 8px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; box-shadow: 0 10px 25px rgba(0,0,0,.1); opacity: 0; visibility: hidden; transform: translateY(-6px); transition: .2s ease; }
.dropdown-menu.show, .dropdown:hover .dropdown-menu { opacity: 1; visibility: visible; transform: translateY(0); }
.dropdown-item { display: block; padding: 10px 12px; border-radius: 6px; color: #1f2937; text-decoration: none; }
.dropdown-item:hover { background: #f3f4f6; color: #2563eb; }
.dropdown-menu, #kt-profile-menu { background-color: #f3f4f6 !important; }
.dropdown-item:hover, .dropdown-item:focus, .dropdown-item:active { background-color: #e5e7eb; }
.dropdown-menu .dropdown-item.active { background-color: #e5e7eb !important; background-image: none !important; }
#mainNav .dropdown-menu .dropdown-item.active, #mainNav .dropdown-toggle.active, #mobileMenu a.active { color: #2563eb !important; font-weight: 700; }
select { color-scheme: light; }
select option { background-color: #f3f4f6; color: #1f2937; }
.kt-header-actions { gap: 12px; }
.kt-action-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 42px; padding: 10px 16px; border-radius: 10px; background: linear-gradient(135deg,#0047ab,#003580); color: #fff; font-size: 14px; font-weight: 600; text-decoration: none; white-space: nowrap; }
#kt-dashboard-button { border: 1px solid #e1e7ee; background: #f1f3f5; color: #000; }
#mobileMenuBtn { display: none; border: 0; background: transparent; color: #374151; font-size: 22px; }
#mobileMenu { border-top: 1px solid #e5e7eb; background: #fff; }
#mobileMenu-inner { display: grid; gap: 12px; padding: 16px 0; }
#mobileMenu[hidden] { display: none !important; }
.pattern-grid { background-image: linear-gradient(rgba(0,102,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,102,255,.05) 1px, transparent 1px); background-size: 50px 50px; }
.blob { position: absolute; border-radius: 50%; filter: blur(60px); opacity: .3; animation: float 8s ease-in-out infinite; }
.blob-1 { width: 400px; height: 400px; top: -200px; right: -200px; background: #0066ff; }
.blob-2 { width: 300px; height: 300px; bottom: -150px; left: -150px; background: #0047ab; animation-delay: -4s; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
.all-tenders-main { position: relative; min-height: 60vh; overflow: hidden; background: linear-gradient(135deg,#f9fafb,#f0fdf4); }
.page-inner { position: relative; z-index: 10; width: min(1536px, 100%); margin: 0 auto; padding: 96px 16px; }
.page-heading { margin: 0 0 24px; color: #4b5563; font-size: 30px; line-height: 1.15; font-weight: 700; }
.page-intro { max-width: 768px; margin: 0 auto 64px; color: #4b5563; font-size: 20px; line-height: 1.5; }
.filter-heading { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; padding: 16px; border-radius: 24px; background: rgba(0,0,0,.05); }
.filter-heading h2 { display: flex; align-items: center; gap: 8px; margin: 0; font-size: 18px; font-weight: 700; }
.filter-heading p { margin: 0 auto 0 0; color: #4b5563; font-size: 14px; }
.filter-heading h2 i { color: #16a34a; }
.filter-panel { margin-bottom: 24px; padding: 0; background: transparent; }
.filter-panel.collapsed { display: none; margin-bottom: 0; }
.filter-panel.expanded { margin-bottom: 24px; }
.filter-content { transition: opacity .3s ease, transform .3s ease; }
.filter-panel.collapsed .filter-content { opacity: 0; transform: translateY(-20px); pointer-events: none; }
.filter-panel.expanded .filter-content { opacity: 1; transform: translateY(0); pointer-events: all; }
.filter-toggle { display: flex; align-items: center; gap: 8px; padding: 8px 24px; border: 0; border-radius: 12px; background: linear-gradient(135deg,#0047ab,#0047ab); color: #fff; font-weight: 600; cursor: pointer; transition: all .3s ease; }
.filter-toggle:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,102,255,.3); }
.input-modern { width: 100%; padding: 14px 18px; border: 2px solid transparent; border-radius: 12px; outline: none; background: rgba(255,255,255,.95); font-size: 15px; transition: all .3s ease; }
.input-modern:focus { border-color: #0066ff; background: #fff; box-shadow: 0 0 0 4px rgba(0,102,255,.1); }
#tender-filters { display: grid; gap: 24px; }
.filter-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 16px; }
.filter-grid-dates { grid-template-columns: minmax(0,1fr); }
.filter-field label { display: block; margin-bottom: 8px; color: #374151; font-size: 14px; font-weight: 500; }
.filter-field input:disabled, .filter-field select:disabled { background: #f3f4f6; color: #6b7280; cursor: not-allowed; }
.filter-exact { display: flex; align-items: center; gap: 8px; margin-top: 12px; color: #4b5563; font-size: 14px; }
.filter-exact input { width: 16px; height: 16px; margin: 0; accent-color: #0066ff; }
.date-input-wrapper { position: relative; display: flex; align-items: center; min-height: 48px; overflow: hidden; border-radius: 12px; background: rgba(255,255,255,.95); }
.date-input-wrapper i { margin: 0 16px; color: #6b7280; }
.date-input-wrapper input { width: 100%; min-width: 0; padding: 14px 12px; border: 0; outline: 0; background: transparent; font-size: 15px; }
.date-input-wrapper input:disabled { color: #6b7280; cursor: not-allowed; }
.filter-actions { display: flex; grid-column: 1 / -1; justify-content: center; gap: 16px; padding-top: 24px; border-top: 2px solid #e5e7eb; }
.btn-primary, .btn-secondary { display: inline-flex; min-height: 42px; align-items: center; justify-content: center; gap: 8px; padding: 12px 24px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all .3s ease; }
.btn-primary { border: 0; background: linear-gradient(135deg,#0047ab,#003580); color: #fff; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0,102,255,.4); }
.btn-secondary { border: 2px solid #e5e7eb; background: #fff; color: #374151; }
.btn-secondary:hover { border-color: #0066ff; color: #0066ff; }
.tender-results-summary { margin: 0 0 16px; color: #4b5563; font-size: 14px; }
#tender-results { margin-bottom: 64px; }
.tender-card { position: relative; }
.card-hover { position: relative; overflow: hidden; transition: all .4s cubic-bezier(.4,0,.2,.5); }
.card-hover:hover { transform: translateY(-8px); box-shadow: 0 20px 30px rgba(22,95,206,.2); }
.tender-card-top { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.tender-card-title { margin: 0 0 16px; color: #1f2937; font-size: 20px; line-height: 1.35; font-weight: 700; }
.tender-card-reference { margin: 0; color: #6b7280; font: 12px 'Space Mono', monospace; }
.badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
.badge-category { background: linear-gradient(135deg,#0047ab,#0047ab); color: #fff; }
.badge-active { background: linear-gradient(135deg,#5db89a,#65c5a7); color: #fff; }
.tender-category { display: inline-block; padding: 6px 14px; border-radius: 20px; background: linear-gradient(135deg,#0047ab,#0047ab); color: #fff; font-size: 12px; font-weight: 600; text-transform: uppercase; }
.tender-published { display: inline-block; padding: 6px 14px; border-radius: 20px; background: linear-gradient(135deg,#5db89a,#65c5a7); color: #fff; font-size: 12px; font-weight: 600; }
.tender-deadline { color: #374151; font-size: 14px; font-weight: 700; text-align: right; }
.tender-card-meta { display: flex; flex-direction: column; justify-content: space-between; gap: 16px; }
.tender-card-facts { display: flex; flex-wrap: wrap; gap: 32px; }
.tender-card-fact-label { margin-bottom: 4px; color: #111827; font-size: 12px; font-weight: 700; text-transform: uppercase; }
.tender-card-fact-value { color: #1f2937; font-size: 15px; font-weight: 500; overflow-wrap: anywhere; }
.tender-card-actions { display: flex; justify-content: flex-end; }
.mono { font-family: 'Space Mono', monospace; }
.neon-glow { box-shadow: 0 0 20px rgba(0,102,255,.3), 0 0 40px rgba(0,102,255,.2); }
#scrollTop { position: fixed; right: 32px; bottom: 32px; z-index: 50; display: flex; width: 56px; height: 56px; align-items: center; justify-content: center; border: 0; border-radius: 50%; background: linear-gradient(135deg,#0066ff,#0047ab); color: #fff; cursor: pointer; opacity: 0; visibility: hidden; transition: all .3s ease; }
#scrollTop.visible { opacity: 1; visibility: visible; }
#scrollTop:hover { transform: scale(1.1); }
.tender-results-state, .tender-load-error { padding: 18px; border-radius: 8px; background: #fff; color: #475467; }
.tender-results-state { border: 1px solid #e1e7ee; }
.tender-load-error { display: flex; align-items: center; justify-content: space-between; gap: 16px; border: 1px solid #f1c7c7; background: #fff7f7; color: #8f2424; }
.tender-results-state[hidden], .tender-load-error[hidden] { display: none !important; }
#tender-detail-modal { width: min(920px, calc(100vw - 32px)); max-width: none; max-height: min(88vh, 900px); margin: auto; padding: 0; overflow: visible; border: 0; border-radius: 16px; background: transparent; color: #1f2937; }
#tender-detail-modal::backdrop { background: rgba(10,25,41,.6); backdrop-filter: blur(3px); }
.tender-modal-shell { display: flex; max-height: min(88vh, 900px); flex-direction: column; overflow: hidden; border: 1px solid #e1e7ee; border-radius: 16px; background: #fff; box-shadow: 0 24px 70px rgba(10,25,41,.28); }
.tender-modal-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding: 24px; border-bottom: 1px solid #e5e7eb; }
.tender-modal-header h2 { margin: 10px 0 8px; color: #1f2937; font-size: 24px; line-height: 1.3; }
.tender-modal-description { margin: 0; color: #4b5563; line-height: 1.5; }
.tender-modal-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
.tender-modal-actions[hidden] { display: none !important; }
.tender-modal-close { display: grid; width: 40px; height: 40px; flex: none; place-items: center; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; color: #374151; cursor: pointer; }
.tender-modal-close:hover { border-color: #2563eb; color: #2563eb; }
.tender-modal-content { display: grid; gap: 20px; overflow: auto; padding: 24px; }
.tender-modal-section { padding: 18px; border: 1px solid #e5eaf0; border-radius: 10px; background: #fff; }
.tender-modal-section h3 { margin: 0 0 14px; color: #1f2937; font-size: 17px; }
.tender-modal-facts { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 16px; }
.tender-modal-fact-label { display: block; margin-bottom: 4px; color: #667085; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.tender-modal-fact-value { color: #1f2937; font-size: 14px; overflow-wrap: anywhere; }
.tender-modal-list { display: grid; gap: 12px; margin: 0; padding: 0; list-style: none; }
.tender-modal-list-item { display: grid; gap: 6px; padding-bottom: 12px; border-bottom: 1px solid #eef0f3; }
.tender-modal-list-item:last-child { padding-bottom: 0; border-bottom: 0; }
.tender-modal-document { grid-template-columns: minmax(0,1fr) auto auto; align-items: center; gap: 16px; }
.tender-modal-list-title { color: #1f2937; font-weight: 600; }
.tender-modal-list-meta { color: #667085; font-size: 13px; }
.tender-modal-links { display: flex; flex-wrap: wrap; gap: 14px; font-size: 14px; font-weight: 600; }
.tender-modal-links a { color: #126ac2; text-decoration: none; }
.tender-modal-links a:hover { color: #0047ab; text-decoration: underline; text-underline-offset: 3px; }
.tender-modal-answer { display: grid; gap: 5px; }
.tender-modal-answer + .tender-modal-answer { margin-top: 14px; padding-top: 14px; border-top: 1px solid #eef0f3; }
@media (max-width: 600px) { #tender-detail-modal { width: calc(100vw - 20px); max-height: 92vh; } .tender-modal-shell { max-height: 92vh; } .tender-modal-header, .tender-modal-content { padding: 18px; } .tender-modal-facts { grid-template-columns: 1fr; gap: 12px; } .tender-modal-header h2 { font-size: 20px; } .tender-modal-document { grid-template-columns: minmax(0,1fr) auto; gap: 8px 12px; } .tender-modal-document .tender-modal-list-meta { grid-column: 1; } .tender-modal-document .tender-modal-links { grid-column: 2; grid-row: 1 / span 2; } }
#all-tenders-footer { padding: 28px 16px; background: #0b1f3b; color: #fff; }
.footer-inner { width: min(1200px, 100%); margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
.footer-links { display: flex; flex-wrap: wrap; gap: 18px; }
.footer-links a { color: #e4eaf3; text-decoration: none; }
.footer-links a:hover { color: #fff; text-decoration: underline; }
@media (min-width: 768px) { .page-heading { font-size: 60px; } .tender-card-meta { flex-direction: row; } }
@media (max-width: 900px) { #mainNav { gap: 14px; } #site-nav { gap: 14px; } }
@media (max-width: 767px) { #mainNav, .kt-header-actions { display: none; } #mobileMenuBtn { display: inline-flex; } .filter-grid { grid-template-columns: 1fr 1fr; } .filter-actions { grid-column: 1 / -1; } }
@media (max-width: 560px) { .page-heading { font-size: 30px; } .filter-grid { grid-template-columns: 1fr; } .tender-card-top, .tender-load-error { align-items: flex-start; flex-direction: column; } .tender-deadline { text-align: left; } .filter-actions { align-items: stretch; flex-direction: column; } .footer-inner { align-items: flex-start; flex-direction: column; } }
@media (max-width: 1023px) { .filter-grid-primary, .filter-grid-live { grid-template-columns: repeat(2,minmax(0,1fr)); } .filter-grid-dates { grid-template-columns: repeat(2,minmax(0,1fr)); } }
@media (max-width: 560px) { .filter-grid-primary, .filter-grid-live, .filter-grid-dates { grid-template-columns: 1fr; } }
@media (min-width: 1024px) { .filter-grid-dates { grid-template-columns: repeat(3,minmax(0,1fr)); } }
@media (min-width: 1280px) { .filter-grid-dates { grid-template-columns: repeat(5,minmax(0,1fr)); } }
</style>

<div id="headerWrapper" class="navbar-blur">
  <div id="topBar"><div class="absolute inset-0 pattern-dots opacity-30"></div><div id="topBar-inner"><span><i class="far fa-clock"></i> <span id="live-time"></span></span><span aria-hidden="true">|</span><span><i class="fas fa-phone"></i> +254 700 000 000</span></div></div>
  <nav id="site-nav" aria-label="Main navigation">
    <a id="site-logo" href="/" aria-label="KenyaTenders home"><img src="https://ik.imagekit.io/kltovsgah/kentender_logo.png" alt="KenyaTenders"></a>
    <div id="mainNav">
      <a href="/">Home</a><a href="/about">About</a>
      <div class="dropdown"><button class="dropdown-toggle" type="button">Tenders <i class="fas fa-chevron-down" aria-hidden="true"></i></button><div class="dropdown-menu"><a href="/all-tenders" class="dropdown-item">All Tenders</a><a href="/contracts" class="dropdown-item">Awarded Contracts</a></div></div>
      <div class="dropdown"><button class="dropdown-toggle" type="button">Industries <i class="fas fa-chevron-down" aria-hidden="true"></i></button><div class="dropdown-menu"><a href="/industry/public" class="dropdown-item">Public Sector</a><a href="/industry/private" class="dropdown-item">Private Sector</a><a href="/industry/donor" class="dropdown-item">Donor Funded</a></div></div>
    </div>
    {% if frappe.session.user == 'Guest' %}
    <div class="kt-header-actions"><a id="kt-dashboard-button" class="kt-action-button" href="/app/home"><i class="fas fa-table-columns" aria-hidden="true"></i><span>Go to Dashboard</span></a><a id="kt-start-trial" class="kt-action-button" href="/tenant_registration"><i class="fas fa-rocket" aria-hidden="true"></i><span>Get Started</span></a></div>
    {% else %}
    <div class="kt-header-actions">
      <a id="kt-dashboard-button" class="kt-action-button" href="/app/home"><i class="fas fa-table-columns" aria-hidden="true"></i><span>Go to Dashboard</span></a>
      <div class="kt-profile-wrap">
        <button type="button" id="kt-profile-button" aria-haspopup="menu" aria-expanded="false">
          <span class="kt-profile-avatar" aria-hidden="true">{{ frappe.session.user[0:1]|upper }}</span><span>{{ frappe.session.user }}</span><i class="fas fa-chevron-down kt-profile-chevron" aria-hidden="true"></i>
        </button>
        <div id="kt-profile-menu" role="menu" aria-label="Account menu" hidden>
          <a href="/account" role="menuitem"><i class="fas fa-user" aria-hidden="true"></i><span>Profile</span></a>
          <button type="button" role="menuitem" data-kt-profile-logout><i class="fas fa-right-from-bracket" aria-hidden="true"></i><span>Log out</span></button>
        </div>
      </div>
    </div>
    {% endif %}
    <button id="mobileMenuBtn" type="button" aria-label="Open menu"><i class="fas fa-bars" aria-hidden="true"></i></button>
  </nav>
  <nav id="mobileMenu" hidden aria-label="Mobile navigation"><div id="mobileMenu-inner"><a href="/">Home</a><a href="/about">About</a><a href="/all-tenders">All Tenders</a><a href="/contracts">Awarded Contracts</a><a href="/app/home">Go to Dashboard</a>{% if frappe.session.user == 'Guest' %}<a href="/tenant_registration">Get Started</a>{% else %}<a href="/account">Profile</a>{% endif %}</div></nav>
</div>

<main class="all-tenders-main">
  <div class="absolute inset-0 pattern-grid opacity-50"></div>
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>
  <div class="page-inner">
    <div class="text-center mb-16">
      <h1 class="page-heading">All <span class="bg-gray-600 bg-clip-text text-transparent">Tenders</span></h1>
      <p class="page-intro">Browse published opportunities and review tender details across Kenya.</p>
    </div>

    <div class="filter-heading">
      <h2><i class="fas fa-filter"></i><span>All Tenders Filters</span></h2>
      <button class="filter-toggle" id="filterToggle" type="button" aria-expanded="false"><i class="fas fa-chevron-up"></i><span class="toggle-text">Show Filters</span></button>
    </div>

    <section class="filter-panel collapsed" id="filterPanel" aria-label="Tender filters">
      <div class="filter-content" id="filterContent">
        <form id="tender-filters">
          <div class="filter-grid filter-grid-primary">
            <div class="filter-field"><label for="tender-reference">Ref. No.</label><input id="tender-reference" class="input-modern bg-white" type="search" placeholder="Enter KET reference" disabled data-filter-placeholder="reference"></div>
            <div class="filter-field"><label for="tender-location">Location</label><select id="tender-location" class="input-modern bg-white" disabled data-filter-placeholder="location"><option value="">All Locations</option><option value="nairobi">Nairobi County</option><option value="mombasa">Mombasa County</option><option value="kisumu">Kisumu County</option><option value="kiambu">Kiambu County</option><option value="nakuru">Nakuru County</option></select></div>
            <div class="filter-field"><label for="tender-financier">Financier</label><select id="tender-financier" class="input-modern bg-white" disabled data-filter-placeholder="financier"><option value="">All Financiers</option><option value="world-bank">World Bank</option><option value="afdb">African Development Bank</option><option value="eu">European Union</option><option value="gok">Government of Kenya</option><option value="usaid">USAID</option></select></div>
            <div class="filter-field"><label for="tender-search">Search Keywords</label><input id="tender-search" class="input-modern bg-white" type="search" placeholder="Enter keywords"><label class="filter-exact" for="tender-exact"><input id="tender-exact" type="checkbox" disabled data-filter-placeholder="exact-match">Exact match only</label></div>
          </div>
          <div class="filter-grid filter-grid-dates">
            <div class="filter-field"><label for="tender-award-from">Award Date From</label><div class="date-input-wrapper"><i class="fas fa-calendar-alt" aria-hidden="true"></i><input id="tender-award-from" type="date" disabled data-filter-placeholder="award-date-from"></div></div>
            <div class="filter-field"><label for="tender-award-to">Award Date To</label><div class="date-input-wrapper"><i class="fas fa-calendar-alt" aria-hidden="true"></i><input id="tender-award-to" type="date" disabled data-filter-placeholder="award-date-to"></div></div>
            <div class="filter-field"><label for="tender-contract-from">Contract Start From</label><div class="date-input-wrapper"><i class="fas fa-calendar-alt" aria-hidden="true"></i><input id="tender-contract-from" type="date" disabled data-filter-placeholder="contract-start-from"></div></div>
            <div class="filter-field"><label for="tender-contract-to">Contract End To</label><div class="date-input-wrapper"><i class="fas fa-calendar-alt" aria-hidden="true"></i><input id="tender-contract-to" type="date" disabled data-filter-placeholder="contract-end-to"></div></div>
            <div class="filter-field"><label for="tender-value-range">Value Range</label><select id="tender-value-range" class="input-modern bg-white" disabled data-filter-placeholder="value-range"><option value="">Any Value</option><option value="under-10m">Under KES 10M</option><option value="10m-50m">KES 10M - 50M</option><option value="50m-200m">KES 50M - 200M</option><option value="over-200m">Over KES 200M</option></select></div>
          </div>
          <div class="filter-grid filter-grid-live">
            <div class="filter-field"><label for="tender-method">Method</label><select id="tender-method" class="input-modern bg-white"><option value="">All methods</option></select></div>
            <div class="filter-field"><label for="tender-reservation">Reservation</label><select id="tender-reservation" class="input-modern bg-white"><option value="">All categories</option></select></div>
            <div class="filter-field"><label for="tender-closing">Availability</label><select id="tender-closing" class="input-modern bg-white"><option value="all">Open and closed</option><option value="open">Open tenders</option><option value="closed">Closed or cancelled</option></select></div>
          </div>
          <div class="filter-actions">
            <button type="submit" class="btn-primary"><i class="fas fa-search"></i><span>Search Tenders</span></button>
            <button id="tender-filter-reset" type="button" class="btn-secondary"><i class="fas fa-redo"></i><span>Reset Filters</span></button>
          </div>
        </form>
      </div>
    </section>

    <div class="tender-results-summary"><p id="tender-count" aria-live="polite">Loading tenders…</p></div>
    <div id="tender-load-error" class="tender-load-error" role="alert" hidden><span>We could not load tenders. Please try again.</span><button id="tender-retry" type="button" class="btn-secondary">Try again</button></div>
    <div id="tender-results-state" class="tender-results-state" role="status" hidden></div>
    <div id="tender-results" class="space-y-6 mb-16" aria-live="polite"></div>
  </div>
</main>

<dialog id="tender-detail-modal" aria-labelledby="tender-detail-title" aria-describedby="tender-detail-description">
  <div class="tender-modal-shell">
    <header class="tender-modal-header">
      <div>
        <span id="tender-detail-status" class="badge badge-active" hidden></span>
        <h2 id="tender-detail-title">Tender details</h2>
        <p id="tender-detail-description" class="tender-modal-description"></p>
        <div id="tender-detail-actions" class="tender-modal-actions" role="group" aria-label="Tender actions" hidden></div>
      </div>
      <button id="tender-modal-close" class="tender-modal-close" type="button" aria-label="Close tender details"><i class="fas fa-times" aria-hidden="true"></i></button>
    </header>
    <div id="tender-detail-content" class="tender-modal-content" aria-live="polite"></div>
  </div>
</dialog>

<button id="scrollTop" class="neon-glow" type="button" aria-label="Back to top"><i class="fas fa-arrow-up text-2xl" aria-hidden="true"></i></button>

<footer class="bg-[#0b1f3b] text-white pt-16 pb-8 mt-16">
  <div class="container mx-auto px-4">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
      <div><img src="https://ik.imagekit.io/kltovsgah/kentender_logo.png" alt="KenyaTenders" class="w-40 mb-4 invert brightness-0"><p class="text-gray-400 mb-6">Kenya's leading tender discovery platform.</p></div>
      <div><h4 class="text-lg font-bold mb-6">Quick Links</h4><ul class="space-y-3"><li><a href="/about" class="text-gray-400 hover:text-white">About Us</a></li><li><a href="/all-tenders" class="text-gray-400 hover:text-white">All Tenders</a></li><li><a href="/contracts" class="text-gray-400 hover:text-white">Contract Awards</a></li></ul></div>
      <div><h4 class="text-lg font-bold mb-6">Industries</h4><ul class="space-y-3"><li><a href="/industry/public" class="text-gray-400 hover:text-white">Public Sector</a></li><li><a href="/industry/private" class="text-gray-400 hover:text-white">Private Sector</a></li><li><a href="/industry/donor" class="text-gray-400 hover:text-white">Donor Funded</a></li></ul></div>
      <div><h4 class="text-lg font-bold mb-6">Contact</h4><ul class="space-y-4"><li><i class="fas fa-phone text-[#1f4fd8] mr-3"></i>+254 700 000 000</li><li><i class="fas fa-envelope text-[#1f4fd8] mr-3"></i>info@kentender.co.ke</li><li><i class="fas fa-map-marker-alt text-[#1f4fd8] mr-3"></i>Nairobi, Kenya</li></ul></div>
    </div>
    <div class="border-t border-gray-700 pt-8 text-center"><p class="text-gray-400 text-sm">© 2026 KenyaTenders. All rights reserved.</p></div>
  </div>
</footer>

<script>
(function() {
  var clock = document.getElementById('live-time');
  function updateTime() { if (clock) clock.textContent = new Date().toLocaleString('en-KE', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
  updateTime();
  setInterval(updateTime, 30000);
  document.querySelectorAll('.dropdown-toggle').forEach(function(button) { button.addEventListener('click', function(event) { event.stopPropagation(); var menu = button.nextElementSibling; document.querySelectorAll('.dropdown-menu').forEach(function(item) { if (item !== menu) item.classList.remove('show'); }); menu.classList.toggle('show'); }); });
  document.addEventListener('click', function(event) { if (!event.target.closest('.dropdown')) document.querySelectorAll('.dropdown-menu').forEach(function(menu) { menu.classList.remove('show'); }); });
  var currentPath = window.location.pathname.replace(/\/$/, '') || '/';
  document.querySelectorAll('#mainNav a, #mobileMenu a').forEach(function(link) {
    var href = (link.getAttribute('href') || '').replace(/\/$/, '') || '/';
    if (href !== currentPath) return;
    link.classList.add('active');
    link.setAttribute('aria-current', 'page');
    var dropdown = link.closest('.dropdown');
    var toggle = dropdown && dropdown.querySelector('.dropdown-toggle');
    if (toggle) toggle.classList.add('active');
  });
  var mobileButton = document.getElementById('mobileMenuBtn');
  var mobileMenu = document.getElementById('mobileMenu');
  mobileButton.addEventListener('click', function() { mobileMenu.hidden = !mobileMenu.hidden; });
  var scrollTop = document.getElementById('scrollTop');
  window.addEventListener('scroll', function() { if (window.scrollY > 500) scrollTop.classList.add('visible'); else scrollTop.classList.remove('visible'); }, { passive: true });
  scrollTop.addEventListener('click', function() { window.scrollTo({ top: 0, behavior: 'smooth' }); });
})();
</script>
<script src="/assets/frontend/js/all_tenders.js?v=8"></script>
<script src="/assets/frontend/js/public_profile_menu.js?v=1"></script>
"""
