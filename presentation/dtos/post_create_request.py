from pydantic import BaseModel, Field

class PostCreateRequest(BaseModel):
    content: str = Field(..., max_length=1000, min_length=1)
