from pydantic import BaseModel


class ShortenRequest(BaseModel):
    long_url: str
    custom_code: str | None = None


class URLItem(BaseModel):
    long_url: str
    short_code: str
    click_count: int
    created_at: str


class URLListResponse(BaseModel):
    urls: list[URLItem]


class ShortenResponse(BaseModel):
    long_url: str
    short_code: str
    short_url: str
    click_count: int
    created_at: str


class ErrorDetails(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetails
