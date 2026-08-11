"""Testes unitários de `techpulse_ai.utils.dates`.

Além do mapeamento de cada formato aceito, estes testes fixam a
garantia central da função: o retorno é sempre timezone-aware em UTC,
para que artigos de fontes diferentes possam ser ordenados juntos.
"""
from datetime import UTC, datetime, timedelta, timezone

import pytest

from techpulse_ai.utils.dates import parse_date


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Timestamps Unix (Hacker News).
        (1704110400, datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        (1704110400.5, datetime(2024, 1, 1, 12, 0, 0, 500000, tzinfo=UTC)),
        (0, datetime(1970, 1, 1, 0, 0, tzinfo=UTC)),
        # RFC 822/2822 (feeds RSS).
        ("Mon, 01 Jan 2024 12:00:00 +0000", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        ("Mon, 01 Jan 2024 14:00:00 +0200", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        ("Mon, 01 Jan 2024 07:00:00 -0500", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        # ISO 8601 (APIs REST, ex: Dev.to).
        ("2024-01-01T12:00:00Z", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        ("2024-01-01T14:00:00+02:00", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        ("2024-01-01", datetime(2024, 1, 1, 0, 0, tzinfo=UTC)),
    ],
)
def test_parse_date_converts_supported_formats_to_utc(value, expected):
    assert parse_date(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "   ",
        "not a date",
        "2024-13-45T99:00:00",
        [1, 2],
        {},
        object(),
    ],
)
def test_parse_date_returns_none_for_unusable_values(value):
    assert parse_date(value) is None


@pytest.mark.parametrize("value", [1e20, -1e20])
def test_parse_date_returns_none_for_out_of_range_timestamps(value):
    """Timestamps absurdos devem virar `None`, não estourar `OverflowError`."""
    assert parse_date(value) is None


def test_parse_date_strips_surrounding_whitespace():
    assert parse_date("  2024-01-01T12:00:00Z  ") == datetime(2024, 1, 1, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "value",
    [
        1704110400,
        "Mon, 01 Jan 2024 12:00:00 +0000",
        "Mon, 01 Jan 2024 12:00:00 -0000",  # RFC 822: fuso "desconhecido"
        "Mon, 01 Jan 2024 12:00:00",  # RFC 822 sem offset
        "2024-01-01T12:00:00Z",
        "2024-01-01T12:00:00",  # ISO 8601 sem offset
        "2024-01-01",
        "2024-01-01T14:00:00+02:00",
    ],
)
def test_parse_date_always_returns_utc_aware_datetime(value):
    parsed = parse_date(value)

    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # RFC 822 com fuso "desconhecido" (-0000) devolve datetime naive.
        ("Mon, 01 Jan 2024 12:00:00 -0000", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        ("Mon, 01 Jan 2024 12:00:00", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        ("2024-01-01T12:00:00", datetime(2024, 1, 1, 12, 0, tzinfo=UTC)),
        ("2024-01-01", datetime(2024, 1, 1, 0, 0, tzinfo=UTC)),
    ],
)
def test_parse_date_interprets_missing_timezone_as_utc(value, expected):
    """Datas sem fuso são tratadas como UTC, sem deslocar o horário."""
    parsed = parse_date(value)

    assert parsed == expected
    assert parsed.replace(tzinfo=None) == expected.replace(tzinfo=None)


def test_parse_date_preserves_the_instant_when_converting_offsets():
    """Converter para UTC não pode alterar o instante representado."""
    same_instant = [
        parse_date("Mon, 01 Jan 2024 12:00:00 +0000"),
        parse_date("Mon, 01 Jan 2024 14:00:00 +0200"),
        parse_date("2024-01-01T07:00:00-05:00"),
        parse_date(1704110400),
    ]

    assert len(set(same_instant)) == 1
    assert same_instant[0] == datetime(2024, 1, 1, 12, 0, tzinfo=UTC)


def test_dates_from_different_sources_are_mutually_comparable():
    """Regressão: misturar naive e aware quebrava a ordenação da lista final.

    O `NewsCollectorService` junta artigos de todas as fontes em uma
    lista única, então datas vindas de formatos diferentes precisam ser
    comparáveis entre si.
    """
    parsed = [
        parse_date("2024-03-01T12:00:00"),  # ISO sem offset
        parse_date(1704110400),  # timestamp Unix
        parse_date("Mon, 01 Jan 2024 12:00:00"),  # RFC 822 sem offset
        parse_date("2024-02-01T12:00:00+02:00"),  # ISO com offset
    ]

    ordered = sorted(parsed)

    assert ordered == [
        datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        datetime(2024, 2, 1, 10, 0, tzinfo=UTC),
        datetime(2024, 3, 1, 12, 0, tzinfo=UTC),
    ]


def test_parse_date_accepts_non_utc_timezone_objects():
    moment = datetime(2024, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))

    assert parse_date(moment.isoformat()) == moment
