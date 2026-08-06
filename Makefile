# KenTender monorepo helpers — bench root: /home/midasuser/frappe-bench
# Default site matches sites/common_site_config.json → default_site

SITE ?= kentender.midas.com
BENCH_ROOT ?= /home/midasuser/frappe-bench
KENTENDER_APPS := kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_suppliers,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations,kentender_transparency
INSTALL_ORDER := kentender_core kentender_strategy kentender_budget kentender_procurement kentender_suppliers kentender_governance kentender_compliance kentender_stores kentender_assets kentender_integrations kentender_transparency

.PHONY: help install install-one migrate build build-kentender clear restart doctor list symlinks validate-links smoke ui-smoke ui-workspace-pattern-gate ui-strategy-typography-gate ui-strategy-alignment-ui-gate ui-strategy-role-gate ui-stitch-desk-chrome-gate ui-budget-funding-portfolio-gate ui-budget-funding-register-gate ui-budget-funding-overview-gate ui-budget-funding-lines-gate ui-budget-funding-activity-gate ui-budget-funding-revisions-gate ui-budget-funding-revision-review-gate ui-budget-funding-downstream-gate ui-budget-funding-review-gate ui-budget-funding-audit-gate ui-budget-funding-performance-gate ui-budget-funding-check-reserve-gate ui-budget-role-gate ui-create-demand-strategy-gate ui-civic-ledger-queue-gate ui-civic-ledger-ui01-gate ui-civic-ledger-cfg01-gate ui-civic-ledger-cfg02-gate ui-civic-ledger-cfg03-gate ui-civic-ledger-cfg04-gate ui-civic-ledger-cfg05-gate ui-civic-ledger-cfg06-gate ui-civic-ledger-cfg07-gate ui-civic-ledger-cfg08-gate ui-civic-ledger-cfg09-gate ui-civic-ledger-wg01-gate ui-civic-ledger-wg02-gate ui-civic-ledger-wg03-gate pub-domain-gate ui-publications-gate bw-domain-gate bw-a0-domain-gate bw-a2-domain-gate bw-a3-domain-gate bw-a4-domain-gate bw-manifest-phase1-gate bw-manifest-phase2-gate bw-manifest-phase3-gate bw-manifest-phase4-gate bw-manifest-phase5-gate bw-manifest-phase2-reset bw-manifest-phase2-reseed ui-bidder-a0-gate ui-bidder-a1-gate ui-bidder-a2-gate ui-bidder-a3-gate ui-bidder-a4-gate bw-x100-domain-gate bw-s300-domain-gate ui-bidder-s300-cbq-gate bw-fot-domain-gate ui-bidder-fot-gate bw-statutory-domain-gate ui-bidder-statutory-gate bw-tender-security-domain-gate ui-bidder-tender-security-gate bw-preliminary-domain-gate ui-bidder-preliminary-gate tm2-v1-contamination-audit p11-04-tm2-surface-gate p11-05-tm2-surface-legacy-literal-gate p12-01-scenario-harness x-01-planning-std-poc-gate x-02-no-plain-bench-build-gate x-03-doc9-acceptance-sequence-gate std-verbatim-gate std-step1-gate nssf-calibration-gate e1-nssf-seed-gate e1-nssf-poc-gate seed-stable-platform seed-stable-platform-reset seed-stable-platform-validate seed-demand-to-bidder-journey

