"""Pydantic models for Recipe Box API."""

from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Allowed units for ingredient measurements
ALLOWED_UNITS = {"g", "kg", "ml", "l", "tsp", "tbsp", "pcs"}


class StrictModel(BaseModel):
    """Base model with strict validation and trimmed strings."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class IngredientBase(StrictModel):
    """Base model for ingredient."""

    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value:
            raise ValueError("name must not be empty")
        return value


class IngredientCreate(IngredientBase):
    """Model for creating ingredient."""

    pass


class Ingredient(IngredientBase):
    """Full ingredient model with ID."""

    id: int


class RecipeIngredientBase(StrictModel):
    """Base model for recipe ingredient with amount and unit."""

    ingredient_id: int
    amount: Decimal = Field(..., gt=0, le=999_999.99)
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


class RecipeBase(StrictModel):
    """Base model for recipe."""

    title: str = Field(..., min_length=1, max_length=200)
    steps: str = Field(..., min_length=1, max_length=10000)


class RecipeCreate(RecipeBase):
    """Model for creating recipe with ingredients."""

    ingredients: List[RecipeIngredientCreate] = Field(
        ..., max_length=100, description="Maximum 100 ingredients per recipe"
    )


class RecipeUpdate(StrictModel):
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
    ingredients: List[RecipeIngredient] = Field(default_factory=list)


class UserBase(StrictModel):
    """Base user schema."""

    email: str = Field(..., min_length=5, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("email must contain '@' and domain part")
        local, _, domain = email.partition("@")
        if "." not in domain or not local or not domain:
            raise ValueError("email must contain domain with dot")
        return email


class UserRegister(UserBase):
    """Payload for user registration."""

    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(ch.isalpha() for ch in value) or not any(
            ch.isdigit() for ch in value
        ):
            raise ValueError("password must include letters and digits")
        return value


class UserLogin(UserBase):
    """Payload for user login."""

    password: str = Field(..., min_length=8, max_length=128)


class UserPublic(UserBase):
    """User information returned to clients."""

    id: int


class TokenResponse(StrictModel):
    """Bearer token returned after successful authentication."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
