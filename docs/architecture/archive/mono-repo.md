# kentender_v1 recommended layout

/home/midasuser/frappe-bench/

├── apps/

│ ├── frappe/

│ ├── erpnext/

│ ├── payments/ # if used

│ ├── kentender_v1/ # monorepo container only

│ │ ├── .git/

│ │ ├── docs/

│ │ │ ├── architecture/

│ │ │ ├── module-prds/

│ │ │ ├── prompts/

│ │ │ ├── delivery/

│ │ │ └── test-contracts/

│ │ ├── scripts/

│ │ ├── Makefile

│ │ ├── AGENTS.md

│ │ ├── .windsurf/

│ │ │ ├── rules/

│ │ │ └── workflows/

│ │ ├── kentender_core/

│ │ ├── kentender_strategy/

│ │ ├── kentender_budget/

│ │ ├── kentender_procurement/

│ │ ├── kentender_governance/

│ │ ├── kentender_compliance/

│ │ ├── kentender_stores/

│ │ ├── kentender_assets/

│ │ └── kentender_integrations/

│ ├── kentender_core -> kentender_v1/kentender_core

│ ├── kentender_strategy -> kentender_v1/kentender_strategy

│ ├── kentender_budget -> kentender_v1/kentender_budget

│ ├── kentender_procurement -> kentender_v1/kentender_procurement

│ ├── kentender_governance -> kentender_v1/kentender_governance

│ ├── kentender_compliance -> kentender_v1/kentender_compliance

│ ├── kentender_stores -> kentender_v1/kentender_stores

│ ├── kentender_assets -> kentender_v1/kentender_assets

│ └── kentender_integrations -> kentender_v1/kentender_integrations

├── sites/

│ ├── apps.txt

│ └── kentender.local/

└── env/

# Symlink commands

Run these from:

cd /home/midasuser/frappe-bench/apps

Then:

ln -s kentender_v1/kentender_core kentender_core  
ln -s kentender_v1/kentender_strategy kentender_strategy  
ln -s kentender_v1/kentender_budget kentender_budget  
ln -s kentender_v1/kentender_procurement kentender_procurement  
ln -s kentender_v1/kentender_governance kentender_governance  
ln -s kentender_v1/kentender_compliance kentender_compliance  
ln -s kentender_v1/kentender_stores kentender_stores  
ln -s kentender_v1/kentender_assets kentender_assets  
ln -s kentender_v1/kentender_integrations kentender_integrations

Check:

ls -l /home/midasuser/frappe-bench/apps

**Install order**

Use your dependency chain. From your architecture:

- core → strategy → budget → procurement → stores → assets
- governance/compliance/integrations are side apps consuming published interfaces.

So install in this order:

bench --site kentender.local install-app kentender_core  
bench --site kentender.local install-app kentender_strategy  
bench --site kentender.local install-app kentender_budget  
bench --site kentender.local install-app kentender_procurement  
bench --site kentender.local install-app kentender_governance  
bench --site kentender.local install-app kentender_compliance  
bench --site kentender.local install-app kentender_stores  
bench --site kentender.local install-app kentender_assets  
bench --site kentender.local install-app kentender_integrations

**sites/apps.txt**

Make sure sites/apps.txt contains the real apps, not kentender_v1:

frappe  
erpnext  
kentender_core  
kentender_strategy  
kentender_budget  
kentender_procurement  
kentender_governance  
kentender_compliance  
kentender_stores  
kentender_assets  
kentender_integrations

**Makefile**

Put this at:

/home/midasuser/frappe-bench/apps/kentender_v1/Makefile

