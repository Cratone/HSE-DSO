"""Tests for input size limits (ADR-003)."""

import pytest
from pydantic import ValidationError

from app import models


class TestRecipeTitleLimits:
    """Tests for recipe title length validation."""

    def test_title_min_length(self):
        """Test that empty title is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            models.RecipeCreate(
                title="",
                steps="Some steps",
                ingredients=[],
            )

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("title",)

    def test_title_max_length_accepted(self):
        """Test that title at max length (200) is accepted."""
        title = "A" * 200
        recipe = models.RecipeCreate(
            title=title,
            steps="Some steps",
            ingredients=[],
        )
        assert len(recipe.title) == 200

    def test_title_over_max_length_rejected(self):
        """Test that title over max length is rejected."""
        title = "A" * 201
        with pytest.raises(ValidationError) as exc_info:
            models.RecipeCreate(
                title=title,
                steps="Some steps",
                ingredients=[],
            )

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("title",)
        assert "at most 200 characters" in error["msg"]


class TestRecipeStepsLimits:
    """Tests for recipe steps length validation."""

    def test_steps_min_length(self):
        """Test that empty steps are rejected."""
        with pytest.raises(ValidationError):
            models.RecipeCreate(
                title="Test Recipe",
                steps="",
                ingredients=[],
            )

    def test_steps_max_length_accepted(self):
        """Test that steps at max length (10000) are accepted."""
        # Create exactly 10000 chars
        steps = "A" * 10000

        recipe = models.RecipeCreate(
            title="Long Recipe",
            steps=steps,
            ingredients=[],
        )
        assert len(recipe.steps) == 10000

    def test_steps_over_max_length_rejected(self):
        """Test that steps over max length are rejected."""
        steps = "A" * 10001

        with pytest.raises(ValidationError) as exc_info:
            models.RecipeCreate(
                title="Test Recipe",
                steps=steps,
                ingredients=[],
            )

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("steps",)
        assert "at most 10000 characters" in error["msg"]


class TestMaxIngredientsLimit:
    """Tests for maximum number of ingredients per recipe."""

    def test_max_ingredients_accepted(self):
        """Test that 100 ingredients (max) are accepted."""
        ingredients = [
            models.RecipeIngredientCreate(ingredient_id=i, amount=10.0, unit="g")
            for i in range(1, 101)
        ]

        recipe = models.RecipeCreate(
            title="Recipe with 100 ingredients",
            steps="Mix everything",
            ingredients=ingredients,
        )
        assert len(recipe.ingredients) == 100

    def test_over_max_ingredients_rejected(self):
        """Test that more than 100 ingredients are rejected."""
        ingredients = [
            models.RecipeIngredientCreate(ingredient_id=i, amount=10.0, unit="g")
            for i in range(1, 102)
        ]

        with pytest.raises(ValidationError) as exc_info:
            models.RecipeCreate(
                title="Recipe with 101 ingredients",
                steps="Mix everything",
                ingredients=ingredients,
            )

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ingredients",)
        assert "at most 100 items" in error["msg"]


class TestIngredientNameLimits:
    """Tests for ingredient name length validation."""

    def test_ingredient_name_min_length(self):
        """Test that empty ingredient name is rejected."""
        with pytest.raises(ValidationError):
            models.IngredientCreate(name="")

    def test_ingredient_name_max_length_accepted(self):
        """Test that ingredient name at max length (100) is accepted."""
        name = "A" * 100
        ingredient = models.IngredientCreate(name=name)
        assert len(ingredient.name) == 100

    def test_ingredient_name_over_max_length_rejected(self):
        """Test that ingredient name over 100 chars is rejected."""
        name = "A" * 101

        with pytest.raises(ValidationError) as exc_info:
            models.IngredientCreate(name=name)

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("name",)
        assert "at most 100 characters" in error["msg"]


class TestRecipeUpdateLimits:
    """Tests for RecipeUpdate model limits."""

    def test_update_title_over_max_rejected(self):
        """Test that updating title to over max length is rejected."""
        with pytest.raises(ValidationError):
            models.RecipeUpdate(title="A" * 201)

    def test_update_steps_over_max_rejected(self):
        """Test that updating steps to over max length is rejected."""
        with pytest.raises(ValidationError):
            models.RecipeUpdate(steps="A" * 10001)

    def test_update_ingredients_over_max_rejected(self):
        """Test that updating to over 100 ingredients is rejected."""
        ingredients = [
            models.RecipeIngredientCreate(ingredient_id=i, amount=10.0, unit="g")
            for i in range(1, 102)
        ]

        with pytest.raises(ValidationError):
            models.RecipeUpdate(ingredients=ingredients)


class TestUnitFieldLimit:
    """Tests for unit field max length."""

    def test_unit_max_length(self):
        """Test that unit has max_length=10."""
        # Valid short unit
        valid = models.RecipeIngredientCreate(ingredient_id=1, amount=10.0, unit="g")
        assert valid.unit == "g"

        # 10 chars should work (though not in ALLOWED_UNITS)
        # This will fail on unit validation, not length
        with pytest.raises(ValidationError) as exc_info:
            models.RecipeIngredientCreate(ingredient_id=1, amount=10.0, unit="A" * 10)

        # But the error should be about allowed units, not length
        error = exc_info.value.errors()[0]
        assert "Unit must be one of" in error["msg"]

        # 11 chars should fail on length
        with pytest.raises(ValidationError) as exc_info:
            models.RecipeIngredientCreate(ingredient_id=1, amount=10.0, unit="A" * 11)

        errors = exc_info.value.errors()
        # Should have length error
        assert any("at most 10 characters" in e["msg"] for e in errors)
