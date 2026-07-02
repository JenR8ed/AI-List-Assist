---
domain: ai-list-assist/sot
status: approved
dash_validated: true
---

# JAIOS_SOT — AI-List-Assist

**JenR8ed AI Operating System Single Source of Truth** for the AI List Assist platform.

This is the primary reference for all agents and humans working in this repository.

## Project Overview
High-performance AI automation platform that transforms unstructured photos into structured marketplace listings for professional online resellers.

Key stack: Python/Flask, Gemini + Cloud Vision (hybrid), eBay REST APIs (Inventory/Offer), PostgreSQL + Redis for market intel, Docker.

## Core Principles (from JAIOS)
- Zero-credential / Zero-token policy: No secrets in git. Use Doppler for runtime secrets (see README update).
- FSAD (File-System-as-Database): Operational state in `fsad/` (proposals → approved → archive) with YAML frontmatter. See also the org-level relations/ FSAD in secure_agent_workspace.
- Privacy & sovereignty first.
- Agent roles: Follow AGENTS.md (this file is now governed by the prepended JAIOS header).
- Hallucinations: Report using the org ISSUE_TEMPLATE/agent_hallucination_report.md

## Key Services (from architecture)
(See full in README or app_enhanced.py)

## Governance
- All changes must respect dash_validated frontmatter where applicable.
- CI includes the new Dash CI workflow which performs lint, tests, secret scan and emits `dash_validated=true`.
- Reference org `.github` repo for shared templates, legal, and SOT.

## References
- Org JAIOS: https://github.com/JenR8ed/.github (docs/governance/)
- Local: README.md, AGENTS.md, fsad/README.md, docs/governance/
- Dev Notebook SOT: in secure_agent_workspace/08_2026-06-08_Dev_Notebook_SOT/

Maintained under JAIOS migration.