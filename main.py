#!/usr/bin/env python3
"""
Trends Researcher - Main Entry Point
"""
import os
from dotenv import load_dotenv
load_dotenv()

from masumi import create_masumi_app, Config
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from agent import process_job

INPUT_SCHEMA = {
    "input_data": [
        {
            "id": "request",
            "type": "string",
            "name": "Research Request",
            "validations": [],
            "data": {
                "description": "Natural language marketing research request (e.g. 'Compare interest in oat milk vs almond milk in the US over the last 12 months')"
            }
        },
        {
            "id": "geo",
            "type": "string",
            "name": "Geo",
            "validations": [{"validation": "optional", "value": "true"}],
            "data": {
                "description": "Country code (e.g. US, GB, DE). Leave empty for worldwide."
            }
        },
        {
            "id": "timeframe",
            "type": "string",
            "name": "Timeframe",
            "validations": [{"validation": "optional", "value": "true"}],
            "data": {
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
