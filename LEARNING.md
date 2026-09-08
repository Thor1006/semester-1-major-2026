# Learning and rebuilding the project

## Our working method

Each lesson follows this sequence:

1. **Understand:** name the small problem and explain the concepts needed.
2. **Build:** implement one runnable piece.
3. **Trace:** follow a concrete input through the code to its output.
4. **Check:** run it and compare the behavior with an explicit expectation.
5. **Try:** make one small change or recreate the piece independently.

The aim is to explain and recreate the behavior, not memorize the finished source. Lessons may be split into smaller sessions depending on Python experience.

## Planned lessons

| Lesson | What we build | What you learn |
| --- | --- | --- |
| 1 | A Tkinter window with a queue-ID field, button, and output label | Widgets, layout, functions, callbacks, and the event loop |
| 2 | Patient registration with generated ward IDs and an in-memory queue | Lists, dictionaries, sets, validation, random selection, and displaying records |
| 3 | A doctor and room assignment for a simple case | Resource state, conditions, and separating logic from the interface |
| 4 | Scheduling with time slots and staff-assigned urgency | Interval overlap, ordering, constraints, and testing edge cases |
| 5 | Start, finish, cancel, and overrun workflows | State transitions and keeping the queue and resource views consistent |
| 6 | Save and reload fictional appointments | SQLite, record identifiers, and persistence |
| 7 | Simulated room events, followed by one ESP32 button | Event messages, serial communication, debouncing, and disconnections |
| 8 | A documented baseline duration estimate | Averages, medians, and stating where an estimate came from |
| 9 (optional) | General hospital FAQs, beginning locally | Public information boundaries and API request construction |
| 10 | Independent rebuild and presentation | Reconstructing requirements, explaining choices, and demonstrating limitations |

## Current progress

- Completed: proposal captured and project instructions created.
- Completed: step-by-step teaching approach documented.
- Implemented and checked: lesson 1, including a working window and Add callback.
- User practice observed: you added a messagebox confirmation to lesson 1. That popup is retained in lesson 2.
- Completed: lesson 2 registration, generated ward-based queue IDs, and an in-memory queue. The user reported finishing learning this part on 2026-09-06; no additional assessment was performed.
- Implemented and checked: lesson 3, reserving rooms and doctors for today's cases. Two rooms and two doctors per ward support the three-patient demonstration. The user's lesson 3 practice is pending.
- Next after practice: time-slot scheduling in lesson 4. Completion/release and persistence remain later increments.
- Removed on 2026-09-08 at your request: the lesson 3 machine-learning extension, its simulated history, and its walkthrough. Assignment now takes the first compatible free room and doctor in configured order. The project needs no extra packages again.
- Preparation for lesson 6 (persistence), 2026-09-08: ticket uniqueness is now scoped to one appointment date, so each ward gets a fresh pool of 100 suffixes every day. Without this, saving records to disk would have capped a ward at 100 patients forever rather than 100 per day. The trade-off to remember: a ticket alone no longer identifies a registration, so the date plus the ticket is the key.
- Implemented and checked, 2026-09-08: lesson 6 persistence. Registrations are saved to a local SQLite file and restored on startup; reservations are not. Built ahead of lessons 4 and 5 because you asked for it; time-slot scheduling and the release lifecycle are still missing. Your lesson 6 practice is pending.
- Implemented and checked, 2026-09-08: bulk CSV import, deleting one registration, clearing all of them, and a double-click details window. Your practice for this step is pending.
- Implemented and checked, 2026-09-08: configurable capacity per ward, saved between runs, with reductions refused when they would delete a reserved resource; and taking an individual room or doctor out of service. Your practice for this step is pending.
- Implemented and checked, 2026-09-08: manual assignment of a chosen room and doctor, and automatic assignment of every waiting case in arrival order. Your practice for this step is pending.
- No hardware checks are complete.

## First lesson's target

Enter a fictional queue ID such as `Q001`, click a button, and see `Added Q001` in a label. An empty input should produce a helpful message.

This first exercise only teaches input and button handling. Actual queue storage comes in lesson 2.

Concept to understand: `button click -> Python callback -> read input -> validate -> update label`.

Practice after the lesson: change the success message to `Queue Q001 is ready for check-in.` (using whatever ID was entered).

## Lesson notes

### Lesson 1: a window that responds

**Historical lesson:** preserved in `lessons/lesson_01.py`, including your later popup experiment. The explanation below describes the original label-update lesson; the current `app.py` now implements lesson 3. Lesson 2 is preserved in `lessons/lesson_02/`.

The snapshot contains detailed teaching comments in seven parts: imports, window creation, container layout, controls, the callback, button registration, and the event loop. The user subsequently removed the footer and replaced the success-label update with a popup; the snapshot preserves that experiment.

Run from the project folder in PowerShell:

```powershell
& 'C:\ProgramData\miniconda3\python.exe' app.py
```

**Vocabulary and code map**

