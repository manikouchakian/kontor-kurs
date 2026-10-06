from decimal import Decimal

from project import parse_rate, parse_date, calculate_conversion
import sqlite3

from project import init_db, save_rate, get_rate

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


def test_save_rate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_db()

    connection = sqlite3.connect("rates.db")

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