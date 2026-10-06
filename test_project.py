from decimal import Decimal

from project import parse_rate, parse_date, calculate_conversion
import sqlite3

from project import init_db, save_rate, get_rate,validate_headers,read_rates
import subprocess
import sys
from pathlib import Path
import pytest

def test_parse_rate():
    assert parse_rate(" 1.20 ") == Decimal("1.20")

    assert parse_rate("N/A") is None
    assert parse_rate("") is None
    assert parse_rate("0") is None
    assert parse_rate("-1.20") is None
    assert parse_rate("NaN") is None
    assert parse_rate("Infinity") is None


def test_parse_date():
    assert parse_date("2026-09-30") == "2026-09-30"
    assert parse_date(" 2024-02-29 ") == "2024-02-29"

    assert parse_date("2026-02-29") is None
    assert parse_date("2026-13-01") is None
    assert parse_date("hello") is None


def test_calculate_conversion():
    assert calculate_conversion(
        Decimal("100"), Decimal("1.20"), Decimal("0.90")
    ) == Decimal("75")

    assert calculate_conversion(
        Decimal("100"), Decimal("1"), Decimal("1.20")
    ) == Decimal("120")

    assert calculate_conversion(
        Decimal("0"), Decimal("1.20"), Decimal("0.90")
    ) == Decimal("0")


def test_save_rate(tmp_path):
    db_path = tmp_path / "rates.db"
    init_db(db_path)

    connection = sqlite3.connect(db_path)

    try:
        with connection:
            first = save_rate(
                connection, "2026-09-30", "USD", Decimal("1.20")
            )

            duplicate = save_rate(
                connection, "2026-09-30", "USD", Decimal("1.20")
            )

            changed = save_rate(
                connection, "2026-09-30", "USD", Decimal("1.30")
            )

        assert first == 1
        assert duplicate == 0
        assert changed == 0

        count = connection.execute(
            "SELECT COUNT(*) FROM rates"
        ).fetchone()[0]

        assert count == 1

        stored_rate = get_rate(connection, "2026-09-30", "USD")
        assert stored_rate == Decimal("1.20")

    finally:
        connection.close()


def test_convert_cli(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)

    connection = sqlite3.connect(db_path)

    try:
        with connection:
            save_rate(connection, "2026-09-30", "USD", Decimal("1.20"))
            save_rate(connection, "2026-09-30", "GBP", Decimal("0.90"))
    finally:
        connection.close()

    script = Path(__file__).resolve().with_name("project.py")

    command = [
        sys.executable,
        str(script),
        "convert",
        "100",
        "--from", "USD",
        "--to", "GBP",
        "--date", "2026-09-30",
        "--db", str(db_path),
    ]

    result = subprocess.run(
        command,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "100 USD = 75.00 GBP" in result.stdout

    command[3] = "abc"

    result = subprocess.run(
        command,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "Amount must be a number." in result.stderr



def test_validate_headers():
    assert validate_headers(
        [" Date ", " usd ", "GBP", ""]
    ) == ["Date", "USD", "GBP", ""]

    with pytest.raises(ValueError, match="Duplicate"):
        validate_headers(["Date", "USD", " usd "])

    with pytest.raises(ValueError, match="Date column"):
        validate_headers(["USD", "GBP"])

    with pytest.raises(ValueError, match="empty"):
        validate_headers(None)


def test_read_rates(tmp_path):
    csv_path = tmp_path / "sample.csv"

    csv_path.write_text(
        "Date,USD,GBP\n"
        "2026-09-30,1.20,N/A\n"
        "invalid-date,1.20,0.90\n"
        "2026-10-01,0,0.90\n"
        "2026-10-02,1.10\n",
        encoding="utf-8",
    )

    skipped = {"rows": 0, "rates": 0}
    records = list(read_rates(csv_path, skipped))

    assert records == [
        ("2026-09-30", "USD", Decimal("1.20")),
        ("2026-10-01", "GBP", Decimal("0.90")),
    ]

    assert skipped == {"rows": 2, "rates": 2}