- `import tkinter as tk` makes Python's GUI library available under the shorter name `tk`. `ttk` supplies themed controls from the same library.
- A **widget** is a visible interface component. `Label` displays text, `Entry` accepts text, and `Button` responds to clicks.
- `window = tk.Tk()` creates the main window. `title()` names it; `geometry()` gives its starting dimensions.
- A `Frame` groups widgets. Here it gives the controls some padding around the window edges.
- `pack()` places the frame inside the window. `grid()` places the controls inside that frame in numbered rows and columns. Using both here is valid because they manage children of different parents; avoid mixing them for children of the same parent.
- `sticky='w'` aligns a control west (left). `sticky='ew'` stretches it east to west. `columnconfigure(0, weight=1)` lets column 0 grow with the frame. `pady` adds vertical spacing.
- `def add_case():` defines a **function**, a named block of instructions. Defining it does not immediately run its body.
- A **callback** is a function another part of the program calls when something happens. `command=add_case` gives the button that function. `command=add_case()` would run it immediately during setup and pass its return value instead.
- `queue_entry.get()` reads the field as a string. `.strip()` removes spaces and other whitespace from both ends.
- `if not queue_id:` detects an empty string. `return` stops the function after displaying the validation message.
- `f'Added {queue_id}'` is an **f-string**: Python substitutes the value of `queue_id` inside the braces.
- `result_label.config(text=...)` changes the existing label's text.
- `mainloop()` runs the **event loop**, which waits for events such as typing and clicks and dispatches their handlers.
- `if __name__ == '__main__':` starts the event loop when this file is run directly. Importing this lesson file still creates its widgets, but skips the loop, allowing a short verification script to invoke its button and close it. Later we can move setup into a function when that structure becomes useful.

**Trace a click**

1. You type `  Q001  ` into the Entry.
2. You click Add. Tkinter calls `add_case`.
3. `.get()` returns `  Q001  `; `.strip()` produces `Q001`.
4. The string is not empty, so the validation branch is skipped.
5. The f-string becomes `Added Q001`, and `.config()` updates the label.
6. The callback finishes. The event loop keeps the window responsive for the next action.

The queue ID is a local variable inside the callback. This lesson only displays it; it does not append a record to a list or save a file.

**Checks performed**

The actual Tkinter button was invoked with empty input, spaces only, `Q001`, and `  Q002  `. The resulting messages matched expectations. Window creation, vertical layout bounds, and event-loop startup/shutdown were also checked. No claim is made that you have tried the lesson yet.

**Your exercise**

Change the success message so entering `Q001` displays `Queue Q001 is ready for check-in.`. Keep the queue ID dynamic so `Q002` also works.

Hint: modify the f-string inside `add_case`, leaving `{queue_id}` in the message. Save, close the old window, and run the file again to load your change. Then check that an empty field still produces the validation message.

After that, try recreating the window, Entry, button callback, and label in a separate practice file using the behavior description above. Further lessons can wait until you have had a chance to try this increment.

### Lesson 1: deeper explanation

**Names, objects, and text are different things.** In `queue_entry = ttk.Entry(content)`, the right side constructs an Entry object and the assignment binds a Python name to it. That name is not the typed queue ID. Calling `queue_entry.get()` later returns the current text as a string. The widget continues to exist while its contents can change many times.

Similarly, `result_label` refers to a Label object. `result_label.config(text='Hello')` changes that object's text option. Writing `result_label = 'Hello'` would bind the name to a string instead of updating the widget. A later `.config()` call on that string would fail because strings have no such method.

**Arguments supply inputs to an operation.** In `ttk.Label(content, text='Queue ID')`, `content` is a positional argument identifying the parent. `text='Queue ID'` is a keyword argument identifying an option by name. The `=` in a keyword argument associates a parameter name with a value for this call; it does not create a standalone `text` variable in this module. In `window.minsize(420, 280)`, position distinguishes width from height.

**Ownership and layout are separate.** The root window contains the `content` frame, which contains the labels, Entry, and Button. Destroying a parent destroys its contained widgets. However, specifying a parent does not tell Tkinter how to display its child. A geometry manager supplies the placement rules.

For resizing, three decisions cooperate. `pack(expand=True, fill='both')` makes the frame receive and fill extra window space. `columnconfigure(0, weight=1)` lets its grid column grow. `sticky='ew'` stretches the Entry and Button across that enlarged column. `sticky='w'` aligns a widget left without stretching it to both edges. No grid row has a growing weight here, so the controls remain toward the top when the window gets taller.

**Spacing has multiple layers.** Frame `padding=24` provides space inside the frame around the child layout. Widget `pady=(0, 12)` provides space outside that widget, above and below it. `wraplength=360` instead controls text wrapping: it neither adds padding nor restricts the number of input characters.

**Setup and interaction happen at different times.** Top-level statements execute in order to construct the interface. The `def` statement creates a function object but does not run its body. `command=add_case` registers that function as a handler. Only when the button is activated does the body read the then-current input. `mainloop()` processes user input, callbacks, and redraws while the application is open.

**Indentation defines control flow.** The function body is indented four spaces. The validation branch nests another level beneath `if not queue_id:`. Its `return` exits the callback immediately. The success update is outside that branch. Omitting `return` would let execution continue to the success update even after invalid input. Rejecting invalid input early like this is often called a guard clause.

**Cleaning and validation are separate steps.** `.strip()` returns a string without leading/trailing whitespace; it does not edit the Entry or remove internal spaces. The following empty-string check is the only validation rule in this lesson. Thus `Q 001` and `hello` are accepted as nonempty input. Format, uniqueness, and length constraints would require explicit additional rules.

