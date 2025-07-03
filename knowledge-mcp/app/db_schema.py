from typing import List, Dict, Optional, Any
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from datetime import datetime


# Tenant schemas
class TenantCreate(BaseModel):
    tenant_id: str


class TenantInfo(BaseModel):
    tenant_id: str
    created_at: datetime


# File-level metadata
class FileMetadata(BaseModel):
    filename: str
    content_type: str
    text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    extra: Dict[str, Any] = Field(default_factory=dict)


class FileCreate(BaseModel):
    file_id: str
    metadata: FileMetadata


class FileInfo(BaseModel):
    file_id: str
    metadata: FileMetadata
    created_at: datetime


# Chunk-level metadata including text
class ChunkMetadata(BaseModel):
    text: str  # content of the chunk
    offset: Optional[int] = None  # chunk sequence or offset
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChunkUpsert(BaseModel):
    chunk_id: str
    embedding: Annotated[List[float], Field(min_items=1)]
    metadata: ChunkMetadata


class ChunkInfo(BaseModel):
    chunk_id: str
    score: float
    metadata: ChunkMetadata


class QueryRequest(BaseModel):
    embedding: Annotated[List[float], Field(min_items=1)]
    top_k: int = 5


class QueryResult(BaseModel):
    file_id: str
    chunk_id: str
    score: float
    metadata: ChunkMetadata


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    chunks_created: int
    message: str
