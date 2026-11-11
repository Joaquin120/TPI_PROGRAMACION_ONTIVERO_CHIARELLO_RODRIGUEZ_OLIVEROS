import os

# Configure test environment variables before module imports
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "parcial_db")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("SECRET_KEY", "test-parcial-secret-key-32-chars-long")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # Fast for unit tests
