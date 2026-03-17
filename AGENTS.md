# AGENTS.md

## 1. Architectural Context & Role
* **Project Name:** AI List Assist.
* **System Overview:** This repository contains a full-stack Flask application designed to automate the lifecycle of online reselling by normalizing unstructured visual data into structured, category-specific marketplace listings.
* **Expected Behavior:** You are an autonomous developer operating within this repository. You are expected to implement logic, optimize API interactions (specifically the marketplace Inventory and Offer APIs), and adhere to the established service-based architecture managed by `app_enhanced.py`.

## 2. Operational Boundaries & Safeguards
* **Strict Credential Policy:** You must **never** hardcode any API credentials, application IDs, or RuNames into the source code. All secrets must be fetched via environment variables defined in the `.env` file.
* **Protected Infrastructure:** Do not modify any files related to the CI/CD pipeline, the `docker-compose.dev.yml` file, or the local CUPS print bridge without explicit human approval.
* **Sanitization Scripts:** The `scripts/sanitize_repo.sh` and `scripts/init_secure_workspace.sh` files are restricted and must not be altered.
* **Pre-commit Constraints:** Ensure your commits do not include large binaries (>10MB) or any private keys, as the pre-commit configuration will reject them.

## 3. Development & Tooling Standards
* **Runtime Environment**: The project targets Python 3.12+ for production stability and modern async support.
* **Dependency Management:** Strictly use `pip` for package management. If you introduce a new package, you must append it to `requirements.txt`. 
* **Local Execution:** The standard command to run the full stack in development mode is `docker-compose -f docker-compose.dev.yml up --build`.
* **Tunneling:** Assume the local development environment relies on ngrok routing to port 5000 for handling OAuth 2.0 HTTPS callbacks. 
* **Data Persistence:** The application relies on a dual-database strategy (`valuations.db` and `listings.db`) using SQLite. Adhere to the established schema when interacting with these files.

## 4. Coding Conventions & Integrations
* **Type Safety:** Maintain the use of Python dataclasses (e.g., `ListingDraft`, `DetectedItem`) and strict type hinting across all services.
* **Marketplace Integration:** When writing code for the target platform, always utilize the modern REST/JSON Inventory API model rather than the legacy Trading API. Ensure you account for dynamic Business Policies (Shipping, Payment, Return) via the Account API rather than hardcoding "default" strings.
* **Offline-First Resilience:** When modifying the data persistence layer or vision service, ensure the architecture supports an offline-first mode where detected items are cached locally if the network signal drops.

## 5. Testing Protocols
* **Test Execution:** Always validate your logic before committing by running the test suite using `pytest tests/ -v` in your preferred terminal.
* **Connection Validation:** If you modify marketplace integration logic, instruct the user to verify sandbox access using the `python scripts/ebay_inventory_check.py` handshake script.
