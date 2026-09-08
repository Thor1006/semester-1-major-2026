# Handoff between agents

A shared coordination file for the assistants working on this project (Claude Code and
Codex). It records **how the two hand work back and forth**, not the project's rules.
The rules stay in `AGENTS.md`; this file must never restate or override them.

## Which file owns what

Keeping each fact in exactly one place is what prevents the two assistants from
starting a session with different pictures of the project.

| File | Owns | Do not put here |
| --- | --- | --- |
| `AGENTS.md` | Durable project rules: scope, teaching method, scheduling constraints, ML and hardware boundaries, privacy limits. Coarse feature status in *Current state*. | Session-by-session narration. |
| `LEARNING.md` | Lesson roadmap, lesson-by-lesson progress, teaching notes, exercises, common mistakes. | Project rules. |
| `README.md` | What a newcomer runs and what currently works, with verified commands. | Planned features described as working. |
| `HANDOFF.md` (this file) | The handoff protocol and an append-only log of what each session changed. | Any fact the files above already own. |

When these disagree, `AGENTS.md` wins on rules and `LEARNING.md` wins on lesson progress.
Fix the disagreement in the owning file rather than adding a correction here.

## Start of a session

1. Read `AGENTS.md` in full. Codex loads it automatically; Claude Code loads it through
   the `@AGENTS.md` import in `CLAUDE.md`.
2. Read the latest entry in the session log below to see what the other assistant last did
   and what it deliberately left alone.
3. Read `LEARNING.md` *Current progress* before proposing the next lesson. Do not advance
   past a lesson whose independent practice is still pending unless the user says to.
4. Verify claims against the code before repeating them. An entry below describes what was
   true when written, not necessarily what is true now.

## End of a session

Before reporting work as finished:

- [ ] Ran the change and observed the actual behavior, not only reasoned about it.
- [ ] Updated `LEARNING.md` if a lesson advanced or an exercise was completed.
- [ ] Updated `README.md` status and run commands if either changed, and `AGENTS.md`
      *Current state* if a feature genuinely became working.
- [ ] Added a session log entry below.
- [ ] Committed the change. The repository is local only; there is no remote,
      so nothing is published by committing.
- [ ] Stated plainly what was left unfinished or unverified.

Whoever lands a change updates these in the same turn. A change that ships without its
record is the main way the two assistants drift apart.

## Open threads

- Lesson 3 room/doctor reservation is implemented and checked. User practice is pending;
  see `LEARNING.md` for the exercise and next increment.
- Lesson 3 now includes ML pair ranking with explicitly simulated history; the
  user's ML practice remains pending. No hardware or external AI call is verified.

## Session log

Newest first. One short entry per session: what changed, what was verified, what was not.

### 2026-09-08 - Claude Code (Opus 5) - Configurable capacity

- The user asked for a way to change the capacity of the whole system. Rooms and doctors
  per ward are now configurable from the Rooms and doctors tab and saved between runs.
- `make_demo_resources(capacity, disabled)` replaces the hard-coded `range(1, 3)`. Wards
  absent from the mapping use `DEFAULT_CAPACITY`, so a ward added to `WARD_CODES` later
  gets resources rather than none. Passing nothing still yields the original two-and-two,
  so existing callers and tests are unaffected.
- `blocking_reservations` is the safety rule: reducing capacity removes resources from the
  END of the numbering, and the change is refused, by name, if any of them is reserved.
  Same rule blocks taking a reserved resource out of service. Silently dropping a
  reservation would leave a patient unassigned with nothing on screen to say so.
- Resource IDs are positional (`R01-3` is the third room), so growing a ward never renames
  an existing resource and existing reservations stay valid.
- Out-of-service resources are stored in their own table, NOT as a smaller capacity number,
  so a room under maintenance keeps its ID instead of it being reused by the next room.
- `rebuild_resources` uses `rooms[:] = ...` rather than rebinding: `assign_patient` holds
  the same list objects, so a rebind would leave it working from the old lists.