help:
	@echo "Targets:"
	@echo "  make install SITE=$(SITE)     — install-app all KenTender apps in order"
	@echo "  make install-one APP=...      — install-app single app"
	@echo "  make migrate SITE=$(SITE)"
	@echo "  make build — desk assets via ./scripts/bench-with-node.sh (Node ≥24; see frappe-bench AGENTS.md)"
	@echo "  make build-kentender — all KenTender apps via bench-with-node.sh"
	@echo "  make clear SITE=$(SITE)"
	@echo "  make restart"
	@echo "  make doctor"
	@echo "  make list SITE=$(SITE)"
	@echo "  make symlinks"
	@echo "  make validate-links"
	@echo "  make smoke SITE=$(SITE) — guard_frappe_scaffolds + Wave 0 smoke tests"
	@echo "  make tm2-v1-contamination-audit SITE=$(SITE) — P11-03 static scan + catalogue (kentender_procurement)"
	@echo "  make p11-04-tm2-surface-gate SITE=$(SITE) — P11-04 TM2 paths must not get_doc/new_doc Procurement Tender"
	@echo "  make p11-05-tm2-surface-legacy-literal-gate SITE=$(SITE) — P11-05 TM2 paths + v2 desk JS must not quote Procurement Tender"
	@echo "  make p12-01-scenario-harness SITE=$(SITE) — P12-01 doc 7 §2 scenario catalog + S01–S13 stub test modules"
	@echo "  make x-01-planning-std-poc-gate SITE=$(SITE) — X-01 planning + STD POC regression slice (tender-management §X)"
	@echo "  make x-02-no-plain-bench-build-gate — X-02 tender-management prompts must not document bare bench asset build (doc 9 §3.1)"
	@echo "  make x-03-doc9-acceptance-sequence-gate — X-03 doc 9 §23.4 KenTender acceptance runbook markers (doc + audit)"
	@echo "  make ui-smoke — Phase La: npm run test:ui:smoke (needs Node, running site, apps/kentender_v1/.env.ui)"
	@echo "  make ui-workspace-pattern-gate — workspace contract tests (selection, scroll, anti-flicker)"
	@echo "  make ui-strategy-typography-gate — Strategy typography + shared plan chrome (Espresso bleed, Manrope/Inter pins)"
	@echo "  make ui-strategy-alignment-ui-gate — Strategy Alignment Stitch UI shell (includes typography gate + full nav)"
	@echo "  make ui-strategy-role-gate — STR-SUP-005 wave 2 (AC matrix + role Playwright)"
	@echo "  make ui-stitch-desk-chrome-gate — Shared Stitch Desk chrome baseline (Win98/select/Espresso) — required before Stitch Desk UI Done"
	@echo "  make ui-budget-funding-portfolio-gate — Budget & Funding portfolio (BUD-UI-01) chrome + layout + Playwright"
	@echo "  make ui-budget-funding-register-gate — Register approved budget (Prompt 2) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-overview-gate — Budget Overview workspace (BUD-UI-03) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-lines-gate — Budget Lines + Line Editor (BUD-UI-04/05) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-activity-gate — Funding Activity (BUD-UI-07) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-revisions-gate — Budget Revisions (BUD-UI-08) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-revision-review-gate — Budget Revision Review (BUD-UI-09) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-downstream-gate — Budget Downstream Usage (BUD-UI-10) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-review-gate — Budget Readiness/Review (BUD-UI-11) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-audit-gate — Budget Audit History (BUD-UI-12) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-performance-gate — Funding Performance (BUD-UI-02) chrome + domain + Playwright"
	@echo "  make ui-budget-funding-check-reserve-gate — Check and Reserve (BUD-UI-06) chrome + domain + Playwright"
	@echo "  make ui-budget-role-gate — BUD-SUP-002 role matrix (API + Playwright capability gating)"
	@echo "  make ui-create-demand-strategy-gate — XMOD-STR-002/003 create-demand strategy + PVC (domain + Playwright)"
	@echo "  make ui-civic-ledger-queue-gate — Civic Ledger queue/list contract (chrome, filters, table footer)"
	@echo "  make ui-civic-ledger-ui01-gate — UI-01 home structural layout + mockup states"
	@echo "  make ui-civic-ledger-cfg01-gate — CFG-01 Tender Profile strip/form/Continue gate"
	@echo "  make ui-civic-ledger-cfg02-gate — CFG-02 Tender Data Sheet strip/form/Continue gate"
	@echo "  make ui-civic-ledger-cfg03-gate — CFG-03 IT Requirements table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg04-gate — CFG-04 Implementation Schedule approach/table/Continue gate"
	@echo "  make ui-civic-ledger-cfg05-gate — CFG-05 System Inventory table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg06-gate — CFG-06 Price Schedule tabs/table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg07-gate — CFG-07 Evaluation Setup tabs/table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg08-gate — CFG-08 Forms & Evidence filters/table/drawer/Continue gate"
	@echo "  make ui-civic-ledger-cfg09-gate — CFG-09 Contract Values tabs/table/drawer/Run Check gate"
	@echo "  make ui-civic-ledger-wg01-gate — WG-01 Readiness Check summary/findings/submit gate"
	@echo "  make ui-civic-ledger-wg02-gate — WG-02 Review & Approval checklist/decision gate"
	@echo "  make ui-civic-ledger-wg03-gate — WG-03 Document Preview (document artifact path) gate"
	@echo "  make pub-domain-gate SITE=$(SITE) — Tender Publications domain API tests"
	@echo "  make ui-publications-gate — Publications A1/A2/A3 Playwright smoke"
	@echo "  make bw-domain-gate SITE=$(SITE) — Bidder workspace A1 domain API tests"
	@echo "  make bw-a0-domain-gate SITE=$(SITE) — Available Tenders (A0) domain tests"
	@echo "  make bw-a2-domain-gate SITE=$(SITE) — Submission Checklist (A2) domain + web route tests"
	@echo "  make bw-a3-domain-gate SITE=$(SITE) — Tender Documents & Addenda (A3) domain + web route tests"
	@echo "  make bw-a4-domain-gate SITE=$(SITE) — Requirement Matrix (A4) domain + web route tests"
	@echo "  make bw-manifest-phase1-gate SITE=$(SITE) — G1 Phase 1 BWMF schemas + NSSF fixture errata"
	@echo "  make bw-manifest-phase2-gate SITE=$(SITE) — G1 Phase 2 schema preflight + persistence"
	@echo "  make bw-manifest-phase3-gate SITE=$(SITE) — G1 Phase 3 deterministic BWMF compiler"
	@echo "  make bw-manifest-phase4-gate SITE=$(SITE) — G1 Phase 4 content-addressed resources"
	@echo "  make bw-manifest-phase5-gate SITE=$(SITE) — G1 Phase 5 governance and atomic publication"
	@echo "  make bw-manifest-phase2-reset SITE=$(SITE) — clear BWMF persistence rows"
	@echo "  make bw-manifest-phase2-reseed SITE=$(SITE) — clear + seed BWMF canonical fixture"
	@echo "  make ui-bidder-a0-gate — A0 Available Tenders Website Playwright smoke"
	@echo "  make ui-bidder-a1-gate — Bidder A1 Published Tender Overview Playwright smoke"
	@echo "  make ui-bidder-a2-gate — A2 Submission Checklist Website Playwright smoke"
	@echo "  make ui-bidder-a3-gate — A3 Tender Documents & Addenda Website Playwright smoke"
	@echo "  make ui-bidder-a4-gate — A4 Requirement Matrix Website Playwright smoke"
	@echo "  make bw-fot-domain-gate SITE=$(SITE) — FoT Review-and-Certify domain + order tests"
	@echo "  make ui-bidder-fot-gate — FoT Review-and-Certify Website Playwright smoke"
	@echo "  make bw-statutory-domain-gate SITE=$(SITE) — Statutory Declarations domain + web tests"
	@echo "  make ui-bidder-statutory-gate — Statutory Declarations Website Playwright smoke"
	@echo "  make bw-tender-security-domain-gate SITE=$(SITE) — Tender Security domain tests"
	@echo "  make ui-bidder-tender-security-gate — Tender Security Website Playwright smoke"
	@echo "  make bw-preliminary-domain-gate SITE=$(SITE) — Preliminary Requirements domain tests"
	@echo "  make ui-bidder-preliminary-gate — Preliminary Requirements Website Playwright smoke"
	@echo "  make bw-qualification-domain-gate SITE=$(SITE) — Qualification and Capability domain tests"
	@echo "  make ui-bidder-qualification-gate — Qualification and Capability Website Playwright smoke"
	@echo "  make bw-technical-proposal-domain-gate SITE=$(SITE) — Technical Proposal domain + layout guard"
	@echo "  make ui-bidder-technical-proposal-gate — Technical Proposal Website Playwright smoke"
	@echo "  make bw-requirements-compliance-domain-gate SITE=$(SITE) — Requirements Compliance domain + layout guard"
	@echo "  make ui-bidder-requirements-compliance-gate — Requirements Compliance Website Playwright smoke"
	@echo "  make bw-price-schedule-domain-gate SITE=$(SITE) — Price Schedule domain + layout guard"
	@echo "  make ui-bidder-price-schedule-gate — Price Schedule Website Playwright smoke"
	@echo "  make bw-final-submission-domain-gate SITE=$(SITE) — Final Submission domain + layout + stitch contracts"
	@echo "  make bw-final-submission-stitch-contract-gate SITE=$(SITE) — Final Submission per-Stitch-file UI contracts (01–05)"
	@echo "  make ui-bidder-final-submission-gate — Final Submission Website Playwright smoke (modal structure)"
	@echo "  make std-verbatim-gate SITE=$(SITE) — BE-14 verbatim extraction + smoke contracts"
	@echo "  make std-step1-gate SITE=$(SITE) — BE-15 Step 1 activation/consumption/render smoke"
	@echo "  make nssf-calibration-gate SITE=$(SITE) — CAL-NSSF golden proof gate"
	@echo "  make e1-nssf-seed-gate SITE=$(SITE) — E1 NSSF seed mapper + preview (subset)"
	@echo "  make e1-nssf-poc-gate SITE=$(SITE) — full E1 PoC: seed + bid APIs + Playwright bidder workspace"
	@echo "  make seed-stable-platform SITE=$(SITE) — load MOH stable platform seed (Works + IT STD)"
	@echo "  make seed-stable-platform-reset SITE=$(SITE) — clear + reload stable platform seed"
	@echo "  make seed-demand-to-bidder-journey SITE=$(SITE) — quiet Demand→CFG→bidder sample"
	@echo "  make seed-stable-platform-validate SITE=$(SITE) — validate stable platform seed only"
	@echo "  make seed-demo-platform-reset SITE=$(SITE) — clean PEs + linked IT STD demo platform seed"
	@echo "  make seed-demo-platform-validate SITE=$(SITE) — validate demo platform seed only"
	@for app in $(INSTALL_ORDER); do \
		echo "Installing $$app on $(SITE)"; \
		cd $(BENCH_ROOT) && bench --site $(SITE) install-app $$app || exit 1; \
	done

