import asyncio
from datetime import datetime
import app.vector_db as db
import app.db_schema as schemas
import app.text_processing as text_proc
import app.embeddings as embeddings

from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Literal
import os
from fastmcp.exceptions import ToolError
from uuid import uuid4
import hashlib

# Import all the command functions
from fastmcp.server.dependencies import get_http_headers

# Configure server-specific settings
PORT = os.getenv("PORT", 9000)
MCP_PATH = os.getenv("MCP_PATH", "/mcp/knowledge")

mcp = FastMCP(
    name="KnowledgeMCPServer",
    on_duplicate_tools="error",                  # Handle duplicate registrations
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
)

def _get_tenant_id() -> str:
    headers = get_http_headers()
    tenant_id = headers.get("x-forwarded-user", None)
    if not tenant_id:
        raise ToolError("No tenant id found in headers")
    return tenant_id

# Use the embedding service
generate_embedding = embeddings.generate_embedding

## manage tenant tools
@mcp.tool(
    name="create_knowledge_set",
)
async def create_tenant() -> schemas.TenantInfo:
    tenant_id = str(uuid4())
    await db.create_tenant(tenant_id)
    return schemas.TenantInfo(
        tenant_id=tenant_id,
        created_at=datetime.now()
    )

@mcp.tool(
    name="list_knowledge_sets",
)
async def list_tenants() -> list:
    ts = await db.list_tenants()
    return [schemas.TenantInfo(**t.__dict__) for t in ts]

@mcp.tool(
    name="delete_knowledge_set",
)
async def delete_tenant() -> dict:
    tenant_id = _get_tenant_id()
    await db.delete_tenant(tenant_id)
    return {"detail": "tenant and related data deleted"}


## client tools

@mcp.tool(
    name="ingest_file"
)
async def ingest_file(
    filename: Annotated[str, Field(description="The name of the file")],
    content_type: Annotated[str, Field(description="The type of the file")],
    content: Annotated[bytes, Field(description="The content of the file")]
) -> schemas.FileUploadResponse:
    """
    Upload and process a file: extract text, chunk it, generate embeddings, and store.
    This is the main file upload endpoint that handles the complete workflow.
    """
    tenant_id = _get_tenant_id()
    
    try:
        # Generate unique file ID
        file_id = str(uuid4())
        
        # Extract text from file content
        raw_text = text_proc.extract_text_from_content(
            content, 
            content_type
        )
        
        # Clean the text
        cleaned_text = text_proc.clean_text(raw_text)
        
        # Create file metadata
        file_metadata = schemas.FileMetadata(
            filename=filename,
            content_type=content_type,
            text=cleaned_text,
            created_at=datetime.now(),
            extra={
                "original_size": len(content),
                "processed_size": len(cleaned_text),
            }
        )
        
        # Store file metadata
        await db.create_file(
            tenant_id,
            file_id,
            file_metadata.model_dump(mode='json')
        )
        
        # Chunk the text
        text_chunks = text_proc.chunk_text(
            cleaned_text
        )
        
        # Generate embeddings and create chunk objects
        chunks_to_upsert = []
        for i, (chunk_text, offset) in enumerate(text_chunks):
            # Generate embedding for this chunk
            embedding = await generate_embedding(chunk_text)
            
            # Create chunk metadata
            chunk_metadata = schemas.ChunkMetadata(
                text=chunk_text,
                offset=offset,
                extra={
                    "chunk_index": i,
                    "chunk_length": len(chunk_text)
                }
            )
            
            # Create chunk upsert object
            chunk_upsert = schemas.ChunkUpsert(
                chunk_id=f"{file_id}_chunk_{i}",
                embedding=embedding,
                metadata=chunk_metadata
            )
            chunks_to_upsert.append(chunk_upsert)
        
        # Store all chunks
        if chunks_to_upsert:
            await db.upsert_chunks(tenant_id, file_id, chunks_to_upsert)
        
        return schemas.FileUploadResponse(
            file_id=file_id,
            filename=filename,
            chunks_created=len(chunks_to_upsert),
            message=f"Successfully processed file '{filename}' into {len(chunks_to_upsert)} chunks"
        )
        
    except Exception as e:
        raise ToolError(f"Failed to process file: {str(e)}")


@mcp.tool(
    name="list_files"
)
async def list_files() -> list[schemas.FileInfo]:
    """List all files for the current tenant."""
    tenant_id = _get_tenant_id()
    files = await db.list_files(tenant_id)
    if not files:
        return []
    return [
        schemas.FileInfo(
            file_id=f.file_id,
            metadata=schemas.FileMetadata(**f.file_metadata),
            created_at=f.created_at
        ) for f in files
    ]

@mcp.tool(
    name="remove_file"
)
async def delete_file(file_id: str) -> dict:
    """Delete a file and all its chunks."""
    tenant_id = _get_tenant_id()
    ok = await db.delete_file(tenant_id, file_id)
    if not ok:
        raise ToolError("Failed to delete file")
    return {"detail": "file deleted"}

@mcp.tool(
    name="query"
)
async def text_query(
    query_text: Annotated[str, Field(description="The text to query the knowledge base")],
) -> list[schemas.QueryResult]:
    top_k = 5
    """Query chunks using text input"""
    tenant_id = _get_tenant_id()
    
    # Generate embedding for the query text
    query_embedding = await generate_embedding(query_text)
    
    # Query the database
    rows = await db.query_chunks(
        tenant_id, query_embedding, top_k
    )
    return [
        schemas.QueryResult(
            file_id=r.file_id,
            chunk_id=r.chunk_id,
            score=r.score,
            metadata=schemas.ChunkMetadata(**r.chunk_metadata)
        ) for r in rows
    ]

async def streamable_http_server():
    """Main entry point for the MCP server."""
    await db.init_db()
    await mcp.run_async(
        transport="streamable-http", # fixed to streamable-http
        host="0.0.0.0",
        port=PORT,
        path=MCP_PATH,
    )

if __name__ == "__main__":
    asyncio.run(streamable_http_server())