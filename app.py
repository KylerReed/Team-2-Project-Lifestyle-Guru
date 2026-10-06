from datetime import date, timedelta
import math
import os
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    session,
)

from calculations import (
    calculate_bmi,
    calculate_bmr,
    inches_to_cm,
    kilograms_to_pounds,
    pounds_to_kg,
)
from database import (
    ensure_profile_schema as ensure_profile_schema_in_database,
    get_database_connection as open_database_connection,
)

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

app.config["DATABASE"] = Path(
    os.environ.get("LIFESTYLE_GURU_DATABASE", Path(app.root_path) / "lifestyle_guru.db")
)

ACTIVITY_LEVELS = {
    "sedentary": "sedentary",
    "lightly active": "low",
    "low": "low",
    "moderately active": "average",
    "average": "average",
    "active": "high",
    "very active": "high",
    "high": "high",
}
PROFILE_GOALS = {"Lose weight", "Maintain weight", "Gain weight"}
MEAL_TYPES = ("Breakfast", "Lunch", "Dinner", "Snacks")
ONBOARDING_KEYS = (
    "onboarding_age",
    "onboarding_sex",
    "onboarding_weight_pounds",
    "onboarding_height_inches",
    "onboarding_activity_level",
)


def get_database_connection():
    """Return a connection to the team's existing SQLite database."""
    return open_database_connection(app.config["DATABASE"])


def ensure_profile_schema():
    """Apply the one small profile migration needed by the onboarding workflow."""
    ensure_profile_schema_in_database(app.config["DATABASE"])


def get_demo_user_id(connection):
    """Return the repository's existing development user, if present."""
    row = connection.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    return row["id"] if row is not None else None


