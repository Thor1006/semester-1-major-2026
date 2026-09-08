"""Checks for manual assignment and automatic arrival-order assignment.

    python -m unittest -v test_assignment_modes.py
"""

import unittest
from datetime import date

from assignment import (assign_patient, assign_patient_to, auto_assign,
                        available_resources, make_demo_resources)

TODAY = date(2026, 9, 8)


def case(queue_id, ward='General medicine', day=None):
    return {'queue_id': queue_id, 'destination_ward': ward,
            'appointment_date': (day or TODAY.isoformat())}


class ManualAssignmentTests(unittest.TestCase):

    def setUp(self):
        self.rooms, self.doctors = make_demo_resources()
        self.assignments = {}

    def assign_to(self, queue_id, room_id, doctor_id, **kwargs):
        return assign_patient_to(case(queue_id, **kwargs), self.rooms, self.doctors,
                                 self.assignments, room_id, doctor_id, TODAY)

    def test_a_staff_member_can_choose_the_second_pair(self):
        """The point of manual mode: override first-fit, not the rules."""
        result = self.assign_to('Q0101', 'R01-2', 'D01-2')
        self.assertEqual(result, {'room_id': 'R01-2', 'doctor_id': 'D01-2'})
        self.assertEqual(self.assignments['Q0101'], result)

    def test_pairs_can_be_mixed(self):
        """Room 1 with doctor 2 is a legal combination first-fit would not pick."""
        self.assertEqual(self.assign_to('Q0101', 'R01-1', 'D01-2')['doctor_id'], 'D01-2')

    def test_an_unknown_resource_is_named(self):
        with self.assertRaisesRegex(ValueError, 'R01-9 is not a room'):
            self.assign_to('Q0101', 'R01-9', 'D01-1')
        with self.assertRaisesRegex(ValueError, 'D01-9 is not a doctor'):
            self.assign_to('Q0101', 'R01-1', 'D01-9')

    def test_a_resource_from_another_ward_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'R02-1 does not serve General medicine'):
            self.assign_to('Q0101', 'R02-1', 'D01-1')

    def test_an_out_of_service_resource_is_refused(self):
        self.rooms[0]['enabled'] = False
        with self.assertRaisesRegex(ValueError, 'R01-1 is out of service'):
            self.assign_to('Q0101', 'R01-1', 'D01-1')

    def test_an_already_reserved_resource_names_who_holds_it(self):
        self.assign_to('Q0101', 'R01-1', 'D01-1')
        with self.assertRaisesRegex(ValueError, 'R01-1 is already reserved by Q0101'):
            self.assign_to('Q0102', 'R01-1', 'D01-2')

    def test_a_case_already_assigned_is_refused(self):
        self.assign_to('Q0101', 'R01-1', 'D01-1')
        with self.assertRaisesRegex(ValueError, 'already has an assignment'):
            self.assign_to('Q0101', 'R01-2', 'D01-2')

    def test_another_date_cannot_take_todays_resources(self):
        with self.assertRaisesRegex(ValueError, 'dated today'):
            self.assign_to('Q0101', 'R01-1', 'D01-1', day='2026-09-20')

    def test_a_bad_doctor_leaves_the_room_free(self):
        """Check everything before mutating: a rejected pair reserves nothing."""
        with self.assertRaises(ValueError):
            self.assign_to('Q0101', 'R01-1', 'D02-1')
        self.assertEqual(self.assignments, {})
        free_rooms, _ = available_resources('General medicine', self.rooms,
                                            self.doctors, self.assignments)
        self.assertIn('R01-1', [room['id'] for room in free_rooms])

    def test_available_resources_matches_what_manual_mode_accepts(self):
        """The chooser must never offer something the rules would refuse."""
        self.assign_to('Q0101', 'R01-1', 'D01-1')
        free_rooms, free_doctors = available_resources(
            'General medicine', self.rooms, self.doctors, self.assignments)
        self.assertEqual([room['id'] for room in free_rooms], ['R01-2'])
        self.assertEqual([doctor['id'] for doctor in free_doctors], ['D01-2'])
        # Everything offered is genuinely assignable.
        self.assign_to('Q0102', free_rooms[0]['id'], free_doctors[0]['id'])