install-one:
	@test -n "$(APP)" || (echo "Usage: make install-one APP=kentender_core SITE=..." && exit 1)
	cd $(BENCH_ROOT) && bench --site $(SITE) install-app $(APP)

migrate:
	cd $(BENCH_ROOT) && bench --site $(SITE) migrate

build:
	cd $(BENCH_ROOT) && ./scripts/bench-with-node.sh build

build-kentender:
	cd $(BENCH_ROOT) && ./scripts/bench-with-node.sh build --apps $(KENTENDER_APPS)

clear:
	cd $(BENCH_ROOT) && bench --site $(SITE) clear-cache && bench --site $(SITE) clear-website-cache

restart:
	cd $(BENCH_ROOT) && bench restart

doctor:
	cd $(BENCH_ROOT) && bench doctor

list:
	cd $(BENCH_ROOT) && bench --site $(SITE) list-apps

symlinks:
	cd $(BENCH_ROOT)/apps && \
	ln -sfn kentender_v1/kentender_core kentender_core && \
	ln -sfn kentender_v1/kentender_strategy kentender_strategy && \
	ln -sfn kentender_v1/kentender_budget kentender_budget && \
	ln -sfn kentender_v1/kentender_procurement kentender_procurement && \
	ln -sfn kentender_v1/kentender_governance kentender_governance && \
	ln -sfn kentender_v1/kentender_compliance kentender_compliance && \
	ln -sfn kentender_v1/kentender_stores kentender_stores && \
	ln -sfn kentender_v1/kentender_assets kentender_assets && \
	ln -sfn kentender_v1/kentender_integrations kentender_integrations && \
	ln -sfn kentender_v1/kentender_suppliers kentender_suppliers && \
	ln -sfn kentender_v1/kentender_transparency kentender_transparency

