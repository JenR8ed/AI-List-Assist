# **AI-List-Assist | Release 2.0: Monorepo Hardening & GitLab Handoff**

## **🎯 Strategic Objective**

Release 2.0 represents a total architectural pivot for AI-List-Assist. We are migrating from a prototype Flask application to an enterprise **FARM Stack** (FastAPI, React, Neon Postgres) governed by an **Agent-Only Architecture**.

Before this GitHub monorepo is handed off to GitLab for automated CI/CD lifecycle management, the repository must be strictly hardened. This document outlines the mandatory checklist to sanitize the codebase, enforce schema contracts, and prep the environment for GitLab runners.

## **Phase 1: Architectural Re-Baselining (Agent-Only Pivot)**

GitLab pipelines will fail intentionally if human-centric testing or non-deterministic agent behaviors are detected. The codebase must be locked down to strict contracts.

* \[ \] **Purge Legacy Routing:** Remove all traces of app\_enhanced.py and the Flask ecosystem.  
* \[ \] **Enforce Pydantic Contracts:** Ensure all agent inputs, outputs, and handoff boundaries are strictly typed using Pydantic BaseModel schemas located in models/domain.py (or models/agent\_contracts.py).  
* \[ \] **Scaffold Session Replays:** Create the centralized tests/fixtures/sessions/ directory. Populate it with JSON fixtures representing successful, deterministic multi-agent workflows (Vision \-\> Valuation \-\> Synthesis \-\> eBay API).  
* \[ \] **Scaffold Evaluation Scripts:** Add scripts/evaluate\_token\_usage.py to enforce LLM cost limits during CI/CD execution.

## **Phase 2: Monorepo Structural Hardening**

GitLab CI/CD requires a predictable, immutable file structure to cache dependencies efficiently and isolate testing stages.

* \[ \] **Enforce Strict Directory Layout:**  
  ├── .jules/                  \# MCP Tool configs (Neon, Stitch)  
  ├── api/                     \# FastAPI Routers  
  ├── core/                    \# Settings, Auth, and DB Engine  
  ├── models/                  \# Pydantic schemas & SQLModel tables  
  ├── services/                \# Business logic & Agent orchestrators  
  ├── scripts/                 \# CI/CD evaluation and DB migration scripts  
  ├── tests/                   \# Pytest suite  
  │   ├── contracts/           \# Fast validation tests  
  │   ├── workflows/           \# Slow full-agent execution tests  
  │   └── fixtures/sessions/   \# Deterministic replay data  
  ├── frontend/                \# (Future) Next.js/React application  
  └── .gitlab-ci.yml           \# The finalized GitLab pipeline definition

* \[ \] **Secret Decoupling:** Ensure absolutely no .env files are tracked in version control. All configuration must route through core/config.py relying entirely on OS-level environment variables (NEON\_DATABASE\_URL, STITCH\_TOKEN).

## **Phase 3: Tooling & Git Workflow Hardening**

Prevent "dirty diffs" and hallucinated code reviews before the GitLab pipeline even triggers.

* \[ \] **Notebook Sterilization:** Verify that jupytext and nbstripout are actively enforced via Git hooks.  
  * *Rule:* .ipynb files must be stripped of execution outputs before committing.  
  * *Rule:* All notebook logic must be paired and synced with .py percent-formatted scripts (e.g., AI\_List\_Assist\_Development\_Notebook.py).  
* \[ \] **Pre-commit Hooks (Optional but Recommended):** Configure black, ruff, and mypy to run locally before code is pushed, ensuring GitLab runners aren't wasting compute minutes on syntax errors.

## **Phase 4: The GitLab Handoff Checklist**

Once the repository is structured, these final verification steps must be taken before importing the project to GitLab.

* \[ \] **Pipeline Definition:** Verify .gitlab-ci.yml is committed to the root, utilizing the python:3.12-slim Docker image.  
* \[ \] **Stage Mapping:** Ensure the CI file defines the following execution stages:  
  1. contract-tests (Timeout: 5m)  
  2. handoff-tests (Timeout: 10m)  
  3. session-replay (Timeout: 15m)  
  4. full-agent-workflows (Timeout: 30m)  
* \[ \] **Variable Migration Prep:** Document the production and staging secrets that will need to be manually injected into the GitLab CI/CD Variables dashboard upon import:  
  * NEON\_DATABASE\_URL  
  * STITCH\_TOKEN  
  * ANTHROPIC\_API\_KEY (for evaluation agents)  
  * EBAY\_OAUTH\_CREDENTIALS

## **🚀 Definition of Ready (DoR) for Handoff**

The repository is cleared for GitLab import **ONLY WHEN**:

1. pytest tests/contracts/ passes 100% locally.  
2. No raw SQLite queries exist (all db operations use asyncpg \+ SQLModel).  
3. Jules (or GitMCP) successfully validates the Pydantic schemas against the live Neon Postgres database.