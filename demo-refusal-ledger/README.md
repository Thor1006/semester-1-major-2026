# Demo: refusal as evidence

A runnable demonstration of the proposal in [`../INNOVATION.md`](../INNOVATION.md).

**This is a prototype, not part of the lessons.** It imports nothing from the main
project, so Codex can keep editing `registration.py` and `assignment.py` without
breaking it, and it cannot affect the lessons. All data is fictional and simulated;
everything here demonstrates software behaviour, not clinical effectiveness.

## Run it

```powershell
Set-Location 'C:\Users\Thor1\Documents\Pattadon\Py-SPSM-Codex\preview-1-prime\demo-refusal-ledger'
& 'C:\ProgramData\miniconda3\python.exe' demo.py
```

Checks:

```powershell
& 'C:\ProgramData\miniconda3\python.exe' -m unittest -v test_demo.py
```

## The one line that matters

The project's `assignment.py` does this when it cannot place a case:

```python
raise ValueError(f'No available doctor for {ward}. The case stays waiting.')
```

It has just worked out the binding constraint — and it throws it away. This demo
returns a record instead:

```python
{'code': 'no_doctor', 'ward': 'General medicine',
 'rooms_free': 2, 'doctors_free': 0, 'is_capacity': True}
```

`rooms_free: 2` is the whole argument. The ward turned patients away **while two
rooms sat empty**.

## What the demo shows

Three wards shaped differently on purpose, over five clinic days:

| Ward | Rooms | Doctors | Result |
| --- | --- | --- | --- |
| General medicine | 4 | 2 | 15 refusals, all doctor-bound, 2 rooms idle each time |
| Pediatrics | 1 | 3 | 10 refusals, all room-bound, 2 doctors idle each time |
| Orthopedics | 2 | 2 | nothing refused |

Replaying the same demand against modified resources:

| Ward | Change | Absorbed |
| --- | --- | --- |
| General medicine | +1 doctor | 5 of 15 |
| General medicine | **+1 room** | **0 of 15** |
| Pediatrics | +1 doctor | 0 of 10 |
| Pediatrics | +1 room | 5 of 10 |

An extra room in General medicine absorbs **nothing**, because rooms were never the
constraint there. "We keep turning patients away, we need more space" is wrong for
one ward and right for the other, and only the ledger can tell them apart.

## Why the counterfactual is exact

First-fit assignment is deterministic, so recorded demand replayed against a changed
resource set reproduces exactly what that rule would have done. It is not a
statistical estimate. `test_demo.py` checks this directly: replaying with *unchanged*
resources must reproduce the original run, and adding a resource must never cost a
case a reservation it previously had. Both are asserted rather than assumed.

## Files

| File | Purpose |
| --- | --- |
| `clinic.py` | Resources, first-fit assignment, and the refusal records |
| `replay.py` | Counterfactual capacity replay |
| `scenario.py` | The fictional five-day demand |
| `demo.py` | Prints the report |
| `test_demo.py` | 10 checks on the claims above |

## Honest limits

- Simulated data throughout. No real clinic is measured.
- Resources reset each morning, standing in for the session completion/release step
  the project has not built yet (roadmap lesson 5). Within a single day one doctor
  still serves exactly one case, so the absorbed counts are a floor, not a forecast.
  **Release is a prerequisite for this measurement to be realistic.**
- The counterfactual answers what *this deterministic rule* would have done, not what
  a real clinic would have done.
- Not modelled: clinical urgency, triage, time slots, sensing, persistence.
