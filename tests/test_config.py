from __future__ import annotations

import os

from cosmos import config, paths


def test_load_credentials_from_files(tmp_path, monkeypatch):
    cred = tmp_path / "credentials"
    cred.mkdir()
    (cred / "gemini.env").write_text("GEMINI_API_KEY=xyz123\n# a comment\n", encoding="utf-8")
    (cred / "fred.env").write_text('FRED_API_KEY="fred-abc"\n', encoding="utf-8")
    monkeypatch.setattr(paths, "CREDENTIALS_DIR", cred)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    st = config.load_credentials()
    assert config.has_gemini_key() and os.environ["GEMINI_API_KEY"] == "xyz123"
    assert config.has_fred_key() and os.environ["FRED_API_KEY"] == "fred-abc"  # quotes stripped
    assert {"gemini.env", "fred.env"}.issubset(set(st["env_files"]))
    assert st["gemini"] is True and st["fred"] is True


def test_does_not_override_existing_env(tmp_path, monkeypatch):
    cred = tmp_path / "credentials"
    cred.mkdir()
    (cred / "gemini.env").write_text("GEMINI_API_KEY=fromfile\n", encoding="utf-8")
    monkeypatch.setattr(paths, "CREDENTIALS_DIR", cred)
    monkeypatch.setenv("GEMINI_API_KEY", "fromenv")
    config.load_credentials()
    assert os.environ["GEMINI_API_KEY"] == "fromenv"  # an already-set env var wins


def test_status_is_booleans_only(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CREDENTIALS_DIR", tmp_path / "credentials")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    st = config.status()
    assert all(isinstance(v, bool) for v in st.values())


def test_no_service_account_by_default(tmp_path, monkeypatch):
    # resolved at call time now — set the env var, not a module global
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_PATH", str(tmp_path / "nope.json"))
    assert config.has_google_service_account() is False


def test_service_account_env_is_honored_live(tmp_path, monkeypatch):
    sa = tmp_path / "sa.json"
    sa.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_PATH", str(sa))
    assert config.has_google_service_account() is True   # no longer stale from import
