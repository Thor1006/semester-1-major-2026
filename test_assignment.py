"""Lesson 3 checks: conflicts and failed assignments must not corrupt state."""

import unittest
from datetime import date
from assignment import make_demo_resources, assign_patient


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        # Each test gets fresh data. Fix the date so tests also work next year.
        self.rooms, self.doctors = make_demo_resources()
        self.assignments = {}
        self.today = date(2026, 9, 6)

    def record(self, ticket='Q0107', ward='General medicine', day='2026-09-06'):
        return {'queue_id': ticket, 'destination_ward': ward, 'appointment_date': day}

    def assign(self, record):
        return assign_patient(record, self.rooms, self.doctors, self.assignments, self.today)

    def test_two_pairs_then_third_waits(self):
        first = self.assign(self.record())
        second = self.assign(self.record('Q0142'))
        self.assertNotEqual(first['room_id'], second['room_id'])
        self.assertNotEqual(first['doctor_id'], second['doctor_id'])
        before = self.assignments.copy()
        with self.assertRaisesRegex(ValueError, 'No available room'):
            self.assign(self.record('Q0199'))
        self.assertEqual(self.assignments, before)

    def test_repeat_click_does_not_consume_second_pair(self):
        self.assign(self.record())
        with self.assertRaisesRegex(ValueError, 'already'):
            self.assign(self.record())
        self.assertEqual(len(self.assignments), 1)
        self.assertEqual(self.assign(self.record('Q0142'))['room_id'], 'R01-2')

    def test_no_doctor_does_not_reserve_room(self):
        for doctor in self.doctors:
            doctor['enabled'] = False
        with self.assertRaisesRegex(ValueError, 'No available doctor'):
            self.assign(self.record())
        self.assertEqual(self.assignments, {})
        self.doctors[0]['enabled'] = True
        self.assertEqual(self.assign(self.record())['room_id'], 'R01-1')

    def test_disabled_room_is_skipped(self):
        self.rooms[0]['enabled'] = False
        self.assertEqual(self.assign(self.record())['room_id'], 'R01-2')

    def test_other_wards_resources_are_not_substitutes(self):
        for room in self.rooms:
            if room['ward'] == 'General medicine':
                room['enabled'] = False
        with self.assertRaisesRegex(ValueError, 'No available room'):
            self.assign(self.record())
        self.assertEqual(self.assignments, {})

    def test_shared_doctor_cannot_work_in_two_wards_at_once(self):
        self.doctors = [{'id': 'D-shared', 'wards': ['General medicine', 'Pediatrics'], 'enabled': True}]
        self.assign(self.record())
        with self.assertRaisesRegex(ValueError, 'No available doctor'):
            self.assign(self.record('Q0207', 'Pediatrics'))
        self.assertEqual(len(self.assignments), 1)

    def test_future_and_past_dates_do_not_take_current_resources(self):
        for day in ['2026-09-05', '2026-09-07']:
            with self.subTest(day=day), self.assertRaisesRegex(ValueError, 'today'):
                self.assign(self.record(day=day))
        self.assertEqual(self.assignments, {})

    def test_factory_instances_are_independent(self):
        other_rooms, _ = make_demo_resources()
        self.rooms[0]['enabled'] = False
        self.assertTrue(other_rooms[0]['enabled'])


if __name__ == '__main__':
    unittest.main()
