"""Counterfactual capacity replay.

The ledger tells you what was refused and why. That is an observation. This turns
it into a recommendation: how many of those refusals would ONE more doctor, or
ONE more room, actually have absorbed?

Because assignment is deterministic first-fit, the recorded demand can be re-run
against a modified resource set and the answer is exact for that rule. It is not
a statistical estimate. An optimising or randomised scheduler could not make the
same claim honestly.
"""

from clinic import run_from_spec, served_refs, capacity_refusals


def counterfactual(cases, spec, ward, extra_rooms=0, extra_doctors=0, today=None):
    """Replay the same demand with extra resources added to one ward.

    Returns which cases the extra resources absorbed, and — as an honesty check —
    any case that was served before but is not served after.
    """
    base = run_from_spec(cases, spec, today)

    modified = dict(spec)
    rooms, doctors = spec[ward]
    modified[ward] = (rooms + extra_rooms, doctors + extra_doctors)
    alternative = run_from_spec(cases, modified, today)

    before, after = served_refs(base), served_refs(alternative)
    return {
        'ward': ward,
        'extra_rooms': extra_rooms,
        'extra_doctors': extra_doctors,
        'absorbed': sorted(after - before),
        # Should always be empty: adding a resource should never cost a case a
        # reservation it previously had. Reported rather than assumed, so that a
        # violation would be visible instead of silently swallowed.
        'lost': sorted(before - after),
        'served_before': len(before),
        'served_after': len(after),
        'capacity_refused_before': len(capacity_refusals(base)),
        'capacity_refused_after': len(capacity_refusals(alternative)),
    }


def replay_is_exact(cases, spec, today=None):
    """Replaying with UNCHANGED resources must reproduce the original run.

    If this were ever false, every counterfactual built on the same machinery
    would be untrustworthy, so it is checked rather than assumed.
    """
    first = run_from_spec(cases, spec, today)
    second = run_from_spec(cases, spec, today)
    same_served = served_refs(first) == served_refs(second)
    same_refusals = ([(r['case_ref'], r['code']) for r in first['refusals']] ==
                     [(r['case_ref'], r['code']) for r in second['refusals']])
    return same_served and same_refusals


def options(cases, spec, ward, today=None):
    """Compare the realistic procurement choices for one ward."""
    return [
        counterfactual(cases, spec, ward, extra_doctors=1, today=today),
        counterfactual(cases, spec, ward, extra_rooms=1, today=today),
        counterfactual(cases, spec, ward, extra_rooms=1, extra_doctors=1, today=today),
    ]