**A callback updates state and then finishes.** Each invocation has its own local `queue_id`. The function looks up the module-level widget names and calls their methods. No `global` declaration is needed because those widget names are not reassigned inside the function. The function returns `None`, but the label retains its updated text in widget state. That temporary interface state is different from a case list or database; the next result overwrites the previous message.

**The event loop is not automatic parallel execution.** Our callback runs on the GUI thread. While it is executing, normal event handling on that same thread must wait. That is why it should finish promptly. A string check needs no background thread; serial reads or long model training later need a different arrangement so the interface stays responsive.

**The main guard controls only its indented block.** `if __name__ == '__main__':` checks whether this module is the program's entry point. Only `window.mainloop()` is guarded here. Importing the file still creates its widgets. A later refactoring can put setup in a function to avoid that import-time behavior when the project needs it.

**Common mistakes**

| Mistake | Consequence | Correct approach here |
| --- | --- | --- |
| `command=add_case()` | Runs the function during setup and passes its return value to Button. | Pass `command=add_case`. |
| `queue_entry.get` without `()` | Refers to the method rather than calling it to read text. | Call `queue_entry.get()`. |
| Removing `f` from the success string | Displays `{queue_id}` literally. | Keep `f'Added {queue_id}'`. |
| Removing the early `return` | Overwrites the validation error with the success message. | Exit the callback after showing the error. |
| Using both `pack` and `grid` for children of one parent | The geometry managers compete; Tk normally raises an error. | Use one of these managers per parent. |
| Typing a very long ID | The result can wrap beyond the available space; there is no length constraint or scrolling yet. | Use short fictional IDs for this exercise; add bounds deliberately later. |
| Saving code while the old window is open | The process continues with previously loaded code. | Close and restart it. |

**Rebuild order and reasons.** Import tools before using their names. Create the root before its children and the frame before using it as their parent. Make the Entry and result label available before the callback is invoked. Define the callback before passing its name to the button. Start the event loop after setup. Grid positions determine visual order, so constructing row 5 before row 4 is valid.

### Lesson 3: assigning a room and doctor

**Status:** implemented and checked; independent practice pending. Read `assignment.py` first, then `refresh_resources()` and `assign_selected()` in `app.py`. The registration code is still present, and lesson 2's source is preserved in `lessons/lesson_02/`.

**Run from this project folder:**

```powershell
& 'C:\ProgramData\miniconda3\python.exe' app.py
```

**What this increment means.** You choose a registered case dated today and request an immediate reservation. The program must find both a room in its ward and an available doctor configured to support that ward. A successful reservation lasts for this running session. Selecting a future appointment does not reserve today's resources; later lessons will model actual start/end times. This lesson does not start a consultation or release a completed one.

**State is the data describing the situation now.** `rooms` and `doctors` describe the resources; `assignments` describes reservations. An example room dictionary is `{'id': 'R01-1', 'ward': 'General medicine', 'enabled': True}`. An example doctor has `wards: ['General medicine']`, a list so a doctor can eventually support more than one ward. `enabled` describes whether the resource can be used at all, independently of whether it currently has a reservation.

The `assignments` dictionary starts as `{}`. After an assignment it might contain:

```python
assignments = {
    'Q0107': {'room_id': 'R01-1', 'doctor_id': 'D01-1'},
}
```

The outer key identifies the ticket. The inner dictionary connects it to two resource IDs. Queue IDs, room IDs, and doctor IDs serve different purposes. Both `R01-1` and `R01-2` belong to the same ward; the shared `01` does not make them the same room.

**A factory gives us fresh starting data.** `make_demo_resources()` builds new room/doctor dictionaries inside nested `for` loops. The outer loop visits wards, and `range(1, 3)` in the inner loop yields 1 and 2. `return rooms, doctors` returns a tuple, which `rooms, doctors = make_demo_resources()` unpacks into two names. Fresh objects make tests independent and avoid accidentally reusing another run's changed resource settings.

**Derive availability from one source.** We do not maintain a separate `busy` flag on every resource and a second copy in every patient. Instead, `used_rooms = {item['room_id'] for item in assignments.values()}` derives the occupied room IDs from the existing assignments. Braces here form a set comprehension: evaluate the expression for each value and collect distinct IDs. Membership tests such as `candidate['id'] not in used_rooms` then answer whether a room is already reserved.

This avoids a common consistency bug: saying a room is free in one object but reserved in another. The resource table is another view of the same assignments. Its rows are display output, not the authoritative state.

**Find the first valid pair.** The function checks each room in configuration order. A room must match the destination ward, be enabled, and be absent from `used_rooms`. `and` requires all three conditions to be true. Every room passing all three is appended to `available_rooms`, and the reservation then takes `available_rooms[0]`: the first one configured. An empty list means nothing was suitable, which is what raises the no-room error.

Doctor selection is similar, but checks whether the ward is in a list of supported wards. Occupancy is checked across all assignments, so a doctor supporting two wards cannot be assigned in both simultaneously. This is a deterministic first-fit rule: the same waiting list always produces the same reservations, so you can predict what the button will do. It does not claim the pairing is the best possible one, because choosing among feasible pairs would need a stated goal this project has not defined. Staff choose which case to process; no clinical urgency ranking or random-ID sorting is involved.

