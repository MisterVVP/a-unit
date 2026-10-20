#!/usr/bin/env python3
"""Validate, package, and install A-Unit's Codex CLI adapter (Python 3.11+)."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required. Install requirements.txt in your Python environment.")

ROOT = Path(__file__).resolve().parent
FORMAT_VERSION = 1
IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
ROSTER = frozenset("hannibal plan-solo baracus go-rilla snake-eyes nodefather sharp-shooter face droid-rage swift-justice murdock pit-crew dock-norris trace-ventura repo-man lint-eastwood".split())


class Error(Exception):
    """An actionable validation or installation error."""


class UniqueSafeLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise Error("Frontmatter keys must be unique strings")
        result[key] = loader.construct_object(value_node)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    mode: str
    body: str


def text_file(path: Path) -> str:
    # Universal newlines make Windows checkouts render identically to Unix checkouts.
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise Error(f"Cannot read {path}: {exc}") from exc
    if not text.strip():
        raise Error(f"Required content is empty: {path}")
    return text


def sources(root: Path = ROOT) -> tuple[str, list[Role]]:
    contract = text_file(root / "agents/_shared/engineering-contract.md")
    roles = []
    names = set()
    for path in sorted((root / "agents").glob("*.md")):
        match = re.fullmatch(r"---\n(.*?)\n---\n(.*)", text_file(path), re.DOTALL)
        if not match:
            raise Error(f"Missing or malformed frontmatter: {path}")
        try:
            data = yaml.load(match[1], Loader=UniqueSafeLoader)
        except yaml.YAMLError as exc:
            raise Error(f"Invalid YAML in {path}: {exc}") from exc
        if not isinstance(data, dict) or set(data) != {"name", "description", "mode"}:
            raise Error(f"Expected exactly name, description, mode in {path}")
        if not all(isinstance(value, str) and value.strip() for value in data.values()):
            raise Error(f"Metadata must contain nonempty strings: {path}")
        name = data["name"]
        if not IDENTIFIER.fullmatch(name) or name != path.stem or name in names:
            raise Error(f"Invalid, duplicate, or mismatched name in {path}")
        if data["mode"] not in {"read-only", "write"}:
            raise Error(f"Invalid mode in {path}")
        body = match[2]
        if not body.strip():
            raise Error(f"Empty role body in {path}")
        if contract in body:
            raise Error(f"Shared contract already embedded in {path}")
        roles.append(Role(name, data["description"], data["mode"], body))
        names.add(name)
    if names != ROSTER:
        raise Error(f"Roster mismatch; missing={sorted(ROSTER - names)}, unexpected={sorted(names - ROSTER)}")
    return contract, roles


def compose(contract: str, role: Role) -> str:
    """Vendor-neutral, lossless shared-contract + role-body composition."""
    return contract + "\n\n" + role.body


def render(root: Path = ROOT) -> dict[str, bytes]:
    contract, roles = sources(root)
    artifacts = {}
    for role in roles:
        if role.name == "hannibal":
            continue
        fields = {"name": f"aunit-{role.name}", "description": role.description,
                  "developer_instructions": compose(contract, role)}
        # JSON basic strings are valid TOML basic strings; ensure_ascii=False avoids
        # JSON surrogate escapes, which TOML does not allow for non-BMP characters.
        content = "".join(f"{key} = {json.dumps(value, ensure_ascii=False)}\n" for key, value in fields.items())
        artifacts[f"agents/aunit-{role.name}.toml"] = content.encode("utf-8")
    commander = next(role for role in roles if role.name == "hannibal")
    header = "---\nname: a-unit\ndescription: Coordinate engineering with Hannibal in the main session and A-Unit specialists. Invoke explicitly for implementation, investigation, or review.\n---\n\n"
    routing = "\n\n## Codex CLI activation and routing\n\n" + (
        "Act as Hannibal in this main session. Do not spawn Hannibal. Use the installed "
        "specialist agent_type names below for bounded assignments. For custom roles, "
        "start a fresh agent without full-history inheritance (fork_turns=none when "
        "that option is exposed). Give it the necessary evidence and ownership in the "
        "assignment. Omit model and reasoning overrides to inherit session defaults. "
        "If a role is unavailable, report it and check installation; do not silently "
        "substitute an unconfigured agent. Read-only and review constraints are behavioral; "
        "runtime permissions come from the parent session.\n\n"
    )
    routing += "\n".join(f"- `aunit-{r.name}`: {r.description} Default intent: {r.mode}." for r in roles if r.name != "hannibal") + "\n"
    artifacts["skills/a-unit/SKILL.md"] = (header + compose(contract, commander) + routing).encode("utf-8")
    artifacts["skills/a-unit/agents/openai.yaml"] = b"policy:\n  allow_implicit_invocation: false\n"
    return artifacts


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_path(path: Path) -> None:
    for part in reversed((path, *path.parents)):
        reparse = (getattr(part.lstat(), "st_file_attributes", 0) &
                   getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)) if part.exists() else 0
        if part.is_symlink() or reparse:
            raise Error(f"Symlink destinations are not supported: {part}")
        if part.exists() and part != path and not part.is_dir():
            raise Error(f"Destination parent is not a directory: {part}")
    if path.exists() and not path.is_file():
        raise Error(f"Destination is not a regular file: {path}")


@dataclass(frozen=True)
class Layout:
    codex: Path
    skills: Path

    @property
    def manifest(self) -> Path:
        return self.codex / "a-unit-manifest.json"

    def destination(self, key: str) -> Path:
        if re.fullmatch(r"agents/aunit-[a-z][a-z0-9]*(?:-[a-z0-9]+)*\.toml", key):
            return self.codex / key
        if key in {"skills/a-unit/SKILL.md", "skills/a-unit/agents/openai.yaml"}:
            return self.skills / key.removeprefix("skills/")
        raise Error(f"Unsafe or unsupported managed path: {key!r}")


def layout(project: Path | None, user: bool, codex_home: Path | None = None,
           user_home: Path | None = None) -> Layout:
    if project is not None:
        project = Path(os.path.abspath(project.expanduser()))
        if not project.is_dir():
            raise Error(f"Project directory does not exist: {project}")
        return Layout(project / ".codex", project / ".agents/skills")
    if not user:
        raise Error("Choose --user or --project PATH explicitly")
    home = user_home or Path.home()
    configured = codex_home or Path(os.environ.get("CODEX_HOME") or home / ".codex")
    return Layout(Path(os.path.abspath(configured.expanduser())), home / ".agents/skills")


def read_manifest(target: Layout) -> dict | None:
    safe_path(target.manifest)
    if not target.manifest.exists():
        return None
    try:
        data = json.loads(target.manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Error(f"Cannot read ownership manifest: {exc}") from exc
    if (not isinstance(data, dict) or set(data) != {"package", "format_version", "source_revision", "files"}
            or data["package"] != "a-unit" or type(data["format_version"]) is not int
            or data["format_version"] != FORMAT_VERSION or not isinstance(data["files"], dict)
            or not (data["source_revision"] is None or isinstance(data["source_revision"], str))):
        raise Error("Invalid or unsupported ownership manifest")
    for key, value in data["files"].items():
        target.destination(key)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise Error(f"Invalid managed hash for {key}")
    return data


def revision(root: Path = ROOT) -> str | None:
    # git metadata is optional (e.g. an extracted package). Never require Git.
    try:
        if not (root / ".git").exists():
            return text_file(root / "SOURCE_REVISION").strip() if (root / "SOURCE_REVISION").exists() else None
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True, check=True)
        return result.stdout.strip() + ("+dirty" if dirty.stdout else "")
    except (OSError, subprocess.CalledProcessError):
        return None


@dataclass
class Plan:
    changes: dict[Path, bytes | None]
    preserved: list[Path]
    expected: dict[Path, bytes | None] = field(default_factory=dict)

    def show(self) -> None:
        for path, content in self.changes.items():
            action = "remove" if content is None else ("update" if path.exists() else "create")
            print(f"{action}: {path}")
        for path in self.preserved:
            print(f"preserve modified: {path}")
        if not self.changes:
            print("No changes.")


def install_plan(target: Layout, artifacts: dict[str, bytes], source_revision: str | None) -> Plan:
    old = read_manifest(target)
    owned = old["files"] if old else {}
    changes = {}
    expected = {target.manifest: target.manifest.read_bytes() if old else None}
    # Inspect every current and stale artifact before planning any writes.
    for key in sorted(owned.keys() | artifacts.keys()):
        path = target.destination(key)
        safe_path(path)
        current = path.read_bytes() if path.exists() else None
        expected[path] = current
        if current is not None:
            if key not in owned:
                raise Error(f"Unowned file collision: {path}")
            if digest(current) != owned[key]:
                raise Error(f"Locally modified managed file: {path}; save or move it before retrying")
        desired = artifacts.get(key)
        if desired != current:
            changes[path] = desired
    data = {"package": "a-unit", "format_version": FORMAT_VERSION,
            "source_revision": source_revision, "files": {k: digest(v) for k, v in sorted(artifacts.items())}}
    # Source metadata alone need not rewrite an otherwise identical installation.
    if old and old["files"] == data["files"] and not changes:
        return Plan({}, [], expected)
    encoded = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    if not target.manifest.exists() or target.manifest.read_bytes() != encoded:
        changes[target.manifest] = encoded
    return Plan(changes, [], expected)


def uninstall_plan(target: Layout) -> Plan:
    old = read_manifest(target)
    if old is None:
        return Plan({}, [])
    changes, preserved, remaining = {}, [], {}
    expected_state = {target.manifest: target.manifest.read_bytes()}
    for key, expected in sorted(old["files"].items()):
        path = target.destination(key)
        safe_path(path)
        expected_state[path] = path.read_bytes() if path.exists() else None
        if not path.exists():
            continue
        if digest(path.read_bytes()) == expected:
            changes[path] = None
        else:
            preserved.append(path)
            remaining[key] = expected
    if remaining:
        data = {**old, "files": remaining}
        encoded = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
        if target.manifest.read_bytes() != encoded:
            changes[target.manifest] = encoded
    else:
        changes[target.manifest] = None
    return Plan(changes, preserved, expected_state)


def atomic_write(path: Path, content: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".a-unit-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_plan(plan: Plan) -> None:
    if not plan.changes:
        return
    for path, expected in plan.expected.items():
        safe_path(path)
        if (path.read_bytes() if path.exists() else None) != expected:
            raise Error(f"Destination changed after preview: {path}; retry to preview again")
    # Back up all affected bytes on disk before the first replacement. Backups
    # survive failed rollback; success and successful rollback clean them up.
    backup = Path(tempfile.mkdtemp(prefix="a-unit-recovery-"))
    original, changed, created_dirs = {}, [], []
    try:
        for index, path in enumerate(plan.changes):
            safe_path(path)
            saved = backup / str(index)
            if path.exists():
                shutil.copyfile(path, saved)
                original[path] = saved
            else:
                original[path] = None
        (backup / "paths.json").write_text(json.dumps({str(i): str(p) for i, p in enumerate(plan.changes)}, indent=2), encoding="utf-8")
        for path, content in plan.changes.items():
            safe_path(path)
            if path in plan.expected and (path.read_bytes() if path.exists() else None) != plan.expected[path]:
                raise Error(f"Destination changed during installation: {path}")
            if content is None:
                path.unlink()
            else:
                missing = []
                parent = path.parent
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for directory in reversed(missing):
                    directory.mkdir()
                    created_dirs.append(directory)
                atomic_write(path, content)
            changed.append(path)
    except (OSError, Error) as exc:
        failures = []
        for path in reversed(changed):
            try:
                saved = original[path]
                if saved is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, saved.read_bytes())
            except OSError as restore_error:
                failures.append(f"{path}: {restore_error}")
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        if failures:
            raise Error(f"Installation failed: {exc}. Recovery incomplete: {failures}. Backups: {backup}") from exc
        shutil.rmtree(backup)
        raise Error(f"Installation failed; previous file contents restored: {exc}") from exc
    shutil.rmtree(backup)


def package(path: Path, root: Path = ROOT) -> None:
    sources(root)
    files = [root / "aunit.py", root / "requirements.txt", root / "README.md", root / "LICENSE",
             root / "templates/AGENTS.md", root / "agents/_shared/engineering-contract.md"]
    files += sorted((root / "agents").glob("*.md"))
    payload = {str(p.relative_to(root)): p.read_bytes() for p in files}
    payload["SOURCE_REVISION"] = ((revision(root) or "unknown") + "\n").encode()
    safe_path(path)
    if path.exists():
        raise Error(f"Package output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Fixed timestamps, permissions, order, and no host-specific paths.
    with tempfile.TemporaryDirectory(prefix="a-unit-package-") as staging:
        staged = Path(staging) / "package.zip"
        with zipfile.ZipFile(staged, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(payload.items()):
                info = zipfile.ZipInfo(f"a-unit/{name}")
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content)
        atomic_write(path, staged.read_bytes())
    print(f"Packaged: {path}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate canonical sources")
    p = sub.add_parser("render", help="Render standalone Codex artifacts into a new directory")
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("package", help="Build a portable local ZIP with allowlisted public sources")
    p.add_argument("--output", type=Path, default=Path("dist/a-unit-codex.zip"))
    for command in ("install", "uninstall"):
        p = sub.add_parser(command, help=f"Preview {command}; add --apply to write")
        scope = p.add_mutually_exclusive_group(required=True)
        scope.add_argument("--user", action="store_true", help="Personal squad for all projects")
        scope.add_argument("--project", type=Path, help="Explicit existing target project")
        p.add_argument("--apply", action="store_true", help="Apply the printed, preflighted plan")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            contract, roles = sources()
            print(f"Valid: {len(roles)} roles and shared contract ({len(contract)} characters)")
        elif args.command == "package":
            package(args.output.absolute())
        elif args.command == "render":
            artifacts = render()
            output = args.output.absolute()
            # Check parents without demanding that the output directory be a file.
            safe_path(output / ".a-unit-render-check")
            if output.exists():
                raise Error(f"Render output must be a new directory: {output}")
            apply_plan(Plan({output / key: value for key, value in artifacts.items()}, []))
            print(f"Rendered: {len(ROSTER) - 1} subagents and 1 activation skill in {output}")
        else:
            target = layout(args.project, args.user)
            plan = (install_plan(target, render(), revision()) if args.command == "install"
                    else uninstall_plan(target))
            plan.show()
            if args.apply:
                apply_plan(plan)
                print("Applied.")
            else:
                print("Preview only. Add --apply to write these changes.")
            if plan.preserved:
                return 1
        return 0
    except (Error, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
