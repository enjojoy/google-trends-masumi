#!/usr/bin/env python3
"""
Trends Researcher - Main Entry Point

Run with: masumi run main.py
"""
from dotenv import load_dotenv
load_dotenv()

from masumi import run
from agent import process_job

INPUT_SCHEMA = {
    "input_data": [
        {
            "id": "request",
            "type": "string",
            "name": "Research Request",
            "data": {
                "description": "Natural language marketing research request (e.g. 'Compare interest in oat milk vs almond milk in the US over the last 12 months')"
            }
        },
        {
            "id": "geo",
            "type": "string",
            "name": "Geo",
            "data": {
                "description": "Country code (e.g. US, GB, DE). Leave empty for worldwide.",
                "optional": True
            }
        },
        {
            "id": "timeframe",
            "type": "string",
            "name": "Timeframe",
            "data": {
                "description": "Time range e.g. 'today 12-m', 'today 3-m'. Default: today 12-m",
                "optional": True
            }
        }
    ]
}

if __name__ == "__main__":
    run(
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA
    )