**Check first, then mutate.** Discovering a room does not immediately reserve it. The function first verifies that a doctor is also available. Only after both are found does it execute `assignments[queue_id] = assignment`. If any earlier check raises `ValueError`, the dictionary remains exactly as it was. This prevents a failed doctor search from leaving a room stranded in a reserved state.

The callback runs on the one Tkinter UI thread, so a second click is processed after the first call completes. It sees the updated dictionary and cannot assign the same ticket again. This is sufficient for this local lesson, but separate users/processes would require stronger shared-storage transaction guarantees.

**Connect the rule to the window.** `queue_table.selection()` returns a tuple of selected row IDs. An empty tuple is false in a condition, so it is easy to reject a click without a selection. Our row IDs are queue IDs. `next(item for item in patient_records if ...)` searches for the corresponding dictionary; the UI creates rows from that same list, so the selected record is expected to exist. The callback invokes `assign_patient`, catches its explanatory errors, and updates the table's assignment cell after success. `refresh_resources()` then rebuilds the Rooms and doctors view from the updated dictionary.

`ttk.Notebook` adds tabs. Each tab is a container attached using `.add()`. The queue and resource tables can therefore use the same screen area without crowding the registration form. A tab switch changes the visible view, not the underlying data.

**Trace the three-patient example.** Register three fictional General medicine cases dated today. Select them in registration order, since their randomly generated ticket values do not indicate order.

| Action | Room | Doctor | Outcome |
| --- | --- | --- | --- |
| Assign first case | R01-1 | D01-1 | Pair reserved |
| Assign second case | R01-2 | D01-2 | A different pair reserved |
| Try third case | None free in that ward | No new reservation | Case stays Waiting |
| Click first case again | Existing reservation | Existing reservation | Rejected as already assigned |

**Verification.** All 16 registration/assignment tests passed. They exercise the real registration and assignment buttons, duplicate-click prevention, disabled resources, unavailable doctors without partial reservation, ward compatibility, doctors shared between wards, and date restrictions. Control bounds were checked at the default and minimum window sizes. This is software verification, not an assessment of your understanding or clinical validation.

**Your practice exercise.** In `app.py`, immediately after `rooms, doctors = make_demo_resources()`, add `doctors[0]['enabled'] = False`. Save and restart. The resource tab should show the first doctor as Unavailable. Assign two cases in General medicine: the first should get a room and the remaining enabled doctor; the second should stay Waiting with a no-doctor message, even though a room is still available. Explain which check caused this and why the room was not reserved. Remove your temporary line to restore the two-doctor demonstration.

**Current limits to remember.** The app tracks tickets rather than permanent patient identities; two registrations for the same person are not recognized as one patient. It does not use name matching as proof of identity. Reservation release, shifts, time intervals, priority, and persistence are future lessons. Closing the app resets all current state.


### Lesson 6: remembering the queue after the window closes

**Status:** implemented and checked; independent practice pending. Read `storage.py` first,
then the three places `app.py` uses it: the two lines near the top that open the database and
load records, `add_queue_row`, and the save inside `add_case`.

**Run it:**

```powershell
& 'C:\ProgramData\miniconda3\python.exe' app.py
```

**What this increment means.** Until now every registration lived in a Python list, and
closing the window destroyed it. The list was the only copy. This lesson gives the project
its first memory that outlives the process: register a patient, close the app completely,
open it again, and the queue is still there.

**What is saved, and what deliberately is not.** Registrations are saved. Room and doctor
reservations are not. That is not laziness, it is a consequence of what the project can do:
nothing here can END a reservation. There is no session completion, no release step. If a
reservation were saved, tomorrow it would come back still holding a room, and no part of the
program could free it. It would look like a feature and behave like a bug. Every loaded case
therefore starts as Waiting, and the startup message says so.

**Why SQLite.** It is in Python's standard library, so no new dependency is needed, and the
whole database is one ordinary file you can delete to start over. A CSV would also work, but
SQLite gives us the uniqueness rule for free and will not leave a half-written record behind
if the program stops mid-write.

**A table is a shape you declare once.** `CREATE TABLE IF NOT EXISTS` describes the columns
and the rules. `IF NOT EXISTS` is what makes it safe to run at every startup instead of only
the first one. `TEXT NOT NULL` means the column holds text and may never be empty of a value
(an empty string is still a value; `NULL` is the absence of one).

**The most important line in the file.**

```sql
UNIQUE (appointment_date, queue_id)
```

That is the ticket rule from `registration.py`, written where the DATABASE can enforce it.
A ticket is only unique within one appointment date, so `Q0147` may exist on the 8th and
again on the 9th, but never twice on the same day. Even a bug elsewhere in the program
cannot write a duplicate: SQLite refuses the insert. A rule enforced in one place only is a
rule waiting to be broken by the second piece of code that forgets it.

**Order needs its own column.** `row_id INTEGER PRIMARY KEY` is filled in automatically and
increases with each insert. Without it, `SELECT` makes no promise at all about the order rows
come back in, and the queue would reshuffle itself every restart. Date plus ticket identifies
a row but cannot tell us which arrived first.

**Never build SQL by joining strings.** Look at the `?` marks in `save_registration`:

```python
connection.execute('INSERT INTO registrations (...) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (record['appointment_date'], record['queue_id'], ...))
```