def active_demo_user_id():
    """Return the session user only when it is still present in the database."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    with get_database_connection() as connection:
        user = connection.execute(
            "SELECT id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return user["id"] if user is not None else None


def onboarding_required():
    """Keep onboarding screens on the simple demo-user path."""
    return active_demo_user_id() is not None


def parse_age(value):
    try:
        age = int(value)
    except (TypeError, ValueError):
        raise ValueError("Age must be a whole number.")
    if not 10 <= age <= 100:
        raise ValueError("Age must be between 10 and 100.")
    return age


def parse_sex(value):
    sex = (value or "").strip().lower()
    if sex in {"female", "male"}:
        return sex
    if sex == "other":
        raise ValueError(
            "This prototype can calculate BMR for Female or Male selections only."
        )
    raise ValueError("Choose Female or Male.")


def parse_activity_level(value):
    normalized = (value or "").strip().lower()
    try:
        return ACTIVITY_LEVELS[normalized]
    except KeyError:
        raise ValueError("Choose a valid activity level.")


def parse_goal(value):
    goal = (value or "").strip()
    if goal not in PROFILE_GOALS:
        raise ValueError("Choose a valid goal.")
    return goal


def parse_weight_pounds(value, unit):
    try:
        weight = float(value)
    except (TypeError, ValueError):
        raise ValueError("Weight must be a number.")
    if not math.isfinite(weight) or weight <= 0:
        raise ValueError("Weight must be greater than zero.")

    unit = (unit or "").strip().lower()
    if unit in {"kg", "kilogram", "kilograms"}:
        return kilograms_to_pounds(weight)
    if unit in {"lb", "lbs", "pound", "pounds"}:
        return weight
    raise ValueError("Choose kilograms or pounds.")


def parse_height_inches(value, unit):
    try:
        height = float(value)
    except (TypeError, ValueError):
        raise ValueError("Height must be a number.")
    if not math.isfinite(height) or height <= 0:
        raise ValueError("Height must be greater than zero.")

    unit = (unit or "").strip().lower()
    if unit in {"cm", "centimeter", "centimeters"}:
        return height / 2.54
    if unit in {"in", "inch", "inches"}:
        return height
    raise ValueError("Choose centimeters or inches.")


def normalized_profile_measurements(weight_pounds, height_inches):
    """Use metric measurements internally for BMI and BMR."""
    return pounds_to_kg(weight_pounds), inches_to_cm(height_inches)


def profile_stats(profile):
    weight_kg, height_cm = normalized_profile_measurements(
        profile["weight_pounds"], profile["height_inches"]
    )
    return (
        calculate_bmi(weight_kg, height_cm),
        calculate_bmr(profile["sex"], profile["age"], weight_kg, height_cm),
    )


def parse_profile_name(value):
    """Allow a blank name while keeping a concise, display-safe saved name."""
    name = (value or "").strip()
    if len(name) > 80:
        raise ValueError("Profile name must be 80 characters or fewer.")
    return name or None


def save_profile(
    user_id, name, age, sex, weight_pounds, height_inches, activity_level, goal
):
    """Insert or update the active demo user's profile in the existing table."""
    with get_database_connection() as connection:
        connection.execute(
            """
            INSERT INTO profiles
                (user_id, name, height_inches, weight_pounds, age, sex, activity_level, goal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                height_inches = excluded.height_inches,
                weight_pounds = excluded.weight_pounds,
                age = excluded.age,
                sex = excluded.sex,
                activity_level = excluded.activity_level,
                goal = excluded.goal,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                name,
                height_inches,
                weight_pounds,
                age,
                sex,
                activity_level,
                goal,
            ),
        )


def onboarding_profile_values():
    try:
        return (
            parse_age(session.get("onboarding_age")),
            parse_sex(session.get("onboarding_sex")),
            float(session["onboarding_weight_pounds"]),
            float(session["onboarding_height_inches"]),
            parse_activity_level(session.get("onboarding_activity_level")),
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError("Complete each onboarding step before saving your profile.")


def parse_measurement(value, label):
    parts = (value or "").strip().split()
    if len(parts) != 2:
        raise ValueError(f"{label} must include a value and unit.")
    return parts


def profile_form_values(form):
    """Read the existing Profile screen's metric/inch select values."""
    weight_value, weight_unit = parse_measurement(form.get("weight"), "Weight")
    height_value, height_unit = parse_measurement(form.get("height"), "Height")
    return (
        parse_profile_name(form.get("profile_name")),
        parse_age(form.get("age")),
        parse_sex(form.get("gender")),
        parse_weight_pounds(weight_value, weight_unit),
        parse_height_inches(height_value, height_unit),
        parse_activity_level(form.get("activity_level")),
        parse_goal(form.get("goal")),
    )


def get_food_user_id(connection):
    """Get the food owner without adding authentication work in this pass.

    The current login screen does not set session['user_id'] yet.  During local
    development, the existing database has one approved user row, so that user
    can own food records.  Once authentication is integrated, it must set the
    session value instead of relying on this temporary single-user fallback.
    """
    session_user_id = active_demo_user_id()
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
    except (TypeError, ValueError) as error:
        raise ValueError("Food nutrition values must be numbers.") from error

    if (
        not name
        or meal_type not in MEAL_TYPES
        or not all(
            math.isfinite(value) and value >= 0
            for value in (calories, protein, carbohydrates, fats)
        )
    ):
        raise ValueError(
            "Food details must include a name, valid meal type, and non-negative values."
        )

    return name, meal_type, calories, protein, carbohydrates, fats


def get_goal_form_values():
    """Validate the approved calorie-plus-percent goal model."""
    try:
        calories = int(request.form.get("calories", ""))
        protein_percent = int(request.form.get("protein_percent", ""))
        carbohydrate_percent = int(request.form.get("carbohydrate_percent", ""))
        fat_percent = int(request.form.get("fat_percent", ""))
    except (TypeError, ValueError) as error:
        raise ValueError("Goal values must be whole numbers.") from error

    if not 1000 <= calories <= 4000 or calories % 50 != 0:
        raise ValueError("Calories must be between 1000 and 4000 in increments of 50.")

    percentages = (protein_percent, carbohydrate_percent, fat_percent)
    if any(percent < 0 or percent > 100 for percent in percentages):
        raise ValueError("Each macro percentage must be between 0 and 100.")
    if sum(percentages) != 100:
        raise ValueError("Protein, carbohydrate, and fat percentages must total 100.")

    return calories, protein_percent, carbohydrate_percent, fat_percent


def calculate_goal_macro_allocation(
    calories, protein_percent, carbohydrate_percent, fat_percent
):
    """Calculate gram targets from the approved daily calorie percentages."""
    protein_grams = (calories * protein_percent / 100) / 4
    carbohydrate_grams = (calories * carbohydrate_percent / 100) / 4
    fat_grams = (calories * fat_percent / 100) / 9
    return (
        round(protein_grams, 1),
        round(carbohydrate_grams, 1),
        round(fat_grams, 1),
    )


def get_daily_nutrition_totals(connection, user_id, meal_date):
    """Return actual totals from persisted meal logs for one user and ISO date."""
    totals = {"calories": 0.0, "protein": 0.0, "fats": 0.0, "carbs": 0.0}
    if user_id is None:
        return totals

    row = connection.execute(
        """
        SELECT COALESCE(SUM(calories), 0) AS calories,
               COALESCE(SUM(protein_grams), 0) AS protein,
               COALESCE(SUM(fat_grams), 0) AS fats,
               COALESCE(SUM(carbohydrate_grams), 0) AS carbs
        FROM meal_logs
        WHERE user_id = ? AND meal_date = ?
        """,
        (user_id, meal_date),
    ).fetchone()
    return {name: float(row[name]) for name in totals}


def format_nutrition_value(value):
    """Format display values without turning a genuine zero into ``0.0``."""
    value = float(value)
    return str(int(value)) if value.is_integer() else f"{value:.1f}"


def calculate_progress(consumed, target):
    """Return a safe, capped nutrition progress percentage."""
    target = float(target)
    if target <= 0:
        return 0
    return min(100, round((float(consumed) / target) * 100, 1))


def get_compact_date_options(requested_date):
    """Build the four-date selector from a valid ISO date or today's local date."""
    try:
        selected_date = (
            date.fromisoformat(requested_date) if requested_date else date.today()
        )
    except (TypeError, ValueError):
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


def get_saved_profile(connection, user_id):
    """Fetch the one saved prototype profile for a user, if it exists."""
    if user_id is None:
        return None
    return connection.execute(
        "SELECT * FROM profiles WHERE user_id = ?", (user_id,)
    ).fetchone()


def onboarding_has_state():
    """Return whether this session is in a new-profile onboarding sequence."""
    return any(key in session for key in ONBOARDING_KEYS)


def parse_meal_date(value):
    """Validate a date submitted for a persisted meal record."""
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as error:
        raise ValueError("Choose a valid meal date.") from error


def parse_meal_type(value):
    meal_type = (value or "").strip()
    if meal_type not in MEAL_TYPES:
        raise ValueError("Choose Breakfast, Lunch, Dinner, or Snacks.")
    return meal_type


def get_manual_meal_values(form):
    """Validate editable nutrition snapshots for a logged meal."""
    name = (form.get("food_name") or "").strip()
    if not name:
        raise ValueError("Meal name is required.")
    try:
        calories = float(form.get("calories", ""))
        protein = float(form.get("protein", ""))
        carbohydrates = float(form.get("carbs", ""))
        fats = float(form.get("fats", ""))
    except (TypeError, ValueError) as error:
        raise ValueError("Meal nutrition values must be numbers.") from error
    if not all(
        math.isfinite(value) and value >= 0
        for value in (calories, protein, carbohydrates, fats)
    ):
        raise ValueError("Meal nutrition values must be non-negative.")
    return (
        parse_meal_date(form.get("meal_date")),
        parse_meal_type(form.get("meal_type")),
        name,
        calories,
        protein,
        carbohydrates,
        fats,
    )


def insert_meal_log(
    connection,
    user_id,
    meal_date,
    meal_type,
    food_name,
    calories,
    protein,
    carbohydrates,
    fats,
    food_item_id=None,
):
    """Persist one nutrition snapshot and record actual Food Library usage."""
    connection.execute(
        """
        INSERT INTO meal_logs
            (user_id, food_item_id, meal_date, meal_type, food_name, calories,
             protein_grams, carbohydrate_grams, fat_grams)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            food_item_id,
            meal_date,
            meal_type,
            food_name,
            calories,
            protein,
            carbohydrates,
            fats,
        ),
    )
    if food_item_id is not None:
        connection.execute(
            "UPDATE food_items SET usage_count = usage_count + 1 WHERE id = ? AND user_id = ?",
            (food_item_id, user_id),
        )


ensure_profile_schema()


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with get_database_connection() as connection:
            user_id = get_demo_user_id(connection)
            saved_profile = get_saved_profile(connection, user_id)
        if user_id is None:
            abort(500, "The demo user is missing from lifestyle_guru.db.")

        session["user_id"] = user_id
        for key in ONBOARDING_KEYS:
            session.pop(key, None)

        return redirect(url_for("dashboard" if saved_profile is not None else "age"))

    return render_template("login.html")


@app.route("/age", methods=["GET", "POST"])
def age():
    if not onboarding_required():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            session["onboarding_age"] = parse_age(request.form.get("selected_age"))
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("age"))
        return redirect(url_for("weight"))

    return render_template("age.html")


@app.route("/weight", methods=["GET", "POST"])
def weight():
    if not onboarding_required():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            session["onboarding_weight_pounds"] = parse_weight_pounds(
                request.form.get("selected_weight"), request.form.get("weight_unit")
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("weight"))
        return redirect(url_for("gender"))

    return render_template("weight.html")


@app.route("/gender", methods=["GET", "POST"])
def gender():
    if not onboarding_required():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            session["onboarding_sex"] = parse_sex(request.form.get("gender"))
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("gender"))
        return redirect(url_for("height"))

    return render_template("gender.html")


@app.route("/height", methods=["GET", "POST"])
def height():
    if not onboarding_required():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            session["onboarding_height_inches"] = parse_height_inches(
                request.form.get("height_value"), request.form.get("height_unit")
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("height"))
        return redirect(url_for("activity"))

    return render_template("height.html")


@app.route("/activity", methods=["GET", "POST"])
def activity():
    if not onboarding_required():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            session["onboarding_activity_level"] = parse_activity_level(
                request.form.get("activity")
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("activity"))
        return redirect(url_for("goal"))

    return render_template("activity.html")


@app.route("/goal", methods=["GET", "POST"])
def goal():
    user_id = active_demo_user_id()
    if user_id is None:
        return redirect(url_for("login"))

    with get_database_connection() as connection:
        saved_profile = get_saved_profile(connection, user_id)

    if (
        request.method == "GET"
        and saved_profile is not None
        and not onboarding_has_state()
    ):
        return redirect(url_for("set_goals"))

    if request.method == "POST":
        try:
            selected_goal = parse_goal(request.form.get("goal"))
            age_value, sex, weight_pounds, height_inches, activity_level = (
                onboarding_profile_values()
            )
        except ValueError as error:
            flash(str(error), "error")

            return redirect(
                url_for("set_goals" if saved_profile is not None else "age")
            )

        save_profile(
            user_id,
            None,
            age_value,
            sex,
            weight_pounds,
            height_inches,
            activity_level,
            selected_goal,
        )
        for key in ONBOARDING_KEYS:
            session.pop(key, None)
        return redirect(url_for("dashboard"))

    return render_template("goal.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    selected_day, date_options = get_compact_date_options(request.args.get("date"))
    selected_date = selected_day.isoformat()
    goal_targets = {
        "calories": 0,
        "protein": 0,
        "fats": 0,
        "carbs": 0,
    }
    consumed = {"calories": 0.0, "protein": 0.0, "fats": 0.0, "carbs": 0.0}
    profile_name = None

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
            consumed = get_daily_nutrition_totals(connection, user_id, selected_date)
            profile_row = get_saved_profile(connection, user_id)
            profile_name = profile_row["name"] if profile_row is not None else None

    if goal is not None:
        goal_targets = {
            "calories": goal["calories"],
            "protein": goal["protein_grams"],
            "fats": goal["fat_grams"],
            "carbs": goal["carbohydrate_grams"],
        }

    consumed_display = {
        nutrient: format_nutrition_value(value) for nutrient, value in consumed.items()
    }
    progress = {
        "calories": calculate_progress(consumed["calories"], goal_targets["calories"]),
        "protein": calculate_progress(consumed["protein"], goal_targets["protein"]),
        "fats": calculate_progress(consumed["fats"], goal_targets["fats"]),
        "carbs": calculate_progress(consumed["carbs"], goal_targets["carbs"]),
    }

    return render_template(
        "dashboard.html",
        selected_date=selected_date,
        date_options=date_options,
        goal_targets=goal_targets,
        consumed=consumed,
        consumed_display=consumed_display,
        progress=progress,
        profile_name=profile_name or "Demo User",
    )
@app.route("/notifications")
def notifications():
    """Render the user notifications page."""
    return render_template("notifications.html")

@app.route("/log_meal", methods=["GET", "POST"])
def log_meal():
    selected_day, _ = get_compact_date_options(request.args.get("date"))
    selected_meal = request.args.get("meal", "Breakfast")
    if selected_meal not in MEAL_TYPES:
        selected_meal = "Breakfast"
    return render_template(
        "log_meal.html",
        selected_date=selected_day.isoformat(),
        selected_meal=selected_meal,
    )


@app.route("/foods/<int:food_id>/log", methods=["GET", "POST"])
def log_food(food_id):
    """Create an actual meal record from one saved Food Library item."""
    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        if user_id is None:
            return redirect(url_for("login"))
        food_item = connection.execute(
            """
            SELECT id, name, meal_type, calories, protein_grams,
                   carbohydrate_grams, fat_grams
            FROM food_items WHERE id = ? AND user_id = ?
            """,
            (food_id, user_id),
        ).fetchone()
        if food_item is None:
            flash("That Food Library item is unavailable.", "error")
            return redirect(url_for("food_library"))

        if request.method == "POST":
            try:
                meal_date = parse_meal_date(request.form.get("meal_date"))
                meal_type = parse_meal_type(request.form.get("meal_type"))
            except ValueError as error:
                flash(str(error), "error")
                return redirect(url_for("log_food", food_id=food_id))
            insert_meal_log(
                connection,
                user_id,
                meal_date,
                meal_type,
                food_item["name"],
                food_item["calories"],
                food_item["protein_grams"],
                food_item["carbohydrate_grams"],
                food_item["fat_grams"],
                food_item["id"],
            )

    if request.method == "POST":
        flash("Meal logged.", "success")
        return redirect(url_for("daily_menu", date=meal_date, meal=meal_type))

    selected_day, _ = get_compact_date_options(request.args.get("date"))
    selected_meal = request.args.get("meal", food_item["meal_type"])
    if selected_meal not in MEAL_TYPES:
        selected_meal = food_item["meal_type"]
    return render_template(
        "log_food.html",
        food=food_item,
        selected_date=selected_day.isoformat(),
        selected_meal=selected_meal,
    )


@app.route("/meals/<int:meal_id>/edit", methods=["GET", "POST"])
def edit_meal(meal_id):
    """Edit one owned, persisted meal snapshot without changing its history ID."""
    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        if user_id is None:
            return redirect(url_for("login"))
        meal = connection.execute(
            """
            SELECT id, food_item_id, meal_date, meal_type, food_name, calories,
                   protein_grams, carbohydrate_grams, fat_grams
            FROM meal_logs WHERE id = ? AND user_id = ?
            """,
            (meal_id, user_id),
        ).fetchone()
        if meal is None:
            flash("That logged meal is unavailable.", "error")
            return redirect(url_for("daily_menu"))

        if request.method == "POST":
            try:
                (
                    meal_date,
                    meal_type,
                    food_name,
                    calories,
                    protein,
                    carbohydrates,
                    fats,
                ) = get_manual_meal_values(request.form)
            except ValueError as error:
                flash(str(error), "error")
                return redirect(url_for("edit_meal", meal_id=meal_id))
            connection.execute(
                """
                UPDATE meal_logs
                SET meal_date = ?, meal_type = ?, food_name = ?, calories = ?,
                    protein_grams = ?, carbohydrate_grams = ?, fat_grams = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    meal_date,
                    meal_type,
                    food_name,
                    calories,
                    protein,
                    carbohydrates,
                    fats,
                    meal_id,
                    user_id,
                ),
            )
            flash("Meal updated.", "success")
            return redirect(url_for("daily_menu", date=meal_date, meal=meal_type))

    return render_template("edit_meal.html", meal=meal, meal_types=MEAL_TYPES)


