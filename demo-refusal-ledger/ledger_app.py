"""A Tkinter view of the refusal ledger: what the app could look like finished.

    python ledger_app.py

This is a PROTOTYPE of the proposal in ../INNOVATION.md, not a lesson and not
part of the project. It imports clinic.py and replay.py from this folder and
nothing from the project, so Codex's files are unaffected in both directions.

All data is fictional and simulated. Nothing here measures a real clinic.

One design note worth reading before the code. The entire interface is a pure
function of two things: the list of cases presented, and the resource
specification. Every view is recomputed by replaying that demand from scratch
whenever either changes. No view holds its own copy of the state, so no view can
drift out of agreement with another one. That is only affordable because
assignment is deterministic - the same property that makes the counterfactual
exact also makes the UI cheap to keep honest.
"""

import tkinter as tk
from tkinter import ttk

from clinic import WARDS, capacity_refusals, run_from_spec, served_refs
from replay import counterfactual
from scenario import DAYS, SHORT, SPEC, build_cases

BG = '#f7f7f9'
ACCENT = '#1f4e79'
MUTED = '#6b6b76'
WARN = '#a8322d'
GOOD = '#1e6b3a'


class LedgerApp:
    """The window and everything in it."""

    def __init__(self, root):
        self.root = root
        root.title('Outpatient capacity ledger - prototype')
        root.geometry('1180x760')
        root.minsize(990, 725)
        root.configure(bg=BG)

        # ---- state -----------------------------------------------------
        # These two are the ONLY authoritative state in the application.
        self.cases = []
        self.spec = dict(SPEC)
        self.manual_count = 0

        self._build_styles()
        self._build_header()
        self._build_tabs()
        self._build_status()

        self.refresh()

    # -- construction ----------------------------------------------------

    def _build_styles(self):
        style = ttk.Style()
        # 'clam' honours background colours on Windows, unlike the native theme.
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('.', background=BG)
        style.configure('TFrame', background=BG)
        style.configure('TLabelframe', background=BG)
        style.configure('TLabelframe.Label', background=BG, foreground=ACCENT,
                        font=('Segoe UI', 10, 'bold'))
        style.configure('TLabel', background=BG)
        style.configure('Title.TLabel', font=('Segoe UI', 17, 'bold'), foreground=ACCENT)
        style.configure('Sub.TLabel', font=('Segoe UI', 9), foreground=MUTED)
        style.configure('Head.TLabel', font=('Segoe UI', 11, 'bold'), foreground=ACCENT)
        style.configure('Big.TLabel', font=('Segoe UI', 22, 'bold'), foreground=ACCENT)
        style.configure('Verdict.TLabel', font=('Segoe UI', 10), foreground=WARN)
        style.configure('Treeview', rowheight=23, font=('Segoe UI', 9))
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))

    def _build_header(self):
        head = ttk.Frame(self.root, padding=(18, 14, 18, 6))
        head.pack(fill='x')
        ttk.Label(head, text='Outpatient capacity ledger',
                  style='Title.TLabel').pack(anchor='w')
        ttk.Label(head, style='Sub.TLabel',
                  text=('Prototype of INNOVATION.md - every refusal is kept, with the '
                        'resource that caused it.   Simulated data: demonstrates software '
                        'behaviour only.')).pack(anchor='w')

    def _build_tabs(self):
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill='both', expand=True, padx=18, pady=(8, 4))

        self.tab_clinic = ttk.Frame(self.tabs, padding=14)
        self.tab_ledger = ttk.Frame(self.tabs, padding=14)
        self.tab_demand = ttk.Frame(self.tabs, padding=14)
        self.tab_replay = ttk.Frame(self.tabs, padding=14)

        self.tabs.add(self.tab_clinic, text='  Clinic and demand  ')
        self.tabs.add(self.tab_ledger, text='  Refusal ledger  ')
        self.tabs.add(self.tab_demand, text='  Unmet demand  ')
        self.tabs.add(self.tab_replay, text='  Capacity replay  ')

        self._build_clinic_tab()
        self._build_ledger_tab()
        self._build_demand_tab()
        self._build_replay_tab()

    def _build_status(self):
        self.status = tk.StringVar(value='Ready.')
        bar = ttk.Frame(self.root, padding=(18, 4, 18, 10))
        bar.pack(fill='x')
        ttk.Label(bar, textvariable=self.status, style='Sub.TLabel').pack(anchor='w')

    # -- tab 1: clinic and demand ---------------------------------------

    def _build_clinic_tab(self):
        frame = self.tab_clinic
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        left = ttk.Frame(frame)
        left.grid(row=0, column=0, sticky='ns', padx=(0, 16))

        # Resources. Changing a spinbox replays the whole week immediately, so
        # the effect of one more doctor is visible without leaving the tab.
        res = ttk.Labelframe(left, text='Resources per ward', padding=12)
        res.pack(fill='x')
        ttk.Label(res, text='Rooms', style='Sub.TLabel').grid(row=0, column=1, padx=4)
        ttk.Label(res, text='Doctors', style='Sub.TLabel').grid(row=0, column=2, padx=4)

        self.spin_vars = {}
        for row, ward in enumerate(WARDS, start=1):
            rooms, doctors = self.spec[ward]
            ttk.Label(res, text=ward).grid(row=row, column=0, sticky='w', pady=3)
            room_var = tk.IntVar(value=rooms)
            doc_var = tk.IntVar(value=doctors)
            ttk.Spinbox(res, from_=0, to=12, width=4, textvariable=room_var,
                        command=self.on_spec_change).grid(row=row, column=1, padx=4)
            ttk.Spinbox(res, from_=0, to=12, width=4, textvariable=doc_var,
                        command=self.on_spec_change).grid(row=row, column=2, padx=4)
            self.spin_vars[ward] = (room_var, doc_var)

        # Demand.
        demand = ttk.Labelframe(left, text='Present a case', padding=12)
        demand.pack(fill='x', pady=(14, 0))
        demand.columnconfigure(1, weight=1)

        ttk.Label(demand, text='Clinic day').grid(row=0, column=0, sticky='w', pady=3)
        self.day_var = tk.StringVar(value=DAYS[0])
        ttk.Combobox(demand, values=DAYS, textvariable=self.day_var, state='readonly',
                     width=14).grid(row=0, column=1, sticky='ew', pady=3)

        ttk.Label(demand, text='Ward').grid(row=1, column=0, sticky='w', pady=3)
        self.ward_var = tk.StringVar(value=list(WARDS)[0])
        ttk.Combobox(demand, values=list(WARDS), textvariable=self.ward_var,
                     state='readonly', width=18).grid(row=1, column=1, sticky='ew', pady=3)

        self.future_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(demand, variable=self.future_var,
                        text='Dated next week (a workflow refusal)').grid(
            row=2, column=0, columnspan=2, sticky='w', pady=(6, 2))

        ttk.Button(demand, text='Present this case', command=self.on_present).grid(
            row=3, column=0, columnspan=2, sticky='ew', pady=(10, 2))

        actions = ttk.Labelframe(left, text='Scenario', padding=12)
        actions.pack(fill='x', pady=(14, 0))
        ttk.Button(actions, text='Run the simulated week',
                   command=self.on_run_week).pack(fill='x')
        ttk.Button(actions, text='Clear all demand',
                   command=self.on_clear).pack(fill='x', pady=(6, 0))

        hint = ttk.Label(left, style='Sub.TLabel', wraplength=250, justify='left',
                         text=('Present more cases than a ward can take, then watch the '
                               'right-hand column: it records what was still free at the '
                               'moment the case was turned away.'))
        hint.pack(fill='x', pady=(14, 0))

        # Outcome log.
        right = ttk.Labelframe(frame, text='Outcomes, in arrival order', padding=10)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        columns = ('day', 'case', 'ward', 'outcome', 'detail')
        self.tree_out = self._tree(right, columns,
                                   {'day': ('Day', 80), 'case': ('Case', 95),
                                    'ward': ('Ward', 125), 'outcome': ('Outcome', 85),
                                    'detail': ('Detail', 215)}, flex='detail')

    # -- tab 2: the ledger ----------------------------------------------

    def _build_ledger_tab(self):
        frame = self.tab_ledger
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, style='Sub.TLabel', justify='left', wraplength=760,
                  text=('Every refusal, kept rather than discarded. A capacity refusal is '
                        'evidence of unmet demand. A workflow refusal - a duplicate click, '
                        'or a case dated for another day - is not, and counting the two '
                        'together would inflate the measurement until it meant nothing.')
                  ).grid(row=0, column=0, sticky='w', pady=(0, 10))

        box = ttk.Frame(frame)
        box.grid(row=1, column=0, sticky='nsew')
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        columns = ('day', 'case', 'ward', 'constraint', 'rooms', 'doctors', 'kind')
        self.tree_ledger = self._tree(box, columns,
                                      {'day': ('Day', 80), 'case': ('Case', 95),
                                       'ward': ('Ward', 130), 'constraint': ('Binding constraint', 125),
                                       'rooms': ('Rooms idle', 80), 'doctors': ('Doctors idle', 85),
                                       'kind': ('Counts as', 110)}, flex='kind')

        self.ledger_note = ttk.Label(frame, style='Head.TLabel', text='')
        self.ledger_note.grid(row=2, column=0, sticky='w', pady=(10, 0))

    # -- tab 3: unmet demand --------------------------------------------

    def _build_demand_tab(self):
        frame = self.tab_demand
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        cards = ttk.Frame(frame)
        cards.grid(row=0, column=0, sticky='ew', pady=(0, 14))
        self.card_vars = {}
        for index, (key, label) in enumerate((('presented', 'Cases presented'),
                                              ('served', 'Reservations made'),
                                              ('unmet', 'Unmet demand'),
                                              ('workflow', 'Workflow refusals'))):
            card = ttk.Labelframe(cards, text=label, padding=(16, 8))
            card.grid(row=0, column=index, padx=(0, 12), sticky='w')
            var = tk.StringVar(value='0')
            ttk.Label(card, textvariable=var, style='Big.TLabel').pack()
            self.card_vars[key] = var

        ttk.Label(frame, style='Sub.TLabel', justify='left', wraplength=760,
                  text=('Unmet demand grouped by the resource that actually bound. The last '
                        'column is the part a scheduler never tells you: what sat idle while '
                        'the case was turned away.')).grid(row=1, column=0, sticky='w',
                                                           pady=(0, 10))

        box = ttk.Frame(frame)
        box.grid(row=2, column=0, sticky='nsew')
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        columns = ('ward', 'constraint', 'cases', 'idle')
        self.tree_demand = self._tree(box, columns,
                                      {'ward': ('Ward', 170), 'constraint': ('Binding constraint', 140),
                                       'cases': ('Cases refused', 100),
                                       'idle': ('While these sat idle', 240)}, flex='idle')

    # -- tab 4: replay ---------------------------------------------------

    def _build_replay_tab(self):
        frame = self.tab_replay
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        ttk.Label(frame, style='Sub.TLabel', justify='left', wraplength=760,
                  text=('The recorded demand, replayed against more resources. Because '
                        'assignment is deterministic first-fit, this is exactly what that '
                        'rule would have done - not a statistical estimate.')
                  ).grid(row=0, column=0, sticky='w', pady=(0, 10))

        controls = ttk.Frame(frame)
        controls.grid(row=1, column=0, sticky='w', pady=(0, 12))
        ttk.Label(controls, text='Ward').pack(side='left')
        self.replay_ward = tk.StringVar(value=list(WARDS)[0])
        ttk.Combobox(controls, values=list(WARDS), textvariable=self.replay_ward,
                     state='readonly', width=20).pack(side='left', padx=(6, 16))
        ttk.Button(controls, text='Replay this ward',
                   command=self.refresh_replay).pack(side='left')

        box = ttk.Frame(frame)
        box.grid(row=2, column=0, sticky='nsew')
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        columns = ('change', 'absorbed', 'remaining', 'lost')
        self.tree_replay = self._tree(box, columns,
                                      {'change': ('Change', 150),
                                       'absorbed': ('Refusals absorbed', 140),
                                       'remaining': ('Still refused', 120),
                                       'lost': ('Reservations lost', 130)}, flex='change')

        self.verdict = ttk.Label(frame, style='Verdict.TLabel', wraplength=760,
                                 justify='left', text='')
        self.verdict.grid(row=3, column=0, sticky='w', pady=(12, 0))

    # -- helpers ---------------------------------------------------------

    def _tree(self, parent, columns, spec, flex=None):
        """Build a Treeview with a vertical scrollbar in a two-column grid.

        Only the `flex` column stretches. The rest keep their width, so the
        table stays inside the window at the minimum size and the spare space
        goes to the one column that benefits from it.
        """
        tree = ttk.Treeview(parent, columns=columns, show='headings',
                            selectmode='browse', height=8)
        for key in columns:
            heading, width = spec[key]
            tree.heading(key, text=heading)
            anchor = 'center' if key in ('rooms', 'doctors', 'cases', 'absorbed',
                                         'remaining', 'lost') else 'w'
            tree.column(key, width=width, minwidth=60, anchor=anchor,
                        stretch=(key == flex))
        tree.grid(row=0, column=0, sticky='nsew')

        bar = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        bar.grid(row=0, column=1, sticky='ns')
        tree.configure(yscrollcommand=bar.set)

        # Colour carries no information on its own here; every row also states
        # its kind in text, so the table stays readable without relying on hue.
        tree.tag_configure('capacity', foreground=WARN)
        tree.tag_configure('workflow', foreground=MUTED)
        tree.tag_configure('good', foreground=ACCENT)
        return tree

    def _read_spec(self):
        """Read the spinboxes back into the resource specification."""
        spec = {}
        for ward, (room_var, doc_var) in self.spin_vars.items():
            try:
                spec[ward] = (max(0, room_var.get()), max(0, doc_var.get()))
            except tk.TclError:
                spec[ward] = self.spec[ward]     # a half-typed box: keep the old value
        return spec

    @staticmethod
    def _clear(tree):
        tree.delete(*tree.get_children())

    # -- events ----------------------------------------------------------

    def on_spec_change(self):
        self.spec = self._read_spec()
        self.refresh()
        self.status.set('Resources changed. Every view was recomputed by replaying '
                        'the same demand.')

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
        self.status.set(f'Presented one {ward} case on {day}.')

    def on_run_week(self):
        self.cases.extend(build_cases())
        self.refresh()
        self.status.set('Loaded the simulated five-day week.')

    def on_clear(self):
        self.cases = []
        self.manual_count = 0
        self.refresh()
        self.status.set('Cleared all demand.')

    # -- rendering -------------------------------------------------------

    def refresh(self):
        """Recompute every view from (cases, spec). The only update path."""
        self.ledger = run_from_spec(self.cases, self.spec) if self.cases else {
            'assigned': [], 'refusals': [], 'events': []}
        self.refresh_outcomes()
        self.refresh_ledger()
        self.refresh_demand()
        self.refresh_replay()

    def refresh_outcomes(self):
        self._clear(self.tree_out)
        for item in self.ledger['events']:
            if item['outcome'] == 'assigned':
                detail = f'{item["room_id"]} with {item["doctor_id"]}'
                tag = 'good'
                outcome = 'assigned'
            else:
                if item['is_capacity']:
                    detail = (f'{item["rooms_free"]} room(s) and '
                              f'{item["doctors_free"]} doctor(s) still free')
                    tag = 'capacity'
                else:
                    detail = item['detail']
                    tag = 'workflow'
                outcome = item['code']
            self.tree_out.insert('', 'end', tags=(tag,), values=(
                item['day'], item['case_ref'], item['ward'], outcome, detail))
        children = self.tree_out.get_children()
        if children:
            self.tree_out.see(children[-1])

    def refresh_ledger(self):
        self._clear(self.tree_ledger)
        for item in self.ledger['refusals']:
            capacity = item['is_capacity']
            self.tree_ledger.insert('', 'end', tags=('capacity' if capacity else 'workflow',),
                                    values=(item['day'], item['case_ref'], item['ward'],
                                            item['code'],
                                            item['rooms_free'] if capacity else '-',
                                            item['doctors_free'] if capacity else '-',
                                            'unmet demand' if capacity else 'not capacity'))
        capacity = capacity_refusals(self.ledger)
        workflow = len(self.ledger['refusals']) - len(capacity)
        self.ledger_note.config(
            text=f'{len(capacity)} capacity refusals counted as unmet demand.   '
                 f'{workflow} workflow refusals excluded.')

    def refresh_demand(self):
        capacity = capacity_refusals(self.ledger)
        self.card_vars['presented'].set(str(len(self.cases)))
        self.card_vars['served'].set(str(len(self.ledger['assigned'])))
        self.card_vars['unmet'].set(str(len(capacity)))
        self.card_vars['workflow'].set(
            str(len(self.ledger['refusals']) - len(capacity)))

        self._clear(self.tree_demand)
        grouped = {}
        for item in capacity:
            key = (item['ward'], item['code'])
            grouped.setdefault(key, []).append(item)
        for (ward, code), items in sorted(grouped.items()):
            example = items[0]
            if code == 'no_doctor':
                idle = f'{example["rooms_free"]} room(s) standing empty'
            else:
                idle = f'{example["doctors_free"]} doctor(s) with no room to use'
            self.tree_demand.insert('', 'end', tags=('capacity',),
                                    values=(ward, code, len(items), idle))

    def refresh_replay(self):
        self._clear(self.tree_replay)
        self.verdict.config(text='')
        ward = self.replay_ward.get()
        if not self.cases:
            self.verdict.config(text='Present some cases first, or run the simulated week.')
            return

        refused = len([r for r in capacity_refusals(self.ledger) if r['ward'] == ward])
        results = {}
        for label, kwargs in (('+1 doctor', {'extra_doctors': 1}),
                              ('+1 room', {'extra_rooms': 1}),
                              ('+1 of each', {'extra_rooms': 1, 'extra_doctors': 1}),
                              ('+2 doctors', {'extra_doctors': 2}),
                              ('+2 rooms', {'extra_rooms': 2})):
            result = counterfactual(self.cases, self.spec, ward, **kwargs)
            results[label] = result
            absorbed = len(result['absorbed'])
            self.tree_replay.insert('', 'end',
                                    tags=('good' if absorbed else 'workflow',),
                                    values=(label, f'{absorbed} of {refused}',
                                            refused - absorbed, len(result['lost'])))

        if refused == 0:
            self.verdict.config(text=f'{ward} refused nothing. Nothing to absorb.')
            return

        doctor = len(results['+1 doctor']['absorbed'])
        room = len(results['+1 room']['absorbed'])
        if doctor and not room:
            text = (f'An extra ROOM in {ward} would have absorbed nothing at all. '
                    f'Rooms were never the constraint here - buying space would have '
                    f'been money spent on a room that was already empty.')
        elif room and not doctor:
            text = (f'An extra DOCTOR in {ward} would have absorbed nothing. The room '
                    f'is the constraint; the doctors were already idle.')
        elif room or doctor:
            text = (f'Both help in {ward}: +1 doctor absorbs {doctor}, +1 room absorbs '
                    f'{room}. Neither resource alone is the whole story.')
        else:
            text = (f'Neither one more room nor one more doctor absorbs anything in '
                    f'{ward}. The refusals have another cause - check the ledger.')
        self.verdict.config(text=text)


def main():
    root = tk.Tk()
    LedgerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
