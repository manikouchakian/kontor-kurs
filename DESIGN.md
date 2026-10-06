# Design Decisions

## Small functions

Each function has a clear job. Some functions check input, others read or save rates, and one function calculates the conversion.

This makes the code easier to understand and test. The main function reads the user's command and calls the appropriate function.

## File paths

Default file paths are based on the location of project.py. This allows the program to run from another folder.

Users can choose a different input file with --csv and a different database with --db. Relative paths supplied by the user are based on the terminal's current folder.

## SQLite storage

Each rate is identified by its date and currency. This pair is the table's primary key.

Importing the same data again does not create duplicate records. If a record already exists, the program keeps its current value.

## Decimal values

Rates are read as Decimal values and stored as text to preserve their decimal representation. They are converted back to Decimal when needed for calculations.

All stored rates are relative to one euro. A conversion uses the source and target rates from the same date.

## Error handling

The program reports expected errors with a short message. It returns exit code 0 for success and 1 when an operation fails. Argparse returns exit code 2 for invalid command syntax.

## Testing

Tests check input validation, conversion calculations, duplicate handling, and the conversion command.

Database tests use temporary files so they do not change the project's real database.