Each `?` is a PLACEHOLDER. SQLite substitutes the value itself, with correct quoting. Had we
written `f"... VALUES ('{name}')"`, a patient named `O'Brien` would break the statement, and
in a networked system the same habit is the classic SQL-injection vulnerability. There is a
test for the apostrophe case.

**`commit` is what makes it permanent.** Until `connection.commit()` runs, an insert lives
only inside this connection's transaction and would vanish if the program stopped. We commit
after each registration rather than at shutdown, so a crash cannot lose the queue.

**Loading must be invisible.** `load_registrations` returns plain dictionaries with exactly
the keys `create_patient_record` produces. That is the point: the rest of the program cannot
tell a loaded record from a fresh one, so `patient_records` simply starts full instead of
empty, and ticket generation automatically avoids the tickets already saved for that date.

**One consequence in the interface.** The queue table identifies each row by an `iid`. That
used to be the queue ID, which was fine while tickets were unique. Now that `Q0147` can exist
on two dates, using the ticket alone would make Tkinter refuse the second row outright. Hence
`row_key(record)`, which returns `"2026-09-08|Q0147"`: the same key the database uses.

**Save before you celebrate.** In `add_case`, the record is written to the database BEFORE it
is added to the list and the table. If the write fails, the user sees the error and no row
appears. The reverse order would let the table claim a patient was stored when they were not
--- the worst kind of bug in a system whose whole job is remembering.

**Trace one registration through.**

| Step | What happens |
| --- | --- |
| You click Register | `add_case` reads the fields |
| `create_patient_record` | validates, and picks a ticket unused *on that date* |
| `storage.save_registration` | inserts the row with placeholders, then commits |
| The list and table | the record is appended and a row appears, keyed `date|ticket` |
| You close the app | the process ends; the file remains |
| You reopen it | `storage.connect` opens the file, `load_registrations` refills the list, and `add_queue_row` rebuilds every row as Waiting |

**Where the file lives.** `Path(__file__).resolve().parent / 'clinic.db'` puts the database
next to the source, whichever folder you launched from. Writing `C:\Users\...` there would
break the project on any other computer. `.gitignore` already excludes `*.db`, so patient
records are never committed to version control even by accident.

**Your practice exercise.** Add a `registered_at` column recording when each registration was
made, and show it in the queue table. **Hint:** three places change. Add the column to
`SCHEMA` in `storage.py`, add it to the `INSERT` and the `SELECT` (and to `FIELDS`), and add
a column to `queue_table`. For the value, `from datetime import datetime` and
`datetime.now().isoformat(timespec='seconds')`. Then delete `clinic.db` and run the app
again --- and think about why deleting it was necessary, which is the next paragraph.

**The trap you just met.** `CREATE TABLE IF NOT EXISTS` does nothing when the table already
exists, even if your `SCHEMA` has changed. Adding a column to the text does not add it to a
file created yesterday, and you get a confusing error about a missing column. Real projects
solve this with MIGRATIONS: recorded, ordered changes applied to an existing database.
Deleting the file is the crude version, and acceptable here only because the data is
fictional.

**Common mistakes**

| Mistake | Consequence | Correct approach here |
| --- | --- | --- |
| Forgetting `commit()` | The insert disappears when the program ends. | Commit after each save. |
| Building SQL with f-strings | An apostrophe in a name breaks the statement; in a real system it is an injection hole. | Use `?` placeholders. |
| `SELECT` without `ORDER BY` | The queue order changes unpredictably between restarts. | Order by `row_id`. |
| Keying the table row by ticket alone | Tkinter refuses the second row when a ticket recurs on another date. | Use `row_key(record)`. |
| Saving reservations too | A restored reservation holds a room forever, because nothing can release it. | Save registrations only, until lesson 5 exists. |
| Running the checks against `clinic.db` | Test patients end up in your real saved queue. | The checks point `storage.DATABASE_PATH` at a temporary file. |

**Current limits to remember.** Only registrations persist. There is still no time-slot
scheduling (lesson 4), no completion or release (lesson 5), no way to edit or delete a saved
registration from inside the app, and no migrations. The app opens one database connection
and writes on the interface thread; that is fine at this size, but a slow or networked
database would need the work moved off the event loop.


### Lesson 6 extension: importing, deleting, and inspecting saved data

**Status:** implemented and checked; practice pending. Read `bulk_import.py` first, then
the four new callbacks in `app.py`: `show_details`, `delete_selected`, `import_csv` and
`clear_all`, plus the three new functions in `storage.py`.

Saving data was only half the job. Once information persists you need to get it in
quickly, look at it, and take it out again --- otherwise a typo is permanent and the only
way to inspect a record is to read the database file.

**Bulk import: validate everything, then write.**

`read_import_file` reads the CSV, runs every row through the same
`create_patient_record` used by the form, and collects the failures. Only if there are
none does it return records. Nothing is written from that module at all: it opens a file
and returns values, which is why it can be tested without a window or a database.

The rule it follows is ALL OR NOTHING. One bad row and nothing is imported. The
alternative --- import the good rows, list the skipped ones --- is a defensible design,
but it leaves the user reconciling two lists to work out who actually arrived. Here we
would rather they fix the file and try again. `storage.save_many` enforces the same rule
at the database level with `with connection:`, which rolls the whole transaction back if
any insert fails.

Two details worth copying into your own file-reading code:

