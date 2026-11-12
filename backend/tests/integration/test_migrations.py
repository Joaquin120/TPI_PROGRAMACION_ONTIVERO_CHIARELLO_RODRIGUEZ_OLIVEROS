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
    """Verifies that Alembic ScriptDirectory detects revision 003 as head with parents 002 and 001."""
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert heads == ["003"]

    rev_003 = script.get_revision("003")
    assert rev_003 is not None
    assert rev_003.revision == "003"
    assert rev_003.down_revision == "002"

    rev_002 = script.get_revision("002")
    assert rev_002 is not None
    assert rev_002.revision == "002"
    assert rev_002.down_revision == "001"

    rev_001 = script.get_revision("001")
    assert rev_001 is not None
    assert rev_001.revision == "001"
    assert rev_001.down_revision is None


@pytest.fixture
def migration_module_002():
    """Dynamically loads the 002_create_clientes migration revision."""
    migration_path = Path("alembic/versions/002_create_clientes.py")
    assert migration_path.exists(), f"Migration file not found at {migration_path}"

    spec = importlib.util.spec_from_file_location("migration_002", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_002_upgrade_and_downgrade(migration_module, migration_module_002) -> None:
    """Verifies upgrade and downgrade for clientes table."""
    test_engine = create_engine("sqlite:///:memory:")

    with test_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            migration_module.upgrade()
            migration_module_002.upgrade()

            inspector = inspect(conn)
            assert "clientes" in inspector.get_table_names()
            columns = {col["name"] for col in inspector.get_columns("clientes")}
            assert {"id", "nombre", "email"}.issubset(columns)

            migration_module_002.downgrade()
            inspector = inspect(conn)
            assert "clientes" not in inspector.get_table_names()


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


@pytest.fixture
def migration_module_003():
    """Dynamically loads the 003_create_ventas migration revision."""
    migration_path = Path("alembic/versions/003_create_ventas.py")
    assert migration_path.exists(), f"Migration file not found at {migration_path}"

    spec = importlib.util.spec_from_file_location("migration_003", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_003_upgrade_and_downgrade(migration_module, migration_module_002, migration_module_003) -> None:
    """Verifies upgrade and downgrade for ventas and ventas_renglones tables."""
    test_engine = create_engine("sqlite:///:memory:")

    with test_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            migration_module.upgrade()
            migration_module_002.upgrade()
            migration_module_003.upgrade()

            inspector = inspect(conn)
            assert "ventas" in inspector.get_table_names()
            assert "ventas_renglones" in inspector.get_table_names()

            migration_module_003.downgrade()
            inspector = inspect(conn)
            assert "ventas_renglones" not in inspector.get_table_names()
            assert "ventas" not in inspector.get_table_names()

