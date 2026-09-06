"""A Tkinter view of the refusal ledger, in the main project's house style.

    python ledger_app.py

This is a PROTOTYPE of the proposal in ../INNOVATION.md, not a lesson and not
part of the project. It imports clinic.py and replay.py from this folder and
nothing from the project, so Codex's files are unaffected in both directions.

All data is fictional and simulated. Nothing here measures a real clinic.

LAYOUT follows app.py deliberately, so this reads as a screen the project could
grow rather than as a separate tool:

  - no ttk.Style and no theme_use: the native theme, like the rest of the project
  - a content Frame with padding=24, packed into the root
  - one heading at ('Segoe UI', 20, 'bold'), then a plain instructions label
  - a LabelFrame of controls on the left, a Notebook of tables on the right
  - labels above inputs at pady=(0, 4), inputs at pady=(0, 12), sticky='ew'
  - Treeview with show='headings', height=10, and the same two-way yview/set
    scrollbar wiring app.py uses
  - no colour coding: every row states its kind in a column, as app.py does

DESIGN NOTE. The interface holds no derived state. Every view is recomputed by
replaying the recorded demand whenever the cases or the resources change, so no
two views can disagree. That is affordable only because assignment is
deterministic - the same property that makes the counterfactual exact.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from clinic import WARDS, capacity_refusals, run_from_spec
from replay import counterfactual
from scenario import DAYS, SHORT, SPEC, build_cases


class LedgerApp:
    """The window and everything in it."""

    def __init__(self, window):
        self.window = window
        window.title('Outpatient Scheduler - capacity ledger prototype')
        window.geometry('1220x750')
        window.minsize(1160, 720)

        # The only authoritative state in the application.
        self.cases = []
        self.spec = dict(SPEC)
        self.manual_count = 0

        # pack expands the frame inside the root; grid arranges its children.
        content = ttk.Frame(window, padding=24)
        content.pack(fill='both', expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(2, weight=1)

        heading = ttk.Label(content, text='Capacity ledger',
                            font=('Segoe UI', 20, 'bold'))
        heading.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        instructions = ttk.Label(
            content,
            text=('Every refusal is kept, with the resource that caused it. '
                  'Simulated data: this demonstrates software behaviour only.'),
        )
        instructions.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 20))

        self._build_controls(content)
        self._build_workspace(content)
        self.refresh()

    # -- the left-hand control panel -------------------------------------

    def _build_controls(self, content):
        form = ttk.LabelFrame(content, text='Clinic setup', padding=18)
        form.grid(row=2, column=0, sticky='nsew', padx=(0, 18))
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text='Resources per ward').grid(
            row=0, column=0, sticky='w', pady=(0, 4))

        # A child frame keeps this three-column grid from imposing extra columns
        # on the single-column form - the same reason app.py wraps its medical
        # information Text and scrollbar in a frame of their own.
        table = ttk.Frame(form)
        table.grid(row=1, column=0, sticky='ew', pady=(0, 12))
        table.columnconfigure(0, weight=1)
        ttk.Label(table, text='Rooms').grid(row=0, column=1, padx=6)
        ttk.Label(table, text='Doctors').grid(row=0, column=2, padx=6)

        self.spin_vars = {}
        for row, ward in enumerate(WARDS, start=1):
            rooms, doctors = self.spec[ward]
            ttk.Label(table, text=ward).grid(row=row, column=0, sticky='w', pady=2)
            room_var = tk.IntVar(value=rooms)
            doctor_var = tk.IntVar(value=doctors)
            ttk.Spinbox(table, from_=0, to=12, width=4, textvariable=room_var,
                        command=self.on_spec_change).grid(row=row, column=1, padx=6)
            ttk.Spinbox(table, from_=0, to=12, width=4, textvariable=doctor_var,
                        command=self.on_spec_change).grid(row=row, column=2, padx=6)
            self.spin_vars[ward] = (room_var, doctor_var)

        ttk.Label(form, text='Clinic day').grid(row=2, column=0, sticky='w', pady=(0, 4))
        self.day_var = tk.StringVar(value=DAYS[0])
        ttk.Combobox(form, values=DAYS, textvariable=self.day_var,
                     state='readonly').grid(row=3, column=0, sticky='ew', pady=(0, 12))

        ttk.Label(form, text='Destination ward').grid(row=4, column=0, sticky='w',
                                                      pady=(0, 4))
        self.ward_var = tk.StringVar(value=list(WARDS)[0])
        ttk.Combobox(form, values=list(WARDS), textvariable=self.ward_var,
                     state='readonly').grid(row=5, column=0, sticky='ew', pady=(0, 12))

        self.future_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, variable=self.future_var,
                        text='Dated next week, so it cannot reserve today').grid(
            row=6, column=0, sticky='w', pady=(0, 16))

        ttk.Button(form, text='Present one case',
                   command=self.on_present).grid(row=7, column=0, sticky='ew')
        ttk.Button(form, text='Run the simulated week',
                   command=self.on_run_week).grid(row=8, column=0, sticky='ew',
                                                  pady=(8, 0))
        ttk.Button(form, text='Clear all demand',
                   command=self.on_clear).grid(row=9, column=0, sticky='ew',
                                               pady=(8, 0))

        # The project ends its form with a wrapped status label; so does this.
        self.result_label = ttk.Label(
            form, wraplength=390,
            text='Run the simulated week, then raise a doctor spinbox by one.')
        self.result_label.grid(row=10, column=0, sticky='w', pady=(16, 0))

    # -- the right-hand notebook -----------------------------------------

    def _build_workspace(self, content):
        workspace = ttk.Notebook(content)
        workspace.grid(row=2, column=1, sticky='nsew')

        outcomes = ttk.Frame(workspace, padding=18)
        workspace.add(outcomes, text='Outcomes')
        ledger = ttk.Frame(workspace, padding=18)
        workspace.add(ledger, text='Refusal ledger')
        demand = ttk.Frame(workspace, padding=18)
        workspace.add(demand, text='Unmet demand')
        replay = ttk.Frame(workspace, padding=18)
        workspace.add(replay, text='Capacity replay')

        self._build_outcomes(outcomes)
        self._build_ledger(ledger)
        self._build_demand(demand)
        self._build_replay(replay)

    def _build_outcomes(self, panel):
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        ttk.Label(panel, wraplength=470,
                  text=('Every case in arrival order. A refusal records what was still '
                        'free at that moment: the contrast is the useful part.')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 14))

        self.tree_out = self._table(panel, (
            ('day', 'Day', 78, False), ('case', 'Case', 82, False),
            ('ward', 'Ward', 130, True), ('outcome', 'Outcome', 88, False),
            ('detail', 'Detail', 215, True)))

    def _build_ledger(self, panel):
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        ttk.Label(panel, wraplength=470,
                  text=('A capacity refusal is evidence of unmet demand. A workflow '
                        'refusal is not, and counting them together would inflate the '
                        'measurement until it meant nothing.')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 14))

        # Seven columns is the widest table here, so these are kept tight enough
        # that the window still fits the project's 1220x750 / 1160x720 sizes.
        self.tree_ledger = self._table(panel, (
            ('day', 'Day', 78, False), ('case', 'Case', 82, False),
            ('ward', 'Ward', 115, True), ('constraint', 'Constraint', 102, False),
            ('rooms', 'Rooms idle', 74, False), ('doctors', 'Doctors idle', 80, False),
            ('kind', 'Counts as', 94, True)))

        self.ledger_label = ttk.Label(panel, wraplength=470, text='')
        self.ledger_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10, 0))

    def _build_demand(self, panel):
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)

        self.totals_label = ttk.Label(panel, wraplength=470, text='')
        self.totals_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))

        ttk.Label(panel, wraplength=470,
                  text=('Grouped by the resource that actually bound. The last column '
                        'is what a scheduler never tells you.')).grid(
            row=1, column=0, columnspan=2, sticky='w', pady=(0, 14))

        self.tree_demand = self._table(panel, (
            ('ward', 'Ward', 170, True), ('constraint', 'Constraint', 130, False),
            ('cases', 'Refused', 80, False),
            ('idle', 'While these sat idle', 230, True)), row=2)

    def _build_replay(self, panel):
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(3, weight=1)
        ttk.Label(panel, wraplength=470,
                  text=('The recorded demand replayed against more resources. First-fit '
                        'is deterministic, so this is exactly what that rule would have '
                        'done, not an estimate.')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 14))

        ttk.Label(panel, text='Ward').grid(row=1, column=0, sticky='w', pady=(0, 4))
        self.replay_ward = tk.StringVar(value=list(WARDS)[0])
        chooser = ttk.Combobox(panel, values=list(WARDS), textvariable=self.replay_ward,
                               state='readonly')
        chooser.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 14))
        # Selecting a ward should show that ward, without a second click.
        chooser.bind('<<ComboboxSelected>>', lambda event: self.refresh_replay())

        self.tree_replay = self._table(panel, (
            ('change', 'Change', 140, True), ('absorbed', 'Absorbed', 120, False),
            ('remaining', 'Still refused', 110, False),
            ('lost', 'Reservations lost', 130, False)), row=3)

        self.verdict_label = ttk.Label(panel, wraplength=470, text='')
        self.verdict_label.grid(row=4, column=0, columnspan=2, sticky='w', pady=(12, 0))

    # -- helpers ---------------------------------------------------------

    def _table(self, panel, columns, row=1):
        """A Treeview with a scrollbar, wired the way app.py wires its tables."""
        table = ttk.Treeview(panel, columns=[column[0] for column in columns],
                             show='headings', height=10, selectmode='browse')
        for key, title, width, stretch in columns:
            table.heading(key, text=title)
            table.column(key, width=width, minwidth=max(60, width - 40),
                         stretch=stretch)
        table.grid(row=row, column=0, sticky='nsew')

        scroll = ttk.Scrollbar(panel, orient='vertical', command=table.yview)
        scroll.grid(row=row, column=1, sticky='ns')
        table.configure(yscrollcommand=scroll.set)
        return table

    def _read_spec(self):
        spec = {}
        for ward, (room_var, doctor_var) in self.spin_vars.items():
            try:
                spec[ward] = (max(0, room_var.get()), max(0, doctor_var.get()))
            except tk.TclError:
                spec[ward] = self.spec[ward]   # a half-typed box: keep the old value
        return spec

    @staticmethod
    def _clear(table):
        table.delete(*table.get_children())

    # -- events ----------------------------------------------------------

    def on_spec_change(self):
        self.spec = self._read_spec()
        self.refresh()
        self.result_label.config(
            text='Resources changed. Every view was recomputed by replaying the '
                 'same demand.')

    def on_present(self):
        day = self.day_var.get()
        ward = self.ward_var.get()
        self.manual_count += 1
        self.cases.append({
            'case_ref': f'{SHORT[ward]}-{self.manual_count}m',
            'ward': ward,
            'day': day,
            'appointment_date': '2026-09-14' if self.future_var.get() else day,
        })
        self.refresh()
        self.result_label.config(text=f'Presented one {ward} case on {day}.')

    def on_run_week(self):
        self.cases.extend(build_cases())
        self.refresh()
        self.result_label.config(
            text='Loaded the simulated week. Now raise a doctor spinbox by one and '
                 'watch unmet demand fall.')

    def on_clear(self):
        # The project asks before an action the user cannot undo; so does this.
        if self.cases and not messagebox.askyesno(
                'Clear all demand',
                'Discard every case presented so far? The ledger will be empty.'):
            return
        self.cases = []
        self.manual_count = 0
        self.refresh()
        self.result_label.config(text='Cleared all demand.')

    # -- rendering -------------------------------------------------------

    def refresh(self):
        """Recompute every view from (cases, spec). The only update path."""
        self.ledger = (run_from_spec(self.cases, self.spec) if self.cases
                       else {'assigned': [], 'refusals': [], 'events': []})
        self.refresh_outcomes()
        self.refresh_ledger()
        self.refresh_demand()
        self.refresh_replay()

    def refresh_outcomes(self):
        self._clear(self.tree_out)
        for item in self.ledger['events']:
            if item['outcome'] == 'assigned':
                outcome = 'assigned'
                detail = f'{item["room_id"]} with {item["doctor_id"]}'
            else:
                outcome = item['code']
                detail = (f'{item["rooms_free"]} room(s) and '
                          f'{item["doctors_free"]} doctor(s) still free'
                          if item['is_capacity'] else item['detail'])
            self.tree_out.insert('', 'end', values=(
                item['day'], item['case_ref'], item['ward'], outcome, detail))
        rows = self.tree_out.get_children()
        if rows:
            self.tree_out.see(rows[-1])

    def refresh_ledger(self):
        self._clear(self.tree_ledger)
        for item in self.ledger['refusals']:
            capacity = item['is_capacity']
            self.tree_ledger.insert('', 'end', values=(
                item['day'], item['case_ref'], item['ward'], item['code'],
                item['rooms_free'] if capacity else '-',
                item['doctors_free'] if capacity else '-',
                'unmet demand' if capacity else 'not capacity'))
        capacity = capacity_refusals(self.ledger)
        workflow = len(self.ledger['refusals']) - len(capacity)
        self.ledger_label.config(
            text=f'{len(capacity)} capacity refusals counted as unmet demand. '
                 f'{workflow} workflow refusals excluded.')

    def refresh_demand(self):
        capacity = capacity_refusals(self.ledger)
        self.totals_label.config(
            text=(f'{len(self.cases)} cases presented.   '
                  f'{len(self.ledger["assigned"])} reservations made.   '
                  f'{len(capacity)} turned away for want of a resource.'))

        self._clear(self.tree_demand)
        grouped = {}
        for item in capacity:
            grouped.setdefault((item['ward'], item['code']), []).append(item)
        for (ward, code), items in sorted(grouped.items()):
            example = items[0]
            idle = (f'{example["rooms_free"]} room(s) standing empty'
                    if code == 'no_doctor'
                    else f'{example["doctors_free"]} doctor(s) with no room to use')
            self.tree_demand.insert('', 'end', values=(ward, code, len(items), idle))

    def refresh_replay(self):
        self._clear(self.tree_replay)
        ward = self.replay_ward.get()
        if not self.cases:
            self.verdict_label.config(
                text='Present some cases first, or run the simulated week.')
            return

        refused = len([r for r in capacity_refusals(self.ledger) if r['ward'] == ward])
        results = {}
        for label, options in (('+1 doctor', {'extra_doctors': 1}),
                               ('+1 room', {'extra_rooms': 1}),
                               ('+1 of each', {'extra_rooms': 1, 'extra_doctors': 1}),
                               ('+2 doctors', {'extra_doctors': 2}),
                               ('+2 rooms', {'extra_rooms': 2})):
            result = counterfactual(self.cases, self.spec, ward, **options)
            results[label] = len(result['absorbed'])
            self.tree_replay.insert('', 'end', values=(
                label, f'{results[label]} of {refused}',
                refused - results[label], len(result['lost'])))

        if refused == 0:
            self.verdict_label.config(text=f'{ward} refused nothing. Nothing to absorb.')
            return

        doctor, room = results['+1 doctor'], results['+1 room']
        if doctor and not room:
            text = (f'An extra room in {ward} would have absorbed nothing at all. '
                    f'Rooms were never the constraint here, so buying space would '
                    f'have been money spent on a room that was already empty.')
        elif room and not doctor:
            text = (f'An extra doctor in {ward} would have absorbed nothing. The room '
                    f'is the constraint; the doctors were already idle.')
        elif room or doctor:
            text = (f'Both help in {ward}: one more doctor absorbs {doctor}, one more '
                    f'room absorbs {room}. Neither alone is the whole story.')
        else:
            text = (f'Neither one more room nor one more doctor absorbs anything in '
                    f'{ward}. The refusals have another cause; check the ledger.')
        self.verdict_label.config(text=text)


def main():
    window = tk.Tk()
    LedgerApp(window)
    window.mainloop()


if __name__ == '__main__':
    main()
