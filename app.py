"""Lesson 3: registration plus immediate room and doctor reservations.

Your fully annotated lesson 1, including the popup you added, is preserved in
lessons/lesson_01.py. Lesson 2 is preserved in lessons/lesson_02/.
"""

# 1. IMPORTS AND DATA
# tkinter controls the window, ttk provides themed widgets, and messagebox
# retains your confirmation popup. date supplies the default appointment date.
import tkinter as tk
from datetime import date
# filedialog asks the operating system for a file, so we never build a path by
# hand or guess where the user keeps their spreadsheet.
from tkinter import filedialog, messagebox, ttk

# Import our own module using its filename without .py. It owns validation and
# ID generation; this file owns the visible interface and its event handling.
from registration import WARD_CODES, create_patient_record
from assignment import (DEFAULT_CAPACITY, MAX_PER_WARD, assign_patient,
                        assign_patient_to, auto_assign, available_resources,
                        blocking_reservations, make_demo_resources)
from bulk_import import REQUIRED_COLUMNS, read_import_file
import storage

# Open the local database and read back everything registered previously. From
# lesson 6 onward this list starts FULL rather than empty, and closing the app
# no longer loses the queue. The file stays on this computer; nothing is
# transmitted anywhere.
database = storage.connect()
# This LIST holds one dictionary per registration, in arrival order. Records
# loaded from disk are ordinary dictionaries, identical in shape to new ones,
# so the rest of the program cannot tell them apart. It also feeds ticket
# generation, so yesterday's saved tickets are excluded from today's choices.
patient_records = storage.load_registrations(database)

# Capacity is configuration, so it is saved too. A ward missing from the table
# has never been changed and uses the default, which is why a ward added to
# WARD_CODES later starts with resources instead of none.
capacity = storage.load_capacity(database)
disabled_resources = storage.load_disabled_resources(database)

# Unpack the two lists returned by the factory. The separate dictionary maps
# queue IDs to reservations; its presence/absence defines reserved/waiting state.
# Reservations are deliberately NOT saved: nothing can end one yet, so a
# restored reservation would hold a room forever. Every loaded case therefore
# starts as Waiting.
rooms, doctors = make_demo_resources(capacity, disabled_resources)
assignments = {}


def row_key(record):
    """The unique row identifier for one registration.

    A ticket alone is NOT unique any more: the pool is scoped to a date, so
    Q0147 may exist on the 8th and again on the 9th. Using the ticket as the
    table's row id would make Tkinter refuse the second one. Date plus ticket
    is the same key the database uses.
    """
    return f"{record['appointment_date']}|{record['queue_id']}"

# Assignment takes the first compatible free room and doctor, in configured
# order. No duration is predicted and no model is loaded: the app needs only
# Python's standard library and Tkinter.
assignment_rule = ('Assignment takes the first compatible free room and doctor, '
                   'in configured order.')


# 2. WINDOW AND CONTAINERS
# Calling Tk constructs the root; assignment binds a name to the object.
# Its methods set the title, requested starting dimensions, and minimum size.
window = tk.Tk()
window.title('App')
window.geometry('1220x750')
window.minsize(1160, 720)

# pack expands the frame inside the root; grid arranges that frame's children.
# Mixing managers is valid here because they manage DIFFERENT parents.
content = ttk.Frame(window, padding=24)
content.pack(fill='both', expand=True)
content.columnconfigure(0, weight=1)
content.columnconfigure(1, weight=1)
content.rowconfigure(2, weight=1)

heading = ttk.Label(content, text='Front-desk registration', font=('Segoe UI', 20, 'bold'))
# columnspan=2 covers both grid columns. sticky='w' anchors text to the left.
heading.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
instructions = ttk.Label(
    content,
    text=('Use fictional patient details: registrations are saved to a file on this computer. '
          'Double-click a queue row to see its details.'),
)
instructions.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 20))

# LabelFrame groups widgets with a visible caption. nsew stretches the container
# north, south, east and west. Padding is internal; padx/pady add external gaps.
form = ttk.LabelFrame(content, text='Patient information', padding=18)
form.grid(row=2, column=0, sticky='nsew', padx=(0, 18))
form.columnconfigure(0, weight=1)

# A Notebook is a tab container: show either the queue or resource availability
# without squeezing two tables onto the same screen. add() manages its pages.
workspace = ttk.Notebook(content)
workspace.grid(row=2, column=1, sticky='nsew')
queue_panel = ttk.Frame(workspace, padding=18)
workspace.add(queue_panel, text='Patient queue')
resource_panel = ttk.Frame(workspace, padding=18)
workspace.add(resource_panel, text='Rooms and doctors')
queue_panel.columnconfigure(0, weight=1)
queue_panel.rowconfigure(1, weight=1)


