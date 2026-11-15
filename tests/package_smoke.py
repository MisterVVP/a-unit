"""Exercise published artifacts in isolated environments on any supported OS.

No imports from the source checkout: all commands run outside it, from a fresh
venv, against artifacts verified with the release checksum file.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import venv
import zipfile


def run(arguments, cwd, env=None):
    result = subprocess.run([str(arg) for arg in arguments], cwd=cwd, env=env,
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Command failed: {arguments}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def smoke(artifacts: Path, expected_version: str):
    expected_names = {f"a-unit-{expected_version}.zip", f"a_unit-{expected_version}-py3-none-any.whl"}
    checksums = {}
    for line in (artifacts / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        checksum, name = line.split("  ", 1)
        assert name in expected_names and name not in checksums, f"Unexpected artifact: {name}"
        checksums[name] = checksum
    assert checksums.keys() == expected_names, "Incomplete release"
    for name, checksum in checksums.items():
        assert hashlib.sha256((artifacts / name).read_bytes()).hexdigest() == checksum, name

    with zipfile.ZipFile(artifacts / f"a-unit-{expected_version}.zip") as archive:
        public_payload = {name.removeprefix("a-unit/"): archive.read(name) for name in archive.namelist()}
    with zipfile.ZipFile(artifacts / f"a_unit-{expected_version}-py3-none-any.whl") as archive:
        wheel_payload = {name.removeprefix("a_unit/"): archive.read(name)
                         for name in archive.namelist() if name.startswith("a_unit/")}
    assert wheel_payload == public_payload, "Wheel and ZIP public payloads differ"

    with tempfile.TemporaryDirectory(prefix="a-unit-host-") as tmp:
        host = Path(tmp).resolve()
        environment = host / "environment with spaces"
        venv.create(environment, with_pip=True)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        command = environment / ("Scripts/a-unit.exe" if os.name == "nt" else "bin/a-unit")
        clean_env = dict(os.environ, PYTHONPATH="", PYTHONUTF8="1")
        wheel = artifacts / f"a_unit-{expected_version}-py3-none-any.whl"
        run([python, "-m", "pip", "install", wheel], host, clean_env)
        assert run([command, "--version"], host, clean_env).strip() == f"a-unit {expected_version}"
        run([command, "validate"], host, clean_env)
        assert run([python, "-m", "a_unit", "--version"], host, clean_env).strip() == f"a-unit {expected_version}"
        run([python, "-c", "from importlib.metadata import version; "
             f"assert version('a-unit') == {expected_version!r}"], host, clean_env)

        with zipfile.ZipFile(artifacts / f"a-unit-{expected_version}.zip") as archive:
            archive.extractall(host / "extracted")
        bundle = host / "extracted/a-unit"
        assert (bundle / "VERSION").read_text().strip() == expected_version
        assert (bundle / "SOURCE_REVISION").read_text().strip()
        # Install via the ZIP, then update via the wheel. No checkout is used by
        # either path. User scope uses a fake home and a custom CODEX_HOME.
        home = host / "fake home"
        home.mkdir()
        user_env = dict(clean_env, HOME=str(home), USERPROFILE=str(home),
                        CODEX_HOME=str(host / "custom codex"))
        project = host / "project with spaces"
        project.mkdir()
        for scope, env, codex, skills in [
            (["--project", project], clean_env, project / ".codex", project / ".agents/skills"),
            (["--user"], user_env, host / "custom codex", home / ".agents/skills"),
        ]:
            codex.mkdir(parents=True)
            (codex / "config.toml").write_text("# preserve local config\n", encoding="utf-8")
            instructions = project / "AGENTS.md"
            instructions.write_text("Keep project policy.\n", encoding="utf-8")
            manifest = codex / "a-unit-manifest.json"
            run([python, bundle / "aunit.py", "install", *scope], host, env)
            assert not manifest.exists(), "Preview changed the host"
            run([python, bundle / "aunit.py", "install", *scope, "--apply"], host, env)
            original = json.loads(manifest.read_text(encoding="utf-8"))
            assert len(original["files"]) == 20
            assert len(list((codex / "agents").glob("*.toml"))) == 15
            assert "## Coordination procedure" in (skills / "a-unit/SKILL.md").read_text(encoding="utf-8")
            run([command, "install", *scope, "--apply"], host, env)
            assert json.loads(manifest.read_text(encoding="utf-8")) == original
            # Exercise an actual managed-content update using a prior bundle.
            role = bundle / "agents/face.md"
            current = role.read_bytes()
            role.write_bytes(current + b"\nPrior release fixture.\n")
            run([python, bundle / "aunit.py", "install", *scope, "--apply"], host, env)
            prior = (codex / "agents/aunit-face.toml").read_bytes()
            run([command, "install", *scope, "--apply"], host, env)
            assert (codex / "agents/aunit-face.toml").read_bytes() != prior
            role.write_bytes(current)
            run([command, "uninstall", *scope], host, env)
            assert manifest.exists(), "Uninstall preview changed the host"
            run([command, "uninstall", *scope, "--apply"], host, env)
            assert not manifest.exists()
            assert not list((codex / "agents").glob("aunit-*.toml"))
            assert not (skills / "a-unit/SKILL.md").exists()
            assert (codex / "config.toml").read_text() == "# preserve local config\n"
            assert instructions.read_text() == "Keep project policy.\n"
    print(f"Passed: version {expected_version}, wheel + ZIP, project + user install/update/uninstall")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    smoke(args.artifacts.resolve(), args.version)
