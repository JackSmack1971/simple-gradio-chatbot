# Technology Stack Decisions

> **Status**: ✅ Complete - Stack baselined and approved for implementation
> **Phase**: Context Engineering - Technology Research

## Technology Decision Framework

### Evaluation Criteria
- **Performance**: Throughput, latency, startup time benchmarks.
- **Community**: Release cadence, contributor base, support quality.
- **Maintenance**: Long-term support, patch frequency, backward compatibility.
- **Team Fit**: Familiarity for Python-focused engineers, learning curve for contributors.
- **Integration**: Compatibility with OpenRouter APIs, observability tooling, and deployment targets.
- **Cost**: Licensing, hosting footprint, operational efficiency.

## Frontend Technology Stack

### Framework Decision
- **Selected**: Gradio 4.22.0 running on Python 3.11
- **Alternatives Considered**:
  - Streamlit 1.32.0 (scored lower on real-time streaming support and theming flexibility)
  - Custom React 18 + FastAPI UI (higher development overhead, duplicate work for chat components)
  - NiceGUI 2.0 (smaller community, less mature documentation)
- **Justification**:
  - Native support for conversational interfaces, markdown rendering, and streaming outputs align with FR-3 requirements.
  - Fast startup (<3s) and lightweight deployment footprint help satisfy AC-001 performance targets.
  - Large community and first-party components reduce time-to-market and maintenance burden.
- **Configuration**:
  - Serve via `gradio.ChatInterface` with custom `Blocks` for analytics and settings panels.
  - Enable server-side session state using `gradio.State` objects backed by Redis for persistence.
  - Apply theming through `gradio.themes.Base` with custom palette meeting WCAG 2.1 AA contrast requirements.

### UI Library Decision
- **Selected**: Gradio native component library + `gradio-themes` 0.1.5
- **Justification**: Built-in chat bubbles, file upload, and metrics components reduce need for third-party JS frameworks while supporting accessibility semantics. `gradio-themes` allows consistent branding without maintaining bespoke CSS pipelines.

### State Management
- **Selected**: Gradio session state with Redis 7.2.4 as backing store
- **Architecture**:
  - In-memory state for transient UI interactions (draft messages, toggles).
  - Persistent state stored in Redis for active sessions and synchronized with SQLite conversation store after each response.
  - Prevents loss of context during multi-tab usage and enables horizontal scaling across ASGI workers.

## Backend Technology Stack

### Runtime/Framework Decision
- **Selected**: Python 3.11.8 with FastAPI 0.110.0 (ASGI) served by Uvicorn 0.29.0
- **Performance Benchmarks**:
  - FastAPI + Uvicorn handles ≥ 3,000 requests/min on c6i.large with p95 latency < 120ms for lightweight endpoints.
  - Async `httpx` client ensures streaming responses from OpenRouter without blocking event loop, supporting AC-005.
- **Scalability Analysis**:
  - Stateless API layer with Redis-backed session sharing allows horizontal autoscaling.
  - Background tasks (Celery 5.3 + Redis broker) manage retention purges and analytics aggregation without blocking chat flows.

### Database Decision
- **Primary Database**: SQLite 3.45 managed via SQLAlchemy 2.0.28 with Alembic 1.13 migrations
- **Schema Design**:
  - Normalized schema storing workspaces, users, conversations, messages, and prompt templates.
  - JSON columns for model metadata and cost breakdowns to accommodate provider-specific fields.
  - Row-level encryption for API key vault using SQLCipher-compatible extension.
- **Caching Strategy**:
  - Redis 7.2.4 for session cache, rate limiting counters, and model catalog caching (15 minute TTL).
  - Local in-memory LRU cache for static configuration to minimize Redis calls on single-node deployments.

## DevOps & Infrastructure

### Deployment Platform
- **Selected**: Fly.io Machines (Shared CPU 1x, 1 vCPU, 2 GB RAM) with autoscaling to 3 instances
- **Cost Analysis**:
  - Base machine: ~$0.013/hr → ~$9.36/month per instance; autoscaling adds up to $28.08/month at peak.
  - Redis (Upstash tier) ~$10/month; persistent volume for SQLite snapshots ~$5/month.
  - Total infrastructure budget ≈ $54/month excluding OpenRouter usage, meeting BR-6 budget constraint.

### CI/CD Pipeline
- **Tools**:
  - GitHub Actions (hosted runners) for linting, testing, and deployment packaging.
  - Ruff 0.3.5 + Black 24.3b0 for lint/format checks.
  - Pytest 8.1 for automated tests, Coverage.py 7.4 for reporting.
  - Fly.io GitHub Action for blue/green deployments; Snyk CLI for vulnerability scanning.
- **Configuration**:
  - Workflows triggered on pull request and main branch merges.
  - Stages: lint → unit tests → integration tests (mock OpenRouter) → build Docker image → security scan → deploy to staging → manual approval → production deploy.
  - Secrets injected via GitHub OIDC → Fly.io for deployment, ensuring no plaintext credentials in pipeline.

---
**Quality Standard**: All selections undergo quarterly review to confirm continued compliance with performance, security, and cost guardrails.
