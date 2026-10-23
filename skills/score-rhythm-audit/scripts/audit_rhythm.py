#!/usr/bin/env python3
"""Check explicitly transcribed voice intervals in exact quarter-note units.

This is a structural checker, not optical music recognition. It never changes
durations or uses horizontal engraving distance to manufacture timing.
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

SCHEMA = 'guitar-pro-skills/rhythm-v1'


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError('use an integer or a rational string, not a floating-point number')
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f'invalid rational: {value!r}') from exc


def issue(errors, code, location, message):
    errors.append({'code': code, 'location': location, 'message': message})


def audit_voice(voice, expected, location, errors):
    if not isinstance(voice, dict):
        issue(errors, 'voice', location, 'voice must be an object')
        return []
    events = voice.get('events')
    if not isinstance(events, list) or not events:
        issue(errors, 'empty_voice', location, 'include explicit rests; omit genuinely unused voices')
        return []
    intervals = []
    for index, event in enumerate(events):
        event_location = f'{location}/event[{index}]'
        if not isinstance(event, dict):
            issue(errors, 'event', event_location, 'event must be an object')
            continue
        try:
            onset, duration = rational(event.get('onset')), rational(event.get('duration'))
        except ValueError as exc:
            issue(errors, 'rational', event_location, str(exc))
            continue
        kind = event.get('kind')
        if kind not in ('note', 'rest'):
            issue(errors, 'kind', event_location, 'kind must be note or rest')
            continue
        if onset < 0 or duration <= 0:
            issue(errors, 'range', event_location, 'onset must be nonnegative and duration positive')
            continue
        intervals.append((onset, duration, kind))
    cursor = Fraction(0)
    for onset, duration, _ in sorted(intervals):
        if onset < cursor:
            issue(errors, 'overlap', location, f'event starts at {onset}, before prior end {cursor}; chords are one event')
        if onset > cursor:
            issue(errors, 'gap', location, f'missing explicit rest between {cursor} and {onset}')
        cursor = max(cursor, onset + duration)
    if cursor != expected:
        issue(errors, 'duration', location, f'voice ends at {cursor}; expected {expected}')
    return intervals


def audit(data):
    errors = []
    normalized = []
    if not isinstance(data, dict) or data.get('schema') != SCHEMA:
        issue(errors, 'schema', '/', f'expected schema {SCHEMA}')
        return report(errors, normalized)
    measures = data.get('measures')
    if not isinstance(measures, list) or not measures:
        issue(errors, 'measures', '/', 'measures must be a nonempty array')
        return report(errors, normalized)
    seen_bars = set()
    for index, measure in enumerate(measures):
        location = f'measures[{index}]'
        if not isinstance(measure, dict):
            issue(errors, 'measure', location, 'measure must be an object')
            continue
        number = measure.get('number')
        if not isinstance(number, int) or isinstance(number, bool) or number < 0 or number in seen_bars:
            issue(errors, 'number', location, 'number must be a unique nonnegative integer; zero may identify a pickup')
            continue
        seen_bars.add(number)
        location = f'measure[{number}]'
        meter = measure.get('meter')
        if not isinstance(meter, list) or len(meter) != 2 or any(type(v) is not int or v <= 0 for v in meter):
            issue(errors, 'meter', location, 'meter must contain two positive integers')
            continue
        expected = Fraction(meter[0] * 4, meter[1])
        if 'expected_duration' in measure:
            reason = measure.get('duration_reason')
            if not isinstance(reason, str) or not reason.strip():
                issue(errors, 'duration_reason', location, 'a source-supported duration_reason is required for an override')
            try:
                expected = rational(measure['expected_duration'])
                if expected <= 0:
                    raise ValueError('expected_duration must be positive')
            except ValueError as exc:
                issue(errors, 'duration', location, str(exc))
                continue
        voices = measure.get('voices')
        if not isinstance(voices, list) or not voices:
            issue(errors, 'voices', location, 'include at least one voice')
            continue
        seen_voices = set()
        for voice in voices:
            if not isinstance(voice, dict):
                issue(errors, 'voice', location, 'voice must be an object')
                continue
            track, voice_id = voice.get('track'), voice.get('voice')
            if not isinstance(track, str) or not track.strip() or not isinstance(voice_id, str) or not voice_id.strip():
                issue(errors, 'voice_id', location, 'track and voice must be nonempty strings')
                continue
            key = (track, voice_id)
            voice_location = f'{location}/{track}/{voice_id}'
            if key in seen_voices:
                issue(errors, 'duplicate_voice', voice_location, 'duplicate track and voice')
            seen_voices.add(key)
            intervals = audit_voice(voice, expected, voice_location, errors)
            normalized.append({
                'measure': number, 'meter': meter, 'duration': str(expected),
                'track': track, 'voice': voice_id,
                'events': [{'onset': str(t), 'duration': str(d), 'kind': k} for t, d, k in sorted(intervals)],
            })
    return report(errors, normalized)


def report(errors, normalized):
    return {
        'structural_pass': not errors,
        'source_verified': False,
        'scope': 'explicitly supplied voices and measures; no pitch, glyph, source, audio or missing-track verification',
        'errors': errors,
        'voices_checked': len(normalized),
        'normalized': sorted(normalized, key=lambda v: (v['measure'], v['track'], v['voice'])),
    }


def compare(actual, reference):
    actual_report, reference_report = audit(actual), audit(reference)
    good = actual_report['structural_pass'] and reference_report['structural_pass']
    actual_rows = {(v['measure'], v['track'], v['voice']): v for v in actual_report['normalized']}
    reference_rows = {(v['measure'], v['track'], v['voice']): v for v in reference_report['normalized']}
    differences = []
    for key in sorted(actual_rows.keys() | reference_rows.keys()):
        if actual_rows.get(key) != reference_rows.get(key):
            differences.append({'measure': key[0], 'track': key[1], 'voice': key[2],
                                'actual': actual_rows.get(key), 'reference': reference_rows.get(key)})
    return {'reference_match': good and not differences, 'differences': differences,
            'reference_errors': reference_report['errors'],
            'reference_caveat': 'Matching a JSON reference does not prove that the reference matches the source PDF.'}


def load(path):
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def write_report(result, path, sources):
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if path is None:
        print(rendered, end='')
        return
    if any(path.resolve() == source.resolve() or (path.exists() and os.path.samefile(path, source)) for source in sources):
        raise ValueError('report output must not overwrite an input')
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False)
    temp = Path(handle.name)
    try:
        with handle:
            handle.write(rendered)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--reference', type=Path, help='independently source-reviewed timing JSON')
    parser.add_argument('--output', type=Path, help='JSON report (default: stdout)')
    args = parser.parse_args()
    try:
        data, digest = load(args.input)
        result = audit(data)
        result['input_sha256'] = digest
        sources = [args.input]
        if args.reference:
            reference, digest = load(args.reference)
            result.update(compare(data, reference))
            result['reference_sha256'] = digest
            sources.append(args.reference)
        write_report(result, args.output, sources)
        return 0 if result['structural_pass'] and result.get('reference_match', True) else 1
    except (OSError, ValueError) as exc:
        print(f'audit_rhythm: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
