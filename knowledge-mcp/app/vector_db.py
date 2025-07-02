import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import (
    Column, String, JSON, TIMESTAMP, text,
    select, delete
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pgvector.sqlalchemy import Vector
from datetime import datetime

# config
database_url = os.getenv(
    "DATABASE_URL",
    # "postgresql+asyncpg://postgres:password@db:5432/postgres"
    "postgresql+asyncpg://postgres:password@localhost:5432/postgres"
)
engine = create_async_engine(database_url, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()
EMBED_DIM = 1536

# models
class Tenant(Base):
    __tablename__ = "tenants"
    tenant_id = Column(String, primary_key=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False
    )

class FileRecord(Base):
    __tablename__ = "files"
    tenant_id = Column(String, primary_key=True)
    file_id = Column(String, primary_key=True)
    file_metadata = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False
    )

class ChunkEntry(Base):
    __tablename__ = "chunks"
    tenant_id = Column(String, primary_key=True)
    file_id = Column(String, primary_key=True)
    chunk_id = Column(String, primary_key=True)
    embedding = Column(Vector(EMBED_DIM), nullable=False)
    chunk_metadata = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False
    )

# init database
async def init_db():
    async with engine.begin() as conn:
        # ensure pgvector extension is enabled
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # create tables and index
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_chunks_embedding "
                "ON chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);"
            )
        )

# tenant CRUD
async def create_tenant(tenant_id: str):
    async with AsyncSessionLocal() as session:
        stmt = pg_insert(Tenant).values(tenant_id=tenant_id)
        stmt = stmt.on_conflict_do_nothing()
        await session.execute(stmt)
        await session.commit()

async def list_tenants():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Tenant))
        return res.scalars().all()

async def delete_tenant(tenant_id: str):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(ChunkEntry).where(ChunkEntry.tenant_id == tenant_id))
        await session.execute(delete(FileRecord).where(FileRecord.tenant_id == tenant_id))
        await session.execute(delete(Tenant).where(Tenant.tenant_id == tenant_id))
        await session.commit()

# file CRUD
async def create_file(tenant_id: str, file_id: str, metadata: dict):
    async with AsyncSessionLocal() as session:
        stmt = pg_insert(FileRecord).values(
            tenant_id=tenant_id, file_id=file_id, file_metadata=metadata
        ).on_conflict_do_nothing()
        await session.execute(stmt)
        await session.commit()

async def list_files(tenant_id: str):
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(FileRecord.file_id, FileRecord.file_metadata, FileRecord.created_at)
            .where(FileRecord.tenant_id == tenant_id)
        )
        return res.all()

async def delete_file(tenant_id: str, file_id: str):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(ChunkEntry).where(
            (ChunkEntry.tenant_id == tenant_id) & (ChunkEntry.file_id == file_id)
        ))
        res = await session.execute(delete(FileRecord).where(
            (FileRecord.tenant_id == tenant_id) & (FileRecord.file_id == file_id)
        ))
        await session.commit()
        return res.rowcount > 0

# chunk CRUD
async def upsert_chunks(tenant_id: str, file_id: str, chunks: list):
    async with AsyncSessionLocal() as session:
        stmt = pg_insert(ChunkEntry)
        vals = []
        for chunk in chunks:
            vals.append({
                'tenant_id': tenant_id,
                'file_id': file_id,
                'chunk_id': chunk.chunk_id,
                'embedding': chunk.embedding,
                'chunk_metadata': chunk.metadata.dict()
            })
        stmt = stmt.values(vals)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ChunkEntry.tenant_id, ChunkEntry.file_id, ChunkEntry.chunk_id],
            set_={
                'embedding': stmt.excluded.embedding,
                'chunk_metadata': stmt.excluded.chunk_metadata
            }
        )
        await session.execute(stmt)
        await session.commit()

async def delete_chunk(tenant_id: str, file_id: str, chunk_id: str):
    async with AsyncSessionLocal() as session:
        res = await session.execute(delete(ChunkEntry).where(
            (ChunkEntry.tenant_id == tenant_id) & 
            (ChunkEntry.file_id == file_id) & 
            (ChunkEntry.chunk_id == chunk_id)
        ))
        await session.commit()
        return res.rowcount > 0

async def query_chunks(tenant_id: str, embedding: list, top_k: int):
    async with AsyncSessionLocal() as session:
        q = (
            select(
                ChunkEntry.file_id,
                ChunkEntry.chunk_id,
                ChunkEntry.chunk_metadata,
                ChunkEntry.embedding.l2_distance(embedding).label("score")
            )
            .where(ChunkEntry.tenant_id == tenant_id)
            .order_by(text("score"))
            .limit(top_k)
        )
        res = await session.execute(q)
        return res.all()