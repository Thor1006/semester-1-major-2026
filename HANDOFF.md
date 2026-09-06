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
- No appointment dataset, trained duration model, ESP32 connection, or external AI call
  has been implemented or verified.

## Session log

Newest first. One short entry per session: what changed, what was verified, what was not.

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
