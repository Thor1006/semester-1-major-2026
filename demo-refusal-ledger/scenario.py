"""A fictional five-day clinic week, written so the result is worth looking at.

All patient details are fictional and no personal data appears anywhere: a case
reference, a ward, and a date are everything the measurement needs. That is the
privacy argument made concrete rather than asserted.

The three wards are deliberately shaped differently:

  General medicine  4 rooms, 2 doctors  -> doctors bind, rooms sit idle
  Pediatrics        1 room,  3 doctors  -> the room binds, doctors sit idle
  Orthopedics       2 rooms, 2 doctors  -> balanced, nothing is refused

A naive reading of "we keep turning patients away, we need more space" is wrong
for General medicine and right for Pediatrics. The ledger can tell them apart.
"""

DAYS = ['2026-09-01', '2026-09-02', '2026-09-03', '2026-09-04', '2026-09-05']

# {ward: (rooms, doctors)}
SPEC = {
    'General medicine': (4, 2),
    'Pediatrics': (1, 3),
    'Orthopedics': (2, 2),
}

# Cases presenting per ward, per day.
DEMAND = {
    'General medicine': 5,
    'Pediatrics': 3,
    'Orthopedics': 2,
}

SHORT = {'General medicine': 'GM', 'Pediatrics': 'PD', 'Orthopedics': 'OR'}


def build_cases():
    """Return the week's case list in arrival order."""
    cases = []
    for day_index, day in enumerate(DAYS, start=1):
        for ward, count in DEMAND.items():
            for number in range(1, count + 1):
                cases.append({
                    'case_ref': f'{SHORT[ward]}-{day_index}-{number}',
                    'ward': ward,
                    'day': day,
                    'appointment_date': day,
                })

        if day_index == 1:
            # Two workflow refusals, included to prove they are kept out of the
            # capacity count. Neither says anything about resources.
            cases.append({
                'case_ref': 'GM-1-1',          # already reserved earlier today
                'ward': 'General medicine',
                'day': day,
                'appointment_date': day,
            })
            cases.append({
                'case_ref': 'GM-1-next-week',  # a future appointment
                'ward': 'General medicine',
                'day': day,
                'appointment_date': '2026-09-14',
            })
    return cases
