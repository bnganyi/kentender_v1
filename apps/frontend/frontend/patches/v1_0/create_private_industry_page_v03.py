import frappe


def execute():
    create_private_industry_page()


def create_private_industry_page():
    frappe.db.sql("DELETE FROM `tabWeb Page` WHERE name = 'industry/private' OR route = 'industry/private'")
    frappe.db.commit()

    page = frappe.new_doc("Web Page")
    page.title = "Private Sector Procurement Module"
    page.route = "industry/private"
    page.published = 1
    page.content_type = "HTML"
    page.full_width = 1
    page.show_title = 0
    page.main_section_html = PAGE_HTML
    page.insert(ignore_permissions=True, ignore_if_duplicate=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("✅ Private Sector page created at /industry/private")


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

.pattern-dots { background-image: radial-gradient(circle, rgba(0,102,255,0.1) 1px, transparent 1px); background-size: 30px 30px; }
.pattern-grid {
  background-image:
    linear-gradient(rgba(0,102,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,102,255,0.05) 1px, transparent 1px);
  background-size: 50px 50px;
}

.glass { backdrop-filter: blur(20px); border:1px solid rgba(255,255,255,0.2); }

.card-hover { transition: all 0.4s cubic-bezier(0.4,0,0.2,.5); position:relative; overflow:hidden; }
.card-hover:hover { transform: translateY(-8px); box-shadow: 0 20px 30px rgba(22,95,206,0.2); }

.blob { position:absolute; border-radius:50%; filter: blur(60px); opacity:0.3; animation: float 8s ease-in-out infinite; }
.blob-1 { width:400px; height:400px; background: var(--primary-blue); top:-200px; right:-200px; }
.blob-2 { width:300px; height:300px; background: var(--deep-blue); bottom:-150px; left:-150px; animation-delay:-4s; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }

@keyframes fadeInUp { from { opacity:0; transform: translateY(30px); } to { opacity:1; transform: translateY(0); } }
.animate-in { animation: fadeInUp 0.8s ease-out forwards; }

.mono { font-family:'Space Mono', monospace; }

.neon-glow {
  box-shadow: 0 0 20px rgba(2,46,112,0.3),
              0 0 40px rgba(0,102,255,0.2),
              0 0 60px rgba(0,102,255,0.1);
}

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

body.loading { overflow:hidden; }
body:not(.loading) { overflow:visible; }
#loadingOverlay {
  position:fixed; inset:0; background:white;
  display:flex; align-items:center; justify-content:center;
  z-index:9999; opacity:1; transition: opacity 0.3s ease-out;
}
body:not(.loading) #loadingOverlay { opacity:0; pointer-events:none; }
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

   <div class="hidden md:block" style="display:block !important;">
  <a href="/login" 
     class="btn-primary text-sm"
     style="display:inline-flex !important;
            visibility:visible !important;
            opacity:1 !important;
            background:linear-gradient(135deg,#0047AB,#003580) !important;
            color:#ffffff !important;
            padding:12px 24px !important;
            border-radius:10px !important;
            font-weight:600 !important;
            font-size:14px !important;
            text-decoration:none !important;
            align-items:center !important;
            gap:8px !important;
            white-space:nowrap !important;
            min-width:180px !important;
            justify-content:center !important;">
    <i class="fas fa-rocket" style="color:#ffffff !important;"></i>
    <span style="color:#ffffff !important;">Start Free Trial</span>
  </a>
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

<section class="relative py-24 overflow-hidden">
  <div class="absolute inset-0 pattern-grid opacity-90"></div>
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>

  <div class="container mx-auto px-6 relative z-10">
    <div class="max-w-8xl mx-auto text-center">
      <div class="animate-in mb-12">
        <h1 class="text-3xl md:text-5xl mt-6 font-bold text-gray-600 mb-8 leading-tight">
          Private Sector Procurement<br>&amp; Contract Administration Module
        </h1>
        <p class="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto">
          Automates private sector procurement and sourcing activities
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16 animate-in" style="animation-delay: 0.2s;">
        <div class="glass rounded-2xl p-8 text-left card-hover bg-black/5">
          <div class="flex items-start gap-4">
            <i class="fas fa-sitemap text-cyan-600 text-3xl mt-1"></i>
            <div>
              <h3 class="text-2xl font-bold text-gray-800 mb-3">Flexible Workflows</h3>
              <p class="text-lg text-gray-600">Supports flexible approval workflows and supplier management</p>
            </div>
          </div>
        </div>

        <div class="glass rounded-2xl p-8 text-left card-hover bg-black/5">
          <div class="flex items-start gap-4">
            <i class="fas fa-file-contract text-cyan-600 text-3xl mt-1"></i>
            <div>
              <h3 class="text-2xl font-bold text-gray-800 mb-3">Contract Management</h3>
              <p class="text-lg text-gray-600">Manages contracts, renewals, and performance tracking</p>
            </div>
          </div>
        </div>

        <div class="glass rounded-2xl p-8 text-left card-hover bg-black/5">
          <div class="flex items-start gap-4">
            <i class="fas fa-chart-line text-cyan-600 text-3xl mt-1"></i>
            <div>
              <h3 class="text-2xl font-bold text-gray-800 mb-3">Operational Excellence</h3>
              <p class="text-lg text-gray-600">Improves efficiency, cost control, and operational visibility</p>
            </div>
          </div>
        </div>
      </div>

      <div class="animate-in" style="animation-delay: 0.4s;">
        <a href="https://eprivate.midas.co.ke/#login"
           class="inline-flex items-center bg-blue-800 py-3 px-6 rounded-full text-white font-semibold hover:bg-blue-700 transition-colors gap-3 neon-glow">
          <i class="fas fa-rocket mr-3"></i> Get Started
        </a>
        <p class="text-gray-600 mt-10 text-lg">Streamline your private sector procurement today</p>
      </div>
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