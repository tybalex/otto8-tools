import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@db:5432/postgres"
)

async def get_conn():
    return await asyncpg.connect(DATABASE_URL)

async def init_master_table():
    conn = await get_conn()
    # Track users
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS rag_users (
        user_id TEXT PRIMARY KEY
    );
    """)
    conn.close()

async def create_user(user_id: str):
    table = f"idx_{user_id}"
    conn = await get_conn()
    # Create per-user table
    await conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {table} (
        file_id TEXT,
        embedding VECTOR,
        metadata JSONB,
        PRIMARY KEY (file_id)
    );
    """)
    # Register in rag_users
    await conn.execute(
        "INSERT INTO rag_users(user_id) VALUES($1) ON CONFLICT DO NOTHING;",
        user_id
    )
    conn.close()

async def list_users():
    conn = await get_conn()
    rows = await conn.fetch("SELECT user_id FROM rag_users;")
    conn.close()
    return [r['user_id'] for r in rows]

async def delete_user(user_id: str):
    table = f"idx_{user_id}"
    conn = await get_conn()
    await conn.execute(f"DROP TABLE IF EXISTS {table};")
    await conn.execute(
        "DELETE FROM rag_users WHERE user_id = $1;",
        user_id
    )
    conn.close()

async def upsert_file(user_id: str, file_id: str, embedding: list, metadata: dict):
    table = f"idx_{user_id}"
    conn = await get_conn()
    await conn.execute(f"""
    INSERT INTO {table}(file_id, embedding, metadata)
    VALUES($1, $2::vector, $3)
    ON CONFLICT (file_id) DO UPDATE
      SET embedding = EXCLUDED.embedding,
          metadata  = EXCLUDED.metadata;
    """, file_id, embedding, metadata)
    conn.close()

async def delete_file(user_id: str, file_id: str) -> bool:
    table = f"idx_{user_id}"
    conn = await get_conn()
    result = await conn.execute(
        f"DELETE FROM {table} WHERE file_id = $1;", file_id
    )
    conn.close()
    return not result.endswith("0")

async def query_user(user_id: str, embedding: list, top_k: int):
    table = f"idx_{user_id}"
    conn = await get_conn()
    rows = await conn.fetch(f"""
      SELECT file_id, metadata, embedding <-> $1::vector AS score
      FROM {table}
      ORDER BY embedding <-> $1::vector
      LIMIT $2;
    """, embedding, top_k)
    conn.close()
    return rows