"""Ponto de entrada da aplicação TechPulse AI (fase 1 - coleta).

Monta as fontes de notícias configuradas, executa a coleta através do
`NewsCollectorService` e imprime os resultados no terminal, apenas para
validação manual. Não há persistência nem interface gráfica nesta etapa.
"""

import os

import psycopg
from dotenv import load_dotenv

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
from techpulse_ai.services.news_collector_service import (
    NewsCollectorService,
    NewsSource,
)

DEFAULT_TECHCRUNCH_RSS_URL = "https://techcrunch.com/feed/"


def build_service() -> NewsCollectorService:
    """Monta o `NewsCollectorService` com todas as fontes da primeira etapa.

    URLs de feeds podem ser sobrescritas via variáveis de ambiente
    (ver `.env.example`), o que facilita testes e trocas de fonte sem
    alterar código.

    Returns:
        Instância de `NewsCollectorService` pronta para coletar.
    """
    techcrunch_url = os.getenv("TECHCRUNCH_RSS_URL", DEFAULT_TECHCRUNCH_RSS_URL)
    github_url = os.getenv("GITHUB_BLOG_RSS_URL", GITHUB_BLOG_FEED_URL)
    hackernews_limit = int(os.getenv("HACKERNEWS_LIMIT", "20"))
    devto_per_page = int(os.getenv("DEVTO_PER_PAGE", "20"))

    sources = [
        NewsSource(
            name="TechCrunch",
            collector=RSSCollector(feed_url=techcrunch_url, source_name="TechCrunch"),
            normalizer=normalize_rss_entries,
        ),
        NewsSource(
            name="GitHub Blog",
            collector=GitHubBlogCollector(feed_url=github_url),
            normalizer=normalize_github_entries,
        ),
        NewsSource(
            name="Hacker News",
            collector=HackerNewsCollector(limit=hackernews_limit),
            normalizer=normalize_hackernews_entries,
        ),
        NewsSource(
            name="Dev.to",
            collector=DevToCollector(per_page=devto_per_page),
            normalizer=normalize_devto_entries,
        ),
    ]

    return NewsCollectorService(sources=sources)


def print_articles(articles: list[Article]) -> None:
    """Imprime os artigos coletados no terminal, para validação manual.

    Args:
        articles: Lista de `Article` a serem exibidos.
    """
    print(f"\nTotal de artigos coletados: {len(articles)}\n")
    print("-" * 80)
    for article in articles:
        published = article.published_at.isoformat() if article.published_at else "N/A"
        print(f"Título : {article.title}")
        print(f"Fonte  : {article.source}")
        print(f"Data   : {published}")
        print(f"URL    : {article.url}")
        print("-" * 80)


def main() -> None:
    """Executa a coleta completa e armazena os resultados em banco."""
    load_dotenv()
    service = build_service()
    articles = service.collect_all()
    with psycopg.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    ) as conn, conn.cursor() as cur:
        cur.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id serial primary key,
                    titulo text,
                    fonte text,
                    data_publicacao date,
                    url text
                )
                """)
        for article in articles:
            publicado_em = article.published_at.date() if article.published_at else None
            cur.execute(
                """
                    INSERT INTO articles (titulo, fonte, data_publicacao, url)
                    VALUES (%s, %s, %s, %s)
                """,
                (article.title, article.source, publicado_em, article.url)
            )


if __name__ == "__main__":
    main()
