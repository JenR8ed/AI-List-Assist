# AGENTS.md

## 1. Architectural Context & Role
* **Project Name:** AI List Assist (Release 2.0 Agent-Only Architecture).
* **System Overview:** This repository contains a full-stack FARM application (FastAPI, Postgres/Neon, React/Next.js) designed to automate the lifecycle of online reselling by normalizing unstructured visual data into structured, category-specific marketplace listings. This operates on a strict Agent-Only Architecture.
* **Expected Behavior:** You are an autonomous developer operating within this repository. You are expected to implement logic, optimize API interactions (specifically the marketplace Inventory and Offer APIs), and adhere to the established service-based architecture managed by `main.py`.

## 2. Agent Lifecycle & Handoff Procedures
The agent ecosystem operates in a strict, sequential lifecycle. Data flows linearly through the following specialized agent services:

1.  **Vision Agent (`VisionService`)**: Ingests raw imagery and performs OCR/object detection to identify the brand, model, and initial condition.
2.  **Valuation Agent (`ValuationService`)**: Receives normalized vision data and performs market analysis using real-time eBay sold data to make a "List/No-List" profitability decision.
3.  **Synthesis Agent (`ListingSynthesisEngine` & `CategoryDetailGenerator`)**: Synthesizes the final listing, maps attributes to eBay taxonomy, and resolves missing item aspects (potentially looping in the `ConversationOrchestrator`).
4.  **API Agent (`eBayIntegration`)**: Finalizes the payload and pushes the listing directly to the eBay REST Inventory/Offer APIs.

Handoffs between agents are strictly typed and must validate against the defined Pydantic schema contracts before progressing to the next stage.

## 3. Pydantic Schema Contract Requirements
Agent inputs, outputs, and handoff boundaries are strictly modeled and validated as Pydantic classes (`BaseModel`).
*   Contract schema definitions are decentralized near their respective application code domains.
*   Agents must **never** pass raw dictionaries or unstructured data between lifecycle stages.
*   Any schema validation failure must trigger an immediate halt and log the error for orchestration recovery.

## 4. Operational Boundaries & Safeguards
* **Strict Credential Policy:** You must **never** hardcode any API credentials, application IDs, or RuNames into the source code. All secrets must be fetched via environment variables defined in the `.env` file (or piped via `WSLENV`).
* **Secrets Management:** Use the 'Add Secrets' button on your screen to securely pass OPENAI_API_KEY or database credentials to the agent's VM.
* **Protected Infrastructure:** Do not modify any files related to the CI/CD pipeline, the `docker-compose.dev.yml` file, or the local CUPS print bridge without explicit human approval.
* **Sanitization Scripts:** The `scripts/sanitize_repo.sh` and `scripts/init_secure_workspace.sh` files are restricted and must not be altered.
* **Pre-commit Constraints:** Ensure your commits do not include large binaries (>10MB) or any private keys, as the pre-commit configuration will reject them.

## 5. Development & Tooling Standards
* **Runtime Environment:** The project is built for Python 3.12+ to utilize specific async features and type hinting.
* **Dependency Management:** Strictly use pip for package management. If you introduce a new package, you must append it to requirements.txt.
* **Local Execution:** The standard command to run the full stack in development mode is `docker-compose -f docker-compose.dev.yml up --build`, or run `scripts/agent_bootstrap.sh` to scaffold the environment.
* **Tunneling:** Assume the local development environment relies on ngrok routing to port 8000 for handling OAuth 2.0 HTTPS callbacks.
* **Data Persistence:** The application relies on Neon Serverless Postgres.

## 6. Coding Conventions & Integrations
* **Type Safety:** Maintain the use of Python dataclasses and Pydantic models (e.g., `ListingDraft`, `DetectedItem`) and strict type hinting across all services.
* **Marketplace Integration:** When writing code for the target platform, always utilize the modern REST/JSON Inventory API model rather than the legacy Trading API. Ensure you account for dynamic Business Policies (Shipping, Payment, Return) via the Account API rather than hardcoding "default" strings.
* **Offline-First Resilience:** When modifying the data persistence layer or vision service, ensure the architecture supports an offline-first mode where detected items are cached locally if the network signal drops.

## 7. Testing Protocols
* **Test Execution:** Always validate your logic before committing by running the test suite using `pytest tests/ -v` in your preferred terminal.
* **Connection Validation:** If you modify marketplace integration logic, instruct the user to verify sandbox access using the `python scripts/ebay_inventory_check.py` handshake script.