# 3. THE FIVE INPUTS
# Entry accepts one line, Text accepts multiple lines, and Combobox offers choices.
# Each has a field label. An asterisk marks a required field.
name_label = ttk.Label(form, text='Patient name *')
name_label.grid(row=0, column=0, sticky='w', pady=(0, 4))
name_entry = ttk.Entry(form)
name_entry.grid(row=1, column=0, sticky='ew', pady=(0, 12))

information_label = ttk.Label(form, text='Medical history / information (optional)')
information_label.grid(row=2, column=0, sticky='w', pady=(0, 4))
# Text height is measured in text lines. wrap='word' wraps at word boundaries.
# A child frame lets the Text and its scrollbar share one row of the main form.
information_frame = ttk.Frame(form)
information_frame.grid(row=3, column=0, sticky='ew', pady=(0, 12))
information_frame.columnconfigure(0, weight=1)
information_text = tk.Text(information_frame, height=5, width=35, wrap='word', font=('Segoe UI', 10))
information_text.grid(row=0, column=0, sticky='ew')
information_scroll = ttk.Scrollbar(information_frame, orient='vertical', command=information_text.yview)
information_scroll.grid(row=0, column=1, sticky='ns')
# Two-way connection: scrollbar calls yview to move the text, while the text
# calls the scrollbar's set method to update the thumb position.
information_text.configure(yscrollcommand=information_scroll.set)

date_label = ttk.Label(form, text='Appointment date * (YYYY-MM-DD)')
date_label.grid(row=4, column=0, sticky='w', pady=(0, 4))
date_entry = ttk.Entry(form)
date_entry.grid(row=5, column=0, sticky='ew', pady=(0, 12))
# insert(0, ...) places text at character index zero. The default stays editable.
date_entry.insert(0, date.today().isoformat())

phone_label = ttk.Label(form, text='Phone number *')
phone_label.grid(row=6, column=0, sticky='w', pady=(0, 4))
phone_entry = ttk.Entry(form)
phone_entry.grid(row=7, column=0, sticky='ew', pady=(0, 12))

ward_label = ttk.Label(form, text='Destination ward *')
ward_label.grid(row=8, column=0, sticky='w', pady=(0, 4))
# list(dictionary) gives the keys, which here are readable ward names.
# readonly prevents inventing a destination by typing. Initially blank so the
# staff member chooses deliberately. A ward may later have several rooms.
ward_combobox = ttk.Combobox(form, values=list(WARD_CODES), state='readonly')
ward_combobox.grid(row=9, column=0, sticky='ew', pady=(0, 16))


# 4. QUEUE OVERVIEW
# join combines generated strings with a separator. These codes are examples;
# edit WARD_CODES in registration.py to use the desired destinations.
ward_legend = ' | '.join(f'{code}: {ward}' for ward, code in WARD_CODES.items())
legend_label = ttk.Label(queue_panel, text=ward_legend, wraplength=390)
legend_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 14))

# Treeview makes a table. show='headings' hides its extra hierarchy column.
# The in-memory record retains the five inputs, but the overview displays only
# the ID, ward, and date. Medical information is not shown in the shared queue.
queue_table = ttk.Treeview(queue_panel, columns=('queue_id', 'ward', 'date', 'assignment'), show='headings', height=10, selectmode='browse')
queue_table.heading('queue_id', text='Queue ID')
queue_table.heading('ward', text='Ward')
queue_table.heading('date', text='Date')
queue_table.heading('assignment', text='Assignment')
queue_table.column('queue_id', width=85, minwidth=70, stretch=False)
queue_table.column('ward', width=170, minwidth=100)
queue_table.column('date', width=105, minwidth=90, stretch=False)
queue_table.column('assignment', width=165, minwidth=150)
queue_table.grid(row=1, column=0, sticky='nsew')
queue_scroll = ttk.Scrollbar(queue_panel, orient='vertical', command=queue_table.yview)
queue_scroll.grid(row=1, column=1, sticky='ns')
queue_table.configure(yscrollcommand=queue_scroll.set)


def assignment_text(record):
    """What the Assignment column should say for one record.

    Reservations are keyed by ticket alone, which is only safe because just
    today's cases can hold one. The date check stops an identical ticket on
    another date borrowing today's reservation for display.
    """
    reservation = assignments.get(record['queue_id'])
    if reservation and record['appointment_date'] == date.today().isoformat():
        return f"{reservation['room_id']} / {reservation['doctor_id']}"
    return 'Waiting'


def add_queue_row(record):
    """Put one registration in the table and scroll it into view.

    Used both for cases loaded from the database at startup and for cases
    registered while the app is open, so a restored row is built by exactly the
    same code as a fresh one.
    """
    # '' means a top-level row, 'end' appends it, and iid is the unique row key.
    queue_table.insert(
        '', 'end', iid=row_key(record),
        values=(record['queue_id'], record['destination_ward'],
                record['appointment_date'], assignment_text(record)),
    )
    # see scrolls the row into view if the table has become longer.
    queue_table.see(row_key(record))


def refresh_queue_assignments():
    """Rewrite every Assignment cell from the reservation dictionary.

    Automatic assignment changes many rows at once, so rebuilding the column
    from the actual state is simpler and safer than trying to remember which
    rows were touched. It is also idempotent: running it twice is harmless.
    """
    for record in patient_records:
        key = row_key(record)
        if queue_table.exists(key):
            queue_table.set(key, 'assignment', assignment_text(record))


# Show everything read back from the database. Assignment state is not restored,
# so each loaded case is Waiting again.
for saved_record in patient_records:
    add_queue_row(saved_record)

format_label = ttk.Label(
    queue_panel,
    # Showing the expected CSV header here means the user learns the format
    # before choosing a file, instead of only from an error afterwards.
    text=(assignment_rule + '\nSelect a case dated today. Q0147 = ward 01 + random 47.'
          '\nCSV import columns: ' + ', '.join(REQUIRED_COLUMNS)),
    wraplength=390,
)
format_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(14, 0))
# Say on startup whether anything was restored, so a returning user can see at
# a glance that the queue survived rather than wondering whether it saved.
if patient_records:
    startup_text = (f'{len(patient_records)} patient(s) loaded from the saved queue. '
                    'Reservations are not restored.')
else:
    startup_text = 'Complete the required fields to generate a queue ID.'
result_label = ttk.Label(form, text=startup_text, wraplength=390)
# Row 10 is reserved for the button constructed after its callback definition.
result_label.grid(row=11, column=0, sticky='w', pady=(12, 0))

# This second table is a VIEW of configured resources and current reservations.
# Availability is derived from assignments, so both views use the same state.
resource_panel.columnconfigure(0, weight=1)
resource_panel.rowconfigure(1, weight=1)
ttk.Label(resource_panel, text='Configured capacity per ward. Reservations last for this session; session completion comes later.', wraplength=480).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 14))
resource_table = ttk.Treeview(resource_panel, columns=('id', 'ward', 'state'), show='headings')
for column, title, width in [('id', 'Resource', 85), ('ward', 'Ward(s)', 175), ('state', 'State', 180)]:
    resource_table.heading(column, text=title)
    resource_table.column(column, width=width)
resource_table.grid(row=1, column=0, sticky='nsew')
resource_scroll = ttk.Scrollbar(resource_panel, orient='vertical', command=resource_table.yview)
resource_scroll.grid(row=1, column=1, sticky='ns')
resource_table.configure(yscrollcommand=resource_scroll.set)


def refresh_resources():
    """Rebuild the availability view from the actual assignment dictionary."""
    # Delete only display rows, never the resource records or reservations.
    for row in resource_table.get_children():
        resource_table.delete(row)
    for kind, resources in [('room_id', rooms), ('doctor_id', doctors)]:
        reserved_by = {value[kind]: key for key, value in assignments.items()}
        for resource in resources:
            if resource['id'] in reserved_by:
                state = f"Reserved: {reserved_by[resource['id']]}"
            elif not resource['enabled']:
                state = 'Unavailable'
            else:
                state = 'Available'
            ward = resource['ward'] if kind == 'room_id' else ', '.join(resource['wards'])
            # iid is the resource ID, so a selected row can be acted on without
            # reading text back out of the display.
            resource_table.insert('', 'end', iid=resource['id'],
                                  values=(resource['id'], ward, state))


# 4b. CAPACITY: how many rooms and doctors each ward actually has.
capacity_box = ttk.LabelFrame(resource_panel, text='Capacity', padding=12)
capacity_box.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(14, 0))
capacity_box.columnconfigure(6, weight=1)

ttk.Label(capacity_box, text='Ward').grid(row=0, column=0, sticky='w', padx=(0, 6))
capacity_ward = ttk.Combobox(capacity_box, values=list(WARD_CODES), state='readonly',
                             width=18)
capacity_ward.grid(row=0, column=1, padx=(0, 12))
capacity_ward.set(list(WARD_CODES)[0])

ttk.Label(capacity_box, text='Rooms').grid(row=0, column=2, sticky='w', padx=(0, 4))
rooms_spin = ttk.Spinbox(capacity_box, from_=0, to=MAX_PER_WARD, width=4)
rooms_spin.grid(row=0, column=3, padx=(0, 12))
ttk.Label(capacity_box, text='Doctors').grid(row=0, column=4, sticky='w', padx=(0, 4))
doctors_spin = ttk.Spinbox(capacity_box, from_=0, to=MAX_PER_WARD, width=4)
doctors_spin.grid(row=0, column=5, padx=(0, 12))


def show_ward_capacity(event=None):
    """Load the chosen ward's current numbers into the two spinboxes."""
    current_rooms, current_doctors = capacity.get(capacity_ward.get(), DEFAULT_CAPACITY)
    # delete/insert rather than set(), so the box shows the stored value even if
    # the user had typed something else and then switched wards.
    rooms_spin.delete(0, 'end')
    rooms_spin.insert(0, current_rooms)
    doctors_spin.delete(0, 'end')
    doctors_spin.insert(0, current_doctors)


def rebuild_resources():
    """Recreate the resource lists from the current capacity and disabled set.

    The lists are replaced IN PLACE with rooms[:] = ... rather than rebound.
    assign_patient was handed these exact list objects, so rebinding the names
    here would leave it working from the old lists.
    """
    new_rooms, new_doctors = make_demo_resources(capacity, disabled_resources)
    rooms[:] = new_rooms
    doctors[:] = new_doctors
    refresh_resources()


def apply_capacity():
    """Change one ward's capacity, refusing to delete a resource in use."""
    ward = capacity_ward.get()
    try:
        # Spinbox contents are TEXT, and the user can type into it, so an
        # invalid entry has to be caught rather than assumed away.
        new_rooms = int(rooms_spin.get())
        new_doctors = int(doctors_spin.get())
    except ValueError:
        capacity_message.config(text='Rooms and doctors must be whole numbers.')
        return
    if not (0 <= new_rooms <= MAX_PER_WARD and 0 <= new_doctors <= MAX_PER_WARD):
        capacity_message.config(text=f'Enter values between 0 and {MAX_PER_WARD}.')
        return

    # Check BEFORE changing anything. Shrinking a ward onto a reserved room
    # would otherwise delete a resource a patient is currently holding, and
    # nothing would tell the staff member it had happened.
    blocked = blocking_reservations(ward, new_rooms, new_doctors, capacity, assignments)
    if blocked:
        capacity_message.config(
            text=f"Cannot reduce {ward}: {', '.join(sorted(blocked))} "
                 f"{'is' if len(blocked) == 1 else 'are'} reserved. "
                 f'Delete or reassign those cases first.')
        return

    storage.save_capacity(database, ward, new_rooms, new_doctors)
    capacity[ward] = (new_rooms, new_doctors)
    rebuild_resources()
    capacity_message.config(
        text=f'{ward} now has {new_rooms} room(s) and {new_doctors} doctor(s). Saved.')


def set_selected_resource(enabled):
    """Take the selected room or doctor out of service, or put it back."""
    selected = resource_table.selection()
    if not selected:
        capacity_message.config(text='Select a room or doctor in the table first.')
        return
    resource_id = selected[0]

    # A reserved resource is in use right now. Marking it unavailable would
    # contradict the reservation shown next to it in the same table.
    holder = next((queue_id for queue_id, reservation in assignments.items()
                   if resource_id in (reservation['room_id'], reservation['doctor_id'])),
                  None)
    if holder and not enabled:
        capacity_message.config(
            text=f'{resource_id} is reserved by {holder}. Free it before taking it '
                 f'out of service.')
        return

    storage.set_resource_enabled(database, resource_id, enabled)
    if enabled:
        disabled_resources.discard(resource_id)
    else:
        disabled_resources.add(resource_id)
    rebuild_resources()
    # The rebuild replaced every row, so restore the selection the user had.
    if resource_table.exists(resource_id):
        resource_table.selection_set(resource_id)
    capacity_message.config(
        text=f"{resource_id} is {'back in service' if enabled else 'out of service'}.")


capacity_ward.bind('<<ComboboxSelected>>', show_ward_capacity)
ttk.Button(capacity_box, text='Apply', command=apply_capacity).grid(
    row=0, column=6, sticky='e')

service_row = ttk.Frame(capacity_box)
service_row.grid(row=1, column=0, columnspan=7, sticky='ew', pady=(10, 0))
service_row.columnconfigure(0, weight=1)
service_row.columnconfigure(1, weight=1)
ttk.Button(service_row, text='Take selected out of service',
           command=lambda: set_selected_resource(False)).grid(row=0, column=0,
                                                              sticky='ew', padx=(0, 4))
ttk.Button(service_row, text='Put selected back in service',
           command=lambda: set_selected_resource(True)).grid(row=0, column=1,
                                                             sticky='ew', padx=(4, 0))

capacity_message = ttk.Label(resource_panel, text='', wraplength=480)
capacity_message.grid(row=3, column=0, columnspan=2, sticky='w', pady=(10, 0))
show_ward_capacity()


def assign_selected():
    """Translate a selected table row into a domain-rule call and refresh views."""
    selected = queue_table.selection()  # A tuple of selected row IDs, possibly empty.
    if not selected:
        assignment_message.config(text='Select a waiting case in the table first.')
        return
    # The iid we set while registering is date|ticket. Look up its record in our
    # list instead of trusting text copied from the displayed columns.
    record = next(item for item in patient_records if row_key(item) == selected[0])
    try:
        reservation = assign_patient(record, rooms, doctors, assignments)
    except ValueError as error:
        assignment_message.config(text=str(error))
        messagebox.showwarning('Assignment failed', str(error))
        return
    # Only the visible cell changes. The reservation is not written to the
    # database: nothing can release it yet, so it lasts for this session only.
    refresh_queue_assignments()
    # Say what was reserved and why it was that pair. A reservation lasts for
    # this session; nothing here releases a resource when a session finishes.
    assignment_message.config(
        text=f"Reserved {reservation['room_id']} / {reservation['doctor_id']}. "
             f"First compatible free pair in configured order.")
    refresh_resources()


def selected_record():
    """Return the record for the highlighted row, or None if nothing is chosen."""
    selected = queue_table.selection()
    if not selected:
        return None
    # next(..., None) returns None instead of raising when nothing matches, so a
    # stale selection cannot crash a callback.
    return next((item for item in patient_records if row_key(item) == selected[0]), None)


def show_details(event=None):
    """Open a window with everything stored about one registration.

    Bound to DOUBLE-click rather than single click on purpose. A single click
    selects a row, and selecting is how you choose a case to assign or delete;
    if selecting also opened a window you would have to dismiss it before every
    other action. Double-click to open is the ordinary desktop convention.

    The queue table deliberately hides medical information, because that table
    is visible to anyone glancing at the screen. Here it is shown, because a
    staff member has deliberately asked for one specific patient. That is a
    judgement about who is looking, not an accident.
    """
    record = selected_record()
    if record is None:
        assignment_message.config(text='Select a case first, then double-click it.')
        return

    # Toplevel makes a second window. transient ties it to the main window so it
    # stays in front and minimises with it; grab_set makes it modal, so the
    # underlying table cannot change while its details are on screen.
    details = tk.Toplevel(window)
    details.title(f"Queue {record['queue_id']}")
    details.transient(window)
    details.resizable(False, False)

    body = ttk.Frame(details, padding=18)
    body.pack(fill='both', expand=True)
    body.columnconfigure(1, weight=1)

    ttk.Label(body, text=f"Queue {record['queue_id']}",
              font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, columnspan=2,
                                                  sticky='w', pady=(0, 12))

    reservation = assignments.get(record['queue_id'])
    # A reservation belongs to today's list only, so a same ticket on another
    # date must not appear to share it.
    if reservation and record['appointment_date'] == date.today().isoformat():
        assignment_text = f"{reservation['room_id']} / {reservation['doctor_id']}"
    else:
        assignment_text = 'Waiting - no room or doctor reserved'

    fields = [('Patient name', record['patient_name']),
              ('Appointment date', record['appointment_date']),
              ('Destination ward', f"{record['destination_ward']} "
                                   f"(code {record['ward_code']})"),
              ('Phone number', record['phone_number']),
              ('Assignment', assignment_text)]
    for index, (label, value) in enumerate(fields, start=1):
        ttk.Label(body, text=label + ':').grid(row=index, column=0, sticky='nw',
                                               padx=(0, 12), pady=2)
        ttk.Label(body, text=value, wraplength=320).grid(row=index, column=1,
                                                         sticky='w', pady=2)

    ttk.Label(body, text='Medical history / information:').grid(
        row=6, column=0, columnspan=2, sticky='w', pady=(12, 4))
    notes = tk.Text(body, height=6, width=52, wrap='word', font=('Segoe UI', 10))
    notes.grid(row=7, column=0, columnspan=2, sticky='ew')
    notes.insert('1.0', record['medical_information'] or '(none recorded)')
    # state='disabled' makes the Text read-only. It must be set AFTER inserting,
    # because a disabled Text refuses insertions too.
    notes.configure(state='disabled')

    ttk.Button(body, text='Close', command=details.destroy).grid(
        row=8, column=0, columnspan=2, sticky='ew', pady=(14, 0))
    details.grab_set()


def delete_selected():
    """Delete one registration from the database, the list, and the table."""
    record = selected_record()
    if record is None:
        assignment_message.config(text='Select the case to delete first.')
        return

    # Name the patient in the question. "Delete this record?" invites a reflex
    # yes; naming who disappears gives the user something to check.
    if not messagebox.askyesno(
            'Delete registration',
            f"Delete {record['queue_id']} - {record['patient_name']}, "
            f"{record['appointment_date']}?\n\nThis cannot be undone."):
        return

    storage.delete_registration(database, record['appointment_date'], record['queue_id'])
    patient_records.remove(record)
    queue_table.delete(row_key(record))

    # Free any room and doctor this case was holding. Without this the resources
    # would stay reserved by a patient who no longer exists, and nothing could
    # release them. The date check matters: assignments are keyed by ticket
    # alone, and only today's cases can hold one, so deleting another date's
    # identical ticket must not release today's reservation.
    if record['appointment_date'] == date.today().isoformat():
        if assignments.pop(record['queue_id'], None) is not None:
            refresh_resources()

    assignment_message.config(
        text=f"Deleted {record['queue_id']}. {len(patient_records)} patient(s) remain.")


def import_csv():
    """Read many registrations from a CSV file, all of them or none."""
    path = filedialog.askopenfilename(
        title='Import registrations from CSV',
        filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
    # An empty string means the user cancelled the dialog.
    if not path:
        return

    try:
        # Validate the WHOLE file first. Nothing is written until every row is
        # known to be good, so a bad row cannot leave a half-finished import.
        new_records = read_import_file(path, patient_records)
        storage.save_many(database, new_records)
    except ValueError as error:
        messagebox.showwarning('Import refused', str(error))
        return
    except OSError as error:
        messagebox.showwarning('Import failed', f'Could not read the file.\n{error}')
        return

    for record in new_records:
        patient_records.append(record)
        add_queue_row(record)
    result_label.config(text=f'Imported {len(new_records)} patient(s). '
                             f'{len(patient_records)} in the queue.')
    messagebox.showinfo('Import complete',
                        f'{len(new_records)} registration(s) added.\n'
                        'Reservations are not part of an import.')


def clear_all():
    """Empty the saved queue completely, after two deliberate confirmations."""
    if not patient_records:
        result_label.config(text='There is nothing saved to clear.')
        return
    # Two questions, because this cannot be undone and one reflex click should
    # not be enough to lose everything.
    if not messagebox.askyesno(
            'Clear saved queue',
            f'Delete ALL {len(patient_records)} saved registration(s)?\n\n'
            'This cannot be undone.'):
        return
    if not messagebox.askokcancel('Clear saved queue', 'Really delete everything?'):
        return

    removed = storage.delete_all_registrations(database)
    # clear() empties the EXISTING list, so every other reference still sees it.
    patient_records.clear()
    queue_table.delete(*queue_table.get_children())
    assignments.clear()
    refresh_resources()
    result_label.config(text=f'Cleared {removed} saved registration(s).')


def manual_assign():
    """Let a staff member choose which room and doctor a case gets.

    The chooser is built from `available_resources`, the same function the rule
    uses, so it can never offer a pair that would then be refused. Manual mode
    overrides WHICH pair is used, never WHETHER the pair is legal: a staff
    member knows things the program does not, but still cannot put two patients
    in one room.
    """
    record = selected_record()
    if record is None:
        assignment_message.config(text='Select the case to assign first.')
        return
    if record['queue_id'] in assignments:
        assignment_message.config(text=f"{record['queue_id']} already has an assignment.")
        return
    if record['appointment_date'] != date.today().isoformat():
        assignment_message.config(
            text='Only cases dated today can be assigned right now.')
        return

    ward = record['destination_ward']
    free_rooms, free_doctors = available_resources(ward, rooms, doctors, assignments)
    if not free_rooms or not free_doctors:
        missing = 'room' if not free_rooms else 'doctor'
        assignment_message.config(
            text=f'No available {missing} in {ward}. Nothing to choose from.')
        return

    chooser = tk.Toplevel(window)
    chooser.title(f"Assign {record['queue_id']}")
    chooser.transient(window)
    chooser.resizable(False, False)
    body = ttk.Frame(chooser, padding=18)
    body.pack(fill='both', expand=True)
    body.columnconfigure(1, weight=1)

    ttk.Label(body, text=f"{record['queue_id']} - {record['patient_name']}",
              font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, columnspan=2,
                                                  sticky='w', pady=(0, 4))
    ttk.Label(body, text=f'{ward}, {record["appointment_date"]}').grid(
        row=1, column=0, columnspan=2, sticky='w', pady=(0, 14))

    ttk.Label(body, text='Room').grid(row=2, column=0, sticky='w', padx=(0, 10), pady=4)
    room_choice = ttk.Combobox(body, state='readonly', width=24,
                               values=[room['id'] for room in free_rooms])
    room_choice.grid(row=2, column=1, sticky='ew', pady=4)
    room_choice.current(0)

    ttk.Label(body, text='Doctor').grid(row=3, column=0, sticky='w', padx=(0, 10), pady=4)
    doctor_choice = ttk.Combobox(body, state='readonly', width=24,
                                 values=[doctor['id'] for doctor in free_doctors])
    doctor_choice.grid(row=3, column=1, sticky='ew', pady=4)
    doctor_choice.current(0)

    problem = ttk.Label(body, text='', wraplength=300)
    problem.grid(row=4, column=0, columnspan=2, sticky='w', pady=(10, 0))

    def confirm():
        try:
            reservation = assign_patient_to(record, rooms, doctors, assignments,
                                            room_choice.get(), doctor_choice.get())
        except ValueError as error:
            # The list could have gone stale if something else took a resource
            # while this window was open, so the rule still gets the last word.
            problem.config(text=str(error))
            return
        refresh_queue_assignments()
        refresh_resources()
        assignment_message.config(
            text=f"Reserved {reservation['room_id']} / {reservation['doctor_id']} "
                 f"for {record['queue_id']}, chosen manually.")
        chooser.destroy()

    buttons = ttk.Frame(body)
    buttons.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(14, 0))
    buttons.columnconfigure(0, weight=1)
    buttons.columnconfigure(1, weight=1)
    ttk.Button(buttons, text='Assign', command=confirm).grid(row=0, column=0,
                                                             sticky='ew', padx=(0, 4))
    ttk.Button(buttons, text='Cancel', command=chooser.destroy).grid(row=0, column=1,
                                                                     sticky='ew',
                                                                     padx=(4, 0))
    chooser.grab_set()


