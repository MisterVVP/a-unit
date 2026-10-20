# A-Unit

**No Gods. No Masters. Just Agents.**

A portable engineering squad: Hannibal coordinates your main Codex CLI session and calls fourteen focused specialist agents. Each installed definition contains the complete shared engineering contract and its role instructions. No source checkout or private documentation is needed at runtime.

**Status: local Codex CLI packaging preview.** The Python installer and automated checks are implemented. Adapter wiring was exercised on Linux with Codex CLI **0.159.2**, using an offline deterministic Responses fixture. Live-model engineering quality and macOS/Windows runtime behavior have not been evaluated. GitHub Packages and other runtime adapters are deferred.

## Install on Ubuntu

Prerequisites: Git, Python **3.11+** with `venv`/pip, and Codex CLI. Use **0.159.2** as the compatibility baseline; older versions are unverified. Authenticate Codex normally before your live trial (`codex login`).

```bash
git clone https://github.com/MisterVVP/a-unit.git
cd a-unit
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python aunit.py validate

# Preview a personal installation, then apply it.
.venv/bin/python aunit.py install --user
.venv/bin/python aunit.py install --user --apply

# Start a NEW session in the repository you want to work on.
cd /path/to/your/project
codex
```

Inside Codex, explicitly invoke the skill:

```text
$a-unit Investigate this repository and propose a small, testable Python improvement. Do not edit yet.
```

Hannibal stays in the main session. It invokes Trace Ventura for every coding task, including small changes, to plan observability early and validate affected coverage before completion. It invokes Dock Norris whenever work involves containerization, a local Dockerized setup, or Kubernetes deployment. Other specialists are selected when useful; Hannibal can implement small changes directly while still performing the required consultations. To verify delegation explicitly, ask:

```text
$a-unit Use aunit-snake-eyes for an inspection-only review of the Python code. Report findings and checks; do not edit files.
```

If your CLI has multi-agent support disabled, enable it for the session with `codex --enable multi_agent`. Installation does not edit feature flags, model settings, concurrency, or permissions.

## Project scope and other platforms

Choose **one scope** for the activation skill. For a squad pinned to an existing repository, replace `--user` with an explicit project path:

```bash
.venv/bin/python aunit.py install --project /path/to/your/project
.venv/bin/python aunit.py install --project /path/to/your/project --apply
```

Paths with spaces work when quoted. The working directory never implicitly selects a target project. Installation leaves existing `AGENTS.md` and `config.toml` files untouched. The optional [project instruction template](templates/AGENTS.md) is a manual starting point.

| Artifact | User scope | Project scope |
| --- | --- | --- |
| Fourteen agent TOMLs | `$CODEX_HOME/agents/aunit-*.toml` (default `~/.codex/agents`) | `<project>/.codex/agents/aunit-*.toml` |
| Hannibal activation skill | `~/.agents/skills/a-unit/` | `<project>/.agents/skills/a-unit/` |
| Ownership manifest | `$CODEX_HOME/a-unit-manifest.json` | `<project>/.codex/a-unit-manifest.json` |

`CODEX_HOME` changes the user **agent** destination; the preferred user **skill** destination remains `~/.agents/skills`. Set `CODEX_HOME` consistently when installing, running Codex, updating, and uninstalling. The manifest uses relative artifact paths so project installations can move with the repository.

Codex gives same-name project agent roles precedence over user roles in a trusted project. **Skills differ:** with `a-unit` installed in both scopes (or another copy under the legacy `$CODEX_HOME/skills` directory), `$a-unit` can be ambiguous and load neither copy. Remove the unwanted installation or select the intended skill explicitly through Codex's skill picker. Start a fresh session after changes. Project configuration may require the normal Codex trust decision; do not disable trust checks to load it.

On macOS/Linux, use the same Python commands. On Windows, create the environment with `py -3.11 -m venv .venv` (or a newer Python), then replace `.venv/bin/python` with `.venv\Scripts\python.exe`. In PowerShell, quote environment variables and paths normally. The installer uses Python filesystem operations and no Bash, symlinks, or external installation commands. Existing symlink/reparse-point destinations are deliberately refused. Cross-platform CI is configured; local execution here covered Linux only.

## Package and inspect locally

No registry, wheel, or global executable is required. The local ZIP contains the Python utility, its dependency declaration, canonical role sources, license, public README, and optional project template. Definitions are rendered at installation time. Keep the ZIP and extracted directory only as long as needed to install or update.

```bash
.venv/bin/python aunit.py render --output dist/codex
.venv/bin/python aunit.py package --output dist/a-unit-codex.zip
```

