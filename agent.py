#!/usr/bin/env python3
"""
Trends Researcher - Agent Logic

Implement process_job with your agent's business logic.
"""
import json
import asyncio
import logging
from pytrends.request import TrendReq
from openai import AsyncOpenAI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

openai_client = AsyncOpenAI()

PARSE_PROMPT = """You are a Google Trends query planner for marketing research.

Given a research request, extract:
1. keywords: list of 1-5 search terms to compare (Google Trends supports max 5)
2. geo: country code if mentioned (e.g. "US", "GB") or "" for worldwide
3. timeframe: one of "today 12-m", "today 3-m", "today 5-y", or a date range like "2023-01-01 2024-01-01"
4. focus: what the researcher wants to know

Respond with JSON only, no explanation.

Request: {request}
"""


async def process_job(identifier_from_purchaser: str, input_data: dict):
    """
    Process a Google Trends research request.

    Args:
        identifier_from_purchaser: Unique ID from the purchaser
        input_data: Must contain 'request' key with a natural language research question

    Returns:
        Structured marketing research report as a string
    """
    request = input_data.get("request", "")
    geo_override = input_data.get("geo", "")
    timeframe_override = input_data.get("timeframe", "")

    # Step 1: Parse the research request
    parse_resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": PARSE_PROMPT.format(request=request)}]
    )

    parsed = json.loads(parse_resp.choices[0].message.content)
    keywords = parsed.get("keywords", [request])[:5]
    geo = geo_override or parsed.get("geo", "")
    timeframe = timeframe_override or parsed.get("timeframe", "today 12-m")
    focus = parsed.get("focus", "general trends")

    logger.info(f"Fetching trends: keywords={keywords} geo={geo} timeframe={timeframe}")

    # Step 2: Fetch from Google Trends (sync → executor)
    loop = asyncio.get_event_loop()
    trends_data = await loop.run_in_executor(None, lambda: fetch_trends(keywords, geo, timeframe))

    # Step 3: Generate report
    data_payload = json.dumps({"keywords": keywords, "geo": geo or "worldwide", "timeframe": timeframe, **trends_data}, indent=2)

    summary_resp = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"""You are a marketing research analyst. Write a clear, actionable report based on this Google Trends data.

Research focus: {focus}
Original request: {request}

Data:
{data_payload}

Write a structured report with:
- **Key Findings** (2-3 bullet points)
- **Trend Analysis** (rising, declining, seasonal)
- **Competitive Insights** (if multiple keywords)
- **Recommended Actions** (2-3 concrete marketing suggestions)

Be specific and data-driven."""}]
    )

    return summary_resp.choices[0].message.content


def fetch_trends(keywords: list, geo: str, timeframe: str) -> dict:
    pytrends = TrendReq(hl="en-US", tz=0)
    pytrends.build_payload(keywords, geo=geo, timeframe=timeframe)
    result = {}

    try:
        iot = pytrends.interest_over_time()
        summary = {}
        if not iot.empty:
            for kw in keywords:
                if kw in iot.columns:
                    s = iot[kw]
                    summary[kw] = {
                        "avg": round(float(s.mean()), 1),
                        "peak": int(s.max()),
                        "peak_date": s.idxmax().strftime("%Y-%m-%d"),
                        "latest": int(s.iloc[-1]),
                        "trend": "rising" if s.iloc[-1] > s.mean() else "declining"
                    }
        result["interest_over_time"] = summary
    except Exception as e:
        result["interest_over_time"] = {"error": str(e)}

    try:
        rq = pytrends.related_queries()
        related = {}
        for kw in keywords:
            if kw in rq and rq[kw]:
                top = rq[kw].get("top")
                rising = rq[kw].get("rising")
                related[kw] = {
                    "top": top["query"].head(5).tolist() if top is not None else [],
                    "rising": rising["query"].head(5).tolist() if rising is not None else []
                }
        result["related_queries"] = related
    except Exception:
        result["related_queries"] = {}

    return result
