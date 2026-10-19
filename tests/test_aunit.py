import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile

import aunit


class Sources(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.root = Path(self.tmp.name)
        shutil.copytree(aunit.ROOT / 'agents', self.root / 'agents')
        self.addCleanup(self.tmp.cleanup)

    def alter(self, before, after, name='face'):
        p = self.root / f'agents/{name}.md'
        p.write_text(p.read_text().replace(before, after), encoding='utf-8')

    def test_valid_sources_and_modes(self):
        shared, roles = aunit.sources(self.root)
        self.assertEqual(12, len(roles))
        self.assertTrue(shared.strip())
        self.assertEqual(['plan-solo'], [r.name for r in roles if r.mode == 'read-only'])

    def test_invalid_metadata(self):
        invalid = [
            ('name: face', 'name: face\nname: face'),
            ('name: face', 'name: face\nunknown: yes'),
            ('name: face', 'name: ../face'),
            ('name: face', 'name: Face'),
            ('name: face', 'name: nodefather'),
            ('name: face', 'name: [face]'),
            ('name: face', 'name: true'),
            ('mode: write', 'mode: execute'),
            ('mode: write', 'mode: null'),
            ('mode: write\n', ''),
            ('name: face', 'name: !!python/object/apply:os.system [echo unsafe]'),
        ]
        p = self.root / 'agents/face.md'
        original = p.read_text()
        for before, after in invalid:
            with self.subTest(after=after):
                p.write_text(original.replace(before, after))
                with self.assertRaises(aunit.Error):
                    aunit.render(self.root)
        p.write_text(original)

    def test_blank_description_and_body(self):
        p = self.root / 'agents/face.md'
        original = p.read_text()
        for source in [original.split('description:')[0] + 'description: " "\nmode: write\n---\nbody',
                       '---\nname: face\ndescription: React\nmode: write\n---\n \n',
                       'name: face\nno frontmatter']:
            with self.subTest(source=source):
                p.write_text(source)
                with self.assertRaises(aunit.Error):
                    aunit.render(self.root)

    def test_missing_role_or_extra_role(self):
        p = self.root / 'agents/face.md'
        p.unlink()
        with self.assertRaises(aunit.Error):
            aunit.sources(self.root)
        p.write_text('---\nname: face\ndescription: React\nmode: write\n---\nbody')
        (self.root / 'agents/rogue.md').write_text('---\nname: rogue\ndescription: Rogue\nmode: write\n---\nbody')
        with self.assertRaises(aunit.Error):
            aunit.sources(self.root)

    def test_missing_empty_and_duplicate_shared_contract(self):
        p = self.root / 'agents/_shared/engineering-contract.md'
        original = p.read_text()
        for content in ['', '  \n']:
            p.write_text(content)
            with self.assertRaises(aunit.Error):
                aunit.render(self.root)
        p.unlink()
        with self.assertRaises(aunit.Error):
            aunit.render(self.root)
        p.write_text(original)
        with (self.root / 'agents/face.md').open('a') as stream:
            stream.write(original)
        with self.assertRaises(aunit.Error):
            aunit.render(self.root)

    def test_lossless_deterministic_vendor_serialization(self):
        unusual = '\nQuotes """ and \'\'\', slash \\, tab\t, Unicode українська 🐍 and control \x01\n'
        for p in [self.root / 'agents/face.md', self.root / 'agents/_shared/engineering-contract.md']:
            with p.open('a', encoding='utf-8') as stream:
                stream.write(unusual)
        shared, roles = aunit.sources(self.root)
        files = aunit.render(self.root)
        self.assertEqual(files, aunit.render(self.root))
        self.assertEqual(13, len(files))
        for role in roles:
            composed = aunit.compose(shared, role)
            if role.name == 'hannibal':
                content = files['skills/a-unit/SKILL.md'].decode()
                self.assertIn(composed, content)
                self.assertEqual(1, content.count('## Coordination procedure'))
            else:
                parsed = tomllib.loads(files[f'agents/aunit-{role.name}.toml'].decode())
                self.assertEqual({'name', 'description', 'developer_instructions'}, set(parsed))
                self.assertEqual(composed, parsed['developer_instructions'])
                content = parsed['developer_instructions']
            self.assertEqual(1, content.count(shared))
            self.assertLess(content.index(shared), content.index(role.body))
        self.assertNotIn('agents/aunit-hannibal.toml', files)
        policy = aunit.yaml.safe_load(files['skills/a-unit/agents/openai.yaml'])
        self.assertIs(False, policy['policy']['allow_implicit_invocation'])

    def test_crlf_checkout_produces_same_output(self):
        before = aunit.render(self.root)
        for path in (self.root / 'agents').rglob('*.md'):
            path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
        self.assertEqual(before, aunit.render(self.root))


class Installation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.project = self.root / 'project with spaces'
        self.project.mkdir()
        self.target = aunit.layout(self.project, False)
        self.artifacts = aunit.render()

    def install(self, artifacts=None):
        plan = aunit.install_plan(self.target, artifacts or self.artifacts, 'test-revision')
        aunit.apply_plan(plan)
        return plan

    def tree(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_scope_paths(self):
        self.assertEqual(self.project / '.codex/agents/aunit-face.toml', self.target.destination('agents/aunit-face.toml'))
        self.assertEqual(self.project / '.agents/skills/a-unit/SKILL.md', self.target.destination('skills/a-unit/SKILL.md'))
        home, configured = self.root / 'home', self.root / 'alternate codex'
        with patch.dict(os.environ, {'CODEX_HOME': str(configured)}):
            user = aunit.layout(None, True, user_home=home)
            self.assertEqual(configured, user.codex)
            self.assertEqual(home / '.agents/skills', user.skills)
        with patch.dict(os.environ, {'CODEX_HOME': ''}):
            self.assertEqual(home / '.codex', aunit.layout(None, True, user_home=home).codex)
        with self.assertRaises(aunit.Error):
            aunit.layout(None, False)
        with self.assertRaises(aunit.Error):
            aunit.layout(self.root / 'missing', False)

    def test_preview_and_idempotent_install(self):
        self.assertEqual({}, self.tree())
        plan = aunit.install_plan(self.target, self.artifacts, 'rev')
        self.assertFalse(self.target.manifest.exists())
        self.assertEqual(14, len(plan.changes))
        aunit.apply_plan(plan)
        before = self.tree()
        mtimes = {p: p.stat().st_mtime_ns for p in self.project.rglob('*') if p.is_file()}
        self.install()
        self.assertEqual(before, self.tree())
        self.assertEqual(mtimes, {p: p.stat().st_mtime_ns for p in mtimes})
        data = json.loads(self.target.manifest.read_text())
        self.assertEqual('rev', data['source_revision'])
        self.assertEqual(1, data['format_version'])

    def test_preserves_project_policy_config_and_unrelated_files(self):
        originals = {'AGENTS.md': b'Project rules', '.codex/config.toml': b'model = "own-model"\n',
                     '.codex/agents/other.toml': b'other', '.agents/skills/other/SKILL.md': b'other skill'}
        for key, value in originals.items():
            path = self.project / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        self.install()
        aunit.apply_plan(aunit.uninstall_plan(self.target))
        self.assertFalse(self.target.manifest.exists())
        for key, value in originals.items():
            self.assertEqual(value, (self.project / key).read_bytes())

    def test_unowned_identical_content_is_still_a_collision(self):
        path = self.target.destination('skills/a-unit/SKILL.md')
        path.parent.mkdir(parents=True)
        path.write_bytes(self.artifacts['skills/a-unit/SKILL.md'])
        before = self.tree()
        with self.assertRaisesRegex(aunit.Error, 'Unowned'):
            self.install()
        self.assertEqual(before, self.tree())

    def test_modified_file_blocks_update_before_any_writes(self):
        self.install()
        self.target.destination('skills/a-unit/SKILL.md').write_text('My customization')
        before = self.tree()
        with self.assertRaisesRegex(aunit.Error, 'Locally modified'):
            self.install()
        self.assertEqual(before, self.tree())

    def test_upgrades_and_stale_artifacts(self):
        self.install()
        newer = dict(self.artifacts)
        newer.pop('agents/aunit-baracus.toml')
        newer['agents/aunit-face.toml'] += b'# new adapter revision\n'
        self.install(newer)
        self.assertFalse(self.target.destination('agents/aunit-baracus.toml').exists())
        self.assertEqual(newer['agents/aunit-face.toml'], self.target.destination('agents/aunit-face.toml').read_bytes())
        self.assertEqual(set(newer), set(json.loads(self.target.manifest.read_text())['files']))

    def test_modified_stale_artifact_blocks_upgrade(self):
        self.install()
        self.target.destination('agents/aunit-baracus.toml').write_text('local changes')
        newer = dict(self.artifacts)
        newer.pop('agents/aunit-baracus.toml')
        before = self.tree()
        with self.assertRaises(aunit.Error):
            self.install(newer)
        self.assertEqual(before, self.tree())

    def test_missing_owned_file_can_be_repaired(self):
        self.install()
        path = self.target.destination('agents/aunit-face.toml')
        path.unlink()
        self.install()
        self.assertEqual(self.artifacts['agents/aunit-face.toml'], path.read_bytes())

    def test_uninstall_preserves_and_reports_local_changes(self):
        self.install()
        path = self.target.destination('agents/aunit-face.toml')
        original = path.read_bytes()
        path.write_text('local changes')
        plan = aunit.uninstall_plan(self.target)
        self.assertEqual([path], plan.preserved)
        aunit.apply_plan(plan)
        self.assertEqual('local changes', path.read_text())
        self.assertEqual(['agents/aunit-face.toml'], list(json.loads(self.target.manifest.read_text())['files']))
        path.write_bytes(original)
        aunit.apply_plan(aunit.uninstall_plan(self.target))
        self.assertEqual({}, aunit.uninstall_plan(self.target).changes)

    def test_manifest_validation_and_path_traversal(self):
        self.install()
        manifest = self.target.manifest.read_bytes()
        for content in [b'not JSON', b'[]', manifest.replace(b'"format_version": 1', b'"format_version": 99'),
                        manifest.replace(b'agents/aunit-face.toml', b'../outside'),
                        manifest.replace(b'agents/aunit-face.toml', b'/absolute'),
                        manifest.replace(b'agents/aunit-face.toml', b'agents\\\\aunit-face.toml')]:
            with self.subTest(content=content[:70]):
                self.target.manifest.write_bytes(content)
                before = self.tree()
                with self.assertRaises(aunit.Error):
                    self.install()
                with self.assertRaises(aunit.Error):
                    aunit.uninstall_plan(self.target)
                self.assertEqual(before, self.tree())
        self.target.manifest.write_bytes(manifest)

    def test_symlink_parent_file_and_manifest_are_refused(self):
        other = self.root / 'outside'
        other.mkdir()
        link = self.project / '.codex'
        try:
            link.symlink_to(other, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Host does not permit symlinks')
        with self.assertRaises(aunit.Error):
            self.install()
        self.assertEqual([], list(other.iterdir()))
        link.unlink()
        self.install()
        path = self.target.destination('agents/aunit-face.toml')
        path.unlink()
        path.symlink_to(other / 'missing')
        with self.assertRaises(aunit.Error):
            self.install()
        with self.assertRaises(aunit.Error):
            aunit.uninstall_plan(self.target)
        path.unlink()
        self.target.manifest.unlink()
        self.target.manifest.symlink_to(other / 'missing')
        with self.assertRaises(aunit.Error):
            self.install()

    def test_directory_collision_fails_before_writes(self):
        self.target.destination('agents/aunit-face.toml').mkdir(parents=True)
        before = self.tree()
        with self.assertRaises(aunit.Error):
            self.install()
        self.assertEqual(before, self.tree())

    def test_changed_after_preview_is_preserved(self):
        self.install()
        newer = dict(self.artifacts)
        newer['agents/aunit-face.toml'] += b'# update\n'
        plan = aunit.install_plan(self.target, newer, 'new-rev')
        path = self.target.destination('agents/aunit-face.toml')
        path.write_text('concurrent edit')
        before = self.tree()
        with self.assertRaisesRegex(aunit.Error, 'changed after preview'):
            aunit.apply_plan(plan)
        self.assertEqual(before, self.tree())

    def test_partial_install_and_update_roll_back(self):
        real_write = aunit.atomic_write
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    self.install()
                before = self.tree()
                newer = {k: v + b'\n' for k, v in self.artifacts.items()}
                plan = aunit.install_plan(self.target, newer, 'next')
                calls = 0

                def failing_write(path, content):
                    nonlocal calls
                    calls += 1
                    if calls == 3:
                        raise OSError('injected disk failure')
                    real_write(path, content)

                with patch('aunit.atomic_write', side_effect=failing_write):
                    with self.assertRaisesRegex(aunit.Error, 'previous file contents restored'):
                        aunit.apply_plan(plan)
                self.assertEqual(before, self.tree())

    def test_partial_uninstall_rolls_back(self):
        self.install()
        before = self.tree()
        real_unlink = Path.unlink
        calls = 0

        def failing_unlink(path, *args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError('injected remove failure')
            return real_unlink(path, *args, **kwargs)

        with patch.object(Path, 'unlink', failing_unlink):
            with self.assertRaisesRegex(aunit.Error, 'previous file contents restored'):
                aunit.apply_plan(aunit.uninstall_plan(self.target))
        self.assertEqual(before, self.tree())

    def test_invalid_source_does_not_create_destinations(self):
        source = self.root / 'source'
        shutil.copytree(aunit.ROOT / 'agents', source / 'agents')
        (source / 'agents/_shared/engineering-contract.md').unlink()
        with self.assertRaises(aunit.Error):
            aunit.install_plan(self.target, aunit.render(source), 'bad')
        self.assertFalse(self.target.codex.exists())
        self.assertFalse(self.target.skills.exists())

    def test_cli_preview_apply_and_remove_from_another_directory(self):
        script = aunit.ROOT / 'aunit.py'
        def run(*args):
            return subprocess.run([sys.executable, str(script), *args, '--project', str(self.project)],
                                  cwd=self.root, capture_output=True, text=True)
        result = run('install')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(self.target.codex.exists())
        result = run('install', '--apply')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.target.manifest.exists())
        result = run('uninstall', '--apply')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(self.target.manifest.exists())


class Packaging(unittest.TestCase):
    def test_portable_package_allows_only_public_sources(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as tmp:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            for name in ['aunit.py', 'requirements.txt', 'README.md', 'LICENSE']:
                shutil.copy(aunit.ROOT / name, source / name)
            shutil.copytree(aunit.ROOT / 'agents', source / 'agents')
            shutil.copytree(aunit.ROOT / 'templates', source / 'templates')
            (source / 'private-plan.md').write_text('private maintainer notes')
            one, two = root / 'one.zip', root / 'two.zip'
            with contextlib.redirect_stdout(io.StringIO()):
                aunit.package(one, source)
                aunit.package(two, source)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            with zipfile.ZipFile(one) as archive:
                self.assertFalse(any('private' in name or 'AGENTS.md' == name for name in archive.namelist()))
                archive.extractall(root / 'extracted')
            packaged = root / 'extracted/a-unit'
            project = root / 'target'
            project.mkdir()
            # Remove access to canonical source fixture: only extracted payload remains.
            shutil.rmtree(source)
            result = subprocess.run([sys.executable, str(packaged / 'aunit.py'), 'install', '--project', str(project), '--apply'],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            installed = (project / '.agents/skills/a-unit/SKILL.md').read_text()
            self.assertIn('## Coordination procedure', installed)
            self.assertNotIn('ai-db', installed)
            self.assertNotIn(str(aunit.ROOT), installed)
            self.assertEqual(11, len(list((project / '.codex/agents').glob('*.toml'))))


if __name__ == '__main__':
    unittest.main()
