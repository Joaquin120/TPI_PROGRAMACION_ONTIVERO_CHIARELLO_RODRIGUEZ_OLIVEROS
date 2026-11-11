import pytest
from pydantic import ValidationError

from parcial.app.core.config import Settings, get_settings


def test_valid_settings_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies that individual postgres and security settings load and assemble DATABASE_URL."""
    monkeypatch.setenv("POSTGRES_USER", "custom_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "custom_password")
    monkeypatch.setenv("POSTGRES_DB", "parcial_db")
    monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("BCRYPT_ROUNDS", "10")
    monkeypatch.setenv("APP_NAME", "Test_Libreria")

    settings = Settings(_env_file=None)
    assert settings.APP_NAME == "Test_Libreria"
    assert settings.POSTGRES_USER == "custom_user"
    assert settings.POSTGRES_PASSWORD == "custom_password"
    assert settings.POSTGRES_DB == "parcial_db"
    assert settings.POSTGRES_HOST == "db.example.com"
    assert settings.POSTGRES_PORT == 5433
    assert settings.SECRET_KEY == "test-secret-key"
    assert settings.BCRYPT_ROUNDS == 10
    assert (
        settings.DATABASE_URL
        == "postgresql+asyncpg://custom_user:custom_password@db.example.com:5433/parcial_db"
    )


def test_missing_postgres_credentials_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies fail-fast when required Postgres variables are missing."""
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    
    errors = str(exc_info.value)
    assert "POSTGRES_USER" in errors
    assert "POSTGRES_PASSWORD" in errors
    assert "POSTGRES_DB" in errors
    assert "SECRET_KEY" in errors


def test_missing_secret_key_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies fail-fast when SECRET_KEY is missing even if DB credentials are provided."""
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "SECRET_KEY" in str(exc_info.value)


def test_bcrypt_max_concurrency_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies the configurable bcrypt concurrency limit is loaded from settings."""
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.setenv("BCRYPT_MAX_CONCURRENCY", "2")

    settings = Settings(_env_file=None)

    assert settings.BCRYPT_MAX_CONCURRENCY == 2


def test_get_settings_singleton_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies get_settings returns the same cached instance."""
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("SECRET_KEY", "secret")

    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
