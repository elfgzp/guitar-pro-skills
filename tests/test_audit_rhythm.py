import copy
import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/score-rhythm-audit/scripts/audit_rhythm.py'
SPEC = importlib.util.spec_from_file_location('audit_rhythm', SCRIPT)
rhythm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rhythm)


def sample():
    return {
        'schema': 'guitar-pro-skills/rhythm-v1',
        'measures': [{
            'number': 1, 'meter': [4, 4],
            'voices': [{'track': 'guitar', 'voice': 'upper', 'events': [
                {'onset': '0', 'duration': '2/3', 'kind': 'note'},
                {'onset': '2/3', 'duration': '1/3', 'kind': 'note'},
                {'onset': '1', 'duration': '3', 'kind': 'rest'},
            ]}],
        }],
    }


class RhythmTests(unittest.TestCase):
    def test_triplet_exact_arithmetic(self):
        self.assertTrue(rhythm.audit(sample())['structural_pass'])

    def test_overlapping_events_even_when_total_fits(self):
        data = sample()
        data['measures'][0]['voices'][0]['events'][1]['onset'] = '1/3'
        self.assertIn('overlap', {e['code'] for e in rhythm.audit(data)['errors']})

    def test_gap_requires_explicit_rest(self):
        data = sample()
        data['measures'][0]['voices'][0]['events'].pop(1)
        self.assertIn('gap', {e['code'] for e in rhythm.audit(data)['errors']})

    def test_pickup_requires_reason_and_duration(self):
        data = sample()
        bar = data['measures'][0]
        bar['expected_duration'] = '1'
        bar['duration_reason'] = 'pickup verified in source'
        bar['voices'][0]['events'].pop()
        self.assertTrue(rhythm.audit(data)['structural_pass'])
        del bar['duration_reason']
        self.assertFalse(rhythm.audit(data)['structural_pass'])

    def test_changed_meter(self):
        data = sample()
        bar = copy.deepcopy(data['measures'][0])
        bar['number'] = 2
        bar['meter'] = [3, 4]
        bar['voices'][0]['events'][-1]['duration'] = '2'
        data['measures'].append(bar)
        self.assertTrue(rhythm.audit(data)['structural_pass'])

    def test_voices_are_checked_independently(self):
        data = sample()
        voice = copy.deepcopy(data['measures'][0]['voices'][0])
        voice['voice'] = 'lower'
        voice['events'] = [{'onset': 0, 'duration': 4, 'kind': 'rest'}]
        data['measures'][0]['voices'].append(voice)
        self.assertTrue(rhythm.audit(data)['structural_pass'])

    def test_fractional_float_is_not_silently_rounded(self):
        data = sample()
        data['measures'][0]['voices'][0]['events'][0]['duration'] = 0.6667
        self.assertFalse(rhythm.audit(data)['structural_pass'])

    def test_duplicate_voice_rejected(self):
        data = sample()
        data['measures'][0]['voices'].append(copy.deepcopy(data['measures'][0]['voices'][0]))
        self.assertFalse(rhythm.audit(data)['structural_pass'])

    def test_rest_not_changed_to_note_in_comparison(self):
        actual = sample()
        actual['measures'][0]['voices'][0]['events'][-1]['kind'] = 'note'
        self.assertTrue(rhythm.audit(actual)['structural_pass'])
        self.assertFalse(rhythm.compare(actual, sample())['reference_match'])

    def test_two_valid_different_rhythms_are_not_equivalent(self):
        actual = sample()
        events = actual['measures'][0]['voices'][0]['events']
        events[0]['duration'] = '1/2'
        events[1]['onset'] = '1/2'
        events[1]['duration'] = '1/2'
        self.assertTrue(rhythm.audit(actual)['structural_pass'])
        self.assertFalse(rhythm.compare(actual, sample())['reference_match'])

    def test_empty_document_and_empty_voice_fail(self):
        self.assertFalse(rhythm.audit({'schema': 'guitar-pro-skills/rhythm-v1', 'measures': []})['structural_pass'])
        data = sample()
        data['measures'][0]['voices'][0]['events'] = []
        self.assertFalse(rhythm.audit(data)['structural_pass'])

    def test_reference_comparison_normalizes_rationals_and_order(self):
        actual = sample()
        actual['measures'][0]['voices'][0]['events'][0]['onset'] = '0/3'
        actual['measures'][0]['voices'][0]['events'].reverse()
        self.assertTrue(rhythm.compare(actual, sample())['reference_match'])

    def test_invalid_reference_cannot_pass(self):
        invalid = sample()
        invalid['measures'][0]['voices'][0]['events'] = []
        self.assertFalse(rhythm.compare(invalid, invalid)['reference_match'])


if __name__ == '__main__':
    unittest.main()
