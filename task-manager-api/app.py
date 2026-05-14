"""Composition root para o Task Manager API.

Refatorado pela skill `refactor-arch`:
- SECRET_KEY, DEBUG, ALLOWED_ORIGINS e creds SMTP movidos para env (config/settings.py).
- Senhas com bcrypt (substitui MD5 sem salt).
- to_dict() do User não expõe mais a senha.
- JWT real assinado com SECRET_KEY (substitui o "fake-jwt-token-N").
- datetime.utcnow → datetime.now(timezone.utc).
- Query.get → db.session.get.
- Lógica de negócio movida das rotas para services/.
- Lógica de overdue centralizada em Task.is_overdue() (era duplicada 4×).
- Validação via marshmallow schemas (substitui validação ad-hoc).
- Bare except: removido — error handler centralizado em middlewares/error_handler.py.
- N+1 em listagem de tasks e relatórios eliminado com joinedload().
- Blueprint de categorias extraído de report_routes para category_routes.
- NotificationService recebe credenciais via env, com flag NOTIFICATIONS_ENABLED.
"""
import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.auth_routes import auth_bp
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
    )


def create_app() -> Flask:
    _configure_logging()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG

    CORS(app, origins=settings.ALLOWED_ORIGINS)
    db.init_app(app)

    # Importar os models antes do create_all() para registrar as tabelas.
    from models import task, user, category  # noqa: F401

    register_error_handlers(app)
    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(auth_bp)

    @app.route('/')
    def index():
        from datetime import datetime, timezone
        return jsonify({'message': 'Task Manager API', 'version': '1.0',
                        'now': str(datetime.now(timezone.utc))})

    @app.route('/health')
    def health():
        from datetime import datetime, timezone
        return jsonify({'status': 'ok',
                        'timestamp': str(datetime.now(timezone.utc))})

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host='0.0.0.0', port=5000)
