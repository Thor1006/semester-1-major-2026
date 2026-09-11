# Outpatient scheduling assistant

A student project using **Tkinter** and **ESP32** to explore better coordination of outpatient queues, doctors, and rooms.

## Project documents

- `AGENTS.md`: project instructions for Codex, including scope, architecture, scheduling rules, hardware behavior, and privacy boundaries.
- `Proposal.md`: an unchanged copy of the original proposal at project creation.
- `LEARNING.md`: step-by-step learning roadmap, lesson progress, and independent rebuild exercises.
- `HANDOFF.md`: shared newest-first session log for Codex and Claude Code.
- `presentation/slides.html`: a presentation deck for the project, in Thai. Open it in a browser and use the arrow keys; print it to save a PDF with one slide per page.

## Working direction

Start with one department: staff enter fictional cases, assign clinical urgency, and use the app to find compatible doctor and room slots. Add staff-confirmed ESP32 room updates after the core scheduler works. A general FAQ assistant is an optional later extension.

The original proposal is broader than this first version. `AGENTS.md` records the proposed implementation defaults so they can be refined during development.

## Status

Registrations are now saved. Closing the app and reopening it restores the queue from a local SQLite file, `clinic.db`, created beside the source on first run.

Registration accepts patient name, optional medical information, appointment date, phone, and destination ward. Select a case dated today and click **Assign selected case**. The app filters for a compatible, available room and doctor and reserves the first of each in configured order; the **Rooms and doctors** tab reflects reservations.

**Reservations are not saved, only registrations.** Nothing in the project can end a reservation yet, so a restored one would hold a room with no way to free it. Every case therefore comes back as Waiting. The database file stays on this computer, is excluded from version control, and is never transmitted anywhere.

### Assigning cases

Three buttons sit under the queue table:

- **Assign selected** takes the first compatible free room and doctor, in configured order.
- **Choose room/doctor...** opens a chooser listing only the rooms and doctors that are actually available for that case's ward, so you can pick a specific pair. The rules still apply: you can override which pair is used, not whether it is legal.
- **Auto-assign all** serves every waiting case dated today in **arrival order** - first come, first served - and reports how many were assigned and why the first blocked case could not be.
- **Mark done** finishes a visit. The confirmation names the room and doctor that will be freed, and once done they are immediately available to the next patient.

Arrival order means the order cases were registered, which is the order the queue table shows and the order they are reloaded from the database. **The random part of a ticket is not a position**: `Q0199` may well have arrived before `Q0102`.

Auto-assign fills gaps; it never reshuffles work already done. A pair you chose by hand stays exactly as you set it, and a full ward does not stop a different ward being served.

### Finished cases

**Mark done** is how a visit ends. It releases the room and doctor so the next patient can have them, and records when the case finished.

The case is **archived, not deleted**: it stays in the database, disappears from the working queue, and comes back with the **Show completed cases** checkbox, where it shows as `Done`. Its details window records the finishing time.

There is no reopen. By the time you notice a mistake the freed room may already belong to somebody else, so restoring the old reservation could double-book it. The confirmation therefore names what is about to be freed before anything happens.

### Changing capacity

The **Rooms and doctors** tab configures how many rooms and doctors each ward has. Choose a ward, set the two numbers, and click **Apply**. The change is saved, so it survives a restart. Every ward starts with two of each.

Growing a ward is always safe: resources are numbered by position, so adding a third room creates `R01-3` and leaves `R01-1` and `R01-2` exactly as they were. Reducing removes from the end.

**A reduction that would delete a reserved room or doctor is refused**, naming the resources in use. Deal with those cases first. Silently dropping a reservation would leave a patient unassigned with nothing on screen to say so.

The same tab takes an individual room or doctor **out of service** for maintenance. An out-of-service resource is never assigned, shows as Unavailable, and stays that way after a restart. A resource that is currently reserved cannot be taken out of service.

### Managing saved data

Four controls sit under the queue table:

- **Details**, or double-click a row, opens everything stored about that patient, including the medical information the queue table deliberately hides.
- **Delete** removes the selected registration after naming the patient in the confirmation. Any room and doctor it was holding are released.
- **Import CSV...** adds many registrations from a spreadsheet export.
- **Clear all** empties the saved queue, behind two confirmations.

