import yfinance as yf
import json

try:
    ticker = yf.Ticker("VOO")
    if ticker.news:
        content = ticker.news[0]['content']
        print(json.dumps(content, indent=2))
    else:
        print("No news found.")
except Exception as e:
    print(f"Error: {e}")
