# kentender_suppliers

This app **owns** supplier identity, onboarding, classification, performance, and sanctions/blacklisting per [global-architecture-v3.md](../docs/architecture/global-architecture-v3.md).

- DocTypes stay thin; orchestration lives under `kentender_suppliers/services/`.
- `kentender_procurement` **references** suppliers; it does not own supplier lifecycle.
