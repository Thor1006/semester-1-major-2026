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
| 8 | A baseline duration estimate, then an ML comparison if data permits | Features, targets, train/test separation, regression, and error in minutes |
| 9 (optional) | General hospital FAQs, beginning locally | Public information boundaries and API request construction |
| 10 | Independent rebuild and presentation | Reconstructing requirements, explaining choices, and demonstrating limitations |

## Current progress

- Completed: proposal captured and project instructions created.
- Completed: step-by-step teaching approach documented.
- Implemented and checked: lesson 1, including a working window and Add callback.
- User practice observed: you added a messagebox confirmation to lesson 1. That popup is retained in lesson 2.
- Completed: lesson 2 registration, generated ward-based queue IDs, and an in-memory queue. The user reported finishing learning this part on 2026-09-06; no additional assessment was performed.
- Next: lesson 3, introducing multiple rooms within each ward and doctor availability. Begin with a small example of two rooms and three waiting patients before adding time-slot scheduling.
- No model training or hardware checks are complete yet.

## First lesson's target

Enter a fictional queue ID such as `Q001`, click a button, and see `Added Q001` in a label. An empty input should produce a helpful message.

This first exercise only teaches input and button handling. Actual queue storage comes in lesson 2.

Concept to understand: `button click -> Python callback -> read input -> validate -> update label`.

Practice after the lesson: change the success message to `Queue Q001 is ready for check-in.` (using whatever ID was entered).

## Lesson notes

### Lesson 1: a window that responds

**Historical lesson:** preserved in `lessons/lesson_01.py`, including your later popup experiment. The explanation below describes the original label-update lesson; the current `app.py` now implements lesson 2.

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
