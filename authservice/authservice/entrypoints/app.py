import datetime
import re
import typing as t
import uuid

from flask import Flask, g, request
from flask import typing as ft
from flask.json.provider import DefaultJSONProvider as _JSONProvider
from flask.wrappers import Request

from ..config import cfg
from ..entrypoints.blueprints import init_blueprint
from ..entrypoints.errorhandler import init_errorhandler
from ..entrypoints.extensions import init_extensions
from ..tokens.tokens import TokenManager


class _CustomJSONProvider(_JSONProvider):
    """Custom Json Provider"""

    @staticmethod
    def default(o: t.Any):
        """Default methods"""

        if isinstance(o, datetime.date):
            return o.isoformat()

        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return _JSONProvider.default(o)


def create_app() -> Flask:
    """Запуск приложения"""

    app = Flask(__name__)
    app.config.from_object(cfg)

    app.json = _CustomJSONProvider(app)
    app.json.sort_keys = False

    # init extension
    init_extensions(app)

    # init blueprint
    init_blueprint(app)

    # init errorhandler
    init_errorhandler(app)

    @app.before_request
    def _before_request_handler() -> None:
        version = app.config.get("API_VERSION")
        request_id = uuid.uuid4()

        h_accept = request.headers.get("Accept")
        if h_accept:
            raw_version = re.match(
                r"application/app.v\d.\d?.\w*",
                h_accept,
                re.I | re.M,
            )

            if raw_version:
                p = re.compile(r"[^\d.]")
                version = float(
                    p.sub("", raw_version.group()).rstrip(".").lstrip("."),
                )

        # Request Id From Frontend
        h_request_id = request.headers.get("X-Request-Id")
        if h_request_id:
            try:
                request_id = uuid.UUID(h_request_id)
            except (ValueError, TypeError):
                pass

        g.version = version
        g.request_id = request_id

        g.current_user = None
        h_access_token = request.headers.get("X-Auth-Token")
        if h_access_token:
            token_manager = (
                TokenManager()
            )  # todo вынести инициализацию токен-менеджера куда-нибудь ещё...
            g.current_user = token_manager.decode_access_token(h_access_token)

    @app.after_request
    def _after_request_handler(response: ft.ResponseClass) -> ft.ResponseClass:
        response.headers["X-Media-Type"] = f"app.v{g.version}"
        response.headers["X-Request-Id"] = g.request_id

        # Отправим фронту token
        if hasattr(g, "token"):
            response.headers["X-Session-Token"] = g.token

        response.headers[
            "Access-Control-Expose-Headers"
        ] = "X-Session-Token, X-Media-Type, X-Request-Id, Content-Disposition"

        return response

    return app
