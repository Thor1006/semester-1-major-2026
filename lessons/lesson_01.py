"""Lesson 1: read a queue ID and respond to a button click."""

# READING THIS FILE
# Python executes the top-level statements from top to bottom during setup.
# The indented body of add_case() runs later, when the button calls it.
# Lines starting with # are comments; Python does not execute them.
# The triple-quoted string above is a module docstring: documentation that
# Python tools can inspect. The function below also has its own docstring.

# 1. IMPORTS: make existing tools available to this program.
# A module is an importable unit of Python code. tkinter is Python's interface
# to the Tcl/Tk GUI toolkit. "as tk" binds a shorter name to the imported module,
# letting us write tk.Tk() instead of tkinter.Tk(). The alias is our choice.
import tkinter as tk

# ttk is tkinter's themed-widget module. Its Frame, Label, Entry, and Button
# classes supply standard themed controls. No extra pip package is required,
# though the Python installation itself must include Tkinter and Tcl/Tk.
from tkinter import ttk


from tkinter import messagebox


# 2. THE WINDOW: construct an object, then configure it.
# Read this assignment from right to left:
#   tk.Tk() constructs an instance of Tk, the main/root-window class.
#   = binds the name window to that object so we can refer to it again.
# An object bundles state and operations; a window has a title and a title()
# method for changing it. We can use existing classes before writing our own.
# This application needs one Tk root. Additional windows would use Toplevel.
window = tk.Tk()

# Dot notation accesses a method belonging to an object. Parentheses call it.
# The quoted text is an argument passed to title(); the quotes are Python syntax
# and do not appear in the title bar. A method is an operation on an object.
window.title('Outpatient Scheduler - Lesson 1')

# geometry() accepts ONE string: 'widthxheight'. These are the requested starting
# dimensions in Tk's pixel coordinate units; the OS adds window decorations.
# The user can resize the window because this is not a fixed-size restriction.
window.geometry('500x300')

# minsize() takes TWO integers instead: minimum width, then minimum height.
# Numbers without quotes are numeric values, unlike the string passed above.
window.minsize(420, 280)

# 3. THE CONTAINER: parent-child relationships and layout.
# A widget is a GUI component. A Frame is a container for other widgets.
# window is the first positional argument: it identifies the frame's parent.
# padding=24 is a keyword argument: it names the option we want to set.
# Here, it leaves internal space between the frame edges and its child layout.
content = ttk.Frame(window, padding=24)

# Constructing a widget and arranging it are separate operations.
# pack() is a geometry manager: it determines placement and use of space.
# expand=True lets this frame's parcel receive extra available window space.
# fill='both' stretches the frame to fill that parcel in both directions.
# True is a Boolean value (true/false), not the string 'True'.
content.pack(fill='both', expand=True)

# The children INSIDE content will use grid(), a row-and-column layout.
# Rows and columns are numbered starting at 0. weight=1 lets column 0 grow.
# A weight is a relative share of extra space, not pixels or a percentage.
# With only one growing column, it receives all the extra width grid allocates.
#
# Using pack AND grid here is valid because they manage DIFFERENT parents:
#   pack manages content within window.
#   grid manages the controls within content.
# Avoid using pack and grid to manage children of the SAME parent.
content.columnconfigure(0, weight=1)

# 4. THE CONTROLS: construct widgets, then place them in the grid.
# Label displays text. The first argument makes it a child of content.
# text= sets what it says. font= receives a tuple of family, point size, and style.
# A tuple groups values; commas separate them. The outer Label(...) parentheses
# call the constructor, while the inner (...) group the font tuple.
heading = ttk.Label(content, text='Front-desk check-in', font=('Segoe UI', 18, 'bold'))

# row=0, column=0: first cell. sticky='w': west/left alignment within that cell.
# pady=(0, 8): EXTERNAL vertical space, 0 above this widget and 8 below it.
# Compare that with padding=24, which puts space INSIDE the containing frame.
heading.grid(row=0, column=0, sticky='w', pady=(0, 8))

# A separate label provides instructions. Distinct variable names let us refer
# to individual widget objects if we want to update them later.
instructions = ttk.Label(content, text='Enter a fictional queue ID, such as Q001.')
# Row 1 sits below row 0; the lower gap separates the instructions from the form.
instructions.grid(row=1, column=0, sticky='w', pady=(0, 16))

# The field label explains what the next input is for.
queue_label = ttk.Label(content, text='Queue ID')
queue_label.grid(row=2, column=0, sticky='w', pady=(0, 4))

# Entry is a single-line input. No text is inserted here, so it starts empty.
# queue_entry refers to the WIDGET OBJECT, not the string the user will type.
# We ask for its current text later by calling queue_entry.get().
queue_entry = ttk.Entry(content)

# sticky='ew' stretches the widget east-to-west across its allocated cell.
# Resizing takes two cooperating settings: weight grows the column, while
# sticky='ew' lets the widget stretch inside that enlarged column.
queue_entry.grid(row=3, column=0, sticky='ew', pady=(0, 12))

# Create the output label ONCE; the callback changes this object's text later.
# wraplength=360 wraps text after roughly that distance, not after 360 characters.
# It is a display setting, not a limit on how much text can be entered.
result_label = ttk.Label(content, text='Ready for a queue ID.', wraplength=360)

