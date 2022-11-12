from flask.views import MethodView as FlaskMethodView

from authservice.tokens.tokens import TokenManager
from authservice.unit_of_work import UnitOfWork


class MethodView(FlaskMethodView):
    """Redefined MethodView from Flask"""

    def __init__(self, *args, **kwargs):
        self._uow: UnitOfWork = UnitOfWork()
        self.token_manager: TokenManager = TokenManager()
