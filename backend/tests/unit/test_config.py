import pytest
from pydantic import ValidationError

from src.core.config import Settings, get_settings


def test_valid_settings_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies valid settings load with expected attributes and defaults."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/test_db",
    )
    monkeypatch.setenv("APP_NAME", "Custom_Backend")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DB_ECHO", "True")
    monkeypatch.setenv("DB_POOL_SIZE", "15")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "20")
    monkeypatch.setenv("DB_TIMEOUT", "5.0")

    settings = Settings(_env_file=None)
    assert settings.APP_NAME == "Custom_Backend"
    assert settings.ENVIRONMENT == "testing"
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/test_db"
    assert settings.DB_ECHO is True
    assert settings.DB_POOL_SIZE == 15
    assert settings.DB_MAX_OVERFLOW == 20
    assert settings.DB_TIMEOUT == 5.0


def test_missing_database_url_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies that missing DATABASE_URL raises ValidationError."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    "invalid_url",
    [
        "postgresql://postgres:postgres@localhost:5432/db",
        "sqlite+aiosqlite:///test.db",
        "mysql+asyncmy://user:pass@localhost/db",
        "invalid_scheme://host/db",
        "",
    ],
)
def test_invalid_database_url_scheme_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch,
    invalid_url: str,
) -> None:
    """Verifies that invalid DATABASE_URL schemes raise ValidationError."""
    monkeypatch.setenv("DATABASE_URL", invalid_url)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_get_settings_singleton_cache() -> None:
    """Verifies get_settings returns the same cached instance."""
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
