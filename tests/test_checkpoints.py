from __future__ import annotations

from cosmos import paths
from cosmos.checkpoints import (
    CheckpointMatchRule,
    CheckpointPredicate,
    evaluate_checkpoint_rule,
    evaluate_document,
    grade_documents,
)


def _rule(pattern, scope=("8-K",), is_regex=False, case_sensitive=False,
          predicate=CheckpointPredicate.EDGAR_FILING_CONTAINS):
    return CheckpointMatchRule(predicate, tuple(scope), pattern,
                               case_sensitive=case_sensitive, is_regex=is_regex)


def test_literal_dot_is_escaped_no_false_positive():
    # "BRK.B" as a literal must NOT match "BRKXB"
    rule = _rule("BRK.B", is_regex=False)
    assert evaluate_checkpoint_rule(rule, "shares of BRKXB traded") is False
    assert evaluate_checkpoint_rule(rule, "shares of BRK.B traded") is True


def test_regex_mode_matches():
    rule = _rule(r"Form\s+S-\d", is_regex=True)
    assert evaluate_checkpoint_rule(rule, "filed Form S-3 today") is True


def test_case_insensitive_default():
    rule = _rule("bankruptcy")
    assert evaluate_checkpoint_rule(rule, "Chapter 11 BANKRUPTCY petition") is True


def test_invalid_regex_quarantined_no_crash():
    rule = _rule("S-3 (File No.", is_regex=True)  # unbalanced paren
    # does not raise; returns non-match
    assert evaluate_checkpoint_rule(rule, "anything") is False
    q = list(paths.QUARANTINE.glob("*INVALID_REGEX*.json"))
    assert q, "invalid regex should have been quarantined"


def test_scope_prefilter_skips_out_of_scope():
    rule = _rule("dilution", scope=("S-3",))
    in_scope = {"scope": "S-3", "text": "shelf dilution registration"}
    out_scope = {"scope": "HEADLINE", "text": "dilution rumor"}
    assert evaluate_document(rule, in_scope) is True
    assert evaluate_document(rule, out_scope) is None  # skipped


def test_grade_documents_only_in_scope():
    rule = _rule("award", scope=("8-K",),
                 predicate=CheckpointPredicate.EDGAR_FILING_CONTAINS)
    docs = [
        {"scope": "8-K", "text": "contract award announced"},
        {"scope": "HEADLINE", "text": "award season"},
        {"scope": "8-K", "text": "no news"},
    ]
    graded = grade_documents(rule, docs)
    assert len(graded) == 2                      # HEADLINE skipped
    assert [g[1] for g in graded] == [True, False]
