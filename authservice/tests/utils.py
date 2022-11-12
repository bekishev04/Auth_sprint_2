import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from authservice.database import db, models


def get_random_one(
    m: models.BaseModel,
    j: list | None = None,
    oj: list | None = None,
    w: ColumnElement | None = None,
):
    """Generate random"""

    if w is None:
        w = sa.true()

    if j is None:
        j = []

    if oj is None:
        oj = []

    q = sa.select(m)
    for _j in j:
        q = q.join(*_j)

    for _oj in oj:
        q = q.join(*_oj)

    q = q.where(w).order_by(
        sa.func.random(),
    )

    return (
        db.session.execute(
            q,
        )
        .scalars()
        .first()
    )


def get_random_list(
    m: models.BaseModel,
    j: list | None = None,
    oj: list | None = None,
    w: ColumnElement | None = None,
):
    """Generate random"""

    if w is None:
        w = sa.true()

    if j is None:
        j = []

    if oj is None:
        oj = []

    q = sa.select(m)
    for _j in j:
        q = q.join(*_j)

    for _oj in oj:
        q = q.join(*_oj)

    q = q.where(w).order_by(
        sa.func.random(),
    )

    return (
        db.session.execute(
            q,
        )
        .scalars()
        .all()
    )
