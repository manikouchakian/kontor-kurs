import argparse
import csv
from decimal import Decimal, InvalidOperation, DecimalException
from datetime import date 
import sqlite3 
import sys 
from pathlib import Path
from tabulate import tabulate



BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = BASE_DIR / "rates.db"
DEFAULT_CSV = BASE_DIR / "data" / "eurofxref-hist.csv"

def main():
    parser = argparse.ArgumentParser(
        description="Import, convert, and explore ECB exchange rates."
    )

    commands = parser.add_subparsers(dest="command", required=True)

    import_parser = commands.add_parser(
        "import",
        help="Import ECB rates from CSV",
    )

    import_parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="Path to the input CSV",
    )

    import_parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to the SQLite database",
    )

    convert_parser = commands.add_parser(
        "convert",
        help="Convert an amount using stored rates",
    )

    convert_parser.add_argument("amount")
    convert_parser.add_argument("--from", dest="source", required=True)
    convert_parser.add_argument("--to", dest="target", required=True)
    convert_parser.add_argument("--date", dest="rate_date", required=True)

    convert_parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to the SQLite database",
    )

    stats_parser = commands.add_parser(
        "stats",
        help="Show statistics for a currency",
    )

    stats_parser.add_argument("currency")

    stats_parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to the SQLite database",
    )

    args = parser.parse_args()

    try:
        if args.command == "import":
            import_rates(
                args.csv.expanduser(),
                args.db.expanduser(),
            )

        elif args.command == "convert":
            convert_currency(
                args.amount,
                args.source,
                args.target,
                args.rate_date,
                args.db.expanduser(),
            )

        elif args.command == "stats":
            show_stats(
                args.currency,
                args.db.expanduser(),
            )

    except (
        OSError,
        UnicodeError,
        csv.Error,
        sqlite3.Error,
        ValueError,
        DecimalException,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0

def validate_headers(fieldnames):
    if not fieldnames:
        raise ValueError("CSV is empty or has no header.")

    headers = []

    for name in fieldnames:
        name = name.strip()

        if name.lower() == "date":
            name = "Date"
        else:
            name = name.upper()

        headers.append(name)

    if "Date" not in headers:
        raise ValueError("CSV must contain a Date column.")

    named_headers = [name for name in headers if name]

    if len(named_headers) != len(set(named_headers)):
        raise ValueError("Duplicate column names are not allowed.")

    return headers


def read_rates(csv_path, skipped):
    with open(csv_path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        reader.fieldnames = validate_headers(reader.fieldnames)

        for row in reader:
            if None in row or None in row.values():
                skipped["rows"] += 1
                continue

            rate_date = parse_date(row["Date"])

            if rate_date is None:
                skipped["rows"] += 1
                continue

            for currency, value in row.items():
                if currency == "Date" or not currency:
                    continue

                rate = parse_rate(value)

                if rate is None:
                    skipped["rates"] += 1
                    continue

                yield rate_date, currency, rate


def import_rates(csv_path=DEFAULT_CSV, db_path=DEFAULT_DB):
    init_db(db_path)

    inserted_rates = 0
    duplicate_rates = 0
    skipped = {"rows": 0, "rates": 0}

    connection = sqlite3.connect(db_path)

    try:
        with connection:
            for rate_date, currency, rate in read_rates(csv_path, skipped):
                inserted = save_rate(
                    connection,
                    rate_date,
                    currency,
                    rate,
                )

                if inserted == 1:
                    inserted_rates += 1
                else:
                    duplicate_rates += 1

    finally:
        connection.close()

    print("Inserted rates:", inserted_rates)
    print("Duplicate rates:", duplicate_rates)
    print("Skipped rates:", skipped["rates"])
    print("Skipped rows:", skipped["rows"])
    

def parse_rate(value):
    value = value.strip()

    try:
        rate = Decimal(value)
    except InvalidOperation:
        return None
    if not rate.is_finite() or rate <= 0:
        return None 

    return rate
        

def parse_date(value):
    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError:
        return None
    return parsed.isoformat()


def convert_currency(amount, source, target, rate_date, db_path=DEFAULT_DB):
    try:
        amount = Decimal(amount)
    except InvalidOperation:
        raise ValueError("Amount must be a number.") from None

    if not amount.is_finite() or amount < 0:
        raise ValueError("Amount must be finite and non-negative.")

    rate_date = parse_date(rate_date)

    if rate_date is None:
        raise ValueError("Please provide a valid date in YYYY-MM-DD format.")

    source = source.strip().upper()
    target = target.strip().upper()

    db_path = Path(db_path).expanduser().resolve()

    if not db_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {db_path}. Run import first."
        )

    connection = sqlite3.connect(
        db_path.as_uri() + "?mode=ro",
        uri=True,
    )

    try:
        row = connection.execute(
            "SELECT 1 FROM rates WHERE date = ? LIMIT 1",
            (rate_date,),
        ).fetchone()

        if row is None:
            raise ValueError("No stored rates for this date.")

        source_rate = (
            Decimal("1")
            if source == "EUR"
            else get_rate(connection, rate_date, source)
        )

        target_rate = (
            Decimal("1")
            if target == "EUR"
            else get_rate(connection, rate_date, target)
        )

        if source_rate is None or target_rate is None:
            raise ValueError(
                "A currency is unknown or its rate is missing for this date."
            )

        result = calculate_conversion(amount, source_rate, target_rate)

        print(f"{amount} {source} = {result:.2f} {target} ({rate_date})")

    finally:
        connection.close()


        
def show_stats(currency, db_path=DEFAULT_DB):
    currency = currency.strip().upper()
    db_path = Path(db_path).expanduser().resolve()

    if not db_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {db_path}. Run import first."
        )

    connection = sqlite3.connect(
        db_path.as_uri() + "?mode=ro",
        uri=True,
    )

    try:
        stats = get_stats(connection, currency)
    finally:
        connection.close()

    if stats is None:
        raise ValueError("No stored rates for this currency.")

    table = [
        ["Currency", currency],
        ["Count", stats["count"]],
        ["First date", stats["first_date"]],
        ["Last date", stats["last_date"]],
        ["Minimum", f"{stats['minimum']:.6f}"],
        ["Maximum", f"{stats['maximum']:.6f}"],
        ["Average", f"{stats['average']:.6f}"],
    ]

    print("Rates are quoted per 1 EUR.")
    print(
        tabulate(
            table,
            headers=["Metric", "Value"],
            tablefmt="simple",
            disable_numparse=True,
        )
    )


