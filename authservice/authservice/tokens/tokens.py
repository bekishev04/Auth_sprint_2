import abc
import uuid
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4, UUID

from pydantic import ValidationError

from .. import schemas
from ..database import models
from ..unit_of_work import UnitOfWork
from ..utils.jwt_utils import get_jwt_token, decode_jwt_token, check_jwt_token
from ..config import cfg


class AbstractTokenManager:
    _uow: UnitOfWork = UnitOfWork()

    @abc.abstractmethod
    def get_token_pair(self, user_id: uuid.UUID) -> tuple[uuid4, str]:
        pass

    @abc.abstractmethod
    def check_refresh_token(self, token: str) -> bool:
        pass

    @abc.abstractmethod
    def refresh_access_token(self, refresh_token: str) -> uuid4:
        pass

    @abc.abstractmethod
    def invalidate_token(self, refresh_token: UUID):
        pass

    @abc.abstractmethod
    def invalidate_all_tokens(self, user_id: UUID):
        pass

    @abc.abstractmethod
    def decode_access_token(
        self, access_token: str
    ) -> Optional[schemas.JWTPayload]:
        pass

    @abc.abstractmethod
    def check_access_token(self, access_token: str) -> bool:
        pass


class TokenManager(AbstractTokenManager):
    def get_token_pair(self, user_id: uuid.UUID) -> tuple[str, uuid4]:
        with self._uow:
            user_row = self._uow.users.get(user_id)
        access_token_expiry_date = datetime.now() + timedelta(
            minutes=cfg.ACCESS_TOKEN_TTL
        )
        refresh_token_expiry_date = datetime.now() + timedelta(
            minutes=cfg.REFRESH_TOKEN_TTL
        )
        jwt_payload = schemas.JWTPayload(
            id=user_id,
            role=user_row.role,
            valid_through=access_token_expiry_date,
            full_name=user_row.full_name,
            login=user_row.login,
        )

        access_token = get_jwt_token(jwt_payload.json())
        refresh_token = uuid4()

        with self._uow:
            row = models.Session(user_id=user_id)
            row.token = refresh_token
            row.expired_at = refresh_token_expiry_date
            self._uow.tokens.add(row)
            self._uow.commit()
        return access_token, refresh_token

    def check_refresh_token(self, token: UUID) -> bool:
        with self._uow:
            row = self._uow.tokens.get_by(token=token)
            if not row:
                return False
            return row.expired_at and (
                row.expired_at > datetime.now()
            )  # expired_at может быть None

    def refresh_access_token(
        self, refresh_token: UUID
    ) -> Optional[tuple[str, uuid4]]:
        if not self.check_refresh_token(refresh_token):
            return None
        with self._uow:
            token_row = self._uow.tokens.get_by(token=refresh_token)
            user_row = self._uow.users.get(token_row.user_id)
            token_row.expired_at = None
            self._uow.commit()
        return self.get_token_pair(user_row.id)

    def invalidate_token(self, refresh_token: UUID) -> None:
        with self._uow:
            token_row = self._uow.tokens.get_by(token=refresh_token)
            if not token_row:
                return
            token_row.expired_at = None
            self._uow.commit()

    def invalidate_all_tokens(self, user_id: UUID) -> None:
        with self._uow:
            user_tokens = self._uow.tokens.fetch_by(
                user_id=user_id,
                max_expired_at=datetime.now(),
            )
            if not user_tokens:
                return
            with self._uow:
                for t in user_tokens:
                    t.expired_at = None
                    self._uow.tokens.add(t)
                self._uow.commit()

    def decode_access_token(
        self, access_token: str
    ) -> Optional[schemas.JWTPayload]:
        try:
            token = schemas.JWTPayload.parse_raw(
                decode_jwt_token(access_token)
            )
        except ValidationError:
            return None
        if token.valid_through < datetime.now():
            return None
        return token

    def check_access_token(self, access_token: str) -> bool:
        return check_jwt_token(access_token)
