---
trigger: glob
globs:
  - "apps/**/doctype/**/*.py"
  - "apps/**/services/**/*.py"
  - "apps/**/api/**/*.py"
---

Frappe implementation rules for KenTender:
- DocType layer = persistence + thin validation only
- services/ = business orchestration and critical actions
- api/ = explicit endpoints only
- utils/ = lightweight helpers
- UI/client code must call services, not embed business logic
- Do not bury workflow logic in UI handlers