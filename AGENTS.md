# Working on A-Unit

A-Unit defines reusable engineering roles and their runtime packaging. Keep canonical behavior portable and adapters small.

## Current stage

This revision is an agent-contract draft. Executable tooling, generated runtime definitions, and installation instructions are planned work. Describe their status accurately.

## Editing rules

- Keep roles focused on their specialty; put shared behavior in agents/_shared/engineering-contract.md.
- Packaging must include the complete shared contract before each role body. Resolve shared sources from the A-Unit package, not the target project's working directory; installed agents must be self-contained.
- Keep repository-specific commands and conventions in the target project's instructions.
- Preserve canonical identifiers unless a rename includes an explicit compatibility decision.
- Keep display names independent of functional role descriptions.
- Preserve React JavaScript/JSX support; do not require a TypeScript migration.
- Add no model identifiers, provider-specific settings, or fixed concurrency values to canonical roles.
- Keep deployment, publication, credentials, and destructive operations within the user's authorization.
- Do not claim production readiness, runtime compatibility, or successful checks without evidence.

## Validation

For documentation changes, check relative links, roster consistency, frontmatter, cross-document behavior, and absence of unsupported implementation claims. No executable project checks exist at this stage.

When tooling is implemented, document its actual setup and validation commands here. Tests must cover meaningful failures and preservation of canonical instructions rather than merely mirror implementation details.
