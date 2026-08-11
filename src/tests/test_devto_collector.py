"""Testes unitários do `DevToCollector`, sem acesso à rede."""
import pytest
import requests

from techpulse_ai.collectors import devto_collector
from techpulse_ai.collectors.base import BaseCollector
from techpulse_ai.collectors.devto_collector import DEVTO_ARTICLES_URL, DevToCollector


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


def install_fake_api(monkeypatch, payload, status_code=200):
    """Instala um `requests.get` falso e devolve o registro das chamadas."""
    calls = []

    def fake_get(url, params=None, timeout=None, **kwargs):
        calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(payload, status_code)

    monkeypatch.setattr(devto_collector.requests, "get", fake_get)
    return calls


def test_collect_returns_api_payload_unchanged(monkeypatch):
    payload = [{"id": 1, "title": "Artigo"}, {"id": 2, "title": "Outro"}]
    install_fake_api(monkeypatch, payload)

    assert DevToCollector().collect() == payload


def test_collect_requests_the_articles_endpoint(monkeypatch):
    calls = install_fake_api(monkeypatch, [])

    DevToCollector().collect()

    assert calls[0]["url"] == DEVTO_ARTICLES_URL


def test_collect_sends_per_page_and_omits_tag_by_default(monkeypatch):
    calls = install_fake_api(monkeypatch, [])

    DevToCollector(per_page=5).collect()

    assert calls[0]["params"] == {"per_page": 5}


def test_collect_sends_tag_when_configured(monkeypatch):
    calls = install_fake_api(monkeypatch, [])

    DevToCollector(tag="python", per_page=5).collect()

    assert calls[0]["params"] == {"per_page": 5, "tag": "python"}


def test_collect_passes_configured_timeout(monkeypatch):
    calls = install_fake_api(monkeypatch, [])

    DevToCollector(timeout=42).collect()

    assert calls[0]["timeout"] == 42


def test_collect_returns_empty_list_when_api_has_no_articles(monkeypatch):
    install_fake_api(monkeypatch, [])

    assert DevToCollector().collect() == []


def test_collect_raises_on_http_error(monkeypatch):
    install_fake_api(monkeypatch, None, status_code=503)

    with pytest.raises(requests.HTTPError):
        DevToCollector().collect()


def test_collector_defaults_and_contract():
    collector = DevToCollector()

    assert collector.tag is None
    assert collector.per_page == 20
    assert collector.timeout == 10
    assert isinstance(collector, BaseCollector)
