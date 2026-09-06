"""Run the demonstration and print the report.

    python demo.py

Everything printed is derived from simulated demand. It demonstrates software
behaviour, not clinical or operational effectiveness.
"""

from collections import Counter

from clinic import CAPACITY_CODES, capacity_refusals, run_from_spec, served_refs
from replay import counterfactual, replay_is_exact
from scenario import DAYS, SPEC, build_cases

RULE = '=' * 76
THIN = '-' * 76


def heading(text):
    print(f'\n{RULE}\n{text}\n{RULE}')


def show_configuration():
    heading('1. THE CLINIC')
    print(f'{len(DAYS)} clinic days, {DAYS[0]} to {DAYS[-1]}.'
          '  Resources reset each morning.\n')
    print(f'  {"Ward":<20}{"Rooms":>7}{"Doctors":>9}   Shape')
    print(f'  {THIN[:56]}')
    for ward, (rooms, doctors) in SPEC.items():
        if rooms > doctors:
            shape = 'more rooms than doctors'
        elif doctors > rooms:
            shape = 'more doctors than rooms'
        else:
            shape = 'balanced'
        print(f'  {ward:<20}{rooms:>7}{doctors:>9}   {shape}')


def show_one_day(cases):
    """Trace a single day so the refusals are visible one at a time."""
    heading(f'2. ONE DAY IN DETAIL  ({DAYS[0]})')
    print('Every line below is a record the current project computes and then')
    print('discards. Note what is still free at the moment of each refusal.\n')

    day_one = [c for c in cases if c['day'] == DAYS[0]]
    ledger = run_from_spec(day_one, SPEC)

    print(f'  {"Case":<16}{"Ward":<19}{"Outcome":<14}Detail')
    print(f'  {THIN[:72]}')
    # events is in arrival order, one entry per case, so a reference that
    # appears twice is shown twice with its real outcome each time.
    for case, item in zip(day_one, ledger['events']):
        if item['outcome'] == 'assigned':
            detail = f'{item["room_id"]} + {item["doctor_id"]}'
            print(f'  {case["case_ref"]:<16}{case["ward"]:<19}{"assigned":<14}{detail}')
        else:
            tag = item['code'] if item['is_capacity'] else f'{item["code"]} *'
            if item['is_capacity']:
                detail = (f'{item["rooms_free"]} room(s) and '
                          f'{item["doctors_free"]} doctor(s) still free')
            else:
                detail = item['detail']
            print(f'  {case["case_ref"]:<16}{case["ward"]:<19}{tag:<14}{detail}')
    print('\n  * workflow refusal: excluded from the capacity measurement.')


def show_ledger(cases):
    heading('3. THE WEEK, SUMMARISED')
    ledger = run_from_spec(cases, SPEC)
    capacity = capacity_refusals(ledger)
    workflow = [r for r in ledger['refusals'] if not r['is_capacity']]

    print(f'  Cases presented      {len(cases):>3}')
    print(f'  Reservations made    {len(ledger["assigned"]):>3}')
    print(f'  Capacity refusals    {len(capacity):>3}   <- unmet demand')
    print(f'  Workflow refusals    {len(workflow):>3}   <- NOT unmet demand')

    print('\n  Unmet demand by ward and binding constraint:\n')
    print(f'  {"Ward":<20}{"Constraint":<14}{"Cases":>7}   While idle')
    print(f'  {THIN[:66]}')
    grouped = Counter((r['ward'], r['code']) for r in capacity)
    for (ward, code), count in sorted(grouped.items()):
        example = next(r for r in capacity if r['ward'] == ward and r['code'] == code)
        idle = f'{example["rooms_free"]} room(s), {example["doctors_free"]} doctor(s)'
        print(f'  {ward:<20}{code:<14}{count:>7}   {idle}')

    print('\n  Read the last column. General medicine turned cases away while')
    print('  rooms stood empty; Pediatrics turned them away while doctors did.')


def show_counterfactual(cases):
    heading('4. WHAT WOULD ONE MORE RESOURCE HAVE ABSORBED?')
    print('The same recorded demand, replayed against modified resources.')
    print('First-fit is deterministic, so this is exact for that rule, not an')
    print('estimate.\n')

    print(f'  {"Ward":<20}{"Change":<16}{"Absorbed":>10}{"Lost":>7}')
    print(f'  {THIN[:56]}')
    for ward in ('General medicine', 'Pediatrics'):
        refused = len([r for r in capacity_refusals(run_from_spec(cases, SPEC))
                       if r['ward'] == ward])
        for label, kwargs in (('+1 doctor', {'extra_doctors': 1}),
                              ('+1 room', {'extra_rooms': 1}),
                              ('+1 of each', {'extra_rooms': 1, 'extra_doctors': 1})):
            result = counterfactual(cases, SPEC, ward, **kwargs)
            absorbed = f'{len(result["absorbed"])} of {refused}'
            print(f'  {ward:<20}{label:<16}{absorbed:>10}{len(result["lost"]):>7}')
        print()

    print('  This is the finding. In General medicine an extra ROOM absorbs')
    print('  nothing at all, because rooms were never the constraint. Buying')
    print('  space there would have been money spent on an idle room.')


def show_integrity(cases):
    heading('5. INTEGRITY CHECKS')
    exact = replay_is_exact(cases, SPEC)
    print(f'  Replay with unchanged resources reproduces the original run: {exact}')

    worst = None
    for ward in SPEC:
        for kwargs in ({'extra_doctors': 1}, {'extra_rooms': 1},
                       {'extra_rooms': 1, 'extra_doctors': 1}):
            result = counterfactual(cases, SPEC, ward, **kwargs)
            if result['lost']:
                worst = (ward, kwargs, result['lost'])
    print(f'  Adding a resource never cost a case its reservation:          '
          f'{worst is None}')
    if worst:
        print(f'    VIOLATION: {worst}')


def show_limits():
    heading('6. WHAT THIS DOES NOT SHOW')
    print('  - The data is simulated. Nothing here measures a real clinic.')
    print('  - Resources reset each morning because the project has no session')
    print('    completion or release yet. Within a single day one doctor still')
    print('    serves exactly one case, so these numbers are a floor, not a')
    print('    forecast. Release (roadmap lesson 5) is a prerequisite for the')
    print('    measurement to be realistic.')
    print('  - The counterfactual answers what THIS deterministic rule would')
    print('    have done, not what a real clinic would have done.')
    print('  - No clinical urgency, no triage, no diagnosis.')


def main():
    cases = build_cases()
    print('\nREFUSAL AS EVIDENCE - a demonstration of INNOVATION.md')
    print('Simulated data. Demonstrates software behaviour only.')
    show_configuration()
    show_one_day(cases)
    show_ledger(cases)
    show_counterfactual(cases)
    show_integrity(cases)
    show_limits()
    print()


if __name__ == '__main__':
    main()
