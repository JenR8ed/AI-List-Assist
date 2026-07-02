---
domain: ai-list-assist/governance
status: draft
dash_validated: false
---

# FSAD Architecture (File-System-as-Database) — AI-List-Assist

Adapted for project-specific operational ledger. See also org-level in JenR8ed/.github .

## State Machine
- `fsad/proposals/` — New ideas, feature proposals, experiments
- `fsad/approved/` — Validated, ready for implementation or published
- `fsad/archive/` — Completed, deprecated, or historical records

Each record uses YAML frontmatter:
```yaml
---
id: <slug-or-uuid>
created_at: 2026-07-01
state: proposal | approved | archived
owner: JenR8ed
tags: [valuation, listing, consignment, ...]
---
```

## Records
- listing workflows
- valuation jobs
- consignment transactions

See [fsad/README.md](../../fsad/README.md) and the central docs/governance/fsad-architecture.md in the .github governance repo for full details.

## Integration with Dash
The Dash CI workflow and governance stamp ensure changes to tracked state respect the model.