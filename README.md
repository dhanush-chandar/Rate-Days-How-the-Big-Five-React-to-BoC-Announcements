# Rate Days: How the Big Five React to BoC Announcements

An interactive dashboard analyzing whether Bank of Canada interest rate announcements cause measurably larger price movements in Canada's Big Five bank stocks compared to normal trading days.

**Live dashboard:** https://rate-days-how-the-big-five-react-to-boc.onrender.com/

## What this looks at

- Daily price volatility on Bank of Canada announcement days vs. normal trading days, across RBC, TD, BMO, Scotiabank, and CIBC
- Which bank reacts most (and least) to rate announcements
- How closely the five banks move together (correlation)
- Full price history for each bank, with announcement dates marked

## Key finding

Contrary to the assumption that all bank stocks would react similarly to rate announcements, **only TD Bank shows a meaningfully larger price move on announcement days** (+0.26% average). The other four banks show little change, and two (CIBC, Scotiabank) are actually *less* volatile on announcement days than on normal ones.

## Data

- **Stock prices:** pulled via [yfinance](https://pypi.org/project/yfinance/) (Yahoo Finance), Jan 2025–Aug 2026
- **Rate announcement dates:** Bank of Canada's public schedule, 13 announcements covered

## Stack

- Python, pandas
- Plotly for visualizations
- Dash for the web app
- Deployed on Render

## Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:8050` in your browser.

## Disclaimer

Built as a personal portfolio project for educational and demonstrative purposes. Not financial advice.

---
Built by [Dhanush Chandar Sivakumar](https://www.linkedin.com/in/dhanushchandarsivakumar)
