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

Lesson 2 is runnable: enter patient name, medical history/information, appointment date, phone number, and destination ward. Medical information may be blank; the other fields are required. Registering generates a ticket, adds a row to the session queue, and shows the confirmation popup introduced by the user.

`Q0147` means `Q` + ward `01` + random suffix `47`. `Q0107` and `Q0142` can coexist: the ward prefix is shared and only full IDs are unique. Wards may have multiple rooms; this step does not assign rooms. The ward names/codes in `registration.py` are editable examples.

The app chooses among unused suffixes `00`–`99`, allowing 100 tickets per ward per running session. Different appointment dates do not reset that pool. A full pool produces a helpful error. Closing the app loses records and resets used IDs; there is no persistence, API transmission, room assignment, or scheduling yet. Use fictional patient details for this lesson.

## Run the current lesson

From PowerShell, these commands use the existing Python installation on this computer:

```powershell
Set-Location 'C:\Users\Thor1\Documents\Pattadon\Py-SPSM-Codex\preview-1-prime'
& 'C:\ProgramData\miniconda3\python.exe' app.py
```

No extra packages are required. On another computer with Python and Tkinter installed, run `python app.py` from this folder. The `python` command on this computer currently points to a manager without a configured runtime, so use the explicit path above.

Try two fictional registrations for General medicine: both IDs should begin `Q01`, with different two-digit suffixes. Invalid dates or missing required fields should leave the form available for correction and should not add a row. Name, phone, and information clear after success; ward and date remain selected.

The original lesson is preserved in `lessons/lesson_01.py`. Detailed teaching comments are in both current Python modules, and the walkthrough is in `LEARNING.md`.

Run the registration checks from this folder with:

```powershell
& 'C:\ProgramData\miniconda3\python.exe' -m unittest -v test_registration.py
```

For future Codex sessions, open this folder as the working project so its `AGENTS.md` is discovered at startup. If working from the parent workspace, explicitly read `preview-1-prime/AGENTS.md` before editing this project.