validate-links:
	@test -L $(BENCH_ROOT)/apps/kentender_core
	@test -L $(BENCH_ROOT)/apps/kentender_strategy
	@test -L $(BENCH_ROOT)/apps/kentender_budget
	@test -L $(BENCH_ROOT)/apps/kentender_procurement
	@test -L $(BENCH_ROOT)/apps/kentender_governance
	@test -L $(BENCH_ROOT)/apps/kentender_compliance
	@test -L $(BENCH_ROOT)/apps/kentender_stores
	@test -L $(BENCH_ROOT)/apps/kentender_assets
	@test -L $(BENCH_ROOT)/apps/kentender_integrations
	@test -L $(BENCH_ROOT)/apps/kentender_suppliers
	@test -L $(BENCH_ROOT)/apps/kentender_transparency
	@echo "All KenTender symlinks look present."

smoke:
	cd $(BENCH_ROOT) && python3 apps/kentender_v1/scripts/guard_frappe_scaffolds.py
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_core --module kentender_core.tests.test_wave0_smoke

ui-smoke:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npm run test:ui:smoke

ui-workspace-pattern-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test \
		tests/ui/smoke/dia-landing/dia-pattern-lock.spec.ts

# Fast gate for Strategy CSS/chrome/typography work (Desk Espresso bleed, shared plan header).
ui-strategy-typography-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_strategy.tests.test_strategy_ui_stitch_layout_guard
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		-g "strategy typography resists Desk Espresso|shared plan chrome is identical|shared plan chrome survives soft tab navigation|VC and Measurements section titles" \
		tests/ui/smoke/strategy-alignment/strategy-alignment-nav.spec.ts

