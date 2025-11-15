"""FastAPI application entry point for the Recipe Box service."""

import base64
import hashlib
import hmac
import secrets
from itertools import count
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import problem
from app.models import (
    Ingredient,
    IngredientCreate,
    Recipe,
    RecipeCreate,
    RecipeIngredient,
    RecipeIngredientCreate,
    RecipeUpdate,
    TokenResponse,
    UserLogin,
    UserPublic,
    UserRegister,
)

app = FastAPI(title="Recipe Box API", version="0.3.0")

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Bearer token issued by POST /auth/login",
)


PASSWORD_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256."""

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored PBKDF2 hash."""

    try:
        salt_b64, digest_b64 = stored.split(":", 1)
    except ValueError:
        return False
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(digest_b64)
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return hmac.compare_digest(actual, expected)


def generate_token() -> str:
    """Generate random session token."""

    return secrets.token_urlsafe(32)


class InMemoryRecipeStore:
    """Simple in-memory storage to support the MVP use-case."""

    def __init__(self) -> None:
        self._ingredients: dict[int, Ingredient] = {}
        self._ingredients_by_name: dict[str, int] = {}
        self._recipes: dict[int, Recipe] = {}
        self._ingredient_seq = count(start=1)
        self._recipe_seq = count(start=1)
        self._users: dict[int, dict[str, str]] = {}
        self._users_by_email: dict[str, int] = {}
        self._sessions: dict[str, int] = {}
        self._user_seq = count(start=1)

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().casefold()

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def create_ingredient(self, payload: IngredientCreate) -> Ingredient:
        norm = self._normalize_name(payload.name)
        if norm in self._ingredients_by_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists"
            )

        ingredient = Ingredient(id=next(self._ingredient_seq), name=payload.name)
        self._ingredients[ingredient.id] = ingredient
        self._ingredients_by_name[norm] = ingredient.id
        return ingredient.model_copy(deep=True)

    def list_ingredients(self) -> List[Ingredient]:
        return [
            ingredient.model_copy(deep=True)
            for ingredient in self._ingredients.values()
        ]

    def get_ingredient(self, ingredient_id: int) -> Ingredient:
        ingredient = self._ingredients.get(ingredient_id)
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found"
            )
        return ingredient.model_copy(deep=True)

    def reset(self) -> None:
        """Utility for tests to wipe the in-memory state."""

        self._ingredients.clear()
        self._ingredients_by_name.clear()
        self._recipes.clear()
        self._ingredient_seq = count(start=1)
        self._recipe_seq = count(start=1)
        self._users.clear()
        self._users_by_email.clear()
        self._sessions.clear()
        self._user_seq = count(start=1)

    def create_user(self, payload: UserRegister) -> UserPublic:
        email = self._normalize_email(payload.email)
        if email in self._users_by_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already exists"
            )

        user_id = next(self._user_seq)
        record = {
            "id": user_id,
            "email": email,
            "password_hash": hash_password(payload.password),
        }
        self._users[user_id] = record
        self._users_by_email[email] = user_id
        return UserPublic(id=user_id, email=email)

    def authenticate_user(self, payload: UserLogin) -> str:
        email = self._normalize_email(payload.email)
        user_id = self._users_by_email.get(email)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        record = self._users[user_id]
        if not verify_password(payload.password, record["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        token = generate_token()
        self._sessions[token] = user_id
        return token

    def get_user_by_token(self, token: str) -> UserPublic:
        user_id = self._sessions.get(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return self.get_user(user_id)

    def get_user(self, user_id: int) -> UserPublic:
        record = self._users.get(user_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return UserPublic(id=record["id"], email=record["email"])

    def create_recipe(self, payload: RecipeCreate, owner_id: int) -> Recipe:
        recipe_ingredients = [
            self._convert_recipe_ingredient(ing) for ing in payload.ingredients
        ]
        recipe = Recipe(
            id=next(self._recipe_seq),
            owner_id=owner_id,
            title=payload.title,
            steps=payload.steps,
            ingredients=recipe_ingredients,
        )
        self._recipes[recipe.id] = recipe
        return recipe.model_copy(deep=True)

    def list_recipes(
        self, owner_id: int, ingredient_name: str | None = None
    ) -> List[Recipe]:
        recipes = [
            recipe for recipe in self._recipes.values() if recipe.owner_id == owner_id
        ]
        if ingredient_name:
            norm = self._normalize_name(ingredient_name)
            ingredient_id = self._ingredients_by_name.get(norm)
            if ingredient_id is None:
                return []
            recipes = [
                recipe
                for recipe in recipes
                if any(ing.ingredient_id == ingredient_id for ing in recipe.ingredients)
            ]
        return [recipe.model_copy(deep=True) for recipe in recipes]

    def get_recipe(self, recipe_id: int, owner_id: int) -> Recipe:
        recipe = self._recipes.get(recipe_id)
        if not recipe or recipe.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
            )
        return recipe.model_copy(deep=True)

    def update_recipe(
        self, recipe_id: int, owner_id: int, payload: RecipeUpdate
    ) -> Recipe:
        recipe = self._recipes.get(recipe_id)
        if not recipe or recipe.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
            )

        recipe_data = recipe.model_dump()
        if payload.title is not None:
            recipe_data["title"] = payload.title
        if payload.steps is not None:
            recipe_data["steps"] = payload.steps
        if payload.ingredients is not None:
            recipe_data["ingredients"] = [
                self._convert_recipe_ingredient(ing) for ing in payload.ingredients
            ]

        updated = Recipe(**recipe_data)
        self._recipes[recipe_id] = updated
        return updated.model_copy(deep=True)

    def delete_recipe(self, recipe_id: int, owner_id: int) -> None:
        recipe = self._recipes.get(recipe_id)
        if not recipe or recipe.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
            )
        del self._recipes[recipe_id]

    def _convert_recipe_ingredient(
        self, ingredient: RecipeIngredientCreate
    ) -> RecipeIngredient:
        if ingredient.ingredient_id not in self._ingredients:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown ingredient_id={ingredient.ingredient_id}",
            )
        return RecipeIngredient(**ingredient.model_dump())


