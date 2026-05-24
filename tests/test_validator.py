"""Unit tests for SQL validator."""
from app.sql.validator import SQLValidator

def test_valid_select():
    val = SQLValidator()
    assert val.validate("SELECT * FROM students;") is True

def test_forbidden_keywords():
    val = SQLValidator()
    for kw in ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER"]:
        assert val.validate(f"{kw} FROM students;") is False

def test_invalid_table():
    val = SQLValidator()
    assert val.validate("SELECT * FROM secret_table;") is False
