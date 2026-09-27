# app.py 

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from calculations import (
    calculate_bmi,
    calculate_bmr,
    calculate_meal_calories,
    calculate_macros
)


app = Flask(__name__)

# Needed for Flask sessions and flash messages
app.secret_key = "change-this-secret-key"



# HELPER FUNCTIONS


def get_metric_measurements():
    """
    Returns the user's weight and height in:
        weight = kilograms
        height = centimeters

    This allows BMI and BMR to use one consistent calculation.
    """

    unit_system = session.get("unit_system", "metric")

    
    # US measurements
    

    if unit_system == "us":

        weight_lbs = session.get("weight_lbs")
        feet = session.get("height_feet")
        inches = session.get("height_inches")

        if (
            weight_lbs is None
            or feet is None
            or inches is None
        ):
            return None, None

        weight_kg = weight_lbs * 0.45359237

        height_cm = (
            ((feet * 12) + inches)
            * 2.54
        )

        return weight_kg, height_cm

    
    # Metric measurements
   

    return (
        session.get("weight_kg"),
        session.get("height_cm")
    )


def calculate_profile_results():

    weight_kg, height_cm = (
        get_metric_measurements()
    )

    age = session.get("age")
    gender = session.get("gender")

    bmi = None
    bmr = None

    
    # BMI
    

    if weight_kg and height_cm:

        bmi = calculate_bmi(
            weight_kg,
            height_cm
        )

    
    # BMR
    

    if (
        weight_kg
        and height_cm
        and age
        and gender
    ):

        try:

            bmr = calculate_bmr(
                gender,
                age,
                weight_kg,
                height_cm
            )

        except ValueError:

            bmr = None

    return bmi, bmr



# HOME


@app.route("/")
def home():

    return redirect(
        url_for("profile")
    )



# FIX #1 — /gender


@app.route(
    "/gender",
    methods=["GET", "POST"]
)
def gender():

    if request.method == "POST":

        selected_gender = (
            request.form
            .get("gender", "")
            .strip()
            .lower()
        )

        # Validate input
        if selected_gender not in (
            "male",
            "female"
        ):

            flash(
                "Please select a valid gender.",
                "error"
            )

            return redirect(
                url_for("gender")
            )

        # Save gender
        session["gender"] = (
            selected_gender
        )

        flash(
            "Gender saved. Next, enter your age.",
            "success"
        )

        # ====================================================
        # FIX:
        #
        # Previously /gender was skipping part of the
        # profile process.
        #
        # Now:
        #
        # /gender
        #     ↓
        # /age
        #     ↓
        # /weight
        #     ↓
        # /height
        #     ↓
        # /profile
        # ====================================================

        return redirect(
            url_for("age")
        )

    return render_template(
        "gender.html",
        gender=session.get(
            "gender",
            ""
        )
    )



# FIX #2 — /age


@app.route(
    "/age",
    methods=["GET", "POST"]
)
def age():

    if request.method == "POST":

        raw_age = (
            request.form
            .get("age", "")
            .strip()
        )

        try:

            age_value = int(
                raw_age
            )

            if (
                age_value < 1
                or age_value >= 120
            ):
                raise ValueError

        except ValueError:

            flash(
                "Please enter an age between 1 and 119.",
                "error"
            )

            return redirect(
                url_for("age")
            )

        # Save age
        session["age"] = age_value

        flash(
            "Age saved. Next, enter your weight.",
            "success"
        )

        # ====================================================
        # FIX:
        #
        # BEFORE:
        #
        # /age → skipped /weight
        #
        # AFTER:
        #
        # /age → /weight
        #
        # The weight will no longer appear as None.
        # ====================================================

        return redirect(
            url_for("weight")
        )

    return render_template(
        "age.html",
        age=session.get(
            "age",
            ""
        )
    )



# /weight


