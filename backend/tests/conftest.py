import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


@pytest.fixture
def db_session():
    """An isolated in-memory SQLite session with the full schema applied.

    Models use SQLAlchemy's database-agnostic types (Uuid, Numeric,
    Enum(native_enum=False)) specifically so the same model definitions
    can be exercised here without a running Postgres instance.
    """
    engine = create_engine("sqlite:///:memory:")

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
