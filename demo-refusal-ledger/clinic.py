"""Core rules for the refusal-ledger demonstration.

This folder is STANDALONE on purpose. It imports nothing from the main project,
so Codex can keep editing registration.py and assignment.py without breaking the
demonstration, and the demonstration cannot affect the lessons.

The one difference from the project's assignment.py is the point of the whole
demo. The project does this on failure:

    raise ValueError(f'No available doctor for {ward}. The case stays waiting.')

The binding constraint is computed, turned into a sentence, shown once, and lost.
Here the same computation RETURNS A RECORD instead, so it can be counted later.
"""

from datetime import date

# Ward codes, kept local so this folder does not depend on the project.
WARDS = {
    'General medicine': '01',
    'Pediatrics': '02',
    'Orthopedics': '03',
}

# A refusal caused by a MISSING RESOURCE. These are capacity evidence.
CAPACITY_CODES = ('no_room', 'no_doctor')

# A refusal caused by how the request was made. These say nothing about
# capacity, and counting them as unmet demand would inflate the measurement.
WORKFLOW_CODES = ('duplicate', 'not_today', 'unknown_ward')


def make_resources(spec):
    """Build rooms and doctors from {ward: (room_count, doctor_count)}.

    Returns two lists of dictionaries, matching the project's plain-dict style.
    Resource IDs such as R01-1 and D01-1 are separate from patient queue IDs.
    """
    rooms, doctors = [], []
    for ward, (room_count, doctor_count) in spec.items():
        code = WARDS[ward]
        for number in range(1, room_count + 1):
            rooms.append({'id': f'R{code}-{number}', 'ward': ward, 'enabled': True})
        for number in range(1, doctor_count + 1):
            doctors.append({'id': f'D{code}-{number}', 'wards': [ward], 'enabled': True})
    return rooms, doctors


def free_resources(ward, rooms, doctors, assignments):
    """Return the rooms and doctors in `ward` that are enabled and unreserved.

    Availability is DERIVED from assignments rather than stored as a flag on each
    resource, so the two can never disagree.
    """
    used_rooms = {item['room_id'] for item in assignments.values()}
    used_doctors = {item['doctor_id'] for item in assignments.values()}
    open_rooms = [r for r in rooms
                  if r['ward'] == ward and r['enabled'] and r['id'] not in used_rooms]
    open_doctors = [d for d in doctors
                    if ward in d['wards'] and d['enabled'] and d['id'] not in used_doctors]
    return open_rooms, open_doctors


def try_assign(case, rooms, doctors, assignments, today):
    """Attempt one assignment. Never raises: it returns what happened.

    Returns a dictionary with 'outcome' of 'assigned' or 'refused'. A refusal
    carries the binding constraint AND what was still free at that moment,
    because "refused for a doctor while a room stood idle" is the actionable
    fact and a bare refusal count is not.
    """
    ref = case['case_ref']
    ward = case['ward']

    # --- Workflow refusals: not capacity evidence. -----------------------
    if ref in assignments:
        return _refused(case, 'duplicate', 'This case already holds a reservation.', 0, 0)
    if ward not in WARDS:
        return _refused(case, 'unknown_ward', f'{ward} is not a configured ward.', 0, 0)
    if case['appointment_date'] != today.isoformat():
        return _refused(case, 'not_today',
                        'Only cases dated today can reserve resources now.', 0, 0)

    # --- Capacity refusals: the measurement. -----------------------------
    open_rooms, open_doctors = free_resources(ward, rooms, doctors, assignments)

    if not open_rooms:
        return _refused(case, 'no_room', f'No free room in {ward}.',
                        len(open_rooms), len(open_doctors))
    if not open_doctors:
        return _refused(case, 'no_doctor', f'No free doctor for {ward}.',
                        len(open_rooms), len(open_doctors))

    # First-fit, in configuration order. Deterministic on purpose: it is what
    # makes the counterfactual replay in replay.py exact rather than modelled.
    chosen = {'room_id': open_rooms[0]['id'], 'doctor_id': open_doctors[0]['id']}
    assignments[ref] = chosen
    return {'outcome': 'assigned', 'case_ref': ref, 'ward': ward,
            'room_id': chosen['room_id'], 'doctor_id': chosen['doctor_id']}


def _refused(case, code, detail, rooms_free, doctors_free):
    """Build one refusal record. This is the object the project throws away."""
    return {
        'outcome': 'refused',
        'case_ref': case['case_ref'],
        'ward': case['ward'],
        'code': code,
        'detail': detail,
        'rooms_free': rooms_free,
        'doctors_free': doctors_free,
        'is_capacity': code in CAPACITY_CODES,
    }


def run_clinic(cases, rooms, doctors, today):
    """Process one day's cases in arrival order and return that day's ledger."""
    assignments = {}
    assigned, refusals, events = [], [], []
    for case in cases:
        result = try_assign(case, rooms, doctors, assignments, today)
        result['day'] = case['day']
        # events preserves arrival order. A case reference can legitimately
        # appear twice (assigned, then refused as a duplicate), so outcomes
        # must not be keyed by reference alone.
        events.append(result)
        if result['outcome'] == 'assigned':
            assigned.append(result)
        else:
            refusals.append(result)
    return {'assigned': assigned, 'refusals': refusals,
            'events': events, 'assignments': assignments}


def run_from_spec(cases, spec, today=None):
    """Run several clinic days against the same resource specification.

    Each day gets FRESH resources. This is the demo's stand-in for the
    completion/release lifecycle the project has not built yet: without it, a
    doctor reserved on Monday would still be busy on Friday, and every added
    resource could only ever absorb one case in total. Resetting per day lets a
    doctor serve one case per day, which is enough for the measurement to mean
    something. The real system needs release (roadmap lesson 5) for this to hold
    within a single day as well.
    """
    assigned, refusals, events = [], [], []
    for day in sorted({case['day'] for case in cases}):
        rooms, doctors = make_resources(spec)
        todays_cases = [case for case in cases if case['day'] == day]
        ledger = run_clinic(todays_cases, rooms, doctors, date.fromisoformat(day))
        assigned.extend(ledger['assigned'])
        refusals.extend(ledger['refusals'])
        events.extend(ledger['events'])
    return {'assigned': assigned, 'refusals': refusals, 'events': events}


def served_refs(ledger):
    """The set of case references that received a reservation."""
    return {item['case_ref'] for item in ledger['assigned']}


def capacity_refusals(ledger):
    """Only refusals caused by a missing resource.

    Mixing workflow refusals into this set would inflate unmet demand and make
    the number meaningless.
    """
    return [r for r in ledger['refusals'] if r['is_capacity']]