STORE = InMemoryRecipeStore()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> UserPublic:
    """Retrieve current authenticated user from bearer token."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    return STORE.get_user_by_token(token)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException with RFC 7807 format."""
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return problem(
        status=exc.status_code,
        title=f"HTTP {exc.status_code}",
        detail=detail,
        type_="about:blank",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with RFC 7807 format."""
    errors = exc.errors()
    sanitized_errors = []
    for error in errors:
        error_copy = error.copy()
        ctx = error_copy.get("ctx")
        if ctx:
            error_copy["ctx"] = {
                key: (str(value) if isinstance(value, Exception) else value)
                for key, value in ctx.items()
            }
        sanitized_errors.append(error_copy)
    error_details = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field}: {error['msg']}")

    detail = "; ".join(error_details)
    return problem(
        status=422,
        title="Validation Error",
        detail=detail,
        type_="about:blank",
        extras={"validation_errors": sanitized_errors},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with RFC 7807 format (masked details)."""
    import traceback

    traceback.print_exc()

    return problem(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred. Please contact support.",
        type_="about:blank",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
def register_user(payload: UserRegister):
    return STORE.create_user(payload)


@app.post("/auth/login", response_model=TokenResponse)
def login_user(payload: UserLogin):
    token = STORE.authenticate_user(payload)
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=UserPublic)
def read_current_user(current_user: UserPublic = Depends(get_current_user)):
    return current_user


@app.post("/ingredients", response_model=Ingredient)
def create_ingredient(
    payload: IngredientCreate,
    current_user: UserPublic = Depends(get_current_user),
):
    return STORE.create_ingredient(payload)


@app.get("/ingredients", response_model=list[Ingredient])
def list_ingredients(
    current_user: UserPublic = Depends(get_current_user),
):
    return STORE.list_ingredients()


@app.get("/ingredients/{ingredient_id}", response_model=Ingredient)
def get_ingredient(
    ingredient_id: int,
    current_user: UserPublic = Depends(get_current_user),
):
    return STORE.get_ingredient(ingredient_id)


@app.post("/recipes", response_model=Recipe, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreate,
    current_user: UserPublic = Depends(get_current_user),
):
    return STORE.create_recipe(payload, owner_id=current_user.id)


@app.get("/recipes", response_model=list[Recipe])
def list_recipes(
    ingredient: str | None = Query(default=None, min_length=1, max_length=100),
    current_user: UserPublic = Depends(get_current_user),
):
    return STORE.list_recipes(owner_id=current_user.id, ingredient_name=ingredient)


@app.get("/recipes/{recipe_id}", response_model=Recipe)
def get_recipe(
    recipe_id: int,
    current_user: UserPublic = Depends(get_current_user),
):
    return STORE.get_recipe(recipe_id, owner_id=current_user.id)


@app.patch("/recipes/{recipe_id}", response_model=Recipe)
def update_recipe(
    recipe_id: int,
    payload: RecipeUpdate,
    current_user: UserPublic = Depends(get_current_user),
):
    if payload.model_dump(exclude_none=True) == {}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )
    return STORE.update_recipe(recipe_id, owner_id=current_user.id, payload=payload)


@app.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    current_user: UserPublic = Depends(get_current_user),
):
    STORE.delete_recipe(recipe_id, owner_id=current_user.id)
