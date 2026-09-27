# calculations.py



# UNIT CONVERSIONS


def pounds_to_kg(pounds):

    return pounds * 0.45359237


def feet_inches_to_cm(
    feet,
    inches
):

    return (
        ((feet * 12) + inches)
        * 2.54
    )



# BMI


def calculate_bmi(
    weight_kg,
    height_cm
):

    if weight_kg <= 0:

        raise ValueError(
            "Weight must be greater than zero."
        )

    if height_cm <= 0:

        raise ValueError(
            "Height must be greater than zero."
        )

    height_m = (
        height_cm / 100
    )

    bmi = (
        weight_kg
        / (height_m ** 2)
    )

    return round(
        bmi,
        1
    )


def calculate_bmi_us(
    weight_lbs,
    height_feet,
    height_inches
):

    weight_kg = (
        pounds_to_kg(
            weight_lbs
        )
    )

    height_cm = (
        feet_inches_to_cm(
            height_feet,
            height_inches
        )
    )

    return calculate_bmi(
        weight_kg,
        height_cm
    )



# BMR


def calculate_bmr(
    sex,
    age,
    weight_kg,
    height_cm
):

    if age <= 0:
        raise ValueError(
            "Age must be greater than zero."
        )

    if weight_kg <= 0:
        raise ValueError(
            "Weight must be greater than zero."
        )

    if height_cm <= 0:
        raise ValueError(
            "Height must be greater than zero."
        )

    sex = sex.lower()

    
    if sex == "male":

        bmr = (
            (10 * weight_kg)
            + (6.25 * height_cm)
            - (5 * age)
            + 5
        )

    elif sex == "female":

        bmr = (
            (10 * weight_kg)
            + (6.25 * height_cm)
            - (5 * age)
            - 161
        )

    else:

        raise ValueError(
            "Sex must be male or female."
        )

    return round(bmr)


def calculate_bmr_us(
    sex,
    age,
    weight_lbs,
    height_feet,
    height_inches
):

    return calculate_bmr(

        sex,

        age,

        pounds_to_kg(
            weight_lbs
        ),

        feet_inches_to_cm(
            height_feet,
            height_inches
        )
    )


# MEAL CALORIES


def calculate_meal_calories(
    protein_grams,
    fat_grams,
    carb_grams
):

    protein_calories = (
        protein_grams * 4
    )

    fat_calories = (
        fat_grams * 9
    )

    carb_calories = (
        carb_grams * 4
    )

    return round(

        protein_calories
        + fat_calories
        + carb_calories

    )


# MACRO GOALS


def calculate_macros(
    total_calories,
    protein_percent,
    fat_percent,
    carb_percent
):

    if round(
        protein_percent
        + fat_percent
        + carb_percent,
        2
    ) != 100:

        raise ValueError(
            "Macro percentages must add up to 100%."
        )

    protein_calories = (
        total_calories
        * protein_percent
        / 100
    )

    fat_calories = (
        total_calories
        * fat_percent
        / 100
    )

    carb_calories = (
        total_calories
        * carb_percent
        / 100
    )

    return {

        "protein_grams":
            round(
                protein_calories / 4,
                1
            ),

        "fat_grams":
            round(
                fat_calories / 9,
                1
            ),

        "carb_grams":
            round(
                carb_calories / 4,
                1
            ),

        "protein_calories":
            round(
                protein_calories
            ),

        "fat_calories":
            round(
                fat_calories
            ),

        "carb_calories":
            round(
                carb_calories
            )

    }