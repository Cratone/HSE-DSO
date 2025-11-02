from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.errors import problem

app = FastAPI(title="Recipe Box API", version="0.1.0")


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
    # Format validation errors for user
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
        extras={"validation_errors": errors},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with RFC 7807 format (masked details)."""
    # Log the actual error for debugging (would use proper logger in production)
    import traceback

    traceback.print_exc()

    # Return masked error to client
    return problem(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred. Please contact support.",
        type_="about:blank",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise HTTPException(status_code=422, detail="name must be 1..100 chars")
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise HTTPException(status_code=404, detail="item not found")
