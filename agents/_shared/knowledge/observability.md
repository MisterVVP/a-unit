# Observability and reliability: practical engineering guide

Apply proportional observability to the affected user journey. Reuse the target project's instrumentation and monitoring stack instead of inventing new infrastructure.

## Signals and instrumentation
- Start from user-visible operations and failure modes. Cover latency, traffic, errors, and saturation where a running service exists.
- Prefer counters for events, gauges for current state, and histograms for latency/size distributions. Record units and labels consistently; use route patterns rather than raw URLs.
- Keep metric label combinations bounded. Never label metrics with user IDs, trace IDs, arbitrary input, or unbounded error text.
- Emit structured logs with severity, operation, timestamps, and actionable failure context. Minimize/redact personal data, tokens, secrets, and sensitive payloads.
- Propagate trace context across service boundaries and asynchronous handoffs; connect trace/span identifiers to logs when supported. Use the existing OpenTelemetry naming conventions and resource attributes.
- Keep exporters bounded and failure-tolerant: dropped or delayed telemetry must not indefinitely block business requests.

## Availability, SLIs, SLOs, and alerts
- Distinguish service availability observed by users from process uptime and metrics scrape success.
- Define each SLI precisely, including success/failure semantics, numerator, denominator, window, exclusions, and behavior with no traffic or missing measurements.
- Use agreed objectives if they exist. If not, propose candidate targets explicitly; do not silently assert an SLO.
- For a request-success SLI, a simple error budget is the allowed fraction of bad eligible requests over the evaluation window; calculate compliance using the same event eligibility rules.
- Prefer actionable alerts for user impact, sustained failure, or meaningful error-budget burn; evaluate both shorter and longer windows to distinguish fast outages from slow degradation.
- Avoid pages for every diagnostic spike. Give alerts an owner, likely impact, and investigation/mitigation steps.

## Verify the full signal path
- Exercise representative successful, failed, and slow operations and inspect emitted metrics, logs, traces, and available dashboards.
- Check metric units, cardinality, missing-data behavior, redaction, and sensible instrumentation overhead.
- Differentiate validated application emission from successful scrape/export, dashboard query correctness, and alert firing. Report unverified stages explicitly.