def init_db(db_path=DEFAULT_DB):
    connection = sqlite3.connect(db_path)

    try:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rates (
                    date TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    rate TEXT NOT NULL,
                    PRIMARY KEY (date, currency)
                )
                               """)
    finally:
        connection.close()


def save_rate(connection, rate_date, currency, rate):
    cursor = connection.execute(
        """
        INSERT INTO rates (date, currency, rate)
        VALUES (?, ?, ?)
        ON CONFLICT(date, currency) DO NOTHING
        """,
        (rate_date, currency, str(rate)),
    )

    return cursor.rowcount


def get_rate(connection, rate_date, currency):
    currency = currency.strip().upper()

    cursor = connection.execute(
        """
        SELECT rate
        FROM rates
        WHERE date = ? AND currency = ?
        """,
        (rate_date, currency),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return Decimal(row[0])


def get_stats(connection, currency):
    currency = currency.strip().upper()

    rows = connection.execute(
        """
        SELECT date, rate
        FROM rates
        WHERE currency = ?
        ORDER BY date
        """,
        (currency,),
    ).fetchall()

    if not rows:
        return None

    rates = [Decimal(row[1]) for row in rows]

    return {
        "count": len(rates),
        "first_date": rows[0][0],
        "last_date": rows[-1][0],
        "minimum": min(rates),
        "maximum": max(rates),
        "average": sum(rates) / len(rates),
    }


def calculate_conversion(amount, source_rate, target_rate):
    return amount * target_rate / source_rate

if __name__ == "__main__":
    sys.exit(main())