import yfinance as yf

try:
    ticker = yf.Ticker("VOO")
    info = ticker.info
    print("--- PRICE KEYS ---")
    print(f"currentPrice: {info.get('currentPrice')}")
    print(f"regularMarketPrice: {info.get('regularMarketPrice')}")
    print(f"previousClose: {info.get('previousClose')}")
    print(f"navPrice: {info.get('navPrice')}")
except Exception as e:
    print(f"Error: {e}")