# Full Strategy Alignment UI shell — typography + shared Stitch Desk chrome, then nav smoke.
ui-strategy-alignment-ui-gate: ui-strategy-typography-gate ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/strategy-alignment/strategy-alignment-nav.spec.ts

# STR-SUP-005 first wave — AC matrix domain + thin Viewer/Manager Desk evidence.
ui-strategy-role-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_strategy.seeds.strategy_role_users.upsert_strategy_role_users
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_strategy.tests.test_strategy_mvp1_ac_matrix
	cd $(BENCH_ROOT) && bench --site $(SITE) clear-cache
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/strategy-alignment/strategy-role-matrix.spec.ts

# Shared Stitch Desk chrome baseline — must stay green for Strategy/Budget/… canvases.
ui-stitch-desk-chrome-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_core.tests.test_stitch_desk_chrome_gate
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/stitch-desk/stitch-desk-chrome.spec.ts

# BUD-UI-01 Budget & Funding portfolio — chrome baseline + layout guard + Playwright smoke.
ui-budget-funding-portfolio-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-portfolio.spec.ts

# Register approved budget (Prompt 2) — chrome + layout + Playwright create/cancel.
ui-budget-funding-register-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_register
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-register.spec.ts

# BUD-UI-03 Budget Overview workspace — domain + layout/chrome + Playwright.
ui-budget-funding-overview-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_overview
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-overview.spec.ts

# BUD-UI-04 / BUD-UI-05 Budget Lines + Line Editor — domain + layout/chrome + Playwright.
ui-budget-funding-lines-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_lines
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-lines.spec.ts \
		tests/ui/smoke/budget-funding/budget-funding-line-strategy-xmod-str-001.spec.ts

# BUD-UI-07 Funding Activity — domain + layout/chrome + Playwright.
ui-budget-funding-activity-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_funding_activity
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-activity.spec.ts

# BUD-UI-08 Budget Revisions — domain + layout/chrome + Playwright.
ui-budget-funding-revisions-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_revisions
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-revisions.spec.ts

# BUD-UI-09 Budget Revision Review — domain + layout/chrome + Playwright.
ui-budget-funding-revision-review-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_revision_review
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.moh_mvp_v1_portfolio.upsert_moh_mvp_v1_portfolio
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-revision-review.spec.ts

