# A-Unit

**No Gods. No Masters. Just Agents.**

A portable engineering squad for Codex CLI: Hannibal coordinates your main session and calls fifteen focused specialists. Installed definitions contain the complete shared engineering contract, role instructions, and applicable offline guidance. The source checkout is not needed at runtime.

**Status: Codex CLI preview with versioned packaging.** A-Unit builds a universal Python wheel and portable ZIP for GitHub Releases. CI exercises installation, updates, and removal on Ubuntu, macOS, and Windows with Python 3.11 and 3.13. Codex adapter wiring has been exercised on Linux with CLI **0.159.2** using an offline fixture; live-model engineering quality and native macOS/Windows Codex runtime behavior remain unverified. Other runtime adapters are deferred.

[Packaging CI](https://github.com/MisterVVP/a-unit/actions/workflows/checks.yml) · [Releases](https://github.com/MisterVVP/a-unit/releases)

## Install a specific version

Prerequisites: Python **3.11+** with pip/venv, and Codex CLI. Use Codex **0.159.2** as the compatibility baseline; older versions are unverified. Authenticate Codex normally (`codex login`). Git is optional for release installations.

Packages are hosted as **GitHub Release assets**. GitHub Packages has no Python package registry. Use an exact release URL to select a version; the commands below use `0.1.0` as an example and require that release to have been published. See [Releases](https://github.com/MisterVVP/a-unit/releases) for available versions.

On Linux or macOS:

```bash
VERSION=0.1.0
python3 -m venv .a-unit-venv
.a-unit-venv/bin/python -m pip install "https://github.com/MisterVVP/a-unit/releases/download/v${VERSION}/a_unit-${VERSION}-py3-none-any.whl"
.a-unit-venv/bin/a-unit --version
.a-unit-venv/bin/a-unit install --user
.a-unit-venv/bin/a-unit install --user --apply
```

On Windows, in PowerShell:

```powershell
$Version = '0.1.0'
py -3.11 -m venv .a-unit-venv
.\.a-unit-venv\Scripts\python.exe -m pip install "https://github.com/MisterVVP/a-unit/releases/download/v$Version/a_unit-$Version-py3-none-any.whl"
.\.a-unit-venv\Scripts\a-unit.exe --version
.\.a-unit-venv\Scripts\a-unit.exe install --user
.\.a-unit-venv\Scripts\a-unit.exe install --user --apply
```

A newer Python also works; adjust the launcher selection. These commands require no environment activation or PowerShell execution-policy change. Below, `a-unit` means the executable in this virtual environment; use its full path or add the environment's executable directory to your PATH.

The package installs the `a-unit` utility first. `a-unit install` previews the Codex files, and `--apply` writes them. Keep the utility environment for updates and uninstalling; Codex itself uses only the installed definitions.

For an offline host, download the wheel and its PyYAML dependency on a machine with the same OS/Python/architecture using `python -m pip download --dest wheelhouse <exact-wheel-URL>`. Transfer `wheelhouse`, then use `python -m pip install --no-index --find-links wheelhouse a-unit==0.1.0` inside the host's environment.

## Use the squad

Start a **new** Codex session in the repository you want to work on:

```bash
cd /path/to/your/project
codex
```

Explicitly invoke the activation skill:

```text
$a-unit Investigate this repository and propose a small, testable Python improvement. Do not edit yet.
```

Hannibal stays in the main session. Coding tasks include Trace Ventura's observability consultation and a fresh Lint Eastwood review of the final diff. Container and Kubernetes work includes Dock Norris. Other specialists are selected as useful. To request one explicitly:

```text
$a-unit Use aunit-snake-eyes for an inspection-only review of the Python code. Report findings and checks; do not edit files.
```

If multi-agent support is disabled, enable it for the session with `codex --enable multi_agent`. Installation does not change model settings, feature flags, concurrency, or permissions. Canonical read-only modes describe behavior; runtime permissions come from the parent Codex session.

## Installation scope

Choose **one scope**. For a squad pinned to an existing project, use an explicit path instead of `--user`:

```bash
a-unit install --project "/path/to/your/project"
a-unit install --project "/path/to/your/project" --apply
```

Quote paths containing spaces on every OS. The working directory never implicitly selects the target project. Existing `AGENTS.md`, `config.toml`, and unrelated files remain untouched. The [project instruction template](templates/AGENTS.md) is an optional manual starting point.

| Artifact | User scope | Project scope |
| --- | --- | --- |
| Fifteen agent TOMLs | `$CODEX_HOME/agents/aunit-*.toml` (default `~/.codex/agents`) | `<project>/.codex/agents/aunit-*.toml` |
| Hannibal activation skill | `~/.agents/skills/a-unit/` | `<project>/.agents/skills/a-unit/` |
| Ownership manifest | `$CODEX_HOME/a-unit-manifest.json` | `<project>/.codex/a-unit-manifest.json` |

`CODEX_HOME` changes the user agent destination; the user skill destination remains `~/.agents/skills`. Set it consistently when installing, running Codex, updating, and uninstalling. On Windows, `~` denotes your user profile.

Project roles take precedence over user roles in a trusted project. Duplicate `a-unit` skills across scopes (including the legacy `$CODEX_HOME/skills` directory) can make `$a-unit` ambiguous. Remove the unwanted installation or select the intended skill with Codex's skill picker, then start a fresh session. Use Codex's normal project trust process.

## Update and uninstall

To update or select an older version, install that exact release wheel into the same utility environment with `python -m pip install --upgrade <exact-wheel-URL>`, then rerun `a-unit install` with the same scope and `--apply`. Changing the Python package alone does not update installed Codex definitions.

```bash
a-unit uninstall --user
a-unit uninstall --user --apply
# Or: a-unit uninstall --project "/path/to/project" [--apply]
```

Uninstall the definitions before deleting the utility environment. `pip uninstall a-unit` only removes the utility package.

Installation previews by default. Ownership hashes protect existing files: identical reinstallations do nothing; updates replace unchanged managed files and remove unchanged stale artifacts. Unowned collisions and locally edited managed files block updates. Save or move conflicting files before retrying; there is no force overwrite. Existing symlink/reparse-point destinations are refused.

Uninstall preserves edited files, reports them, and exits with status 1 when manual cleanup is still needed. Keep the ownership manifest until removal is complete. Ordinary write/remove failures attempt rollback and report recovery paths if needed; run one installer at a time. Recovery from power loss or process termination is not guaranteed.

## Build and publish

Before the first release, you can install from a checkout with `python -m pip install .` in a virtual environment, then use the same `a-unit` commands. To build release assets locally:

```bash
python -m pip install -r requirements.txt build
python scripts/build_release.py --output dist
```

The output directory must be new. A release contains `a_unit-<version>-py3-none-any.whl`, `a-unit-<version>.zip`, and `SHA256SUMS`. The ZIP can also be extracted and used with `python aunit.py` after installing its `requirements.txt`. Both formats contain only allowlisted public sources; neither includes repository instructions, private notes, tests, or Git history.

Maintainers publish by committing the desired `VERSION` (`MAJOR.MINOR.PATCH`) and pushing its matching tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Use a new version and tag for each release. The release workflow rejects mismatched versions, builds once, verifies those artifacts across all three operating systems, then publishes them using GitHub's built-in token. It downloads the published version and repeats installation checks on each OS. Pull requests emulate the same host lifecycle using downloaded CI artifacts without publishing a release. Each release's checksums can be used to verify downloaded assets (`sha256sum -c SHA256SUMS`, `shasum -a 256 -c SHA256SUMS`, or PowerShell `Get-FileHash -Algorithm SHA256`).

## The gang

| Agent | Specialty | Definition / installed role |
| --- | --- | --- |
| Hannibal | Main-session commander | [hannibal](agents/hannibal.md), via `$a-unit` |
| Lint Eastwood | Code quality, lint evidence, maintainability, security, and performance review | [lint-eastwood](agents/lint-eastwood.md), `aunit-lint-eastwood` |
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


## Troubleshooting

If roles are missing, check `codex --version`, the printed destinations, project trust, and multi-agent availability. If the skill is missing, check scope and duplicate copies, then restart Codex. Platform installation tests cover file delivery and lifecycle; live tasks, Android/iOS builds, and native Codex runtime behavior need their own suitable hosts.

## License

[Apache License 2.0](LICENSE).
