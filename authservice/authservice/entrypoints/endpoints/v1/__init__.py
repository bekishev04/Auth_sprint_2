from flask import Blueprint

from authservice.entrypoints.endpoints.v1.initialization import bp as bp_init
from authservice.entrypoints.endpoints.v1.users import bp as bp_user


bp_v1 = Blueprint("v1", __name__, url_prefix="/v1")

bp_v1.register_blueprint(bp_init)
bp_v1.register_blueprint(bp_user)


__all__ = (
    "bp_v1",
)