class AutoAssignTests(unittest.TestCase):

    def setUp(self):
        self.rooms, self.doctors = make_demo_resources()
        self.assignments = {}

    def test_cases_are_served_in_arrival_order(self):
        """First come, first served: list order, not ticket order."""
        # Ticket values deliberately descend, so an implementation that sorted
        # by ticket would produce a different answer and fail this test.
        records = [case('Q0199'), case('Q0150'), case('Q0102')]
        result = auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)

        self.assertEqual([queue_id for queue_id, _ in result['assigned']],
                         ['Q0199', 'Q0150'])
        self.assertEqual(result['assigned'][0][1]['room_id'], 'R01-1')
        self.assertEqual(result['assigned'][1][1]['room_id'], 'R01-2')
        self.assertEqual([queue_id for queue_id, _ in result['waiting']], ['Q0102'])

    def test_a_waiting_case_reports_why(self):
        records = [case('Q0101'), case('Q0102'), case('Q0103')]
        result = auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        self.assertIn('No available room', result['waiting'][0][1])

    def test_a_full_ward_does_not_block_a_different_ward(self):
        """One exhausted ward must not stop the rest of the list being served."""
        records = [case('Q0101'), case('Q0102'), case('Q0103'),
                   case('Q0201', ward='Pediatrics')]
        result = auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        assigned = [queue_id for queue_id, _ in result['assigned']]
        self.assertIn('Q0201', assigned)
        self.assertEqual([queue_id for queue_id, _ in result['waiting']], ['Q0103'])

    def test_already_assigned_cases_are_left_alone(self):
        records = [case('Q0101'), case('Q0102')]
        assign_patient(records[0], self.rooms, self.doctors, self.assignments, TODAY)
        before = dict(self.assignments['Q0101'])

        result = auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        self.assertEqual([queue_id for queue_id, _ in result['assigned']], ['Q0102'])
        self.assertEqual(self.assignments['Q0101'], before)

    def test_a_manual_choice_is_respected_by_a_later_auto_run(self):
        """Auto-assign fills the gaps; it never reshuffles existing work."""
        records = [case('Q0101'), case('Q0102')]
        assign_patient_to(records[0], self.rooms, self.doctors, self.assignments,
                          'R01-2', 'D01-2', TODAY)
        auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        self.assertEqual(self.assignments['Q0101'],
                         {'room_id': 'R01-2', 'doctor_id': 'D01-2'})
        self.assertEqual(self.assignments['Q0102'],
                         {'room_id': 'R01-1', 'doctor_id': 'D01-1'})

    def test_other_dates_are_not_touched_and_not_reported_as_waiting(self):
        """A future appointment is not part of today's queue at all."""
        records = [case('Q0101'), case('Q0102', day='2026-09-20')]
        result = auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        self.assertEqual([queue_id for queue_id, _ in result['assigned']], ['Q0101'])
        self.assertEqual(result['waiting'], [])
        self.assertNotIn('Q0102', self.assignments)

    def test_running_twice_changes_nothing_the_second_time(self):
        records = [case('Q0101'), case('Q0102'), case('Q0103')]
        auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        snapshot = dict(self.assignments)
        again = auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        self.assertEqual(self.assignments, snapshot)
        self.assertEqual(again['assigned'], [])

    def test_an_empty_queue_is_not_an_error(self):
        result = auto_assign([], self.rooms, self.doctors, self.assignments, TODAY)
        self.assertEqual(result, {'assigned': [], 'waiting': []})

    def test_extra_capacity_lets_auto_assign_serve_everyone(self):
        records = [case(f'Q010{n}') for n in range(1, 4)]
        rooms, doctors = make_demo_resources({'General medicine': (3, 3)})
        result = auto_assign(records, rooms, doctors, {}, TODAY)
        self.assertEqual(len(result['assigned']), 3)
        self.assertEqual(result['waiting'], [])


if __name__ == '__main__':
    unittest.main()
