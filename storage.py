"""
PostgreSQL job storage backend for Masumi agents.
Implements the JobStorage interface from masumi.job_manager.

Requires: asyncpg, DATABASE_URL env var
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from masumi.job_manager import JobStorage

logger = logging.getLogger(__name__)


class PostgresJobStorage(JobStorage):
    """PostgreSQL-backed job storage for persistent state across restarts."""

    def __init__(self):
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            import asyncpg
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                raise RuntimeError("DATABASE_URL environment variable is required")
            self._pool = await asyncpg.create_pool(database_url)
            await self._ensure_table()
        return self._pool

    async def _ensure_table(self):
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS masumi_jobs (
                    job_id TEXT PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS masumi_jobs_status_idx
                ON masumi_jobs ((data->>'status'))
            """)
        logger.info("PostgreSQL job storage table ready")

    async def create_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO masumi_jobs (job_id, data) VALUES ($1, $2::jsonb)",
                job_id, json.dumps(job_data)
            )

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT data FROM masumi_jobs WHERE job_id = $1", job_id
            )
        return json.loads(row["data"]) if row else None

    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE masumi_jobs
                SET data = data || $2::jsonb, updated_at = NOW()
                WHERE job_id = $1
            """, job_id, json.dumps(updates))

    async def delete_job(self, job_id: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM masumi_jobs WHERE job_id = $1", job_id
            )

    async def list_jobs(self, status: Optional[str] = None) -> list:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    "SELECT data FROM masumi_jobs WHERE data->>'status' = $1", status
                )
            else:
                rows = await conn.fetch("SELECT data FROM masumi_jobs")
        return [json.loads(row["data"]) for row in rows]
