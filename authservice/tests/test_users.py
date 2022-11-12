import datetime
import http

import pytest
import sqlalchemy as sa

from authservice.database import models, db
from . import random_refs as r
from .utils import get_random_one


def _get_random_user():
    """Generate random user"""

    return get_random_one(
        models.User,
        w=models.User.login.notin_(["admin"]),
    )


class TestAuthApi:
    """Auth Api Test"""

    @pytest.mark.parametrize("body", [{"login": "admin", "password": "admin"}])
    def test_signin(self, client, body):

        rv = client.post("api/v1/user/login", json=body)

        assert rv.status_code == http.HTTPStatus.OK

    @pytest.mark.parametrize(
        "body", [{"login": "test1", "password": "admin", "full_name": "test"}]
    )
    def test_signup(self, client, body):

        rv = client.post("api/v1/user/signup", json=body)

        assert rv.status_code == http.HTTPStatus.CREATED

        user = (
            db.session.execute(
                sa.select(models.User).where(
                    models.User.login == body["login"],
                )
            )
            .scalars()
            .first()
        )

        assert str(user.id) == rv.json["id"]


@pytest.mark.use_user("admin")
class TestUsersApi:
    """Group Users Api Test"""

    def test_get(self, client, headers):
        """Test Case Api"""

        rv = client.get("api/v1/user/users", headers=headers)

        assert rv.status_code == 200

    def test_get_one(self, client, headers):
        """Test Case Api"""

        row = _get_random_user()

        rv = client.get(f"api/v1/user/users/{row.id}", headers=headers)

        assert rv.status_code == 200
        assert rv.json["login"] == row.login

    @pytest.mark.parametrize("body", [r.random_users()[0]])
    def test_put(self, client, headers, body):
        """Test Case Api"""

        row = _get_random_user()
        rv = client.put(
            f"api/v1/user/users/{row.id}",
            json=body,
            headers=headers,
        )

        assert rv.status_code == 200

    def test_delete(self, client, headers):
        """Test Case Api"""

        row = get_random_one(
            models.User,
            w=models.User.login.notin_(["admin", "user"]),
        )
        rv = client.delete(f"api/v1/user/users/{row.id}", headers=headers)

        assert rv.status_code == 200


@pytest.mark.use_user("admin")
class TestUserPassworsEditApi:
    """User Api Test"""

    @pytest.mark.parametrize(
        "body",
        [
            {
                "password_old": "admin",
                "password": "admin2",
                "password_repeat": "admin2",
            }
        ],
    )
    def test_post(self, client, headers, body):
        """Test Case Api"""

        row = _get_random_user()
        rv = client.post(
            f"api/v1/user/users/{row.id}/password-edit",
            json=body,
            headers=headers,
        )

        assert rv.status_code == 200


@pytest.mark.use_user("admin")
class TestRefreshTokenEditApi:
    """User Api Test"""

    def test_post(self, client):
        """Test Case Api"""

        user = db.session.execute(
            sa.select(models.User).where(
                models.User.login == "admin",
            )
        ).scalar()

        session = db.session.execute(
            sa.select(models.Session).where(
                models.Session.user_id == user.id,
                models.Session.expired_at > datetime.datetime.now(),
            )
        ).scalar()
        body = dict(
            refresh_token=session.token,
        )

        rv = client.post(
            f"api/v1/user/refresh-token",
            json=body,
        )
        assert rv.status_code == 200

        rv = client.get(
            "api/v1/user/users",
            headers={"X-Auth-Token": rv.json["access_token"]},
        )
        assert rv.status_code == 200


@pytest.mark.use_user("user")
class TestSessionsApi:
    """User Api Test"""

    def test_get_and_put(self, client, headers):
        """Test Case Api"""

        rv = client.get("api/v1/user/sessions", headers=headers)

        assert rv.status_code == 200

        session_id = rv.json["items"][0]["id"]

        rv = client.put(
            f"api/v1/user/sessions/{session_id}/deactivate", headers=headers
        )
        assert rv.status_code == 200

