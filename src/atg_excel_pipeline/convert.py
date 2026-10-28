"""Conversions de cellules — reproduction des règles Power Query (§10)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

ErrorKind = Literal["cell", "conversion"] | None

EXCEL_EPOCH = datetime(1899, 12, 30)
EXCEL_ERROR_PREFIXES = (
    "#N/A",
    "#VALUE!",
    "#VALEUR!",
    "#REF!",
    "#DIV/0!",
    "#NAME?",
    "#NULL!",
    "#NUM!",
    "#GETTING_DATA",
    "#CALC!",
)
_MULTI_SPACE = re.compile(r" {2,}")


@dataclass(frozen=True)
class Converted:
    value: object
    error: ErrorKind = None


def is_excel_error(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip().upper()
    return any(text.startswith(prefix) for prefix in EXCEL_ERROR_PREFIXES)


def is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def clean_text(value: object) -> str | None:
    """U+00A0 et sauts de ligne → espace, trim, espaces multiples, vide → NULL.

    Identifiants numériques Excel : ``12345`` et non ``12345.0``.
    """

    if is_excel_error(value):
        return None
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")

    text = str(value).replace("\xa0", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = _MULTI_SPACE.sub(" ", text).strip()
    return text or None


def parse_number(value: object) -> Converted:
    if is_blank(value):
        return Converted(None)
    if is_excel_error(value):
        return Converted(None, "cell")
    if isinstance(value, bool):
        return Converted(None, "conversion")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Converted(float(value))
    if isinstance(value, Decimal):
        return Converted(float(value))

    text = str(value).replace("\xa0", "").replace(" ", "").strip()
    if text == "":
        return Converted(None)
    text = text.replace(",", ".")
    try:
        return Converted(float(text))
    except ValueError:
        return Converted(None, "conversion")


def parse_integer(value: object) -> Converted:
    """Arrondi ROUND_HALF_EVEN (pair le plus proche)."""

    number = parse_number(value)
    if number.value is None:
        return number
    quantized = Decimal(str(number.value)).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
    return Converted(int(quantized))


def _from_excel_serial(serial: float) -> date:
    return (EXCEL_EPOCH + timedelta(days=float(serial))).date()


def parse_date(value: object, *, dayfirst: bool = True) -> Converted:
    if is_blank(value):
        return Converted(None)
    if is_excel_error(value):
        return Converted(None, "cell")
    if isinstance(value, datetime):
        return Converted(value.date())
    if isinstance(value, date):
        return Converted(value)
    if isinstance(value, bool):
        return Converted(None, "conversion")
    if isinstance(value, (int, float)):
        try:
            return Converted(_from_excel_serial(float(value)))
        except OverflowError:
            return Converted(None, "conversion")

    text = str(value).strip()
    if not text:
        return Converted(None)
    if dayfirst:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return Converted(datetime.strptime(text[:10], fmt).date())
            except ValueError:
                continue
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return Converted(datetime.strptime(text[:10], fmt).date())
        except ValueError:
            continue
    if not dayfirst:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return Converted(datetime.strptime(text[:10], fmt).date())
            except ValueError:
                continue
    return Converted(None, "conversion")


def _hhmmss_from_int(n: int) -> time | None:
    text = f"{n:06d}"
    if len(text) > 6:
        return None
    hours, minutes, seconds = int(text[:2]), int(text[2:4]), int(text[4:6])
    if hours > 23 or minutes > 59 or seconds > 59:
        return None
    return time(hours, minutes, seconds)


def _time_from_fraction(fraction: float) -> time:
    total = int(round(float(fraction) * 86400)) % 86400
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hours, minutes, seconds)


def parse_time_sortie(value: object) -> Converted:
    """HHMMSS numérique arrondi, complété à 6 chiffres (comportement M)."""

    if is_blank(value):
        return Converted(None)
    if is_excel_error(value):
        return Converted(None, "cell")
    if isinstance(value, time):
        return Converted(value.replace(microsecond=0))
    if isinstance(value, datetime):
        return Converted(value.time().replace(microsecond=0))
    if isinstance(value, bool):
        return Converted(None, "conversion")
    try:
        if isinstance(value, str):
            text = value.strip().replace(" ", "").replace("\xa0", "")
            if text.isdigit():
                parsed = _hhmmss_from_int(int(text))
            else:
                return Converted(None, "conversion")
        else:
            parsed = _hhmmss_from_int(int(round(float(value))))
    except (TypeError, ValueError, OverflowError):
        return Converted(None, "conversion")
    if parsed is None:
        return Converted(None, "conversion")
    return Converted(parsed)


def parse_time_entree(value: object) -> Converted:
    """Parseur tolérant : time, datetime, fraction Excel, HH:MM[:SS], HHMMSS."""

    if is_blank(value):
        return Converted(None)
    if is_excel_error(value):
        return Converted(None, "cell")
    if isinstance(value, time):
        return Converted(value.replace(microsecond=0))
    if isinstance(value, datetime):
        return Converted(value.time().replace(microsecond=0))
    if isinstance(value, bool):
        return Converted(None, "conversion")
    if isinstance(value, (int, float)):
        number = float(value)
        if 0 <= number < 1:
            return Converted(_time_from_fraction(number))
        try:
            parsed = _hhmmss_from_int(int(round(number)))
        except (ValueError, OverflowError):
            return Converted(None, "conversion")
        if parsed is None:
            return Converted(None, "conversion")
        return Converted(parsed)

    text = str(value).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return Converted(datetime.strptime(text, fmt).time())
        except ValueError:
            continue
    digits = text.replace(" ", "").replace("\xa0", "")
    if digits.isdigit():
        parsed = _hhmmss_from_int(int(digits))
        if parsed is not None:
            return Converted(parsed)
    return Converted(None, "conversion")
