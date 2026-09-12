import frappe


def execute():
    create_homepage()


def create_homepage():
    """Create the complete KenyaTenders homepage as a Web Page (idempotent)"""
    
    # Safe delete (idempotent)
    frappe.db.sql("DELETE FROM `tabWeb Page` WHERE name = 'home' OR route = 'home'")
    frappe.db.commit()
    
    page = frappe.new_doc("Web Page")
    page.title = "Home"
    page.route = "home"
    page.published = 1
    page.content_type = "HTML"
    page.full_width = 1
    page.show_title = 0
    page.main_section_html = PAGE_HTML
    
    page.insert(ignore_permissions=True, ignore_if_duplicate=True)
    frappe.db.commit()
    print("✅ Homepage created")

    ws = frappe.get_doc("Website Settings")
    ws.home_page = "home"
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("✅ Website Settings: home_page = 'home'")

    frappe.clear_cache()
    print("🌐 Visit: http://localhost:8000/")


PAGE_HTML = r'''
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { margin: 0 !important; padding: 0 !important; width: 100%; overflow-x: hidden; }
body { font-family: 'Outfit', sans-serif; background: #F8FAFC; color: #0A1929; padding-top: 0 !important; }

.navbar, nav.navbar, .navbar-light, header.navbar,
.web-footer, .page-header-wrapper, .page-breadcrumbs,
footer.web-footer { display: none !important; }

:root {
  --primary-blue: #0066FF;
  --deep-blue: #0047AB;
  --midnight: #0A1929;
  --ghost-white: #F8FAFC;
}

.navbar-blur { background: rgba(255,255,255,0.97); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(0,102,255,0.1); }
#mainNav { display: flex !important; align-items: center; gap: 2rem; }
@media (max-width: 767px) { #mainNav { display: none !important; } }

.dropdown { position: relative; display: inline-block; }
.dropdown-toggle {
  color: #374151; font-weight: 500; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  background: none; border: none; padding: 0; font-size: 1rem;
  transition: color 0.3s ease;
}
.dropdown-toggle:hover { color: #2563eb; }
.dropdown-menu {
  position: absolute; top: 100%; left: 0;
  background: white; border: 1px solid #e5e7eb; border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1); min-width: 200px;
  padding: 8px 0; margin-top: 8px;
  opacity: 0; visibility: hidden; transform: translateY(-10px);
  transition: all 0.3s ease; z-index: 9999;
}
.dropdown-menu.show { opacity: 1; visibility: visible; transform: translateY(0); }
.dropdown-item {
  display: block; padding: 12px 20px; color: #1f2937;
  text-decoration: none; font-size: 14px; transition: all 0.2s ease;
}
.dropdown-item:hover { background: #f3f4f6; color: #0066ff; padding-left: 24px; }
.dropdown-arrow { transition: transform 0.3s ease; font-size: 0.75rem; }
.dropdown-arrow.rotate-180 { transform: rotate(180deg); }

@media (min-width: 768px) {
  .dropdown:hover .dropdown-menu {
    opacity: 1 !important; visibility: visible !important;
    transform: translateY(0) !important;
  }
  .dropdown:hover .dropdown-arrow { transform: rotate(180deg); }
}

.btn-primary, a.btn-primary, button.btn-primary {
  background: linear-gradient(135deg, #0047AB, #003580) !important;
  color: #ffffff !important;
  padding: 12px 24px !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  transition: all 0.3s ease !important;
  border: none !important;
  cursor: pointer !important;
  text-decoration: none !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  line-height: 1.2 !important;
  white-space: nowrap !important;
  visibility: visible !important;
  opacity: 1 !important;
}
.btn-primary:hover, a.btn-primary:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 10px 30px rgba(0,102,255,0.4) !important;
}
.btn-primary i, a.btn-primary i { color: #ffffff !important; display: inline-block !important; }

.glass { background: rgba(255,255,255,0.1); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.2); }
.card-hover { transition: all 0.3s ease; }
.card-hover:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
.mono { font-family: 'Space Mono', monospace; }
.neon-glow { box-shadow: 0 0 20px rgba(0,102,255,0.3), 0 0 40px rgba(0,102,255,0.2); }
.input-modern {
  background: white; border: 2px solid transparent; border-radius: 12px;
  padding: 14px 18px; font-size: 16px; outline: none; width: 100%;
  transition: all 0.3s ease;
}
.input-modern:focus { border-color: #0066FF; box-shadow: 0 0 0 4px rgba(0,102,255,0.1); }
.pattern-dots {
  background-image: radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px);
  background-size: 30px 30px;
}
.pattern-grid {
  background-image:
    linear-gradient(rgba(0,102,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,102,255,0.05) 1px, transparent 1px);
  background-size: 50px 50px;
}
.badge {
  display: inline-block; padding: 6px 14px; border-radius: 20px;
  font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
}
.badge-active { background: linear-gradient(135deg, #5db89a, #65c5a7); color: white; }
.badge-category { background: linear-gradient(135deg, #0066FF, #0047AB); color: white; }

@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-20px)} }
@keyframes fadeInUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
.float { animation: float 6s ease-in-out infinite; }
.animate-in { animation: fadeInUp 0.8s ease-out forwards; }
.stat-card { animation: fadeInUp 0.6s ease-out forwards; }

.blob { position: absolute; border-radius: 50%; filter: blur(60px); opacity: 0.3; animation: float 8s ease-in-out infinite; }
.blob-1 { width: 400px; height: 400px; background: #0066FF; top: -200px; right: -200px; }
.blob-2 { width: 300px; height: 300px; background: #0047AB; bottom: -150px; left: -150px; animation-delay: -4s; }

#mobileMenu.hidden { display: none !important; }
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: #F8FAFC; }
::-webkit-scrollbar-thumb { background: #0066FF; border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #0047AB; }
</style>

<div id="headerWrapper" class="navbar-blur sticky top-0 z-50">
  <div id="topBar" class="bg-[#0b1f3b] text-white relative overflow-hidden">
    <div class="absolute inset-0 pattern-dots opacity-30"></div>
    <div class="container mx-auto px-4 py-2 relative z-10">
      <div class="flex items-center gap-4 text-sm">
        <span class="mono"><i class="far fa-clock mr-2"></i><span id="live-time">Loading...</span></span>
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
      <a href="/" class="text-gray-700 font-medium hover:text-blue-600 transition-colors">Home</a>
      <a href="/about" class="text-gray-700 font-medium hover:text-blue-600 transition-colors">About</a>

      <div class="dropdown">
        <button class="dropdown-toggle" type="button">
          Tenders <i class="fas fa-chevron-down dropdown-arrow"></i>
        </button>
        <div class="dropdown-menu">
          <a href="/tenders" class="dropdown-item">All Tenders</a>
          <a href="/contracts" class="dropdown-item">Awarded Contracts</a>
        </div>
      </div>

      <div class="dropdown">
        <button class="dropdown-toggle" type="button">
          Industries <i class="fas fa-chevron-down dropdown-arrow"></i>
        </button>
        <div class="dropdown-menu">
          <a href="/industry/public" class="dropdown-item">Public Sector</a>
          <a href="/industry/private" class="dropdown-item">Private Sector</a>
          <a href="/industry/donor" class="dropdown-item">Donor Funded</a>
        </div>
      </div>
    </div>

    <div id="kt-start-trial-wrap" class="hidden md:block">
      <a href="/login" id="kt-start-trial">
        <i class="fas fa-rocket"></i>
        <span>Start Free Trial</span>
      </a>
    </div>

    <button id="mobileMenuBtn" type="button" class="md:hidden text-gray-700 text-2xl">
      <i class="fas fa-bars"></i>
    </button>
  </nav>

  <div id="mobileMenu" class="hidden border-t bg-white">
    <div class="container mx-auto px-4 py-4 space-y-3">
      <a href="/" class="block text-gray-700 font-medium py-2">Home</a>
      <a href="/about" class="block text-gray-700 font-medium py-2">About</a>
      <a href="/tenders" class="block text-gray-700 font-medium py-2">All Tenders</a>
      <a href="/contracts" class="block text-gray-700 font-medium py-2">Awarded Contracts</a>
      <a href="/industry/public" class="block text-gray-700 font-medium py-2">Public Sector</a>
      <a href="/industry/private" class="block text-gray-700 font-medium py-2">Private Sector</a>
      <a href="/industry/donor" class="block text-gray-700 font-medium py-2">Donor Funded</a>
      <a href="/login" class="btn-primary text-sm inline-block mt-2">Start Free Trial</a>
    </div>
  </div>
</div>

<style>
#kt-start-trial-wrap {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  flex-shrink: 0 !important;
}
#kt-start-trial {
  display: inline-flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  background: linear-gradient(135deg, #0047AB, #003580) !important;
  color: #ffffff !important;
  padding: 12px 24px !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  text-decoration: none !important;
  white-space: nowrap !important;
  min-width: 180px !important;
  font-family: 'Outfit', sans-serif !important;
  border: none !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
}
#kt-start-trial i,
#kt-start-trial span,
#kt-start-trial * { color: #ffffff !important; }
#kt-start-trial:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 10px 30px rgba(0,102,255,0.4) !important;
}
@media (max-width: 767px) {
  #kt-start-trial-wrap { display: none !important; }
}
</style>

<section class="relative overflow-hidden" style="background: linear-gradient(135deg, #0b1f3b 0%, #1e3a5f 60%, #0066FF 100%); min-height: 55vh;">
  <div class="absolute inset-0 pattern-dots opacity-20"></div>
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>

  <div class="container mx-auto px-4 pt-20 pb-6 text-center relative z-10">
    <h1 class="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
      Discover Kenya's
      <span class="bg-gradient-to-r from-blue-300 to-cyan-300 bg-clip-text text-transparent">Premier Tenders</span>
    </h1>
    <p class="text-xl text-white/90 mb-10 max-w-2xl mx-auto">
      Access verified government and private sector opportunities. Real-time updates. Advanced filtering. Expert support.
    </p>

    <div class="glass bg-white/10 rounded-2xl p-6 max-w-2xl mx-auto mb-12">
      <form action="/tenders" method="GET" class="flex flex-col md:flex-row gap-3">
        <input type="text" name="search" placeholder="Search tenders by keyword, category, or location..." class="input-modern flex-1" style="color:#0b1f3b;">
        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-6 py-3 rounded-xl whitespace-nowrap">
          <i class="fas fa-search mr-2"></i>Search Now
        </button>
      </form>
      <div class="mt-3 text-sm text-blue-200">
        Popular:
        <a href="/tenders?q=Construction" class="text-white hover:underline">Construction</a> •
        <a href="/tenders?q=IT" class="text-white hover:underline">IT Services</a> •
        <a href="/tenders?q=Energy" class="text-white hover:underline">Energy</a> •
        <a href="/tenders?q=Healthcare" class="text-white hover:underline">Healthcare</a>
      </div>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 max-w-4xl mx-auto">
      <div class="glass rounded-xl p-5"><div class="text-3xl font-bold text-white mono">1000+</div><div class="text-blue-300 text-sm mt-1">Active Tenders</div></div>
      <div class="glass rounded-xl p-5"><div class="text-3xl font-bold text-white mono">24/7</div><div class="text-blue-300 text-sm mt-1">Real-time Updates</div></div>
      <div class="glass rounded-xl p-5"><div class="text-3xl font-bold text-white mono">100%</div><div class="text-blue-300 text-sm mt-1">Verified Sources</div></div>
      <div class="glass rounded-xl p-5"><div class="text-3xl font-bold text-white mono">5K+</div><div class="text-blue-300 text-sm mt-1">Happy Users</div></div>
    </div>
  </div>
</section>

<section class="py-10 relative bg-white">
  <div class="absolute inset-0 pattern-grid"></div>
  <div class="container mx-auto px-4 pt-16 relative z-10">
    <div class="text-center mb-14">
      <h2 class="text-4xl md:text-5xl font-bold mb-4">Browse by Industry</h2>
      <p class="text-xl text-gray-600 max-w-2xl mx-auto">Find opportunities tailored to your business sector</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <a href="/industry/public" class="bg-white rounded-2xl p-6 shadow-md card-hover border border-gray-100 block">
        <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mb-4 neon-glow">
          <i class="fas fa-building text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-2">Construction</h3>
        <p class="text-gray-600 text-sm mb-4">Building & infrastructure projects</p>
        <div class="flex items-center text-blue-600 font-semibold text-sm"><span>Explore</span><i class="fas fa-arrow-right ml-2"></i></div>
      </a>

      <a href="/industry/private" class="bg-white rounded-2xl p-6 shadow-md card-hover border border-gray-100 block">
        <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center mb-4 neon-glow">
          <i class="fas fa-laptop-code text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-2">IT & Software</h3>
        <p class="text-gray-600 text-sm mb-4">Technology solutions & services</p>
        <div class="flex items-center text-cyan-600 font-semibold text-sm"><span>Explore</span><i class="fas fa-arrow-right ml-2"></i></div>
      </a>

      <a href="/industry/public" class="bg-white rounded-2xl p-6 shadow-md card-hover border border-gray-100 block">
        <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-400 to-blue-500 flex items-center justify-center mb-4 neon-glow">
          <i class="fas fa-bolt text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-2">Energy</h3>
        <p class="text-gray-600 text-sm mb-4">Power & renewable energy</p>
        <div class="flex items-center text-blue-600 font-semibold text-sm"><span>Explore</span><i class="fas fa-arrow-right ml-2"></i></div>
      </a>

      <a href="/industry/public" class="bg-white rounded-2xl p-6 shadow-md card-hover border border-gray-100 block">
        <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-cyan-400 to-cyan-500 flex items-center justify-center mb-4 neon-glow">
          <i class="fas fa-heartbeat text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-2">Healthcare</h3>
        <p class="text-gray-600 text-sm mb-4">Medical supplies & services</p>
        <div class="flex items-center text-cyan-600 font-semibold text-sm"><span>Explore</span><i class="fas fa-arrow-right ml-2"></i></div>
      </a>

      <a href="/industry/public" class="bg-white rounded-2xl p-6 shadow-md card-hover border border-gray-100 block">
        <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center mb-4 neon-glow">
          <i class="fas fa-shield-alt text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-2">Security</h3>
        <p class="text-gray-600 text-sm mb-4">Defense & security equipment</p>
        <div class="flex items-center text-blue-600 font-semibold text-sm"><span>Explore</span><i class="fas fa-arrow-right ml-2"></i></div>
      </a>

      <a href="/industry/private" class="bg-white rounded-2xl p-6 shadow-md card-hover border border-gray-100 block">
        <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-cyan-600 to-cyan-700 flex items-center justify-center mb-4 neon-glow">
          <i class="fas fa-chart-line text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-2">Finance</h3>
        <p class="text-gray-600 text-sm mb-4">Banking & financial services</p>
        <div class="flex items-center text-cyan-600 font-semibold text-sm"><span>Explore</span><i class="fas fa-arrow-right ml-2"></i></div>
      </a>
    </div>
  </div>
</section>

<section class="py-10 bg-gradient-to-br from-gray-50 to-blue-50">
  <div class="container mx-auto px-4">
    <div class="flex justify-between items-center mb-12 flex-wrap gap-4">
      <div>
        <h2 class="text-4xl md:text-5xl font-bold mb-2">Latest Tenders</h2>
        <p class="text-gray-600 text-lg">Fresh opportunities updated daily</p>
      </div>
      <a href="/tenders" class="flex items-center text-blue-600 font-semibold hover:text-blue-700 transition-colors">
        View All <i class="fas fa-arrow-right ml-2"></i>
      </a>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div class="bg-white rounded-2xl shadow-md card-hover overflow-hidden">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2">
              <span class="badge badge-category">CONSTRUCTION</span>
              <span class="badge badge-active">ACTIVE</span>
            </div>
            <span class="text-sm text-gray-500 mono">REF: 134301616</span>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Supply, Delivery & Installation of Fisheries Equipment - University of Cape Coast</h3>
          <div class="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-xl">
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Deadline</div><div class="font-bold text-red-600 mono">28 Feb 2026</div></div>
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Value</div><div class="font-bold text-gray-800">Refer Document</div></div>
          </div>
          <div class="flex justify-between items-center flex-wrap gap-2">
            <div class="flex items-center text-gray-600"><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-sm">Ghana</span></div>
            <a href="/tenders" class="btn-primary text-sm py-2 px-5">View Details <i class="fas fa-arrow-right ml-2"></i></a>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-md card-hover overflow-hidden">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2">
              <span class="badge badge-category">CONSTRUCTION</span>
              <span class="badge badge-active">ACTIVE</span>
            </div>
            <span class="text-sm text-gray-500 mono">REF: 134280425</span>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Additional Works For Gatundu Funeral Home In Kiambu County</h3>
          <div class="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-xl">
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Deadline</div><div class="font-bold text-red-600 mono">03 Feb 2026</div></div>
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Value</div><div class="font-bold text-gray-800">Refer Document KES</div></div>
          </div>
          <div class="flex justify-between items-center flex-wrap gap-2">
            <div class="flex items-center text-gray-600"><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-sm">Kiambu County, Kenya</span></div>
            <a href="/tenders" class="btn-primary text-sm py-2 px-5">View Details <i class="fas fa-arrow-right ml-2"></i></a>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-md card-hover overflow-hidden">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2">
              <span class="badge" style="background: linear-gradient(135deg, #8B5CF6, #6D28D9); color: white;">SUPPLIES</span>
              <span class="badge badge-active">ACTIVE</span>
            </div>
            <span class="text-sm text-gray-500 mono">REF: 134280415</span>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Assorted Pipes And Fittings In Mirangine Ward</h3>
          <div class="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-xl">
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Deadline</div><div class="font-bold text-red-600 mono">02 Feb 2026</div></div>
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Value</div><div class="font-bold text-gray-800">Refer Document KES</div></div>
          </div>
          <div class="flex justify-between items-center flex-wrap gap-2">
            <div class="flex items-center text-gray-600"><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-sm">Mirangine Ward, Kenya</span></div>
            <a href="/tenders" class="btn-primary text-sm py-2 px-5">View Details <i class="fas fa-arrow-right ml-2"></i></a>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-md card-hover overflow-hidden">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4 flex-wrap gap-2">
            <div class="flex gap-2">
              <span class="badge badge-category">CONSTRUCTION</span>
              <span class="badge badge-active">ACTIVE</span>
            </div>
            <span class="text-sm text-gray-500 mono">REF: 134280409</span>
          </div>
          <h3 class="text-xl font-bold mb-4 leading-tight">Construction Of Farewell Home & Hospital Renovation At Karuri Level IV</h3>
          <div class="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-xl">
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Deadline</div><div class="font-bold text-red-600 mono">03 Feb 2026</div></div>
            <div><div class="text-xs text-gray-500 mb-1 uppercase tracking-wide">Value</div><div class="font-bold text-gray-800">Refer Document KES</div></div>
          </div>
          <div class="flex justify-between items-center flex-wrap gap-2">
            <div class="flex items-center text-gray-600"><i class="fas fa-map-marker-alt mr-2 text-blue-600"></i><span class="text-sm">Karuri, Kenya</span></div>
            <a href="/tenders" class="btn-primary text-sm py-2 px-5">View Details <i class="fas fa-arrow-right ml-2"></i></a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="py-10 relative overflow-hidden">
  <div class="absolute inset-0 bg-[#0b1f3b]"></div>
  <div class="absolute inset-0 pattern-dots opacity-20"></div>

  <div class="container mx-auto px-4 relative z-10">
    <div class="max-w-5xl mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div class="text-white">
          <h2 class="text-4xl md:text-5xl font-bold mb-6 text-white">Start Your Free Trial Today</h2>
          <p class="text-xl mb-8 text-cyan-100">Access 1 million+ verified tenders from Kenya and beyond</p>

          <ul class="space-y-4 mb-8">
            <li class="flex items-start"><i class="fas fa-check-circle text-cyan-400 text-xl mr-3 mt-1"></i><span class="text-lg">Daily tender alerts via email</span></li>
            <li class="flex items-start"><i class="fas fa-check-circle text-cyan-400 text-xl mr-3 mt-1"></i><span class="text-lg">Advanced search & filtering tools</span></li>
            <li class="flex items-start"><i class="fas fa-check-circle text-cyan-400 text-xl mr-3 mt-1"></i><span class="text-lg">Export data to Excel</span></li>
            <li class="flex items-start"><i class="fas fa-check-circle text-cyan-400 text-xl mr-3 mt-1"></i><span class="text-lg">Expert bidding assistance</span></li>
            <li class="flex items-start"><i class="fas fa-check-circle text-cyan-400 text-xl mr-3 mt-1"></i><span class="text-lg">API access for integration</span></li>
          </ul>

          <div class="glass rounded-xl p-6">
            <div class="flex items-center">
              <i class="fas fa-gift text-yellow-400 text-3xl mr-4"></i>
              <div>
                <div class="font-bold text-lg">Limited Time Offer</div>
                <div class="text-cyan-200">Get 30 days free trial - No credit card required</div>
              </div>
            </div>
          </div>
        </div>

        <div class="glass bg-white/10 rounded-2xl p-8">
          <div class="mb-6">
            <h3 class="text-2xl font-bold text-white mb-2">Register Now</h3>
            <p class="text-cyan-200">Join 5,000+ businesses finding opportunities</p>
          </div>

          <form class="space-y-4" onsubmit="event.preventDefault(); alert('Thank you for registering!'); this.reset();">
            <div><input type="text" placeholder="Your Full Name" class="input-modern w-full" required></div>
            <div><input type="email" placeholder="Email Address" class="input-modern w-full" required></div>
            <div><input type="tel" placeholder="Phone Number" class="input-modern w-full" required></div>
            <div>
              <select class="input-modern w-full" required>
                <option value="">Select Your Country</option>
                <option value="ke">Kenya</option>
                <option value="tz">Tanzania</option>
                <option value="ug">Uganda</option>
                <option value="rw">Rwanda</option>
                <option value="gh">Ghana</option>
              </select>
            </div>
            <div>
              <select class="input-modern w-full" required>
                <option value="">Select Your Industry</option>
                <option value="construction">Construction</option>
                <option value="it">IT & Software</option>
                <option value="energy">Energy</option>
                <option value="healthcare">Healthcare</option>
                <option value="finance">Finance</option>
                <option value="other">Other</option>
              </select>
            </div>
            <button type="submit" class="w-full bg-[#1f4fd8] text-white font-bold py-4 px-8 rounded-xl hover:bg-blue-500 transition-all shadow-lg">
              <i class="fas fa-rocket mr-2"></i>Start Free Trial
            </button>
            <p class="text-center text-sm text-cyan-200">By registering, you agree to our Terms & Privacy Policy</p>
          </form>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="py-10 bg-white">
  <div class="container mx-auto px-4">
    <div class="text-center mb-16">
      <h2 class="text-4xl md:text-5xl font-bold mb-4">Powerful Features</h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">Everything you need to find and win tenders</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <div class="bg-gray-50 p-8 rounded-2xl card-hover border border-gray-100">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-6 neon-glow">
          <i class="fas fa-bell text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-3">Smart Alerts</h3>
        <p class="text-gray-600">Get instant notifications for tenders matching your business profile and preferences.</p>
      </div>

      <div class="bg-gray-50 p-8 rounded-2xl card-hover border border-gray-100">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-6 neon-glow">
          <i class="fas fa-filter text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-3">Advanced Filtering</h3>
        <p class="text-gray-600">Search by industry, location, value, deadline, and more with powerful filters.</p>
      </div>

      <div class="bg-gray-50 p-8 rounded-2xl card-hover border border-gray-100">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-6 neon-glow">
          <i class="fas fa-file-excel text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-3">Export Data</h3>
        <p class="text-gray-600">Download tender data to Excel for analysis and integration with your systems.</p>
      </div>

      <div class="bg-gray-50 p-8 rounded-2xl card-hover border border-gray-100">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-6 neon-glow">
          <i class="fas fa-hands-helping text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-3">Expert Support</h3>
        <p class="text-gray-600">Get professional guidance to prepare winning bids and navigate the tender process.</p>
      </div>

      <div class="bg-gray-50 p-8 rounded-2xl card-hover border border-gray-100">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-6 neon-glow">
          <i class="fas fa-code text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-3">API Access</h3>
        <p class="text-gray-600">Integrate live tender data directly into your business applications with our API.</p>
      </div>

      <div class="bg-gray-50 p-8 rounded-2xl card-hover border border-gray-100">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-6 neon-glow">
          <i class="fas fa-shield-alt text-white text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold mb-3">Verified Sources</h3>
        <p class="text-gray-600">All tenders are verified from official government and private sector sources.</p>
      </div>
    </div>
  </div>
</section>

<footer class="bg-[#0b1f3b] text-white pt-16 pb-8">
  <div class="container mx-auto px-4">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
      <div>
        <img src="https://ik.imagekit.io/kltovsgah/kentender_logo.png" alt="KenyaTenders" class="w-40 mb-4 invert brightness-0">
        <p class="text-gray-400 mb-6">Kenya's leading tender discovery platform. Find verified government and private sector opportunities.</p>
        <div class="flex gap-3">
          <a href="#" class="w-10 h-10 bg-[#1f4fd8] rounded-lg flex items-center justify-center hover:bg-blue-700"><i class="fab fa-facebook-f"></i></a>
          <a href="#" class="w-10 h-10 bg-[#1f4fd8] rounded-lg flex items-center justify-center hover:bg-blue-700"><i class="fab fa-twitter"></i></a>
          <a href="#" class="w-10 h-10 bg-[#1f4fd8] rounded-lg flex items-center justify-center hover:bg-blue-700"><i class="fab fa-linkedin-in"></i></a>
          <a href="#" class="w-10 h-10 bg-[#1f4fd8] rounded-lg flex items-center justify-center hover:bg-blue-700"><i class="fab fa-instagram"></i></a>
        </div>
      </div>

      <div>
        <h4 class="text-lg font-bold mb-6 text-white">Quick Links</h4>
        <ul class="space-y-3">
          <li><a href="/about" class="text-gray-400 hover:text-white">About Us</a></li>
          <li><a href="/tenders" class="text-gray-400 hover:text-white">All Tenders</a></li>
          <li><a href="/contracts" class="text-gray-400 hover:text-white">Contract Awards</a></li>
          <li><a href="/tenders" class="text-gray-400 hover:text-white">Advanced Search</a></li>
          <li><a href="#" class="text-gray-400 hover:text-white">Pricing Plans</a></li>
          <li><a href="#" class="text-gray-400 hover:text-white">Blogs & News</a></li>
        </ul>
      </div>

      <div>
        <h4 class="text-lg font-bold mb-6 text-white">Resources</h4>
        <ul class="space-y-3">
          <li><a href="#" class="text-gray-400 hover:text-white">How It Works</a></li>
          <li><a href="#" class="text-gray-400 hover:text-white">Publish Tenders</a></li>
          <li><a href="#" class="text-gray-400 hover:text-white">API Documentation</a></li>
          <li><a href="#" class="text-gray-400 hover:text-white">Help Center</a></li>
          <li><a href="#" class="text-gray-400 hover:text-white">Terms of Service</a></li>
          <li><a href="#" class="text-gray-400 hover:text-white">Privacy Policy</a></li>
        </ul>
      </div>

      <div>
        <h4 class="text-lg font-bold mb-6 text-white">Contact Us</h4>
        <ul class="space-y-4">
          <li class="flex items-start">
            <i class="fas fa-envelope text-[#1f4fd8] mr-3 mt-1"></i>
            <div>
              <div class="text-sm text-gray-400">Email</div>
              <a href="mailto:info@kenyatenders.com" class="text-white hover:text-cyan-400">info@kenyatenders.com</a>
            </div>
          </li>
          <li class="flex items-start">
            <i class="fas fa-phone text-[#1f4fd8] mr-3 mt-1"></i>
            <div>
              <div class="text-sm text-gray-400">Phone</div>
              <a href="tel:+254700000000" class="text-white hover:text-cyan-400">+254 700 000 000</a>
            </div>
          </li>
          <li class="flex items-start">
            <i class="fas fa-map-marker-alt text-[#1f4fd8] mr-3 mt-1"></i>
            <div>
              <div class="text-sm text-gray-400">Location</div>
              <p class="text-white">Nairobi, Kenya</p>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <div class="border-t border-gray-700 pt-8 text-center">
      <p class="text-gray-400 text-sm">© 2026 KenyaTenders. All rights reserved.</p>
    </div>
  </div>
</footer>

<button id="scrollTop" onclick="window.scrollTo({top:0, behavior:'smooth'})"
  style="position:fixed; bottom:32px; right:32px; width:56px; height:56px;
         background:linear-gradient(135deg,#0066FF,#0047AB); color:white;
         border:none; border-radius:50%; display:none; align-items:center;
         justify-content:center; box-shadow:0 10px 30px rgba(0,102,255,0.4);
         cursor:pointer; z-index:50; font-size:20px;">
  <i class="fas fa-arrow-up"></i>
</button>

<script>
(function() {
  'use strict';

  // Live clock
  function updateTime() {
    var el = document.getElementById('live-time');
    if (el) el.textContent = new Date().toLocaleString('en-KE', {
      weekday: 'short', year: 'numeric', month: 'short',
      day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }
  updateTime();
  setInterval(updateTime, 30000);

  // Dropdowns
  document.querySelectorAll('.dropdown-toggle').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      e.preventDefault();
      var menu = btn.nextElementSibling;
      document.querySelectorAll('.dropdown-menu').forEach(function(m) {
        if (m !== menu) m.classList.remove('show');
      });
      menu.classList.toggle('show');
      var arrow = btn.querySelector('.dropdown-arrow');
      if (arrow) arrow.classList.toggle('rotate-180');
    });
  });
  document.addEventListener('click', function() {
    document.querySelectorAll('.dropdown-menu').forEach(function(m) { m.classList.remove('show'); });
    document.querySelectorAll('.dropdown-arrow').forEach(function(a) { a.classList.remove('rotate-180'); });
  });

  // Mobile menu
  var mobileBtn = document.getElementById('mobileMenuBtn');
  var mobileMenu = document.getElementById('mobileMenu');
  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      mobileMenu.classList.toggle('hidden');
    });
  }

  // Scroll to top
  var scrollTopBtn = document.getElementById('scrollTop');
  if (scrollTopBtn) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 500) scrollTopBtn.style.display = 'flex';
      else scrollTopBtn.style.display = 'none';
    }, { passive: true });
  }

  // Active nav highlight
  (function initActiveNav() {
    try {
      var path = window.location.pathname || '/';
      var cleanPath = path.replace(/\/$/, '') || '/';
      var matched = false;

      document.querySelectorAll('#mainNav a, #mobileMenu a').forEach(function(a) {
        var href = a.getAttribute('href') || '';
        var cleanHref = href.replace(/\/$/, '') || '/';
        var isMatch = false;

        if (cleanPath === '/' && (cleanHref === '/' || cleanHref === '/home' || cleanHref === 'home')) isMatch = true;
        else if (cleanHref === cleanPath) isMatch = true;
        else if (cleanHref !== '/' && cleanPath.indexOf(cleanHref) === 0) isMatch = true;
        else if ((cleanPath === '/contracts' && cleanHref === '/contract') ||
                 (cleanPath === '/contract' && cleanHref === '/contracts')) isMatch = true;

        if (isMatch) {
          a.classList.add('active');
          a.setAttribute('aria-current', 'page');
          a.style.setProperty('color', '#2563eb', 'important');
          a.style.setProperty('font-weight', '700', 'important');
          a.style.setProperty('border-bottom', '2px solid #2563eb', 'important');
          a.style.setProperty('padding-bottom', '4px', 'important');
          a.style.setProperty('display', 'inline-block', 'important');
          matched = true;

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

      if (!matched && (cleanPath === '/' || cleanPath === '')) {
        var homeLink = document.querySelector('#mainNav a[href="/"]');
        if (homeLink) {
          homeLink.classList.add('active');
          homeLink.style.setProperty('color', '#2563eb', 'important');
          homeLink.style.setProperty('font-weight', '700', 'important');
          homeLink.style.setProperty('border-bottom', '2px solid #2563eb', 'important');
          homeLink.style.setProperty('padding-bottom', '4px', 'important');
          homeLink.style.setProperty('display', 'inline-block', 'important');
        }
      }
    } catch (e) { console.error('Active nav error:', e); }
  })();

})();
</script>
'''