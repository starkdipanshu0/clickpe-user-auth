import os
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, redirect, url_for, make_response, request, current_app
from extensions import db, oauth
from models import User


auth = Blueprint("auth", __name__)


# ------------------------------------------
# GOOGLE LOGIN
# ------------------------------------------
@auth.route("/auth/google/start")
def google_start():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route("/auth/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")

    if not userinfo:
        # Fallback to ID token parsing (rare cases)
        userinfo = oauth.google.parse_id_token(token)

    google_id = userinfo["sub"]
    email = userinfo.get("email")
    name = userinfo.get("name")
    avatar = userinfo.get("picture")

    user = User.query.filter_by(id=google_id, provider="google").first()

    if not user:
        user = User(
            id=google_id,
            provider="google",
            name=name,
            email=email,
            avatar_url=avatar,
            last_login=datetime.utcnow()
        )
        db.session.add(user)
    else:
        user.last_login = datetime.utcnow()

    db.session.commit()

    encoded = _generate_jwt("google", google_id, email)

    resp = make_response(redirect("/dashboard"))
    resp.set_cookie("access_token", encoded, httponly=True, samesite="Lax")
    return resp


# ------------------------------------------
# GITHUB LOGIN
# ------------------------------------------
@auth.route("/auth/github/start")
def github_start():
    redirect_uri = url_for("auth.github_callback", _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@auth.route("/auth/github/callback")
def github_callback():
    token = oauth.github.authorize_access_token()

    # Basic user info
    user_data = oauth.github.get("user").json()
    emails = oauth.github.get("user/emails").json()

    github_id = str(user_data["id"])
    name = user_data.get("name") or user_data.get("login")
    avatar = user_data.get("avatar_url")

    # find primary verified email
    email = None
    for e in emails:
        if e.get("primary") and e.get("verified"):
            email = e["email"]
            break
    if not email and emails:
        email = emails[0]["email"]

    # Upsert user
    user = User.query.filter_by(id=github_id, provider="github").first()
    if not user:
        user = User(
            id=github_id,
            provider="github",
            name=name,
            email=email,
            avatar_url=avatar,
            last_login=datetime.utcnow(),
        )
        db.session.add(user)
    else:
        user.last_login = datetime.utcnow()

    db.session.commit()

    encoded = _generate_jwt("github", github_id, email)

    resp = make_response(redirect("/dashboard"))
    resp.set_cookie("access_token", encoded, httponly=True, samesite="Lax")
    return resp

@auth.route("/logout")
def logout():
    resp = redirect("/")
    resp.set_cookie("access_token", "", expires=0)
    return resp
# ------------------------------------------
# Helper: Generate JWT
# ------------------------------------------
def _generate_jwt(provider, uid, email):
    payload = {
        "sub": uid,
        "email": email,
        "provider": provider,
        "exp": datetime.utcnow() + timedelta(hours=8),
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET"],
        algorithm="HS256"
    )
    # pyjwt may return bytes in some envs — ensure it's a str
    if isinstance(token, bytes):
        token = token.decode()
    return token

