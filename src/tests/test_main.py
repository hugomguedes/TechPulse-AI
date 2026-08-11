"""Testes unitários de `techpulse_ai.main`.

Cobrem a montagem das fontes (`build_service`), a formatação da saída
no terminal (`print_articles`) e a orquestração do `main`. Nenhuma
chamada de rede acontece: os coletores são apenas construídos, nunca
executados, o `main` recebe um serviço falso e o `save_articles` é
substituído por um dublê — caso contrário abriria conexão real com o
PostgreSQL, que só existe dentro do docker-compose.
"""
from datetime import UTC, datetime

import pytest

from techpulse_ai import main as main_module
from techpulse_ai.collectors.devto_collector import DevToCollector
from techpulse_ai.collectors.github_collector import (
    GITHUB_BLOG_FEED_URL,
    GitHubBlogCollector,
)
from techpulse_ai.collectors.hackernews_collector import HackerNewsCollector
from techpulse_ai.collectors.rss_collector import RSSCollector
from techpulse_ai.models.article import Article
from techpulse_ai.normalizers.devto_normalizer import normalize_devto_entries
from techpulse_ai.normalizers.github_normalizer import normalize_github_entries
from techpulse_ai.normalizers.hackernews_normalizer import normalize_hackernews_entries
from techpulse_ai.normalizers.rss_normalizer import normalize_rss_entries
from techpulse_ai.services.news_collector_service import NewsCollectorService

CONFIG_ENV_VARS = (
    "TECHCRUNCH_RSS_URL",
    "GITHUB_BLOG_RSS_URL",
    "HACKERNEWS_LIMIT",
    "DEVTO_PER_PAGE",
)


@pytest.fixture
def clean_env(monkeypatch):
    """Remove as variáveis de configuração, isolando os testes do ambiente."""
    for name in CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_build_service_returns_service_with_all_four_sources(clean_env):
    service = main_module.build_service()

    assert isinstance(service, NewsCollectorService)
    assert [source.name for source in service.sources] == [
        "TechCrunch",
        "GitHub Blog",
        "Hacker News",
        "Dev.to",
    ]


def test_build_service_wires_each_collector_type(clean_env):
    collectors = [source.collector for source in main_module.build_service().sources]

    assert type(collectors[0]) is RSSCollector
    assert type(collectors[1]) is GitHubBlogCollector
    assert type(collectors[2]) is HackerNewsCollector
    assert type(collectors[3]) is DevToCollector


def test_build_service_wires_each_matching_normalizer(clean_env):
    normalizers = [source.normalizer for source in main_module.build_service().sources]

    assert normalizers == [
        normalize_rss_entries,
        normalize_github_entries,
        normalize_hackernews_entries,
        normalize_devto_entries,
    ]


def test_build_service_uses_defaults_when_env_is_unset(clean_env):
    sources = main_module.build_service().sources

    assert sources[0].collector.feed_url == main_module.DEFAULT_TECHCRUNCH_RSS_URL
    assert sources[1].collector.feed_url == GITHUB_BLOG_FEED_URL
    assert sources[2].collector.limit == 20
    assert sources[3].collector.per_page == 20


def test_build_service_reads_feed_urls_from_env(clean_env, monkeypatch):
    monkeypatch.setenv("TECHCRUNCH_RSS_URL", "https://exemplo.com/tc.xml")
    monkeypatch.setenv("GITHUB_BLOG_RSS_URL", "https://exemplo.com/gh.xml")

    sources = main_module.build_service().sources

    assert sources[0].collector.feed_url == "https://exemplo.com/tc.xml"
    assert sources[1].collector.feed_url == "https://exemplo.com/gh.xml"


def test_build_service_reads_numeric_limits_from_env(clean_env, monkeypatch):
    monkeypatch.setenv("HACKERNEWS_LIMIT", "5")
    monkeypatch.setenv("DEVTO_PER_PAGE", "7")

    sources = main_module.build_service().sources

    assert sources[2].collector.limit == 5
    assert sources[3].collector.per_page == 7


def test_build_service_keeps_source_name_for_techcrunch_collector(clean_env):
    assert main_module.build_service().sources[0].collector.source_name == "TechCrunch"


@pytest.mark.parametrize("name", ["HACKERNEWS_LIMIT", "DEVTO_PER_PAGE"])
def test_build_service_raises_on_non_numeric_limit(clean_env, monkeypatch, name):
    """Documenta o comportamento atual: um valor inválido no `.env` derruba a app."""
    monkeypatch.setenv(name, "vinte")

    with pytest.raises(ValueError):
        main_module.build_service()


def test_print_articles_shows_total_and_article_fields(capsys):
    articles = [
        Article(
            title="Primeira notícia",
            url="https://exemplo.com/1",
            source="TechCrunch",
            published_at=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        )
    ]

    main_module.print_articles(articles)

    output = capsys.readouterr().out
    assert "Total de artigos coletados: 1" in output
    assert "Título : Primeira notícia" in output
    assert "Fonte  : TechCrunch" in output
    assert "Data   : 2024-01-01T12:00:00+00:00" in output
    assert "URL    : https://exemplo.com/1" in output


def test_print_articles_shows_na_when_published_at_is_missing(capsys):
    articles = [Article(title="Sem data", url="https://exemplo.com/2", source="Dev.to")]

    main_module.print_articles(articles)

    assert "Data   : N/A" in capsys.readouterr().out


def test_print_articles_prints_every_article(capsys):
    articles = [
        Article(title=f"Notícia {index}", url=f"https://exemplo.com/{index}", source="Dev.to")
        for index in range(3)
    ]

    main_module.print_articles(articles)

    output = capsys.readouterr().out
    assert "Total de artigos coletados: 3" in output
    for index in range(3):
        assert f"Notícia {index}" in output


def test_print_articles_handles_empty_list(capsys):
    main_module.print_articles([])

    output = capsys.readouterr().out
    assert "Total de artigos coletados: 0" in output
    assert "Título" not in output


def test_main_loads_env_collects_prints_and_saves(capsys, monkeypatch):
    calls = []
    saved = []

    class FakeService:
        def collect_all(self):
            calls.append("collect_all")
            return [Article(title="Coletada", url="https://exemplo.com/1", source="Dev.to")]

    def fake_save(articles):
        calls.append("save_articles")
        saved.extend(articles)

    monkeypatch.setattr(main_module, "load_dotenv", lambda: calls.append("load_dotenv"))
    monkeypatch.setattr(main_module, "build_service", lambda: FakeService())
    monkeypatch.setattr(main_module, "save_articles", fake_save)

    main_module.main()

    assert calls == ["load_dotenv", "collect_all", "save_articles"]
    assert "Coletada" in capsys.readouterr().out
    assert [article.title for article in saved] == ["Coletada"]


def test_main_does_not_touch_the_network_when_service_returns_nothing(capsys, monkeypatch):
    saved = []

    class EmptyService:
        def collect_all(self):
            return []

    monkeypatch.setattr(main_module, "load_dotenv", lambda: None)
    monkeypatch.setattr(main_module, "build_service", lambda: EmptyService())
    monkeypatch.setattr(main_module, "save_articles", saved.append)

    main_module.main()

    assert "Total de artigos coletados: 0" in capsys.readouterr().out
    assert saved == [[]]


def test_default_techcrunch_url_points_to_techcrunch():
    assert main_module.DEFAULT_TECHCRUNCH_RSS_URL == "https://techcrunch.com/feed/"
