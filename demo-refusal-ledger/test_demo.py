"""Checks for the claims the demonstration makes on screen.

    python -m unittest -v test_demo.py
"""

import unittest

from clinic import (CAPACITY_CODES, capacity_refusals, make_resources,
                    run_from_spec, served_refs, try_assign)
from replay import counterfactual, replay_is_exact
from scenario import SPEC, build_cases
from datetime import date


class LedgerTests(unittest.TestCase):

    def setUp(self):
        self.cases = build_cases()
        self.ledger = run_from_spec(self.cases, SPEC)

    def test_workflow_refusals_are_excluded_from_capacity(self):
        """A duplicate click must never be counted as unmet demand."""
        codes = {r['code'] for r in capacity_refusals(self.ledger)}
        self.assertTrue(codes.issubset(set(CAPACITY_CODES)))
        all_codes = {r['code'] for r in self.ledger['refusals']}
        self.assertIn('duplicate', all_codes)
        self.assertIn('not_today', all_codes)
        self.assertEqual(len(self.ledger['refusals']) - len(capacity_refusals(self.ledger)), 2)

    def test_doctor_bound_refusal_records_idle_rooms(self):
        """The contrast is the actionable fact, so it must be recorded."""
        doctor_bound = [r for r in capacity_refusals(self.ledger)
                        if r['code'] == 'no_doctor']
        self.assertTrue(doctor_bound)
        for refusal in doctor_bound:
            self.assertEqual(refusal['doctors_free'], 0)
            self.assertGreater(refusal['rooms_free'], 0,
                               'a doctor-bound refusal should show idle rooms')

    def test_room_bound_refusal_records_idle_doctors(self):
        room_bound = [r for r in capacity_refusals(self.ledger)
                      if r['code'] == 'no_room']
        self.assertTrue(room_bound)
        for refusal in room_bound:
            self.assertEqual(refusal['rooms_free'], 0)
            self.assertGreater(refusal['doctors_free'], 0)

    def test_a_duplicate_does_not_consume_a_resource(self):
        rooms, doctors = make_resources({'General medicine': (2, 2)})
        assignments = {}
        case = {'case_ref': 'X-1', 'ward': 'General medicine',
                'day': '2026-09-01', 'appointment_date': '2026-09-01'}
        today = date(2026, 9, 1)

        first = try_assign(case, rooms, doctors, assignments, today)
        second = try_assign(case, rooms, doctors, assignments, today)

        self.assertEqual(first['outcome'], 'assigned')
        self.assertEqual(second['code'], 'duplicate')
        self.assertEqual(len(assignments), 1, 'the retry must not reserve a second pair')


class ReplayTests(unittest.TestCase):

    def setUp(self):
        self.cases = build_cases()

    def test_replay_with_unchanged_resources_is_exact(self):
        """Everything downstream depends on this being true."""
        self.assertTrue(replay_is_exact(self.cases, SPEC))

    def test_adding_a_resource_never_costs_a_case_its_reservation(self):
        """Monotonicity. Checked rather than assumed."""
        for ward in SPEC:
            for kwargs in ({'extra_doctors': 1}, {'extra_rooms': 1},
                           {'extra_rooms': 1, 'extra_doctors': 1},
                           {'extra_doctors': 3}):
                result = counterfactual(self.cases, SPEC, ward, **kwargs)
                self.assertEqual(result['lost'], [],
                                 f'{ward} {kwargs} lost a reservation')

    def test_extra_room_absorbs_nothing_where_doctors_bind(self):
        """The headline finding of the demonstration."""
        result = counterfactual(self.cases, SPEC, 'General medicine', extra_rooms=1)
        self.assertEqual(result['absorbed'], [])

    def test_extra_doctor_absorbs_one_case_per_day(self):
        """Five clinic days, so one added doctor absorbs five cases."""
        result = counterfactual(self.cases, SPEC, 'General medicine', extra_doctors=1)
        self.assertEqual(len(result['absorbed']), 5)

    def test_pediatrics_is_the_mirror_image(self):
        room = counterfactual(self.cases, SPEC, 'Pediatrics', extra_rooms=1)
        doctor = counterfactual(self.cases, SPEC, 'Pediatrics', extra_doctors=1)
        self.assertEqual(len(room['absorbed']), 5)
        self.assertEqual(doctor['absorbed'], [])

    def test_absorbed_cases_were_previously_refused(self):
        """An absorbed case must be one the original run actually turned away."""
        base = run_from_spec(self.cases, SPEC)
        refused = {r['case_ref'] for r in capacity_refusals(base)}
        result = counterfactual(self.cases, SPEC, 'General medicine', extra_doctors=1)
        for ref in result['absorbed']:
            self.assertIn(ref, refused)


if __name__ == '__main__':
    unittest.main()
