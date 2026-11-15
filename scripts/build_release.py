"""Build release ZIP/wheel from the public allowlist and write SHA-256 sums."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aunit


def build(output: Path, tag: str | None = None) -> None:
    version = aunit.version()
    if tag is not None and tag != f"v{version}":
        raise aunit.Error(f"Tag {tag!r} does not match VERSION (v{version})")
    if tag and (aunit.revision() or "").endswith("+dirty"):
        raise aunit.Error("Release builds require a clean checkout")
    if output.exists():
        raise aunit.Error(f"Release output must be a new directory: {output}")
    # Stage the complete release before exposing it. Build the wheel from the
    # same allowlisted sources as the ZIP, never from the unrestricted checkout.
    with tempfile.TemporaryDirectory(prefix="a-unit-release-") as tmp:
        staging = Path(tmp)
        artifacts = staging / "artifacts"
        artifacts.mkdir()
        bundle = artifacts / f"a-unit-{version}.zip"
        aunit.package(bundle)
        with zipfile.ZipFile(bundle) as archive:
            archive.extractall(staging / "source")
        subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(artifacts),
                        str(staging / "source/a-unit")], check=True)
        sums = "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
                       for path in sorted(artifacts.iterdir()))
        (artifacts / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="\n")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(artifacts, output)
    print(f"Release {version}: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tag", help="Require this release tag to match VERSION")
    args = parser.parse_args()
    try:
        build(args.output.resolve(), args.tag)
    except (aunit.Error, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"error: {exc}\n")
