from collections import OrderedDict

from flask import Flask
from flask_cors import CORS
from pydantic import EmailStr
from spectree import SpecTree
from spectree.config import Contact
from spectree.models import (
    Server,
    SecurityScheme,
    SecuritySchemeData,
    SecureType,
)

from ..config import cfg
from ..database import db, migrate


spec_tree = SpecTree(
    "flask",
    mode="strict",
    title="Docs AuthService API",
    version=cfg.API_VERSION,
    annotations=True,
    contact=Contact(
        name="Бекишев Матвей",
        email=EmailStr("bekishev04@yandex.ru"),
    ),
    servers=[
        Server(
            url="http://127.0.0.1:5555/",
            description="Local Server",
        ),
    ],
    security_schemes=[
        SecurityScheme(
            # todo баг библиотеки
            name="auth_apiKey_backup",
            data={"type": "apiKey", "name": "Authorization", "in": "header"},
        ),
        # SecurityScheme(
        #     name="ApiKey",
        #     data=SecuritySchemeData(
        #         type=SecureType.HTTP,
        #         description="Access Token in AuthService API",
        #         scheme="bearer",
        #         bearerFormat="UUID",
        #     ),
        # ),
    ],
    security=dict(
        ApiKey=[],
    ),
)


def init_extensions(app: Flask) -> Flask:
    """Init Exceptions"""

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # docs
    spec_tree.register(app)

    return app


class Registry:
    """Register Class"""

    _registry_: OrderedDict = OrderedDict()

    def register(self, name: str):
        def wrap(entity):
            self._registry_[name] = entity

            return entity

        return wrap

    def items(self):
        return self._registry_.items()
