"""
Cosmos Savant — core package.

Four concurrent loops on one ledger (ADR-019): SENSE, THINK, SURFACE, LEARN.
This package holds the deterministic, governed machinery. Trade execution is
NEVER performed by a language model (Section 0). The governor's 5% cap
(imported verbatim from /hermes) and the write-authority matrix (Section 1)
bind every intelligence in this system.

Module map (constitution bare-name -> package module):
    oracle.py            -> cosmos.oracle
    verify_intake.py     -> cosmos.verify_intake
    checkpoints.py       -> cosmos.checkpoints
    edgar_poller.py      -> cosmos.edgar_poller
    schema validators    -> cosmos.schema_validation
    shared utilities     -> cosmos.paths / backoff / persistence / alerts / quarantine / grading
"""

__version__ = "1.0.0"
