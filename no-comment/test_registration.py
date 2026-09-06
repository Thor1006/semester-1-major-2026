"""Checks for lesson 2. All patient details here are fictional test inputs."""

import unittest
from unittest.mock import patch

from registration import WARD_CODES, create_patient_record, generate_queue_id


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.records = []
        self.fields = dict(name='Demo Patient', information='Fictional note only',
                           date_text='2026-09-06', phone='081-000-0000',
                           ward='General medicine', records=self.records)

    def test_same_ward_prefix_is_allowed_but_full_ids_are_unique(self):
        for _ in range(100):
            self.records.append(create_patient_record(**self.fields))
        ids = {record['queue_id'] for record in self.records}
        self.assertEqual(ids, {f'Q01{number:02d}' for number in range(100)})

    def test_full_ward_does_not_block_other_ward_or_mutate_records(self):
        self.records.extend({'queue_id': f'Q01{number:02d}'} for number in range(100))
        with self.assertRaisesRegex(ValueError, 'all 100'):
            create_patient_record(**self.fields)
        self.assertEqual(len(self.records), 100)
        other = create_patient_record(**{**self.fields, 'ward': 'Pediatrics'})
        self.assertTrue(other['queue_id'].startswith('Q02'))

    def test_only_remaining_suffix_is_used(self):
        used = {f'Q01{number:02d}' for number in range(100) if number != 7}
        self.assertEqual(generate_queue_id('01', used), 'Q0107')

    def test_required_fields_and_limits(self):
        for field, value in [('name', ' '), ('name', 'x'*101), ('information', 'x'*2001),
                             ('ward', ''), ('ward', 'Unknown'), ('phone', ''),
                             ('phone', 'abc0810000000'), ('phone', '123'),
                             ('phone', '1'*16), ('phone', '081+0000000')]:
            with self.subTest(field=field, value_length=len(value)):
                with self.assertRaises(ValueError):
                    create_patient_record(**{**self.fields, field: value})
                self.assertEqual(self.records, [])

    def test_actual_calendar_and_explicit_date_format(self):
        for invalid in ['2026-02-29', '2026-02-30', '06/09/2026', '20260906', '2026-9-6', '']:
            with self.subTest(date=invalid):
                with self.assertRaises(ValueError):
                    create_patient_record(**{**self.fields, 'date_text': invalid})
        leap = create_patient_record(**{**self.fields, 'date_text': '2028-02-29'})
        self.assertEqual(leap['appointment_date'], '2028-02-29')

    def test_optional_notes_unicode_names_and_phone_normalization(self):
        record = create_patient_record(**{
            **self.fields, 'name': '  ผู้ป่วยตัวอย่าง  ', 'information': ' ',
            'phone': '+66 (81) 000-0000',
        })
        self.assertEqual(record['patient_name'], 'ผู้ป่วยตัวอย่าง')
        self.assertEqual(record['medical_information'], '')
        self.assertEqual(record['phone_number'], '+66810000000')
        local = create_patient_record(**self.fields)
        self.assertEqual(local['phone_number'], '0810000000')

    def test_configuration_checks(self):
        for invalid in ['1', '001', 'ab']:
            with self.assertRaises(ValueError):
                generate_queue_id(invalid, set())
        with patch.dict(WARD_CODES, {'Pediatrics': '01'}):
            with self.assertRaisesRegex(ValueError, 'unique code'):
                create_patient_record(**self.fields)


class InterfaceTests(unittest.TestCase):
    def test_registration_popup_table_and_invalid_double_click(self):
        import app
        app.window.withdraw()
        try:
            with patch('app.messagebox.showinfo') as popup:
                app.add_button.invoke()
                self.assertEqual(app.patient_records, [])
                popup.assert_not_called()
                for _ in range(2):
                    app.name_entry.insert(0, 'Demo Patient')
                    app.information_text.insert('1.0', 'Fictional private note')
                    app.phone_entry.insert(0, '081-000-0000')
                    app.date_entry.delete(0, 'end')
                    app.date_entry.insert(0, '2026-09-06')
                    app.ward_combobox.set('General medicine')
                    app.add_button.invoke()
                self.assertEqual(len(app.patient_records), 2)
                self.assertEqual(len(app.queue_table.get_children()), 2)
                self.assertEqual(popup.call_count, 2)
                for record in app.patient_records:
                    self.assertTrue(record['queue_id'].startswith('Q01'))
                    self.assertEqual(record['medical_information'], 'Fictional private note')
                    self.assertEqual(app.queue_table.item(record['queue_id'], 'values'),
                                     (record['queue_id'], 'General medicine', '2026-09-06'))
                self.assertNotEqual(app.patient_records[0]['queue_id'], app.patient_records[1]['queue_id'])
                self.assertNotIn('Fictional private note', popup.call_args.args[1])
                self.assertEqual(app.name_entry.get(), '')
                self.assertEqual(app.phone_entry.get(), '')
                self.assertEqual(app.information_text.get('1.0', 'end-1c'), '')
                app.add_button.invoke()
                self.assertEqual(len(app.patient_records), 2)
                self.assertEqual(popup.call_count, 2)
        finally:
            app.window.destroy()


if __name__ == '__main__':
    unittest.main()
