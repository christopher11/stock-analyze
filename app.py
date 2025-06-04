import streamlit as st
import os
from dotenv import load_dotenv
import requests
import pandas as pd
import openai
import json
from ollama import chat

result = load_dotenv()
print("load_dotenv() result:", result)

# Load API keys from the .env file
MARKETSTACK_API_KEY = os.getenv('MARKETSTACK_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
LOCAL_LLM = os.getenv('LOCAL_LLM', 'false').lower() == 'true'
LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', 'gemma3:1b')
LOCAL_LLM_URL = os.getenv('LOCAL_LLM_URL', 'http://localhost:11434')

st.title('📈 Stock Trend Analyzer')
st.write('This tool fetches stock data from online APIs and uses an LLM 🤖 to analyze trends and provide insights.')

st.markdown('---')

st.header('🔍 Analyze a Stock')

ticker = st.text_input('Enter Stock Ticker (e.g. → AAPL, TSLA):')
period = st.selectbox('Select Period:', ['Day', 'Week', 'Month'])

st.markdown('---')

@st.cache_data(show_spinner=False)
def fetch_stock_data(symbol, period):
    base_url = 'http://api.marketstack.com/v1/eod'
    params = {
        'access_key': MARKETSTACK_API_KEY,
        'symbols': symbol,
        'limit': 30  # fetch up to 30 days for flexibility
    }
    
    response = requests.get(base_url, params=params)
    
    data = response.json()
    if 'data' not in data or not data['data']:
        return None
    
    df = pd.DataFrame(data['data'])
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    if period == 'Day':
        df = df.tail(1)
    elif period == 'Week':
        df = df.tail(5)
    elif period == 'Month':
        df = df.tail(22)
    return df

def call_ollama_llm(prompt, model, url=None):
    # Ollama Python will pick up OLLAMA_HOST
    if url:
        os.environ["OLLAMA_HOST"] = url.rstrip('/')

    try:
        response = chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Failed to connect to Ollama. Error: {e}"

def get_llm_trend_and_explanation(ticker, period, df):
    if df is None or df.empty:
        return 'No data to analyze.'
    table = df.to_csv(index=False)
    prompt = f"""You are a data-analysis assistant.    
Here is the historical price data for {ticker} over the last {period.lower()}:
<DATA BEGINS>
{table}
<DATA ENDS>

Please analyze this data and determine:
- The overall trend (upward, downward, or neutral)
- Predict and provide a brief explanation of what might 
    have caused this trend (≤ 100 words)
Output your answer in a user-friendly format.

Use this below format to return the answer:
**Trend**: <state the trend> \n
**Explanation**: <state the prediction and explanation> \n
"""
    try:
        if LOCAL_LLM:
            return call_ollama_llm(prompt, LOCAL_LLM_MODEL, LOCAL_LLM_URL)
        else:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            return "No response from OpenAI"
    except Exception as e:
        return f"Error from LLM: {e}"

if st.button('🔎 Analyze'):
    st.write('Fetching data and analyzing... ⏳')
    df = fetch_stock_data(ticker, period)
    if df is not None and not df.empty:
        st.dataframe(df)
    llm_explanation = get_llm_trend_and_explanation(ticker, period, df)
    st.write('### 🤖 LLM Analysis:')
    st.write(llm_explanation)