# BUD-UI-10 Downstream Usage — domain + layout/chrome + Playwright.
ui-budget-funding-downstream-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_downstream_usage
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.moh_mvp_v1_portfolio.upsert_moh_mvp_v1_portfolio
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-downstream.spec.ts

# BUD-UI-11 Readiness and Review — domain + layout/chrome + Playwright.
ui-budget-funding-review-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_readiness
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.moh_mvp_v1_portfolio.upsert_moh_mvp_v1_portfolio
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-review.spec.ts

# BUD-UI-12 Audit History — domain + layout/chrome + Playwright.
ui-budget-funding-audit-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_audit
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.moh_mvp_v1_portfolio.upsert_moh_mvp_v1_portfolio
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-audit.spec.ts

# BUD-UI-02 Funding Performance — domain + layout/chrome + Playwright.
ui-budget-funding-performance-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_funding_performance
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.moh_mvp_v1_portfolio.upsert_moh_mvp_v1_portfolio
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-performance.spec.ts

# BUD-UI-06 Check and Reserve — domain + layout/chrome + Playwright.
ui-budget-funding-check-reserve-gate: ui-stitch-desk-chrome-gate
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_check_reserve
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_ui_stitch_layout_guard
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.moh_mvp_v1_portfolio.upsert_moh_mvp_v1_portfolio
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-check-reserve.spec.ts

# BUD-SUP-002 — role matrix API + Playwright (Admin chrome smokes unchanged).
ui-budget-role-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.budget_role_users.upsert_budget_role_users
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_budget.tests.test_budget_role_matrix
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_budget.seeds.budget_role_matrix_ui_prep.prepare_budget_role_matrix_ui
	cd $(BENCH_ROOT) && bench --site $(SITE) clear-cache
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/budget-funding/budget-funding-role-matrix.spec.ts


# XMOD-STR-002 / 003 — create-demand Strategy target + PVC Review E2E.
ui-create-demand-strategy-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_procurement.demand_intake.tests.test_demand_strategy_readiness
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests \
		--module kentender_strategy.tests.test_strategy_mvp1_ac_matrix
	cd $(BENCH_ROOT) && bench --site $(SITE) clear-cache
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/create-demand/create-demand-strategy-xmod-str-002.spec.ts \
		tests/ui/smoke/create-demand/create-demand-pvc-xmod-str-003.spec.ts \
		tests/ui/smoke/create-demand/create-demand-wizard.spec.ts

ui-civic-ledger-queue-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/kt-cl-queue-pattern-lock.spec.ts \
		tests/ui/smoke/publications/a2-publications-queue.spec.ts

ui-civic-ledger-ui01-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/ui01-layout-contract.spec.ts \
		tests/ui/smoke/it-std-wizard/ui01-home.spec.ts \
		tests/ui/smoke/it-std-wizard/ui01-mockup-states.spec.ts

ui-civic-ledger-cfg01-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg01-tender-profile.spec.ts

ui-civic-ledger-cfg02-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg02-tender-data-sheet.spec.ts

ui-civic-ledger-cfg03-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg03-it-requirements.spec.ts

ui-civic-ledger-cfg04-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg04-implementation-schedule.spec.ts

ui-civic-ledger-cfg05-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg05-system-inventory.spec.ts

ui-civic-ledger-cfg06-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg06-price-schedule.spec.ts

ui-civic-ledger-cfg07-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg07-evaluation-setup.spec.ts

ui-civic-ledger-cfg08-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg08-forms-and-evidence.spec.ts

ui-civic-ledger-cfg09-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/cfg09-contract-values.spec.ts

ui-civic-ledger-wg01-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/wg01-readiness.spec.ts

ui-civic-ledger-wg02-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/wg02-review.spec.ts

ui-civic-ledger-wg03-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/wg03-document-preview.spec.ts

pub-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_publication_setup_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_configuration_document_preview_api

ui-publications-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/publications/a1-package-review.spec.ts \
		tests/ui/smoke/publications/a2-publications-queue.spec.ts \
		tests/ui/smoke/publications/a3-publication-setup.spec.ts

bid-submissions-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bid_submissions_api

