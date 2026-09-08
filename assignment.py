"""Lesson 3: reserve a compatible room AND doctor for a registered case today.

These are immediate, in-memory reservations, not a future appointment calendar.
There are no Tkinter imports: the same rules can be tested without a window.
"""

from datetime import date
from registration import WARD_CODES


# How many rooms and doctors a ward has if nothing else has been configured.
DEFAULT_CAPACITY = (2, 2)

# An upper bound on what the interface will configure. It is a guard against a
# typed 900 filling the table with pretend resources, not a hospital rule.
MAX_PER_WARD = 12


def make_demo_resources(capacity=None, disabled=()):
    """Create fresh resources for every ward.

    capacity maps a ward name to a (rooms, doctors) pair. Wards missing from it
    fall back to DEFAULT_CAPACITY, so old callers and tests that pass nothing
    still get the original two-and-two demonstration.

    disabled is a collection of resource IDs to mark unusable, which is how a
    room out for maintenance survives a restart.
    """
    # A factory function builds NEW lists/dictionaries every time it is called.
    # Tests can therefore start clean without sharing another test's resources.
    capacity = capacity or {}
    disabled = set(disabled)
    rooms = []
    doctors = []
    for ward, code in WARD_CODES.items():
        room_count, doctor_count = capacity.get(ward, DEFAULT_CAPACITY)
        # range(1, n + 1) yields 1..n. These are example resource IDs, distinct
        # from a patient's QWWRR ticket. More rooms can belong to the same ward.
        #
        # The NUMBERING MATTERS: a resource keeps its ID when capacity changes,
        # because IDs are derived from position, not from insertion order. Going
        # from two rooms to three adds R01-3 and leaves R01-1 and R01-2 exactly
        # as they were, so an existing reservation still points at a real room.
        for number in range(1, room_count + 1):
            identifier = f'R{code}-{number}'
            rooms.append({'id': identifier, 'ward': ward,
                          'enabled': identifier not in disabled})
        for number in range(1, doctor_count + 1):
            identifier = f'D{code}-{number}'
            doctors.append({'id': identifier, 'wards': [ward],
                            'enabled': identifier not in disabled})
    # Return a pair of lists (a tuple). The caller can unpack: rooms, doctors = ...
    return rooms, doctors


def blocking_reservations(ward, room_count, doctor_count, capacity, assignments):
    """Reserved resource IDs that shrinking a ward would delete.

    An empty list means the change is safe. A non-empty one means staff must
    deal with those cases first: `AGENTS.md` requires that in-progress work is
    not altered behind the user's back, and silently dropping a reservation
    would leave a patient unassigned with nobody told.

    Reducing capacity removes resources from the END of the numbering, so
    going from three rooms to two removes R01-3 and never renames R01-1.
    """
    old_rooms, old_doctors = capacity.get(ward, DEFAULT_CAPACITY)
    code = WARD_CODES[ward]
    # range is empty when the new count is not smaller, so growing a ward
    # produces no candidates for removal at all.
    removed = [f'R{code}-{number}' for number in range(room_count + 1, old_rooms + 1)]
    removed += [f'D{code}-{number}' for number in range(doctor_count + 1, old_doctors + 1)]

    reserved = set()
    for reservation in assignments.values():
        reserved.add(reservation['room_id'])
        reserved.add(reservation['doctor_id'])
    return [identifier for identifier in removed if identifier in reserved]


def check_case_is_assignable(record, assignments, today=None):
    """Raise unless this case may receive a reservation right now.

    Shared by every assignment mode, so automatic, manual and first-fit can
    never disagree about which cases are eligible.
    """
    queue_id = record['queue_id']
    # assignments is a dictionary keyed by queue ID. Each value records one
    # reserved room and doctor. This is the single source of reservation state:
    # we derive availability from it instead of maintaining duplicate busy flags.
    if queue_id in assignments:
        raise ValueError(f'{queue_id} already has an assignment.')

    # A reservation means NOW. Later dates must not consume today's resources.
    # The optional today parameter allows repeatable tests with a known date.
    # Passing no date uses the local computer's calendar date.
    if today is None:
        today = date.today()
    if record['appointment_date'] != today.isoformat():
        raise ValueError('Only appointments dated today can receive an immediate assignment.')
    return record['destination_ward']


def available_resources(ward, rooms, doctors, assignments):
    """Return the (rooms, doctors) in `ward` that are enabled and unreserved.

    The manual chooser shows exactly this list, so a staff member can never be
    offered a resource that the rules would then refuse.
    """
    # Set comprehensions collect resource IDs already reserved by ANY case.
    # Doctors can support multiple wards, so their occupancy must be global.
    used_rooms = {item['room_id'] for item in assignments.values()}
    used_doctors = {item['doctor_id'] for item in assignments.values()}

    free_rooms = []
    for candidate in rooms:
        # and requires all conditions. enabled models a room that is usable;
        # a room without a reservation may still be disabled for maintenance.
        if candidate['ward'] == ward and candidate['enabled'] and candidate['id'] not in used_rooms:
            free_rooms.append(candidate)

    free_doctors = []
    for candidate in doctors:
        # in checks membership of the supported-wards list. It does not infer a
        # doctor's qualifications from medical notes: compatibility is configured.
        if ward in candidate['wards'] and candidate['enabled'] and candidate['id'] not in used_doctors:
            free_doctors.append(candidate)
    return free_rooms, free_doctors


