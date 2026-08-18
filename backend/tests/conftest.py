import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed import seed_default_categories
from app.db.session import get_db
from app.main import app
from app.models import Base


@pytest.fixture
def db_session():
    """An isolated in-memory SQLite session with the full schema applied.

    Models use SQLAlchemy's database-agnostic types (Uuid, Numeric,
    Enum(native_enum=False)) specifically so the same model definitions
    can be exercised here without a running Postgres instance. StaticPool
    keeps a single connection alive for the whole test so the in-memory
    database survives across the multiple connections FastAPI's request
    handling and the test itself each open.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    """A TestClient wired to the same in-memory DB session as the test itself."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(client, db_session):
    """A `client` whose database already has the system default categories."""
    seed_default_categories(db_session)
    return client
