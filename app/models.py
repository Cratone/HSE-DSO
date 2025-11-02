"""Pydantic models for Recipe Box API."""

from typing import List

from pydantic import BaseModel, Field, field_validator

# Allowed units for ingredient measurements
ALLOWED_UNITS = {"g", "kg", "ml", "l", "tsp", "tbsp", "pcs"}


class IngredientBase(BaseModel):
    """Base model for ingredient."""

    name: str = Field(..., min_length=1, max_length=100)


class IngredientCreate(IngredientBase):
    """Model for creating ingredient."""

    pass


class Ingredient(IngredientBase):
    """Full ingredient model with ID."""

    id: int


class RecipeIngredientBase(BaseModel):
    """Base model for recipe ingredient with amount and unit."""

    ingredient_id: int
    amount: float = Field(..., gt=0, le=999999.99)
    unit: str = Field(..., min_length=1, max_length=10)

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        """Validate that unit is in allowed list."""
        if v not in ALLOWED_UNITS:
            allowed = ", ".join(sorted(ALLOWED_UNITS))
            raise ValueError(f"Unit must be one of: {allowed}. Got: {v}")
        return v


class RecipeIngredientCreate(RecipeIngredientBase):
    """Model for creating recipe ingredient."""

    pass


class RecipeIngredient(RecipeIngredientBase):
    """Full recipe ingredient model."""

    pass


class RecipeBase(BaseModel):
    """Base model for recipe."""

    title: str = Field(..., min_length=1, max_length=200)
    steps: str = Field(..., min_length=1, max_length=10000)


class RecipeCreate(RecipeBase):
    """Model for creating recipe with ingredients."""

    ingredients: List[RecipeIngredientCreate] = Field(
        ..., max_length=100, description="Maximum 100 ingredients per recipe"
    )


class RecipeUpdate(BaseModel):
    """Model for updating recipe (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=200)
    steps: str | None = Field(None, min_length=1, max_length=10000)
    ingredients: List[RecipeIngredientCreate] | None = Field(
        None, max_length=100, description="Maximum 100 ingredients per recipe"
    )


class Recipe(RecipeBase):
    """Full recipe model with ID and ingredients."""

    id: int
    owner_id: int
    ingredients: List[RecipeIngredient] = []
