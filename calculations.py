"""Reusable unit-conversion and profile-calculation helpers."""

KILOGRAMS_PER_POUND = 0.45359237
CENTIMETERS_PER_INCH = 2.54

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "low": 1.375,
    "lightly active": 1.375,
    "average": 1.55,
    "moderately active": 1.55,
    "high": 1.725,
    "active": 1.725,
    "very active": 1.725,
}

CALORIE_GOAL_ADJUSTMENTS = {
    "Lose weight": -500,
    "Maintain weight": 0,
    "Gain weight": 300,
}


def pounds_to_kg(pounds):
    """Convert pounds to kilograms without rounding the stored calculation value."""
    return float(pounds) * KILOGRAMS_PER_POUND


def kilograms_to_pounds(kilograms):
    """Convert kilograms to pounds for the existing profile schema."""
    return float(kilograms) / KILOGRAMS_PER_POUND


def feet_inches_to_cm(feet, inches):
    """Convert a feet-and-inches measurement to centimeters."""
    return ((float(feet) * 12) + float(inches)) * CENTIMETERS_PER_INCH


def inches_to_cm(inches):
    """Convert a total-inch measurement to centimeters."""
    total_inches = float(inches)
    return feet_inches_to_cm(int(total_inches // 12), total_inches % 12)


def calculate_bmi(weight_kg, height_cm):
    """Return body mass index rounded to one decimal place."""
    weight_kg = float(weight_kg)
    height_cm = float(height_cm)
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero.")
    if height_cm <= 0:
        raise ValueError("Height must be greater than zero.")
    return round(weight_kg / ((height_cm / 100) ** 2), 1)


def calculate_bmr(sex, age, weight_kg, height_cm):
    """Return Mifflin-St Jeor BMR for the supported female/male equations."""
    age = int(age)
    weight_kg = float(weight_kg)
    height_cm = float(height_cm)
    if age <= 0:
        raise ValueError("Age must be greater than zero.")
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero.")
    if height_cm <= 0:
        raise ValueError("Height must be greater than zero.")

    sex = str(sex).lower()
    if sex == "male":
        adjustment = 5
    elif sex == "female":
        adjustment = -161
    else:
        raise ValueError("BMR is available for female or male profiles only.")

    return round((10 * weight_kg) + (6.25 * height_cm) - (5 * age) + adjustment)


def calculate_tdee(bmr, activity_level):
    """Return estimated daily energy use from BMR and an activity factor."""
    bmr = float(bmr)
    if bmr <= 0:
        raise ValueError("BMR must be greater than zero.")

    normalized_activity = str(activity_level or "").strip().lower()
    try:
        activity_factor = ACTIVITY_FACTORS[normalized_activity]
    except KeyError as error:
        raise ValueError("Choose a valid activity level.") from error

    return round(bmr * activity_factor)


def calculate_recommended_calorie_target(tdee, goal):
    """Return a conservative recommendation; it never changes a saved goal."""
    tdee = float(tdee)
    if tdee <= 0:
        raise ValueError("TDEE must be greater than zero.")

    try:
        adjustment = CALORIE_GOAL_ADJUSTMENTS[str(goal).strip()]
    except KeyError as error:
        raise ValueError("Choose a valid goal.") from error

    return round(tdee + adjustment)
