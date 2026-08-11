"""Funções utilitárias para conversão de datas vindas de fontes externas.

Cada fonte representa datas de um jeito diferente (string RFC 822,
timestamp Unix, ISO 8601...). Este módulo centraliza essa conversão para
que os normalizadores não precisem lidar com `datetime` diretamente.
"""
from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


def _to_utc(moment: datetime) -> datetime:
    """Converte um `datetime` para UTC, garantindo que seja timezone-aware.

    Datas sem fuso horário são interpretadas como UTC. Isso é comum em
    feeds RSS mal formatados (que omitem o offset ou usam `-0000`) e em
    APIs que devolvem ISO 8601 sem offset.

    Args:
        moment: `datetime` naive ou aware.

    Returns:
        O mesmo instante, sempre com `tzinfo=UTC`.
    """
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def parse_date(value: str | float | None) -> datetime | None:
    """Converte um valor de data em diversos formatos para `datetime`.

    Suporta:
        - Timestamps Unix (int/float), como os usados pelo Hacker News.
        - Strings no formato RFC 822/2822, comuns em feeds RSS.
        - Strings ISO 8601, comuns em APIs REST (ex: Dev.to).

    O resultado é sempre timezone-aware em UTC, para que artigos de
    fontes diferentes possam ser comparados e ordenados entre si.
    Valores sem fuso horário são interpretados como UTC.

    Args:
        value: Valor bruto de data vindo da fonte externa.

    Returns:
        Um `datetime` timezone-aware em UTC, ou `None` se `value` for
        `None` ou não puder ser interpretado.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        try:
            return _to_utc(parsedate_to_datetime(value))
        except (TypeError, ValueError):
            pass

        try:
            iso_value = value.replace("Z", "+00:00")
            return _to_utc(datetime.fromisoformat(iso_value))
        except ValueError:
            return None

    return None
