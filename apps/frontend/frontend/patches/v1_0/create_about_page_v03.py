import frappe


def execute():
    create_about_page()


def create_about_page():
    frappe.db.sql("DELETE FROM `tabWeb Page` WHERE name = 'about' OR route = 'about'")
    frappe.db.commit()

    page = frappe.new_doc("Web Page")
    page.title = "About Us"
    page.route = "about"
    page.published = 1
    page.content_type = "HTML"
    page.full_width = 1
    page.show_title = 0
    page.main_section_html = PAGE_HTML
    page.insert(ignore_permissions=True, ignore_if_duplicate=True)

    frappe.db.commit()
    frappe.clear_cache()
    print("✅ About page created at /about")


PAGE_HTML = r"""
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
  position: absolute; top: 100%; left: 0; background: white;
  border: 1px solid #e5e7eb; border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1); min-width: 200px;
  padding: 8px 0; margin-top: 8px; opacity: 0; visibility: hidden;
  transform: translateY(-10px); transition: all 0.3s ease; z-index: 9999;
}
.dropdown-menu.show { opacity: 1; visibility: visible; transform: translateY(0); }
.dropdown-item { display: block; padding: 12px 20px; color: #1f2937; text-decoration: none; font-size: 14px; transition: all 0.2s ease; }
.dropdown-item:hover { background: #f3f4f6; color: #0066ff; padding-left: 24px; }
.dropdown-arrow { transition: transform 0.3s ease; font-size: 0.75rem; }
.dropdown-arrow.rotate-180 { transform: rotate(180deg); }

@media (min-width: 768px) {
  .dropdown:hover .dropdown-menu { opacity: 1 !important; visibility: visible !important; transform: translateY(0) !important; }
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

.pattern-grid {
  background-image: linear-gradient(rgba(0,102,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,102,255,0.05) 1px, transparent 1px);
  background-size: 50px 50px;
}
.pattern-dots { background-image: radial-gradient(circle, rgba(0,102,255,0.1) 1px, transparent 1px); background-size: 30px 30px; }
.card-hover { transition: all 0.3s ease; }
.card-hover:hover { transform: translateY(-6px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
.blob { position: absolute; border-radius: 50%; filter: blur(60px); opacity: 0.3; animation: float 8s ease-in-out infinite; }
.blob-1 { width: 400px; height: 400px; background: #0066FF; top: -200px; right: -200px; }
.blob-2 { width: 300px; height: 300px; background: #0047AB; bottom: -150px; left: -150px; animation-delay: -4s; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
#mobileMenu.hidden { display: none !important; }
</style>

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
  <div class="absolute inset-0 pattern-dots opacity-30"></div>
  <div class="blob blob-1"></div>
  <div class="blob blob-2"></div>

  <div class="container mx-auto px-4 relative z-10">
    <div class="max-w-6xl mx-auto">
      <div class="text-center mb-20">
        <h1 class="text-4xl md:text-5xl font-bold text-gray-800 mb-6 leading-tight">
          About <span class="text-blue-600">KenyaTenders</span>
        </h1>
        <p class="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto">
          Empowering businesses across Kenya with transparent, real-time access to verified procurement opportunities
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-20">
        <div class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
          <div class="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-6">
            <i class="fas fa-bullseye text-white text-2xl"></i>
          </div>
          <h2 class="text-2xl font-bold text-gray-900 mb-4">Our Mission</h2>
          <p class="text-gray-600 leading-relaxed">
            To democratize access to public and private sector tenders in Kenya by providing a modern,
            reliable, and user-friendly platform that connects businesses with opportunities—driving
            economic growth and transparency.
          </p>
        </div>

        <div class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
          <div class="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-6">
            <i class="fas fa-eye text-white text-2xl"></i>
          </div>
          <h2 class="text-2xl font-bold text-gray-900 mb-4">Our Vision</h2>
          <p class="text-gray-600 leading-relaxed">
            To become the definitive procurement intelligence platform in East Africa, empowering
            thousands of businesses to compete fairly and win contracts that transform communities and industries.
          </p>
        </div>
      </div>

      <div class="bg-[#0b1f3b] rounded-3xl p-12 mb-20 text-center">
        <h2 class="text-3xl md:text-4xl font-bold text-white mb-8">Our Story</h2>
        <p class="text-lg text-cyan-100 max-w-4xl mx-auto leading-relaxed">
          Founded in Nairobi, KenyaTenders was born from the frustration of navigating fragmented and
          outdated tender information sources. We saw businesses—especially SMEs—missing out on life-changing
          opportunities due to lack of timely, accurate data. Today, we aggregate, verify, and deliver thousands
          of tenders daily from government portals, county websites, and private institutions, helping over
          5,000 users stay ahead in a competitive market.
        </p>
      </div>

      <div class="text-center mb-12">
        <h2 class="text-3xl md:text-4xl font-bold text-gray-800 mb-4">Our Core Values</h2>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 card-hover text-center">
          <div class="w-14 h-14 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-6">
            <i class="fas fa-shield-alt text-white text-xl"></i>
          </div>
          <h3 class="text-xl font-bold text-gray-800 mb-3">Transparency</h3>
          <p class="text-gray-600">Every tender is sourced and verified from official channels—no guesswork.</p>
        </div>

        <div class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 card-hover text-center">
          <div class="w-14 h-14 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-6">
            <i class="fas fa-bolt text-white text-xl"></i>
          </div>
          <h3 class="text-xl font-bold text-gray-800 mb-3">Speed</h3>
          <p class="text-gray-600">Real-time updates and instant alerts so you never miss a deadline.</p>
        </div>

        <div class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 card-hover text-center">
          <div class="w-14 h-14 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-6">
            <i class="fas fa-users text-white text-xl"></i>
          </div>
          <h3 class="text-xl font-bold text-gray-800 mb-3">Empowerment</h3>
          <p class="text-gray-600">Tools and support that level the playing field for businesses of all sizes.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<script>
(function() {
  'use strict';
  function updateTime() {
    var el = document.getElementById('live-time');
    if (el) el.textContent = new Date().toLocaleString();
  }
  updateTime();
  setInterval(updateTime, 1000);

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

  // Active nav
  (function initActiveNav() {
    try {
      var path = window.location.pathname || '/';
      var cleanPath = path.replace(/\/$/, '') || '/';
      document.querySelectorAll('#mainNav a, #mobileMenu a').forEach(function(a) {
        var href = a.getAttribute('href') || '';
        var cleanHref = href.replace(/\/$/, '') || '/';
        var isMatch = (cleanHref === cleanPath) || (cleanHref !== '/' && cleanPath.indexOf(cleanHref) === 0);
        if (cleanPath === '/' && (cleanHref === '/' || cleanHref === '/home')) isMatch = true;

        if (isMatch) {
          a.classList.add('active');
          a.setAttribute('aria-current', 'page');
          a.style.setProperty('color', '#2563eb', 'important');
          a.style.setProperty('font-weight', '700', 'important');
          a.style.setProperty('border-bottom', '2px solid #2563eb', 'important');
          a.style.setProperty('padding-bottom', '4px', 'important');
          a.style.setProperty('display', 'inline-block', 'important');
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