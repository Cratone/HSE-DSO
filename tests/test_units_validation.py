"""Tests for ingredient unit validation (ADR-002)."""

import pytest
from pydantic import ValidationError

from app.models import ALLOWED_UNITS, RecipeCreate, RecipeIngredientCreate


def test_allowed_units_constant():
    """Test that ALLOWED_UNITS is properly defined."""
    assert ALLOWED_UNITS == {"g", "kg", "ml", "l", "tsp", "tbsp", "pcs"}


def test_valid_units_accepted():
    """Test that all valid units are accepted."""
    for unit in ALLOWED_UNITS:
        # Should not raise ValidationError
        ingredient = RecipeIngredientCreate(
            ingredient_id=1,
            amount=100.0,
            unit=unit,
        )
        assert ingredient.unit == unit


def test_invalid_unit_rejected():
    """Test that invalid units are rejected."""
    invalid_units = ["щепотка", "cups", "oz", "pinch", "bunch", "handful"]

    for unit in invalid_units:
        with pytest.raises(ValidationError) as exc_info:
            RecipeIngredientCreate(
                ingredient_id=1,
                amount=100.0,
                unit=unit,
            )

        # Check that error message mentions allowed units
        error = exc_info.value.errors()[0]
        assert "Unit must be one of" in error["msg"]


def test_unit_validation_in_recipe_create():
    """Test that unit validation works in full recipe creation."""
    # Valid recipe
    valid_recipe = RecipeCreate(
        title="Test Recipe",
        steps="Mix and bake",
        ingredients=[
            RecipeIngredientCreate(ingredient_id=1, amount=500.0, unit="g"),
            RecipeIngredientCreate(ingredient_id=2, amount=2.0, unit="tbsp"),
        ],
    )
    assert len(valid_recipe.ingredients) == 2

    # Invalid recipe
    with pytest.raises(ValidationError):
        RecipeCreate(
            title="Bad Recipe",
            steps="Mix and bake",
            ingredients=[
                RecipeIngredientCreate(ingredient_id=1, amount=500.0, unit="cups"),
            ],
        )


def test_unit_case_sensitive():
    """Test that unit validation is case-sensitive."""
    # 'g' should work
    valid = RecipeIngredientCreate(ingredient_id=1, amount=100.0, unit="g")
    assert valid.unit == "g"

    # 'G' should fail
    with pytest.raises(ValidationError):
        RecipeIngredientCreate(ingredient_id=1, amount=100.0, unit="G")


def test_amount_positive():
    """Test that amount must be positive."""
    # Positive amount OK
    valid = RecipeIngredientCreate(ingredient_id=1, amount=100.0, unit="g")
    assert valid.amount == 100.0

    # Zero amount should fail
    with pytest.raises(ValidationError):
        RecipeIngredientCreate(ingredient_id=1, amount=0.0, unit="g")

    # Negative amount should fail
    with pytest.raises(ValidationError):
        RecipeIngredientCreate(ingredient_id=1, amount=-5.0, unit="g")


def test_amount_max_value():
    """Test that amount has reasonable maximum."""
    # Just under limit should work
    valid = RecipeIngredientCreate(ingredient_id=1, amount=999999.99, unit="g")
    assert valid.amount == 999999.99

    # Over limit should fail
    with pytest.raises(ValidationError):
        RecipeIngredientCreate(ingredient_id=1, amount=1000000.0, unit="g")
