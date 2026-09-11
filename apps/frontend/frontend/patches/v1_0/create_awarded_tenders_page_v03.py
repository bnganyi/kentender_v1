import frappe


def execute():
    create_awarded_tenders_page()


def create_awarded_tenders_page():
    frappe.db.sql("DELETE FROM `tabWeb Page` WHERE name = 'contracts' OR route = 'contracts'")
    frappe.db.commit()

    page = frappe.new_doc("Web Page")
    page.title = "Awarded Tenders"
    page.route = "contracts"
    page.published = 1
    page.content_type = "HTML"
    page.full_width = 1
    page.show_title = 0
    page.main_section_html = PAGE_HTML
    page.insert(ignore_permissions=True, ignore_if_duplicate=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("✅ Awarded Tenders page created at /contracts")


PAGE_HTML = r"""
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">

<style>
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
html, body { margin:0 !important; padding:0 !important; width:100%; overflow-x:hidden; }

:root {
  --primary-blue:#0066FF;
  --deep-blue:#0047AB;
  --midnight:#0A1929;
  --ghost-white:#F8FAFC;
}

.navbar, nav.navbar, .navbar-light, header.navbar,
.web-footer, .page-header-wrapper, .page-breadcrumbs { display:none !important; }

body { font-family:'Outfit', sans-serif; background: var(--ghost-white); color: var(--midnight); overflow-x:hidden; }

::-webkit-scrollbar { width:10px; }
::-webkit-scrollbar-track { background: var(--ghost-white); }
::-webkit-scrollbar-thumb { background: var(--primary-blue); border-radius:5px; }
::-webkit-scrollbar-thumb:hover { background: var(--deep-blue); }

.navbar-blur { background: rgba(255,255,255,0.97); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(0,102,255,0.1); }
#mainNav { display:flex !important; align-items:center; gap:2rem; }
@media (max-width:767px) { #mainNav { display:none !important; } }
#mobileMenu:not(.hidden) { display:block !important; }

.dropdown { position:relative; display:inline-block; }
.dropdown-toggle {
  color:#374151; font-weight:500; cursor:pointer;
  display:flex; align-items:center; gap:6px;
  background:none; border:none; padding:0; font-size:1rem;
  transition: color 0.2s ease;
}
.dropdown-toggle:hover { color:#2563eb; }
.dropdown-menu {
  position:absolute; top:100%; left:0;
  background:white; border:1px solid #e5e7eb; border-radius:8px;
  box-shadow:0 10px 25px rgba(0,0,0,0.1);
  min-width:200px; padding:8px 0; margin-top:8px;
  opacity:0; visibility:hidden; transform:translateY(-10px);
  transition:all 0.3s ease; z-index:9999;
}
.dropdown-menu.show { opacity:1; visibility:visible; transform:translateY(0); }
.dropdown-item { display:block; padding:12px 20px; color:#1f2937; text-decoration:none; font-size:14px; transition: all 0.2s ease; }
.dropdown-item:hover { background:#f3f4f6; color:#0066ff; padding-left:24px; }
.dropdown-arrow { transition: transform 0.3s ease; font-size:0.75rem; }
.dropdown-arrow.rotate-180 { transform: rotate(180deg); }

@media (min-width: 768px) {
  .dropdown:hover .dropdown-menu { opacity:1 !important; visibility:visible !important; transform:translateY(0) !important; }
  .dropdown:hover .dropdown-arrow { transform: rotate(180deg); }
}

.btn-primary, a.btn-primary, button.btn-primary {
  background: linear-gradient(135deg, #0047AB, #003580) !important;
  color: #ffffff !important;
  padding: 12px 24px !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  border: none !important;
  cursor: pointer !important;
  text-decoration: none !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  white-space: nowrap !important;
  visibility: visible !important;
  opacity: 1 !important;
  transition: all 0.3s ease !important;
}
.btn-primary:hover, a.btn-primary:hover { transform: translateY(-2px) !important; box-shadow: 0 10px 30px rgba(0,102,255,0.4) !important; }
.btn-primary i, a.btn-primary i { color: #ffffff !important; }

.btn-secondary {
  background:white; color:#374151; border:2px solid #e5e7eb;
  padding:12px 28px; border-radius:10px; font-weight:600;
  cursor:pointer; transition: all 0.3s ease;
  display:inline-flex; align-items:center; gap:8px;
}
.btn-secondary:hover { border-color: var(--primary-blue); color: var(--primary-blue); }

.badge { display:inline-block; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; }
.badge-active { background: linear-gradient(135deg,#5db89a,#65c5a7); color:white; }
.badge-category { background: linear-gradient(135deg, var(--deep-blue), var(--deep-blue)); color:white; }

.card-hover { transition: all 0.4s cubic-bezier(0.4,0,0.2,.5); position:relative; overflow:hidden; }
.card-hover:hover { transform: translateY(-8px); box-shadow: 0 20px 30px rgba(22,95,206,0.2); }

.input-modern {
  background: rgba(255,255,255,0.95);
  border: 2px solid transparent; border-radius:12px;
  padding:14px 18px; font-size:15px;
  transition: all 0.3s ease; outline:none; width:100%;
}
.input-modern:focus { border-color: var(--primary-blue); box-shadow: 0 0 0 4px rgba(0,102,255,0.1); background: white; }

.pattern-dots { background-image: radial-gradient(circle, rgba(0,102,255,0.1) 1px, transparent 1px); background-size: 30px 30px; }
.pattern-grid {
  background-image:
    linear-gradient(rgba(0,102,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,102,255,0.05) 1px, transparent 1px);
  background-size: 50px 50px;
}

.glass { backdrop-filter: blur(20px); border:1px solid rgba(255,255,255,0.2); }

.blob { position:absolute; border-radius:50%; filter: blur(60px); opacity:0.3; animation: float 8s ease-in-out infinite; }
.blob-1 { width:400px; height:400px; background: var(--primary-blue); top:-200px; right:-200px; }
.blob-2 { width:300px; height:300px; background: var(--deep-blue); bottom:-150px; left:-150px; animation-delay:-4s; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }

@keyframes fadeInUp { from { opacity:0; transform: translateY(30px); } to { opacity:1; transform: translateY(0); } }
.animate-in { animation: fadeInUp 0.8s ease-out forwards; }

.mono { font-family:'Space Mono', monospace; }

#scrollTop {
  position:fixed; bottom:32px; right:32px;
  width:56px; height:56px; border-radius:50%;
  background: linear-gradient(135deg, var(--deep-blue), var(--deep-blue));
  color:white; border:none; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  box-shadow: 0 10px 30px rgba(0,102,255,0.4);
  z-index:50; opacity:0; visibility:hidden; transition: all 0.3s ease;
}
#scrollTop.visible { opacity:1; visibility:visible; }
#scrollTop:hover { transform: scale(1.1); }
.neon-glow { box-shadow: 0 0 20px rgba(0,102,255,0.3), 0 0 40px rgba(0,102,255,0.2); }

.filter-panel { transition: all 0.4s cubic-bezier(0.4,0,0.2,1); overflow:hidden; }
.filter-panel.collapsed { max-height:80px; margin-bottom:2px; box-shadow:none; }
.filter-panel.expanded { max-height:1200px; margin-bottom:48px; }
.filter-content { transition: opacity 0.3s ease, transform 0.3s ease; }
.filter-panel.collapsed .filter-content { opacity:0; transform: translateY(-20px); pointer-events:none; }
.filter-panel.expanded .filter-content { opacity:1; transform: translateY(0); pointer-events:all; }
.filter-toggle {
  background: linear-gradient(135deg, var(--deep-blue), var(--deep-blue));
  color:white; border:none; padding:8px 24px; border-radius:12px;
  font-weight:600; cursor:pointer; transition: all 0.3s ease;
  display:flex; align-items:center; gap:8px;
}
.filter-toggle:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,102,255,0.3); }

.date-input-wrapper { position:relative; display:flex; align-items:center; background:white; border-radius:12px; overflow:hidden; }
.date-input-wrapper i { color:#6b7280; font-size:14px; }
.date-input-wrapper .date-input { border:none; background:transparent; padding:14px 12px; width:100%; outline:none; font-size:15px; }
.custom-checkbox { width:16px; height:16px; accent-color: var(--primary-blue); cursor:pointer; }

.pagination-btn {
  min-width:40px; height:40px; border-radius:8px;
  background:white; border:1px solid #e5e7eb; color:#374151;
  font-weight:600; cursor:pointer; transition: all 0.2s ease;
}
.pagination-btn:hover { border-color: var(--primary-blue); color: var(--primary-blue); }
.pagination-btn.active { background: linear-gradient(135deg, var(--deep-blue), var(--deep-blue)); color:white; border-color: transparent; }

body.loading { overflow:hidden; }
body:not(.loading) { overflow:visible; }
#loadingOverlay {
  position:fixed; inset:0; background:white;
  display:flex; align-items:center; justify-content:center;
  z-index:9999; opacity:1; transition: opacity 0.3s ease-out;
}
body:not(.loading) #loadingOverlay { opacity:0; pointer-events:none; }

@media (max-width:768px) {
  .filter-panel.expanded { max-height: calc(100vh - 140px); overflow-y:auto; -webkit-overflow-scrolling:touch; }
  .filter-panel.collapsed { max-height:100px; }
}
</style>

<div id="loadingOverlay">
  <img src="https://ik.imagekit.io/kltovsgah/kentender_loader.gif" alt="Loading..." style="width:80px;height:80px;">
</div>

<div id="headerWrapper" class="navbar-blur sticky top-0 z-50">
  <div id="topBar" class="bg-[#0b1f3b] text-white relative overflow-hidden">
    <div class="absolute inset-0 pattern-dots opacity-30"></div>
    <div class="container mx-auto px-4 py-2 relative z-10">
      <div class="flex items-center gap-4 text-sm">
        <span class="mono"><i class="far fa-clock mr-2"></i><span id="live-time"></span></span>
        <span class="hidden md:inline">|</span>
        <span class="hidden md:inline"><i class="fas fa-phone mr-2"></i>+254 700 000 000</span>
      </div>
    </div>
  </div>

  <nav class="container mx-auto px-4 py-4 flex items-center justify-between">
    <a href="/" class="flex items-center">
      <img src="https://ik.imagekit.io/kltovsgah/kentender_logo.png" alt="KenyaTenders" class="h-12 object-contain">
    </a>

    <div id="mainNav">
      <a href="/" class="text-gray-700 font-medium hover:text-blue-600">Home</a>
      <a href="/about" class="text-gray-700 font-medium hover:text-blue-600">About</a>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Tenders <i class="fas fa-chevron-down dropdown-arrow"></i></button>
        <div class="dropdown-menu">
          <a href="/tenders" class="dropdown-item">All Tenders</a>
          <a href="/contracts" class="dropdown-item">Awarded Contracts</a>
        </div>
      </div>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Industries <i class="fas fa-chevron-down dropdown-arrow"></i></button>
        <div class="dropdown-menu">
          <a href="/industry/public" class="dropdown-item">Public Sector</a>
          <a href="/industry/private" class="dropdown-item">Private Sector</a>
          <a href="/industry/donor" class="dropdown-item">Donor Funded</a>
        </div>
      </div>
    </div>

    <div class="hidden md:block">
      <a href="/login" class="btn-primary text-sm"><i class="fas fa-rocket mr-2"></i>Start Free Trial</a>
    </div>

    <button id="mobileMenuBtn" type="button" class="md:hidden text-gray-700 text-2xl"><i class="fas fa-bars"></i></button>
  </nav>

  <div id="mobileMenu" class="hidden border-t bg-white">
    <div class="container mx-auto px-4 py-4 space-y-3">
      <a href="/" class="block text-gray-700 font-medium py-2">Home</a>
      <a href="/about" class="block text-gray-700 font-medium py-2">About</a>
      <a href="/tenders" class="block text-gray-700 font-medium py-2">All Tenders</a>
      <a href="/contracts" class="block text-gray-700 font-medium py-2">Awarded Contracts</a>
      <a href="/login" class="btn-primary text-sm inline-block mt-2">Start Free Trial</a>
    </div>
  </div>
</div>

<section class="relative py-24 overflow-hidden bg-gradient-to-br from-gray-50 to-green-50">
  <div class="absolute inset-0 pattern-grid opacity-50"></div>
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>

  <div class="container mx-auto relative z-10 px-4">
    <div class="text-center mb-16">
      <h1 class="text-3xl md:text-6xl font-bold text-gray-600 mb-6">
        Awarded <span class="bg-gray-600 bg-clip-text text-transparent">Tenders</span>
      </h1>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        View recently awarded contracts across government and private sectors in Kenya
      </p>
    </div>

    <div class="bg-black/5 py-4 px-4 rounded-3xl mb-8 flex justify-between items-center flex-wrap gap-3">
      <h2 class="flex items-center gap-2 font-bold text-lg">
        <i class="fas fa-filter text-green-600"></i>
        <span>Awarded Tenders Filters</span>
      </h2>
      <button class="filter-toggle" id="filterToggle" type="button">
        <i class="fas fa-plus"></i>
        <span class="toggle-text">Hide Filters</span>
      </button>
    </div>

    <div class="filter-panel bg-[#0b1f3b]/5 shadow-xl rounded-2xl mb-8 p-6 md:p-8" id="filterPanel">
      <div class="filter-content" id="filterContent">
        <form class="space-y-6" onsubmit="event.preventDefault();">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            <div>
              <label class="block text-sm font-medium mb-2">Ref. No.</label>
              <input type="text" placeholder="Enter KET reference" class="input-modern bg-white placeholder-gray-500">
            </div>
            <div>
              <label class="block text-sm font-medium mb-2"><i class="fas fa-map-marker-alt text-red-500 mr-1"></i>Location</label>
              <select class="input-modern bg-white">
                <option value="">All Locations</option>
                <option value="nairobi">Nairobi County</option>
                <option value="mombasa">Mombasa County</option>
                <option value="kisumu">Kisumu County</option>
                <option value="kiambu">Kiambu County</option>
                <option value="nakuru">Nakuru County</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">Financier</label>
              <select class="input-modern bg-white">
                <option value="">All Financiers</option>
                <option value="world-bank">World Bank</option>
                <option value="afdb">African Development Bank</option>
                <option value="eu">European Union</option>
                <option value="gok">Government of Kenya</option>
                <option value="usaid">USAID</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">Search Keywords</label>
              <input type="text" placeholder="Enter keywords" class="input-modern bg-white placeholder-gray-500">
              <div class="mt-3 flex items-center">
                <input type="checkbox" id="exact" class="custom-checkbox mr-2">
                <label for="exact" class="text-sm text-gray-600 cursor-pointer">Exact match only</label>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            <div>
              <label class="block text-sm font-medium mb-2">Award Date From</label>
              <div class="date-input-wrapper"><i class="fas fa-calendar-alt mx-4"></i><input type="date" class="date-input"></div>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">Award Date To</label>
              <div class="date-input-wrapper"><i class="fas fa-calendar-alt mx-4"></i><input type="date" class="date-input"></div>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">Contract Start From</label>
              <div class="date-input-wrapper"><i class="fas fa-calendar-alt mx-4"></i><input type="date" class="date-input"></div>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">Contract End To</label>
              <div class="date-input-wrapper"><i class="fas fa-calendar-alt mx-4"></i><input type="date" class="date-input"></div>
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">Value Range</label>
              <select class="input-modern bg-white">
                <option value="">Any Value</option>
                <option value="under-10m">Under KES 10M</option>
                <option value="10m-50m">KES 10M - 50M</option>
                <option value="50m-200m">KES 50M - 200M</option>
                <option value="over-200m">Over KES 200M</option>
              </select>
            </div>
          </div>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6 border-t-2 border-gray-200">
            <button type="submit" class="btn-primary"><i class="fas fa-search"></i><span>Search Awarded Tenders</span></button>
            <button type="reset" class="btn-secondary"><i class="fas fa-redo"></i><span>Reset Filters</span></button>
          </div>
        </form>
      </div>
    </div>

    <div class="space-y-6 mb-16">
      <div class="rounded-2xl shadow-lg card-hover overflow-hidden bg-black/5">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2"><span class="badge badge-category text-xs">ROAD WORKS</span><span class="badge badge-active">Awarded</span></div>
            <div class="flex items-center text-gray-600 gap-2">
              <div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Awarded Date:</div>
              <div class="font-bold text-sm text-green-600 mono">12 Jan 2026</div>
            </div>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Rehabilitation of County Access Roads – Phase II</h3>
          <div class="flex flex-col lg:flex-row justify-between gap-4">
            <div class="flex flex-wrap gap-8">
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide mb-1">Winner</div><div class="font-bold text-green-700">Mavuno Roads Ltd</div></div>
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide">Location</div><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-md">Kericho County</span></div>
              <div><div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Contract Value</div><div class="font-medium text-gray-800 mono">KES 412M</div></div>
            </div>
            <button class="btn-primary text-sm whitespace-nowrap">View Details <i class="fas fa-arrow-right ml-2"></i></button>
          </div>
        </div>
      </div>

      <div class="rounded-2xl shadow-lg card-hover overflow-hidden bg-black/5">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2"><span class="badge badge-category text-xs">ICT</span><span class="badge badge-active">Awarded</span></div>
            <div class="flex items-center text-gray-600 gap-2">
              <div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Awarded Date:</div>
              <div class="font-bold text-sm text-green-600 mono">05 Feb 2026</div>
            </div>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Supply &amp; Configuration of Data Center Infrastructure</h3>
          <div class="flex flex-col lg:flex-row justify-between gap-4">
            <div class="flex flex-wrap gap-8">
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide mb-1">Winner</div><div class="font-bold text-green-700">Netcore Solutions Ltd</div></div>
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide">Location</div><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-md">Nairobi County</span></div>
              <div><div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Contract Value</div><div class="font-medium text-gray-800 mono">KES 96M</div></div>
            </div>
            <button class="btn-primary text-sm whitespace-nowrap">View Details <i class="fas fa-arrow-right ml-2"></i></button>
          </div>
        </div>
      </div>

      <div class="rounded-2xl shadow-lg card-hover overflow-hidden bg-black/5">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2"><span class="badge badge-category text-xs">HEALTH</span><span class="badge badge-active">Awarded</span></div>
            <div class="flex items-center text-gray-600 gap-2">
              <div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Awarded Date:</div>
              <div class="font-bold text-sm text-green-600 mono">22 Dec 2025</div>
            </div>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Supply of Radiology &amp; Diagnostic Equipment</h3>
          <div class="flex flex-col lg:flex-row justify-between gap-4">
            <div class="flex flex-wrap gap-8">
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide mb-1">Winner</div><div class="font-bold text-green-700">Meditech Africa Ltd</div></div>
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide">Location</div><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-md">Kisii County</span></div>
              <div><div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Contract Value</div><div class="font-medium text-gray-800 mono">KES 178M</div></div>
            </div>
            <button class="btn-primary text-sm whitespace-nowrap">View Details <i class="fas fa-arrow-right ml-2"></i></button>
          </div>
        </div>
      </div>

      <div class="rounded-2xl shadow-lg card-hover overflow-hidden bg-black/5">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2"><span class="badge badge-category text-xs">EDUCATION</span><span class="badge badge-active">Awarded</span></div>
            <div class="flex items-center text-gray-600 gap-2">
              <div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Awarded Date:</div>
              <div class="font-bold text-sm text-green-600 mono">18 Jan 2026</div>
            </div>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Construction of Technical Training Workshops</h3>
          <div class="flex flex-col lg:flex-row justify-between gap-4">
            <div class="flex flex-wrap gap-8">
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide mb-1">Winner</div><div class="font-bold text-green-700">Prime Builders Kenya</div></div>
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide">Location</div><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-md">Nyeri County</span></div>
              <div><div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Contract Value</div><div class="font-medium text-gray-800 mono">KES 245M</div></div>
            </div>
            <button class="btn-primary text-sm whitespace-nowrap">View Details <i class="fas fa-arrow-right ml-2"></i></button>
          </div>
        </div>
      </div>

      <div class="rounded-2xl shadow-lg card-hover overflow-hidden bg-black/5">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2"><span class="badge badge-category text-xs">AGRICULTURE</span><span class="badge badge-active">Awarded</span></div>
            <div class="flex items-center text-gray-600 gap-2">
              <div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Awarded Date:</div>
              <div class="font-bold text-sm text-green-600 mono">30 Nov 2025</div>
            </div>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Supply of Irrigation Pumps &amp; Farm Inputs</h3>
          <div class="flex flex-col lg:flex-row justify-between gap-4">
            <div class="flex flex-wrap gap-8">
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide mb-1">Winner</div><div class="font-bold text-green-700">GreenGrow Supplies Ltd</div></div>
              <div><div class="text-xs text-gray-900 uppercase font-bold tracking-wide">Location</div><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-md">Bungoma County</span></div>
              <div><div class="text-xs text-gray-900 font-bold uppercase tracking-wide">Contract Value</div><div class="font-medium text-gray-800 mono">KES 89M</div></div>
            </div>
            <button class="btn-primary text-sm whitespace-nowrap">View Details <i class="fas fa-arrow-right ml-2"></i></button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex justify-center items-center gap-2 flex-wrap animate-in">
      <button class="pagination-btn"><i class="fas fa-chevron-left"></i></button>
      <button class="pagination-btn active">1</button>
      <button class="pagination-btn">2</button>
      <button class="pagination-btn">3</button>
      <span class="text-gray-600">...</span>
      <button class="pagination-btn">18</button>
      <button class="pagination-btn"><i class="fas fa-chevron-right"></i></button>
    </div>
  </div>
</section>

<button id="scrollTop" class="neon-glow">
  <i class="fas fa-arrow-up text-2xl"></i>
</button>

<footer class="bg-[#0b1f3b] text-white pt-16 pb-8 mt-16">
  <div class="container mx-auto px-4">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
      <div>
        <img src="https://ik.imagekit.io/kltovsgah/kentender_logo.png" alt="KenyaTenders" class="w-40 mb-4 invert brightness-0">
        <p class="text-gray-400 mb-6">Kenya's leading tender discovery platform.</p>
      </div>
      <div>
        <h4 class="text-lg font-bold mb-6">Quick Links</h4>
        <ul class="space-y-3">
          <li><a href="/about" class="text-gray-400 hover:text-white">About Us</a></li>
          <li><a href="/tenders" class="text-gray-400 hover:text-white">All Tenders</a></li>
          <li><a href="/contracts" class="text-gray-400 hover:text-white">Contract Awards</a></li>
        </ul>
      </div>
      <div>
        <h4 class="text-lg font-bold mb-6">Industries</h4>
        <ul class="space-y-3">
          <li><a href="/industry/public" class="text-gray-400 hover:text-white">Public Sector</a></li>
          <li><a href="/industry/private" class="text-gray-400 hover:text-white">Private Sector</a></li>
          <li><a href="/industry/donor" class="text-gray-400 hover:text-white">Donor Funded</a></li>
        </ul>
      </div>
      <div>
        <h4 class="text-lg font-bold mb-6">Contact</h4>
        <ul class="space-y-4">
          <li><i class="fas fa-phone text-[#1f4fd8] mr-3"></i>+254 700 000 000</li>
          <li><i class="fas fa-envelope text-[#1f4fd8] mr-3"></i>info@kentender.co.ke</li>
          <li><i class="fas fa-map-marker-alt text-[#1f4fd8] mr-3"></i>Nairobi, Kenya</li>
        </ul>
      </div>
    </div>
    <div class="border-t border-gray-700 pt-8 text-center">
      <p class="text-gray-400 text-sm">© 2026 KenyaTenders. All rights reserved.</p>
    </div>
  </div>
</footer>

<script>
(function() {
  'use strict';

  document.body.classList.add('loading');
  window.addEventListener('load', function() { document.body.classList.remove('loading'); });
  setTimeout(function() { document.body.classList.remove('loading'); }, 1500);

  function updateTime() {
    var el = document.getElementById('live-time');
    if (el) el.textContent = new Date().toLocaleString();
  }
  updateTime(); setInterval(updateTime, 1000);

  document.querySelectorAll('.dropdown-toggle').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation(); e.preventDefault();
      var menu = btn.nextElementSibling;
      document.querySelectorAll('.dropdown-menu').forEach(function(m) { if (m !== menu) m.classList.remove('show'); });
      menu.classList.toggle('show');
      var arrow = btn.querySelector('.dropdown-arrow');
      if (arrow) arrow.classList.toggle('rotate-180');
    });
  });
  document.addEventListener('click', function() {
    document.querySelectorAll('.dropdown-menu').forEach(function(m) { m.classList.remove('show'); });
  });

  var mobileBtn = document.getElementById('mobileMenuBtn');
  var mobileMenu = document.getElementById('mobileMenu');
  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', function(e) {
      e.preventDefault(); e.stopPropagation();
      mobileMenu.classList.toggle('hidden');
    });
  }

  var scrollTopBtn = document.getElementById('scrollTop');
  if (scrollTopBtn) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 500) scrollTopBtn.classList.add('visible');
      else scrollTopBtn.classList.remove('visible');
    }, { passive: true });
    scrollTopBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  var filterPanel = document.getElementById('filterPanel');
  var filterToggle = document.getElementById('filterToggle');
  if (filterPanel && filterToggle) {
    var toggleIcon = filterToggle.querySelector('i');
    var toggleText = filterToggle.querySelector('.toggle-text');
    var saved = localStorage.getItem('awardedFilterPanelCollapsed');
    if (saved !== 'false') collapse();
    filterToggle.addEventListener('click', function() {
      if (filterPanel.classList.contains('collapsed')) expand();
      else collapse();
    });
    function collapse() {
      filterPanel.classList.remove('expanded'); filterPanel.classList.add('collapsed');
      toggleIcon.classList.remove('fa-chevron-down'); toggleIcon.classList.add('fa-chevron-up');
      if (toggleText) toggleText.textContent = 'Show Filters';
      localStorage.setItem('awardedFilterPanelCollapsed', 'true');
    }
    function expand() {
      filterPanel.classList.remove('collapsed'); filterPanel.classList.add('expanded');
      toggleIcon.classList.remove('fa-chevron-up'); toggleIcon.classList.add('fa-chevron-down');
      if (toggleText) toggleText.textContent = 'Hide Filters';
      localStorage.setItem('awardedFilterPanelCollapsed', 'false');
    }
  }

  // Active nav
  (function initActiveNav() {
    try {
      var path = window.location.pathname || '/';
      var cleanPath = path.replace(/\/$/, '') || '/';
      document.querySelectorAll('#mainNav a, #mobileMenu a').forEach(function(a) {
        var href = a.getAttribute('href') || '';
        var cleanHref = href.replace(/\/$/, '') || '/';
        var isMatch = false;
        if (cleanPath === '/' && (cleanHref === '/' || cleanHref === '/home')) isMatch = true;
        else if (cleanHref === cleanPath) isMatch = true;
        else if (cleanHref !== '/' && cleanPath.indexOf(cleanHref) === 0) isMatch = true;
        else if ((cleanPath === '/contracts' && cleanHref === '/contract') || (cleanPath === '/contract' && cleanHref === '/contracts')) isMatch = true;

        if (isMatch) {
          a.classList.add('active');
          a.setAttribute('aria-current', 'page');
          a.style.setProperty('color', '#2563eb', 'important');
          a.style.setProperty('font-weight', '700', 'important');
          a.style.setProperty('border-bottom', '2px solid #2563eb', 'important');
          a.style.setProperty('padding-bottom', '4px', 'important');
          a.style.setProperty('display', 'inline-block', 'important');
          var dropdown = a.closest('.dropdown');
          if (dropdown) {
            var toggle = dropdown.querySelector('.dropdown-toggle');
            if (toggle) {
              toggle.classList.add('active');
              toggle.style.setProperty('color', '#2563eb', 'important');
              toggle.style.setProperty('font-weight', '700', 'important');
              toggle.style.setProperty('border-bottom', '2px solid #2563eb', 'important');
              toggle.style.setProperty('padding-bottom', '4px', 'important');
              toggle.style.setProperty('display', 'inline-block', 'important');
            }
          }
        } else {
          a.classList.remove('active');
          a.removeAttribute('aria-current');
          a.style.removeProperty('border-bottom');
          a.style.removeProperty('padding-bottom');
          a.style.removeProperty('display');
          a.style.removeProperty('color');
          a.style.removeProperty('font-weight');
        }
      });
    } catch (e) {}
  })();
})();
</script>
"""