The import file needs this header, and `sample_import.csv` is a working example:

```
patient_name,medical_information,appointment_date,phone_number,destination_ward
```

`medical_information` may be blank on any row, but the column must be present. Queue IDs are **not** imported: each row is validated exactly like a typed registration and given a generated ticket. **Import is all or nothing.** If any row is invalid, nothing is written and every problem is listed with the row number as your spreadsheet shows it, so you fix the file once rather than discovering one error per attempt.

`Q0147` means `Q` + ward `01` + random suffix `47`. `Q0107` and `Q0142` can coexist. Each example ward has two rooms and two doctors; their IDs, such as `R01-1` and `D01-1`, are separate from queue IDs. The ward names/codes in `registration.py` are editable examples.

The app chooses among unused suffixes `00`–`99`, allowing 100 tickets per ward per appointment date. Each date has its own pool, so a busy day cannot use up tomorrow's tickets. A full pool produces a helpful error naming the date. Because the pool is per date, the same ticket can appear again on a different day: `Q0147` on the 8th and `Q0147` on the 9th are different patients, and the date plus the ticket is what identifies a registration. Closing the app now keeps registrations but still clears reservations. Use fictional patient details: they are written to a real file on disk. Deleting `clinic.db` resets the project to an empty queue.

These are immediate reservations for today; future time-slot scheduling, shifts, completion/release, persistence, clinical priority, and hardware are later work. Reservations remain until the app closes. The same ticket cannot be assigned twice, but there is no permanent patient identity to detect two registrations belonging to the same person. Staff choose the case; the random ticket does not establish priority.

Assignment is deliberately simple and deterministic: the first compatible free room and the first compatible free doctor, in the order they are configured. The same waiting list therefore always produces the same reservations. This is not a claim that the pairing is the best possible one; choosing among feasible pairs would need a stated goal, which the project has not defined.

## Run the current lesson

From PowerShell, these commands use the existing Python installation on this computer:

```powershell
Set-Location 'C:\Users\Thor1\Documents\Pattadon\Py-SPSM-Codex\preview-1-prime'
& 'C:\ProgramData\miniconda3\python.exe' app.py
```

No extra packages are required: the app uses only the Python standard library and Tkinter, and no internet connection. On another computer with Python and Tkinter installed, run `python app.py` from this folder. The `python` command on this computer points to a manager without a configured runtime, so use the explicit path above. The leftover `.venv` folder is no longer used by anything.

Try two fictional registrations for General medicine: both IDs should begin `Q01`, with different two-digit suffixes. Invalid dates or missing required fields should leave the form available for correction and should not add a row. Name, phone, and information clear after success; ward and date remain selected.

For lesson 3, register three fictional cases in General medicine with today's date. Assign them in registration order: the first gets R01-1 / D01-1, the second gets R01-2 / D01-2, and the third remains Waiting with a reason. The resource tab should then show four reservations. Clicking an already-assigned case must not take another pair.

Earlier lessons are preserved in `lessons/lesson_01.py` and `lessons/lesson_02/`. Run the lesson 2 snapshot with `& 'C:\ProgramData\miniconda3\python.exe' lessons/lesson_02/app.py`. Detailed comments are in the current modules; lesson 3's walkthrough is in `LEARNING.md`.

Run the registration and assignment checks from this folder with:

```powershell
& 'C:\ProgramData\miniconda3\python.exe' -m unittest -v test_registration.py test_assignment.py test_storage.py test_bulk_import.py test_capacity.py test_assignment_modes.py test_lifecycle.py
```

That runs 110 checks covering registration, queue IDs, assignment, saving, deleting, CSV import, capacity, the manual and automatic assignment modes, completion, and the database migration. The checks use temporary files, so running them never touches your saved queue. The detailed teaching walkthroughs are in `LEARNING.md`.

For future Codex sessions, open this folder as the working project so its `AGENTS.md` is discovered at startup. If working from the parent workspace, explicitly read `preview-1-prime/AGENTS.md` before editing this project.
