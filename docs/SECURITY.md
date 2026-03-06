# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Asmblr, please report it **privately** so that we can address it before it is disclosed publicly.

**Do not open a public GitHub issue for security vulnerabilities.**

### How to Report

1. **GitHub Security Advisories** (preferred): Go to the [Security tab](../../security/advisories/new) of this repository and open a private advisory.
2. **Email**: If you cannot use GitHub advisories, send details to the repository maintainers via the contact information in the repository profile.

### What to Include

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Any proof-of-concept code or screenshots
- Your recommended fix (optional)

## Response Process

- We will acknowledge receipt of your report within **48 hours**.
- We aim to provide a fix or mitigation within **7 days** for critical issues and **30 days** for lower severity issues.
- We will notify you when the issue is resolved and credit you in the release notes (unless you prefer to remain anonymous).

## Security Best Practices for Deployments

- Never commit your `.env` file — copy `.env.example` to `.env` and fill in your values locally.
- Rotate `API_KEY` and `UI_PASSWORD` regularly and use `API_KEY_PREV` during the transition window.
- Keep Ollama and all Python dependencies up to date.
- Run behind a reverse proxy (nginx/Caddy) with TLS in production.
- Restrict `API_HOST` and `UI_HOST` to `127.0.0.1` unless you intend to expose the service on the network.

## Scope

The following are **in scope** for vulnerability reports:

- Authentication and authorization bypass
- Remote code execution
- Sensitive data exposure (credentials, run artifacts)
- Injection vulnerabilities (prompt injection with data exfiltration, SQL/command injection)
- Insecure direct object references

The following are **out of scope**:

- Vulnerabilities in Ollama itself (report to the [Ollama project](https://github.com/ollama/ollama))
- Vulnerabilities in base Docker images (tracked in `SECURITY_NOTES.md`)
- Issues that require physical access to the host machine
