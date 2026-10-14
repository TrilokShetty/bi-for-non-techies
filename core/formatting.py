"""Indian currency and fiscal-year helpers for answer wording and prompts."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union


Number = Union[int, float]


def format_inr(amount: Number, *, with_symbol: bool = True) -> str:
    """Format a number in Indian grouping: ₹12,34,567.89

    Why: Indian interview demos and business users expect lakhs/crores style
    grouping, not Western thousands separators.
    """
    negative = amount < 0
    amount = abs(float(amount))
    whole, frac = divmod(round(amount * 100), 100)
    whole_str = str(int(whole))

    if len(whole_str) <= 3:
        grouped = whole_str
    else:
        last3 = whole_str[-3:]
        rest = whole_str[:-3]
        parts = []
        while rest:
            parts.append(rest[-2:])
            rest = rest[:-2]
        grouped = ",".join(reversed(parts)) + "," + last3

    formatted = f"{grouped}.{frac:02d}" if frac else grouped
    if negative:
        formatted = f"-{formatted}"
    return f"₹{formatted}" if with_symbol else formatted


def inr_in_words_hint(amount: Number) -> str:
    """Optional short lakh/crore hint for large totals."""
    n = abs(float(amount))
    if n >= 1_00_00_000:
        return f"{format_inr(amount)} (~{n / 1_00_00_000:.2f} crore)"
    if n >= 1_00_000:
        return f"{format_inr(amount)} (~{n / 1_00_000:.2f} lakh)"
    return format_inr(amount)


def indian_fy(d: Optional[date] = None) -> str:
    """Indian fiscal year label for a date (FY25-26 = Apr 2025–Mar 2026)."""
    d = d or date.today()
    if d.month >= 4:
        start, end = d.year, d.year + 1
    else:
        start, end = d.year - 1, d.year
    return f"FY{str(start)[2:]}-{str(end)[2:]}"


def fy_date_range(fy_label: str) -> tuple[date, date]:
    """Parse 'FY25-26' or 'FY2025-26' into inclusive start/exclusive-style bounds as dates."""
    cleaned = fy_label.upper().replace(" ", "")
    if cleaned.startswith("FY"):
        cleaned = cleaned[2:]
    # Accept 25-26 or 2025-26
    left, right = cleaned.split("-")
    start_year = int(left) if len(left) == 4 else 2000 + int(left)
    end_year = int(right) if len(right) == 4 else 2000 + int(right)
    return date(start_year, 4, 1), date(end_year, 3, 31)


def quarter_for_indian_fy(d: date) -> str:
    """Q1=Apr-Jun … Q4=Jan-Mar within the Indian FY."""
    if d.month in (4, 5, 6):
        return "Q1"
    if d.month in (7, 8, 9):
        return "Q2"
    if d.month in (10, 11, 12):
        return "Q3"
    return "Q4"


def fiscal_context_for_prompt(today: Optional[date] = None) -> str:
    """Short block injected into SQL / generator prompts."""
    today = today or date.today()
    return (
        f"Today's date (ISO): {today.isoformat()}. "
        f"Current Indian fiscal year: {indian_fy(today)} (April–March). "
        "Q1=Apr–Jun, Q2=Jul–Sep, Q3=Oct–Dec, Q4=Jan–Mar. "
        "When users say 'this FY' or 'last quarter', interpret against this calendar. "
        "All money columns end with _inr and are in Indian Rupees."
    )


def maybe_format_value(column: str, value) -> str:
    """Pretty-print a cell if the column looks like an INR amount."""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)) and column.lower().endswith("_inr"):
        return format_inr(value)
    return str(value)


def format_sql_rows(columns: list[str], rows: list[dict]) -> str:
    """Render SQL result rows with INR formatting where applicable."""
    lines = []
    for row in rows:
        parts = [f"{col}={maybe_format_value(col, row.get(col))}" for col in columns]
        lines.append("{ " + ", ".join(parts) + " }")
    return "\n".join(lines)
