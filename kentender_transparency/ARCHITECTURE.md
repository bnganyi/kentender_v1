# kentender_transparency

This app **owns** read-only public publication: notices, tender publication, award publication, and transparency portal surfaces per [global-architecture-v3.md](../docs/architecture/global-architecture-v3.md).

- It does **not** drive transactional state; publishing consumes published interfaces from domain apps.
- `kentender_procurement` owns transaction records; transparency owns disclosure workflows.
