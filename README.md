# Stock AI Analyst 📈🤖

An advanced AI-powered stock analysis dashboard built with **Streamlit** and **Google Gemini 2.0 Flash**.

This application performs a comprehensive **14-Step Fundamental Analysis** on any stock ticker and provides an interactive AI Analyst to answer your questions based on real-time financial data.

![App Screenshot](https://via.placeholder.com/800x400?text=Stock+AI+Analyst+Dashboard) 
*(Replace with your actual screenshot)*

## 🚀 Features

*   **📊 Interactive Dashboard**: Instant view of Valuation, Growth, Health, and Profitability metrics.
*   **📝 14-Step Investment Framework**: Automatically calculates a score (0-100) and a verdict (Buy/Sell/Hold) based on rigorous fundamental criteria.
*   **💬 AI Analyst Chat**: Chat with an AI agent that knows the specific context, numbers, and news of the stock you are analyzing. Uses the latest **Gemini 2.0 Flash** model.
*   **📰 Latest News**: Aggregates top news stories for the ticker.
*   **🔒 Secure**: "Bring Your Own Key" architecture. Your API key is processed in-memory and never stored.

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/jayabalan1992/stock_analyzer.git
    cd stock_analyzer
    ```

2.  **Create a virtual environment (Optional but Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🏃‍♂️ Usage

1.  **Run the Streamlit App:**
    ```bash
    streamlit run app.py
    ```

2.  **Get a Gemini API Key:**
    *   Go to [Google AI Studio](https://aistudio.google.com/).
    *   Create a free API Key.

3.  **Analyze:**
    *   Enter a Ticker (e.g., `NVDA`, `AAPL`) in the sidebar.
    *   Paste your API Key.
    *   Click **Analyze Stock**.

## 📦 Requirements

*   Python 3.8+
*   streamlit
*   yfinance
*   pandas
*   google-genai

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
