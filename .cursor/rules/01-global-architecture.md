---
trigger: model_decision
description: Use when touching app boundaries, imports, architecture, APIs, services, workflows, or multiple apps.
---

KenTender architecture constraints:
- Allowed app set is fixed.
- Respect dependency direction.
- Do not add new apps or move ownership casually.
- Cross-app interaction must use explicit APIs/services.
- Keep business workflows in services/, not DocType controllers.
- Keep cross-cutting controls in kentender_core.
- Do not create hidden coupling or deep cross-app imports.

Read:
- docs/architecture/kentender_architecture_rules_v3.md
- docs/architecture/global-architecture-v3.md