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
            "name": "Geo",
            "description": "2-letter country code to filter by region (e.g. US, GB, DE, FR, JP). Leave empty for worldwide results.",
            "validations": [{"validation": "optional", "value": "true"}]
        },
        {
            "id": "timeframe",
            "type": "option",
            "name": "Timeframe",
            "description": "Time range for the trends data. Default: Last 12 months.",
            "data": {
                "values": [
                    "today 1-m (Last 1 month)",
                    "today 3-m (Last 3 months)",
                    "today 12-m (Last 12 months)",
                    "today 5-y (Last 5 years)",
                    "all (Since 2004)"
                ],
                "default": "today 12-m (Last 12 months)"
            },
            "validations": [
                {"validation": "optional", "value": "true"},
                {"validation": "max", "value": "1"}
            ]
        }
    ]
}

if __name__ == "__main__":
    run(
        start_job_handler=process_job,
        input_schema_handler=INPUT_SCHEMA
    )
