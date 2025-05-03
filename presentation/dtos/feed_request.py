from pydantic import BaseModel, Field

class FeedQueryParams(BaseModel):
    page: int = Field(default=1, gt=0)
    size: int = Field(default=10, gt=0, le=100)

class PostFindQueryParams(FeedQueryParams):
    description: str = Field(..., min_length=2, max_length=20)