def auto_assign_all():
    """Serve every waiting case for today in arrival order: first come, first served."""
    # patient_records is kept in arrival order, and the database reloads it in
    # that order too, so walking the list front to back IS the queue discipline.
    # The random part of a ticket says nothing about position.
    result = auto_assign(patient_records, rooms, doctors, assignments)
    refresh_queue_assignments()
    refresh_resources()

    if not result['assigned'] and not result['waiting']:
        assignment_message.config(
            text='Nothing to assign. Every case dated today already has a room and doctor.')
        return

    if result['assigned']:
        text = f"Assigned {len(result['assigned'])} case(s) in arrival order."
    else:
        # "Assigned 0 case(s)" reads as though the button half-worked. Say
        # plainly that nothing could be done.
        text = 'Nothing could be assigned.'
    if result['waiting']:
        # Name the first blocked case and its reason. A bare count tells staff
        # that something is wrong without telling them what to do about it.
        first_id, reason = result['waiting'][0]
        text += f" {len(result['waiting'])} still waiting - {first_id}: {reason}"
    assignment_message.config(text=text)


assign_row = ttk.Frame(queue_panel)
assign_row.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(12, 0))
for index in range(3):
    assign_row.columnconfigure(index, weight=1)
assign_button = ttk.Button(assign_row, text='Assign selected', command=assign_selected)
assign_button.grid(row=0, column=0, sticky='ew', padx=(0, 4))
manual_button = ttk.Button(assign_row, text='Choose room/doctor...', command=manual_assign)
manual_button.grid(row=0, column=1, sticky='ew', padx=4)
auto_button = ttk.Button(assign_row, text='Auto-assign all', command=auto_assign_all)
auto_button.grid(row=0, column=2, sticky='ew', padx=(4, 0))

