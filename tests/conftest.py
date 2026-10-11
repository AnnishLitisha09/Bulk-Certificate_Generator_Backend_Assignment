"""
Pytest configuration and fixtures.
Provides isolated temporary database and storage environments for automated tests.
"""

from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_temp_dir(tmp_path_factory) -> Path:
    """Session-scoped temporary directory for test storage and database."""
    temp_dir = tmp_path_factory.mktemp("test_app_data")
    return temp_dir


@pytest.fixture(scope="session")
def test_storage_dir(test_temp_dir: Path) -> Path:
    """Temporary storage directory for PDF certificates generated during tests."""
    storage_dir = test_temp_dir / "test_certificates"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture(scope="session")
def test_db_path(test_temp_dir: Path) -> Path:
    """Temporary SQLite database path for isolated test execution."""
    return test_temp_dir / "test_bulk_certificates.db"


@pytest.fixture(scope="session")
def test_settings(test_storage_dir: Path, test_db_path: Path) -> Settings:
    """Override application settings with test database and storage directory."""
    return Settings(
        APP_NAME="Bulk Certificate Generator [TEST]",
        APP_ENV="test",
        DEBUG=False,
        DATABASE_URL=f"sqlite:///{test_db_path.as_posix()}",
        STORAGE_DIR=str(test_storage_dir.as_posix()),
        MAX_BATCH_SIZE=500,
    )


@pytest.fixture(scope="session")
def test_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        future=True,
    )
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Function-scoped database session with fresh tables per test.
    Guarantees clean isolation between test executions without complex savepoint hacks.
    """
    Base.metadata.create_all(bind=test_engine)
    session = Session(bind=test_engine, expire_on_commit=False)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session, test_settings: Settings) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient with overridden get_db and get_settings dependencies.
    """
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