- Updated an assertion I had written earlier that the database contained only a
  `registrations` table. Three tables are now correct; the check still proves reservations
  are not persisted.
- Verified: 74 tests pass (20 new in `test_capacity.py`). The editor was also driven
  through the real widgets across two processes: growing a ward let a third case be served,
  shrinking onto reserved resources was refused and left the rooms intact, shrinking past
  only free resources worked, non-numeric and out-of-range input were rejected, taking a
  free room out of service made assignment skip it, re-enabling restored it, and both
  capacity and out-of-service state survived a restart. Window bounds re-measured at
  969x664; fits 1220x750 and 1160x720.
- NOTE: the user had two `app.py` instances running from `.venv` during this session, which
  is what created `clinic.db` in the project folder. Two instances share one database file
  but keep separate in-memory queues, so they will not see each other's registrations until
  restarted. The UNIQUE constraint still prevents a genuine duplicate.
- Not built: opening hours, shifts, part-time doctors, per-session capacity, removing or
  renaming a ward from the interface. A doctor still supports exactly one ward even though
  the structure holds a list.

### 2026-09-08 - Claude Code (Opus 5) - Import, delete and a details window

- The user asked for bulk import, a way to delete data, and a popup showing a queue entry's
  information. All three are built.
- New `bulk_import.py` reads a CSV and returns records. No Tkinter, no database: it is
  testable on its own. ALL OR NOTHING - every row is validated before anything is written,
  one bad row refuses the whole file, and problems are numbered as a spreadsheet shows them
  (header is row 1). Tickets are generated, never read from the file. `sample_import.csv`
  is a working example and is covered by a test, so it cannot rot.
- `storage.py` gains `save_many` (one transaction, rolls back entirely on failure),
  `delete_registration` (requires BOTH halves of the key) and `delete_all_registrations`.
- `app.py` gains Details / Delete / Import CSV... / Clear all under the queue table, plus a
  `<Double-1>` binding. Details is on double-click because single click selects, and
  selecting is how a case is chosen for assignment or deletion.
- Deleting releases any room and doctor the case held, conditional on the record being
  today's. `assignments` is keyed by ticket alone, which is only safe because just today's
  cases can hold one; without the date check, deleting another date's identical ticket
  would free today's reservation. This is a trap the date-scoped tickets introduced.
- Fixed a stale claim: the instructions label still said records stay in memory until the
  window closes, which persistence made untrue.
- Verified: 54 tests pass. The three features were also driven through the real widgets with
  the dialogs mocked - import added 3 rows to table and database, a file with one bad row
  changed nothing, cancelling did nothing, the details window showed name/phone/notes/pair
  with a read-only notes box, a declined delete kept the record, an accepted delete removed
  it from all three places and freed its two resources, and Clear all emptied everything.
  Window bounds re-measured: 969x664, fits 1220x750 and 1160x720.
- The test suite was re-checked for database pollution: no `clinic.db` is created by it.
- Not built: export, editing a saved registration, import preview or update-existing, undo,
  or any archive of deleted records. Deleting is immediate and permanent.

### 2026-09-08 - Claude Code (Opus 5) - Persistence built (lesson 6)

- The user asked to build persistence. Added `storage.py` (SQLite) and `test_storage.py`,
  and wired `app.py` to load at startup and save on each registration.
- REGISTRATIONS ONLY are saved, by the user's decision. Reservations stay in memory because
  no release/completion step exists (roadmap lesson 5); a restored reservation would hold a
  room that nothing could free. Loaded cases come back as Waiting and the startup label says
  reservations are not restored. **Do not add reservation persistence before lesson 5.**
- The table enforces `UNIQUE (appointment_date, queue_id)`, so the date-scoped ticket rule is
  enforced by the database and not only by the ID generator. `row_id INTEGER PRIMARY KEY`
  preserves arrival order, which date+ticket cannot express.
