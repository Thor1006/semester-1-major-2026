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

Lesson 3 is runnable with ML assignment. Registration accepts patient name, optional medical information, appointment date, phone, and destination ward. Select a case dated today and click **Assign using ML**. The app filters compatible, available resources, predicts the duration for each room/doctor pair with a small decision tree, and reserves the pair with the shortest estimate. Candidate estimates and their source appear below the button; the **Rooms and doctors** tab reflects reservations.

`Q0147` means `Q` + ward `01` + random suffix `47`. `Q0107` and `Q0142` can coexist. Each example ward has two rooms and two doctors; their IDs, such as `R01-1` and `D01-1`, are separate from queue IDs. The ward names/codes in `registration.py` are editable examples.

The app chooses among unused suffixes `00`–`99`, allowing 100 tickets per ward per running session. Different appointment dates do not reset that pool. A full pool produces a helpful error. Closing the app loses records and reservations and resets used IDs. Use fictional patient details for this lesson.

These are immediate reservations for today; future time-slot scheduling, shifts, completion/release, persistence, clinical priority, and hardware are later work. Reservations remain until the app closes, even after the estimated minutes pass. The same ticket cannot be assigned twice, but there is no permanent patient identity to detect two registrations belonging to the same person. Staff choose the case; the random ticket does not establish priority.

The 400 included historical rows are entirely simulated. The model trains on the first 320 and evaluates on the later 80, with no refitting on test rows. It uses only ward, room ID, and doctor ID. It cannot personalize duration from patient history or determine clinical suitability. Lower predicted duration is a teaching objective, not a validated measure of care quality or a globally optimal schedule. Equal predictions are resolved by room ID then doctor ID. An unseen pair uses the training ward median (global median for an unknown ward), labelled as a fallback. Missing data or dependencies enable an explicitly labelled first-available fallback with no numerical estimate.

## Run the current lesson

From PowerShell, these commands use the existing Python installation on this computer:

```powershell
Set-Location 'C:\Users\Thor1\Documents\Pattadon\Py-SPSM-Codex\preview-1-prime'
.\.venv\Scripts\python.exe app.py
```

The project virtual environment already contains scikit-learn. For a fresh setup with Python and Tkinter installed, create a virtual environment and install the pinned dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

On this computer, if `python` points to an unconfigured manager, use `& 'C:\ProgramData\miniconda3\python.exe' -m venv .venv` for the creation step. The app trains the small model before opening the window; restarting loads changes to the CSV. No internet is used when running the app. Earlier lessons do not require scikit-learn.

Try two fictional registrations for General medicine: both IDs should begin `Q01`, with different two-digit suffixes. Invalid dates or missing required fields should leave the form available for correction and should not add a row. Name, phone, and information clear after success; ward and date remain selected.

For lesson 3, register three fictional cases in General medicine with today's date. Assign them in registration order: with the included data, the first gets R01-2 / D01-2, the second gets R01-1 / D01-1, and the third remains Waiting with a reason. Inspect the four candidate estimates after the first assignment and the resource tab's four reservations after the second. Clicking an already-assigned case must not take another pair.

Earlier lessons are preserved in `lessons/lesson_01.py` and `lessons/lesson_02/`. Run the lesson 2 snapshot with `& 'C:\ProgramData\miniconda3\python.exe' lessons/lesson_02/app.py`. Detailed comments are in the current modules; lesson 3's walkthrough is in `LEARNING.md`.

Run the registration and assignment checks from this folder with:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_registration.py test_assignment.py test_duration_model.py
.\.venv\Scripts\python.exe train_assignment.py
```

The training command prints measured errors and writes `artifacts/assignment_evaluation.json`. The included run measured 1.96 minutes mean absolute error for the tree and 5.74 for the ward-median baseline, on simulated data only. Generation instructions and assumptions are in `data/README.md`; the detailed teaching walkthrough is the ML extension at the end of `LEARNING.md`.

For future Codex sessions, open this folder as the working project so its `AGENTS.md` is discovered at startup. If working from the parent workspace, explicitly read `preview-1-prime/AGENTS.md` before editing this project.
