import logging

from flask import Flask, jsonify
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException

from services.auth_service import InactiveUserError, InvalidCredentialsError
from services.category_service import CategoryNotFoundError
from services.task_service import RelatedNotFoundError, TaskNotFoundError
from services.user_service import EmailAlreadyUsedError, UserNotFoundError

log = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(MarshmallowValidationError)
    def _validation(err: MarshmallowValidationError):
        return jsonify({'error': 'Dados inválidos', 'details': err.messages}), 400

    @app.errorhandler(TaskNotFoundError)
    @app.errorhandler(UserNotFoundError)
    @app.errorhandler(CategoryNotFoundError)
    @app.errorhandler(RelatedNotFoundError)
    def _not_found(err: Exception):
        return jsonify({'error': str(err)}), 404

    @app.errorhandler(EmailAlreadyUsedError)
    def _conflict(err: EmailAlreadyUsedError):
        return jsonify({'error': str(err)}), 409

    @app.errorhandler(InvalidCredentialsError)
    def _unauthorized(err: InvalidCredentialsError):
        return jsonify({'error': str(err)}), 401

    @app.errorhandler(InactiveUserError)
    def _forbidden(err: InactiveUserError):
        return jsonify({'error': str(err)}), 403

    @app.errorhandler(HTTPException)
    def _http(err: HTTPException):
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def _unhandled(err: Exception):
        log.exception('unhandled.exception')
        return jsonify({'error': 'Erro interno do servidor'}), 500
