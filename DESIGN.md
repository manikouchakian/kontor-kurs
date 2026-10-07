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

## CSV validation

CSV reading and validation are separate from database writes. This allows the input-processing code to be tested without SQLite.

Column names are trimmed and currency names are converted to uppercase. Duplicate named columns are rejected to prevent one value from silently replacing another.

Invalid dates or incomplete rows cause the whole row to be skipped. An invalid rate only causes that individual rate to be skipped.

Valid rates are yielded one at a time, so the importer does not need to hold the entire dataset in memory.

## Statistics

Statistics use all stored observations for the requested currency. Rates are converted from text to Decimal before calculating minimum, maximum, and arithmetic mean. This avoids comparing numeric values as strings.

Dates are sorted to identify the first and last observation. The output shows the observation count because missing dates mean that the dataset is not necessarily continuous.

EUR is handled as a rate of one during conversions. Statistics only describe currencies actually stored in the database.

## Dates and rounding

Conversions require the exact requested date. The application does not silently substitute an earlier business day because that would change the date chosen by the user.

Calculations use Python's default Decimal context: 28 significant digits and half-even rounding. Conversion results display two decimal places, while statistics display six. This is a consistent display policy rather than currency-specific accounting support.