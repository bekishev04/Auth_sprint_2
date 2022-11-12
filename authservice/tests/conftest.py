import datetime
import time
import uuid

import docker
import psycopg2
import pytest
import sqlalchemy as sa
from alembic import command
from werkzeug.security import generate_password_hash

from authservice import create_app
from authservice.entrypoints import enums
from authservice.config import cfg
from authservice.database import db, migrate, models
from authservice.tokens.tokens import TokenManager

cfg.SQLALCHEMY_DATABASE_URI = (
    "postgresql://postgres:postgres@localhost:54329/postgres"
)


def _timeout(seconds: float):
    """Helper TimeOut"""
    time.sleep(seconds)


def _create_users():
    """Create users for auth"""

    for l, r, n, f in (
        ("admin", enums.UserRole.ADMIN.value, "A", "_A"),
        ("user", enums.UserRole.USER.value, "U", "_U"),
    ):
        db.session.add(
            models.User(
                login=l,
                password=generate_password_hash("admin"),
                role=r,
                full_name=f"{n} {f}",
            )
        )
    db.session.commit()


@pytest.fixture(scope="session")
def container():
    """Database Container"""
    client = docker.from_env()

    container = client.containers.run(
        image="postgres:13.3",
        name="postgres__test",
        detach=True,
        environment={
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "PGDATA": "/var/lib/postgresql/data",
            "POSTGRES_DB": "postgres",
        },
        remove=True,
        ports={"5432/tcp": 54329},
    )

    stop_iter, use_iter = 30, 0
    while use_iter <= stop_iter:
        try:
            conn = psycopg2.connect(cfg.SQLALCHEMY_DATABASE_URI)

            cursor = conn.cursor()
            cursor.execute("select 1 where true")
        except psycopg2.DatabaseError:
            use_iter += 1
            _timeout(2)
        else:
            if cursor.fetchone():
                cursor.close()
                conn.close()
                break
            else:
                use_iter += 1
                _timeout(2)

    yield container

    container.stop()


@pytest.fixture(scope="session")
def app(container):
    """Application Flask"""

    app = create_app()
    with app.app_context():
        app.testing = True
        command.upgrade(migrate.get_config(), "head")

        _create_users()  # created users all roles

        yield app


@pytest.fixture
def client(app):
    """Client Test Flask"""
    with app.test_client() as client:
        yield client


@pytest.fixture
def token_pair(request, app):
    """Test Case Create Refresh Token Api"""

    # todo
    marker = request.node.get_closest_marker("use_user")
    if marker:
        use_user = marker.args[0]
    else:
        use_user = "admin"

    user = (
        db.session.execute(
            sa.select(models.User).where(
                models.User.login == use_user,
            )
        )
        .scalars()
        .first()
    )

    if user:

        return TokenManager().get_token_pair(user.id)


@pytest.fixture
def headers(token_pair):
    """Generate headers for request"""

    access_token, refresh_token = token_pair

    return {
        "X-Auth-Token": f"{access_token}",
    }