@app.post("/meals/<int:meal_id>/delete")
def delete_meal(meal_id):
    """Delete a meal record and reverse the Food Library usage count safely."""
    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        if user_id is None:
            return redirect(url_for("login"))
        meal = connection.execute(
            "SELECT food_item_id FROM meal_logs WHERE id = ? AND user_id = ?",
            (meal_id, user_id),
        ).fetchone()
        if meal is None:
            flash("That logged meal is unavailable.", "error")
            return redirect(url_for("daily_menu"))
        connection.execute(
            "DELETE FROM meal_logs WHERE id = ? AND user_id = ?", (meal_id, user_id)
        )
        if meal["food_item_id"] is not None:
            connection.execute(
                """
                UPDATE food_items
                SET usage_count = CASE WHEN usage_count > 0 THEN usage_count - 1 ELSE 0 END
                WHERE id = ? AND user_id = ?
                """,
                (meal["food_item_id"], user_id),
            )
    flash("Meal deleted.", "success")
    selected_day, _ = get_compact_date_options(request.form.get("meal_date"))
    meal_type = request.form.get("meal_type", "Breakfast")
    if meal_type not in MEAL_TYPES:
        meal_type = "Breakfast"
    return redirect(
        url_for("daily_menu", date=selected_day.isoformat(), meal=meal_type)
    )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = active_demo_user_id()
    if user_id is None:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            
            weight_val_str, weight_unit = parse_measurement(request.form.get("weight"), "Weight")
            height_val_str, height_unit = parse_measurement(request.form.get("height"), "Height")
            
            
            session["weight_unit"] = "lbs" if weight_unit in {"lb", "lbs", "pound", "pounds"} else "kg"
            session["height_unit"] = "in" if height_unit in {"in", "inch", "inches"} else "cm"

            values = profile_form_values(request.form)
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("profile"))
        
        save_profile(user_id, *values)
        return redirect(url_for("profile"))

    with get_database_connection() as connection:
        profile_row = connection.execute(
            """
            SELECT profiles.*, users.email
            FROM profiles JOIN users ON users.id = profiles.user_id
            WHERE profiles.user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if profile_row is None:
        return render_template(
            "profile.html",
            user_email="",
            profile_name="",
            user_gender="",
            user_age=None,
            user_weight_value=None,
            user_weight_unit="kg",
            user_height_value=None,
            user_height_unit="cm",
            user_activity="",
            user_goal="",
            bmi=None,
            bmr=None,
        )

    bmi, bmr = profile_stats(profile_row)

    
    weight_unit = session.get("weight_unit", "kg")
    height_unit = session.get("height_unit", "cm")

    
    if weight_unit == "lbs":
        display_weight = round(profile_row["weight_pounds"])
    else:
        display_weight = round(pounds_to_kg(profile_row["weight_pounds"]))

    if height_unit == "in":
        display_height = round(profile_row["height_inches"])
    else:
        display_height = round(inches_to_cm(profile_row["height_inches"]))

    return render_template(
        "profile.html",
        user_email=profile_row["email"],
        profile_name=profile_row["name"] or "",
        user_gender=profile_row["sex"],
        user_age=profile_row["age"],
        user_weight_value=display_weight,
        user_weight_unit=weight_unit,
        user_height_value=display_height,
        user_height_unit=height_unit,
        user_activity=profile_row["activity_level"],
        user_goal=profile_row["goal"] or "",
        bmi=bmi,
        bmr=bmr,
    )


@app.post("/profile/delete")
def delete_profile():
    """Delete only the active demo user's saved profile, not their other data."""
    user_id = active_demo_user_id()
    if user_id is None:
        return redirect(url_for("login"))

    with get_database_connection() as connection:
        connection.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    return redirect(url_for("profile"))


@app.post("/logout")
def logout():
    """End the simple demo session and discard any incomplete onboarding data."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/add_food", methods=["GET", "POST"])
def add_food():
    if request.method == "POST":
        try:
            name, meal_type, calories, protein, carbohydrates, fats = (
                get_food_form_values()
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("add_food"))

        with get_database_connection() as connection:
            user_id = get_food_user_id(connection)
            if user_id is None:
                return redirect(url_for("login"))

            cursor = connection.execute(
                """
                INSERT INTO food_items
                    (user_id, name, meal_type, calories, protein_grams,
                     carbohydrate_grams, fat_grams)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, meal_type, calories, protein, carbohydrates, fats),
            )

        if request.form.get("return_to") == "log_meal":
            selected_date, _ = get_compact_date_options(request.form.get("meal_date"))
            return redirect(
                url_for(
                    "log_food",
                    food_id=cursor.lastrowid,
                    date=selected_date.isoformat(),
                    meal=meal_type,
                )
            )
        return redirect(url_for("food_library", filter="az"))
    selected_date, date_options = get_compact_date_options(request.args.get("date"))
    return render_template(
        "add_food.html",
        selected_date=selected_date.isoformat(),
        date_options=date_options,
        return_to=("log_meal" if request.args.get("return_to") == "log_meal" else ""),
    )


