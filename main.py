#!/usr/bin/env python3
"""
Trends Researcher - Main Entry Point
"""
import os
import logging
from dotenv import load_dotenv
load_dotenv()

from masumi import run
from masumi.job_manager import InMemoryJobStorage
from agent import process_job

logger = logging.getLogger(__name__)

# Use PostgreSQL if DATABASE_URL is set, otherwise fall back to in-memory
def get_storage():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        try:
            from storage import PostgresJobStorage
            logger.info("Using PostgreSQL job storage")
            return PostgresJobStorage()
        except Exception as e:
            logger.warning(f"Failed to init PostgreSQL storage: {e} — falling back to in-memory")
    else:
        logger.warning("DATABASE_URL not set — using in-memory storage (jobs lost on restart)")
    return InMemoryJobStorage()

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
            "type": "option",
            "name": "Geo",
            "description": "Filter by country. Leave empty (select none) for worldwide results.",
            "data": {
                "values": [
                    "Worldwide",
                    "US - United States",
                    "GB - United Kingdom",
                    "CA - Canada",
                    "AU - Australia",
                    "DE - Germany",
                    "FR - France",
                    "JP - Japan",
                    "IN - India",
                    "BR - Brazil",
                    "MX - Mexico",
                    "ES - Spain",
                    "IT - Italy",
                    "NL - Netherlands",
                    "SE - Sweden",
                    "NO - Norway",
                    "DK - Denmark",
                    "FI - Finland",
                    "PL - Poland",
                    "CH - Switzerland",
                    "AT - Austria",
                    "BE - Belgium",
                    "PT - Portugal",
                    "CZ - Czech Republic",
                    "HU - Hungary",
                    "RO - Romania",
                    "UA - Ukraine",
                    "TR - Turkey",
                    "SA - Saudi Arabia",
                    "AE - United Arab Emirates",
                    "IL - Israel",
                    "ZA - South Africa",
                    "NG - Nigeria",
                    "EG - Egypt",
                    "KR - South Korea",
                    "CN - China",
                    "SG - Singapore",
                    "ID - Indonesia",
                    "TH - Thailand",
                    "PH - Philippines",
                    "MY - Malaysia",
                    "VN - Vietnam",
                    "PK - Pakistan",
                    "BD - Bangladesh",
                    "AR - Argentina",
                    "CO - Colombia",
                    "CL - Chile",
                    "PE - Peru",
                    "NZ - New Zealand",
                    "RU - Russia"
                ],
                "default": "Worldwide"
            },
            "validations": [
                {"validation": "optional", "value": "true"},
                {"validation": "max", "value": "1"}
            ]
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
        input_schema_handler=INPUT_SCHEMA,
        job_storage=get_storage()
    )
