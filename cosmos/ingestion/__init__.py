"""Ingestion adapters — bring the world INTO the system through the right lane.

Reader/research observations (SEC filings, news) go to the observations store,
kept physically separate from the graded prediction ledger (ADR-026 firewall).
Nothing here writes a prediction except through verify_intake.intake() +
ledger.log_prediction() (the write-authority + ADR-030 gates).
"""
