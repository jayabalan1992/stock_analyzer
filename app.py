import streamlit as st
import yfinance as yf
import pandas as pd
import time
from google import genai
from google.genai import types

# --- Configuration ---
st.set_page_config(page_title="Stock AI Analyst", layout="wide")

# --- Sidebar: User Inputs ---
with st.sidebar:
    st.header("Settings")
    ticker_input = st.text_input("Enter Stock Ticker", value="NVDA").upper()
    
    # Check if ticker changed to reset chat
    if "last_ticker" not in st.session_state:
        st.session_state.last_ticker = ticker_input
        
    if ticker_input != st.session_state.last_ticker:
        st.session_state.messages = []
        st.session_state.last_ticker = ticker_input
    
    api_key = st.text_input("Google Gemini API Key", type="password")
    st.caption("🔒 *Your API key is processed in-memory and never stored. It is cleared when you close the tab.*")
    
    if st.button("Analyze Stock"):
        st.session_state.analyze_clicked = True
    
    st.markdown("---")
    st.markdown("### How to use")
    st.markdown("1. Enter a valid Ticker (e.g., NVDA, AAPL).")
    st.markdown("2. Enter your Gemini API Key.")
    st.markdown("3. Click 'Analyze Stock'.")

# --- Backend: Data Fetching & 14-Step Logic ---
@st.cache_data
def get_stock_data(ticker):
    """
    Fetches comprehensive data for 14-step framework.
    Returns structured data with score and analysis details.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        news = stock.news[:5] if stock.news else []
        
        # Helper for safe safe access
        def get(key, default=None):
            return info.get(key, default)

        # --- 1. Data Collection ---
        
        # Price Data
        current_price = get('currentPrice') or get('regularMarketPrice') or get('previousClose')
        target_price = get('targetMeanPrice')
        
        # Growth (Step 3 & 5)
        rev_growth = get('revenueGrowth')
        earnings_growth = get('earningsGrowth')
        
        # Profitability (Step 4)
        gross_margin = get('grossMargins')
        op_margin = get('operatingMargins')
        net_margin = get('profitMargins')
        
        # Returns (Step 9)
        roe = get('returnOnEquity')
        roa = get('returnOnAssets')
        
        # Balance Sheet (Step 8)
        total_cash = get('totalCash')
        total_debt = get('totalDebt')
        debt_to_equity = get('debtToEquity') # Note: yfinance often returns this as %, e.g., 85.0 for 0.85
        current_ratio = get('currentRatio')
        
        # Cash Flow (Step 7)
        free_cashflow = get('freeCashflow')
        op_cashflow = get('operatingCashflow')
        
        # Valuation (Step 10)
        pe = get('trailingPE')
        fwd_pe = get('forwardPE')
        peg = get('trailingPegRatio') or get('pegRatio')
        p_s = get('priceToSalesTrailing12Months')
        
        # Analyst (Step 11)
        rec_key = get('recommendationKey', 'none')
        
        # --- 2. Scoring Engine (0-100) ---
        score = 0
        max_score = 0
        breakdown = []
        
        def check(condition, points, message_pass, message_fail, critical=False):
            nonlocal score, max_score
            max_score += points
            if condition:
                score += points
                breakdown.append(f"✅ {message_pass} (+{points})")
            else:
                if critical: breakdown.append(f"❌ {message_fail}")
                else: breakdown.append(f"⚠️ {message_fail}")

        # -- Growth (20 pts) --
        # Revenue Growth > 10%
        if rev_growth is not None:
            check(rev_growth > 0.10, 10, f"Revenue Growth Strong ({rev_growth:.1%})", f"Revenue Growth Weak ({rev_growth:.1%})")
        else:
            breakdown.append("⚪ Revenue Growth N/A")
            
        # Earnings Growth > 5%
        if earnings_growth is not None:
             check(earnings_growth > 0.05, 10, f"Earnings Growth Strong ({earnings_growth:.1%})", f"Earnings Growth Weak ({earnings_growth:.1%})")
        
        # -- Profitability (20 pts) -- 
        # Margins vary by industry, but positive is baseline
        if net_margin is not None:
             check(net_margin > 0.10, 10, f"Healthy Profit Margin ({net_margin:.1%})", f"Low/Negative Profit Margin ({net_margin:.1%})", critical=True)
        if op_margin is not None:
             check(op_margin > 0.10, 10, f"Strong Operating Margin ({op_margin:.1%})", f"Weak Operating Margin ({op_margin:.1%})")

        # -- Health (20 pts) --
        # Debt/Equity < 1.0 (or 100 in yf terms usually, but checking standard ratio)
        # Note: yfinance often returns DebtToEquity as a whole number percentage (e.g., 150 = 1.5)
        # We will assume if > 5 it's %, if < 5 it's ratio. Safe check > 200 is high debt.
        if debt_to_equity is not None:
            # Normalize: if it's 55, treat as 0.55. If it's 0.55 treat as 0.55.
            # Actually yf usually returns 50 for 0.5. Let's assume threshold of 100 (1.0)
            check(debt_to_equity < 100, 10, f"Conservative Debt Levels ({debt_to_equity}%)", f"High Debt Levels ({debt_to_equity}%)")
        
        if current_ratio is not None:
            check(current_ratio > 1.5, 10, f"Strong Liquidity (Ratio: {current_ratio:.2f})", f"Low Liquidity (Ratio: {current_ratio:.2f})")

        # -- Efficiency (10 pts) --
        if roe is not None:
            check(roe > 0.15, 10, f"High Return on Equity ({roe:.1%})", f"Low ROE ({roe:.1%})")

        # -- Cash Flow (10 pts) --
        # FCF > 0 is arguably the most important
        if free_cashflow is not None:
            check(free_cashflow > 0, 10, "Positive Free Cash Flow", "Negative Free Cash Flow", critical=True)

        # -- Valuation (10 pts) --
        # PEG < 1.5 is reasonable GARP
        if peg is not None:
            check(peg < 1.5, 10, f"Attractively Valued (PEG: {peg})", f"Rich Valuation (PEG: {peg})")
        elif pe is not None:
            # Fallback to PE if PEG missing
            check(pe < 25, 10, f"Reasonable P/E ({pe:.1f})", f"High P/E ({pe:.1f})")

        # -- Analyst/Opinion (10 pts) --
        if target_price and current_price:
            upside = (target_price - current_price) / current_price
            check(upside > 0.10, 10, f"Analyst Upside > 10% (Target: ${target_price})", f"Limited Analyst Upside (Target: ${target_price})")
            
        # Normalize Score to 100
        final_score = int((score / max_score) * 100) if max_score > 0 else 0
        
        if final_score >= 80: verdict = "Strong Buy"
        elif final_score >= 60: verdict = "Buy"
        elif final_score >= 40: verdict = "Hold"
        else: verdict = "Sell"

        return {
            "symbol": ticker,
            "name": get('shortName', ticker),
            "price": current_price,
            "target_price": target_price,
            "summary": get('longBusinessSummary') or get('description', 'No summary.'),
            "score": final_score,
            "verdict": verdict,
            "breakdown": breakdown,
            "metrics": {
                "Growth": {
                    "Revenue Growth": f"{rev_growth:.1%}" if rev_growth else "N/A",
                    "Earnings Growth": f"{earnings_growth:.1%}" if earnings_growth else "N/A"
                },
                "Profitability": {
                    "Gross Margin": f"{gross_margin:.1%}" if gross_margin else "N/A",
                    "Operating Margin": f"{op_margin:.1%}" if op_margin else "N/A",
                    "Net Margin": f"{net_margin:.1%}" if net_margin else "N/A"
                },
                "Health": {
                    "Debt/Equity": f"{debt_to_equity}%" if debt_to_equity else "N/A",
                    "Current Ratio": current_ratio,
                    "Total Cash": f"${total_cash/1e9:.1f}B" if total_cash else "N/A",
                    "Total Debt": f"${total_debt/1e9:.1f}B" if total_debt else "N/A"
                },
                "Valuation": {
                    "P/E": f"{pe:.1f}" if pe else "N/A",
                    "PEG": peg,
                    "P/S": f"{p_s:.1f}" if p_s else "N/A"
                },
                "Cash Flow": {
                    "Free Cash Flow": f"${free_cashflow/1e9:.1f}B" if free_cashflow else "N/A",
                    "Operating Cash Flow": f"${op_cashflow/1e9:.1f}B" if op_cashflow else "N/A"
                }  
            },
            "news": news
        }
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# --- Main App Logic ---

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.get('analyze_clicked') and api_key:
    # Fetch Data
    with st.spinner(f"Running 14-Step Analysis on {ticker_input}..."):
        data = get_stock_data(ticker_input)

    if data:
        # --- UI HEADER ---
        st.title(f"{data['name']} ({data['symbol']})")
        
        # Primary Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
             st.metric("Current Price", f"${data['price']}", delta=None)
        with col2:
             t_price = data['target_price'] if data['target_price'] else "N/A"
             delta_val = None
             if t_price != "N/A" and data['price']:
                 delta_val = f"{((t_price - data['price']) / data['price']):.1%}"
             st.metric("Analyst Target", f"${t_price}", delta=delta_val, delta_color="normal", help="The average price target set by Wall Street analysts for the next 12 months.")
        with col3:
             st.metric("AI Score", f"{data['score']}/100", delta=data['verdict'], help="Our custom score (0-100) based on Growth, Profitability, Health, and Valuation metrics. >80 is Strong Buy.")
        
        st.markdown("---")

        # --- TABS LAYOUT ---
        tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Analysis", "News", "AI Chat"])
        
        metrics = data['metrics']

        # TAB 1: DASHBOARD
        with tab1:
            st.subheader("Valuation & Growth")
            v_col1, v_col2, v_col3, v_col4 = st.columns(4)
            with v_col1:
                st.metric("P/E Ratio", metrics['Valuation']['P/E'], help="Price-to-Earnings Ratio. Measures current share price relative to per-share earnings. Lower is 'cheaper'.")
            with v_col2:
                st.metric("PEG Ratio", metrics['Valuation']['PEG'], help="Price/Earnings-to-Growth. Determines value while taking growth into account. < 1.0 is considered undervalued.")
            with v_col3:
                st.metric("Rev Growth", metrics['Growth']['Revenue Growth'], help="Revenue Growth (Year-over-Year). The increase in sales compared to the previous period.")
            with v_col4:
                st.metric("EPS Growth", metrics['Growth']['Earnings Growth'], help="Earnings Per Share Growth. Shows how much profit is growing on a per-share basis.")
            
            st.markdown("---")
            
            st.subheader("Health & Profitability")
            h_col1, h_col2, h_col3, h_col4 = st.columns(4)
            with h_col1:
                st.metric("Net Margin", metrics['Profitability']['Net Margin'], help="Net Profit Margin. The percentage of revenue left after all expenses are paid.")
            with h_col2:
                st.metric("Debt/Equity", metrics['Health']['Debt/Equity'], help="Debt-to-Equity Ratio. Measures financial leverage. Lower is generally safer (< 100%).")
            with h_col3:
                st.metric("Free Cash Flow", metrics['Cash Flow']['Free Cash Flow'], help="Cash generated after accounting for operating costs and capital assets. Positive is critical.")
            with h_col4:
                st.metric("Current Ratio", metrics['Health']['Current Ratio'], help="Liquidity ratio. Measures ability to pay short-term obligations. > 1.5 is healthy.")
            
            st.info(f"**Business Summary:** {data['summary'][:400]}...")

        # TAB 2: ANALYSIS DETAILS (The 14 Steps Breakdown)
        with tab2:
            st.subheader("Score Calculation Logic")
            for item in data['breakdown']:
                st.write(item)
            
            st.markdown("### Deep Dive Data")
            # Flatten metrics for cleaner display
            flat_metrics = []
            for category, values in metrics.items():
                for k, v in values.items():
                     flat_metrics.append({"Category": category, "Metric": k, "Value": v})
            
            st_df = pd.DataFrame(flat_metrics)
            st.dataframe(st_df, use_container_width=True, hide_index=True)

        # TAB 3: NEWS
        with tab3:
            st.subheader("Latest News")
            if data['news']:
                for article in data['news']:
                    # Robust extraction
                    title = article.get('title')
                    link = article.get('link')
                    if 'content' in article:
                        content = article['content']
                        if not title: title = content.get('title')
                        if not link: 
                            # Robustly handle clickThroughUrl
                            click_through = content.get('clickThroughUrl')
                            if click_through:
                                link = click_through.get('url')
                            if not link:
                                link = content.get('url')
                    
                    if not title: title = "No Title"
                    if not link: link = "#"
                        
                    st.markdown(f"**[{title}]({link})**")
            else:
                st.write("No news found.")

        # TAB 4: AI CHAT
        with tab4:
             st.subheader(f"Chat with {data['symbol']} Agent")
             
             # Context Injection with Extended Metrics
             system_instruction = f"""
             You are a Senior Wall Street Analyst.
             Analyzing: {data['name']} ({data['symbol']})
             
             HARD DATA:
             - Price: {data['price']}, Target: {data['target_price']}
             - Score: {data['score']}/100 ({data['verdict']})
             - Valuation: P/E {metrics['Valuation']['P/E']}, PEG {metrics['Valuation']['PEG']}
             - Growth: Revenue {metrics['Growth']['Revenue Growth']}
             - Health: Debt/Equity {metrics['Health']['Debt/Equity']}, FCF {metrics['Cash Flow']['Free Cash Flow']}
             - Profitability: Net Margin {metrics['Profitability']['Net Margin']}
             
             ANALYSIS SUMMARY:
             {', '.join(data['breakdown'])}
             
             INSTRUCTIONS:
             1. Answer specific questions using this data.
             2. If asked 'Is it a buy?', reference the Score and the specific strengths/weaknesses in the breakdown.
             3. Be concise.
             """
             
             try:
                client = genai.Client(api_key=api_key)
                
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                if prompt := st.chat_input("Ask a question..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing..."):
                            try:
                                response_text = ""
                                # Retry logic for rate limits
                                for attempt in range(4):
                                    try:
                                        response = client.models.generate_content(
                                            model='gemini-2.5-flash',
                                            config=types.GenerateContentConfig(
                                                system_instruction=system_instruction,
                                                temperature=0.5
                                            ),
                                            contents=[prompt]
                                        )
                                        response_text = response.text
                                        break
                                    except Exception as e:
                                        # ClientErr or similar; check for 429
                                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                                            if attempt < 3:
                                                wait = (attempt + 1) ** 2  # 1, 4, 9 seconds
                                                st.toast(f"Rate limit hit. Retrying in {wait}s...", icon="⏳")
                                                time.sleep(wait)
                                                continue
                                        raise e
                                
                                st.markdown(response_text)
                                st.session_state.messages.append({"role": "assistant", "content": response_text})
                            except Exception as e:
                                st.error(f"AI Error: {e}")
             except Exception as e:
                 st.error(f"Client Init Error: {e}")

elif not api_key and st.session_state.get('analyze_clicked'):
    st.warning("Please enter your Google Gemini API Key in the sidebar.")
else:
    st.info("👈 Enter a ticker and API key to start the 14-Step Analysis.")
