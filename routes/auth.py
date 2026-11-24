from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from models.db import get_db_cursor
from extensions import limiter

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access your ConsciousCart workspace.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


@auth_bp.route("/")
def landing():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("15 per hour")
def register():
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        raw_email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if len(full_name) < 2:
            flash("Please enter your full name.", "danger")
            return render_template("auth/register.html")

        try:
            valid = validate_email(raw_email, check_deliverability=False)
            email = valid.normalized
        except EmailNotValidError:
            flash("Please provide a valid email address.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Password and confirmation do not match.", "danger")
            return render_template("auth/register.html")

        pw_hash = generate_password_hash(password)
        with get_db_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash("An account with this email already exists.", "danger")
                return render_template("auth/register.html")

            cur.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                (full_name, email, pw_hash),
            )
            user_id = cur.lastrowid
            cur.execute("INSERT INTO user_preferences (user_id) VALUES (%s)", (user_id,))
            cur.execute(
                "INSERT INTO shopping_lists (user_id, title, status) VALUES (%s, %s, 'active')",
                (user_id, "Weekly Responsible Groceries"),
            )

        flash("Account created successfully. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        with get_db_cursor() as cur:
            cur.execute("SELECT id, full_name, password_hash FROM users WHERE email = %s AND is_active = TRUE", (email,))
            user = cur.fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email address or password.", "danger")
            return render_template("auth/login.html")

        session.clear()
        session.permanent = True
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if len(new_password) < 8 or new_password != confirm_password:
            flash("Ensure the new password is at least 8 characters and matches confirmation.", "danger")
            return render_template("auth/forgot_password.html")

        with get_db_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user:
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (generate_password_hash(new_password), user["id"]),
                )

        flash("If the email exists in our records, the password has been updated.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("auth.landing"))