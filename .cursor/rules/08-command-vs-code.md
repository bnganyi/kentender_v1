---
trigger: always_on
---

Command-vs-code policy:

Use a framework command when the task creates a framework-managed artifact.
Use code edits only when the scaffold already exists.

Creation tasks that require commands:
- new app
- new site
- framework scaffold generation
- framework-managed metadata creation

Customization tasks that may use code edits:
- modify generated DocType files
- add service-layer logic
- add API methods
- refine UI after scaffold exists

If the request is "adjust a rule", "update docs", or "change configuration":
- modify only those files
- do not change application code
- do not generate framework files