- Fixed a latent bug the date scoping had created: the queue table used the ticket as its
  Tkinter row id, which would break as soon as a ticket recurred on another date. `app.py`
  now has `row_key(record)` returning `date|ticket`, used for insert, lookup and selection.
- Found and fixed test pollution: importing `app` opens the database, so the interface test
  was writing test patients into the real `clinic.db`. It now points
  `storage.DATABASE_PATH` at a temporary file before importing `app`, and cleans it up. The
  same test was registering on a fixed date and rewriting `appointment_date` afterwards,
  which would have invalidated a row key; it now registers with today's date directly.
- Verified: 30 tests pass. A two-process restart check registered two patients and made one
  reservation, then a genuinely separate process restored both patients in order with zero
  reservations and every cell Waiting. Starting with no database file works and creates it.
  `git check-ignore` confirms `clinic.db` is excluded from version control.
- Built ahead of lessons 4 and 5 at the user's request. Time-slot scheduling and the release
  lifecycle are still missing, there is no way to edit or delete a saved registration from
  the app, and there are no migrations - changing `SCHEMA` requires deleting `clinic.db`.
  The lesson 6 walkthrough in `LEARNING.md` covers that trap and sets the practice exercise.

### 2026-09-08 - Claude Code (Opus 5) - Ticket pool scoped to a date

- Preparation for persistence, at the user's request. Building persistence first would have
  been a trap: ticket uniqueness was checked against every record in memory, so once records
  survived a restart, "100 per ward per session" would silently have become "100 per ward
  ever". Confirmed by running it before changing anything.
- `create_patient_record` now derives the used-ticket set only from records sharing the same
  appointment date, and the full-pool error names the date instead of "this session".
- The user chose this scoping over widening the suffix or adding a visible date prefix, so
  the staff-facing `QWWRR` format is unchanged.
- CONSEQUENCE FOR WHOEVER BUILDS PERSISTENCE: a ticket is no longer unique on its own.
  `Q0147` may recur on another date. The primary key must be appointment date + ticket.
  This is recorded in `AGENTS.md`, `README.md`, `LEARNING.md` and in the code comments.
- The user also chose that the first persistence increment saves REGISTRATIONS ONLY.
  Reservations stay in memory, because a saved reservation would hold a room with no
  release lifecycle (roadmap lesson 5) able to free it.
- Verified: 18 tests pass, including two new ones covering a full ward on one date still
  accepting the next date, and the same ticket legitimately recurring on a different date.
  An end-to-end run issued 100 tickets for 8 Sept, refused the 101st, and issued one for
  9 Sept.
- Persistence itself is NOT implemented. No database, schema, or file exists yet.

### 2026-09-08 - Claude Code (Opus 5) - Machine learning removed

- The user asked for the machine-learning part to be cut out. Deleted `duration_model.py`,
  `train_assignment.py`, `test_duration_model.py`, the simulated `data/` history,
  `artifacts/`, and the scikit-learn `requirements.txt`.
- `assignment.py`: `assign_patient` lost its `model` parameter, the scoring loops, and the
  `estimate_duration`/`math` imports. It now takes the first compatible free room and
  doctor in configured order and returns only `room_id` and `doctor_id`.
- `app.py`: no longer imports or loads a model. The button reads "Assign selected case"
  again and the message states the rule instead of candidate estimates.
- `AGENTS.md` *Current state* records the removal and says NOT to re-add duration
  prediction or a scikit-learn dependency without the user explicitly asking. The
  *Machine learning* rules section was left in place as guidance if it ever returns; the
  user has not said whether ML is out of scope permanently.
- `README.md` and `LEARNING.md` lost their ML status, setup, commands and walkthrough.
  Three stale claims in the surviving lesson 3 notes were corrected: the roadmap row, a
  pointer to the deleted ML section, and a description of `room = None`/`break` that no
  longer matched the code.
- Verified: 16 tests pass under the base interpreter with no virtual environment; `app.py`
  imports, builds its window and exposes the new button text; the lesson 3 trace table was
  re-checked against a live run and still matches (R01-1/D01-1, then R01-2/D01-2, third
  waits).
