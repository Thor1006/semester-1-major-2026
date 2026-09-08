"""Checks for configurable capacity: how many rooms and doctors a ward has.

    python -m unittest -v test_capacity.py
"""

import os
import tempfile
import unittest
from datetime import date

import storage
from assignment import (DEFAULT_CAPACITY, assign_patient, blocking_reservations,
                        make_demo_resources)


def case(queue_id, ward='General medicine', day='2026-09-08'):
    return {'queue_id': queue_id, 'destination_ward': ward, 'appointment_date': day}


class ResourceFactoryTests(unittest.TestCase):

    def test_no_capacity_given_keeps_the_original_two_and_two(self):
        """Old callers and tests must be unaffected."""
        rooms, doctors = make_demo_resources()
        general = [r for r in rooms if r['ward'] == 'General medicine']
        self.assertEqual([r['id'] for r in general], ['R01-1', 'R01-2'])
        self.assertEqual(DEFAULT_CAPACITY, (2, 2))
        self.assertEqual(len([d for d in doctors if 'General medicine' in d['wards']]), 2)

    def test_capacity_changes_only_the_named_ward(self):
        rooms, doctors = make_demo_resources({'General medicine': (4, 1)})
        self.assertEqual([r['id'] for r in rooms if r['ward'] == 'General medicine'],
                         ['R01-1', 'R01-2', 'R01-3', 'R01-4'])
        self.assertEqual([d['id'] for d in doctors if d['wards'] == ['General medicine']],
                         ['D01-1'])
        # Pediatrics was not mentioned, so it keeps the default.
        self.assertEqual(len([r for r in rooms if r['ward'] == 'Pediatrics']), 2)

    def test_growing_a_ward_keeps_existing_identifiers(self):
        """An existing reservation must still point at a real room."""
        before = [r['id'] for r in make_demo_resources()[0] if r['ward'] == 'General medicine']
        after = [r['id'] for r in make_demo_resources({'General medicine': (5, 5)})[0]
                 if r['ward'] == 'General medicine']
        self.assertEqual(after[:len(before)], before)

    def test_zero_capacity_produces_no_resources(self):
        rooms, doctors = make_demo_resources({'General medicine': (0, 0)})
        self.assertEqual([r for r in rooms if r['ward'] == 'General medicine'], [])
        self.assertEqual([d for d in doctors if d['wards'] == ['General medicine']], [])

    def test_a_disabled_resource_is_built_disabled(self):
        rooms, _ = make_demo_resources(disabled={'R01-2'})
        by_id = {room['id']: room for room in rooms}
        self.assertFalse(by_id['R01-2']['enabled'])
        self.assertTrue(by_id['R01-1']['enabled'])

    def test_a_disabled_room_is_not_assigned(self):
        rooms, doctors = make_demo_resources({'General medicine': (1, 1)},
                                             disabled={'R01-1'})
        with self.assertRaisesRegex(ValueError, 'No available room'):
            assign_patient(case('Q0101'), rooms, doctors, {}, date(2026, 9, 8))

    def test_extra_capacity_lets_a_third_case_be_served(self):
        """The point of the whole feature."""
        rooms, doctors = make_demo_resources({'General medicine': (3, 3)})
        assignments = {}
        for number in range(1, 4):
            assign_patient(case(f'Q010{number}'), rooms, doctors, assignments,
                           date(2026, 9, 8))
        self.assertEqual(len(assignments), 3)


