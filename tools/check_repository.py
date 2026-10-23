#!/usr/bin/env python3
"""Validate the published skill tree without a model-specific runtime."""

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'output', 'outputs', 'work', 'input'}
PRIVATE_PATH = re.compile(r'(?:/(?:Users|home|Volumes)/[^\s\x22\x27<>]+|[A-Za-z]:\\Users\\[^\s]+)')
TOKEN = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')
LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)]+)\)')


def source_files():
    for path in ROOT.rglob('*'):
        if any(part in IGNORED for part in path.relative_to(ROOT).parts):
            continue
        if path.is_symlink() or path.is_file():
            yield path


def main():
    try:
        import yaml
    except ImportError:
        print('Install requirements-dev.txt to validate YAML metadata.', file=sys.stderr)
        return 2
    errors = []
    skills = sorted((ROOT / 'skills').glob('*/SKILL.md'))
    if len(skills) != 6:
        errors.append(f'Expected 6 focused skills, found {len(skills)}')
    for skill in skills:
        if skill.is_symlink() or not skill.resolve().is_relative_to(ROOT):
            errors.append(f'{skill.relative_to(ROOT)}: skill must be a repository resource file')
            continue
        try:
            text = skill.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as exc:
            errors.append(f'{skill.relative_to(ROOT)}: cannot read UTF-8 source ({type(exc).__name__})')
            continue
        if not text.startswith('---\n') or '\n---\n' not in text[4:]:
            errors.append(f'{skill.relative_to(ROOT)}: missing YAML frontmatter')
            continue
        try:
            metadata = yaml.safe_load(text.split('---\n', 2)[1])
        except yaml.YAMLError:
            errors.append(f'{skill.relative_to(ROOT)}: invalid YAML metadata')
            continue
        if not isinstance(metadata, dict):
            errors.append(f'{skill.relative_to(ROOT)}: metadata must be a mapping')
            continue
        name, description = metadata.get('name'), metadata.get('description')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name != skill.parent.name or len(name) > 64:
            errors.append(f'{skill.relative_to(ROOT)}: invalid or mismatching name')
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            errors.append(f'{skill.relative_to(ROOT)}: missing/oversized description')
        if len(text.splitlines()) > 120:
            errors.append(f'{skill.relative_to(ROOT)}: move optional details to references (over 120 lines)')
    for path in source_files():
        if path.is_symlink():
            errors.append(f'{path.relative_to(ROOT)}: publish resource files, not machine-specific symlinks')
            continue
        if path.suffix not in {'.md', '.py', '.cjs', '.json', '.yml', '.yaml', '.html', '.txt'}:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as exc:
            errors.append(f'{path.relative_to(ROOT)}: cannot read UTF-8 source ({type(exc).__name__})')
            continue
        if PRIVATE_PATH.search(text):
            errors.append(f'{path.relative_to(ROOT)}: private absolute path pattern')
        if TOKEN.search(text):
            errors.append(f'{path.relative_to(ROOT)}: possible credential')
        if path.suffix != '.md':
            continue
        for target in LINK.findall(text):
            target = target.split('#', 1)[0].strip('<>')
            if not target or re.match(r'^[a-z]+:', target):
                continue
            resolved = (path.parent / unquote(target)).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(f'{path.relative_to(ROOT)}: missing/outside link {target}')
            if 'skills' in path.relative_to(ROOT).parts:
                skill_root = ROOT / 'skills' / path.relative_to(ROOT).parts[1]
                if not resolved.is_relative_to(skill_root):
                    errors.append(f'{path.relative_to(ROOT)}: resource link leaves independently installable skill: {target}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {len(skills)} skills, local links and publication hygiene')
    return 0


if __name__ == '__main__':
    sys.exit(main())
