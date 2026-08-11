"""Testes unitários do modelo `Article`."""
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from techpulse_ai.models.article import Article


def test_article_creation_with_all_fields():
    article = Article(
        id="1",
        title="Título de teste",
        url="https://example.com/noticia",
        author="Autor Teste",
        published_at=datetime(2024, 1, 1, tzinfo=UTC),
        source="TechCrunch",
        summary="Resumo curto",
        content="Conteúdo completo",
        tags=["ia", "python"],
    )

    assert article.id == "1"
    assert article.title == "Título de teste"
    assert article.tags == ["ia", "python"]


def test_article_creation_with_minimal_fields_defaults_to_none():
    article = Article(title="Só título", url="https://example.com", source="Dev.to")

    assert article.id is None
    assert article.author is None
    assert article.published_at is None
    assert article.summary is None
    assert article.content is None
    assert article.tags == []


def test_article_requires_title_url_and_source():
    with pytest.raises(ValidationError):
        Article(url="https://example.com")


def test_article_config_is_applied_by_pydantic():
    """Regressão: a config vivia em `class ConfigDict`, que o pydantic ignora."""
    assert Article.model_config.get("str_strip_whitespace") is True
    assert Article.model_config.get("frozen") is False


def test_article_strips_whitespace_from_string_fields():
    article = Article(
        id="  42  ",
        title="  Título com espaços  ",
        url="  https://example.com/noticia  ",
        author="  Autor  ",
        source="  TechCrunch  ",
        summary="  Resumo  ",
        content="  Conteúdo  ",
    )

    assert article.id == "42"
    assert article.title == "Título com espaços"
    assert article.url == "https://example.com/noticia"
    assert article.author == "Autor"
    assert article.source == "TechCrunch"
    assert article.summary == "Resumo"
    assert article.content == "Conteúdo"


def test_article_strips_whitespace_inside_tag_list():
    article = Article(
        title="Título", url="https://example.com", source="Dev.to", tags=["  python  ", " ia "]
    )

    assert article.tags == ["python", "ia"]


def test_article_remains_mutable():
    article = Article(title="Antes", url="https://example.com", source="Dev.to")

    article.title = "Depois"

    assert article.title == "Depois"
