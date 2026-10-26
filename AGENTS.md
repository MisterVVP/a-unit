# Working on A-Unit

A-Unit defines reusable engineering roles and their runtime packaging. Keep canonical behavior portable and adapters small.

## Current stage

This revision implements local Codex CLI packaging and conservative installation in aunit.py. Canonical definitions remain portable; generated artifacts are rendered on demand and are not checked in. Runtime wiring has an offline fixture check; live engineering quality and broader platform coverage remain separate validation work.

## Editing rules

- Keep roles focused on their specialty; put shared behavior in agents/_shared/engineering-contract.md. Keep offline reference guidance in the explicit public allowlist under agents/_shared/knowledge/.
- Packaging must include the complete shared contract before each role body. Resolve shared sources from the A-Unit package, not the target project's working directory; installed agents must be self-contained.
- Keep repository-specific commands and conventions in the target project's instructions.
- Preserve canonical identifiers unless a rename includes an explicit compatibility decision.
- Keep display names independent of functional role descriptions.
- Preserve React JavaScript/JSX support; do not require a TypeScript migration.
- Add no model identifiers, provider-specific settings, or fixed concurrency values to canonical roles.
- Keep deployment, publication, credentials, and destructive operations within the user's authorization.
- Do not claim production readiness, runtime compatibility, or successful checks without evidence.
- Treat private plans, decisions, AI context, maintainer notes, and conversation records as private inputs. Do not copy, quote, commit, package, or publish them in this repository, ai-db, or another repository without explicit authorization for those specific documents. Existing maintainer-provided internal docs may be read; keep new private notes outside tracked files. Public user-facing usage and compatibility evidence belong in README.md.
- Package only the explicit public-file allowlist in aunit.py. Never include the whole checkout or add internal documentation to distribution archives.
- Keep user installations scoped explicitly. Never rewrite target AGENTS.md, config.toml, or unowned files; retain ownership/hash checks and recoverable failure behavior.

## Validation

Use Python 3.11+ and install requirements.txt in a virtual environment. Required checks:

- `python aunit.py validate`
- `python -m unittest discover -s tests -v`
- `python aunit.py render --output <new temporary directory>`
- `python aunit.py package --output <new temporary ZIP path>`

For Codex adapter changes, run `python tests/codex_smoke.py` when Codex and local loopback sockets are available; use `--work-dir` for a directory shared with a separate execution server if required. This deterministic fixture checks real CLI discovery/invocation and instruction delivery, not live-model engineering quality. Record unavailable checks honestly.

For documentation changes, check relative links, roster consistency, frontmatter, cross-document behavior, and absence of unsupported implementation claims. Tests must cover meaningful failures and preservation of canonical instructions rather than merely mirror implementation details. The CI matrix covers Ubuntu, macOS, and Windows; do not describe configured jobs as passed before observing their results.