- `.venv` was left on disk. Nothing uses it now; it is the user's to delete.
- Recoverable from git history if ML is ever wanted back.

### 2026-09-08 — Claude Code (Opus 5) — Refusal-ledger work removed

- The user reported that their teacher identified the refusal ledger as a direction that
  would fail the project, and asked for it to be removed.
- Deleted `demo-refusal-ledger/` in full and `INNOVATION.md`, the proposal that argued
  for it. Removed the `INNOVATION.md` row from the ownership table above and the two
  session-log entries describing that work.
- Nothing in the project imported it. The demo folder was standalone by design, so no
  application code, test, lesson, or document needed changing; verified by searching for
  imports of its modules and for references to it outside its own folder.
- Verified after removal: all 23 tests pass in the project `.venv`, and no reference to
  the removed work remains outside git history.
- The work is still recoverable from git history if the objection turns out to be
  narrower than the whole idea. It was removed from the working tree, not from the
  repository's past.

### 2026-09-06 — Codex — Simple ML assignment with simulated history

- User requested ML for assignment and explicitly approved simulated records. Added annotated `duration_model.py`, `train_assignment.py`, 400 generated historical rows with provenance, pinned dependency, and evaluation report. Assignment now scores all feasible pairs and chooses the lowest predicted duration; constraints still filter candidates first. GUI shows simulated model status, candidate estimates, and explicit fallbacks.
- Created project-local `.venv` using the existing Miniconda Python and installed scikit-learn 1.9.0. Use its Python for ML (README commands). Fitting occurs before window creation; no background training or persisted model binary. Generator refuses to overwrite existing CSV experiments.
- Verified all 23 tests in `.venv`, including changed training data changing the winning pair, later test outcomes not affecting fitting, invalid predictions leaving state intact, and the GUI registration/assignment workflow. Also ran the original 16 tests with the base Python to exercise missing-dependency fallback. Checked main control bounds at 1220x750 and 1160x720 with the full four-candidate message. No screenshot visual review.
- Measured chronological simulated test MAE: tree 1.9571 minutes, training ward-median baseline 5.7391, using 320 training and 80 later test rows. First General medicine selection observed: R01-2 / D01-2, 18.9 minutes. These results demonstrate the simulated pattern only.
- Updated current status, setup instructions, and detailed ML teaching walkthrough. Lesson 3 independent practice is pending. Real-world/patient-specific duration, global scheduling optimization, release/lifecycle, hardware, and external integrations remain unimplemented. User practice files and earlier lesson snapshots were preserved.

### 2026-09-06 — Codex — Lesson 3 reservations

- The user said "let's go" after completing lesson 2. Added annotated `assignment.py`, an Assign selected case action and assignment column, and a Rooms and doctors tab. Preserved lesson 2 source in `lessons/lesson_02/`; user practice files in `no-comment` were not edited.
- The implemented increment is immediate reservation for appointments dated today, with two configured rooms/doctors per ward. Both resources must be available before state changes. See `AGENTS.md` and `README.md` for current limitations; future scheduling, releases, and stable patient identities are not implemented.
- Added eight domain tests and expanded the existing GUI workflow check. Ran `C:\ProgramData\miniconda3\python.exe -m unittest -v test_registration.py test_assignment.py`: all 16 tests passed. Checked main control bounds at 1220x750 and 1160x720. No screenshot-based visual verification was performed.
- Added the detailed lesson 3 walkthrough and a disabled-doctor exercise to `LEARNING.md`. Practice completion remains unconfirmed. Updated feature status and run instructions in their owning documents.

### 2026-09-06 — Claude Code (Opus 5) — Git initialised

- Initialised a git repository at the project root, on branch `main`. Two commits:
  a baseline snapshot of all existing work, then a `.gitattributes` line-ending fix.
- Added `.gitignore` covering `__pycache__/`, `*.db`/`*.sqlite*` (lesson 6 will create
  local databases; patient records, even fictional, stay out of version control), `.env`
  and key files, virtualenvs, and editor noise.
