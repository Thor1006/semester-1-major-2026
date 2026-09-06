"""Lesson 3: reserve a compatible room AND doctor for a registered case today.

These are immediate, in-memory reservations, not a future appointment calendar.
There are no Tkinter imports: the same rules can be tested without a window.
"""

from datetime import date
from registration import WARD_CODES


def make_demo_resources():
    """Create fresh example resources: two rooms and two doctors for each ward."""
    # A factory function builds NEW lists/dictionaries every time it is called.
    # Tests can therefore start clean without sharing another test's resources.
    rooms = []
    doctors = []
    for ward, code in WARD_CODES.items():
        # range(1, 3) yields 1 and 2. These are example resource IDs, distinct
        # from a patient's QWWRR ticket. More rooms can belong to the same ward.
        for number in range(1, 3):
            rooms.append({'id': f'R{code}-{number}', 'ward': ward, 'enabled': True})
            doctors.append({'id': f'D{code}-{number}', 'wards': [ward], 'enabled': True})
    # Return a pair of lists (a tuple). The caller can unpack: rooms, doctors = ...
    return rooms, doctors


def assign_patient(record, rooms, doctors, assignments, today=None):
    """Reserve the first compatible free pair; leave state untouched on failure."""
    # assignments is a dictionary keyed by queue ID. Each value records one
    # reserved room and doctor. This is the single source of reservation state:
    # we derive availability from it instead of maintaining duplicate busy flags.
    queue_id = record['queue_id']
    if queue_id in assignments:
        raise ValueError(f'{queue_id} already has an assignment.')

    # A reservation means NOW. Later dates must not consume today's resources.
    # The optional today parameter allows repeatable tests with a known date.
    # Passing no date uses the local computer's calendar date.
    if today is None:
        today = date.today()
    if record['appointment_date'] != today.isoformat():
        raise ValueError('Only appointments dated today can receive an immediate assignment.')

    ward = record['destination_ward']
    # Set comprehensions collect resource IDs already reserved by ANY case.
    # Doctors can support multiple wards, so their occupancy must be global.
    used_rooms = {item['room_id'] for item in assignments.values()}
    used_doctors = {item['doctor_id'] for item in assignments.values()}

    room = None
    for candidate in rooms:
        # and requires all conditions. enabled models a room that is usable;
        # a room without a reservation may still be disabled for maintenance.
        if candidate['ward'] == ward and candidate['enabled'] and candidate['id'] not in used_rooms:
            room = candidate
            break  # Stop searching after the first valid room in configured order.
    if room is None:
        raise ValueError(f'No available room in {ward}. The case stays waiting.')

    doctor = None
    for candidate in doctors:
        # in checks membership of the supported-wards list. It does not infer a
        # doctor's qualifications from medical notes: compatibility is configured.
        if ward in candidate['wards'] and candidate['enabled'] and candidate['id'] not in used_doctors:
            doctor = candidate
            break
    if doctor is None:
        raise ValueError(f'No available doctor for {ward}. The case stays waiting.')

    # Only NOW, after finding BOTH resources, change the shared dictionary.
    # Had we reserved the room earlier, a missing doctor could leave it stuck.
    # The GUI calls this short function on one thread. Multi-user/concurrent
    # scheduling would need database transactions, which this lesson does not use.
    assignment = {'room_id': room['id'], 'doctor_id': doctor['id']}
    assignments[queue_id] = assignment
    return assignment