- `newline=''` in the `open` call. The `csv` module documentation requires it, and it is
  what lets a quoted field containing a line break be read as one value.
- `encoding='utf-8-sig'`. Excel writes an invisible byte-order mark at the start of a CSV.
  Without `-sig` it becomes part of the first column's name, and your header check fails
  with a message that looks like nonsense.

**Row numbers should match what the user sees.** `enumerate(rows, start=2)` counts from 2
because row 1 is the header. Telling someone "row 5 is wrong" when their spreadsheet shows
the problem on row 6 wastes their time and their trust.

**Tickets are generated, never imported.** The CSV has no queue-ID column. If it did, a
file could invent an ID the app would not have chosen, or collide with a saved one. Each
row is given a ticket by the ordinary generator, and the running list `known` grows as
rows are accepted, so two rows in the same file cannot claim the same ticket either.

**Deleting has a consequence beyond the row.** A deleted patient may have been holding a
room and a doctor. Remove the record and forget the reservation, and those resources stay
marked Reserved by someone who no longer exists, with nothing able to release them:

```python
if record['appointment_date'] == date.today().isoformat():
    if assignments.pop(record['queue_id'], None) is not None:
        refresh_resources()
```

The date check is the subtle part. `assignments` is keyed by ticket alone, which is safe
only because just today's cases can hold a reservation. Deleting *another* date's
identical ticket must not release today's room. This is exactly the kind of bug that
date-scoped tickets introduce quietly.

**Confirmations should say what disappears.** "Delete this record?" invites a reflex yes.
Naming the patient, the ticket and the date gives the user something to check. `Clear all`
asks twice, because it cannot be undone and one stray click should not empty the queue.

**A details window, on double-click.** Single click SELECTS a row, and selecting is how
you choose a case to assign or delete. If selecting also opened a window you would have to
dismiss it before every other action. Double-click to open is the ordinary desktop
convention, and `Details` gives the same thing a visible button.

```python
queue_table.bind('<Double-1>', show_details)
```

`bind` attaches a handler to an EVENT rather than to a widget's command. Tkinter passes an
event object to the handler, which is why `show_details(event=None)` accepts an argument
it never uses --- the default lets the button call it with no argument at all.

`Toplevel` creates a second window. `transient(window)` keeps it above the main one;
`grab_set()` makes it modal, so the table underneath cannot change while its details are
displayed. The notes box is filled and *then* set to `state='disabled'`: a disabled Text
refuses insertions, so doing it in the other order leaves you with an empty box.

**A privacy decision, made deliberately.** The queue table hides medical information,
because that table sits on screen where anyone can glance at it. The details window shows
it, because a staff member asked for one named patient. That is a judgement about who is
looking, not an oversight --- and it is worth being able to explain in those terms.

**Trace an import.**

| Step | What happens |
| --- | --- |
| You click Import CSV... | `filedialog.askopenfilename` returns a path, or `''` if you cancelled |
| `read_import_file` | checks the header, then validates every row, collecting problems |
| Any problem | a warning lists them by spreadsheet row number; nothing is written |
| No problems | `storage.save_many` inserts them all inside one transaction |
| The interface | each record is appended to the list and given a table row |

**Your practice exercise.** Add an **Export CSV** button that writes the current queue back
out to a file. **Hint:** `filedialog.asksaveasfilename(defaultextension='.csv')` gives you
a path, and `csv.DictWriter` is the mirror of `DictReader` --- create it with
`fieldnames=bulk_import.REQUIRED_COLUMNS`, call `writeheader()`, then `writerow()` per
record. Think about one question first: should the export include the queue ID? Re-reading
your own export should behave like importing new patients, and the answer follows from
that.

**Common mistakes**

| Mistake | Consequence | Correct approach here |
| --- | --- | --- |
| Writing rows as you validate them | A bad row halfway leaves a partial import nobody can audit. | Validate everything, then write in one transaction. |
| `open(path)` without `newline=''` | A quoted field containing a line break splits into two rows. | Pass `newline=''`, as the csv docs require. |
| Plain `utf-8` for an Excel file | The first column name silently gains a BOM and the header check fails. | Use `utf-8-sig`. |
| Numbering problem rows from 1 | Every message points one row above the real problem. | `enumerate(rows, start=2)`. |
| Deleting a record but not its reservation | A room stays Reserved by a patient who no longer exists. | Pop the assignment and refresh the view. |
| Popping the assignment without checking the date | Deleting another day's identical ticket frees today's room. | Compare `appointment_date` with today first. |
| Opening details on single click | Selecting a row for any other action becomes a fight. | Bind `<Double-1>`. |
| Disabling the notes Text before inserting | The box stays empty; disabled widgets refuse insertions. | Insert first, disable after. |

**Current limits to remember.** There is no export yet (that is your exercise) and no way
to EDIT a saved registration --- only to delete it and enter it again. Import cannot update
an existing patient, and it has no dry-run preview. Deleting is immediate and permanent;
there is no undo and no archive of removed records, which a real clinic would need.


### Lesson 6 extension: changing the capacity of the clinic

**Status:** implemented and checked; practice pending. Read `make_demo_resources` and
`blocking_reservations` in `assignment.py`, then the capacity functions in `storage.py`,
then `apply_capacity` and `set_selected_resource` in `app.py`.

