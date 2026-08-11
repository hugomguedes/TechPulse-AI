"""Modelo de domínio único para representar uma notícia de tecnologia.

Todas as fontes de dados (RSS, APIs de terceiros, etc.) são convertidas
para este modelo pelos normalizadores, garantindo que o restante do
sistema nunca precise conhecer o formato original de cada fonte.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Article(BaseModel):
    """Representa uma notícia padronizada, independente da origem.

    Campos ausentes na fonte original devem ser preenchidos com ``None``
    (ou lista vazia, no caso de ``tags``) pelos normalizadores — nunca
    omitidos.
    """

    model_config = ConfigDict(frozen=False, str_strip_whitespace=True)

    id: str | None = Field(
        default=None,
        description="Identificador único do artigo, quando disponível na fonte.",
    )
    title: str = Field(description="Título da notícia.")
    url: str = Field(description="URL original da notícia.")
    author: str | None = Field(
        default=None, description="Autor da notícia, se informado pela fonte."
    )
    published_at: datetime | None = Field(
        default=None, description="Data/hora de publicação, já convertida para datetime."
    )
    source: str = Field(description="Nome da fonte de origem (ex: 'TechCrunch', 'Hacker News').")
    summary: str | None = Field(
        default=None, description="Resumo curto da notícia, quando fornecido pela fonte."
    )
    content: str | None = Field(
        default=None, description="Conteúdo completo ou parcial da notícia, se disponível."
    )
    tags: list[str | None] = Field(
        default_factory=list, description="Lista de tags/categorias associadas à notícia."
    )
