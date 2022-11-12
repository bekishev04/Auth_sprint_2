from flask import Blueprint, Flask

from ..entrypoints.endpoints import bp_v1

bp_api = Blueprint("api", __name__, url_prefix="/api")


def init_blueprint(app: Flask) -> Flask:
    # group api

    bp_api.register_blueprint(bp_v1)

    # url api
    app.register_blueprint(bp_api)

    return app


__all__ = ("init_blueprint",)
