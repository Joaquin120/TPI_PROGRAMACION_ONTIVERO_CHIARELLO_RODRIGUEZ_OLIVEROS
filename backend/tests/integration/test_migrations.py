import importlib.util
from pathlib import Path

from alembic.config import Config
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import create_engine, inspect


@pytest.fixture
def migration_module():
    """Dynamically loads the 001_initial_schema migration revision."""
    migration_path = Path("alembic/versions/001_initial_schema.py")
    assert migration_path.exists(), f"Migration file not found at {migration_path}"

    spec = importlib.util.spec_from_file_location("migration_001", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_chain_structure() -> None:
    """Verifies that Alembic ScriptDirectory detects revision 001 as root head without parent."""
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert heads == ["001"]

    revision = script.get_revision("001")
    assert revision is not None
    assert revision.revision == "001"
    assert revision.down_revision is None


def test_migration_file_identifiers(migration_module) -> None:
    """Verifies revision metadata and required callables in 001_initial_schema.py."""
    assert migration_module.revision == "001"
    assert migration_module.down_revision is None
    assert migration_module.branch_labels is None
    assert migration_module.depends_on is None
    assert callable(migration_module.upgrade)
    assert callable(migration_module.downgrade)


def test_migration_upgrade_and_downgrade_execution(migration_module) -> None:
    """Verifies that upgrade() creates the items table and indexes cleanly, and downgrade() drops them."""
    test_engine = create_engine("sqlite:///:memory:")

    with test_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            # Run upgrade
            migration_module.upgrade()

            inspector = inspect(conn)
            assert "items" in inspector.get_table_names()

            columns = {col["name"]: col for col in inspector.get_columns("items")}
            expected_columns = [
                "id",
                "name",
                "description",
                "price",
                "stock",
                "is_active",
                "created_at",
                "updated_at",
            ]
            for col_name in expected_columns:
                assert col_name in columns, f"Column {col_name} missing from table items"

            indexes = inspector.get_indexes("items")
            index_names = [idx["name"] for idx in indexes]
            assert "ix_items_name" in index_names

            # Run downgrade
            migration_module.downgrade()

            inspector = inspect(conn)
            assert "items" not in inspector.get_table_names()
