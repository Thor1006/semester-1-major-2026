"""Checks for reading registrations from a CSV file.

    python -m unittest -v test_bulk_import.py

All patient details here are fictional test inputs.
"""

import os
import tempfile
import unittest

from bulk_import import REQUIRED_COLUMNS, read_import_file

HEADER = ','.join(REQUIRED_COLUMNS)
GOOD_ROW = 'Demo Patient,Fictional note,2026-09-10,0810000000,General medicine'


class BulkImportTests(unittest.TestCase):

    def write(self, text):
        """Write a temporary CSV and return its path."""
        handle, path = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(handle, 'w', encoding='utf-8', newline='') as file:
            file.write(text)
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        return path

    def test_a_valid_file_produces_records(self):
        path = self.write(f'{HEADER}\n{GOOD_ROW}\n')
        records = read_import_file(path, [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['patient_name'], 'Demo Patient')
        self.assertEqual(records[0]['destination_ward'], 'General medicine')
        self.assertTrue(records[0]['queue_id'].startswith('Q01'))

    def test_tickets_are_generated_not_taken_from_the_file(self):
        """An imported row must not be able to choose or collide with an ID."""
        rows = '\n'.join([GOOD_ROW] * 5)
        records = read_import_file(self.write(f'{HEADER}\n{rows}\n'), [])
        ids = {record['queue_id'] for record in records}
        self.assertEqual(len(ids), 5, 'each imported row needs its own ticket')

    def test_generated_tickets_avoid_existing_records(self):
        existing = [{'queue_id': f'Q01{n:02d}', 'appointment_date': '2026-09-10'}
                    for n in range(100) if n != 7]
        records = read_import_file(self.write(f'{HEADER}\n{GOOD_ROW}\n'), existing)
        self.assertEqual(records[0]['queue_id'], 'Q0107')

    def test_a_full_day_is_refused_rather_than_overflowing(self):
        existing = [{'queue_id': f'Q01{n:02d}', 'appointment_date': '2026-09-10'}
                    for n in range(100)]
        with self.assertRaisesRegex(ValueError, 'all 100'):
            read_import_file(self.write(f'{HEADER}\n{GOOD_ROW}\n'), existing)

    def test_blank_medical_information_is_allowed(self):
        row = 'Demo Patient,,2026-09-10,0810000000,General medicine'
        records = read_import_file(self.write(f'{HEADER}\n{row}\n'), [])
        self.assertEqual(records[0]['medical_information'], '')

    def test_one_bad_row_prevents_the_whole_import(self):
        """All or nothing: a partial import would leave the user guessing."""
        bad = 'Demo Patient,note,NOT-A-DATE,0810000000,General medicine'
        path = self.write(f'{HEADER}\n{GOOD_ROW}\n{bad}\n{GOOD_ROW}\n')
        with self.assertRaises(ValueError) as caught:
            read_import_file(path, [])
        self.assertIn('Nothing was imported', str(caught.exception))

    def test_problem_rows_are_numbered_as_the_spreadsheet_shows_them(self):
        """Row 1 is the header, so the first patient is row 2."""
        bad = 'Demo Patient,note,NOT-A-DATE,0810000000,General medicine'
        path = self.write(f'{HEADER}\n{GOOD_ROW}\n{bad}\n')
        with self.assertRaises(ValueError) as caught:
            read_import_file(path, [])
        self.assertIn('Row 3:', str(caught.exception))

    def test_every_problem_is_reported_not_just_the_first(self):
        bad_date = 'Demo Patient,note,NOT-A-DATE,0810000000,General medicine'
        bad_ward = 'Demo Patient,note,2026-09-10,0810000000,Nowhere'
        path = self.write(f'{HEADER}\n{bad_date}\n{bad_ward}\n')
        with self.assertRaises(ValueError) as caught:
            read_import_file(path, [])
        message = str(caught.exception)
        self.assertIn('Row 2:', message)
        self.assertIn('Row 3:', message)

    def test_a_long_list_of_problems_is_summarised(self):
        bad = 'Demo Patient,note,NOT-A-DATE,0810000000,General medicine'
        path = self.write(f'{HEADER}\n' + '\n'.join([bad] * 40) + '\n')
        with self.assertRaises(ValueError) as caught:
            read_import_file(path, [])
        self.assertIn('and 28 more', str(caught.exception))

    def test_a_missing_column_is_named(self):
        path = self.write('patient_name,appointment_date\nDemo,2026-09-10\n')
        with self.assertRaises(ValueError) as caught:
            read_import_file(path, [])
        message = str(caught.exception)
        self.assertIn('medical_information', message)
        self.assertIn('phone_number', message)
        self.assertIn('destination_ward', message)

    def test_a_header_with_no_rows_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'no data rows'):
            read_import_file(self.write(f'{HEADER}\n'), [])

    def test_an_empty_file_is_refused(self):
        with self.assertRaises(ValueError):
            read_import_file(self.write(''), [])

    def test_a_quoted_field_containing_a_comma_stays_one_value(self):
        row = 'Demo Patient,"Headaches, and dizziness",2026-09-10,0810000000,General medicine'
        records = read_import_file(self.write(f'{HEADER}\n{row}\n'), [])
        self.assertEqual(records[0]['medical_information'], 'Headaches, and dizziness')

    def test_an_excel_byte_order_mark_does_not_break_the_header(self):
        """Excel writes a BOM; without utf-8-sig the first column name is wrong."""
        path = self.write('﻿' + f'{HEADER}\n{GOOD_ROW}\n')
        records = read_import_file(path, [])
        self.assertEqual(records[0]['patient_name'], 'Demo Patient')

    def test_the_caller_s_record_list_is_never_modified(self):
        """A failed import must leave the caller exactly as it was."""
        existing = [{'queue_id': 'Q0107', 'appointment_date': '2026-09-10'}]
        before = list(existing)
        bad = 'Demo Patient,note,NOT-A-DATE,0810000000,General medicine'
        with self.assertRaises(ValueError):
            read_import_file(self.write(f'{HEADER}\n{bad}\n'), existing)
        self.assertEqual(existing, before)
        # And a SUCCESSFUL read must not modify it either; app.py appends.
        read_import_file(self.write(f'{HEADER}\n{GOOD_ROW}\n'), existing)
        self.assertEqual(existing, before)

    def test_the_bundled_sample_file_imports_cleanly(self):
        """sample_import.csv is documentation; it must actually work."""
        here = os.path.dirname(os.path.abspath(__file__))
        records = read_import_file(os.path.join(here, 'sample_import.csv'), [])
        self.assertEqual(len(records), 5)
        self.assertEqual({r['appointment_date'] for r in records},
                         {'2026-09-10', '2026-09-11'})


if __name__ == '__main__':
    unittest.main()
