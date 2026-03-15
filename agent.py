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

    GEO_OPTIONS = [
        "Worldwide", "US - United States", "GB - United Kingdom", "CA - Canada",
        "AU - Australia", "DE - Germany", "FR - France", "JP - Japan", "IN - India",
        "BR - Brazil", "MX - Mexico", "ES - Spain", "IT - Italy", "NL - Netherlands",
        "SE - Sweden", "NO - Norway", "DK - Denmark", "FI - Finland", "PL - Poland",
        "CH - Switzerland", "AT - Austria", "BE - Belgium", "PT - Portugal",
        "CZ - Czech Republic", "HU - Hungary", "RO - Romania", "UA - Ukraine",
        "TR - Turkey", "SA - Saudi Arabia", "AE - United Arab Emirates", "IL - Israel",
        "ZA - South Africa", "NG - Nigeria", "EG - Egypt", "KR - South Korea",
        "CN - China", "SG - Singapore", "ID - Indonesia", "TH - Thailand",
        "PH - Philippines", "MY - Malaysia", "VN - Vietnam", "PK - Pakistan",
        "BD - Bangladesh", "AR - Argentina", "CO - Colombia", "CL - Chile",
        "PE - Peru", "NZ - New Zealand", "RU - Russia"
    ]
    # option type may return list or int index — normalize to string value
    geo_override = input_data.get("geo", "")
    if isinstance(geo_override, list):
        raw = geo_override[0] if geo_override else ""
        if isinstance(raw, int) and raw < len(GEO_OPTIONS):
            geo_override = GEO_OPTIONS[raw]
        else:
            geo_override = str(raw) if raw else ""
    elif isinstance(geo_override, int):
        geo_override = GEO_OPTIONS[geo_override] if geo_override < len(GEO_OPTIONS) else ""
    else:
        geo_override = str(geo_override) if geo_override else ""
    # Extract 2-letter code (e.g. "US - United States" → "US", "Worldwide" → "")
    if geo_override and geo_override != "Worldwide":
        geo_override = geo_override.split(" - ")[0].strip()
    elif geo_override == "Worldwide":
        geo_override = ""

    TIMEFRAME_OPTIONS = [
        "today 1-m (Last 1 month)",
        "today 3-m (Last 3 months)",
        "today 12-m (Last 12 months)",
        "today 5-y (Last 5 years)",
        "all (Since 2004)"
    ]
    timeframe_override = input_data.get("timeframe", "")
    if isinstance(timeframe_override, list):
        raw = timeframe_override[0] if timeframe_override else ""
        # masumi may pass index (int) instead of value string
        if isinstance(raw, int) and raw < len(TIMEFRAME_OPTIONS):
            timeframe_override = TIMEFRAME_OPTIONS[raw]
        else:
            timeframe_override = str(raw) if raw else ""
    elif isinstance(timeframe_override, int):
        timeframe_override = TIMEFRAME_OPTIONS[timeframe_override] if timeframe_override < len(TIMEFRAME_OPTIONS) else ""
    else:
        timeframe_override = str(timeframe_override) if timeframe_override else ""
    # Strip label suffix (e.g. "today 12-m (Last 12 months)" → "today 12-m")
    if timeframe_override and "(" in timeframe_override:
        timeframe_override = timeframe_override.split("(")[0].strip()

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

    report = summary_resp.choices[0].message.content

    # Append raw data table
    raw_section = format_raw_data(keywords, geo, timeframe, trends_data)

    return f"{report}\n\n{raw_section}"


def format_raw_data(keywords: list, geo: str, timeframe: str, trends_data: dict) -> str:
    """Format raw pytrends data as markdown tables."""
    lines = []
    lines.append("---")
    lines.append("## 📊 Raw Google Trends Data")
    lines.append(f"**Source:** Google Trends | **Keywords:** {', '.join(keywords)} | **Geo:** {geo or 'Worldwide'} | **Timeframe:** {timeframe}")
    lines.append("")

    # Interest over time summary table
    iot = trends_data.get("interest_over_time", {})
    if iot and "error" not in iot:
        lines.append("### Interest Over Time (0–100 index)")
        lines.append("| Keyword | Avg | Peak | Peak Date | Latest | Trend |")
        lines.append("|---------|-----|------|-----------|--------|-------|")
        for kw, stats in iot.items():
            trend_emoji = "📈" if stats["trend"] == "rising" else "📉"
            lines.append(f"| {kw} | {stats['avg']} | {stats['peak']} | {stats['peak_date']} | {stats['latest']} | {trend_emoji} {stats['trend']} |")
        lines.append("")

    # Related queries table
    related = trends_data.get("related_queries", {})
    if related:
        lines.append("### Related Queries")
        for kw, queries in related.items():
            lines.append(f"**{kw}**")
            top = queries.get("top", [])
            rising = queries.get("rising", [])
            if top or rising:
                lines.append("| Top Queries | Rising Queries |")
                lines.append("|-------------|----------------|")
                max_len = max(len(top), len(rising))
                for i in range(max_len):
                    t = top[i] if i < len(top) else ""
                    r = rising[i] if i < len(rising) else ""
                    lines.append(f"| {t} | {r} |")
            lines.append("")

    return "\n".join(lines)


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
