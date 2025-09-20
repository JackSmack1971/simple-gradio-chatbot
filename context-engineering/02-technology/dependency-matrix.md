# Dependency Matrix & Compatibility

> **Status**: ✅ Complete - Versions locked and validated for compatibility
> **Phase**: Context Engineering - Technology Research

## Version Compatibility Matrix

### Primary Dependencies
| Package | Version | Runtime Version | Compatible With |
|---------|---------|-----------------|-----------------|
| python | 3.11.8 | Debian 12 base image | FastAPI, Gradio, Celery toolchain |
| gradio | 4.22.0 | Python 3.11 | FastAPI backend via mounted blocks |
| fastapi | 0.110.0 | Python 3.11 | Uvicorn 0.29.0, Pydantic 2.6.3 |
| uvicorn | 0.29.0 | Python 3.11 | FastAPI 0.110.0 (ASGI) |
| httpx | 0.27.0 | Python 3.11 | Async OpenRouter streaming |
| sqlalchemy | 2.0.28 | Python 3.11 | SQLite 3.45, Alembic 1.13.1 |
| alembic | 1.13.1 | Python 3.11 | SQLAlchemy 2.0 migration scripts |
| pydantic | 2.6.3 | Python 3.11 | FastAPI request/response validation |
| redis | 5.0.3 | Python 3.11 | Redis server 7.2.4 |
| celery | 5.3.6 | Python 3.11 | Redis broker 7.2.4 |
| cryptography | 42.0.5 | Python 3.11 | API key encryption services |
| python-dotenv | 1.0.1 | Python 3.11 | Local environment management |

### Peer Dependencies
| Main Package | Peer Dependency | Required Version | Compatibility Notes |
|--------------|-----------------|------------------|---------------------|
| fastapi | starlette | 0.37.2 | Bundled with FastAPI 0.110; required for ASGI routing |
| fastapi | pydantic | >=2.6,<3 | FastAPI models rely on Pydantic v2 serialization |
| gradio | websockets | 12.0 | Enables streaming + WebSocket connections |
| celery | kombu | 5.3.4 | Message transport, shipped with Celery 5.3.6 |
| sqlalchemy | greenlet | 3.0.3 | Async DB session support |
| redis (client) | redis-server | 7.2.4 | Managed instance via Upstash |
| cryptography | openssl | 3.0+ | Provided by base image; required for AES-GCM |

## Security Analysis

### Vulnerability Assessment
| Package | Known Vulnerabilities | Severity | Mitigation |
|---------|----------------------|----------|------------|
| gradio 4.22.0 | None disclosed as of 2024-04-10 | N/A | Monitor CVE feeds weekly; lock minor version |
| fastapi 0.110.0 | No CVEs affecting 0.110 | N/A | Enable dependency pinning; rerun security scan on release |
| uvicorn 0.29.0 | CVE-2023-45803 (prior versions) | Medium | Patched in 0.29.0; keep >=0.29 |
| httpx 0.27.0 | None | N/A | Enable TLS certificate verification by default |
| sqlalchemy 2.0.28 | None | N/A | Apply SQL injection-safe ORM patterns |
| celery 5.3.6 | None | N/A | Restrict broker credentials; enforce TLS |
| cryptography 42.0.5 | None | N/A | Rotate dependencies quarterly |

### License Compatibility
| Package | License | Commercial Use | Attribution Required |
|---------|---------|----------------|---------------------|
| gradio | Apache-2.0 | Yes | No (retain NOTICE file) |
| fastapi | MIT | Yes | Include MIT license text |
| uvicorn | BSD-3-Clause | Yes | Yes, include in acknowledgements |
| httpx | BSD-3-Clause | Yes | Yes |
| sqlalchemy | MIT | Yes | Include MIT text |
| celery | BSD-3-Clause | Yes | Include notice |
| redis (client) | MIT | Yes | Include MIT text |
| cryptography | Apache-2.0 / BSD dual | Yes | Retain license references |

## Update Strategy

### LTS Roadmap
- **Python 3.11**: Active support until October 2026; plan migration readiness to Python 3.12 within 12 months of LTS release.
- **Gradio 4.x**: Monthly releases; subscribe to release notes and evaluate minor updates quarterly in staging.
- **FastAPI 0.x**: Backward compatible on minor bumps; monitor Starlette and Pydantic version pins via Dependabot.
- **Redis 7.2**: LTS maintenance by Upstash; review upgrade path to 7.4 once GA for improved ACL capabilities.

### Breaking Changes Timeline
- Track Gradio 5.0 roadmap (expected H1 2025) for potential API adjustments to `ChatInterface` and theming; prototype migration in feature branch before GA.
- Monitor FastAPI adoption of Pydantic v3; evaluate compatibility once release candidate available.
- Schedule semi-annual dependency audit verifying Celery/Redis broker compatibility and SQLCipher extension stability.

---
**Maintenance Plan**: Conduct quarterly dependency reviews, automate CVE scans via Snyk and GitHub Dependabot, and document upgrade outcomes in release notes.
