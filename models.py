# models.py
# SQLAlchemy models for the Lifestyle Guru SQLite database

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class UserProfile(Base):
    """Stores the user's profile information."""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String(20), nullable=False)

    unit_system = Column(
        String(20),
        nullable=False,
        default="metric"
    )

    # Metric measurements
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)

    # US measurements
    weight_lbs = Column(Float, nullable=True)
    height_feet = Column(Integer, nullable=True)
    height_inches = Column(Float, nullable=True)

    # Lifestyle information
    activity_level = Column(String(50), nullable=True)
    goal = Column(String(50), nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    macro_goals = relationship(
        "MacroGoals",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    meals = relationship(
        "Meal",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class MacroGoals(Base):
    """Stores the user's daily calorie and macro goals."""

    __tablename__ = "macro_goals"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("user_profiles.id"),
        nullable=False,
        unique=True
    )

    total_calories = Column(
        Float,
        nullable=False
    )

    protein_percent = Column(
        Float,
        nullable=False
    )

    fat_percent = Column(
        Float,
        nullable=False
    )

    carb_percent = Column(
        Float,
        nullable=False
    )

    protein_grams = Column(
        Float,
        nullable=True
    )

    fat_grams = Column(
        Float,
        nullable=True
    )

    carb_grams = Column(
        Float,
        nullable=True
    )

    # Relationship back to UserProfile
    user = relationship(
        "UserProfile",
        back_populates="macro_goals"
    )


class Meal(Base):
    """Stores meals and food entered by the user."""

    __tablename__ = "meals"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("user_profiles.id"),
        nullable=False
    )

    name = Column(
        String(100),
        nullable=False
    )

    meal_type = Column(
        String(50),
        nullable=False
    )

    protein_grams = Column(
        Float,
        nullable=False
    )

    fat_grams = Column(
        Float,
        nullable=False
    )

    carb_grams = Column(
        Float,
        nullable=False
    )

    total_calories = Column(
        Float,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship back to UserProfile
    user = relationship(
        "UserProfile",
        back_populates="meals"
    )