@app.route(
    "/weight",
    methods=["GET", "POST"]
)
def weight():

    if request.method == "POST":

        unit_system = (
            request.form
            .get(
                "unit_system",
                "metric"
            )
            .strip()
            .lower()
        )

        try:

            # --------------------------------------
            # US
            # --------------------------------------

            if unit_system == "us":

                weight_lbs = float(
                    request.form
                    .get("weight_lbs", "")
                )

                if weight_lbs <= 0:
                    raise ValueError

                session["unit_system"] = "us"
                session["weight_lbs"] = (
                    weight_lbs
                )

            # --------------------------------------
            # Metric
            # --------------------------------------

            elif unit_system == "metric":

                weight_kg = float(
                    request.form
                    .get("weight_kg", "")
                )

                if weight_kg <= 0:
                    raise ValueError

                session["unit_system"] = (
                    "metric"
                )

                session["weight_kg"] = (
                    weight_kg
                )

            else:

                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid weight.",
                "error"
            )

            return redirect(
                url_for("weight")
            )

        flash(
            "Weight saved. Next, enter your height.",
            "success"
        )

        return redirect(
            url_for("height")
        )

    return render_template(
        "weight.html",

        unit_system=session.get(
            "unit_system",
            "metric"
        ),

        weight_kg=session.get(
            "weight_kg",
            ""
        ),

        weight_lbs=session.get(
            "weight_lbs",
            ""
        )
    )



# /height


@app.route(
    "/height",
    methods=["GET", "POST"]
)
def height():

    if request.method == "POST":

        unit_system = session.get(
            "unit_system",
            "metric"
        )

        try:

            # --------------------------------------
            # US: feet + inches
            # --------------------------------------

            if unit_system == "us":

                feet = int(
                    request.form
                    .get("height_feet", "")
                )

                inches = float(
                    request.form
                    .get("height_inches", "")
                )

                if (
                    feet < 0
                    or inches < 0
                    or inches >= 12
                    or (
                        feet == 0
                        and inches == 0
                    )
                ):

                    raise ValueError

                session["height_feet"] = feet
                session["height_inches"] = inches

            # --------------------------------------
            # Metric: centimeters
            # --------------------------------------

            else:

                height_cm = float(
                    request.form
                    .get("height_cm", "")
                )

                if height_cm <= 0:
                    raise ValueError

                session["height_cm"] = (
                    height_cm
                )

        except ValueError:

            flash(
                "Please enter a valid height.",
                "error"
            )

            return redirect(
                url_for("height")
            )

        flash(
            "Height saved. Your profile is ready.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    return render_template(
        "height.html",

        unit_system=session.get(
            "unit_system",
            "metric"
        ),

        height_cm=session.get(
            "height_cm",
            ""
        ),

        height_feet=session.get(
            "height_feet",
            ""
        ),

        height_inches=session.get(
            "height_inches",
            ""
        )
    )



# FIX #3 — /profile


