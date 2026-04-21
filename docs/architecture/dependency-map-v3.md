# KenTender dependency map (v3)

## Linear chain (downstream only)

```
kentender_core
  → kentender_strategy
  → kentender_budget
  → kentender_procurement
  → kentender_stores
  → kentender_assets
```

**Rules:** no upstream imports from a downstream app; no direct cross-app database writes — use services and published APIs.

## Side apps

| App | Relationship |
|-----|----------------|
| `kentender_suppliers` | Depends on `kentender_core`; **referenced by** `kentender_procurement` (supplier identity and qualification — not owned by procurement). |
| `kentender_governance` | Consumes published interfaces; approvals/delegation framework. |
| `kentender_compliance` | Policy/regulatory overlays; evaluates against domain data. |
| `kentender_integrations` | External systems (IFMIS, payments, registries); no core business-rule ownership. |
| `kentender_transparency` | **Read-only / publish-only** disclosure; does not drive transactional state. |

## Known follow-ups

- After new apps are installed on a site, validate `hooks.py` `required_apps` and Frappe app dependency metadata if used.
- Deep-import audits: re-run `grep -r "import kentender_"` across apps when adding major features; fix any illegal upstream imports.
