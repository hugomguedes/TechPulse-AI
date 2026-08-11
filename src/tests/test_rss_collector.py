"""Testes unitários do `RSSCollector` e do `GitHubBlogCollector`.

O `feedparser` aceita uma string XML diretamente no lugar de uma URL, o
que permite testar a coleta inteira com feeds falsos (fixtures), sem
nenhuma chamada de rede.
"""
from techpulse_ai.collectors.base import BaseCollector
from techpulse_ai.collectors.github_collector import (
    GITHUB_BLOG_FEED_URL,
    GitHubBlogCollector,
)
from techpulse_ai.collectors.rss_collector import RSSCollector

FULL_RSS_FEED = """<?xml version="1.0"?>
<rss version="2.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Feed de Teste</title>
    <item>
      <title>Nova IA lan&#231;ada</title>
      <link>https://techcrunch.com/noticia-1</link>
      <dc:creator>Jane Doe</dc:creator>
      <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
      <description>Resumo da not&#237;cia</description>
      <content:encoded><![CDATA[<p>Corpo <b>completo</b></p>]]></content:encoded>
      <category>ai</category>
      <category>startups</category>
      <guid>tc-1</guid>
    </item>
  </channel>
</rss>"""

MINIMAL_RSS_FEED = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Feed de Teste</title>
    <item>
      <title>Item sem metadados</title>
      <link>https://techcrunch.com/noticia-2</link>
    </item>
  </channel>
</rss>"""

ATOM_FEED_WITH_UPDATED_ONLY = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Post do GitHub</title>
    <link href="https://github.blog/post-1"/>
    <id>urn:github:1</id>
    <updated>2024-02-02T10:00:00Z</updated>
  </entry>
</feed>"""

EMPTY_RSS_FEED = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Vazio</title></channel></rss>"""


def test_collect_maps_all_fields_from_entry():
    collector = RSSCollector(feed_url=FULL_RSS_FEED, source_name="TechCrunch")

    entries = collector.collect()

    assert len(entries) == 1
    entry = entries[0]
    assert entry["source"] == "TechCrunch"
    assert entry["title"] == "Nova IA lançada"
    assert entry["link"] == "https://techcrunch.com/noticia-1"
    assert entry["author"] == "Jane Doe"
    assert entry["published"] == "Mon, 01 Jan 2024 12:00:00 +0000"
    assert entry["summary"] == "Resumo da notícia"
    assert entry["id"] == "tc-1"


def test_collect_extracts_content_encoded_value():
    entries = RSSCollector(feed_url=FULL_RSS_FEED, source_name="TechCrunch").collect()

    assert entries[0]["content"] == "<p>Corpo <b>completo</b></p>"


def test_collect_extracts_categories_as_tags():
    entries = RSSCollector(feed_url=FULL_RSS_FEED, source_name="TechCrunch").collect()

    assert entries[0]["tags"] == ["ai", "startups"]


def test_collect_returns_none_for_absent_optional_fields():
    entries = RSSCollector(feed_url=MINIMAL_RSS_FEED, source_name="TechCrunch").collect()

    assert len(entries) == 1
    entry = entries[0]
    assert entry["author"] is None
    assert entry["published"] is None
    assert entry["summary"] is None
    assert entry["content"] is None
    assert entry["tags"] == []


def test_collect_falls_back_to_link_when_entry_has_no_guid():
    entries = RSSCollector(feed_url=MINIMAL_RSS_FEED, source_name="TechCrunch").collect()

    assert entries[0]["id"] == "https://techcrunch.com/noticia-2"


def test_collect_falls_back_to_updated_when_published_is_absent():
    entries = RSSCollector(
        feed_url=ATOM_FEED_WITH_UPDATED_ONLY, source_name="GitHub Blog"
    ).collect()

    assert entries[0]["published"] == "2024-02-02T10:00:00Z"


def test_collect_returns_empty_list_for_feed_without_items():
    assert RSSCollector(feed_url=EMPTY_RSS_FEED, source_name="TechCrunch").collect() == []


def test_collect_returns_empty_list_for_malformed_feed():
    """Documenta o comportamento atual: um feed inválido falha em silêncio.

    O `feedparser` sinaliza o problema em `parsed_feed.bozo`, mas o
    coletor ignora essa flag, então uma fonte quebrada é indistinguível
    de uma fonte sem notícias.
    """
    assert RSSCollector(feed_url="isso nao e xml", source_name="TechCrunch").collect() == []


def test_collect_propagates_configured_source_name():
    entries = RSSCollector(feed_url=FULL_RSS_FEED, source_name="Fonte Customizada").collect()

    assert entries[0]["source"] == "Fonte Customizada"


def test_github_collector_uses_default_feed_url_and_source_name():
    collector = GitHubBlogCollector()

    assert collector.feed_url == GITHUB_BLOG_FEED_URL
    assert collector.source_name == "GitHub Blog"


def test_github_collector_accepts_custom_feed_url_keeping_source_name():
    collector = GitHubBlogCollector(feed_url=ATOM_FEED_WITH_UPDATED_ONLY)

    entries = collector.collect()

    assert collector.source_name == "GitHub Blog"
    assert entries[0]["source"] == "GitHub Blog"
    assert entries[0]["title"] == "Post do GitHub"


def test_github_collector_is_an_rss_collector():
    collector = GitHubBlogCollector()

    assert isinstance(collector, RSSCollector)
    assert isinstance(collector, BaseCollector)
