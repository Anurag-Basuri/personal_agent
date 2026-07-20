# Personal Agent Customizations

## Rules & Workflow

- **Repository Pattern Enforcement**: Do NOT use raw SQLAlchemy queries in API endpoints or services. Use the dedicated Repositories located in `backend/app/repositories/`.
- **Resilience**: Any external HTTP requests or third-party API calls must use `retry_with_backoff` (and potentially a `CircuitBreaker`) from `backend/app/core`.
- **Caching**: Wrap read-heavy database calls with the `TTLCache` to prevent performance degradation. Ensure cache is invalidated upon writes.
- **Rate Limiting**: Protect new FastAPI endpoints with the `rate_limit` dependency from `app.core.rate_limiter`.
- **Python Conventions**: Use type hints, adhere to PEP 8, and format docstrings for all new methods.
- **Workflow**: Create detailed implementation plans in an artifact before execution for major structural changes. Write code incrementally and atomically.
- **Documentation Context**: Always read and maintain the context of the four primary project documentation files (`README.md`, `PROGRESS.md`, `ROADMAP.md`, and `SYSTEM_DESIGN.md`). Whenever you implement new features or architectural patterns, you must proactively update these files accordingly, or at the very least, explicitly inform the user that these files need updates to reflect the changes.