class CapacityChangeSafetyTests(unittest.TestCase):

    def setUp(self):
        self.capacity = {'General medicine': (2, 2)}
        self.rooms, self.doctors = make_demo_resources(self.capacity)
        self.assignments = {}
        assign_patient(case('Q0101'), self.rooms, self.doctors, self.assignments,
                       date(2026, 9, 8))   # takes R01-1 and D01-1

    def test_growing_is_always_safe(self):
        self.assertEqual(blocking_reservations('General medicine', 5, 5,
                                               self.capacity, self.assignments), [])

    def test_shrinking_past_a_free_resource_is_safe(self):
        """R01-2 and D01-2 are unused, so dropping to one of each is fine."""
        self.assertEqual(blocking_reservations('General medicine', 1, 1,
                                               self.capacity, self.assignments), [])

    def test_shrinking_onto_a_reserved_resource_is_blocked(self):
        blocked = blocking_reservations('General medicine', 0, 0,
                                        self.capacity, self.assignments)
        self.assertIn('R01-1', blocked)
        self.assertIn('D01-1', blocked)

    def test_only_the_removed_end_of_the_range_is_considered(self):
        """Reducing removes the highest numbers, never renumbers the rest."""
        assign_patient(case('Q0102'), self.rooms, self.doctors, self.assignments,
                       date(2026, 9, 8))   # now R01-2 and D01-2 are taken too
        self.assertEqual(blocking_reservations('General medicine', 2, 2,
                                               self.capacity, self.assignments), [])
        self.assertEqual(sorted(blocking_reservations('General medicine', 1, 1,
                                                      self.capacity, self.assignments)),
                         ['D01-2', 'R01-2'])

    def test_another_ward_is_unaffected(self):
        self.assertEqual(blocking_reservations('Pediatrics', 0, 0,
                                               self.capacity, self.assignments), [])


class CapacityStorageTests(unittest.TestCase):

    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix='.db')
        os.close(handle)
        os.unlink(self.path)
        self.connection = storage.connect(self.path)

    def tearDown(self):
        self.connection.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_a_new_database_has_no_configured_capacity(self):
        """Absent from the table means 'use the default', not 'zero'."""
        self.assertEqual(storage.load_capacity(self.connection), {})

    def test_capacity_round_trips(self):
        storage.save_capacity(self.connection, 'General medicine', 5, 3)
        self.assertEqual(storage.load_capacity(self.connection),
                         {'General medicine': (5, 3)})

    def test_saving_the_same_ward_twice_replaces_it(self):
        storage.save_capacity(self.connection, 'General medicine', 5, 3)
        storage.save_capacity(self.connection, 'General medicine', 1, 1)
        self.assertEqual(storage.load_capacity(self.connection),
                         {'General medicine': (1, 1)})

    def test_negative_capacity_is_refused(self):
        with self.assertRaises(ValueError):
            storage.save_capacity(self.connection, 'General medicine', -1, 2)

    def test_capacity_survives_reopening(self):
        storage.save_capacity(self.connection, 'Pediatrics', 4, 6)
        self.connection.close()
        reopened = storage.connect(self.path)
        try:
            self.assertEqual(storage.load_capacity(reopened), {'Pediatrics': (4, 6)})
        finally:
            reopened.close()
            self.connection = storage.connect(self.path)

    def test_disabling_and_re_enabling_a_resource(self):
        self.assertEqual(storage.load_disabled_resources(self.connection), set())
        storage.set_resource_enabled(self.connection, 'R01-2', False)
        self.assertEqual(storage.load_disabled_resources(self.connection), {'R01-2'})
        storage.set_resource_enabled(self.connection, 'R01-2', True)
        self.assertEqual(storage.load_disabled_resources(self.connection), set())

    def test_disabling_twice_is_harmless(self):
        storage.set_resource_enabled(self.connection, 'R01-2', False)
        storage.set_resource_enabled(self.connection, 'R01-2', False)
        self.assertEqual(storage.load_disabled_resources(self.connection), {'R01-2'})

    def test_a_disabled_id_is_not_reused_by_a_new_resource(self):
        """Disabling is kept apart from capacity for exactly this reason."""
        storage.set_resource_enabled(self.connection, 'R01-3', False)
        rooms, _ = make_demo_resources(
            {'General medicine': (3, 2)},
            disabled=storage.load_disabled_resources(self.connection))
        third = next(room for room in rooms if room['id'] == 'R01-3')
        self.assertFalse(third['enabled'])


if __name__ == '__main__':
    unittest.main()