# Row 4 is reserved for the button constructed below. Creation order does not
# need to equal visual order: row/column numbers determine the grid positions.
result_label.grid(row=5, column=0, sticky='w', pady=(12, 0))



# 5. THE CALLBACK: define what should happen when Add is clicked.
# def defines a function, a named block of reusable instructions.
# Empty parentheses mean this function has no parameters. The colon starts its
# body; the following indentation determines which statements belong to it.
# Four spaces per indentation level is the normal Python convention.
#
# Reaching def creates a function object and binds its name, add_case.
# Python does NOT execute the indented body yet. The button calls it later.
def add_case():
    """This callback runs when the Add button is clicked."""

    # Evaluate from the right-hand expression before assigning the result:
    #   queue_entry.get() -> read the CURRENT Entry contents as a string
    #   .strip()          -> return a string without surrounding whitespace
    #   queue_id = ...    -> bind a LOCAL name to the cleaned string
    #
    # '  Q001  ' becomes 'Q001'; spaces-only input becomes the empty string ''.
    # strip() removes surrounding spaces, tabs, and other whitespace, but not
    # internal spaces: 'Q 001' remains 'Q 001'. It does not edit the Entry widget;
    # it returns a cleaned string for our function to work with.
    queue_id = queue_entry.get().strip()

    # Python treats an empty string as false and a nonempty string as true in a
    # condition. This is called truthiness. "not" reverses that truth value,
    # so the indented if body runs when the cleaned string is empty.
    # We check only nonemptiness in this lesson, not ID format or uniqueness.
    if not queue_id:

        # config(), short for configure(), updates an EXISTING widget's options.
        # text= names the option being changed. This displays the error in the
        # window; print() would send it to the terminal instead.
        result_label.config(text='Please enter a queue ID.')

        # Exit THIS callback immediately. The application stays open.
        # Without return, execution would fall through to the success update
        # below, replacing the helpful error with the unhelpful message 'Added '.
        # An empty return sends the value None back to the caller.
        return

    messagebox.showinfo("Queue ID Added", f"Added {queue_id} to the queue.")
    # This line is outside the if block because it is indented only four spaces.
    # It runs only when the early return above was not taken.
    # f marks a formatted string literal (f-string): Python evaluates what's
    # inside {...} and inserts it. With queue_id equal to 'Q001', this is 'Added Q001'.
    # Without f, the literal text 'Added {queue_id}' would be displayed.
    # Both single quotes and double quotes can delimit strings in Python.
    #result_label.config(text=f'Added {queue_id}')

    # Each call gets its own local queue_id binding. The widget names were bound
    # at module level; the function looks them up and calls their methods.
    # No "global" statement is needed because we do not reassign those names.
    # Mutating a widget's state differs from binding its name to another object.
    #
    # Reaching the end also returns None. Tkinter does not display that return
    # value: .config() already changed the label's text option. The label keeps
    # that state after this call finishes, but no case list/database exists yet.
    # The next result replaces this one; closing the app loses the widget state.


# 6. CONNECT THE BUTTON: pass a function for Tkinter to call later.
# command=add_case supplies the FUNCTION OBJECT as a callback, meaning a handler
# that another component calls when something happens (button activation here).
#
# Compare these two different expressions:
#   command=add_case    -> provide the function for a future click (correct here)
#   command=add_case()  -> call it NOW and provide its result, which is None here
#
# The second version would show the empty-input error during window setup, then
# fail to register our intended function for later clicks. Omitting () is key.
# Defining add_case above this statement ensures its name already exists when
# Python evaluates the argument command=add_case.
add_button = ttk.Button(content, text='Add', command=add_case)

# Row 4 puts the button between the Entry (3) and the output label (5).
add_button.grid(row=4, column=0, sticky='ew')

# Direct keyboard focus to this Entry within our application. When the app is
# active, typing can go there. This does not force the operating system to bring
# this application in front of every other window.
queue_entry.focus_set()

# 7. THE EVENT LOOP: run the application after the interface is ready.
# Python supplies __name__: '__main__' when this file is executed directly,
# or its module name ('app' here) when imported by another Python module.
# == compares two values; = alone assigns/binds a name.
# This condition starts the loop only when the file is run directly.
#
# The guard controls ONLY the code indented below it. Importing this file still
# creates the widgets above. That lets a lesson-check script import app, invoke
# its button, and close its window without automatically entering mainloop().
# Later, we can put setup in a function to avoid GUI side effects on import.
if __name__ == '__main__':

    # mainloop() processes input events, callbacks, resize events, and redraws.
    # It does NOT repeatedly rerun this entire Python file.
    # The ordinary flow is: wait for events -> handle an event -> handle more.
    #
    # The .config() call updates label state; the screen repaint is normally
    # processed as the event loop continues. Callbacks must therefore finish
    # promptly: a long calculation or time.sleep() here would delay input and
    # drawing on the GUI thread. We will handle background work in later lessons.
    #
    # The loop normally returns when this app's root is destroyed, for example
    # when the user closes its window. No more work follows, so the script ends.
    # Saving changes to this file does not update an already-running process.
    # Close the old window and run the file again to load your saved changes.
    window.mainloop()
