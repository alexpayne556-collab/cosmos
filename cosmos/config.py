"""
Credentials loader — dependency-free, gitignored-only.

Loads `credentials/*.env` into the process environment so modules read keys via
os.environ, and no key ever appears in code or a chat transcript. Locations come
from `cosmos.paths` (single source of truth — no duplicated REPO_ROOT).

Deviations from the delivered spec, on purpose:
  * Loading is EXPLICIT via load_credentials(), not on import. A module that reads
    secrets as an import side-effect would leak real keys into every test/tool
    process. Call load_credentials() once at process startup.
  * No `python-dotenv` dependency — a tiny parser keeps the project dependency-free
    (same reasoning as the in-house schema validator).
"""
from __future__ import annotations

import os
import pathlib

from . import paths

def google_service_account_path() -> str:
    """Resolved at CALL time (not import) so a value set via credentials/*.env or the
    environment is honored. (The fan-out audit caught the import-time-capture bug.)"""
    return os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_PATH", str(paths.CREDENTIALS_DIR / "service_account.json")
    )


# Back-compat constant (import-time default). Prefer google_service_account_path().
GOOGLE_SERVICE_ACCOUNT_PATH: str = google_service_account_path()


def _load_env_file(path: pathlib.Path) -> int:
    """Minimal KEY=VALUE .env parser. Never overrides an already-set env var."""
    if not path.exists():
        return 0
    loaded = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val
            loaded += 1
    return loaded


def load_credentials() -> dict:
    """Load every `credentials/*.env` into the environment. Returns a status map of
    BOOLEANS only — never key values."""
    paths.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    env_files = []
    for envf in sorted(paths.CREDENTIALS_DIR.glob("*.env")):
        _load_env_file(envf)
        env_files.append(envf.name)
    return {"env_files": env_files, **status()}


def status() -> dict:
    """Booleans only — safe to log, contains no secret values."""
    return {
        "gemini": has_gemini_key(),
        "fred": has_fred_key(),
        "datagov": has_datagov_key(),
        "polygon": has_polygon_key(),
        "fmp": has_fmp_key(),
        "alpha_vantage": has_alpha_vantage_key(),
        "eodhd": has_eodhd_key(),
        "finnhub": has_finnhub_key(),
        "fda": has_fda_key(),
        "newsdata": has_newsdata_key(),
        "tiingo": has_tiingo_key(),
        "google_service_account": has_google_service_account(),
    }


def has_gemini_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def has_fred_key() -> bool:
    return bool(os.getenv("FRED_API_KEY"))


def has_datagov_key() -> bool:
    """api.data.gov gateway key (Census / GovInfo / Regulations.gov / FEC / NREL / ...).
    Consumers read the value via os.getenv('DATA_GOV_API_KEY') after load_credentials()."""
    return bool(os.getenv("DATA_GOV_API_KEY"))


# --- market-data + catalyst vendor keys (credentials/api_keys.env) -----------
# Booleans only; consumers read the value via os.getenv(<VAR>) after load_credentials().
def has_polygon_key() -> bool:
    return bool(os.getenv("POLYGON_API_KEY"))


def has_fmp_key() -> bool:
    return bool(os.getenv("FMP_API_KEY"))


def has_alpha_vantage_key() -> bool:
    return bool(os.getenv("ALPHA_VANTAGE_API_KEY"))


def has_eodhd_key() -> bool:
    return bool(os.getenv("EODHD_API_KEY"))


def has_finnhub_key() -> bool:
    return bool(os.getenv("FINNHUB_API_KEY"))


def has_fda_key() -> bool:
    return bool(os.getenv("FDA_API_KEY"))


def has_newsdata_key() -> bool:
    return bool(os.getenv("NEWSDATA_API_KEY"))


def has_tiingo_key() -> bool:
    return bool(os.getenv("TIINGO_API_KEY"))


def has_google_service_account() -> bool:
    return pathlib.Path(google_service_account_path()).exists()