Until now every ward had exactly two rooms and two doctors, written into a `range(1, 3)`
that nothing could change. Capacity is the real constraint on how many patients a clinic
can serve, so it belongs in the interface rather than in the source.

**A default is not the same as zero.** `load_capacity` returns only the wards somebody has
actually configured. A ward missing from the table has never been changed, so it uses
`DEFAULT_CAPACITY`. Had we stored a row for every ward up front, adding a new ward to
`WARD_CODES` later would give it no rooms and no doctors, and the bug would look like the
new ward being broken rather than the storage being too eager.

**Identity has to survive a change.** Resource IDs come from POSITION: `R01-3` is the third
room of ward 01, always. Growing a ward from two rooms to three therefore adds `R01-3` and
leaves `R01-1` and `R01-2` untouched, so a reservation pointing at `R01-1` still points at
a real room afterwards. Had IDs been handed out in creation order, or renumbered on each
rebuild, every existing reservation would quietly start referring to a different room.

**Check before you shrink.** This is the important rule in the increment:

```python
blocked = blocking_reservations(ward, new_rooms, new_doctors, capacity, assignments)
if blocked:
    ...refuse, and name them...
```

Reducing capacity deletes resources from the end of the numbering. If one of those is
reserved, the patient holding it would be left assigned to a room that no longer exists ---
or, worse, silently unassigned with nothing on screen to say so. `AGENTS.md` requires that
staff explicitly apply changes to existing assignments, so the interface refuses and names
the resources in use. The same rule stops a reserved room being taken out of service.

Notice this is the same shape as `assign_patient`: work out whether the whole change is
possible, and only then change anything. A validation that runs halfway through a mutation
is not a validation.

**Replace lists in place.** `rebuild_resources` uses slice assignment:

```python
rooms[:] = new_rooms
```

not `rooms = new_rooms`. The list object was handed to `assign_patient`, and other code
holds the same object. Rebinding the name inside a function would create a NEW list that
only that function could see, and (without a `global` declaration) would not even change
the module-level name. `rooms[:] = ...` empties and refills the object everyone shares.

**Out of service is not the same as absent.** A room under maintenance still exists: its ID
must stay taken so the next room added to that ward does not reuse it. That is why disabled
resources live in their own table rather than being expressed as a smaller capacity number.
`enabled` was already in the resource dictionaries from lesson 3 and displayed as
Unavailable; this increment is what finally lets anything set it.

**Spinbox contents are text.** A `ttk.Spinbox` can be typed into as well as clicked, so
`int(rooms_spin.get())` can raise `ValueError`, and the range still has to be checked
afterwards. Trusting a spinbox because it has arrows on it is a common way to meet a
crash.

**Trace a reduction that is refused.**

| Step | What happens |
| --- | --- |
| Ward has 3 rooms; `R01-3` is reserved by a case | |
| You set Rooms to 2 and click Apply | `apply_capacity` reads and range-checks the numbers |
| `blocking_reservations` | works out that `R01-3` would be removed, and that it is reserved |
| The result | nothing is saved, nothing is rebuilt, and the message names `R01-3` |
| You delete or reassign that case, then retry | the list is empty, so the change is saved and applied |

**Your practice exercise.** Add a **Reset capacity to default** button that returns the
selected ward to two rooms and two doctors. **Hint:** it is `apply_capacity` with the
numbers replaced by `DEFAULT_CAPACITY` --- and it must run the same `blocking_reservations`
check, because resetting a ward from four rooms to two is a reduction like any other.
Think about whether it should also put that ward's out-of-service resources back in
service, and be able to say why you chose either way.

**Common mistakes**

| Mistake | Consequence | Correct approach here |
| --- | --- | --- |
| Storing a capacity row for every ward at startup | A ward added later gets zero of everything. | Store only what was configured; fall back to the default. |
| Numbering resources by creation order | Existing reservations start pointing at different rooms. | Derive IDs from position. |
| Shrinking without checking reservations | A patient is left holding a room that no longer exists. | Call `blocking_reservations` first and refuse. |
| `rooms = new_rooms` inside a function | The shared list is untouched; assignment keeps using the old one. | `rooms[:] = new_rooms`. |
| Expressing maintenance as lower capacity | The next room added reuses the ID of the broken one. | Keep out-of-service resources in their own table. |
| `int(spinbox.get())` without a try | A typed value crashes the callback. | Catch `ValueError` and show a message. |

**Current limits to remember.** Capacity is per ward, not per room type or per session ---
there are no opening hours, shifts, or part-time doctors. A doctor still supports exactly
one ward, even though the data structure holds a list. `MAX_PER_WARD` is an interface
guard, not a hospital rule. Removing a ward entirely, or renaming one, still means editing
`WARD_CODES` in the source.


### Lesson 6 extension: choosing a pair, and serving the queue in order

**Status:** implemented and checked; practice pending. Read `check_case_is_assignable`,
`available_resources`, `assign_patient_to` and `auto_assign` in `assignment.py`, then
`manual_assign` and `auto_assign_all` in `app.py`.

One assignment rule was never going to be enough. First fit is predictable but blind: it
cannot know that this patient saw Doctor 2 last month, or that Room 1 has the equipment
this case needs. And assigning a full waiting room one click at a time is tedious. So there
are now three modes --- and the interesting design work is making sure they cannot
contradict each other.

