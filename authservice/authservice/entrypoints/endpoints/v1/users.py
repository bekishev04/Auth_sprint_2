import http
import secrets
import string
import uuid

import requests

from authservice import schemas, cfg
from authservice.database import models
from flask import Blueprint, abort, g
from spectree import Response
from werkzeug.security import check_password_hash, generate_password_hash

from authservice.entrypoints import enums
from authservice.entrypoints.decorators import role_required, login_required
from authservice.entrypoints.extensions import spec_tree
from ._init import MethodView

bp = Blueprint("user", __name__, url_prefix="/user")

TAG = "User:"
E_PASSWORD_EQ_NEW_AND_OLD = "Новый пароль совпадает с предыдущим паролем"


class UserSignupApi(MethodView):
    """User Sign Up Api"""

    @spec_tree.validate(
        resp=Response("HTTP_400", HTTP_201=schemas.RespCreated),
        tags=[TAG + "Users"],
    )
    def post(self, json: schemas.ReqCreateUser):
        """Sign Up User"""
        with self._uow:
            row = models.User(
                **json.dict(),
                role=enums.UserRole.USER,
            )

            row.password = generate_password_hash(json.password)

            self._uow.users.add(row)
            self._uow.commit()

            schema = schemas.RespCreated(
                id=row.id,
            )

        return schema, http.HTTPStatus.CREATED


class UserLoginApi(MethodView):
    """User Login Endpoint"""

    @spec_tree.validate(
        resp=Response("HTTP_400", "HTTP_401", HTTP_200=schemas.RespLogon),
        tags=[TAG + "Users"],
    )
    def post(self, json: schemas.ReqLogin):
        """Login User"""

        with self._uow:
            row = self._uow.users.get_by(login=json.login)

            if not row:
                abort(http.HTTPStatus.NOT_FOUND)

        if check_password_hash(row.password, json.password):
            access_token, refresh_token = self.token_manager.get_token_pair(
                row.id
            )
            with self._uow:
                row = models.LoginHistory(
                    user_id=row.id,
                    user_agent=json.user_agent
                )

                self._uow.login_history.add(row)
                self._uow.commit()

            schema = schemas.RespLogon(
                id=row.id,
                access_token=access_token,
                refresh_token=refresh_token,
            )
            return schema, http.HTTPStatus.OK
        else:
            abort(http.HTTPStatus.UNAUTHORIZED)


class UserOAuthVKApi(MethodView):

    @spec_tree.validate(
        resp=Response("HTTP_400", "HTTP_401", HTTP_200=schemas.RespLogonOAuth),
        tags=[TAG + "UsersOAuthVK"],
    )
    def get(self, query: schemas.ReqOAuthVK):
        if not query.code:
            abort(http.HTTPStatus.BAD_REQUEST)
        link = 'https://oauth.vk.com/access_token'
        params = {'client_id': cfg.VK_APP_ID,
                  'client_secret': cfg.VK_CLIENT_SECRET,
                  'redirect_uri': cfg.VK_REDIRECT_URI,
                  'code': query.code}
        resp = requests.get(link, params=params)
        json = resp.json()
        if json.get('error', None):
            abort(http.HTTPStatus.BAD_REQUEST)
        vk_user_id = str(json.get('user_id', None))
        user_email = json.get('email', None)
        with self._uow:
            remote_user = self._uow.oauth_users.get_by(remote_user_id=vk_user_id)
            if remote_user:
                access_token, refresh_token = self.token_manager.get_token_pair(
                    remote_user.user_id
                )

                history_row = models.LoginHistory(
                    user_id=remote_user.user_id,
                    user_agent=g.user_agent
                )

                self._uow.login_history.add(history_row)
                self._uow.commit()
                return schemas.RespLogonOAuth(access_token=access_token,
                                              refresh_token=refresh_token,
                                              message='user found')
            else:
                alphabet = string.ascii_letters + string.digits
                random_password = ''.join(secrets.choice(alphabet) for _ in range(20))
                row = models.User(
                    login=user_email,
                    role=enums.UserRole.USER,
                    password=generate_password_hash(random_password)
                )
                self._uow.users.add(row)
                self._uow.commit()
                oauth_user = models.OAuthAccounts(
                    user_id=row.id,
                    service_user_id=vk_user_id
                )

                access_token, refresh_token = self.token_manager.get_token_pair(
                    oauth_user.user_id
                )
                self._uow.oauth_users.add(oauth_user)
                self._uow.commit()
                return schemas.RespLogonOAuth(access_token=access_token,
                                              refresh_token=refresh_token,
                                              message='user created')


