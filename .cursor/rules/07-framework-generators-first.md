---
trigger: always_on
---

Framework creation policy for KenTender:

If a Frappe/Bench generator exists for the requested artifact, use the generator first.
Do not handcraft framework scaffolds.

Mandatory examples:
- Frappe app -> use `bench new-app`
- Frappe site -> use `bench new-site`
- Frappe DocType -> use standard Frappe creation/scaffolding flow
- Framework-managed boilerplate -> generate first, then modify

Rules:
1. Do not manually create a new Frappe app scaffold.
2. Do not manually create a new DocType scaffold from scratch.
3. If command execution is unavailable or unreliable, print the exact command and STOP.
4. Only modify generated files after the scaffold exists.
5. If unsure whether an artifact is framework-managed, ask before writing files.