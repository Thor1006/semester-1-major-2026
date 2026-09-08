"""Checks for marking a case done, and for the database migration it needed.

    python -m unittest -v test_lifecycle.py
"""

import os
import sqlite3
import tempfile
import unittest
from datetime import date

import storage
from assignment import (assign_patient, auto_assign, available_resources,
                        make_demo_resources, release_reservation)
from registration import create_patient_record

TODAY = date(2026, 9, 8)


def case(queue_id, ward='General medicine', day=None, status='waiting'):
    return {'queue_id': queue_id, 'destination_ward': ward,
            'appointment_date': (day or TODAY.isoformat()), 'status': status}


class ReleaseTests(unittest.TestCase):

    def setUp(self):
        self.rooms, self.doctors = make_demo_resources()
        self.assignments = {}

    def test_releasing_frees_the_room_for_the_next_patient(self):
        """The whole point: a finished visit gives its room back."""
        first, second, third = case('Q0101'), case('Q0102'), case('Q0103')
        assign_patient(first, self.rooms, self.doctors, self.assignments, TODAY)
        assign_patient(second, self.rooms, self.doctors, self.assignments, TODAY)
        with self.assertRaisesRegex(ValueError, 'No available room'):
            assign_patient(third, self.rooms, self.doctors, self.assignments, TODAY)

        released = release_reservation('Q0101', self.assignments)
        self.assertEqual(released, {'room_id': 'R01-1', 'doctor_id': 'D01-1'})
        # The third case can now be served with the freed pair.
        self.assertEqual(assign_patient(third, self.rooms, self.doctors,
                                        self.assignments, TODAY),
                         {'room_id': 'R01-1', 'doctor_id': 'D01-1'})

    def test_releasing_something_unassigned_is_harmless(self):
        self.assertIsNone(release_reservation('Q0199', self.assignments))

    def test_released_resources_show_as_available_again(self):
        record = case('Q0101')
        assign_patient(record, self.rooms, self.doctors, self.assignments, TODAY)
        free_rooms, _ = available_resources('General medicine', self.rooms,
                                            self.doctors, self.assignments)
        self.assertNotIn('R01-1', [room['id'] for room in free_rooms])

        release_reservation('Q0101', self.assignments)
        free_rooms, _ = available_resources('General medicine', self.rooms,
                                            self.doctors, self.assignments)
        self.assertIn('R01-1', [room['id'] for room in free_rooms])


class CompletedCaseTests(unittest.TestCase):

    def setUp(self):
        self.rooms, self.doctors = make_demo_resources()
        self.assignments = {}

    def test_a_completed_case_cannot_be_assigned_again(self):
        done = case('Q0101', status='completed')
        with self.assertRaisesRegex(ValueError, 'already marked done'):
            assign_patient(done, self.rooms, self.doctors, self.assignments, TODAY)

    def test_auto_assign_skips_completed_cases(self):
        records = [case('Q0101', status='completed'), case('Q0102')]
        result = auto_assign(records, self.rooms, self.doctors, self.assignments, TODAY)
        self.assertEqual([queue_id for queue_id, _ in result['assigned']], ['Q0102'])
        # A finished case is not a failure, so it is not reported as waiting.
        self.assertEqual(result['waiting'], [])

    def test_a_record_without_a_status_is_still_assignable(self):
        """Records written before the lifecycle existed must keep working."""
        old = {'queue_id': 'Q0101', 'destination_ward': 'General medicine',
               'appointment_date': TODAY.isoformat()}
        self.assertEqual(assign_patient(old, self.rooms, self.doctors,
                                        self.assignments, TODAY)['room_id'], 'R01-1')


