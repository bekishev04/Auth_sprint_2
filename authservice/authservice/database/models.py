import datetime
import uuid

from authservice.database import db
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID


class BaseModel(db.Model):
    """Parent BaseModel"""

    __abstract__ = True

    def __init__(self, **kwargs):
        super(BaseModel, self).__init__(**kwargs)

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
        comment="Идентификатор",
    )

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.current_timestamp(),
        comment="Дата создания",
    )

    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.current_timestamp(),
        onupdate=sa.func.current_timestamp(),
        comment="Дата обновления",
    )


class User(BaseModel):
    """Model For Users"""

    __tablename__ = "users"

    login = sa.Column(sa.String(255), comment="Логин", unique=True)
    full_name = sa.Column(sa.String(255), comment="ФИО")
    role = sa.Column(sa.String(255), comment="Роль")
    password = sa.Column(sa.String(255), comment="Пароль")
    last_login = sa.Column(sa.DateTime, comment="Последний вход")


class Session(BaseModel):
    """Model For Sessions"""

    __tablename__ = "sessions"

    user_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    token = sa.Column(sa.String(1000), comment="Токен доступа")
    expired_at = sa.Column(sa.DateTime, comment="Длительность жизни токена")

    user = orm.relationship("User", backref=orm.backref("sessions"))

    @property
    def is_active(self):
        if not self.expired_at:
            return False
        else:
            return bool(self.expired_at < datetime.datetime.now())


class LoginHistory(BaseModel):
    __tablename__ = "login_history"

    __table_args__ = (
        UniqueConstraint('user_id', 'logged_in_at'),
        {
            'postgresql_partition_by': 'RANGE (logged_in_at)',
        }
    )

    user_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    logged_in_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, primary_key=True)
    user_agent = db.Column(db.Text)

    def __repr__(self):
        return f'<UserSignIn {self.user_id}:{self.logged_in_at}>'
