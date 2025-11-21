from flask import Flask, render_template, redirect, request
from config import Config
from extensions import db, migrate, oauth
from models import User
import jwt
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        db.create_all()
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    oauth.register(
        name="github",
        client_id=app.config["GITHUB_CLIENT_ID"],
        client_secret=app.config["GITHUB_CLIENT_SECRET"],
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "read:user user:email"}
    )

    from auth import auth
    app.register_blueprint(auth)


    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        token = request.cookies.get("access_token")
        user = None

        if token:
            try:
                payload = jwt.decode(
                    token,
                    app.config["JWT_SECRET"],
                    algorithms=["HS256"]
                )
                user = User.query.filter_by(
                    id=payload["sub"],
                    provider=payload["provider"]
                ).first()

            except Exception:
                user = None

        users = User.query.all()
        return render_template("dashboard.html", user=user, users=users)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
