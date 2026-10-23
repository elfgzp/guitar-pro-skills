import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/check_repository.py'
SPEC = importlib.util.spec_from_file_location('check_repository', SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        old = checker.ROOT
        self.addCleanup(setattr, checker, 'ROOT', old)
        checker.ROOT = self.root
        for index in range(6):
            folder = self.root / 'skills' / f'skill-{index}'
            folder.mkdir(parents=True)
            (folder / 'SKILL.md').write_text(
                f'---\nname: skill-{index}\ndescription: Use when reviewing example {index}.\n---\n# Skill\n'
            )

    def check(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = checker.main()
        return result, output.getvalue()

    def test_valid_independent_resources(self):
        skill = self.root / 'skills/skill-0'
        (skill / 'reference.md').write_text('An original reference.\n')
        with (skill / 'SKILL.md').open('a') as stream:
            stream.write('[Details](reference.md)\n')
        self.assertEqual(self.check()[0], 0)

    def test_yaml_description_must_be_text(self):
        skill = self.root / 'skills/skill-0/SKILL.md'
        skill.write_text(skill.read_text().replace('Use when reviewing example 0.', '[]'))
        self.assertEqual(self.check()[0], 1)

    def test_missing_and_outside_skill_resources(self):
        skill = self.root / 'skills/skill-0/SKILL.md'
        with skill.open('a') as stream:
            stream.write('[Missing](missing.md)\n[Other](../skill-1/SKILL.md)\n')
        result, output = self.check()
        self.assertEqual(result, 1)
        self.assertIn('missing/outside', output)
        self.assertIn('leaves independently installable skill', output)

    def test_publication_rejects_symlink(self):
        (self.root / 'link.md').symlink_to(self.root / 'skills/skill-0/SKILL.md')
        result, output = self.check()
        self.assertEqual(result, 1)
        self.assertIn('symlink', output)

    def test_bad_encoding_has_located_error(self):
        (self.root / 'broken.md').write_bytes(b'\xff\xfe\x00')
        result, output = self.check()
        self.assertEqual(result, 1)
        self.assertIn('broken.md: cannot read UTF-8', output)


if __name__ == '__main__':
    unittest.main()
