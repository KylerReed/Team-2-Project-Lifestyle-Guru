# models.py

from pydantic import BaseModel, Field
from typing import Optional


# User Profile

class UserProfile(BaseModel):
    name: str

    age: int = Field(
        gt=0,
        lt=120
    )

    sex: str

    unit_system: str = "metric"

    # Metric Measurements
    weight_kg: Optional[float] = Field(
        default=None,
        gt=0
    )

    height_cm: Optional[float] = Field(
        default=None,
        gt=0
    )

    # US Measurements
    weight_lbs: Optional[float] = Field(
        default=None,
        gt=0
    )

    height_feet: Optional[int] = Field(
        default=None,
        gt=0
    )

    height_inches: Optional[int] = Field(
        default=None,
        gt=0,
        lt=12
    )

    activity_level: str

    goal: str 



# Macro Goals


class MacroGoals(BaseModel):

    total_calories: float = Field(
        gt=0
    )

    protein_percent: float = Field(
        gt=0,
        lt=100
    )

    fat_percent: float = Field(
        gt=0,
        lt=100
    )

    carb_percent: float = Field(
        gt=0,
        lt=100
    )



# Meal 


class Meal(BaseModel):

    name: str

    meal_type: str

    protein_grams: float = Field(
        gt=0
    )

    fat_grams: float = Field(
        gt=0
    )

    carb_grams: float = Field(
        gt=0
    )


# User Results


class UserResults(BaseModel):

    bmi: float

    bmr: float

    tdee: float

    calorie_goal: float

    protein_grams: float

    fat_grams: float

    carb_grams: float


# Meal Results

class MealResults(BaseModel):

    name: str

    meal_type: str

    protein_grams: float

    fat_grams: float

    carb_grams: float

    total_calories: float