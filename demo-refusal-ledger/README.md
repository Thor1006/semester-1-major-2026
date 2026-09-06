# Demo: refusal as evidence

A runnable demonstration of the proposal in [`../INNOVATION.md`](../INNOVATION.md).

**This is a prototype, not part of the lessons.** It imports nothing from the main
project, so Codex can keep editing `registration.py` and `assignment.py` without
breaking it, and it cannot affect the lessons. All data is fictional and simulated;
everything here demonstrates software behaviour, not clinical effectiveness.

## Run it

**Double-click `run-app.cmd`** for the Tkinter application, or **`run.cmd`** for the
console report. Same demonstration, two faces.

From a terminal, `run.ps1` takes switches:

```powershell
.\run.ps1              # the demonstration
.\run.ps1 -Test        # the checks only
.\run.ps1 -All         # checks first, then the demonstration
```

Either launcher works from any folder — it switches to its own directory so the
imports resolve — and finds a working Python for itself. It verifies a candidate
interpreter actually runs before using it, because a bare `python` on this machine
resolves to a manager with no configured runtime. If the checks fail, the
demonstration is skipped and the exit code is 1.

`run.cmd` exists because double-clicking a `.ps1` opens it in Notepad rather than
running it, and the execution policy usually blocks unsigned scripts. It passes its
arguments through, so `run.cmd -All` works too.

To bypass the launchers entirely:

```powershell
& 'C:\ProgramData\miniconda3\python.exe' demo.py
& 'C:\ProgramData\miniconda3\python.exe' -m unittest -v test_demo.py
```

## The application

Four tabs over the same data:

| Tab | Shows |
| --- | --- |
| Clinic and demand | Resource spinboxes, a form to present cases, and every outcome in arrival order |
| Refusal ledger | Every refusal kept, with its binding constraint and what sat idle |
| Unmet demand | Totals, and the grouping by ward and binding resource |
| Capacity replay | What one or two more rooms or doctors would have absorbed |

Press **Run the simulated week**, then raise General medicine's doctor spinbox by one
and watch unmet demand fall from 25 to 20. Raise its rooms instead and nothing moves.

The whole interface is a pure function of two things: the cases presented and the
resource specification. Every view is recomputed by replaying that demand from
scratch, so no view can drift out of agreement with another. That is affordable only
because assignment is deterministic - the same property that makes the counterfactual
exact.

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
| `ledger_app.py` | The Tkinter application: four tabs over the same data |
| `demo.py` | Prints the same findings as a console report |
| `test_demo.py` | 10 checks on the claims above |
| `run.ps1` | Launcher: finds Python, runs the app, the report, or the checks |
| `run-app.cmd` | Double-clickable: opens the application |
| `run.cmd` | Double-clickable: prints the console report |

## Honest limits

- Simulated data throughout. No real clinic is measured.
- Resources reset each morning, standing in for the session completion/release step
  the project has not built yet (roadmap lesson 5). Within a single day one doctor
  still serves exactly one case, so the absorbed counts are a floor, not a forecast.
  **Release is a prerequisite for this measurement to be realistic.**
- The counterfactual answers what *this deterministic rule* would have done, not what
  a real clinic would have done.
- Not modelled: clinical urgency, triage, time slots, sensing, persistence.
