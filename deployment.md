# Deployment status

CyberSafe is currently a local development prototype. It is **not ready for public or production deployment** and should not receive real cybercrime reports, personal information, or evidence.

## Known release blockers

- The AI Insights “predictions” are fixed illustrative strings, not trained or validated forecasts.
- Report analysis can fall back to simple keyword rules and sample confidence values. These outputs are not validated for decisions about victims or investigations.
- Configured report analysis may send report descriptions to an external AI provider. Data minimization, consent, retention, and legal review are not implemented here.
- The complaint tracking page requires a signed-in account at the API, even though its public page can be opened without signing in.
- Status changes and timeline entries are written separately rather than as one database transaction; invalid status transitions are not prevented.
- Production operations such as HTTPS termination, managed secrets, durable rate-limit storage, backups, monitoring, incident response, and database migration automation need to be designed and tested.

## Before any real deployment

1. Define the service owner, lawful basis, privacy notice, data retention/deletion policy, and incident response process.
2. Complete an independent security review and threat model. Protect personal data and evidence in transit, at rest, in logs, and in backups.
3. Decide whether tracking is account-only or uses a separate high-entropy, revocable tracking credential. Do not expose complaints through guessable numbers.
4. Make complaint status updates and history entries atomic, enforce valid status transitions, and add reliable notifications and audit records.
5. Either remove prediction claims or develop a real forecasting pipeline with representative data, evaluation, monitoring, uncertainty bounds, and human review.
6. Validate the report-analysis model, constrain and validate outputs, document provider data handling, and keep all recommendations clearly advisory.
7. Configure a production WSGI server, HTTPS, secure CORS, managed secrets, durable shared rate limiting, least-privilege database accounts, backups, monitoring, and tested migrations.
8. Run automated security, authorization, database, upload, recovery, and end-to-end tests using a dedicated test environment.

For local VS Code setup, follow [README.md](README.md). That workflow is for development on your own computer, not production hosting.