# A child frame keeps these four buttons on one row without giving the whole
# queue panel four columns to align against.
actions = ttk.Frame(queue_panel)
actions.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(8, 0))
for index in range(4):
    actions.columnconfigure(index, weight=1)
details_button = ttk.Button(actions, text='Details', command=show_details)
details_button.grid(row=0, column=0, sticky='ew', padx=(0, 4))
delete_button = ttk.Button(actions, text='Delete', command=delete_selected)
delete_button.grid(row=0, column=1, sticky='ew', padx=4)
import_button = ttk.Button(actions, text='Import CSV...', command=import_csv)
import_button.grid(row=0, column=2, sticky='ew', padx=4)
clear_button = ttk.Button(actions, text='Clear all', command=clear_all)
clear_button.grid(row=0, column=3, sticky='ew', padx=(4, 0))

# bind attaches a handler to an EVENT rather than to a button. '<Double-1>' is
# a double click of mouse button 1. Tkinter passes the event object to the
# handler, which is why show_details accepts an ignored `event` argument.
queue_table.bind('<Double-1>', show_details)

assignment_message = ttk.Label(queue_panel, text='Choose a case to reserve a compatible room and doctor.', wraplength=470)
assignment_message.grid(row=5, column=0, columnspan=2, sticky='w', pady=(10, 0))
refresh_resources()


# 5. READ -> VALIDATE -> GENERATE -> STORE -> DISPLAY
def add_case():
    """Register the form once and show the confirmation popup you added."""
    # Entry/Combobox get() reads their text. Text.get() requires start/end:
    # '1.0' means line 1, character 0; 'end-1c' excludes Tk's final newline.
    # Keyword arguments make the mapping from form fields to parameters clear.
    try:
        record = create_patient_record(
            name=name_entry.get(),
            information=information_text.get('1.0', 'end-1c'),
            date_text=date_entry.get(),
            phone=phone_entry.get(),
            ward=ward_combobox.get(),
            records=patient_records,
        )
    except ValueError as error:
        # A validation/capacity error skips the remaining try block. Catch that
        # specific exception and show its message. Keep the input for correction.
        # The early return prevents creating a table row for invalid data.
        result_label.config(text=str(error))
        messagebox.showwarning('Registration failed', str(error))
        return

    # append changes the EXISTING list; no global declaration is needed because
    # we do not assign a new object to patient_records. The list order records
    # registration order. The random ID is not a priority or sequence number.
    # Save to disk BEFORE showing success. If the write fails, the user is told
    # and no row appears, so the table never claims something was stored that
    # was not. The record is only added to the in-memory list after the write
    # succeeds, keeping the list and the database in step.
    try:
        storage.save_registration(database, record)
    except ValueError as error:
        result_label.config(text=str(error))
        return

    # append changes the EXISTING list; no global declaration is needed because
    # we do not assign a new object to patient_records. The list order records
    # registration order. The random ID is not a priority or sequence number.
    patient_records.append(record)
    add_queue_row(record)
    result_label.config(
        text=f"Last registered: {record['queue_id']} on {record['appointment_date']}.\n"
             f'{len(patient_records)} patient(s) saved.')

    # Clear person-specific fields only AFTER storing, leaving ward/date ready
    # for the next case. A second click now fails name validation, rather than
    # accidentally registering the untouched form again.
    name_entry.delete(0, 'end')
    phone_entry.delete(0, 'end')
    information_text.delete('1.0', 'end')
    name_entry.focus_set()

    # Keep your popup. parent associates it with our window. It shows ticket
    # information without including the medical-history text or phone number.
    messagebox.showinfo(
        'Queue ID Added',
        f"Queue {record['queue_id']} created.\nWard: {record['destination_ward']}\nDate: {record['appointment_date']}",
        parent=window,
    )


# 6. CALLBACK REGISTRATION AND EVENT LOOP
# Passing the function WITHOUT () registers it for a future click.
add_button = ttk.Button(form, text='Register patient and generate queue ID', command=add_case)
add_button.grid(row=10, column=0, sticky='ew')
name_entry.focus_set()

# Like lesson 1, importing app.py creates its widgets but skips mainloop.
# The separate registration module has no such GUI side effects on import.
# mainloop dispatches events and redraws; it does not repeatedly rerun the file.
if __name__ == '__main__':
    window.mainloop()
