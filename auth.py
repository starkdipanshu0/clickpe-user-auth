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
    # Force HTTPS scheme for the callback if not in debug mode (optional but safer for OAuth)
    # relying on ProxyFix from app.py is usually enough, but this is explicit.
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route("/auth/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")

    if not userinfo:
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

    # --- CHANGE 1: Use url_for instead of hardcoded string ---
    resp = make_response(redirect(url_for("dashboard")))
    
    # --- CHANGE 2: Add secure=True for HTTPS production apps ---
    # This ensures the cookie is only sent over encrypted connections.
    is_production = not current_app.debug
    resp.set_cookie(
        "access_token", 
        encoded, 
        httponly=True, 
        samesite="Lax", 
        secure=is_production  # Only set Secure=True if not debugging locally
    )
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

    user_data = oauth.github.get("user").json()
    emails = oauth.github.get("user/emails").json()

    github_id = str(user_data["id"])
    name = user_data.get("name") or user_data.get("login")
    avatar = user_data.get("avatar_url")

    email = None
    for e in emails:
        if e.get("primary") and e.get("verified"):
            email = e["email"]
            break
    if not email and emails:
        email = emails[0]["email"]

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

    # --- CHANGE 1: Use url_for here too ---
    resp = make_response(redirect(url_for("dashboard")))
    
    # --- CHANGE 2: Secure cookie ---
    is_production = not current_app.debug
    resp.set_cookie(
        "access_token", 
        encoded, 
        httponly=True, 
        samesite="Lax", 
        secure=is_production
    )
    return resp

@auth.route("/logout")
def logout():
    # --- CHANGE 1: Use url_for("index") instead of "/" ---
    resp = redirect(url_for("index"))
    resp.set_cookie("access_token", "", expires=0)
    return resp

# ... (Helper function remains the same)
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
    if isinstance(token, bytes):
        token = token.decode()
    return token