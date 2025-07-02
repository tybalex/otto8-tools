import app.vector_db as db
import app.db_schema as schemas

from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Literal
import os
from fastmcp.exceptions import ToolError

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
    tenant_id = headers.get("x-forwarded-tenant-id", None)
    if not tenant_id:
        raise ToolError("No tenant id found in headers")
    return tenant_id

# @mcp.on_event("startup")
# async def on_startup():
#     await db.init_db()

## manage tenant tools
@mcp.tool
async def create_tenant(tenant: schemas.TenantCreate):
    await db.create_tenant(tenant.tenant_id)
    tenants = await db.list_tenants()
    for t in tenants:
        if t.tenant_id == tenant.tenant_id:
            return schemas.TenantInfo(
                tenant_id=t.tenant_id,
                plan="free",
                created_at=t.created_at
            )
    raise ToolError("500: Failed to create tenant")

@mcp.tool
async def list_tenants() -> list:
    ts = await db.list_tenants()
    return [schemas.TenantInfo(**t.__dict__) for t in ts]

@mcp.tool
async def delete_tenant(tenant_id: str) -> dict:
    await db.delete_tenant(tenant_id)
    return {"detail": "tenant and related data deleted"}


## client tools

@mcp.tool
async def create_file(
    tenant_id: str,
    file: schemas.FileCreate,
) -> dict:
    await db.create_file(
        tenant_id,
        file.file_id,
        file.metadata.dict()
    )
    return {"detail": "file created"}

@mcp.tool
async def upsert_chunks(
    tenant_id: str,
    file_id: str,
    chunks: list[schemas.ChunkUpsert],
) -> dict:
    await db.upsert_chunks(tenant_id, file_id, chunks)
    return {"detail": "chunks upserted"}

@mcp.tool
async def delete_file(tenant_id: str, file_id: str) -> dict:
    ok = await db.delete_file(tenant_id, file_id)
    if not ok:
        raise ToolError("Failed to delete file")
    return {"detail": "file deleted"}

@mcp.tool
async def query_chunks(
    tenant_id: str,
    q: schemas.QueryRequest
):
    rows = await db.query_chunks(
        tenant_id, q.embedding, q.top_k
    )
    return [
        schemas.QueryResult(
            file_id=r.file_id,
            chunk_id=r.chunk_id,
            score=r.score,
            metadata=schemas.ChunkMetadata(**r.chunk_metadata)
        ) for r in rows
    ]

def streamable_http_server():
    """Main entry point for the MCP server."""
    mcp.run(
        transport="streamable-http", # fixed to streamable-http
        host="0.0.0.0",
        port=PORT,
        path=MCP_PATH,
    )


if __name__ == "__main__":
    streamable_http_server()