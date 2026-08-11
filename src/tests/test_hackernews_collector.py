"""Testes unitários do `HackerNewsCollector`, sem acesso à rede.

As chamadas HTTP são substituídas por um fake de `requests.get`, o que
permite verificar quais URLs são chamadas, o corte pelo `limit` e o
tratamento de itens inexistentes.
"""
import pytest
import requests

from techpulse_ai.collectors import hackernews_collector
from techpulse_ai.collectors.base import BaseCollector
from techpulse_ai.collectors.hackernews_collector import (
    ITEM_URL_TEMPLATE,
    TOP_STORIES_URL,
    HackerNewsCollector,
)


class FakeResponse:
    """Resposta HTTP falsa, com controle sobre o corpo e o status."""

    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


def install_fake_api(monkeypatch, story_ids, items, status_by_url=None):
    """Instala um `requests.get` falso e devolve o registro das chamadas."""
    calls = []
    status_by_url = status_by_url or {}

    def fake_get(url, timeout=None, **kwargs):
        calls.append({"url": url, "timeout": timeout})
        status = status_by_url.get(url, 200)
        if url == TOP_STORIES_URL:
            return FakeResponse(story_ids, status)
        for story_id, item in items.items():
            if url == ITEM_URL_TEMPLATE.format(item_id=story_id):
                return FakeResponse(item, status)
        raise AssertionError(f"URL inesperada: {url}")

    monkeypatch.setattr(hackernews_collector.requests, "get", fake_get)
    return calls


def test_collect_returns_items_for_top_stories(monkeypatch):
    install_fake_api(
        monkeypatch,
        story_ids=[1, 2],
        items={
            1: {"id": 1, "title": "Primeira", "by": "user1"},
            2: {"id": 2, "title": "Segunda", "by": "user2"},
        },
    )

    items = HackerNewsCollector(limit=2).collect()

    assert items == [
        {"id": 1, "title": "Primeira", "by": "user1"},
        {"id": 2, "title": "Segunda", "by": "user2"},
    ]


def test_collect_requests_only_the_first_limit_stories(monkeypatch):
    calls = install_fake_api(
        monkeypatch,
        story_ids=[10, 20, 30, 40, 50],
        items={story_id: {"id": story_id, "title": "t"} for story_id in (10, 20, 30)},
    )

    items = HackerNewsCollector(limit=3).collect()

    assert [item["id"] for item in items] == [10, 20, 30]
    assert calls[0]["url"] == TOP_STORIES_URL
    assert [call["url"] for call in calls[1:]] == [
        ITEM_URL_TEMPLATE.format(item_id=story_id) for story_id in (10, 20, 30)
    ]


def test_collect_handles_limit_larger_than_available_stories(monkeypatch):
    install_fake_api(
        monkeypatch,
        story_ids=[7],
        items={7: {"id": 7, "title": "Única"}},
    )

    items = HackerNewsCollector(limit=50).collect()

    assert len(items) == 1


def test_collect_skips_items_returned_as_null(monkeypatch):
    """A API do Hacker News devolve `null` para itens removidos."""
    install_fake_api(
        monkeypatch,
        story_ids=[1, 2, 3],
        items={
            1: {"id": 1, "title": "Válida"},
            2: None,
            3: {"id": 3, "title": "Também válida"},
        },
    )

    items = HackerNewsCollector(limit=3).collect()

    assert [item["id"] for item in items] == [1, 3]


def test_collect_passes_configured_timeout_to_every_request(monkeypatch):
    calls = install_fake_api(
        monkeypatch,
        story_ids=[1],
        items={1: {"id": 1, "title": "t"}},
    )

    HackerNewsCollector(limit=1, timeout=42).collect()

    assert [call["timeout"] for call in calls] == [42, 42]


def test_collect_raises_when_top_stories_request_fails(monkeypatch):
    install_fake_api(
        monkeypatch,
        story_ids=[],
        items={},
        status_by_url={TOP_STORIES_URL: 500},
    )

    with pytest.raises(requests.HTTPError):
        HackerNewsCollector().collect()


def test_collect_raises_when_an_item_request_fails(monkeypatch):
    install_fake_api(
        monkeypatch,
        story_ids=[1],
        items={1: {"id": 1, "title": "t"}},
        status_by_url={ITEM_URL_TEMPLATE.format(item_id=1): 404},
    )

    with pytest.raises(requests.HTTPError):
        HackerNewsCollector(limit=1).collect()


def test_collector_defaults_and_contract():
    collector = HackerNewsCollector()

    assert collector.limit == 20
    assert collector.timeout == 10
    assert isinstance(collector, BaseCollector)
