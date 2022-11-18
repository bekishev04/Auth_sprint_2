import sqlalchemy.orm as so

from .database import repositories as repo

class UnitOfWork:
    _session: so.scoped_session

    # repositories
    users: repo.UserRepository
    tokens: repo.TokenRepository
    login_history: repo.HistoryRepository
    oauth_users: repo.OAuthAccountsRepository

    def __init__(self): ...
    def __enter__(self) -> UnitOfWork: ...
    def __exit__(self) -> None: ...
    def commit(self) -> None: ...
    def flush(self) -> None: ...
    def rollback(self) -> None: ...
