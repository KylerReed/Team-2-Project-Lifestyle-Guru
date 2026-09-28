from datetime import date, timedelta
from pathlib import Path
import sqlite3

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    session,
)

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


def get_goal_form_values():
    """Validate the existing Set Goals form in its displayed units."""
    try:
        calories = int(request.form.get("calories", ""))
        fats = int(request.form.get("fats", ""))
        protein = int(request.form.get("protein", ""))
        carbohydrates = int(request.form.get("carbs", ""))
    except (TypeError, ValueError):
        abort(400, "Goal values must be whole numbers.")

    if not 1000 <= calories <= 4000 or calories % 50 != 0:
        abort(400, "Calories must be between 1000 and 4000 in increments of 50.")

    if not 0 <= fats <= 150:
        abort(400, "Fats must be between 0 and 150 grams.")

    if not 0 <= protein <= 250:
        abort(400, "Protein must be between 0 and 250 grams.")

    if not 0 <= carbohydrates <= 350:
        abort(400, "Carbohydrates must be between 0 and 350 grams.")

    if protein == 0 and carbohydrates == 0 and fats == 0:
        abort(400, "At least one macro goal must be greater than zero.")

    return calories, protein, carbohydrates, fats


def calculate_goal_macro_percentages(protein, carbohydrates, fats):
    """Convert macro calories into whole percentages that total exactly 100."""
    macro_calories = (protein * 4, carbohydrates * 4, fats * 9)
    total_macro_calories = sum(macro_calories)

    percentages = [
        calories * 100 // total_macro_calories for calories in macro_calories
    ]
    remainders = [calories * 100 % total_macro_calories for calories in macro_calories]
    remaining_points = 100 - sum(percentages)

    for index, _ in sorted(
        enumerate(remainders), key=lambda remainder: (-remainder[1], remainder[0])
    )[:remaining_points]:
        percentages[index] += 1

    return tuple(percentages)


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
    goal_targets = {
        "calories": 2213,
        "protein": 110,
        "fats": 80,
        "carbs": 90,
    }

    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        goal = None
        if user_id is not None:
            goal = connection.execute(
                """
                SELECT calories, protein_grams, carbohydrate_grams, fat_grams
                FROM goals
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

    if goal is not None:
        goal_targets = {
            "calories": goal["calories"],
            "protein": int(goal["protein_grams"]),
            "fats": int(goal["fat_grams"]),
            "carbs": int(goal["carbohydrate_grams"]),
        }

    return render_template(
        "dashboard.html",
        selected_date=selected_date,
        date_options=date_options,
        goal_targets=goal_targets,
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
    selected_filter = request.args.get("filter", "az")
    if selected_filter not in {"az", "za", "favorites", "common"}:
        selected_filter = "az"
    sort_direction = "DESC" if selected_filter == "za" else "ASC"

    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        food_items = []
        if user_id is not None:
            food_items = connection.execute(
                f"""
                SELECT food_items.id, food_items.name, food_items.meal_type,
                       food_items.calories, food_items.protein_grams,
                       food_items.carbohydrate_grams, food_items.fat_grams,
                       CASE WHEN favorites.food_item_id IS NULL THEN 0 ELSE 1 END
                           AS is_favorite
                FROM food_items
                LEFT JOIN favorites
                    ON favorites.user_id = food_items.user_id
                    AND favorites.food_item_id = food_items.id
                WHERE food_items.user_id = ?
                ORDER BY food_items.name COLLATE NOCASE {sort_direction}
                """,
                (user_id,),
            ).fetchall()

    return render_template(
        "food_library.html",
        food_items=food_items,
        selected_filter=selected_filter,
    )


@app.route("/foods/<int:food_id>/favorite", methods=["POST"])
def toggle_favorite(food_id):
    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        if user_id is None:
            abort(409, "A food owner is required before a favorite can be saved.")

        food_item = connection.execute(
            "SELECT id FROM food_items WHERE id = ? AND user_id = ?",
            (food_id, user_id),
        ).fetchone()
        if food_item is None:
            abort(404)

        favorite = connection.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND food_item_id = ?",
            (user_id, food_id),
        ).fetchone()
        if favorite is None:
            connection.execute(
                "INSERT INTO favorites (user_id, food_item_id) VALUES (?, ?)",
                (user_id, food_id),
            )
            is_favorite = True
        else:
            connection.execute(
                "DELETE FROM favorites WHERE user_id = ? AND food_item_id = ?",
                (user_id, food_id),
            )
            is_favorite = False

    return jsonify(is_favorite=is_favorite)


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
    default_goal_values = {
        "calories": 2000,
        "fats": 70,
        "protein": 120,
        "carbs": 200,
    }

    if request.method == "POST":
        calories, protein, carbohydrates, fats = get_goal_form_values()
        protein_percent, carbohydrate_percent, fat_percent = (
            calculate_goal_macro_percentages(protein, carbohydrates, fats)
        )

        with get_database_connection() as connection:
            user_id = get_food_user_id(connection)
            if user_id is None:
                abort(409, "A goal owner is required before goals can be saved.")

            connection.execute(
                """
                INSERT INTO goals
                    (user_id, calories, protein_percent, carbohydrate_percent,
                     fat_percent, protein_grams, carbohydrate_grams, fat_grams)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    calories = excluded.calories,
                    protein_percent = excluded.protein_percent,
                    carbohydrate_percent = excluded.carbohydrate_percent,
                    fat_percent = excluded.fat_percent,
                    protein_grams = excluded.protein_grams,
                    carbohydrate_grams = excluded.carbohydrate_grams,
                    fat_grams = excluded.fat_grams,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    calories,
                    protein_percent,
                    carbohydrate_percent,
                    fat_percent,
                    protein,
                    carbohydrates,
                    fats,
                ),
            )

        return redirect(url_for("dashboard"))

    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        goal = None
        if user_id is not None:
            goal = connection.execute(
                """
                SELECT calories, protein_grams, carbohydrate_grams, fat_grams
                FROM goals
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

    if goal is not None:
        default_goal_values = {
            "calories": goal["calories"],
            "fats": int(goal["fat_grams"]),
            "protein": int(goal["protein_grams"]),
            "carbs": int(goal["carbohydrate_grams"]),
        }

    return render_template("set_goals.html", goal_values=default_goal_values)


@app.route("/daily_menu", methods=["GET", "POST"])
def daily_menu():
    selected_date = request.args.get("date", "12")
    selected_meal = request.args.get("meal", "Breakfast")

    return render_template(
        "daily_menu.html", selected_date=selected_date, selected_meal=selected_meal
    )


if __name__ == "__main__":
    app.run(debug=True)
