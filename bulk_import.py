"""Lesson 7: read many registrations from a CSV file in one go.

Typing patients one at a time is fine for a demonstration and hopeless for a
real morning list. This module turns a spreadsheet export into records.

It contains NO Tkinter and NO database code. It reads a file and returns
records, so it can be tested without opening a window or writing anything.
app.py decides what to do with the result.

ALL OR NOTHING. If any row is invalid, nothing is imported and every problem is
reported together. A half-finished import is the worst outcome: the user cannot
tell which patients arrived without checking each one by hand. The alternative
design - import the good rows and list the skipped ones - is defensible too,
but it makes the user reconcile two lists, and here we prefer that they fix the
file and try again.

THE TICKET IS NOT IMPORTED. Queue IDs are generated exactly as they are for
typed registrations, so an imported patient cannot collide with an existing one
or invent an ID the app would not have chosen.
"""

import csv

from registration import create_patient_record

# The header the file must contain. medical_information may be blank on a row,
# but the COLUMN has to be present, so the file's shape is unambiguous.
REQUIRED_COLUMNS = ('patient_name', 'medical_information', 'appointment_date',
                    'phone_number', 'destination_ward')

# How many problems to list before summarising. A file with 300 broken rows
# should not produce 300 lines in a dialog box.
MAX_REPORTED_PROBLEMS = 12


def read_import_file(path, existing_records):
    """Validate a CSV file and return the records it would add.

    existing_records is the registrations already known, so generated tickets
    avoid both what is already saved and what earlier rows in this same file
    have just claimed.

    Raises ValueError describing every problem found. Nothing is written here:
    the caller saves the returned records, or nothing happens at all.
    """
    # newline='' is what the csv module documentation requires: it lets csv
    # handle line endings itself, so a quoted field containing a newline is
    # read correctly instead of being split into two rows.
    # utf-8-sig quietly swallows the byte-order mark Excel writes at the start
    # of a CSV, which would otherwise become part of the first column's name.
    with open(path, newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)

        # reader.fieldnames is None for a completely empty file.
        header = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in header]
        if missing:
            raise ValueError(
                'The file is missing these columns: ' + ', '.join(missing) +
                '.\nExpected header: ' + ','.join(REQUIRED_COLUMNS))

        rows = list(reader)

    if not rows:
        raise ValueError('The file has a valid header but no data rows.')

    accepted = []
    problems = []
    # A COPY of the existing records. Tickets already claimed by earlier rows in
    # this file must be visible to later rows, but the caller's list must not be
    # touched while the import might still fail.
    known = list(existing_records)

    # start=2 because row 1 is the header, so the number matches what the user
    # sees in a spreadsheet. Reporting "row 5" for the fourth patient wastes
    # their time.
    for line_number, row in enumerate(rows, start=2):
        try:
            record = create_patient_record(
                # .get(...) or '' turns a missing cell into an empty string
                # rather than None, which the validators would reject with a
                # confusing message about the wrong type.
                name=row.get('patient_name') or '',
                information=row.get('medical_information') or '',
                date_text=row.get('appointment_date') or '',
                phone=row.get('phone_number') or '',
                ward=row.get('destination_ward') or '',
                records=known,
            )
        except ValueError as error:
            # Record the problem and KEEP GOING, so the user gets the whole list
            # of what to fix instead of discovering one error per attempt.
            problems.append(f'Row {line_number}: {error}')
            continue
        accepted.append(record)
        known.append(record)

    if problems:
        raise ValueError(_describe(problems, len(rows)))
    return accepted


def _describe(problems, total_rows):
    """Build the message shown when an import is refused."""
    shown = problems[:MAX_REPORTED_PROBLEMS]
    text = (f'Nothing was imported. {len(problems)} of {total_rows} row(s) '
            f'could not be read:\n\n' + '\n'.join(shown))
    if len(problems) > len(shown):
        text += f'\n\n...and {len(problems) - len(shown)} more.'
    return text