@app.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():

    if request.method == "POST":

        name = (
            request.form
            .get("name", "")
            .strip()
        )

        gender_value = (
            request.form
            .get("gender", "")
            .strip()
            .lower()
        )

        # --------------------------------------
        # Validate name
        # --------------------------------------

        if not name:

            flash(
                "Please enter your name.",
                "error"
            )

            return redirect(
                url_for("profile")
            )

        # --------------------------------------
        # Validate gender
        # --------------------------------------

        if gender_value not in (
            "male",
            "female"
        ):

            flash(
                "Please select a valid gender.",
                "error"
            )

            return redirect(
                url_for("profile")
            )

        try:

            age_value = int(
                request.form
                .get("age", "")
            )

            if (
                age_value < 1
                or age_value >= 120
            ):
                raise ValueError

            unit_system = session.get(
                "unit_system",
                "metric"
            )

            # ----------------------------------
            # US profile
            # ----------------------------------

            if unit_system == "us":

                weight_lbs = float(
                    request.form
                    .get("weight_lbs", "")
                )

                feet = int(
                    request.form
                    .get("height_feet", "")
                )

                inches = float(
                    request.form
                    .get("height_inches", "")
                )

                if (
                    weight_lbs <= 0
                    or feet < 0
                    or inches < 0
                    or inches >= 12
                ):

                    raise ValueError

                session["weight_lbs"] = (
                    weight_lbs
                )

                session["height_feet"] = feet

                session["height_inches"] = (
                    inches
                )

            # ----------------------------------
            # Metric profile
            # ----------------------------------

            else:

                weight_kg = float(
                    request.form
                    .get("weight_kg", "")
                )

                height_cm = float(
                    request.form
                    .get("height_cm", "")
                )

                if (
                    weight_kg <= 0
                    or height_cm <= 0
                ):

                    raise ValueError

                session["weight_kg"] = (
                    weight_kg
                )

                session["height_cm"] = (
                    height_cm
                )

        except (
            TypeError,
            ValueError
        ):

            flash(
                "Please enter valid profile information.",
                "error"
            )

            return redirect(
                url_for("profile")
            )

        # ====================================================
        # FIX:
        #
        # Actually save the changed profile values.
        # ====================================================

        session["name"] = name

        session["gender"] = (
            gender_value
        )

        session["age"] = (
            age_value
        )

        # ====================================================
        # FIX:
        #
        # Redirect back to the profile so the template reads
        # the newly saved values instead of the old values.
        # ====================================================

        flash(
            "Profile changes saved successfully!",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    # --------------------------------------
    # Calculate current BMI and BMR
    # --------------------------------------

    bmi, bmr = (
        calculate_profile_results()
    )

    return render_template(
        "profile.html",

        name=session.get(
            "name",
            ""
        ),

        gender=session.get(
            "gender",
            ""
        ),

        age=session.get(
            "age",
            ""
        ),

        unit_system=session.get(
            "unit_system",
            "metric"
        ),

        weight_kg=session.get(
            "weight_kg",
            ""
        ),

        height_cm=session.get(
            "height_cm",
            ""
        ),

        weight_lbs=session.get(
            "weight_lbs",
            ""
        ),

        height_feet=session.get(
            "height_feet",
            ""
        ),

        height_inches=session.get(
            "height_inches",
            ""
        ),

        bmi=bmi,

        bmr=bmr
    )



# FIX #4 — /add_food


@app.route(
    "/add_food",
    methods=["GET", "POST"]
)
def add_food():

    if request.method == "POST":

        name = (
            request.form
            .get("name", "")
            .strip()
        )

        meal_type = (
            request.form
            .get(
                "meal_type",
                "Snack"
            )
        )

        try:

            protein = float(
                request.form
                .get("protein", "0")
            )

            fat = float(
                request.form
                .get("fat", "0")
            )

            carbs = float(
                request.form
                .get("carbs", "0")
            )

            if (
                protein < 0
                or fat < 0
                or carbs < 0
            ):

                raise ValueError

        except ValueError:

            flash(
                "Protein, fats, and carbs must be valid non-negative numbers.",
                "error"
            )

            return redirect(
                url_for("add_food")
            )

        # --------------------------------------
        # Calculate calories
        # --------------------------------------

        calories = (
            calculate_meal_calories(
                protein,
                fat,
                carbs
            )
        )

        # --------------------------------------
        # Save meal temporarily
        # --------------------------------------

        meals = session.get(
            "meals",
            []
        )

        meals.append({

            "name": (
                name
                or "Unnamed Meal"
            ),

            "meal_type": meal_type,

            "protein": protein,

            "fat": fat,

            "carbs": carbs,

            "calories": calories

        })

        session["meals"] = meals

        flash(
            f"{name or 'Meal'} was added successfully!",
            "success"
        )

        return redirect(
            url_for("add_food")
        )

    return render_template(
        "add_food.html",

        meals=session.get(
            "meals",
            []
        ),

        protein=session.get(
            "food_protein",
            0
        ),

        fat=session.get(
            "food_fat",
            0
        ),

        carbs=session.get(
            "food_carbs",
            0
        )
    )



# /add_food/adjust
#
# THIS IS THE SPECIFIC FIX FOR THE 0.1 ISSUE.


@app.post("/add_food/adjust")
def adjust_food():

    macro = request.form.get(
        "macro",
        ""
    )

    direction = request.form.get(
        "direction",
        ""
    )

    if macro not in (
        "protein",
        "fat",
        "carbs"
    ):

        flash(
            "Invalid nutrition field.",
            "error"
        )

        return redirect(
            url_for("add_food")
        )

    if direction not in (
        "increase",
        "decrease"
    ):

        flash(
            "Invalid adjustment.",
            "error"
        )

        return redirect(
            url_for("add_food")
        )

    session_key = (
        f"food_{macro}"
    )

    current = float(
        session.get(
            session_key,
            0
        )
    )

    # ========================================================
    # FIX:
    #
    # BEFORE:
    # current += 0.1
    #
    # NOW:
    # current += 1
    #
    # ========================================================

    if direction == "increase":

        current += 1

    else:

        current = max(
            0,
            current - 1
        )

    session[session_key] = (
        current
    )

    return redirect(
        url_for("add_food")
    )



# FIX #5 — /set_goals


@app.route(
    "/set_goals",
    methods=["GET", "POST"]
)
def set_goals():

    if request.method == "POST":

        try:

            daily_calories = float(
                request.form
                .get(
                    "daily_calories",
                    ""
                )
            )

            protein_percent = float(
                request.form
                .get(
                    "protein_percent",
                    ""
                )
            )

            fat_percent = float(
                request.form
                .get(
                    "fat_percent",
                    ""
                )
            )

            carb_percent = float(
                request.form
                .get(
                    "carb_percent",
                    ""
                )
            )

            if daily_calories <= 0:
                raise ValueError

            percentages = (
                protein_percent,
                fat_percent,
                carb_percent
            )

            if any(
                value < 0
                or value > 100
                for value in percentages
            ):

                raise ValueError

            # --------------------------------------
            # Macro percentages must equal 100
            # --------------------------------------

            if round(
                sum(percentages),
                2
            ) != 100:

                flash(
                    "Protein, fats, and carbs must add up to 100%.",
                    "error"
                )

                return redirect(
                    url_for("set_goals")
                )

        except ValueError:

            flash(
                "Please enter valid goal values.",
                "error"
            )

            return redirect(
                url_for("set_goals")
            )

        # --------------------------------------
        # Calculate grams from percentages
        # --------------------------------------

        macros = calculate_macros(

            daily_calories,

            protein_percent,

            fat_percent,

            carb_percent

        )

        # ====================================================
        # FIX:
        #
        # Save the values instead of only printing them to
        # the terminal.
        # ====================================================

        session["goals"] = {

            "daily_calories":
                daily_calories,

            "protein_percent":
                protein_percent,

            "fat_percent":
                fat_percent,

            "carb_percent":
                carb_percent,

            "protein_grams":
                macros["protein_grams"],

            "fat_grams":
                macros["fat_grams"],

            "carb_grams":
                macros["carb_grams"]

        }

        # ====================================================
        # FIX:
        #
        # Reload the page after saving so the UI shows the
        # updated values.
        # ====================================================

        flash(
            "Goals saved successfully!",
            "success"
        )

        return redirect(
            url_for("set_goals")
        )

    # --------------------------------------
    # Load saved goals
    # --------------------------------------

    goals = session.get(

        "goals",

        {
            "daily_calories": 2000,

            "protein_percent": 50,

            "fat_percent": 30,

            "carb_percent": 20,

            "protein_grams": 250,

            "fat_grams": 66.7,

            "carb_grams": 100
        }
    )

    return render_template(

        "set_goals.html",

        goals=goals

    )



# START FLASK


if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )

