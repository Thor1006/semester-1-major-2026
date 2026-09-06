"""Lesson 2: validate patient input and generate a ward-based queue ID.

No widgets, files, or API requests belong here. Separating these rules from
Tkinter makes them testable without opening a window.
"""

import random
import re
from datetime import date


WARD_CODES = {
    'General medicine': '01',
    'Pediatrics': '02',
    'Orthopedics': '03',
    'Ophthalmology': '04',
}


def generate_queue_id(ward_code, existing_ids):
    """Return an unused Q + two-digit ward + two-digit random suffix."""
    if not re.fullmatch(r'[0-9]{2}', ward_code):
        raise ValueError('A ward code must contain exactly two digits.')

    available_ids = [
        f'Q{ward_code}{number:02d}'
        for number in range(100)
        if f'Q{ward_code}{number:02d}' not in existing_ids
    ]

    if not available_ids:
        raise ValueError(
            f'Ward {ward_code} has used all 100 queue IDs in this session. '
            'No patient was added. A larger ID format is needed for more cases.'
        )

    return random.choice(available_ids)


def create_patient_record(name, information, date_text, phone, ward, records):
    """Validate inputs and return a dictionary; the caller stores it afterward."""
    name = name.strip()
    information = information.strip()
    date_text = date_text.strip()
    phone = phone.strip()

    if not name or len(name) > 100:
        raise ValueError('Enter a patient name between 1 and 100 characters.')
    if len(information) > 2000:
        raise ValueError('Keep medical history / information within 2,000 characters.')

    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', date_text):
        raise ValueError('Enter the appointment date as YYYY-MM-DD, for example 2026-09-06.')
    try:
        appointment_date = date.fromisoformat(date_text)
    except ValueError:
        raise ValueError('Enter a real calendar date; that date does not exist.') from None

    if ward not in WARD_CODES:
        raise ValueError('Choose a destination ward from the list.')
    if len(set(WARD_CODES.values())) != len(WARD_CODES):
        raise ValueError('Give each ward a unique code in the ward configuration.')

    if not re.fullmatch(r'\+?[0-9 ().-]+', phone):
        raise ValueError('Use digits, an optional leading +, and common phone separators.')
    digits = ''.join(character for character in phone if character in '0123456789')
    if not 7 <= len(digits) <= 15:
        raise ValueError('Enter a phone number containing 7 to 15 digits.')
    normalized_phone = ('+' if phone.startswith('+') else '') + digits

    existing_ids = {record['queue_id'] for record in records}
    queue_id = generate_queue_id(WARD_CODES[ward], existing_ids)

    return {
        'queue_id': queue_id,
        'patient_name': name,
        'medical_information': information,
        'appointment_date': appointment_date.isoformat(),
        'phone_number': normalized_phone,
        'destination_ward': ward,
        'ward_code': WARD_CODES[ward],
    }