`render` requires a new output directory and produces `agents/*.toml` plus `skills/a-unit/`. `package` refuses to overwrite an existing archive. Both operations validate sources first. Output uses stable ordering, UTF-8, fixed ZIP timestamps, and no host-specific source paths. Only allowlisted public files enter the archive; repository instructions, internal notes, tests, and `.git` are excluded.

You can transfer the ZIP to another machine, extract it, install `requirements.txt` in a Python environment, and run its `aunit.py install --user` (or `--project PATH`). Git is optional when installing the extracted bundle. Installation itself needs no network access once Python and PyYAML are available. Neither the virtual environment nor the extracted/source directory is a runtime dependency after installation.

## Update and uninstall

Install commands preview by default. `--apply` prints the preflighted plan and applies it. Every source and destination is checked before writes. A SHA-256 ownership manifest tracks installed files; identical reinstallations do nothing. Updates replace unchanged managed files and remove unchanged stale artifacts.

To update, fetch this branch's latest source or extract a newer bundle, then rerun the same install command and scope. Use the same `CODEX_HOME` for user updates.

```bash
.venv/bin/python aunit.py uninstall --user
.venv/bin/python aunit.py uninstall --user --apply
# Or use: uninstall --project /path/to/your/project [--apply]
```

Unowned collisions and locally edited managed files block installation, including identical unowned files. Save or move conflicting files before retrying; there is no force overwrite. Missing managed files can be restored by reinstalling. Uninstall removes only owned files whose hashes still match, preserves and reports edits, retains their ownership entries, and exits with status 1 when manual cleanup remains. Unrelated files and directories are left intact; empty installation directories may remain.

Writes use atomic per-file replacement with recoverable backups. An ordinary write/remove failure rolls back previous contents; an incomplete recovery reports remaining paths and the backup location. Run one installer at a time. This is not a filesystem-wide transaction and does not promise recovery from process termination or power loss. Keep the manifest until removal is complete.

## The gang

| Agent | Specialty | Definition / installed role |
| --- | --- | --- |
| Hannibal | Main-session commander | [hannibal](agents/hannibal.md), via `$a-unit` |
| Repo Man | Repository layout and monorepo organization | [repo-man](agents/repo-man.md), `aunit-repo-man` |
| Plan Solo | System design, inspection only | [plan-solo](agents/plan-solo.md), `aunit-plan-solo` |
| B.A. Barac++ | Backend C++ | [baracus](agents/baracus.md), `aunit-baracus` |
| Go-rilla | Backend Go | [go-rilla](agents/go-rilla.md), `aunit-go-rilla` |
| Snake Eyes | Backend Python | [snake-eyes](agents/snake-eyes.md), `aunit-snake-eyes` |
| The Nodefather | Backend Node.js / JavaScript | [nodefather](agents/nodefather.md), `aunit-nodefather` |
| Sharp Shooter | Backend .NET / C# | [sharp-shooter](agents/sharp-shooter.md), `aunit-sharp-shooter` |
| Face | Frontend React / JavaScript | [face](agents/face.md), `aunit-face` |
| Droid Rage | Android | [droid-rage](agents/droid-rage.md), `aunit-droid-rage` |
| Swift Justice | iOS | [swift-justice](agents/swift-justice.md), `aunit-swift-justice` |
| Murdock | QA and testing | [murdock](agents/murdock.md), `aunit-murdock` |
| Pit Crew | Integration and runtime | [pit-crew](agents/pit-crew.md), `aunit-pit-crew` |
| Dock Norris | Docker, Kubernetes, and DevOps delivery | [dock-norris](agents/dock-norris.md), `aunit-dock-norris` |
| Trace Ventura | Observability, golden signals, and SLI/SLOs | [trace-ventura](agents/trace-ventura.md), `aunit-trace-ventura` |

Repo Man organizes application and library source under `src/` (including Go), tests under `tests/`, documentation under `docs/`, and IaC, Helm charts, and observability configuration under `ops/`. Its default monorepo layout uses `src/apps/<app>/` and `src/libs/<library>/`, with no application code at the repository root. It checks tool constraints and migration paths with the domain owners; existing project requirements take precedence. Use `aunit-repo-man` for layout design, implementation, or inspection-only reviews.

Each specialist supports bounded implement, investigate, or review assignments as appropriate. Model and reasoning selection inherit from the session. A fresh domain reviewer should receive the requirements, baseline/diff, edit restrictions, and evidence rather than relying on the author's summary.