- Added `.gitattributes` normalising line endings to LF. `core.autocrlf` is `true` on this
  machine, and without normalisation a file touched by both assistants diffs entirely as
  invisible line-ending changes.
- The project directory is owned by the `CodexSandboxOffline` account while Claude Code
  runs as `Thor1`, so git refused to operate until the path was added to
  `safe.directory` in the global git config. Codex sessions may need the same exception
  under their own account.
- Verified at snapshot time: all 16 tests pass via
  `python -m unittest test_registration.py test_assignment.py`, all sources compile, and
  the working tree is clean with 20 files tracked.
- Codex was actively writing lesson 3 during this session. `assignment.py` and
  `test_assignment.py` are captured in the baseline commit as working-but-in-progress;
  this session did not review, verify, or change lesson 3 content, and makes no claim
  that the lesson is finished.
- No application code was modified. No remote was configured and nothing was pushed.

### 2026-09-06 — Codex — Lesson 2 learning complete

- The user said, "I'm done learning the 2nd part." Recorded their reported completion in `LEARNING.md` and removed the obsolete pending-practice item above. No additional assessment was performed.
- Next increment: explain and model multiple rooms within a ward and doctor availability, starting with two rooms and three waiting patients. Lesson 3 has not been implemented in this session.
- Documentation only; no application or user practice files were changed. Read back the updated progress and handoff entries; application tests were not rerun for this documentation update.

### 2026-09-06 — Codex

- Updated `AGENTS.md` to require future Codex sessions to read the newest `HANDOFF.md` entry after loading the project rules, and to add a newest-first handoff entry after project changes.
- Updated `README.md` to list `HANDOFF.md` as the shared Codex/Claude Code session log.
- No application behavior changed and no additional tests were needed; this was an instruction/documentation update.

### 2026-09-06 — Codex

- Built lesson 2 in `app.py` and `registration.py`. The form now accepts patient name, optional medical history/information, appointment date (`YYYY-MM-DD`), phone number, and destination ward.
- The user confirmed that the date means appointment date. Date of birth is expected to belong in a future medical-record design, not this registration form.
- Generated queue IDs use `QWWRR`: `Q` + two-digit ward code + two random digits (`00`–`99`). Shared ward prefixes are intentional: `Q0107` and `Q0142` can both belong to ward `01`. Only full IDs must be unique in the current in-memory session. Rooms are separate resources and are not assigned yet.
- Added editable example ward mappings in `registration.py`, validation for names, notes, dates, phone formats, ward codes, and the 100-ID-per-ward session capacity. Successful registrations appear in a Treeview overview and retain the confirmation popup behavior the user added during lesson 1.
- Preserved the heavily annotated lesson 1 as `lessons/lesson_01.py`. Added detailed comments to the new files and updated `AGENTS.md`, `README.md`, and `LEARNING.md` for lesson 2.
- Added `test_registration.py`. Verified with `C:\ProgramData\miniconda3\python.exe -m unittest -v test_registration.py`: all 8 tests passed, including shared ward prefixes, full-pool handling, validation, date rules, phone normalization, popup/table behavior, and duplicate prevention.
- Not implemented or verified: patient-name record lookup, persistence/database, room assignment, doctor availability, scheduling, arrival/urgency fields, duration model, ESP32, or external AI FAQ. Do not describe these as working.
- Next teaching step should wait for the user's lesson 2 practice unless they explicitly ask to continue. The likely next lesson is modeling multiple rooms within a ward and doctor availability; keep patient data fictional.

### 2026-09-06 — Claude Code (Opus 5)

- Added `CLAUDE.md`, a two-line pointer that imports `AGENTS.md` so both assistants work
  from one instruction file. `AGENTS.md` itself was not modified.
- Created this file.
- No application code, tests, or lesson content changed. Nothing was run or re-verified;
  project state is as `LEARNING.md` and `README.md` already describe it.
