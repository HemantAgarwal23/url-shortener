import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from database import (
    get_all_links,
    get_existing_link_for_url,
    get_link_by_code,
    increment_click_count,
    init_db,
    save_url,
    short_code_exists,
)
from models import (
    ErrorResponse,
    ShortenRequest,
    ShortenResponse,
    URLItem,
    URLListResponse,
)
from utils import generate_short_code, is_valid_custom_code, is_valid_url

app = FastAPI(title="Minimal URL Shortener")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def raise_api_error(status_code: int, code: str, message: str) -> None:
    """Raise a structured HTTPException used by the API."""
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Convert HTTPException to a consistent structured JSON response."""
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    code = detail.get("code", "HTTP_ERROR")
    message = detail.get("message", str(exc.detail))
    logger.error("HTTP error %s: %s", code, message)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error={"code": code, "message": message}).model_dump(),
    )


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return validation failures in the same JSON error shape."""
    first_error = exc.errors()[0] if exc.errors() else {}
    message = first_error.get("msg", "Invalid request payload.")
    logger.error("Validation error: %s", message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error={"code": "VALIDATION_ERROR", "message": message}
        ).model_dump(),
    )


def create_unique_short_code() -> str:
    """Generate a unique code by retrying until an unused one is found."""
    while True:
        code = generate_short_code()
        if not short_code_exists(code):
            return code


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database and migrations when the app starts."""
    init_db()


@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest) -> ShortenResponse:
    """Create or reuse a short URL for the provided long URL."""
    long_url = payload.long_url.strip()
    custom_code = payload.custom_code.strip() if payload.custom_code else None

    if not long_url:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="MISSING_URL",
            message="long_url is required.",
        )

    if not is_valid_url(long_url):
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_URL",
            message="Invalid URL. Use a full http(s) URL like https://example.com",
        )

    if custom_code and not is_valid_custom_code(custom_code):
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_CUSTOM_CODE",
            message="custom_code must be alphanumeric and 3-20 characters long.",
        )

    if custom_code and short_code_exists(custom_code):
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="CUSTOM_CODE_ALREADY_EXISTS",
            message="The requested custom_code is already in use.",
        )

    # If the same long URL was already shortened, return existing code.
    existing_link = get_existing_link_for_url(long_url)
    if existing_link:
        existing_code, click_count, created_at = existing_link
        logger.info(
            "URL already shortened long_url=%s short_code=%s", long_url, existing_code
        )
        return ShortenResponse(
            long_url=long_url,
            short_code=existing_code,
            short_url=f"http://localhost:8000/{existing_code}",
            click_count=click_count,
            created_at=created_at,
        )

    short_code = custom_code if custom_code else create_unique_short_code()
    created_at = save_url(long_url, short_code)
    logger.info("URL shortened long_url=%s short_code=%s", long_url, short_code)

    return ShortenResponse(
        long_url=long_url,
        short_code=short_code,
        short_url=f"http://localhost:8000/{short_code}",
        click_count=0,
        created_at=created_at,
    )


@app.get("/urls", response_model=URLListResponse)
def list_urls() -> URLListResponse:
    """Return all stored URLs with metadata in a structured response."""
    stored_links = get_all_links()
    url_items = [
        URLItem(
            long_url=long_url,
            short_code=short_code,
            click_count=click_count,
            created_at=created_at,
        )
        for (long_url, short_code, click_count, created_at) in stored_links
    ]
    return URLListResponse(urls=url_items)


@app.get("/{code}")
def resolve_url(code: str) -> RedirectResponse:
    """Resolve a short code, increment clicks, and redirect to long URL."""
    stored_link = get_link_by_code(code)
    if not stored_link:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CODE_NOT_FOUND",
            message="Short code not found.",
        )

    long_url, _ = stored_link
    increment_click_count(code)
    logger.info("Redirecting short_code=%s long_url=%s", code, long_url)

    # Redirect user to original URL.
    return RedirectResponse(url=long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
