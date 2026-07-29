from __future__ import annotations

from cosmos.edgar_rss import parse_feed

SAMPLE_ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <entry><title>8-K - ACME CORP (0001234567) (Filer)</title>
  <link href="https://www.sec.gov/Archives/edgar/data/1234567/0001234567-26-000123-index.htm"/>
  <category term="8-K"/><id>urn:tag:sec.gov,2008:accession-number=0001234567-26-000123</id>
  <updated>2026-07-29T10:00:00-04:00</updated></entry>
 <entry><title>S-3 - BETA INC (0007654321) (Filer)</title>
  <link href="https://www.sec.gov/Archives/edgar/data/7654321/0007654321-26-000045-index.htm"/>
  <category term="S-3"/><id>urn:tag:sec.gov,2008:accession-number=0007654321-26-000045</id>
  <updated>2026-07-29T09:30:00-04:00</updated></entry>
 <entry><title>malformed no id</title><link href="https://www.sec.gov/none"/></entry>
</feed>"""


def test_parse_extracts_fields():
    entries = parse_feed(SAMPLE_ATOM)
    assert len(entries) == 2                         # the id-less entry is skipped
    e = entries[0]
    assert e["accession_number"] == "0001234567-26-000123"
    assert e["form_type"] == "8-K"
    assert e["ticker"] is None                       # never fabricated
    assert e["company"] == "ACME CORP"
    assert e["url"].endswith("index.htm")


def test_malformed_entry_skipped_not_fabricated():
    assert all(e["accession_number"] for e in parse_feed(SAMPLE_ATOM))


def test_bad_xml_returns_empty_not_raise():
    assert parse_feed(b"not xml <<<") == []
