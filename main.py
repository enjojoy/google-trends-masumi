#!/usr/bin/env python3
"""
Trends Researcher - Main Entry Point
"""
import os
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

from masumi import create_masumi_app, Config
from masumi.job_manager import InMemoryJobStorage
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from agent import process_job

# Use PostgreSQL if DATABASE_URL is set, otherwise fall back to in-memory
try:
    if os.environ.get("DATABASE_URL"):
        from storage import PostgresJobStorage
        job_storage = PostgresJobStorage()
        logger.info("Using PostgreSQL job storage")
    else:
        job_storage = InMemoryJobStorage()
        logger.warning("DATABASE_URL not set — using in-memory storage (jobs lost on restart)")
except Exception as e:
    logger.warning(f"Failed to init PostgreSQL storage: {e} — falling back to in-memory")
    job_storage = InMemoryJobStorage()

INPUT_SCHEMA = {
    "input_data": [
        {
            "id": "request",
            "type": "text",
            "name": "Research Request",
            "validations": [],
            "data": {
                "placeholder": "e.g. Compare interest in oat milk vs almond milk in the US over the last 12 months",
                "description": "Natural language marketing research request"
            }
        },
        {
            "id": "geo",
            "type": "text",
            "name": "Geo",
            "validations": [{"validation": "optional", "value": "true"}],
            "data": {
                "placeholder": "US",
                "description": "Country code (e.g. US, GB, DE). Leave empty for worldwide."
            }
        },
        {
            "id": "timeframe",
            "type": "text",
            "name": "Timeframe",
            "validations": [{"validation": "optional", "value": "true"}],
            "data": {
                "placeholder": "today 12-m",
                "description": "Time range e.g. 'today 12-m', 'today 3-m'. Default: today 12-m."
            }
        }
    ]
}

config = Config(
    payment_service_url=os.environ.get("PAYMENT_SERVICE_URL", ""),
    payment_api_key=os.environ.get("PAYMENT_API_KEY", ""),
)

app = create_masumi_app(
    config=config,
    agent_identifier=os.environ.get("AGENT_IDENTIFIER"),
    network=os.environ.get("NETWORK", "Preprod"),
    seller_vkey=os.environ.get("SELLER_VKEY"),
    start_job_handler=process_job,
    input_schema_handler=INPUT_SCHEMA,
    job_storage=job_storage,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
