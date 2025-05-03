from pydantic import BaseModel, Field

class PostInteractionRequest(BaseModel):
    post_id: str = Field(..., min_length=15, max_length=20, pattern=r'^\d+$')
