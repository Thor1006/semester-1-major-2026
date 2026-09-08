"""Lesson 2: validate patient input and generate a ward-based queue ID.

No widgets, files, or API requests belong here. Separating these rules from
Tkinter makes them testable without opening a window.
"""

# Standard-library tools: choose randomly, check text patterns, validate dates.
import random
import re
from datetime import date


# This DICTIONARY maps ward names (keys) to two-character codes (values).
# These are editable examples, not official hospital codes. Each ward needs
# its own unique code. Quotes preserve the leading zero in '01'.
# A ward can contain multiple rooms. This code identifies the WARD, not a room.
# Many patients may share the prefix Q01; only the complete ID must be unique.
WARD_CODES = {
    'General medicine': '01',
    'Pediatrics': '02',
    'Orthopedics': '03',
    'Ophthalmology': '04',
}


def generate_queue_id(ward_code, existing_ids):
    """Return an unused Q + two-digit ward + two-digit random suffix."""
    # fullmatch checks the WHOLE string; [0-9]{2} means exactly two ASCII digits.
    # Raising ValueError hands an error to the caller without opening a dialog.
    if not re.fullmatch(r'[0-9]{2}', ward_code):
        raise ValueError('A ward code must contain exactly two digits.')

    # range(100) yields 0 through 99; its upper limit is excluded.
    # :02d formats a decimal integer with width 2, padding with zeros:
    # 7 -> '07', 0 -> '00', 47 -> '47'. Ward '01' therefore gives Q0100...Q0199.
    # This LIST COMPREHENSION evaluates the first expression for each number,
    # keeping only candidates whose FULL ID is not already in existing_ids.
    available_ids = [
        f'Q{ward_code}{number:02d}'
        for number in range(100)
        if f'Q{ward_code}{number:02d}' not in existing_ids
    ]

    # Randomness alone does not guarantee uniqueness. Choose only from unused
    # IDs rather than repeatedly guessing: retry loops can get stuck when full.
    # Two random digits allow exactly 100 IDs per ward, regardless of room count.
    if not available_ids:
        raise ValueError(
            f'Ward {ward_code} has used all 100 queue IDs for this appointment date. '
            'No patient was added. A larger ID format is needed for more cases.'
        )

    # choice picks one ITEM from a nonempty list. A queue label is not a password
    # or authorization token. The random digits do not encode priority or order.
    return random.choice(available_ids)


def create_patient_record(name, information, date_text, phone, ward, records):
    """Validate inputs and return a dictionary; the caller stores it afterward."""
    # Parameters are local names receiving arguments from app.py. strip returns
    # cleaned text; it does not alter the contents of any input widgets.
    name = name.strip()
    information = information.strip()
    date_text = date_text.strip()
    phone = phone.strip()

    # Validate before generating/storing an ID. If any check raises ValueError,
    # execution exits this function and the caller can display the explanation.
    if not name or len(name) > 100:
        raise ValueError('Enter a patient name between 1 and 100 characters.')
    if len(information) > 2000:
        raise ValueError('Keep medical history / information within 2,000 characters.')
    # Blank history is allowed. Missing information is not equivalent to having
    # no medical conditions: never fill it with an invented clinical assertion.

    # The user confirmed this is APPOINTMENT DATE, not date of birth.
    # Regex enforces YYYY-MM-DD; fromisoformat checks the actual calendar,
    # including leap years. Neither check restricts historical appointments.
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

    # Phone numbers are strings: integers would lose a leading zero.
    # Permit common separators and an optional leading +, then count digits.
    # This is a basic format check, not international verification or proof of
    # number ownership. No phone verification service is called.
    if not re.fullmatch(r'\+?[0-9 ().-]+', phone):
        raise ValueError('Use digits, an optional leading +, and common phone separators.')
    digits = ''.join(character for character in phone if character in '0123456789')
    if not 7 <= len(digits) <= 15:
        raise ValueError('Enter a phone number containing 7 to 15 digits.')
    normalized_phone = ('+' if phone.startswith('+') else '') + digits

    # A SET stores distinct values and supports membership checks. Extract full
    # IDs from the records, not just ward prefixes. Q0107 does not block Q0142.
    #
    # Uniqueness is scoped to ONE APPOINTMENT DATE. Each ward's pool of 100
    # suffixes therefore refills every day. That matters because records are
    # about to be saved to disk: if the pool spanned every date, a ward would
    # run out permanently after 100 patients instead of after 100 in one day.
    #
    # The consequence to remember: a ticket is no longer unique on its own.
    # Q0147 may legitimately appear again on another date, so anything storing
    # or looking up a registration must key on the DATE PLUS the ticket.
    # .get() is used because a caller may pass partial records in tests.
    existing_ids = {record['queue_id'] for record in records
                    if record.get('appointment_date') == appointment_date.isoformat()}
    queue_id = generate_queue_id(WARD_CODES[ward], existing_ids)

    # A dictionary represents one registration with named fields. isoformat()
    # converts the validated date object back to YYYY-MM-DD text. Returning this
    # dictionary does not yet append it to the queue; app.py handles that step.
    return {
        'queue_id': queue_id,
        'patient_name': name,
        'medical_information': information,
        'appointment_date': appointment_date.isoformat(),
        'phone_number': normalized_phone,
        'destination_ward': ward,
        'ward_code': WARD_CODES[ward],
        # Every case starts waiting. 'completed' is set when staff mark the
        # visit finished, which also releases its room and doctor. Including
        # both keys here means a record loaded from the database has exactly
        # the same shape as a fresh one, so nothing downstream has to care
        # where a record came from.
        'status': 'waiting',
        'completed_at': None,
    }