class StatusStorageTests(unittest.TestCase):

    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix='.db')
        os.close(handle)
        os.unlink(self.path)
        self.connection = storage.connect(self.path)
        self.fields = dict(name='Demo Patient', information='Fictional note',
                           phone='0810000000', ward='General medicine')

    def tearDown(self):
        self.connection.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def make(self, records):
        return create_patient_record(**self.fields, date_text='2026-09-08',
                                     records=records)

    def test_a_new_record_starts_waiting(self):
        record = self.make([])
        self.assertEqual(record['status'], 'waiting')
        self.assertIsNone(record['completed_at'])

    def test_status_round_trips_through_the_database(self):
        record = self.make([])
        storage.save_registration(self.connection, record)
        self.assertEqual(storage.load_registrations(self.connection)[0], record)

    def test_marking_done_is_saved(self):
        record = self.make([])
        storage.save_registration(self.connection, record)
        self.assertTrue(storage.set_case_status(
            self.connection, record['appointment_date'], record['queue_id'],
            storage.COMPLETED, '2026-09-08 14:30:00'))

        loaded = storage.load_registrations(self.connection)[0]
        self.assertEqual(loaded['status'], 'completed')
        self.assertEqual(loaded['completed_at'], '2026-09-08 14:30:00')

    def test_completion_survives_reopening(self):
        record = self.make([])
        storage.save_registration(self.connection, record)
        storage.set_case_status(self.connection, record['appointment_date'],
                                record['queue_id'], storage.COMPLETED, 'now')
        self.connection.close()

        reopened = storage.connect(self.path)
        try:
            self.assertEqual(reopened.execute(
                'SELECT status FROM registrations').fetchone()[0], 'completed')
        finally:
            reopened.close()
            self.connection = storage.connect(self.path)

    def test_status_needs_both_halves_of_the_key(self):
        keep = dict(self.make([]), queue_id='Q0147', appointment_date='2026-09-08')
        other = dict(keep, appointment_date='2026-09-09')
        storage.save_registration(self.connection, keep)
        storage.save_registration(self.connection, other)

        storage.set_case_status(self.connection, '2026-09-09', 'Q0147',
                                storage.COMPLETED, 'now')
        by_date = {row['appointment_date']: row['status'] for row in
                   self.connection.execute(
                       'SELECT appointment_date, status FROM registrations')}
        self.assertEqual(by_date['2026-09-08'], 'waiting')
        self.assertEqual(by_date['2026-09-09'], 'completed')

    def test_an_unknown_status_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'Unknown case status'):
            storage.set_case_status(self.connection, '2026-09-08', 'Q0101', 'finished')

    def test_marking_an_absent_case_reports_false(self):
        self.assertFalse(storage.set_case_status(
            self.connection, '2026-09-08', 'Q0199', storage.COMPLETED, 'now'))


class MigrationTests(unittest.TestCase):
    """A database created before the lifecycle existed must keep its data."""

    # The registrations table exactly as it was before status/completed_at.
    OLD_SCHEMA = """
    CREATE TABLE registrations (
        row_id              INTEGER PRIMARY KEY,
        appointment_date    TEXT NOT NULL,
        queue_id            TEXT NOT NULL,
        patient_name        TEXT NOT NULL,
        medical_information TEXT NOT NULL,
        phone_number        TEXT NOT NULL,
        destination_ward    TEXT NOT NULL,
        ward_code           TEXT NOT NULL,
        UNIQUE (appointment_date, queue_id)
    );
    """

    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix='.db')
        os.close(handle)
        os.unlink(self.path)
        old = sqlite3.connect(self.path)
        old.executescript(self.OLD_SCHEMA)
        old.execute(
            'INSERT INTO registrations (appointment_date, queue_id, patient_name,'
            ' medical_information, phone_number, destination_ward, ward_code)'
            " VALUES ('2026-09-08', 'Q0147', 'Existing Patient', 'note',"
            " '0810000000', 'General medicine', '01')")
        old.commit()
        old.close()

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_the_existing_patient_is_not_lost(self):
        connection = storage.connect(self.path)
        try:
            records = storage.load_registrations(connection)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['patient_name'], 'Existing Patient')
        finally:
            connection.close()

    def test_an_older_record_is_treated_as_waiting(self):
        connection = storage.connect(self.path)
        try:
            record = storage.load_registrations(connection)[0]
            self.assertEqual(record['status'], 'waiting')
            self.assertIsNone(record['completed_at'])
        finally:
            connection.close()

    def test_the_migrated_database_accepts_completion(self):
        connection = storage.connect(self.path)
        try:
            storage.set_case_status(connection, '2026-09-08', 'Q0147',
                                    storage.COMPLETED, 'now')
            self.assertEqual(storage.load_registrations(connection)[0]['status'],
                             'completed')
        finally:
            connection.close()

    def test_migrating_twice_is_harmless(self):
        """connect() runs at every startup, so it must be repeatable."""
        for _ in range(3):
            connection = storage.connect(self.path)
            connection.close()
        connection = storage.connect(self.path)
        try:
            self.assertEqual(len(storage.load_registrations(connection)), 1)
        finally:
            connection.close()


if __name__ == '__main__':
    unittest.main()
