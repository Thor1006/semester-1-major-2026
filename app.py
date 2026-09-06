"""Lesson 3: registration plus immediate room and doctor reservations.

Your fully annotated lesson 1, including the popup you added, is preserved in
lessons/lesson_01.py. Lesson 2 is preserved in lessons/lesson_02/.
"""

# 1. IMPORTS AND DATA
# tkinter controls the window, ttk provides themed widgets, and messagebox
# retains your confirmation popup. date supplies the default appointment date.
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

# Import our own module using its filename without .py. It owns validation and
# ID generation; this file owns the visible interface and its event handling.
from registration import WARD_CODES, create_patient_record
from assignment import make_demo_resources, assign_patient

# This LIST holds one dictionary per successful registration, in insertion order.
# It is RAM storage: closing the app loses records and knowledge of used IDs.
# Nothing is written to disk, logged, or transmitted to an external service.
patient_records = []
# Unpack the two lists returned by the factory. The separate dictionary maps
# queue IDs to reservations; its presence/absence defines reserved/waiting state.
rooms, doctors = make_demo_resources()
assignments = {}


# 2. WINDOW AND CONTAINERS
# Calling Tk constructs the root; assignment binds a name to the object.
# Its methods set the title, requested starting dimensions, and minimum size.
window = tk.Tk()
window.title('Outpatient Scheduler - Patient registration')
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
    text='Use fictional patient details for this lesson. Records stay in memory until the window closes.',
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

format_label = ttk.Label(
    queue_panel,
    text='Select a case dated today, then assign a room and doctor.\nQ0147 = Q + ward 01 + random 47.\n100 IDs per ward per session; random digits do not set priority.',
    wraplength=390,
)
format_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(14, 0))
result_label = ttk.Label(form, text='Complete the required fields to generate a queue ID.', wraplength=390)
# Row 10 is reserved for the button constructed after its callback definition.
result_label.grid(row=11, column=0, sticky='w', pady=(12, 0))

# This second table is a VIEW of configured resources and current reservations.
# Availability is derived from assignments, so both views use the same state.
resource_panel.columnconfigure(0, weight=1)
resource_panel.rowconfigure(1, weight=1)
ttk.Label(resource_panel, text='Example resources: two rooms and two doctors per ward.\nReservations last for this session; session completion comes later.', wraplength=480).grid(row=0, column=0, sticky='w', pady=(0, 14))
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
            resource_table.insert('', 'end', values=(resource['id'], ward, state))


def assign_selected():
    """Translate a selected table row into a domain-rule call and refresh views."""
    selected = queue_table.selection()  # A tuple of selected row IDs, possibly empty.
    if not selected:
        assignment_message.config(text='Select a waiting case in the table first.')
        return
    # The iid we set while registering is the full queue ID. Look up its record
    # in our list instead of trusting text copied from the displayed columns.
    record = next(item for item in patient_records if item['queue_id'] == selected[0])
    try:
        reservation = assign_patient(record, rooms, doctors, assignments)
    except ValueError as error:
        assignment_message.config(text=str(error))
        return
    queue_table.set(selected[0], 'assignment', f"{reservation['room_id']} / {reservation['doctor_id']}")
    assignment_message.config(text=f"Reserved {reservation['room_id']} and {reservation['doctor_id']} for {selected[0]}.")
    refresh_resources()


assign_button = ttk.Button(queue_panel, text='Assign selected case', command=assign_selected)
assign_button.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(12, 0))
assignment_message = ttk.Label(queue_panel, text='Choose a case to reserve a compatible room and doctor.', wraplength=470)
assignment_message.grid(row=4, column=0, columnspan=2, sticky='w', pady=(10, 0))
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
        return

    # append changes the EXISTING list; no global declaration is needed because
    # we do not assign a new object to patient_records. The list order records
    # registration order. The random ID is not a priority or sequence number.
    patient_records.append(record)
    queue_table.insert(
        '', 'end', iid=record['queue_id'],
        values=(record['queue_id'], record['destination_ward'], record['appointment_date'], 'Waiting'),
    )
    # '' means a top-level row, 'end' appends it, and iid is the unique row key.
    # see scrolls the new row into view if the table has become longer.
    queue_table.see(record['queue_id'])
    result_label.config(text=f"Last registered: {record['queue_id']}\n{len(patient_records)} patient(s) in this session.")

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