**Shared checks are what keep three modes honest.** Before this increment, all the
eligibility logic lived inside `assign_patient`. Adding two more modes by copying it would
have created three places to fix every future rule change, and they would drift. Instead
two helpers were extracted:

- `check_case_is_assignable` --- is this case eligible at all? (not already assigned, dated
  today) and returns its ward.
- `available_resources` --- which rooms and doctors in that ward are free, enabled and
  compatible?

`assign_patient` now reads as four short lines on top of those, and the other two modes
build on exactly the same foundation. **A rule stated once cannot disagree with itself.**

**Manual mode overrides the choice, not the rules.** This is the distinction worth
understanding. A staff member genuinely knows things the program does not, so they may pick
any pair --- but they still cannot put two patients in one room, use a room from another
ward, or take a room that is out of service. `assign_patient_to` therefore validates its
arguments exactly as strictly as first fit validates its own choice.

The chooser is built from `available_resources`, the same function the rule uses, so it
**cannot offer something that would then be refused**. That is worth doing deliberately: an
interface that offers an option and then rejects it teaches users to distrust it. The check
still runs on confirm, because the window could have been open while something else took a
resource.

**Refusals name the actual reason.** `_explain_choice` works out *why* a chosen resource is
unusable rather than saying "not available":

| Situation | Message |
| --- | --- |
| No such resource | `R01-9 is not a room in this clinic.` |
| Wrong ward | `R02-1 does not serve General medicine.` |
| Maintenance | `R01-1 is out of service.` |
| Taken | `R01-1 is already reserved by Q0107.` |

The last one is the most useful: it names the ticket holding the room, so staff know whose
case to look at. "Not available" would leave them guessing.

**Automatic mode is first come, first served.** `auto_assign` walks `patient_records` from
front to back. That list is kept in arrival order, and `ORDER BY row_id` reloads it in the
same order after a restart, so **walking the list IS the queue discipline** --- no sorting
step is needed or wanted.

The thing to be careful about: **the ticket is not a position.** `Q0199` may have arrived
before `Q0102`, because the two digits are random. Sorting the queue by ticket would look
sensible and quietly serve people in the wrong order. There is a test whose tickets descend
precisely so that an implementation which sorted them would fail.

**One blocked case must not stop the rest.** A case that cannot be served is recorded with
its reason and the loop continues:

```python
except ValueError as error:
    waiting.append((queue_id, str(error)))
```

Without this, a full General medicine would leave Pediatrics patients unserved even with
rooms standing empty. The return value separates `assigned` from `waiting`, so the
interface can report both.

**Filling gaps is not the same as rescheduling.** `auto_assign` skips any case that already
has a reservation, so a pair you chose by hand survives a later automatic run untouched.
`AGENTS.md` requires that staff explicitly apply changes to existing assignments; silently
"optimising" a manual choice would break that, and would also make the button unsafe to
press twice. Running it twice assigns nothing the second time.

**Rebuild the column, do not patch it.** Automatic assignment changes many rows at once, so
`refresh_queue_assignments` rewrites every Assignment cell from the reservation dictionary
rather than trying to remember which rows changed. It is idempotent, and it removed a small
duplication: first-fit assignment now uses it too.

**Trace an automatic run.** Three General medicine cases and one Pediatrics case arrive,
with two rooms and two doctors per ward. The first case was already given `R01-2 / D01-2`
by hand.

| Case | What happens |
| --- | --- |
| First (manual) | skipped: it already holds a reservation |
| Second | first fit gives it `R01-1 / D01-1`, the remaining General medicine pair |
| Third | no free room in General medicine; recorded as waiting, with the reason |
| Fourth | Pediatrics is untouched, so it gets `R02-1 / D02-1` |

Result: two assigned, one waiting, and the manual choice unchanged.

**Your practice exercise.** Add a **Release** button that frees the selected case's room and
doctor, returning it to Waiting. **Hint:** it is `assignments.pop(queue_id, None)`, then
`refresh_queue_assignments()` and `refresh_resources()`. Two questions to think about
first: should releasing be allowed for a case dated other than today, and should it ask for
confirmation the way Delete does? This exercise is the first half of the completion
lifecycle the project still lacks.

**Common mistakes**

| Mistake | Consequence | Correct approach here |
| --- | --- | --- |
| Copying the eligibility checks into each mode | Three copies drift apart as rules change. | Share `check_case_is_assignable` and `available_resources`. |
| Letting manual mode skip validation | Two patients end up in one room. | Override the choice, never the rules. |
| Offering every resource in the chooser | The interface suggests options it then refuses. | Populate from `available_resources`. |
| Sorting the queue by ticket | Patients are served in random order while looking sorted. | Walk the list in arrival order. |
| Stopping the run at the first failure | A full ward blocks every other ward. | Record the reason and continue. |
| Reassigning cases that already hold a pair | A manual choice is silently overwritten. | Skip cases already in `assignments`. |
| Patching single cells after a bulk change | Rows drift out of step with the real state. | Rebuild the column from `assignments`. |

**Current limits to remember.** There is still no way to RELEASE a reservation (that is
your exercise) and no completion step, so a room stays held until the app closes.
Assignment remains same-day and immediate: no time slots, no shifts, no clinical urgency.
Auto-assign has no preview --- it applies immediately rather than proposing a plan.
