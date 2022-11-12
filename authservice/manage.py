#!/usr/bin/env python3
import argparse
import os

from loguru import logger

from authservice import create_app
from authservice.database import db, models
from authservice.entrypoints import enums

app = create_app()


def local_up() -> None:
    """Функция для запуска локального сервера с локальной базой данных"""

    parser = argparse.ArgumentParser(description="Parse args in script")
    parser.add_argument(
        "-db",
        dest="db",
        default="up",
        help="Options [up, down]",
    )
    args = parser.parse_args()

    if args.db and args.db in ("up", "down"):
        os.system(
            "docker-compose -f ../docker-compose.yml %s %s authservice_db"
            % (args.db, "-d" if args.db == "up" else "")
        )

    # os.system("gunicorn manage:app -b 0.0.0.0:5555 --reload")
    os.system("flask run -p 5555 --reload")


def local_down() -> None:
    """Функция для остановки локальной базой данных"""

    os.system("docker-compose -f ../docker-compose.yml down")


def create_user() -> None:
    """Функция для создания пользователя"""

    parser = argparse.ArgumentParser(description="Parse Argument for create User")

    parser.add_argument(
        "login",
        type=str,
        default="admin",
        help="argument -login Default value is 'admin'",
    )
    parser.add_argument(
        "password",
        type=str,
        default="admin",
        help="argument -password Default value is 'admin'",
    )
    parser.add_argument(
        "role",
        type=enums.UserRole,
        default=enums.UserRole.ADMIN,
        help=f"argument -role Default value is '{enums.UserRole.ADMIN}'",
    )
    parser.add_argument(
        "full_name",
        type=str,
        help="argument -full_name Required",
    )
    args = parser.parse_args()
    with app.app_context():
        user = models.User(
            login=args.login,
            password=args.password,
            role=args.role,
            full_name=args.full_name,
        )

        db.session.add(user)
        db.session.commit()
        logger.info(f"User Created: {user.id}")


if __name__ == "__main__":
    app.run(debug=app.config["FLASK_DEBUG"])
