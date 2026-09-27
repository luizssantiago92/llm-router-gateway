# Security Policy

LLM Router Gateway is an academic / lab demo. The Compose file, image, and CI defaults below are local hardening. They are not a production security review.

## Supported versions

| Version | Supported |
| --- | --- |
| `main` | yes |

## Reporting a vulnerability

Do not open a public GitHub issue for a security report, and do not paste secrets, tokens, or `.env` contents into issues, pull requests, or logs.

Use [private vulnerability reporting](https://github.com/luizssantiago92/llm-router-gateway/security/advisories/new) for this repository.

Include:

- a description of the issue and its impact
- steps to reproduce
- the affected commit or version

Please allow time for a fix before any public disclosure.

## In scope

- Authentication bypass on `POST /v1/chat/completions`
- Secret leakage (API keys in URLs, logs, images, or git)
- Redis exposure in the published Compose file
- Supply-chain issues in this repository's dependencies, image, or GitHub Actions workflows

## Out of scope

- Vulnerabilities in Gemini, Ollama, Docker, or Redis upstream projects (report those to the upstream)
- Misuse of a demo you run yourself on a machine you control
- Production multi-tenant guarantees (this repository does not claim them)

## Secrets in this demo

- Never commit `.env`, API keys, or Redis passwords.
- Compose requires `REDIS_PASSWORD`. Redis is published on `127.0.0.1:6379` only.
- The Gemini adapter sends `GEMINI_API_KEY` in the `x-goog-api-key` header, not the query string.
