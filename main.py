#!/usr/bin/env python3
"""
Trends Researcher - Main Entry Point
"""
import os
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
            "description": "Natural language marketing research request (e.g. 'Compare interest in oat milk vs almond milk in the US over the last 12 months')"
        },
        {
            "id": "geo",
            "type": "string",
            "name": "Geo (optional)",
            "description": "Country code (e.g. US, GB, DE). Leave empty for worldwide."
        },
        {
            "id": "timeframe",
            "type": "string",
            "name": "Timeframe (optional)",
            "description": "Time range e.g. 'today 12-m', 'today 3-m'. Default: today 12-m."
        }
    ]
}

if __name__ == "__main__":
    run(
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA
    )
