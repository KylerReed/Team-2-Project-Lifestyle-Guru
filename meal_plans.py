from functools import lru_cache
import json
import math
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "data" / "calorie_tracker_food_examples.json"

REQUIRED_FIELDS = {
    "goal",
    "activity_level",
    "meal",
    "id",
    "name",
    "serving_g",
    "calories",
    "protein_g",
    "fat_g",
    "carbs_g",
}

GOALS = {"Lose weight", "Maintain weight", "Gain weight"}

MEAL_TYPES = {"Breakfast", "Lunch", "Dinner", "Snacks"}

ACTIVITY_RECOMMENDATION_MAP = {
    "sedentary": "Sedentary",
    "low": "Lightly Active",
    "lightly active": "Lightly Active",
    "average": "Moderately Active",
    "moderately active": "Moderately Active",
    "high": "Very Active",
    "active": "Very Active",
    "very active": "Very Active",
}

NUMERIC_FIELDS = (
    "serving_g",
    "calories",
    "protein_g",
    "fat_g",
    "carbs_g",
)


def normalize_activity_level(activity_level):
    try:
        return ACTIVITY_RECOMMENDATION_MAP[str(activity_level).strip().lower()]
    except KeyError as error:
        raise ValueError("Choose a valid activity level.") from error


def _validate_record(record, index):
    if not isinstance(record, dict):
        raise ValueError(f"Catalog record {index} must be an object.")

    missing_fields = REQUIRED_FIELDS - record.keys()

    if missing_fields:
        raise ValueError(
            f"Catalog record {index} is missing: {', '.join(sorted(missing_fields))}."
        )

    if record["goal"] not in GOALS:
        raise ValueError(f"Catalog record {index} has an invalid goal.")

    if record["activity_level"] not in set(ACTIVITY_RECOMMENDATION_MAP.values()):
        raise ValueError(f"Catalog record {index} has an invalid activity level.")

    if record["meal"] not in MEAL_TYPES:
        raise ValueError(f"Catalog record {index} has an invalid meal type.")

    for field in ("id", "name"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"Catalog record {index} has an invalid {field}.")

    for field in NUMERIC_FIELDS:
        value = record[field]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"Catalog record {index} has an invalid {field}.")

    if record["serving_g"] <= 0:
        raise ValueError(f"Catalog record {index} must have a positive serving size.")


@lru_cache(maxsize=4)
def load_recommendation_catalog(catalog_path=None):
    path = Path(catalog_path) if catalog_path is not None else CATALOG_PATH

    try:
        with path.open(encoding="utf-8") as catalog_file:
            records = json.load(catalog_file)

    except FileNotFoundError as error:
        raise ValueError(f"Recommendation catalog is missing: {path}") from error

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Recommendation catalog is not valid JSON: {error}"
        ) from error

    if not isinstance(records, list):
        raise ValueError("Recommendation catalog must contain a list of records.")

    seen_ids = set()

    for index, record in enumerate(records, start=1):
        _validate_record(record, index)

        if record["id"] in seen_ids:
            raise ValueError(
                f"Recommendation catalog has duplicate id {record['id']!r}."
            )

        seen_ids.add(record["id"])

    return tuple(records)


def get_recommendations(
    goal,
    activity_level,
    meal_type,
    catalog_path=None,
):
    if goal not in GOALS or meal_type not in MEAL_TYPES:
        return ()

    normalized_activity = normalize_activity_level(activity_level)

    return tuple(
        record
        for record in load_recommendation_catalog(catalog_path)
        if record["goal"] == goal
        and record["activity_level"] == normalized_activity
        and record["meal"] == meal_type
    )


def get_recommendation(recommendation_id, catalog_path=None):
    recommendation_id = str(recommendation_id or "").strip()

    if not recommendation_id:
        return None

    return next(
        (
            record
            for record in load_recommendation_catalog(catalog_path)
            if record["id"] == recommendation_id
        ),
        None,
    )