class UserLogoutApi(MethodView):
    """User Logout Endpoint"""

    decorators = [login_required]

    @spec_tree.validate(
        resp=Response("HTTP_400", "HTTP_401", HTTP_200=schemas.RespMessage),
        tags=[TAG + "Users"],
    )
    def post(self, json: schemas.ReqLogout):
        """Logout User"""

        if not self.token_manager.check_access_token(json.access_token):
            abort(http.HTTPStatus.UNAUTHORIZED)
        self.token_manager.invalidate_token(json.refresh_token)
        return schemas.RespMessage(message="OK"), http.HTTPStatus.OK


class UserCompleteLogoutApi(MethodView):
    """User Complete Logout"""

    decorators = [login_required]

    @spec_tree.validate(
        resp=Response("HTTP_400", "HTTP_401", HTTP_200=schemas.RespMessage)
    )
    def post(self, json: schemas.ReqLogout):
        user = g.current_user
        self.token_manager.invalidate_all_tokens(user.id)
        return schemas.RespMessage(message="OK"), http.HTTPStatus.OK


class UserRefreshTokenApi(MethodView):
    """Refresh Token"""

    @spec_tree.validate(
        resp=Response("HTTP_400", "HTTP_401", HTTP_200=schemas.RespLogon)
    )
    def post(self, json: schemas.ReqRefreshToken):
        if not self.token_manager.check_refresh_token(json.refresh_token):
            abort(http.HTTPStatus.UNAUTHORIZED)
        try:
            (
                access_token,
                refresh_token,
            ) = self.token_manager.refresh_access_token(json.refresh_token)
            schema = schemas.RespLogon(
                access_token=access_token, refresh_token=refresh_token
            )
            return schema, http.HTTPStatus.OK
        except TypeError:
            # вместо токенов вернулся None
            abort(http.HTTPStatus.UNAUTHORIZED)


class UsersApi(MethodView):
    """Users Endpoint"""

    decorators = [login_required]

    @role_required(
        enums.UserRole.ADMIN,
    )
    @spec_tree.validate(
        resp=Response("HTTP_401", HTTP_200=schemas.ItemsUser),
        tags=[TAG + "Users"],
    )
    def get(self, query: schemas.ArgsUser):
        """Get Items User"""

        with self._uow:
            rows, cnt = self._uow.users.find_by(query)

        schema = schemas.ItemsUser(items=rows, total=cnt)

        return schema, http.HTTPStatus.OK


class UserApi(MethodView):
    """User Endpoint"""

    decorators = [login_required]

    @role_required(
        enums.UserRole.ADMIN,
    )
    @spec_tree.validate(
        resp=Response("HTTP_401", "HTTP_404", HTTP_200=schemas.ItemUser),
        tags=[TAG + "Manage"],
    )
    def get(self, id: uuid.UUID):
        """Get User"""

        with self._uow:
            row = self._uow.users.get(id)

        if not row:
            abort(
                http.HTTPStatus.NOT_FOUND,
            )

        schema = schemas.ItemUser.from_orm(row)

        return schema, http.HTTPStatus.OK

    @role_required(
        enums.UserRole.ADMIN,
    )
    @spec_tree.validate(
        resp=Response("HTTP_401", "HTTP_404", HTTP_200=schemas.RespMessage),
        tags=[TAG + "Manage"],
    )
    def put(self, id: uuid.UUID, json: schemas.ReqUpdateUser):
        """Edit User"""

        with self._uow:
            row = self._uow.users.get(id)

            if not row:
                abort(
                    http.HTTPStatus.NOT_FOUND,
                )

            row.login = json.login
            row.full_name = json.full_name

            self._uow.users.add(row)
            self._uow.commit()

        schema = schemas.RespMessage(
            message=http.HTTPStatus.OK.phrase,
        )

        return schema, http.HTTPStatus.OK

    @role_required(
        enums.UserRole.ADMIN,
    )
    @spec_tree.validate(
        resp=Response("HTTP_401", "HTTP_404", HTTP_200=schemas.RespMessage),
        tags=[TAG + "Manage"],
    )
    def delete(self, id: uuid.UUID):
        """Delete User"""

        with self._uow:
            row = self._uow.users.get(id)

            if not row:
                abort(
                    http.HTTPStatus.NOT_FOUND,
                )

            if row.id == g.current_user.id:
                abort(
                    http.HTTPStatus.BAD_REQUEST,
                )

            self._uow.users.delete(row)
            self._uow.commit()

        schema = schemas.RespMessage(
            message=http.HTTPStatus.OK.phrase,
        )

        return schema, http.HTTPStatus.OK


