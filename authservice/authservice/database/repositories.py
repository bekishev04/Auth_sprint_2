import abc
import datetime
import uuid

from sqlalchemy import orm as so
import sqlalchemy as sa
from .. import schemas
from ..entrypoints.extensions import Registry
from authservice.database import models
from flask import g

reg_repo = Registry()


class AbstractRepository(abc.ABC):
    """Base Repository"""

    def __init__(self, session: so.scoped_session):
        self.session = session

    @abc.abstractmethod
    def find_by(self, query: schemas.BaseModel):
        """Search data by Query"""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, id_: int):
        """Get Row By Id"""
        raise NotImplementedError


class BaseRepo(AbstractRepository):

    _model = None

    def find_by(self, query: schemas.BaseModel):
        """Search data by Query"""
        raise NotImplementedError

    def get(self, _id: uuid.UUID):
        return self.session.get(self._model, _id)

    def add(self, row):
        self.session.add(row)

    def delete(self, row):
        self.session.delete(row)


@reg_repo.register("users")
class UserRepository(BaseRepo):

    _model = models.User

    def find_by(self, query: schemas.ArgsUser):

        where = sa.true()
        if query.full_name:
            where &= models.User.full_name.ilike(f"%{query.full_name}%")

        if query.role:
            where &= models.User.role == query.role

        # total rows by where
        cnt = self.session.execute(
            sa.select(sa.func.count(sa.distinct(models.User.id))).where(
                where,
            )
        ).scalar()

        sql = self.session.execute(
            sa.select(models.User)
            .where(
                where,
            )
            .order_by(
                sa.desc(models.User.created_at),
            )
            .limit(query.limit)
            .offset(query.offset)
        )

        rows = sql.scalars().all()

        return rows, cnt

    def get_by(self, *, login: str = None):
        where = sa.true()
        if login:
            where &= models.User.login == login
        sql = self.session.execute(sa.select(models.User).where(where))
        row = sql.scalar()
        return row


@reg_repo.register("tokens")
class TokenRepository(BaseRepo):
    _model = models.Session

    def find_by(self, query: schemas.ArgsPaginate):
        where = sa.true()

        where &= models.Session.user_id == g.current_user.id

        # total rows by where
        cnt = self.session.execute(
            sa.select(sa.func.count(sa.distinct(models.Session.id))).where(
                where,
            )
        ).scalar()

        sql = self.session.execute(
            sa.select(models.Session)
            .where(
                where,
            )
            .order_by(
                sa.desc(models.Session.created_at),
            )
            .limit(query.limit)
            .offset(query.offset)
        )

        rows = sql.scalars().all()

        return rows, cnt

    def fetch_by(
        self,
        *,
        user_id: uuid.UUID = None,
        max_expired_at: datetime.datetime = None,
    ):
        where = sa.true()

        if user_id:
            where &= models.Session.user_id == user_id

        if max_expired_at:
            where &= models.Session.expired_at < max_expired_at

        sql = self.session.execute(sa.select(models.Session).where(where))
        rows = sql.scalars().all()

        return rows

    def get_by(self, *, token: uuid.UUID = None):
        where = sa.true()
        if token:
            where &= models.Session.token == str(token)
        sql = self.session.execute(sa.select(models.Session).where(where))
        row = sql.scalar()
        return row


@reg_repo.register("login_history")
class HistoryRepository(BaseRepo):
    _model = models.LoginHistory

    def find_by(self, query: schemas.ArgsHistory, *, user_id=None):
        where = sa.true()
        if user_id:
            where &= models.LoginHistory.user_id == user_id
        if query.after:
            where &= models.LoginHistory.logged_in_at > query.after
        if query.before:
            where &= models.LoginHistory.logged_in_at < query.before
        sql = self.session.execute(sa.select(models.LoginHistory).where(where))
        rows = sql.scalars().all()
        return rows