@app.route("/food_library", methods=["GET", "POST"])
def food_library():
    selected_filter = request.args.get("filter", "az")
    if selected_filter not in {"az", "za", "favorites", "common"}:
        selected_filter = "az"
    where_suffix = ""
    order_by = "food_items.name COLLATE NOCASE ASC"
    if selected_filter == "za":
        order_by = "food_items.name COLLATE NOCASE DESC"
    elif selected_filter == "favorites":
        where_suffix = " AND favorites.food_item_id IS NOT NULL"
    elif selected_filter == "common":
        where_suffix = " AND food_items.usage_count > 0"
        order_by = "food_items.usage_count DESC, food_items.name COLLATE NOCASE ASC"
    selected_day, _ = get_compact_date_options(request.args.get("date"))
    selected_date = selected_day.isoformat()
    selected_meal = request.args.get("meal", "Breakfast")
    if selected_meal not in MEAL_TYPES:
        selected_meal = "Breakfast"

    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        food_items = []
        if user_id is not None:
            food_items = connection.execute(
                f"""
                SELECT food_items.id, food_items.name, food_items.meal_type,
                       food_items.calories, food_items.protein_grams,
                       food_items.carbohydrate_grams, food_items.fat_grams,
                       food_items.usage_count,
                       CASE WHEN favorites.food_item_id IS NULL THEN 0 ELSE 1 END
                           AS is_favorite
                FROM food_items
                LEFT JOIN favorites
                    ON favorites.user_id = food_items.user_id
                    AND favorites.food_item_id = food_items.id
                WHERE food_items.user_id = ? {where_suffix}
                ORDER BY {order_by}
                """,
                (user_id,),
            ).fetchall()

    return render_template(
        "food_library.html",
        food_items=food_items,
        selected_filter=selected_filter,
        selected_date=selected_date,
        selected_meal=selected_meal,
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
            try:
                name, meal_type, calories, protein, carbohydrates, fats = (
                    get_food_form_values()
                )
            except ValueError as error:
                flash(str(error), "error")
                return redirect(url_for("edit_food", food_id=food_id))
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


@app.post("/foods/<int:food_id>/delete")
def delete_food(food_id):
    """Delete one owned Food Library item after the template confirmation."""
    with get_database_connection() as connection:
        user_id = get_food_user_id(connection)
        if user_id is None:
            return redirect(url_for("login"))
        connection.execute(
            "DELETE FROM food_items WHERE id = ? AND user_id = ?", (food_id, user_id)
        )
    flash("Food item deleted.", "success")
    return redirect(url_for("food_library", filter=request.form.get("filter", "az")))


@app.route("/set_goals", methods=["GET", "POST"])
def set_goals():
    default_goal_values = {
        "calories": 2000,
        "protein_percent": 25,
        "carbohydrate_percent": 50,
        "fat_percent": 25,
    }

    if request.method == "POST":
        try:
            calories, protein_percent, carbohydrate_percent, fat_percent = (
                get_goal_form_values()
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("set_goals"))
        protein, carbohydrates, fats = calculate_goal_macro_allocation(
            calories, protein_percent, carbohydrate_percent, fat_percent
        )

        with get_database_connection() as connection:
            user_id = get_food_user_id(connection)
            if user_id is None:
                return redirect(url_for("login"))

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
                       , protein_percent, carbohydrate_percent, fat_percent
                FROM goals
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

    if goal is not None:
        default_goal_values = {
            "calories": goal["calories"],
            "protein_percent": goal["protein_percent"],
            "carbohydrate_percent": goal["carbohydrate_percent"],
            "fat_percent": goal["fat_percent"],
        }
    protein, carbohydrates, fats = calculate_goal_macro_allocation(
        default_goal_values["calories"],
        default_goal_values["protein_percent"],
        default_goal_values["carbohydrate_percent"],
        default_goal_values["fat_percent"],
    )
    return render_template(
        "set_goals.html",
        goal_values=default_goal_values,
        macro_allocation={
            "protein": protein,
            "carbohydrates": carbohydrates,
            "fats": fats,
        },
    )


@app.get("/daily_menu")
def daily_menu():
    selected_day, date_options = get_compact_date_options(request.args.get("date"))
    selected_date = selected_day.isoformat()
    selected_meal = request.args.get("meal", "Breakfast")
    if selected_meal not in MEAL_TYPES:
        selected_meal = "Breakfast"

    logged_meals = []
    user_id = active_demo_user_id()

    if user_id is not None:
        with get_database_connection() as connection:
            logged_meals = connection.execute(
                """
                SELECT id, food_name, calories, protein_grams, fat_grams,
                       carbohydrate_grams
                FROM meal_logs
                WHERE user_id = ? AND meal_date = ? AND meal_type = ?
                ORDER BY created_at, id
                """,
                (user_id, selected_date, selected_meal),
            ).fetchall()

    return render_template(
        "daily_menu.html",
        selected_date=selected_date,
        selected_meal=selected_meal,
        date_options=date_options,
        logged_meals=logged_meals,
    )


if __name__ == "__main__":
    app.run(debug=True)
