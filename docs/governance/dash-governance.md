---
domain: ai-list-assist/governance
status: draft
dash_validated: false
---

# Dash Governance — Zero-Trust Secrets Policy

## Purpose
`dash_validated` + `status` frontmatter (and the CI stamp) provides the control point for publishable / automatable changes.

## Zero-Trust Secrets Policy
- Secrets are **never** committed.
- Injected at runtime via Doppler (see updated README.md).
- Onboarding reference: jenr8ed-doppler-config (private).

## Governance Gate (for relevant artifacts)
Files intended for automation/publishing should carry:
```yaml
---
dash_validated: true
status: Draft | Published | Archived
---
```

## CI Integration
See `.github/workflows/dash.yml`:
- Runs on push/PR
- Lint, tests (with safe env), secret scan via detect-secrets
- Emits `dash_validated=true` output

Violations of secret policy or missing governance are treated as critical.

See also the org \`.github\` repo governance docs and [fsad-architecture.md](fsad-architecture.md).