ui-bid-submissions-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bid-submissions/officer-bid-submissions.spec.ts

bw-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_published_tender_overview_api

bw-a0-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_available_tenders_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_published_tender_overview_web

ui-bidder-a0-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a0-available-tenders.spec.ts

ui-bidder-a1-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a1-published-tender-overview.spec.ts

bw-a2-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_submission_checklist_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_submission_checklist_web

ui-bidder-a2-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a2-submission-checklist.spec.ts

bw-a3-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_tender_documents_addenda_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_tender_documents_addenda_web
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bidder_presentation_boundary

ui-bidder-a3-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a3-documents-addenda.spec.ts

bw-x100-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_x100_evidence_and_issues

bw-s300-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_s300_confidential_business_questionnaire

ui-bidder-s300-cbq-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/s300-cbq.spec.ts

bw-fot-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_fot_review_certify
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_it_std_template_fot_slice
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_f0_foundation

ui-bidder-fot-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/fot-review-certify.spec.ts

bw-statutory-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_statutory_declarations

ui-bidder-statutory-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/statutory-declarations.spec.ts

bw-tender-security-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_tender_security

ui-bidder-tender-security-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/tender-security.spec.ts

bw-preliminary-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_preliminary_requirements

ui-bidder-preliminary-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/preliminary-requirements.spec.ts

bw-qualification-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_qualification_and_capability
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_qualification_stitch_layout_guard

ui-bidder-qualification-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/qualification-and-capability.spec.ts

bw-technical-proposal-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_technical_proposal
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_technical_proposal_stitch_layout_guard

ui-bidder-technical-proposal-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/technical-proposal.spec.ts

bw-requirements-compliance-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_requirements_compliance
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_requirements_compliance_stitch_layout_guard

ui-bidder-requirements-compliance-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/requirements-compliance.spec.ts

bw-price-schedule-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_lean_price_schedule
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_price_schedule_stitch_layout_guard

ui-bidder-price-schedule-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/price-schedule.spec.ts

bw-final-submission-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_final_submission_readiness
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_final_submission_stitch_layout_guard
	$(MAKE) bw-final-submission-stitch-contract-gate SITE=$(SITE)

.PHONY: bw-final-submission-stitch-contract-gate
bw-final-submission-stitch-contract-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bidder_stitch_contract_gate

ui-bidder-final-submission-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 --retries=0 \
		tests/ui/smoke/bidder-workspace/final-submission.spec.ts

bw-a4-domain-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_requirement_matrix_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_requirement_matrix_web

ui-bidder-a4-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/bidder-workspace/a4-requirement-matrix.spec.ts

bw-manifest-phase1-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_schema_conformance_phase1
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_nssf_fixture_errata_phase1

bw-manifest-phase2-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_schema_preflight_phase2
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_persistence_phase2
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_persistence_phase2b
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_persistence_phase2c

bw-manifest-phase3-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_compiler_phase3
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_compile_service_phase3

bw-manifest-phase4-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_resource_oracle_phase4
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_resource_verifier_phase4a
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_materialize_phase4

bw-manifest-phase5-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_bwmf_governance_phase5

bw-manifest-phase2-reset:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture.clear_bwmf_canonical_fixture

bw-manifest-phase2-reseed:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture.seed_bwmf_canonical_fixture

ui-std-config-gate:
	@echo "STD Module POC archived (2026-07). Use: make verify-std-archived && npm run test:ui:smoke:std-module-retired"
	@exit 1

verify-std-archived:
	chmod +x $(BENCH_ROOT)/apps/kentender_v1/scripts/verify-std-archived.sh
	$(BENCH_ROOT)/apps/kentender_v1/scripts/verify-std-archived.sh

ui-std-module-retired-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && npm run test:ui:smoke:std-module-retired

tm2-v1-contamination-audit:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_03_tm2_v1_contamination_audit

p11-04-tm2-surface-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender

p11-05-tm2-surface-legacy-literal-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_management.tests.test_p11_05_tm2_surface_no_procurement_tender_literal

