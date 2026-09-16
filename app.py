from datetime import date, timedelta
from pathlib import Path
import sqlite3

from flask import Flask, abort, redirect, render_template, request, url_for, session

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
app.config["DATABASE"] = Path(app.root_path) / "lifestyle_guru.db"


def get_database_connection():
    """Return a connection to the team's existing SQLite database."""
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


def get_food_user_id(connection):
    """Get the food owner without adding authentication work in this pass.

    The current login screen does not set session['user_id'] yet.  During local
    development, the existing database has one approved user row, so that user
    can own food records.  Once authentication is integrated, it must set the
    session value instead of relying on this temporary single-user fallback.
    """
    session_user_id = session.get("user_id")
    if session_user_id is not None:
        return session_user_id

    users = connection.execute("SELECT id FROM users ORDER BY id LIMIT 2").fetchall()
    return users[0]["id"] if len(users) == 1 else None


def get_food_form_values():
    """Read the existing Add Food form fields in their displayed units."""
    name = request.form.get("meal_name", "").strip()
    meal_type = request.form.get("meal_type", "").strip()

    try:
        calories = float(request.form.get("calories", ""))
        protein = float(request.form.get("protein", ""))
        carbohydrates = float(request.form.get("carbs", ""))
        fats = float(request.form.get("fats", ""))
    except (TypeError, ValueError):
        abort(400, "Food nutrition values must be numbers.")

    if not name or not meal_type or min(calories, protein, carbohydrates, fats) < 0:
        abort(
            400, "Food details must include a name, meal type, and non-negative values."
        )

    return name, meal_type, calories, protein, carbohydrates, fats


def get_compact_date_options(requested_date):
    """Build the four-date selector used by dashboard and Add Food screens."""
    try:
        selected_date = (
            date.fromisoformat(requested_date) if requested_date else date.today()
        )
    except ValueError:
        selected_date = date.today()

    date_options = []
    for offset in (-1, 0, 1, 2):
        option_date = selected_date + timedelta(days=offset)
        date_options.append(
            {
                "value": option_date.isoformat(),
                "month": option_date.strftime("%b"),
                "day": option_date.day,
                "is_selected": option_date == selected_date,
            }
        )

    return selected_date, date_options


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("age"))

    return render_template("login.html")


@app.route("/age", methods=["GET", "POST"])
def age():
    if request.method == "POST":
        session["age"] = request.form.get("selected_age")
        print(f"User selected age: {session['age']}")
        return redirect(url_for("weight"))

    return render_template("age.html")


@app.route("/weight", methods=["GET", "POST"])
def weight():
    if request.method == "POST":
        session["weight"] = request.form.get("selected_weight")
        session["weight_unit"] = request.form.get("weight_unit", "Kg")

        print(f"User selected weight: {session['weight']}")
        return redirect(url_for("gender"))

    return render_template("weight.html")


@app.route("/gender", methods=["GET", "POST"])
def gender():
    if request.method == "POST":
        session["gender"] = request.form.get("gender")
        print(f"User selected gender: {session['gender']}")
        return redirect(url_for("height"))

    return render_template("gender.html")


@app.route("/height", methods=["GET", "POST"])
def height():
    if request.method == "POST":
        session["height"] = request.form.get("height_value")
        # Save whether they chose cm or inches (e.g., passing 'cm' or 'in' from your height template form)
        session["height_unit"] = request.form.get("height_unit", "cm")
        print(f"User selected height: {session['height']} ({session['height_unit']})")
        return redirect(url_for("activity"))

    return render_template("height.html")


@app.route("/activity", methods=["GET", "POST"])
def activity():
    if request.method == "POST":
        session["activity_level"] = request.form.get("activity")
        print(f"User selected activity: {session['activity_level']}")
        return redirect(url_for("goal"))

    return render_template("activity.html")


