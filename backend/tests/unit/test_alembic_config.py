from alembic.config import Config
from src.core.config import get_settings
from src.db.base import Base, POSTGRES_NAMING_CONVENTION


def test_alembic_config_uses_settings_database_url() -> None:
    """Verifies Alembic Config object can load and integrate application settings."""
    alembic_cfg = Config("alembic.ini")
    settings = get_settings()

    # Emulate env.py behavior
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    resolved_url = alembic_cfg.get_main_option("sqlalchemy.url")

    assert resolved_url is not None
    assert resolved_url.startswith("postgresql+asyncpg://")
    assert resolved_url == settings.DATABASE_URL


def test_target_metadata_has_standard_naming_convention() -> None:
    """Verifies that Base.metadata bound to Alembic target_metadata has the standard naming convention."""
    assert Base.metadata.naming_convention == POSTGRES_NAMING_CONVENTION
    assert "ix" in Base.metadata.naming_convention
    assert "uq" in Base.metadata.naming_convention
    assert "ck" in Base.metadata.naming_convention
    assert "fk" in Base.metadata.naming_convention
    assert "pk" in Base.metadata.naming_convention
