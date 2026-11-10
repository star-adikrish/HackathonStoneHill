
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
import json
import os
import re
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# CONFIGURATION
# ==========================================

WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__)

# Vercel runs serverless instances. A random secret on each cold start
# invalidates sessions, so production must use one stable SECRET_KEY.
SECRET_KEY = os.environ.get("SECRET_KEY")
if os.environ.get("VERCEL") and not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Add a stable SECRET_KEY in Vercel "
        "Project Settings > Environment Variables."
    )
app.secret_key = SECRET_KEY or "local-development-only-change-this"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL"))
)

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data.json"
)

DATABASE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS famease_app_state (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


# ==========================================
# DATA MANAGEMENT
# ==========================================

def _default_data():
    return {
        "users": {},
        "user_expenses": {},
        "expenses": []
    }


def _database_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. Add your Supabase "
            "PostgreSQL connection string to Vercel Environment Variables."
        )

    import psycopg

    return psycopg.connect(
        DATABASE_URL,
        sslmode="require",
        connect_timeout=10
    )


def load_data():
    """
    Load FamEase data from persistent PostgreSQL on Vercel.
    Local development continues to use data.json.
    """
    if DATABASE_URL:
        with _database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(DATABASE_TABLE_SQL)
                cursor.execute(
                    "SELECT payload FROM famease_app_state WHERE id = 1"
                )
                row = cursor.fetchone()

                if row:
                    payload = row[0]
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    return payload

                initial_data = _default_data()
                cursor.execute(
                    """
                    INSERT INTO famease_app_state (id, payload)
                    VALUES (1, %s::jsonb)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (json.dumps(initial_data),)
                )
                return initial_data

    # Never silently fall back to an ephemeral file on Vercel.
    if os.environ.get("VERCEL"):
        raise RuntimeError(
            "DATABASE_URL is required on Vercel. Configure a persistent "
            "PostgreSQL database before using FamEase accounts."
        )

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                loaded = json.load(file)
                if isinstance(loaded, dict):
                    loaded.setdefault("users", {})
                    loaded.setdefault("user_expenses", {})
                    loaded.setdefault("expenses", [])
                    return loaded
        except (json.JSONDecodeError, OSError) as error:
            app.logger.exception("Could not load local data.json: %s", error)
            raise

    return _default_data()


def save_data(data):
    """
    Persist the existing FamEase data structure.
    PostgreSQL is used when DATABASE_URL is set; local JSON is for
    development only. Errors are raised so registration never reports
    success when the write failed.
    """
    if DATABASE_URL:
        with _database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(DATABASE_TABLE_SQL)
                cursor.execute(
                    """
                    INSERT INTO famease_app_state (id, payload, updated_at)
                    VALUES (1, %s::jsonb, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        payload = EXCLUDED.payload,
                        updated_at = NOW()
                    """,
                    (json.dumps(data),)
                )
        return True

    if os.environ.get("VERCEL"):
        raise RuntimeError(
            "Cannot save FamEase data: DATABASE_URL is not configured."
        )

    temporary_file = DATA_FILE + ".tmp"
    try:
        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_file, DATA_FILE)
        return True
    except OSError:
        app.logger.exception("Could not save local data.json")
        try:
            if os.path.exists(temporary_file):
                os.remove(temporary_file)
        except OSError:
            pass
        raise


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("demo_mode"):
        today = datetime.now().date()

        data = {
            "users": {
                session["user"]: {
                    "family_members": [
                        session["user"],
                        "Alex",
                        "Sam"
                    ]
                }
            },
            "user_expenses": {
                session["user"]: [
                    {
                        "date": today.strftime("%Y-%m-%d"),
                        "item": "Groceries",
                        "amount": 84.50,
                        "paid_by": "Alex"
                    },
                    {
                        "date": today.strftime("%Y-%m-%d"),
                        "item": "Family dinner",
                        "amount": 56.00,
                        "paid_by": "Sam"
                    },
                    {
                        "date": today.strftime("%Y-%m-%d"),
                        "item": "School supplies",
                        "amount": 32.75,
                        "paid_by": session["user"]
                    }
                ]
            }
        }

    else:
        data = load_data()

    user_expenses = data.get(
        "user_expenses", {}
    ).get(session["user"], [])

    # Migrate legacy expenses
    legacy_expenses = data.get("expenses", [])

    if legacy_expenses and not session.get("demo_mode"):
        migrated = False

        data.setdefault("user_expenses", {})
        data["user_expenses"].setdefault(
            session["user"], []
        )

        for expense in list(legacy_expenses):
            if expense.get("added_by") == session["user"]:
                data["user_expenses"][session["user"]].append(
                    expense
                )
                legacy_expenses.remove(expense)
                migrated = True

        if migrated:
            save_data(data)
            user_expenses = data["user_expenses"][session["user"]]

    # Family members
    users = data.get("users", {})
    user_data = users.get(session["user"], {})

    if isinstance(user_data, dict):
        family_members = list(
            user_data.get("family_members", [])
        )
    else:
        family_members = []

    if not family_members:
        existing_paid = list(
            dict.fromkeys([
                e["paid_by"]
                for e in user_expenses
                if e.get("paid_by")
            ])
        )

        family_members = (
            existing_paid if existing_paid
            else [session["user"]]
        )

    if session["user"] not in family_members:
        family_members.insert(0, session["user"])

    # Current month statistics
    current_month = datetime.now().strftime("%Y-%m")
    current_month_name = datetime.now().strftime("%B %Y")

    monthly_expenses = [
        e for e in user_expenses
        if e.get("date", "").startswith(current_month)
    ]

    monthly_total = sum(
        float(e.get("amount", 0))
        for e in monthly_expenses
    )

    all_time_total = sum(
        float(e.get("amount", 0))
        for e in user_expenses
    )

    indexed_monthly_expenses = [
        (index, expense)
        for index, expense in enumerate(user_expenses)
        if expense.get("date", "").startswith(current_month)
    ]

    indexed_monthly_expenses.sort(
        key=lambda x: x[1].get("date", ""),
        reverse=True
    )

    return render_template(
        "index.html",
        expenses=monthly_expenses,
        indexed_monthly_expenses=indexed_monthly_expenses,
        monthly_expenses=monthly_expenses,
        monthly_total=monthly_total,
        all_time_total=all_time_total,
        current_month_name=current_month_name,
        user=session["user"],
        family_members=family_members,
        demo_mode=session.get("demo_mode", False)
    )


# ==========================================
# DEMO MODE
# ==========================================

@app.route("/demo")
def demo():
    session.clear()
    session["user"] = "Demo"
    session["demo_mode"] = True

    return redirect(url_for("index"))


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")

        data = load_data()
        users = data.get("users", {})

        user_match = None

        if username in users:
            user_match = username
        else:
            for user in users:
                if user.strip().lower() == username.lower():
                    user_match = user
                    break

        if user_match:
            user_data = users[user_match]

            if isinstance(user_data, dict):
                stored_password = user_data.get("password", "")
            else:
                stored_password = user_data

            if check_password_hash(stored_password, password):
                session["user"] = user_match
                return redirect(url_for("index"))

        flash("Invalid username or password")

    return render_template("login.html")


# ==========================================
# REGISTRATION
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get("password", "")

        try:
            family_count = int(
                request.form.get("family_count", 0)
            )
            family_count = max(0, min(family_count, 50))
        except (ValueError, TypeError):
            family_count = 0

        if not username:
            flash("Username is required")
            return render_template("register.html")

        if not password:
            flash("Password is required")
            return render_template("register.html")

        data = load_data()
        users = data.get("users", {})

        if (
            username in users
            or any(
                u.strip().lower() == username.lower()
                for u in users
            )
        ):
            flash("Username already exists")

        else:
            family_members = []

            for i in range(1, family_count + 1):
                member_name = request.form.get(
                    f"family_member_{i}", ""
                ).strip()

                if (
                    member_name
                    and member_name not in family_members
                ):
                    family_members.append(member_name)

            if username not in family_members:
                family_members.insert(0, username)

            users[username] = {
                "password": generate_password_hash(password),
                "family_members": family_members
            }

            data["users"] = users

            if "user_expenses" not in data:
                data["user_expenses"] = {}

            if username not in data["user_expenses"]:
                data["user_expenses"][username] = []

            try:
                save_data(data)
            except Exception:
                app.logger.exception("Registration could not be saved")
                flash(
                    "We couldn't create your account right now. "
                    "Please try again in a moment."
                )
                return render_template("register.html"), 503

            flash("Registration successful! Please sign in.")

            return redirect(url_for("login"))

    return render_template("register.html")


# ==========================================
# ADD EXPENSE
# ==========================================

@app.route("/add_expense", methods=["POST"])
def add_expense():

    if "user" not in session:
        if request.is_json:
            return jsonify({"error": "Unauthorized"}), 401

        return redirect(url_for("login"))

    if session.get("demo_mode"):
        if request.is_json:
            return jsonify({
                "error": "Demo mode is read-only"
            }), 403

        flash(
            "Demo mode is read-only. "
            "Sign in or create an account to add expenses."
        )

        return redirect(url_for("index"))

    is_json = request.is_json

    payload = (
        request.get_json(silent=True)
        if is_json
        else request.form
    )

    if not payload:
        payload = request.form

    date = (
        payload.get("date")
        or datetime.now().strftime("%Y-%m-%d")
    ).strip()

    item = (payload.get("item") or "").strip()

    paid_by = (
        payload.get("paid_by")
        or session["user"]
    ).strip()

    amount_raw = payload.get("amount")

    if not item:
        if is_json:
            return jsonify({
                "error": "Item name is required"
            }), 400

        flash("Item name is required.")
        return redirect(url_for("index"))

    try:
        amount = float(amount_raw)

        if (
            not amount > 0
            or amount > 100000000
            or not amount < float("inf")
        ):
            raise ValueError()

    except (TypeError, ValueError):
        if is_json:
            return jsonify({
                "error": "Please enter a valid positive amount"
            }), 400

        flash("Please enter a valid positive amount.")
        return redirect(url_for("index"))

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        if is_json:
            return jsonify({"error": "Invalid date"}), 400

        flash("Please enter a valid date.")
        return redirect(url_for("index"))

    data = load_data()

    expense = {
        "date": date,
        "item": item,
        "amount": round(amount, 2),
        "paid_by": paid_by,
        "added_by": session["user"]
    }

    data.setdefault("user_expenses", {})
    data["user_expenses"].setdefault(
        session["user"], []
    )

    data["user_expenses"][session["user"]].append(
        expense
    )

    save_data(data)

    if is_json:
        return jsonify({
            "status": "success",
            "expense": expense
        })

    flash(f"Added expense: {item} (₹{amount:.2f})")

    return redirect(url_for("index"))


# ==========================================
# DELETE EXPENSE
# ==========================================

@app.route(
    "/delete_expense/<int:index>",
    methods=["POST"]
)
def delete_expense(index):

    if "user" not in session:
        if request.is_json:
            return jsonify({"error": "Unauthorized"}), 401

        return redirect(url_for("login"))

    if session.get("demo_mode"):
        if request.is_json:
            return jsonify({
                "error": "Demo mode is read-only"
            }), 403

        flash(
            "Demo mode is read-only. "
            "Sign in or create an account to delete expenses."
        )

        return redirect(url_for("index"))

    data = load_data()

    user_expenses = data.get(
        "user_expenses", {}
    ).get(session["user"], [])

    if 0 <= index < len(user_expenses):

        deleted = user_expenses.pop(index)

        data["user_expenses"][session["user"]] = (
            user_expenses
        )

        save_data(data)

        if request.is_json:
            return jsonify({
                "status": "success",
                "deleted": deleted
            })

        flash(
            f'Removed expense: {deleted.get("item", "")}'
        )

    else:
        if request.is_json:
            return jsonify({
                "error": "Expense not found"
            }), 404

        flash("Expense not found.")

    return redirect(url_for("index"))


# ==========================================
# CONTACT
# ==========================================

@app.route("/contact", methods=["POST"])
def contact():

    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not message:
        flash("Please enter your name and message.")
        return redirect(url_for("index"))

    flash(
        f"Thank you {name}! Your message has been received."
    )

    return redirect(url_for("index"))


# ==========================================
# WEATHER API PLACE VALIDATION
# ==========================================

def validate_place_exists(place_name):
    """
    Validate a place using WeatherAPI.

    Returns:
        (True, None) if the place is valid.
        (False, error_message) if the place is invalid.

    If WeatherAPI is unavailable or not configured,
    travel-cost calculations can still continue.
    """

    if not place_name or len(place_name.strip()) < 2:
        return False, "Place name too short"

    # WeatherAPI is optional for travel estimates.
    if not WEATHER_API_KEY:
        return True, None

    try:
        params = urllib.parse.urlencode({
            "key": WEATHER_API_KEY,
            "q": place_name.strip()
        })

        url = (
            "https://api.weatherapi.com/v1/current.json?"
            + params
        )

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "FamEase/1.0"
            }
        )

        # Default HTTPS certificate verification remains enabled.
        with urllib.request.urlopen(
            req,
            timeout=8
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

            if data.get("error"):
                return False, data["error"].get(
                    "message", "Place not found"
                )

            return True, None

    except urllib.error.HTTPError as e:

        if e.code == 400:
            try:
                body = json.loads(
                    e.read().decode("utf-8")
                )

                message = body.get(
                    "error", {}
                ).get(
                    "message", "Place not found"
                )

                return False, message

            except (ValueError, OSError):
                return False, "Place not found"

        # Authentication, rate-limit and service failures
        # should not prevent static travel estimates.
        print(
            f"WeatherAPI HTTP error {e.code}. "
            "Skipping place validation."
        )

        return True, None

    except Exception as e:

        print(
            f"WeatherAPI validation error: {e}. "
            "Skipping place validation."
        )

        return True, None


# ==========================================
# TRAVEL COST CALCULATOR
# NO GEMINI OR AI API REQUIRED
# ==========================================

@app.route(
    "/calculate_travel_cost",
    methods=["POST"]
)
def calculate_travel_cost():

    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid request data"
        }), 400

    destination = (
        data.get("destination") or ""
    ).strip()

    origin = (
        data.get("origin") or ""
    ).strip()

    try:
        days = max(
            1,
            min(365, int(data.get("days", 3)))
        )

        people = max(
            1,
            min(100, int(data.get("people", 1)))
        )

    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid number of days or travelers"
        }), 400

    if not destination:
        return jsonify({
            "error": "Please enter a destination"
        }), 400

    valid_dest, err_dest = validate_place_exists(
        destination
    )

    if not valid_dest:
        return jsonify({
            "error": (
                f'"{destination}" does not appear to be '
                f'a valid place. {err_dest}'
            )
        }), 400

    if origin:

        valid_origin, err_origin = validate_place_exists(
            origin
        )

        if not valid_origin:
            return jsonify({
                "error": (
                    f'"{origin}" does not appear to be '
                    f'a valid place. {err_origin}'
                )
            }), 400

    return get_static_travel_cost(
        destination,
        days,
        people
    )


# ==========================================
# STATIC TRAVEL COST ESTIMATES
# ==========================================

def get_static_travel_cost(
    destination,
    days,
    people
):

    dest_lower = destination.lower()

    base_costs = {

        "goa": {
            "accommodation": 2500,
            "food": 1200,
            "transport": 800,
            "activities": 1500
        },

        "kerala": {
            "accommodation": 2200,
            "food": 1000,
            "transport": 900,
            "activities": 1300
        },

        "rajasthan": {
            "accommodation": 2800,
            "food": 1100,
            "transport": 1200,
            "activities": 1600
        },

        "himachal pradesh": {
            "accommodation": 2000,
            "food": 900,
            "transport": 1500,
            "activities": 1200
        },

        "uttarakhand": {
            "accommodation": 1800,
            "food": 800,
            "transport": 1400,
            "activities": 1100
        },

        "kashmir": {
            "accommodation": 3000,
            "food": 1300,
            "transport": 1800,
            "activities": 2000
        },

        "andaman": {
            "accommodation": 4000,
            "food": 1500,
            "transport": 2500,
            "activities": 2200
        },

        "leh ladakh": {
            "accommodation": 2500,
            "food": 1000,
            "transport": 2000,
            "activities": 1800
        },

        "mumbai": {
            "accommodation": 3500,
            "food": 1400,
            "transport": 600,
            "activities": 1800
        },

        "delhi": {
            "accommodation": 3000,
            "food": 1200,
            "transport": 500,
            "activities": 1500
        },

        "bangalore": {
            "accommodation": 2800,
            "food": 1100,
            "transport": 600,
            "activities": 1200
        },

        "jaipur": {
            "accommodation": 2400,
            "food": 900,
            "transport": 800,
            "activities": 1400
        },

        "manali": {
            "accommodation": 2200,
            "food": 950,
            "transport": 1200,
            "activities": 1500
        },

        "shimla": {
            "accommodation": 2300,
            "food": 950,
            "transport": 1100,
            "activities": 1300
        },

        "dubai": {
            "accommodation": 7000,
            "food": 3000,
            "transport": 15000,
            "activities": 4500
        },

        "singapore": {
            "accommodation": 8000,
            "food": 3500,
            "transport": 18000,
            "activities": 5000
        },

        "london": {
            "accommodation": 12000,
            "food": 4500,
            "transport": 45000,
            "activities": 6000
        },

        "paris": {
            "accommodation": 11000,
            "food": 4200,
            "transport": 42000,
            "activities": 5500
        },

        "tokyo": {
            "accommodation": 9000,
            "food": 3800,
            "transport": 40000,
            "activities": 4800
        },

        "bangkok": {
            "accommodation": 3500,
            "food": 1600,
            "transport": 12000,
            "activities": 2200
        }
    }

    costs = None

    for dest_key, cost_dict in base_costs.items():

        if (
            dest_key in dest_lower
            or any(
                word in dest_lower
                for word in dest_key.split()
            )
        ):
            costs = cost_dict
            break

    if not costs:
        costs = {
            "accommodation": 2500,
            "food": 1000,
            "transport": 1000,
            "activities": 1200
        }

    # Shared accommodation for families
    rooms_needed = max(
        1,
        (people + 1) // 2
    )

    total_accommodation = (
        costs["accommodation"]
        * days
        * rooms_needed
    )

    total_food = (
        costs["food"]
        * days
        * people
    )

    total_transport = (
        costs["transport"]
        * people
    )

    total_activities = (
        costs["activities"]
        * days
        * people
    )

    grand_total = (
        total_accommodation
        + total_food
        + total_transport
        + total_activities
    )

    return jsonify({
        "accommodation": total_accommodation,
        "food": total_food,
        "transport": total_transport,
        "activities": total_activities,
        "total": grand_total
    })


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    debug_mode = (
        os.environ.get("FLASK_DEBUG", "0") == "1"
    )

    app.run(
        debug=debug_mode
    )