p12-01-scenario-harness:
	SITE=$(SITE) $(BENCH_ROOT)/scripts/p12_01_tm2_works_scenario_harness.sh

x-01-planning-std-poc-gate:
	SITE=$(SITE) $(BENCH_ROOT)/scripts/x_01_planning_std_poc_regression_gate.sh

x-02-no-plain-bench-build-gate:
	$(BENCH_ROOT)/scripts/x_02_tender_management_docs_no_plain_bench_build_gate.sh

x-03-doc9-acceptance-sequence-gate:
	$(BENCH_ROOT)/scripts/x_03_doc9_section_23_4_acceptance_sequence_gate.sh

std-verbatim-gate:
	cd $(BENCH_ROOT)/apps/kentender_v1 && PYTHONPATH=. python3 scripts/std_extraction/verbatim/run.py
	cd $(BENCH_ROOT)/apps/kentender_v1 && PYTHONPATH=. python3 scripts/std_extraction/build_package.py v1_1
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_verbatim_extract_clauses
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_record_mapper_verbatim_fields
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_14_verbatim_smoke_contracts

std-step1-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_12_smoke_contracts
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_14_verbatim_smoke_contracts
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption

# Short --test names required (FQ dotted paths match zero tests under this runner).
# Fail the gate if any invocation reports "Ran 0 tests".
nssf-calibration-gate:
	@set -e; \
	for t in \
		test_cal_nssf_001_fixture_import_without_master_mutation \
		test_cal_nssf_002_golden_bind \
		test_cal_nssf_003_tds_values_validate_against_fixture \
		test_cal_nssf_012_render_uses_official_locked_text \
		test_cal_nssf_013_fixture_activation_blocked; do \
		echo ">>> nssf-calibration-gate: $$t"; \
		out=$$(cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
			--module kentender_procurement.std_engine.tests.test_be_15_step1_activation_consumption \
			--test "$$t" 2>&1); \
		status=$$?; \
		printf '%s\n' "$$out"; \
		if printf '%s\n' "$$out" | grep -Eq 'Ran 0 tests?'; then \
			echo "ERROR: nssf-calibration-gate matched zero tests for $$t" >&2; \
			exit 1; \
		fi; \
		if ! printf '%s\n' "$$out" | grep -Eq 'Ran [1-9][0-9]* tests?'; then \
			echo "ERROR: nssf-calibration-gate did not report a non-zero test run for $$t" >&2; \
			exit 1; \
		fi; \
		if [ $$status -ne 0 ]; then \
			echo "ERROR: nssf-calibration-gate failed for $$t (exit $$status)" >&2; \
			exit $$status; \
		fi; \
		if ! printf '%s\n' "$$out" | grep -Eq '^OK$$'; then \
			echo "ERROR: nssf-calibration-gate did not end OK for $$t" >&2; \
			exit 1; \
		fi; \
	done

e1-nssf-seed-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_fixture_mapper
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_seed

e1-nssf-poc-gate:
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.std_engine.tests.test_form_locked_text_activation
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_preview_presentation
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_fixture_mapper
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_schema_compiler
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_e1_nssf_seed
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_configuration_document_preview_api
	cd $(BENCH_ROOT) && bench --site $(SITE) run-tests --app kentender_procurement \
		--module kentender_procurement.tender_configurations.tests.test_electronic_bid_submission
	cd $(BENCH_ROOT)/apps/kentender_v1 && npx playwright test --workers=1 \
		tests/ui/smoke/it-std-wizard/e1-bidder-workspace.spec.ts

seed-stable-platform:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.run

seed-stable-platform-reset:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.run --kwargs '{"reset": true}'

seed-stable-platform-validate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_stable_platform.validate

seed-demand-to-bidder-journey:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute \
		kentender_procurement.tender_configurations.seed.demand_to_bidder_journey_sample.run

seed-demo-platform:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_demo_platform.run --kwargs '{"reset": false}'

seed-demo-platform-reset:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_demo_platform.run --kwargs '{"reset": true}'

seed-demo-platform-validate:
	cd $(BENCH_ROOT) && bench --site $(SITE) execute kentender_core.seeds.seed_demo_platform.validate
