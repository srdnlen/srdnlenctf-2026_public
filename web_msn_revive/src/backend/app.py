from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object("config.Config")

    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{instance_path / 'app.db'}"
    )

    app.config["EMOTICONS_DIR"] = instance_path / "emoticons"
    app.config["EMOTICONS_DIR"].mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from models import User, ChatSession, Message, Export  # noqa: F401

    with app.app_context():
        db.create_all()

    from utils import init_db

    with app.app_context():
        init_db()

    from api import api

    app.register_blueprint(api, url_prefix="/api")

    return app
