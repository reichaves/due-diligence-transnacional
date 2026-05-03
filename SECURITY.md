# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` branch | Yes |
| Older tags | No |

---

## Reporting a vulnerability

**Please do not open a public GitHub issue for security findings.**

Report vulnerabilities by email to:

> reichaves@gmail.com

Include the following in your report:

- Description of the vulnerability and its potential impact
- Steps to reproduce (minimal target.yaml or command that triggers the issue)
- Suggested fix if you have one

You can expect an acknowledgement within **48 hours** and a resolution timeline within **7 days** for critical issues.

---

## Scope

This project is a **local CLI tool** for investigative journalism. It has no web server, no user-facing API, and no persistent process. The attack surface is limited to:

| Component | In scope | Notes |
|-----------|----------|-------|
| `target.yaml` input parsing | Yes | Path traversal, YAML injection |
| Subprocess invocation | Yes | shell=True, argument injection |
| PDF generation | Yes | XML injection into ReportLab |
| API key management | Yes | Hardcoded keys, env exposure |
| External HTTP calls | Yes | SSRF, SSL stripping |
| Web scraping logic | Yes | Input sanitisation |

**Out of scope:**
- Denial of service (this is a single-user local CLI)
- Physical attacks
- Social engineering of the maintainer
- Issues in third-party services (FEC, FARA, OpenCorporates)

---

## Security model summary

See [`docs/security-model.md`](docs/security-model.md) for the full trust model, including:

- Which hosts the pipeline connects to (fixed list)
- How filesystem writes are constrained to `cases/<slug>/`
- Why `shell=True` is never used
- How API keys must be managed

---

## Responsible disclosure

If you discover a vulnerability, we ask that you:

1. Report it privately first (email above)
2. Give us 7 days to release a fix before public disclosure
3. Not exploit the vulnerability beyond what is necessary to demonstrate it

We will credit you in the fix commit if you wish.
