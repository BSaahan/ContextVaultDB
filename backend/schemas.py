from pydantic import BaseModel

class MemoryCreate(BaseModel):
    title: str
    content: str
    category: str = "general"

class MemoryResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str

    class Config:
        from_attributes = True
        
class MemorySearch(BaseModel):
    query: str
    top_k: int = 3

class ChatRequest(BaseModel):
    question: str
    top_k: int = 3