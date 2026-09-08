"""Lesson 6: save registrations to a local SQLite file so they survive a restart.

Until now every registration lived in a Python list and disappeared when the
window closed. This module gives the project its first PERSISTENT MEMORY.

WHAT IS SAVED, AND WHAT IS NOT. Registrations only. Room and doctor
reservations deliberately stay in memory, because nothing in the project can
yet END a reservation: there is no session completion or release step. A saved
reservation would come back tomorrow still holding a room, with no way to free
it. Persisting it would look like a feature and behave like a bug.

WHY SQLite. It is part of Python's standard library, so no new dependency is
needed, and the whole database is one ordinary file you can delete. A plain
text or CSV file would also work, but SQLite gives us the uniqueness rule for
free (see PRIMARY KEY below) and will not corrupt a record halfway through a
write.

PRIVACY. The file never leaves this computer: nothing here opens a network
connection. `.gitignore` already excludes `*.db`, so registrations are not
committed to version control even by accident. Keep using fictional details.
"""

import sqlite3
from pathlib import Path

# __file__ is the path of THIS source file. .resolve() makes it absolute and
# .parent gives the folder holding it, so the database always sits next to the
# code regardless of which folder the app was launched from. Hard-coding
# 'C:\\Users\\...' here would break the project on any other computer.
DATABASE_PATH = Path(__file__).resolve().parent / 'clinic.db'

# The column order matches what create_patient_record returns, so the two are
# easy to compare side by side.
#
# Read the UNIQUE line carefully: it is the ID rule from registration.py,
# written down where the DATABASE can enforce it. A ticket is only unique
# within one appointment date, so Q0147 may exist on the 8th and again on the
# 9th, but never twice on the same day. Even a bug elsewhere in the program
# cannot write a duplicate: SQLite refuses it.
#
# row_id is a separate INTEGER PRIMARY KEY, which SQLite fills in automatically
# and increments. It preserves the ORDER registrations arrived in, which the
# queue table needs and which (date, ticket) alone could not tell us.
SCHEMA = """
CREATE TABLE IF NOT EXISTS registrations (
    row_id              INTEGER PRIMARY KEY,
    appointment_date    TEXT NOT NULL,
    queue_id            TEXT NOT NULL,
    patient_name        TEXT NOT NULL,
    medical_information TEXT NOT NULL,
    phone_number        TEXT NOT NULL,
    destination_ward    TEXT NOT NULL,
    ward_code           TEXT NOT NULL,
    UNIQUE (appointment_date, queue_id)
);
"""

# The fields we read back out, in the order create_patient_record produces them.
FIELDS = ('queue_id', 'patient_name', 'medical_information', 'appointment_date',
          'phone_number', 'destination_ward', 'ward_code')


def connect(path=None):
    """Open the database, creating the file and table if they do not exist yet.

    Passing an explicit path lets tests use a temporary file instead of the real
    one, so running the checks never touches saved registrations.
    """
    # sqlite3.connect creates the file on demand. str() is used because older
    # Python versions do not accept a Path here.
    connection = sqlite3.connect(str(path or DATABASE_PATH))
    # row_factory changes what a query returns: with sqlite3.Row we can read a
    # column by name, row['queue_id'], instead of by position, row[1]. Position
    # numbers silently break the moment someone reorders the SELECT.
    connection.row_factory = sqlite3.Row
    # executescript runs the whole SCHEMA string. CREATE TABLE IF NOT EXISTS
    # means this is safe to run at every startup, not only the first one.
    connection.executescript(SCHEMA)
    connection.commit()
    return connection


def save_registration(connection, record):
    """Write one registration. Raises ValueError if that date already has it."""
    # The ? marks are PLACEHOLDERS. SQLite substitutes the values itself, with
    # correct quoting. Never build SQL by joining strings with patient data:
    # a name containing a quote would corrupt the statement, and in a networked
    # system the same habit is the classic SQL-injection vulnerability.
    try:
        connection.execute(
            'INSERT INTO registrations'
            ' (appointment_date, queue_id, patient_name, medical_information,'
            '  phone_number, destination_ward, ward_code)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?)',
            (record['appointment_date'], record['queue_id'], record['patient_name'],
             record['medical_information'], record['phone_number'],
             record['destination_ward'], record['ward_code']))
    except sqlite3.IntegrityError as error:
        # This fires when the UNIQUE rule is broken. Turning it into ValueError
        # keeps SQLite's vocabulary out of the rest of the program: app.py
        # already knows how to display a ValueError from registration.py.
        raise ValueError(
            f"{record['queue_id']} is already saved for "
            f"{record['appointment_date']}. No patient was added.") from error
    # Without commit the insert is only held in this connection's transaction
    # and would be lost if the program stopped here.
    connection.commit()


def load_registrations(connection):
    """Return every saved registration, oldest first, as plain dictionaries.

    The dictionaries have exactly the keys create_patient_record produces, so
    the rest of the program cannot tell a loaded record from a fresh one.
    """
    # ORDER BY row_id restores the original arrival order. Without it SQLite
    # makes no promise about row order at all.
    rows = connection.execute(
        'SELECT queue_id, patient_name, medical_information, appointment_date,'
        ' phone_number, destination_ward, ward_code'
        ' FROM registrations ORDER BY row_id').fetchall()
    # A LIST COMPREHENSION over the rows, building one dictionary per row.
    # dict(zip(...)) pairs each field name with the matching column value.
    return [dict(zip(FIELDS, tuple(row))) for row in rows]


def count_registrations(connection):
    """How many registrations are stored. Used for the startup message."""
    # fetchone() returns the single result row; [0] is its first column.
    return connection.execute('SELECT COUNT(*) FROM registrations').fetchone()[0]
