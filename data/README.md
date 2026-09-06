# Simulated appointment history

`simulated_appointments.csv` contains 400 invented appointments, created by
`train_assignment.py --generate-demo` with random seed 42. There is no hospital
source and no patient information. Dates span August 1–25, 2026. Every date has
one record for each of four wards times two rooms times two doctors (16 rows).

Each pair has an invented typical duration in the generator's `pair_minutes`
dictionary. Independent Gaussian noise with standard deviation two minutes is
added, then durations are floored at five minutes and rounded to two decimals.
These deliberately learnable patterns demonstrate the software; they do not
establish which rooms/doctors would be faster in a hospital. The generator's
invented duration table is never used by the runtime assignment function.

Columns: unique simulated appointment ID, ISO date, ward, room ID, doctor ID,
completed duration in minutes, and the literal source label `simulated`.
Room/doctor combinations recur on later days, representing distinct invented
appointments. There are no repeated-patient identifiers to evaluate generalization
across patients. Earlier dates train the model; August 21 onward is held out.

From the project folder, `.\.venv\Scripts\python.exe train_assignment.py` trains
and evaluates the existing CSV and writes the JSON report. Add `--generate-demo`
only when creating a new copy without an existing CSV: exclusive file creation
intentionally refuses to overwrite your training-data experiments. The GUI trains
in memory on startup and does not write models or patient data to disk.

The demo assumes all configured rooms/doctors within a ward are suitable for its
cases. It has no appointment types, staffing shifts, treatment outcomes, patient
complexity, or causal evidence. Faster estimated duration must not be interpreted
as better care. Real deployment would need a revised dataset, constraints, and
independent evaluation.
