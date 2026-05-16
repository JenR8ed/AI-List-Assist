# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. **Please do not open a public GitHub issue for security vulnerabilities.**

### Preferred Method: Private Vulnerability Reporting

Use GitHub's built-in [private vulnerability reporting](https://github.com/JenR8ed/AI-List-Assist/security/advisories/new) to report security issues confidentially.

This allows us to:
- Review and validate the report privately
- Develop and test a fix before public disclosure
- Coordinate a responsible disclosure timeline with you

### What to Include

Please provide:
- A clear description of the vulnerability
- Steps to reproduce the issue
- The potential impact and severity
- Any suggested fixes or mitigations (optional)

## Response Timeline

| Stage | Target Time |
|---|---|
| Initial acknowledgment | Within 5 business days |
| Severity assessment | Within 10 business days |
| Fix development | Varies by severity |
| Disclosure | Coordinated with reporter |

## Scope

This policy covers the AI-List-Assist application, including:
- Flask API endpoints and authentication logic
- eBay API integration and OAuth flow
- Gemini AI and Perplexity API integrations
- Database access and data handling
- Dependency vulnerabilities

## Out of Scope

- Issues in third-party services (eBay, Google, Perplexity)
- Social engineering attacks
- Denial of service attacks

## Security Best Practices for Contributors

- Never commit API keys, tokens, or credentials (enforced via secret scanning)
- Use environment variables for all sensitive configuration
- Follow the existing patterns in `shared/` for secure data handling
- Run `pip-audit -r requirements.txt` locally before submitting PRs
