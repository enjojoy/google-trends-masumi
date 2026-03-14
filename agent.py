import os
import json
import asyncio
from dotenv import load_dotenv
from pytrends.request import TrendReq
from openai import AsyncOpenAI
from masumi.agent import MasumiAgent

load_dotenv()

openai_client = AsyncOpenAI()

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "request": {
            "type": "string",
            "description": "Natural language marketing research request (e.g. 'Compare interest in oat milk vs almond milk in the US over the last 12 months')"
        },
        "geo": {
            "type": "string",
            "description": "Country code to focus on (e.g. 'US', 'GB', 'DE'). Leave empty for worldwide."
        },
        "timeframe": {
            "type": "string",
            "description": "Time range (e.g. 'today 12-m', 'today 3-m', '2023-01-01 2024-01-01'). Default: today 12-m"
        }
    },
    "required": ["request"]
}

PARSE_PROMPT = """You are a Google Trends query planner for marketing research.

Given a research request, extract:
1. keywords: list of 1-5 search terms to compare (Google Trends supports max 5)
2. geo: country code if mentioned (e.g. "US", "GB") or "" for worldwide
3. timeframe: one of "today 12-m", "today 3-m", "today 5-y", or a date range like "2023-01-01 2024-01-01"
4. focus: what the researcher wants to know (trend direction, comparison, seasonality, related topics)

Respond with JSON only, no explanation.

Request: {request}
"""

async def process_job(job_id: str, input_data: dict) -> str:
    request = input_data.get("request", "")
    geo_override = input_data.get("geo", "")
    timeframe_override = input_data.get("timeframe", "")

    # Step 1: Use LLM to parse the research request into structured queries
    parse_resp = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": PARSE_PROMPT.format(request=request)
        }]
    )

    parsed = json.loads(parse_resp.choices[0].message.content)
    keywords = parsed.get("keywords", [request])[:5]
    geo = geo_override or parsed.get("geo", "")
    timeframe = timeframe_override or parsed.get("timeframe", "today 12-m")
    focus = parsed.get("focus", "general trends")

    # Step 2: Fetch from Google Trends (sync in executor to avoid blocking)
    loop = asyncio.get_event_loop()
    trends_data = await loop.run_in_executor(None, lambda: fetch_trends(keywords, geo, timeframe))

    # Step 3: Use LLM to write a marketing research summary
    data_payload = json.dumps({
        "keywords": keywords,
        "geo": geo or "worldwide",
        "timeframe": timeframe,
        **trends_data
    }, indent=2)

    summary_resp = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": f"""You are a marketing research analyst. Write a clear, actionable research report based on this Google Trends data.

Research focus: {focus}
Original request: {request}

Data:
{data_payload}

Write a structured report with:
- **Key Findings** (2-3 bullet points)
- **Trend Analysis** (what's rising, declining, seasonal)
- **Competitive Insights** (if multiple keywords)
- **Recommended Actions** (2-3 concrete marketing suggestions)

Be specific and data-driven. Reference actual numbers from the data."""
        }]
    )

    return summary_resp.choices[0].message.content


def fetch_trends(keywords: list, geo: str, timeframe: str) -> dict:
    pytrends = TrendReq(hl="en-US", tz=0)
    pytrends.build_payload(keywords, geo=geo, timeframe=timeframe)

    result = {}

    # Interest over time
    try:
        iot = pytrends.interest_over_time()
        iot_summary = {}
        if not iot.empty:
            for kw in keywords:
                if kw in iot.columns:
                    series = iot[kw]
                    iot_summary[kw] = {
                        "avg": round(float(series.mean()), 1),
                        "peak": int(series.max()),
                        "peak_date": series.idxmax().strftime("%Y-%m-%d"),
                        "latest": int(series.iloc[-1]),
                        "trend": "rising" if series.iloc[-1] > series.mean() else "declining"
                    }
        result["interest_over_time"] = iot_summary
    except Exception as e:
        result["interest_over_time"] = {"error": str(e)}

    # Related queries
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

    # Related topics
    try:
        rt = pytrends.related_topics()
        topics = {}
        for kw in keywords:
            if kw in rt and rt[kw]:
                top = rt[kw].get("top")
                if top is not None:
                    topics[kw] = top["topic_title"].head(5).tolist()
        result["related_topics"] = topics
    except Exception:
        result["related_topics"] = {}

    return result


if __name__ == "__main__":
    agent = MasumiAgent(
        process_job=process_job,
        input_schema=INPUT_SCHEMA,
        name="Trends Researcher",
        description="Marketing research powered by Google Trends. Describe what you want to research in plain English — get a structured trend analysis with actionable insights.",
        version="1.0.0",
        pricing_usdm=1_000_000  # 1.00 USDM per job
    )
    agent.run()
