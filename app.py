from flask import Flask, jsonify
from extensions import db, migrate, bcrypt


def create_app(config=None):
    app = Flask(__name__)

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    if config:
        app.config.from_object(config)

    db.init_app(app)
    from auth import models as _auth_models  # noqa: F401
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    from auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    @app.route("/")
    def home():
        return "Hola Flask"

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
