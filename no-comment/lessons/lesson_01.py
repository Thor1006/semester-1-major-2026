"""Lesson 1: read a queue ID and respond to a button click."""


import tkinter as tk

from tkinter import ttk


from tkinter import messagebox


window = tk.Tk()

window.title('Outpatient Scheduler - Lesson 1')

window.geometry('500x300')

window.minsize(420, 280)

content = ttk.Frame(window, padding=24)

content.pack(fill='both', expand=True)

content.columnconfigure(0, weight=1)

heading = ttk.Label(content, text='Front-desk check-in', font=('Segoe UI', 18, 'bold'))

heading.grid(row=0, column=0, sticky='w', pady=(0, 8))

instructions = ttk.Label(content, text='Enter a fictional queue ID, such as Q001.')
instructions.grid(row=1, column=0, sticky='w', pady=(0, 16))

queue_label = ttk.Label(content, text='Queue ID')
queue_label.grid(row=2, column=0, sticky='w', pady=(0, 4))

queue_entry = ttk.Entry(content)

queue_entry.grid(row=3, column=0, sticky='ew', pady=(0, 12))

result_label = ttk.Label(content, text='Ready for a queue ID.', wraplength=360)

result_label.grid(row=5, column=0, sticky='w', pady=(12, 0))


def add_case():
    """This callback runs when the Add button is clicked."""

    queue_id = queue_entry.get().strip()

    if not queue_id:

        result_label.config(text='Please enter a queue ID.')

        return

    messagebox.showinfo("Queue ID Added", f"Added {queue_id} to the queue.")


add_button = ttk.Button(content, text='Add', command=add_case)

add_button.grid(row=4, column=0, sticky='ew')

queue_entry.focus_set()

if __name__ == '__main__':

    window.mainloop()