SITE ?= kentender.local  
<br/>KENTENDER_APPS = kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations  
<br/>INSTALL_ORDER = kentender_core kentender_strategy kentender_budget kentender_procurement kentender_governance kentender_compliance kentender_stores kentender_assets kentender_integrations  
<br/>.PHONY: help install install-one migrate build build-kentender clear restart doctor list symlinks validate-links  
<br/>help:  
@echo "Targets:"  
@echo " make install SITE=kentender.local"  
@echo " make migrate SITE=kentender.local"  
@echo " make build"  
@echo " make build-kentender"  
@echo " make clear SITE=kentender.local"  
@echo " make restart"  
@echo " make doctor"  
@echo " make list"  
@echo " make symlinks"  
@echo " make validate-links"  
<br/>install:  
@for app in $(INSTALL_ORDER); do \\  
echo "Installing $$app on $(SITE)"; \\  
cd /home/midasuser/frappe-bench && bench --site $(SITE) install-app $$app || exit 1; \\  
done  
<br/>migrate:  
cd /home/midasuser/frappe-bench && bench --site $(SITE) migrate  
<br/>build:  
cd /home/midasuser/frappe-bench && bench build  
<br/>build-kentender:  
cd /home/midasuser/frappe-bench && bench build --apps $(KENTENDER_APPS)  
<br/>clear:  
cd /home/midasuser/frappe-bench && bench --site $(SITE) clear-cache && bench --site $(SITE) clear-website-cache  
<br/>restart:  
cd /home/midasuser/frappe-bench && bench restart  
<br/>doctor:  
cd /home/midasuser/frappe-bench && bench doctor  
<br/>list:  
cd /home/midasuser/frappe-bench && bench --site $(SITE) list-apps  
<br/>symlinks:  
cd /home/midasuser/frappe-bench/apps && \\  
ln -sfn kentender_v1/kentender_core kentender_core && \\  
ln -sfn kentender_v1/kentender_strategy kentender_strategy && \\  
ln -sfn kentender_v1/kentender_budget kentender_budget && \\  
ln -sfn kentender_v1/kentender_procurement kentender_procurement && \\  
ln -sfn kentender_v1/kentender_governance kentender_governance && \\  
ln -sfn kentender_v1/kentender_compliance kentender_compliance && \\  
ln -sfn kentender_v1/kentender_stores kentender_stores && \\  
ln -sfn kentender_v1/kentender_assets kentender_assets && \\  
ln -sfn kentender_v1/kentender_integrations kentender_integrations  
<br/>validate-links:  
@test -L /home/midasuser/frappe-bench/apps/kentender_core  
@test -L /home/midasuser/frappe-bench/apps/kentender_strategy  
@test -L /home/midasuser/frappe-bench/apps/kentender_budget  
@test -L /home/midasuser/frappe-bench/apps/kentender_procurement  
@test -L /home/midasuser/frappe-bench/apps/kentender_governance  
@test -L /home/midasuser/frappe-bench/apps/kentender_compliance  
@test -L /home/midasuser/frappe-bench/apps/kentender_stores  
@test -L /home/midasuser/frappe-bench/apps/kentender_assets  
@test -L /home/midasuser/frappe-bench/apps/kentender_integrations  
@echo "All Kentender symlinks look present."

**Useful scripts instead of raw Bench commands**

Also add:

**scripts/dev-build.sh**

#!/usr/bin/env bash  
set -euo pipefail  
cd /home/midasuser/frappe-bench  
bench build --apps kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations

**scripts/dev-migrate.sh**

#!/usr/bin/env bash  
set -euo pipefail  
SITE="${1:-kentender.local}"  
cd /home/midasuser/frappe-bench  
bench --site "$SITE" migrate

**scripts/dev-refresh.sh**

#!/usr/bin/env bash  
set -euo pipefail  
SITE="${1:-kentender.local}"  
cd /home/midasuser/frappe-bench  
bench --site "$SITE" migrate  
bench build --apps kentender_core,kentender_strategy,kentender_budget,kentender_procurement,kentender_governance,kentender_compliance,kentender_stores,kentender_assets,kentender_integrations  
bench --site "$SITE" clear-cache  
bench --site "$SITE" clear-website-cache

**Windsurf rule you need**

Put this in your Windsurf rules or root AGENTS.md:

KenTender repo structure rules:  
<br/>\- apps/kentender_v1 is a monorepo container only.  
\- The real Frappe apps are the kentender_\* apps.  
\- Bench commands must run from /home/midasuser/frappe-bench.  
\- Do not treat kentender_v1 as a parent Frappe app.  
\- For build/migrate/install flows, use Makefile targets or scripts in apps/kentender_v1/scripts.  
\- If a command affects Kentender broadly, prefer:  
\- make -C /home/midasuser/frappe-bench/apps/kentender_v1 build-kentender  
\- make -C /home/midasuser/frappe-bench/apps/kentender_v1 migrate SITE=kentender.local

**Best editor root**

For Windsurf, open either:

- /home/midasuser/frappe-bench/apps/kentender_v1 for Kentender-only work
- or /home/midasuser/frappe-bench if you want full bench awareness

But Bench commands should still run from:

/home/midasuser/frappe-bench