def assign_patient(record, rooms, doctors, assignments, today=None):
    """Reserve the FIRST compatible free room and doctor, after validation."""
    ward = check_case_is_assignable(record, assignments, today)
    free_rooms, free_doctors = available_resources(ward, rooms, doctors, assignments)
    if not free_rooms:
        raise ValueError(f'No available room in {ward}. The case stays waiting.')
    if not free_doctors:
        raise ValueError(f'No available doctor for {ward}. The case stays waiting.')

    # FIRST FIT: take the earliest compatible free room and doctor in the order
    # they were configured. This is deliberately simple and DETERMINISTIC, so the
    # same waiting list always produces the same reservations and a staff member
    # can predict what the button will do. It does not claim to be the best
    # possible pairing; choosing among feasible pairs needs a stated goal, and
    # this lesson has not defined one.
    chosen = {'room_id': free_rooms[0]['id'], 'doctor_id': free_doctors[0]['id']}

    # Only NOW, after finding BOTH resources, change the shared dictionary.
    # Had we reserved the room earlier, a missing doctor could leave it stuck.
    # The GUI calls this short function on one thread. Multi-user/concurrent
    # scheduling would need database transactions, which this lesson does not use.
    assignments[record['queue_id']] = chosen
    return chosen


def assign_patient_to(record, rooms, doctors, assignments, room_id, doctor_id,
                      today=None):
    """Reserve the room and doctor a staff member CHOSE, if the rules allow it.

    Manual assignment overrides which pair is used, never whether the pair is
    legal. A staff member knows things the program does not - who a patient saw
    last time, which room has the right equipment - but they cannot put two
    people in one room, and the same checks apply as for the automatic modes.
    """
    ward = check_case_is_assignable(record, assignments, today)
    free_rooms, free_doctors = available_resources(ward, rooms, doctors, assignments)

    # _explain_choice raises with a specific reason. Both are checked BEFORE
    # anything changes, so a bad doctor cannot leave a room half-reserved.
    _explain_choice(room_id, 'room', rooms, free_rooms, ward, assignments, 'room_id')
    _explain_choice(doctor_id, 'doctor', doctors, free_doctors, ward, assignments,
                    'doctor_id')

    chosen = {'room_id': room_id, 'doctor_id': doctor_id}
    assignments[record['queue_id']] = chosen
    return chosen


def _explain_choice(identifier, kind, all_resources, free_resources, ward,
                    assignments, key):
    """Raise a message saying exactly why a chosen resource cannot be used."""
    if any(resource['id'] == identifier for resource in free_resources):
        return                                   # it is available: nothing to say

    resource = next((r for r in all_resources if r['id'] == identifier), None)
    if resource is None:
        raise ValueError(f'{identifier} is not a {kind} in this clinic.')

    # Naming the ward, the maintenance state or the holding ticket is the
    # difference between a message staff can act on and one they cannot.
    supported = [resource['ward']] if kind == 'room' else resource['wards']
    if ward not in supported:
        raise ValueError(f'{identifier} does not serve {ward}.')
    if not resource['enabled']:
        raise ValueError(f'{identifier} is out of service.')
    holder = next((queue_id for queue_id, reservation in assignments.items()
                   if reservation[key] == identifier), None)
    raise ValueError(f'{identifier} is already reserved by {holder}.')


def auto_assign(records, rooms, doctors, assignments, today=None):
    """Assign every waiting case for today, in ARRIVAL ORDER.

    First come, first served. `records` is the registration list, which is kept
    in the order cases arrived - and reloaded from the database in that same
    order - so simply walking it front to back IS the queue discipline. The
    random part of a ticket says nothing about position: Q0199 may well have
    arrived before Q0102.

    A case that cannot be served does not stop the run. It is left waiting with
    its reason recorded and the next case is tried, so one full ward never
    blocks a different ward that still has room.

    Returns {'assigned': [(queue_id, reservation)], 'waiting': [(queue_id, why)]}.
    """
    assigned = []
    waiting = []
    for record in records:
        queue_id = record['queue_id']
        # Cases already holding a reservation, and cases for another date, are
        # not failures - they are simply not part of today's waiting list.
        if queue_id in assignments:
            continue
        if today is None:
            reference = date.today()
        else:
            reference = today
        if record['appointment_date'] != reference.isoformat():
            continue
        try:
            assigned.append((queue_id, assign_patient(record, rooms, doctors,
                                                      assignments, today)))
        except ValueError as error:
            waiting.append((queue_id, str(error)))
    return {'assigned': assigned, 'waiting': waiting}