@app.route("/goal", methods=["GET", "POST"])
def goal():
    if request.method == "POST":
        session["goal"] = request.form.get("goal")
        print(f"User selected goal: {session['goal']}")
        return redirect(url_for("dashboard"))

    return render_template("goal.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    selected_date, date_options = get_compact_date_options(request.args.get("date"))

    return render_template(
        "dashboard.html",
        selected_date=selected_date,
        date_options=date_options,
    )


@app.route("/log_meal", methods=["GET", "POST"])
def log_meal():
    return render_template("log_meal.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        session["gender"] = request.form.get("gender")
        session["age"] = request.form.get("age")
        session["weight"] = request.form.get("weight")
        session["height"] = request.form.get("height")
        session["activity_level"] = request.form.get("activity_level")
        session["goal"] = request.form.get("goal")

        print(
            f"Profile Updated -> Gender: {session['gender']}, Age: {session['age']}, Weight: {session['weight']}, Height: {session['height']}, Activity: {session['activity_level']}, Goal: {session['goal']}"
        )
        return redirect(url_for("dashboard"))

    return render_template(
        "profile.html",
        user_gender=session.get("gender", "Female"),
        user_age=int(session.get("age", 19)),
        user_weight=session.get("weight", "62 kg"),
        user_height=session.get("height", "168 cm"),
        user_height_unit=session.get("height_unit", "cm"),
        user_activity=session.get("activity_level", "Moderately Active"),
        user_goal=session.get("goal", "Gain weight"),
    )


@app.route("/add_food", methods=["GET", "POST"])
def add_food():
    if request.method == "POST":
        name, meal_type, calories, protein, carbohydrates, fats = get_food_form_values()

        with get_database_connection() as connection:
            user_id = get_food_user_id(connection)
            if user_id is None:
                abort(409, "A food owner is required before a food item can be saved.")

            connection.execute(
                """
                INSERT INTO food_items
                    (user_id, name, meal_type, calories, protein_grams,
                     carbohydrate_grams, fat_grams)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, meal_type, calories, protein, carbohydrates, fats),
            )

        return redirect(url_for("food_library", filter="az"))
    selected_date, date_options = get_compact_date_options(request.args.get("date"))
    return render_template(
        "add_food.html", selected_date=selected_date, date_options=date_options
    )


@app.route("/food_library", methods=["GET", "POST"])
def food_library():
    selected_filter = request.args.get("filter", "favorites")
    if selected_filter not in {"az", "za", "favorites", "common"}:
        selected_filter = "favorites"

    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        food_items = []
        if user_id is not None:
            food_items = connection.execute(
                """
                SELECT id, name, meal_type, calories, protein_grams,
                       carbohydrate_grams, fat_grams
                FROM food_items
                WHERE user_id = ?
                ORDER BY name COLLATE NOCASE
                """,
                (user_id,),
            ).fetchall()

    return render_template(
        "food_library.html",
        food_items=food_items,
        selected_filter=selected_filter,
    )


@app.route("/foods/<int:food_id>/edit", methods=["GET", "POST"])
def edit_food(food_id):
    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        if user_id is None:
            abort(409, "A food owner is required before a food item can be edited.")

        food_item = connection.execute(
            """
            SELECT id, name, meal_type, calories, protein_grams,
                   carbohydrate_grams, fat_grams
            FROM food_items
            WHERE id = ? AND user_id = ?
            """,
            (food_id, user_id),
        ).fetchone()
        if food_item is None:
            abort(404)

        if request.method == "POST":
            name, meal_type, calories, protein, carbohydrates, fats = (
                get_food_form_values()
            )
            connection.execute(
                """
                UPDATE food_items
                SET name = ?, meal_type = ?, calories = ?, protein_grams = ?,
                    carbohydrate_grams = ?, fat_grams = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    name,
                    meal_type,
                    calories,
                    protein,
                    carbohydrates,
                    fats,
                    food_id,
                    user_id,
                ),
            )
            return redirect(url_for("food_library", filter="az"))

    selected_date, date_options = get_compact_date_options(request.args.get("date"))
    return render_template(
        "add_food.html",
        editing=True,
        food=food_item,
        selected_date=selected_date,
        date_options=date_options,
    )


@app.route("/set_goals", methods=["GET", "POST"])
def set_goals():
    if request.method == "POST":
        calories = request.form.get("calories")
        fats = request.form.get("fats")
        protein = request.form.get("protein")
        carbs = request.form.get("carbs")
        print(
            f"Updated Goals Saved -> Calories: {calories} kcal, Fats: {fats}g, "
            f"Protein: {protein}g, Carbs: {carbs}g"
        )
        return redirect(url_for("dashboard"))
    return render_template("set_goals.html")


@app.route("/daily_menu", methods=["GET", "POST"])
def daily_menu():
    selected_date = request.args.get("date", "12")
    selected_meal = request.args.get("meal", "Breakfast")

    return render_template(
        "daily_menu.html", selected_date=selected_date, selected_meal=selected_meal
    )


if __name__ == "__main__":
    app.run(debug=True)
