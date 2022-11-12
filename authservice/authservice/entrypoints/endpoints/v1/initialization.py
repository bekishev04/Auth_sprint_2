from flask import Blueprint, jsonify

from ._init import MethodView

bp = Blueprint("initialization", __name__)

_TAG_ = "Initialization__"


class WelcomeApi(MethodView):
    """Welcome API"""

    def get(self):
        """Welcome Api"""

        return "Welcome, AuthService API"


bp.add_url_rule("/", view_func=WelcomeApi.as_view("welcome"))
