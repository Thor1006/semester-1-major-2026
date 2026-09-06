"""Lesson 2: patient registration with an automatic ward-based queue ID.

Your fully annotated lesson 1, including the popup you added, is preserved in
lessons/lesson_01.py. This file builds on those widgets and callbacks.
"""

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from registration import WARD_CODES, create_patient_record

patient_records = []


window = tk.Tk()
window.title('Outpatient Scheduler - Patient registration')
window.geometry('1060x730')
window.minsize(980, 700)

content = ttk.Frame(window, padding=24)
content.pack(fill='both', expand=True)
content.columnconfigure(0, weight=1)
content.columnconfigure(1, weight=1)
content.rowconfigure(2, weight=1)

heading = ttk.Label(content, text='Front-desk registration', font=('Segoe UI', 20, 'bold'))
heading.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
instructions = ttk.Label(
    content,
    text='Use fictional patient details for this lesson. Records stay in memory until the window closes.',
)
instructions.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 20))

form = ttk.LabelFrame(content, text='Patient information', padding=18)
form.grid(row=2, column=0, sticky='nsew', padx=(0, 18))
form.columnconfigure(0, weight=1)

queue_panel = ttk.LabelFrame(content, text='Registered queue - this session', padding=18)
queue_panel.grid(row=2, column=1, sticky='nsew')
queue_panel.columnconfigure(0, weight=1)
queue_panel.rowconfigure(1, weight=1)


name_label = ttk.Label(form, text='Patient name *')
name_label.grid(row=0, column=0, sticky='w', pady=(0, 4))
name_entry = ttk.Entry(form)
name_entry.grid(row=1, column=0, sticky='ew', pady=(0, 12))

information_label = ttk.Label(form, text='Medical history / information (optional)')
information_label.grid(row=2, column=0, sticky='w', pady=(0, 4))
information_frame = ttk.Frame(form)
information_frame.grid(row=3, column=0, sticky='ew', pady=(0, 12))
information_frame.columnconfigure(0, weight=1)
information_text = tk.Text(information_frame, height=5, width=35, wrap='word', font=('Segoe UI', 10))
information_text.grid(row=0, column=0, sticky='ew')
information_scroll = ttk.Scrollbar(information_frame, orient='vertical', command=information_text.yview)
information_scroll.grid(row=0, column=1, sticky='ns')
information_text.configure(yscrollcommand=information_scroll.set)

date_label = ttk.Label(form, text='Appointment date * (YYYY-MM-DD)')
date_label.grid(row=4, column=0, sticky='w', pady=(0, 4))
date_entry = ttk.Entry(form)
date_entry.grid(row=5, column=0, sticky='ew', pady=(0, 12))
date_entry.insert(0, date.today().isoformat())

phone_label = ttk.Label(form, text='Phone number *')
phone_label.grid(row=6, column=0, sticky='w', pady=(0, 4))
phone_entry = ttk.Entry(form)
phone_entry.grid(row=7, column=0, sticky='ew', pady=(0, 12))

ward_label = ttk.Label(form, text='Destination ward *')
ward_label.grid(row=8, column=0, sticky='w', pady=(0, 4))
ward_combobox = ttk.Combobox(form, values=list(WARD_CODES), state='readonly')
ward_combobox.grid(row=9, column=0, sticky='ew', pady=(0, 16))


ward_legend = ' | '.join(f'{code}: {ward}' for ward, code in WARD_CODES.items())
legend_label = ttk.Label(queue_panel, text=ward_legend, wraplength=390)
legend_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 14))

queue_table = ttk.Treeview(queue_panel, columns=('queue_id', 'ward', 'date'), show='headings', height=12)
queue_table.heading('queue_id', text='Queue ID')
queue_table.heading('ward', text='Ward')
queue_table.heading('date', text='Date')
queue_table.column('queue_id', width=85, minwidth=70, stretch=False)
queue_table.column('ward', width=170, minwidth=100)
queue_table.column('date', width=105, minwidth=90, stretch=False)
queue_table.grid(row=1, column=0, sticky='nsew')
queue_scroll = ttk.Scrollbar(queue_panel, orient='vertical', command=queue_table.yview)
queue_scroll.grid(row=1, column=1, sticky='ns')
queue_table.configure(yscrollcommand=queue_scroll.set)

format_label = ttk.Label(
    queue_panel,
    text='Q0147 = Q + ward 01 + random 47\nSame ward prefix is allowed; full IDs stay unique.\n100 IDs per ward per session. Rooms are assigned later.',
    wraplength=390,
)
format_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(14, 0))
result_label = ttk.Label(form, text='Complete the required fields to generate a queue ID.', wraplength=390)
result_label.grid(row=11, column=0, sticky='w', pady=(12, 0))


def add_case():
    """Register the form once and show the confirmation popup you added."""
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
        result_label.config(text=str(error))
        return

    patient_records.append(record)
    queue_table.insert(
        '', 'end', iid=record['queue_id'],
        values=(record['queue_id'], record['destination_ward'], record['appointment_date']),
    )
    queue_table.see(record['queue_id'])
    result_label.config(text=f"Last registered: {record['queue_id']}\n{len(patient_records)} patient(s) in this session.")

    name_entry.delete(0, 'end')
    phone_entry.delete(0, 'end')
    information_text.delete('1.0', 'end')
    name_entry.focus_set()

    messagebox.showinfo(
        'Queue ID Added',
        f"Queue {record['queue_id']} created.\nWard: {record['destination_ward']}\nDate: {record['appointment_date']}",
        parent=window,
    )


add_button = ttk.Button(form, text='Register patient and generate queue ID', command=add_case)
add_button.grid(row=10, column=0, sticky='ew')
name_entry.focus_set()

if __name__ == '__main__':
    window.mainloop()
