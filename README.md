# Trends Researcher 📈

A Masumi Network agent that answers marketing research questions using Google Trends data + GPT-4o analysis.

Give it a plain-English research request — get back a structured report with key findings, trend analysis, competitive insights, and recommended actions.

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/enjojoy/google-trends-masumi)

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PAYMENT_SERVICE_URL` | Your Masumi Payment Service URL |
| `PAYMENT_API_KEY` | Payment Service API key |
| `SELLER_VKEY` | Your Cardano wallet verification key |
| `AGENT_IDENTIFIER` | Set after registration on Masumi |
| `NETWORK` | `Preprod` or `Mainnet` (default: Preprod) |
| `OPENAI_API_KEY` | Your OpenAI API key |

## Usage

Input schema:
```json
{
  "request": "Compare interest in oat milk vs almond milk in the US over the last 12 months",
  "geo": "US",
  "timeframe": "today 12-m"
}
```

Only `request` is required — geo and timeframe are auto-detected from the request.

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your .env
python agent.py
# → agent live at http://localhost:8000
```

## Registering on Masumi

Once deployed:
1. Get your public URL from Railway
2. Register via the [Masumi Payment Service admin UI](http://localhost:3001/admin) or use MasumiForge in OpenClaw
3. Add `AGENT_IDENTIFIER` to your Railway env vars
4. Your agent appears on [Sokosumi](https://sokosumi.com) 🎉

## Pricing

**1.00 USDM** per research job (configurable in `agent.py`)

## Part of MasumiForge

Built with [MasumiForge](https://github.com/enjojoy/masumiforge) — forge Masumi agents with OpenClaw.
