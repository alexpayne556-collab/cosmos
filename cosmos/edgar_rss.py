"""
SEC EDGAR Atom feed parser — pure, stdlib-only, no I/O, no network.

Turns a raw EDGAR `getcurrent` Atom feed (bytes) into structured filing entries.
Total function: a malformed entry is skipped, never raised; a key is never
fabricated (no resolvable accession number -> the entry is dropped, not guessed).
`ticker` is left None — EDGAR feeds carry CIK, not ticker; resolving it is a
later VERIFY-lane concern, never invented here.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import List, Optional

_ATOM = "{http://www.w3.org/2005/Atom}"
_ACC_RE = re.compile(r"accession-number=([0-9-]+)")
_ACC_IN_URL_RE = re.compile(r"(\d{10}-\d{2}-\d{6})")


def _accession(id_text: str, url: str) -> Optional[str]:
    m = _ACC_RE.search(id_text or "")
    if m:
        return m.group(1)
    m = _ACC_IN_URL_RE.search(url or "")
    return m.group(1) if m else None


def _company(title: str) -> Optional[str]:
    # SEC getcurrent titles look like "8-K - ACME CORP (0001234567) (Filer)"
    if " - " in title:
        rest = title.split(" - ", 1)[1]
        return rest.split(" (")[0].strip() if " (" in rest else rest.strip()
    return None


def parse_feed(raw: bytes) -> List[dict]:
    """Parse an EDGAR Atom feed. Returns filing dicts:
    {accession_number, form_type, ticker(None), company, title, url, pub_date}."""
    out: List[dict] = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return out
    for e in root.iter(_ATOM + "entry"):
        title_el = e.find(_ATOM + "title")
        title = (title_el.text or "") if title_el is not None else ""
        cat = e.find(_ATOM + "category")
        form_type = cat.get("term") if (cat is not None and cat.get("term")) else (
            title.split(" - ")[0].strip() if " - " in title else "EDGAR"
        )
        link = e.find(_ATOM + "link")
        url = link.get("href") if link is not None else ""
        id_el = e.find(_ATOM + "id")
        accession = _accession(id_el.text if id_el is not None else "", url)
        if not accession:
            continue  # never fabricate a key
        upd = e.find(_ATOM + "updated")
        pub_date = (upd.text or "") if upd is not None else ""
        out.append({
            "accession_number": accession,
            "form_type": form_type,
            "ticker": None,              # feeds carry CIK, not ticker — never fabricated
            "company": _company(title),
            "title": title,
            "url": url,
            "pub_date": pub_date,
        })
    return out
