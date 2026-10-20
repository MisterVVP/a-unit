"""Optional offline harness check: python tests/codex_smoke.py.

Uses the installed Codex executable and a loopback Responses fixture, never a real
model or API key. This checks adapter wiring, not model judgment or engineering
quality. Needs permission to bind a local port. Does not touch user installations.
"""
import contextlib
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aunit


def message(text):
    return {"id": "msg_fixture", "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": text}]}


def tool(name, arguments, call_id):
    return {"id": "fc_" + call_id, "type": "function_call", "call_id": call_id,
            "name": name, "namespace": "multi_agent_v1", "arguments": json.dumps(arguments)}


def run(work_dir=None, role="snake-eyes"):
    executable = shutil.which("codex")
    if not executable:
        raise RuntimeError("codex is required for this optional smoke check")
    version = subprocess.check_output([executable, "--version"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="a-unit-smoke-", dir=work_dir or Path(tempfile.gettempdir()).resolve()) as tmp:
        root = Path(tmp)
        bundle = root / "package.zip"
        with contextlib.redirect_stdout(io.StringIO()):
            aunit.package(bundle)
        with zipfile.ZipFile(bundle) as archive:
            archive.extractall(root / "extracted")
        project = root / "target with spaces"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        example = project / "example.py"
        example.write_text("def answer():\n    return 42\n", encoding="utf-8")
        subprocess.run([sys.executable, str(root / "extracted/a-unit/aunit.py"), "install",
                        "--project", str(project), "--apply"], check=True, capture_output=True)
        shutil.rmtree(root / "extracted")
        target = aunit.layout(project, False)
        role_path = target.destination(f"agents/aunit-{role}.toml")
        original_role = role_path.read_text()
        import tomllib
        project_instructions = tomllib.loads(original_role)["developer_instructions"]
        skill = target.destination("skills/a-unit/SKILL.md").read_text()
        initial_files = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
        codex_home = root / "custom-codex-home"
        (codex_home / "agents").mkdir(parents=True)
        # Same role name in user and project scopes verifies native role precedence.
        (codex_home / f"agents/aunit-{role}.toml").write_text(
            f'name = "aunit-{role}"\ndescription = "USER_SCOPE_FIXTURE"\n'
            'developer_instructions = "USER_SCOPE_INSTRUCTIONS"\n', encoding="utf-8")
        # Later introduce a competing skill via the supported legacy user root.
        # This avoids writing to the real ~/.agents/skills directory.
        fallback = codex_home / "skills/a-unit/SKILL.md"
        fallback.parent.mkdir(parents=True)
        requests, failures = [], []
        phase = "project"

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                try:
                    data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    requests.append((phase, data))
                    if phase != "project":
                        item = message("USER_DONE")
                    elif any(project_instructions in c.get("text", "") for x in data["input"]
                             if x.get("role") == "developer" for c in x.get("content", [])):
                        item = message("SPECIALIST_DONE")
                    else:
                        outputs = [x for x in data["input"] if x.get("type") == "function_call_output"]
                        if not outputs:
                            item = tool("spawn_agent", {"agent_type": f"aunit-{role}", "fork_context": False,
                                        "message": "Review example.py without edits. Return a concise finding."}, "spawn")
                        elif len(outputs) == 1:
                            spawned = json.loads(outputs[0]["output"])
                            item = tool("wait_agent", {"targets": [spawned["agent_id"]], "timeout_ms": 10000}, "wait")
                        else:
                            if "SPECIALIST_DONE" not in str(outputs[-1]):
                                raise AssertionError("Child did not complete through real wait_agent")
                            item = message("MAIN_DONE")
                    response = {"id": "resp_fixture", "object": "response", "status": "completed", "output": [item],
                                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
                    events = [{"type": "response.created", "response": dict(response, status="in_progress", output=[])},
                              {"type": "response.output_item.added", "output_index": 0, "item": item},
                              {"type": "response.output_item.done", "output_index": 0, "item": item},
                              {"type": "response.completed", "response": response}]
                    payload = "".join("event: " + e["type"] + "\ndata: " + json.dumps(e) + "\n\n" for e in events).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as exc:
                    failures.append(str(exc))
                    self.send_error(500)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        config = f'''model = "aunit-fixture"
model_provider = "fixture"
model_reasoning_effort = "low"
[model_providers.fixture]
name = "Local deterministic test fixture"
base_url = "http://127.0.0.1:{server.server_port}/v1"
wire_api = "responses"
requires_openai_auth = false
[features]
apps = false
plugins = false
shell_snapshot = false
multi_agent = true
[projects.{json.dumps(str(project))}]
trust_level = "trusted"
'''
        (codex_home / "config.toml").write_text(config, encoding="utf-8")
        env = dict(os.environ, CODEX_HOME=str(codex_home), RUST_LOG="error")

        def execute(prompt):
            result = subprocess.run([executable, "exec", "--skip-git-repo-check", "--ephemeral", "--json",
                                     "--sandbox", "read-only", "-C", str(project), prompt],
                                    input="", env=env, capture_output=True, text=True, timeout=45)
            if result.returncode:
                raise AssertionError(f"Codex failed ({result.returncode}): {result.stderr[-2000:]}")
            if failures:
                raise AssertionError(failures)
            return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]

        try:
            events = execute(f"$a-unit Review example.py using aunit-{role}. Inspect only; do not edit files.")
            project_requests = [d for p, d in requests if p == "project"]
            main = project_requests[0]
            # The runtime, not the fixture, resolves and injects the explicit skill.
            main_text = json.dumps(main["input"], ensure_ascii=False)
            loaded_text = "\n".join(c.get("text", "") for x in main["input"] for c in x.get("content", []))
            assert skill.strip() in loaded_text, "Project skill was not explicitly loaded"
            assert "USER_SKILL_FIXTURE" not in main_text
            tool_text = json.dumps(main["tools"])
            assert all(f"aunit-{name}" in tool_text for name in aunit.ROSTER - {"hannibal"})
            assert "aunit-hannibal" not in tool_text
            assert "USER_SCOPE_FIXTURE" not in tool_text
            children = [d for d in project_requests if any(
                project_instructions in c.get("text", "") for x in d["input"] if x.get("role") == "developer"
                for c in x.get("content", []))]
            assert len(children) == 1, "Expected one real specialist request"
            child = children[0]
            child_developer_text = "\n".join(c.get("text", "") for x in child["input"] if x.get("role") == "developer"
                                             for c in x.get("content", []))
            assert project_instructions in child_developer_text
            assert child_developer_text.count("# Shared engineering contract") == 1
            assert child["model"] == main["model"]
            assert child.get("reasoning") == main.get("reasoning")
            assert "ReadOnly" in json.dumps(child["input"]) or "read-only" in json.dumps(child["input"])
            calls = [e["item"] for e in events if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "collab_tool_call"]
            assert any(c.get("tool") == "spawn_agent" and c.get("status") == "completed" and c.get("receiver_thread_ids") for c in calls)
            assert any(c.get("tool") in {"wait", "wait_agent"} and c.get("status") == "completed" for c in calls), calls
            assert any(e.get("item", {}).get("text") == "MAIN_DONE" for e in events)
            assert initial_files == {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
            # Remove project role to prove discovery of the same name from custom
            # CODEX_HOME without editing config.toml to declare an agent table.
            role_path.unlink()
            phase = "user"
            execute(f"Report the available aunit-{role} role. Do not use any tools.")
            user = [d for p, d in requests if p == "user"][0]
            assert "USER_SCOPE_FIXTURE" in json.dumps(user["tools"])
            fallback.write_text('---\nname: a-unit\ndescription: User fixture\n---\nUSER_SKILL_FIXTURE\n')
            phase = "ambiguous"
            execute("$a-unit Inspect only. Do not use any tools.")
            ambiguous = [d for p, d in requests if p == "ambiguous"][0]
            ambiguous_text = json.dumps(ambiguous["input"])
            assert "# Hannibal" not in ambiguous_text and "USER_SKILL_FIXTURE" not in ambiguous_text
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        print(f"PASS: {version}; {sys.platform}; local deterministic Responses fixture")
        print(f"Project skill activation, all {len(aunit.ROSTER) - 1} roles discovered, {role} spawn/wait, complete bundled instructions,")
        print("model/reasoning inheritance, read-only parent context, project-over-user role precedence, duplicate-skill ambiguity, custom CODEX_HOME,")
        print("unchanged target files, and execution after extracted package source removal.")
        print("Not tested: live-model judgment, tool-level permission enforcement, preferred user skill root, or domain engineering quality.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, help="Existing temporary root shared with a remote execution server, if used")
    parser.add_argument("--role", choices=sorted(aunit.ROSTER - {"hannibal"}), default="snake-eyes",
                        help="Specialist whose actual instruction delivery and spawn/wait are checked")
    args = parser.parse_args()
    run(args.work_dir, args.role)