Trace Ventura reuses existing telemetry and checks metrics, structured logs, distributed traces, and applicable dashboards. For services, it covers latency, traffic, errors, saturation, a clearly defined availability/uptime signal, and SLI/SLO views with targets, error budgets, and missing-data behavior. It distinguishes process uptime and scrape health from service availability. SLO targets follow project policy or remain explicitly proposed until agreed. Code without a running service still gets an observability consultation, with evidence for inapplicable signals instead of unnecessary monitoring infrastructure.

Dock Norris covers reproducible images, secure Docker/Compose setups, Kubernetes resource/probe configuration, and safe delivery/rollback practices. It coordinates runtime wiring with Pit Crew and rollout telemetry with Trace Ventura. Required routing is an instruction contract; runtime permissions and user authorization still govern all edits and deployments. Missing required specialists are reported as installation blockers. Both new definitions include authoritative best-practice links, including the Google SRE book in Trace Ventura's instructions.

Examples:

```text
$a-unit Have aunit-repo-man review our monorepo layout and propose a src/, tests/, docs/, and ops/ organization. Inspect only; do not move files.
$a-unit Fix the Python pagination regression and run the relevant tests.
$a-unit Add this API response field and expose it in the React JavaScript UI. Coordinate backend, Face, and QA ownership.
$a-unit Have a fresh aunit-face inspect the frontend diff for correctness and accessibility. Review only; do not edit.
$a-unit Add a local Docker Compose setup with Dock Norris and have Trace Ventura check the service telemetry and golden-signal dashboard.
```

Canonical `mode` describes behavioral intent. Plan Solo is inspection only; a review assignment restricts any specialist to inspection. This adapter does **not** translate `mode` into an independent sandbox or disable tools. The parent session's sandbox, approvals, and permissions govern children. Runtime-supported role tool reductions vary by Codex version; this adapter deliberately emits only name, description, and developer instructions. Target repository requirements apply within the runtime instruction hierarchy. Display names remain provisional codenames.

## Checks and compatibility evidence

```bash
.venv/bin/python aunit.py validate
.venv/bin/python -m unittest discover -s tests -v
# Optional: installed Codex + permission to bind a loopback port; no API key.
.venv/bin/python tests/codex_smoke.py
# Check a specialist's actual loading and invocation with the same fixture.
.venv/bin/python tests/codex_smoke.py --role dock-norris
.venv/bin/python tests/codex_smoke.py --role trace-ventura
.venv/bin/python tests/codex_smoke.py --role repo-man
```

In a managed environment with a separate execution server, use `tests/codex_smoke.py --work-dir /path/shared/with/that/server` if needed. The smoke check uses only temporary installations and a deterministic local Responses fixture, not a live model. It removes extracted package sources before starting Codex and verifies actual spawn/wait events and provider-bound instruction content.

| Check | Evidence in this implementation |
| --- | --- |
| Python validation, rendering, installer, local ZIP | 25 tests passed on Linux / Python 3.12 |
| Actual CLI discovery and activation | Prior roster: Codex CLI 0.159.2 on Linux advertised all 13 then-existing roles and injected the complete project skill |
| Repo Man CLI loading | Blocked in this environment: the deterministic fixture could not create its loopback socket; fourteen-role CLI discovery and Repo Man invocation remain unverified |
| Actual child invocation | Python, container/DevOps, and observability specialist fixture checks; full shared contract and role body present in child developer instructions |
| Inheritance | Child request retained parent model and reasoning; read-only parent permission context present |
| Scope behavior | Project-over-user role precedence and custom `CODEX_HOME` exercised; duplicate skill names made bare `$a-unit` ambiguous |
| Preferred user skill root | Upstream released-source conventions and path tests; real home directory left untouched by smoke tests |
| macOS / Windows | Installer designed for both; CI matrix configured, not run from this environment |
| Live-model and role quality | Not run; all language/platform roles remain unevaluated for real engineering work |

For your authenticated Ubuntu trial, install one scope, start a fresh session outside this checkout, invoke `$a-unit`, request the Python inspection above, and confirm the specialist appears in Codex's agent activity. Then try a small authorized change in a disposable repository, inspect the actual diff, and run that project's tests. Android/iOS behavior needs suitable build/device hosts before claiming coverage.

If agents are missing, check `codex --version`, the printed destinations, project trust, and multi-agent availability. If the skill is missing, check the scope table and duplicate copies, then restart Codex. A successful offline fixture does not replace that live trial.

## License

[Apache License 2.0](LICENSE).
