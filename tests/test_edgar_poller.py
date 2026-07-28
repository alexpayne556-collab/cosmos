from __future__ import annotations

import json
import random

from cosmos import paths
from cosmos.edgar_poller import EdgarPoller, BULK_INDEX_URL

URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"


def _alerts():
    p = paths.ALERTS_PATH
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def test_live_200_archives():
    poller = EdgarPoller(fetch=lambda url: (200, b"<rss/>"), sleep=lambda d: None)
    res = poller.poll(URL)
    assert res["mode"] == "LIVE"
    assert list(paths.STAGING_MIRROR.glob("edgar_*.raw"))


def test_block_then_recover_same_identity():
    responses = [(403, b""), (200, b"OK")]
    state = {"i": 0}

    def fetch(url):
        r = responses[min(state["i"], len(responses) - 1)]
        state["i"] += 1
        return r

    poller = EdgarPoller(fetch=fetch, sleep=lambda d: None)
    res = poller.poll(URL, rng=random.Random(0))
    assert res["mode"] == "LIVE_RECOVERED"
    assert res["user_agent"] == poller.user_agent          # NO identity rotation


def test_persistent_block_falls_back_to_bulk_index():
    def fetch(url):
        if url == BULK_INDEX_URL:
            return (200, b"master.idx contents")
        return (403, b"")

    poller = EdgarPoller(fetch=fetch, sleep=lambda d: None)
    res = poller.poll(URL, rng=random.Random(0))
    assert res["mode"] == "BULK_FALLBACK"
    assert res["user_agent"] == poller.user_agent          # same UA on fallback too
    assert any(a["kind"] == "SEC_EDGAR_BULK_FALLBACK" for a in _alerts())


def test_ua_is_declared_and_constant():
    poller = EdgarPoller(fetch=lambda url: (403, b""), sleep=lambda d: None)
    before = poller.user_agent
    poller.poll(URL, rng=random.Random(1))
    assert poller.user_agent == before
    assert "CosmosSavant" in poller.user_agent
