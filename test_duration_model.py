"""Check learned choices, eligibility, fallbacks, and held-out evaluation."""
import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from assignment import assign_patient, make_demo_resources
from duration_model import DATA_PATH, features, load_duration_model, train_duration_model, estimate_duration


class DurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_duration_model()

    def assign(self, model=None, rooms=None, doctors=None, assignments=None, ticket='Q0101'):
        default_rooms, default_doctors = make_demo_resources()
        record = {'queue_id': ticket, 'destination_ward': 'General medicine',
                  'appointment_date': '2026-09-06'}
        return assign_patient(record, default_rooms if rooms is None else rooms,
                              default_doctors if doctors is None else doctors,
                              {} if assignments is None else assignments,
                              date(2026, 9, 6), model=model)

    def test_model_selects_shortest_not_first_and_prevents_conflicts(self):
        reservations = {}
        first = self.assign(self.model, assignments=reservations)
        self.assertEqual((first['room_id'], first['doctor_id']), ('R01-2', 'D01-2'))
        self.assertEqual(len(first['candidates']), 4)
        second = self.assign(self.model, assignments=reservations, ticket='Q0102')
        self.assertEqual((second['room_id'], second['doctor_id']), ('R01-1', 'D01-1'))
        with self.assertRaises(ValueError):
            self.assign(self.model, assignments=reservations, ticket='Q0103')
        self.assertEqual(len(reservations), 2)

    def test_disabled_and_incompatible_resources_never_scored(self):
        rooms, doctors = make_demo_resources()
        doctors[1]['enabled'] = False
        result = self.assign(self.model, rooms, doctors)
        self.assertEqual(result['doctor_id'], 'D01-1')
        self.assertEqual(len(result['candidates']), 2)
        self.assertTrue(all(item['room_id'].startswith('R01-') for item in result['candidates']))

    def test_training_data_changes_the_choice(self):
        # Same algorithm and resources, opposite observations: proves selection
        # depends on learned data, not a hard-coded preference for resource #2.
        rows = []
        for room in (1, 2):
            for doctor in (1, 2):
                rows.extend([{'ward': 'General medicine', 'room_id': f'R01-{room}',
                              'doctor_id': f'D01-{doctor}',
                              'duration_minutes': 10 if (room, doctor) == (1, 1) else 40}] * 10)
        result = self.assign(train_duration_model(rows))
        self.assertEqual((result['room_id'], result['doctor_id']), ('R01-1', 'D01-1'))

    def test_inputs_exclude_outcome_and_patient_details(self):
        row = dict(ward='A', room_id='R', doctor_id='D', duration_minutes=99,
                   name='Fictional person', phone='1234567', information='Private note')
        self.assertEqual(features(row), {'ward': 'A', 'room_id': 'R', 'doctor_id': 'D'})

    def test_fallbacks_are_explicit(self):
        minutes, method = estimate_duration(self.model, 'General medicine', 'NEW', 'D01-1')
        self.assertEqual(minutes, self.model['ward_medians']['General medicine'])
        self.assertIn('fallback', method)
        result = self.assign()
        self.assertIsNone(result['estimated_minutes'])
        self.assertIn('Fallback', result['method'])

    def test_invalid_prediction_does_not_reserve_anything(self):
        state = {}
        with patch('assignment.estimate_duration', return_value=(float('nan'), 'broken')):
            with self.assertRaises(ValueError):
                self.assign(self.model, assignments=state)
        self.assertEqual(state, {})

    def test_evaluation_rows_do_not_train_model(self):
        with DATA_PATH.open(newline='', encoding='utf-8') as source:
            reader = csv.DictReader(source)
            fields, rows = reader.fieldnames, list(reader)
        # Deliberately corrupt only the later outcomes. Predictions must stay
        # identical while measured test error increases substantially.
        for row in rows:
            if row['date'] >= self.model['report']['first_test_date']:
                row['duration_minutes'] = '999'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'history.csv'
            with path.open('w', newline='', encoding='utf-8') as target:
                writer = csv.DictWriter(target, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            changed = load_duration_model(path)
        args = ('General medicine', 'R01-2', 'D01-2')
        self.assertEqual(estimate_duration(self.model, *args), estimate_duration(changed, *args))
        self.assertGreater(changed['report']['tree_mae_minutes'], 900)
        self.assertEqual(self.model['report']['training_rows'], 320)
        self.assertEqual(self.model['report']['test_rows'], 80)


if __name__ == '__main__':
    unittest.main()
