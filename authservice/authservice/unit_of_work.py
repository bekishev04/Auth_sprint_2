from .database.repositories import reg_repo
from .entrypoints.extensions import db


class UnitOfWork:
    """Unit Of Work"""

    def __init__(self):
        self._session = db.session

    def __enter__(self):
        """__enter__"""
        for attr, klass_ in reg_repo.items():
            setattr(self, attr, klass_(self._session))

        return self

    def __exit__(self, exn_type, exn_value, traceback):
        """__exit__"""

        if exn_type:
            self.rollback()

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def flush(self):
        self._session.flush()
