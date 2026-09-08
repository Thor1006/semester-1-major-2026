"""Checks for saving and reloading registrations.

    python -m unittest -v test_storage.py

Every test uses a temporary database file, so running these never reads or
writes the real clinic.db.
"""

import os
import sqlite3
import tempfile
import unittest

import storage
from registration import create_patient_record


class StorageTests(unittest.TestCase):

    def setUp(self):
        # mkstemp returns an open file handle and a path. We close the handle
        # immediately because SQLite wants to open the file itself; on Windows a
        # file left open here could not be reopened.
        handle, self.path = tempfile.mkstemp(suffix='.db')
        os.close(handle)
        os.unlink(self.path)          # let connect() create it from scratch
        self.connection = storage.connect(self.path)
        self.fields = dict(name='Demo Patient', information='Fictional note only',
                           phone='081-000-0000', ward='General medicine')

    def tearDown(self):
        self.connection.close()
        if os.path.exists(self.path):
            os.unlink(self.path)

    def make(self, records, date_text='2026-09-08'):
        return create_patient_record(**self.fields, date_text=date_text, records=records)

    def test_a_new_database_is_empty(self):
        self.assertEqual(storage.load_registrations(self.connection), [])
        self.assertEqual(storage.count_registrations(self.connection), 0)

    def test_a_saved_registration_comes_back_unchanged(self):
        """A loaded record must be indistinguishable from a fresh one."""
        record = self.make([])
        storage.save_registration(self.connection, record)
        loaded = storage.load_registrations(self.connection)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0], record)

    def test_records_keep_their_arrival_order(self):
        records = []
        for _ in range(5):
            record = self.make(records)
            records.append(record)
            storage.save_registration(self.connection, record)
        loaded = storage.load_registrations(self.connection)
        self.assertEqual([r['queue_id'] for r in loaded],
                         [r['queue_id'] for r in records])

    def test_blank_medical_information_survives(self):
        """Medical information is optional; empty must stay empty, not become None."""
        record = create_patient_record(**{**self.fields, 'information': ''},
                                       date_text='2026-09-08', records=[])
        storage.save_registration(self.connection, record)
        self.assertEqual(storage.load_registrations(self.connection)[0]['medical_information'], '')

    def test_the_same_ticket_is_allowed_on_a_different_date(self):
        """The whole point of date-scoped tickets: Q0147 may recur another day."""
        first = dict(self.make([]), queue_id='Q0147', appointment_date='2026-09-08')
        second = dict(first, appointment_date='2026-09-09')
        storage.save_registration(self.connection, first)
        storage.save_registration(self.connection, second)
        self.assertEqual(storage.count_registrations(self.connection), 2)

    def test_the_same_ticket_twice_on_one_date_is_refused(self):
        """The database enforces the key, not just the ID generator."""
        record = dict(self.make([]), queue_id='Q0147', appointment_date='2026-09-08')
        storage.save_registration(self.connection, record)
        with self.assertRaisesRegex(ValueError, 'already saved'):
            storage.save_registration(self.connection, dict(record))
        self.assertEqual(storage.count_registrations(self.connection), 1)

    def test_a_refused_duplicate_does_not_corrupt_the_stored_row(self):
        record = dict(self.make([]), queue_id='Q0147', appointment_date='2026-09-08',
                      patient_name='First Patient')
        storage.save_registration(self.connection, record)
        clash = dict(record, patient_name='Second Patient')
        with self.assertRaises(ValueError):
            storage.save_registration(self.connection, clash)
        stored = storage.load_registrations(self.connection)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]['patient_name'], 'First Patient')

    def test_data_survives_closing_and_reopening(self):
        """The actual promise: closing the app must not lose the queue."""
        record = self.make([])
        storage.save_registration(self.connection, record)
        self.connection.close()

        reopened = storage.connect(self.path)
        try:
            self.assertEqual(storage.load_registrations(reopened), [record])
        finally:
            reopened.close()
            self.connection = storage.connect(self.path)   # for tearDown

    def test_connect_is_safe_to_run_on_an_existing_database(self):
        """Startup runs connect() every time; it must not wipe or fail."""
        record = self.make([])
        storage.save_registration(self.connection, record)
        again = storage.connect(self.path)
        try:
            self.assertEqual(storage.count_registrations(again), 1)
        finally:
            again.close()

    def test_loaded_records_feed_the_id_generator(self):
        """Reloaded tickets must be excluded when the next ID is chosen."""
        records = []
        for _ in range(100):
            record = self.make(records)
            records.append(record)
            storage.save_registration(self.connection, record)

        # A fresh session: the list is rebuilt from disk, not from memory.
        restored = storage.load_registrations(self.connection)
        with self.assertRaisesRegex(ValueError, 'all 100'):
            self.make(restored)
        # The next day still works, because the pool is scoped to a date.
        tomorrow = self.make(restored, date_text='2026-09-09')
        self.assertTrue(tomorrow['queue_id'].startswith('Q01'))

    def test_a_quote_in_a_name_is_stored_literally(self):
        """Placeholders, not string joining: an apostrophe must not break SQL."""
        record = dict(self.make([]), patient_name="O'Brien Test-Patient")
        storage.save_registration(self.connection, record)
        self.assertEqual(storage.load_registrations(self.connection)[0]['patient_name'],
                         "O'Brien Test-Patient")

    def test_the_unique_rule_exists_in_the_schema(self):
        """Guard against someone removing the constraint the key depends on."""
        sql = self.connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'registrations'").fetchone()[0]
        self.assertIn('UNIQUE', sql.upper())
        self.assertIn('appointment_date', sql)
        self.assertIn('queue_id', sql)


if __name__ == '__main__':
    unittest.main()
