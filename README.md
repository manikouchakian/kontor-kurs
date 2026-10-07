# Kontor-Kurs

#### Video Demo:
Not recorded yet. I will add the video link here before the final submission.

#### Description:

Kontor-Kurs is a command-line program that works with historical exchange rates from the European Central Bank. It can import rates from a CSV file, convert an amount between currencies, and show basic statistics for a currency.

The program follows a simple process: read the CSV file, check its contents, save valid rates in SQLite, and use the saved data for conversions and statistics. Once the data has been downloaded and imported, no internet connection is needed.

The scope is deliberately small. There are three commands, and each has a clear purpose. The focus is on handling input carefully, keeping data consistent, and making the code understandable.

## Getting started

Create a virtual environment in the project directory and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Download the historical CSV archive from the [European Central Bank website](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html). Extract it and place `eurofxref-hist.csv` inside a folder called `data`.

The CSV file and generated database are not included in the repository. After downloading the data, run:

```bash
python3 project.py import
```

The program prints how many rates were inserted, how many already existed, and how many rates or rows were skipped.

## Converting currencies

For example, this command converts 100 US dollars to British pounds:

```bash
python3 project.py convert 100 --from USD --to GBP --date 2026-09-30
```

Both exchange rates must be available for the requested date. Currency codes can be entered in uppercase or lowercase.

ECB rates are expressed relative to one euro. The program therefore divides the amount by the source currency's rate and multiplies it by the target currency's rate. When EUR is selected, its rate is one.

## Viewing statistics

To view the stored statistics for US dollars, run:

```bash
python3 project.py stats USD
```

The table shows the number of observations, the first and last dates, and the minimum, maximum, and average rate. These figures describe all stored observations for that currency. The average is an arithmetic mean.

## Choosing different files

By default, the program looks for its CSV file and database relative to the location of `project.py`. This means the defaults still work when the program is started from another directory.

You can also choose your own paths:

```bash
python3 project.py import --csv /path/to/rates.csv --db custom.db
python3 project.py stats USD --db custom.db
```

Every command supports `--db`. Relative paths supplied on the command line are interpreted from the terminal's current directory.

## How the code is organised

`project.py` contains the application. Small functions handle argument parsing, validation, CSV reading, database access, calculations, and output. Keeping these jobs separate makes individual parts easier to test.

`test_project.py` contains the automated tests. `requirements.txt` lists pytest and tabulate. Further explanations are in `DESIGN.md`, and the software licence is in `LICENSE`.

SQLite suits this project because it stores everything in one local file without needing a database server. Each record is identified by its date and currency. Importing the same data again does not create duplicates or overwrite an existing rate.

Rates are handled with Decimal and stored as text to preserve their decimal representation. Conversion results are displayed with two decimal places, while statistics use six.

## Testing

Run the tests with:

```bash
python3 -m pytest -q
```

The tests cover parsing, conversion calculations, duplicate handling, command behaviour, CSV validation, and statistics. Database tests use temporary files, so running them does not change the project's working database.

## Current limitations

The program uses the exact date requested. If that date has no stored rates, it reports an error rather than choosing an earlier date automatically. Dates should be entered in a format such as `2026-09-30`.

Downloads are manual, and the available results depend on the imported dataset. The program does not calculate transaction fees or bank spreads. ECB reference rates are intended for information, so the results are not quotes for an actual currency exchange.

## References

- [ECB exchange reference rates and historical data](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
- [Python Decimal documentation](https://docs.python.org/3/library/decimal.html)