class UserHistoryApi(MethodView):
    decorators = [login_required]

    @spec_tree.validate(
        resp=Response("HTTP_401", "HTTP_404", HTTP_200=schemas.RespHistoryItems),
        tags=[TAG + "History"]
    )
    def get(self, query: schemas.ReqHistory):
        if query.user_id and (query.user_id != g.current_user.id and g.current_user.role != enums.UserRole.ADMIN):
            abort(http.HTTPStatus.UNAUTHORIZED)
        user_id, before, after = query.user_id if query.user_id else g.current_user.id, query.before, query.after
        with self._uow:
            rows = self._uow.login_history.fetch_by(user_id=user_id, before=before, after=after)
        return schemas.RespHistoryItems(items=rows)


class UserPasswordEditApi(MethodView):
    """Edit Password Endpoint"""

    @spec_tree.validate(
        resp=Response("HTTP_401", "HTTP_404", HTTP_200=schemas.RespMessage),
        tags=[TAG + "Users"],
    )
    def post(self, id: uuid.UUID, json: schemas.ReqUserPasswordEdit):
        """Edit User password"""

        with self._uow:
            row = self._uow.users.get(id)

            if not row:
                abort(
                    http.HTTPStatus.NOT_FOUND,
                )

            if not check_password_hash(row.password, json.password_old):
                abort(
                    http.HTTPStatus.UNAUTHORIZED,
                )

            if check_password_hash(row.password, json.password):
                abort(
                    http.HTTPStatus.BAD_REQUEST,
                    E_PASSWORD_EQ_NEW_AND_OLD,
                )

            row.password = generate_password_hash(json.password)
            row.is_new = False

            self._uow.commit()

        schema = schemas.RespMessage(
            message=http.HTTPStatus.OK.phrase,
        )

        return schema, http.HTTPStatus.OK


class UsersSessionsApi(MethodView):
    """User Sessions Endpoint"""

    decorators = [login_required]

    @spec_tree.validate(
        resp=Response("HTTP_401", HTTP_200=schemas.ItemsSession),
        tags=[TAG + "Users"],
    )
    def get(self, query: schemas.ArgsPaginate):
        """Get User All Sessions"""

        with self._uow:
            rows, cnt = self._uow.tokens.find_by(query)

        schema = schemas.ItemsSession(items=rows, total=cnt)

        return schema, http.HTTPStatus.OK


class UserSessionsApi(MethodView):
    """User Sessions Endpoint"""

    decorators = [login_required]

    @spec_tree.validate(
        resp=Response("HTTP_401", "HTTP_404", HTTP_200=schemas.RespMessage),
        tags=[TAG + "Users"],
    )
    def put(self, id: uuid.UUID):
        """Deactivate User Session"""

        with self._uow:
            row = self._uow.tokens.get(id)

            if not row:
                abort(
                    http.HTTPStatus.NOT_FOUND,
                )

            row.expired_at = None

            self._uow.tokens.add(row)
            self._uow.commit()

        schema = schemas.RespMessage(
            message=http.HTTPStatus.OK.phrase,
        )

        return schema, http.HTTPStatus.OK


bp.add_url_rule(
    "/signup",
    view_func=UserSignupApi.as_view("user-signup"),
    methods=["POST"],
)

bp.add_url_rule(
    "/login",
    view_func=UserLoginApi.as_view("user-login"),
    methods=["POST"],
)

bp.add_url_rule(
    "/logout",
    view_func=UserLogoutApi.as_view("user-logout"),
    methods=["POST"],
)

bp.add_url_rule(
    "/complete_logout",
    view_func=UserCompleteLogoutApi.as_view("user-complete-logout"),
    methods=["POST"],
)

bp.add_url_rule(
    "/refresh-token",
    view_func=UserRefreshTokenApi.as_view("user-refresh-token"),
    methods=["POST"],
)

bp.add_url_rule(
    "/users",
    view_func=UsersApi.as_view("users"),
    methods=["GET"],
)

bp.add_url_rule(
    "/users/<uuid:id>",
    view_func=UserApi.as_view("user"),
    methods=["GET", "PUT", "DELETE"],
)

bp.add_url_rule(
    "/users/<uuid:id>/password-edit",
    view_func=UserPasswordEditApi.as_view("password_edit"),
    methods=["POST"],
)

bp.add_url_rule(
    "/sessions",
    view_func=UsersSessionsApi.as_view("sessions"),
    methods=["GET"],
)

bp.add_url_rule(
    "/sessions/<uuid:id>/deactivate",
    view_func=UserSessionsApi.as_view("session_deactivate"),
    methods=["PUT"]
)

bp.add_url_rule(
    "/login_history",
    view_func=UserHistoryApi.as_view("login_history"),
    methods=["GET"]
)

bp.add_url_rule(
    "/oauthvk",
    view_func=UserOAuthVKApi.as_view("oauthvk"),
    methods=["GET"]
)
