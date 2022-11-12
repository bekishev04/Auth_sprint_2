import http
import re

from flask import Flask, jsonify, request
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import HTTPException

from ..database import db

MSG_UNAUTHORIZED = "Ошибка авторизации. Повторите попытку позже"
MSG_INTERNAL_ERROR = (
    "При обработке запроса произошла ошибка. Повторите попытку позже"
)
MSG_FORBIDDEN = "Отказано в доступе"
MSG_SQLALCHEMY_ERROR = (
    "При работе с бд произошла ошибка! Повторите попытку позже."
)


def init_errorhandler(app: Flask) -> None:
    """Init Error Handler"""

    @app.errorhandler(404)
    def not_found(e: HTTPException):
        logger.error(e)

        return (
            jsonify(
                message=e.description,
            ),
            e.code,
        )

    @app.errorhandler(403)
    def forbidden(e: HTTPException):
        logger.error(e)

        return (
            jsonify(
                message=MSG_FORBIDDEN,
            ),
            e.code,
        )

    @app.errorhandler(401)
    def unauthorized(e: HTTPException):
        logger.error(e)

        return (
            jsonify(
                message=MSG_UNAUTHORIZED,
            ),
            e.code,
        )

    @app.errorhandler(500)
    def internal_error(e: HTTPException):
        logger.error(e)

        return (
            jsonify(
                message=MSG_INTERNAL_ERROR,
            ),
            e.code,
        )

    @app.errorhandler(HTTPException)
    def handle_exception(e: HTTPException):
        logger.error(e)

        return (
            jsonify(
                message=e.description,
            ),
            e.code,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_exception_sqlalchemy(e: SQLAlchemyError):
        logger.exception(e)

        db.session.rollback()
        return (
            jsonify(
                message=MSG_SQLALCHEMY_ERROR,
            ),
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @app.errorhandler(ValidationError)
    def handle_exception_validation(e: ValidationError):
        logger.error(e)

        status = http.HTTPStatus.BAD_REQUEST
        if request.method in ("GET", "get"):
            status = http.HTTPStatus.UNPROCESSABLE_ENTITY

        return (
            jsonify(
                message=e.errors(),
            ),
            status,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_exception_sqlalchemy(e: SQLAlchemyError):
        logger.error(e)

        db.session.rollback()
        if isinstance(e, IntegrityError):
            regex = r"^DETAIL:  Key (.+)=(.+) already exists."
            matches = re.findall(regex, e.orig.pgerror, re.MULTILINE)

            resp = dict(
                msg="Такие данные уже используются.",
            )
            if matches:
                items = matches[0]
                keys, values = items

                pattern = re.compile("[^A-Za-z0-9,_.@-]")

                keys = pattern.sub("", keys).split(",")
                values = pattern.sub("", values).split(",")

                resp.update(
                    ctx=dict(
                        zip(keys, values),
                    ),
                )

            return (
                jsonify(
                    resp,
                ),
                400,
            )
