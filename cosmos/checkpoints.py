"""
Checkpoint match-rule engine (ADR-015 Extension, originator: gemini_spark).

Deterministic string/regex matching over frozen source scopes so that natural-
language judgement can never leak into an automated grading pass.

Verify-station resolutions (this build):
  * `is_regex: bool = False`. Non-regex literals are `re.escape()`d, so a
    literal like "BRK.B" matches only "BRK.B", never "BRKXB".
  * Invalid regex is caught, quarantined to /data/quarantine (INVALID_REGEX),
    and treated as a non-match — the nightly grading pipeline never crashes.
  * `source_scope` is pre-filtered before evaluation: a NEWS_HEADLINE_MATCH rule
    is never run against an 8-K, nor an EDGAR_FILING_CONTAINS against a headline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from . import alerts
from .quarantine import QuarantineReason, quarantine


class CheckpointPredicate(str, Enum):
    EDGAR_FILING_CONTAINS = "EDGAR_FILING_CONTAINS"   # scope: SEC form types
    NEWS_HEADLINE_MATCH = "NEWS_HEADLINE_MATCH"       # scope: news domains / HEADLINE
    PRICE_ABOVE = "PRICE_ABOVE"                       # deterministic by nature
    PRICE_BELOW = "PRICE_BELOW"


TEXT_PREDICATES = frozenset({
    CheckpointPredicate.EDGAR_FILING_CONTAINS,
    CheckpointPredicate.NEWS_HEADLINE_MATCH,
})


@dataclass(frozen=True)
class CheckpointMatchRule:
    predicate_type: CheckpointPredicate
    source_scope: Tuple[str, ...]     # frozen list of domains or SEC form types
    match_pattern: str
    case_sensitive: bool = False
    is_regex: bool = False


def compile_rule(rule: CheckpointMatchRule) -> Optional["re.Pattern"]:
    """Compile a rule's pattern. Literals are escaped. Invalid regex is
    quarantined and None is returned (never raised)."""
    pattern = rule.match_pattern if rule.is_regex else re.escape(rule.match_pattern)
    flags = 0 if rule.case_sensitive else re.IGNORECASE
    try:
        return re.compile(pattern, flags)
    except re.error as exc:
        quarantine(
            {"match_pattern": rule.match_pattern, "is_regex": rule.is_regex,
             "predicate_type": rule.predicate_type.value},
            reason=QuarantineReason.INVALID_REGEX,
            errors=[str(exc)],
            source="checkpoints.compile_rule",
        )
        alerts.emit_alert("CHECKPOINT_INVALID_REGEX",
                          f"quarantined invalid checkpoint pattern: {exc}",
                          severity="WARN", pattern=rule.match_pattern)
        return None


def evaluate_checkpoint_rule(rule: CheckpointMatchRule, document_text: str) -> bool:
    """True iff the (compiled) pattern is found in the document text. An
    uncompilable pattern yields False, not an exception."""
    compiled = compile_rule(rule)
    if compiled is None:
        return False
    return bool(compiled.search(document_text))


def in_scope(rule: CheckpointMatchRule, document: dict) -> bool:
    """A document is in scope iff its `scope` field is in the rule's source_scope."""
    return document.get("scope") in rule.source_scope


def evaluate_document(rule: CheckpointMatchRule, document: dict) -> Optional[bool]:
    """Scope-gated evaluation. Returns None (skipped) when the document is out of
    scope, else the boolean match over document['text']."""
    if not in_scope(rule, document):
        return None
    return evaluate_checkpoint_rule(rule, document.get("text", ""))


def grade_documents(rule: CheckpointMatchRule,
                    documents: Sequence[dict]) -> List[Tuple[dict, bool]]:
    """Evaluate a rule across many documents, skipping out-of-scope ones."""
    graded: List[Tuple[dict, bool]] = []
    for doc in documents:
        result = evaluate_document(rule, doc)
        if result is None:
            continue
        graded.append((doc, result))
    return graded
