# Outpatient scheduling assistant

A student project using **Tkinter, machine learning, and ESP32** to explore better coordination of outpatient queues, doctors, and rooms.

## Project documents

- `AGENTS.md`: project instructions for Codex, including scope, architecture, scheduling rules, ML evaluation, hardware behavior, and privacy boundaries.
- `Proposal.md`: an unchanged copy of the original proposal at project creation.
- `LEARNING.md`: step-by-step learning roadmap, lesson progress, and independent rebuild exercises.
- `HANDOFF.md`: shared newest-first session log for Codex and Claude Code.

## Working direction

Start with one department: staff enter fictional cases, assign clinical urgency, and use the app to find compatible doctor and room slots. Add appointment-duration prediction and staff-confirmed ESP32 room updates after the core scheduler works. A general FAQ assistant is an optional later extension.

The original proposal is broader than this first version. `AGENTS.md` records the proposed implementation defaults so they can be refined during development.

## Status

Lesson 3 is runnable. Registration still accepts patient name, optional medical information, appointment date, phone, and destination ward. After registration, select a case dated today and click **Assign selected case**. The app reserves the first available room in that ward and first available doctor supporting it, and updates the **Rooms and doctors** tab.

`Q0147` means `Q` + ward `01` + random suffix `47`. `Q0107` and `Q0142` can coexist. Each example ward has two rooms and two doctors; their IDs, such as `R01-1` and `D01-1`, are separate from queue IDs. The ward names/codes in `registration.py` are editable examples.

The app chooses among unused suffixes `00`–`99`, allowing 100 tickets per ward per running session. Different appointment dates do not reset that pool. A full pool produces a helpful error. Closing the app loses records and reservations and resets used IDs. Use fictional patient details for this lesson.

These are immediate reservations for today; future time-slot scheduling, shifts, completion/release, persistence, clinical priority, ML, and hardware are later work. Reservations remain until the app closes. The same ticket cannot be assigned twice, but there is no permanent patient identity to detect two registrations belonging to the same person. Staff choose the case; the random ticket does not establish priority.

## Run the current lesson

From PowerShell, these commands use the existing Python installation on this computer:

```powershell
Set-Location 'C:\Users\Thor1\Documents\Pattadon\Py-SPSM-Codex\preview-1-prime'
& 'C:\ProgramData\miniconda3\python.exe' app.py
```

No extra packages are required. On another computer with Python and Tkinter installed, run `python app.py` from this folder. The `python` command on this computer currently points to a manager without a configured runtime, so use the explicit path above.

Try two fictional registrations for General medicine: both IDs should begin `Q01`, with different two-digit suffixes. Invalid dates or missing required fields should leave the form available for correction and should not add a row. Name, phone, and information clear after success; ward and date remain selected.

For lesson 3, register three fictional cases in General medicine with today's date. Assign them in registration order: the first two get different rooms/doctors and the third remains Waiting with a reason. Inspect the resource tab to see four reserved resources. Clicking an already-assigned case must not take another pair.

Earlier lessons are preserved in `lessons/lesson_01.py` and `lessons/lesson_02/`. Run the lesson 2 snapshot with `& 'C:\ProgramData\miniconda3\python.exe' lessons/lesson_02/app.py`. Detailed comments are in the current modules; lesson 3's walkthrough is in `LEARNING.md`.

Run the registration and assignment checks from this folder with:

```powershell
& 'C:\ProgramData\miniconda3\python.exe' -m unittest -v test_registration.py test_assignment.py
```

For future Codex sessions, open this folder as the working project so its `AGENTS.md` is discovered at startup. If working from the parent workspace, explicitly read `preview-1-prime/AGENTS.md` before editing this project.
